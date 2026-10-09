"""Scorecard of a model on real validation, and paired bootstrap deltas between two models.

The metrics every strategy is compared on are defined in docs/decisions/README.md Section 3.1. The official AP
(bdc26.evalap) matches detections to GT greedily inside each frame, so the true-positive flags of a frame do not
depend on the other frames. Computing the flags once per frame therefore gives the exact official AP of any
multiset of frames by concatenation, which is what makes a frame bootstrap cheap: resample frames, concatenate
their (score, flag) arrays, interpolate.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .evalap import _greedy_tp, _interp_ap, iou_pair
from .pcdet_export import read_labels_txt

KINDS = (("3d", 0.5), ("bev", 0.5), ("3d", 0.7))


def key(kind: str, thr: float) -> str:
    return f"{kind}@{thr}"


def load_split(root: Path, split: str, ids_filter=None) -> dict:
    """{frame_id: (gt_boxes (G,7), names (G,))} of a dataset split (pcdet layout: ImageSets/<split>.txt, labels/)."""
    ids = (root / "ImageSets" / f"{split}.txt").read_text().split()
    if ids_filter is not None:
        keep = set(ids_filter)
        ids = [i for i in ids if i in keep]
    return {i: read_labels_txt(root / "labels" / f"{i}.txt") for i in ids}


def frame_flags(preds: dict, gts: dict, classes: list[str], exact: bool | None = None) -> dict:
    """Per class and frame: {"scores": in-frame order of the official scorer, "<kind>@<thr>": TP flags, "n_gt": G}.

    In-frame order follows bdc26.evalap._official_ap: score-descending (stable) when the frame has GT of the
    class, the original order otherwise (all false positives). Frames are kept in GT-dict order.
    """
    out = {c: [] for c in classes}
    for c in classes:
        lc = c.lower()
        for fid, (gb, gn) in gts.items():
            gm = np.array([str(n).lower() == lc for n in gn], dtype=bool)
            g = np.asarray(gb, dtype=np.float64).reshape(-1, 7)[gm]
            ps = [p for p in preds.get(fid, []) if str(p.get("class", "Car")).lower() == lc]
            b = np.array([p["box"] for p in ps], dtype=np.float64).reshape(-1, 7)
            s = np.array([p["score"] for p in ps], dtype=np.float64)
            rec = {"fid": fid, "n_gt": int(len(g))}
            if len(b) == 0 or len(g) == 0:
                rec["scores"] = s
                for kind, thr in KINDS:
                    rec[key(kind, thr)] = np.zeros(len(s), dtype=np.int64)
            else:
                order = np.argsort(-s, kind="stable")
                i3, ib = iou_pair(b, g, exact)
                rec["scores"] = s[order]
                for kind, thr in KINDS:
                    iou = (i3 if kind == "3d" else ib)[order]
                    rec[key(kind, thr)] = _greedy_tp(np.ascontiguousarray(iou, dtype=np.float64), float(thr))
            out[c].append(rec)
    return out


def ap_from_flags(recs: list, k: str, index=None) -> float | None:
    """Official AP R40 of the frames recs[index] (all frames when index is None; repeats allowed)."""
    sel = recs if index is None else [recs[i] for i in index]
    n_gt = sum(r["n_gt"] for r in sel)
    if n_gt == 0:
        return None
    sc = [r["scores"] for r in sel if len(r["scores"])]
    if not sc:
        return 0.0
    sc = np.concatenate(sc)
    tp = np.concatenate([r[k] for r in sel if len(r["scores"])])
    return _interp_ap(tp[np.argsort(-sc)], n_gt)[0]


def summarize(flags: dict, classes_with_gt: list[str]) -> dict:
    """Per-class AP and challenge mAP (mean over classes_with_gt that have GT here) for every kind."""
    out = {"per_class": {}, "mAP": {}}
    for c, recs in flags.items():
        out["per_class"][c] = {key(kind, thr): ap_from_flags(recs, key(kind, thr)) for kind, thr in KINDS}
        out["per_class"][c]["n_gt"] = sum(r["n_gt"] for r in recs)
    for kind, thr in KINDS:
        k = key(kind, thr)
        vals = [out["per_class"][c][k] for c in classes_with_gt if c in flags and out["per_class"][c][k] is not None]
        out["mAP"][k] = float(np.mean(vals)) if vals else None
    out["bev_3d_gap"] = (out["mAP"]["bev@0.5"] - out["mAP"]["3d@0.5"]) if out["mAP"]["3d@0.5"] is not None else None
    return out


def paired_bootstrap(fa: dict, fb: dict, classes_with_gt: list[str], n: int = 200, seed: int = 0,
                     k: str = "3d@0.5") -> dict:
    """Paired frame bootstrap of AP(b) - AP(a) per class and for the challenge mAP.

    fa and fb must come from the same GT (same frames, same order). Returns per class and for "mAP":
    {"delta": full-set delta, "p_gain": share of resamples with delta > 0, "ci90": [5th, 95th percentile]}.
    """
    classes = [c for c in classes_with_gt if c in fa and c in fb]
    n_frames = len(next(iter(fa.values())))
    for c in classes:
        assert [r["fid"] for r in fa[c]] == [r["fid"] for r in fb[c]], "bootstrap needs the same frames in the same order"
    rng = np.random.default_rng(seed)
    full = {c: (ap_from_flags(fa[c], k), ap_from_flags(fb[c], k)) for c in classes}
    classes = [c for c in classes if full[c][0] is not None]
    deltas = {c: [] for c in classes + ["mAP"]}
    for _ in range(n):
        idx = rng.integers(0, n_frames, n_frames)
        da, db = [], []
        for c in classes:
            a_, b_ = ap_from_flags(fa[c], k, idx), ap_from_flags(fb[c], k, idx)
            if a_ is None or b_ is None:                 # a resample without GT of this class
                continue
            deltas[c].append(b_ - a_)
            da.append(a_)
            db.append(b_)
        deltas["mAP"].append(float(np.mean(db) - np.mean(da)))
    out = {}
    for c in classes + ["mAP"]:
        d = np.asarray(deltas[c])
        full_d = (full[c][1] - full[c][0]) if c != "mAP" else float(np.mean([full[x][1] for x in classes]) -
                                                                      np.mean([full[x][0] for x in classes]))
        out[c] = {"delta": float(full_d), "p_gain": float((d > 0).mean()) if len(d) else None,
                  "ci90": [float(np.percentile(d, 5)), float(np.percentile(d, 95))] if len(d) else None}
    return out


def class_gate(delta_b: float, p_gain: float | None, delta_a: float | None,
               min_gain: float = 0.01, min_p: float = 0.9, max_a_drop: float = 0.005) -> bool:
    """The class gate of docs/decisions/README.md Section 3.2."""
    return (delta_b >= min_gain and p_gain is not None and p_gain >= min_p
            and (delta_a is None or delta_a >= -max_a_drop))


def combined_estimate(m_ap: float, r: float) -> float:
    return 0.6 * min(max(m_ap / 0.7, 0.0), 1.0) + 0.4 * r


def late_a_ids(track, ids: list[str]) -> list[str]:
    """realval-A frames inside track.yaml `late_a` (LUMPI: Measurement4 4800-6399); [] when the track has none."""
    spec = track.cfg.get("late_a")
    if not spec:
        return []
    out = []
    for i in ids:
        head, _, idx = i.partition("__")
        if head == spec["prefix"] and idx.isdigit() and spec["min_frame"] <= int(idx) <= spec["max_frame"]:
            out.append(i)
    return out


def subset(flags: dict, ids) -> dict:
    keep = set(ids)
    return {c: [r for r in recs if r["fid"] in keep] for c, recs in flags.items()}


def flags_for(pred_path: Path, gts: dict, classes: list[str], exact: bool | None = None, cache: bool = True) -> dict:
    """frame_flags of a predictions file, cached next to it (keyed by file size, mtime, frames and IoU mode)."""
    import pickle
    pred_path = Path(pred_path)
    st = pred_path.stat()
    tag = (st.st_size, int(st.st_mtime), tuple(gts), tuple(classes), exact)
    cpath = pred_path.with_name(f".flags_{pred_path.stem}.pkl")
    if cache and cpath.exists():
        try:
            saved = pickle.loads(cpath.read_bytes())
            if saved["tag"] == tag:
                return saved["flags"]
        except Exception:
            pass
    import json
    preds = json.loads(pred_path.read_text())
    flags = frame_flags({i: preds.get(i, []) for i in gts}, gts, classes, exact)
    if cache:
        cpath.write_bytes(pickle.dumps({"tag": tag, "flags": flags}))
    return flags
