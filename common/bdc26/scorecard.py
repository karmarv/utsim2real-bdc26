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


def frame_group(fid: str, track_name: str, block: int = 1000) -> str:
    """S10 rule 14: the resampling unit of the grouped gate. V2X: the scenario folder (`<scenario>__<frame>`).
    LUMPI: the measurement and a `block`-frame window of it (1000 raw frames = 100 s at 10 Hz)."""
    head, _, idx = fid.partition("__")
    if track_name.lower().startswith("lumpi") and idx.isdigit():
        return f"{head}:{int(idx) // block}"
    return head


def _map_of(fa: dict, fb: dict, classes: list[str], k: str, index=None):
    da, db = [], []
    for c in classes:
        a_, b_ = ap_from_flags(fa[c], k, index), ap_from_flags(fb[c], k, index)
        if a_ is None or b_ is None:
            continue
        da.append(a_)
        db.append(b_)
    return (float(np.mean(db) - np.mean(da))) if da else None


def grouped_bootstrap(fa: dict, fb: dict, classes_with_gt: list[str], groups: list[str], n: int = 1000,
                      seed: int = 0, k: str = "3d@0.5") -> dict:
    """S10 rule 14: paired bootstrap of the mAP delta (b - a) that resamples whole groups of frames (scenarios,
    recording windows) instead of single frames, so correlated neighbouring frames do not count as independent.
    groups[i] is the group of frame i (the order of the per-class records). Returns {"delta", "p_gain", "ci90",
    "n_groups"}."""
    classes = [c for c in classes_with_gt if c in fa and c in fb and ap_from_flags(fa[c], k) is not None]
    n_frames = len(next(iter(fa.values())))
    assert len(groups) == n_frames, "one group label per frame"
    names = sorted(set(groups))
    members = {g: np.flatnonzero(np.asarray(groups) == g) for g in names}
    rng = np.random.default_rng(seed)
    d = []
    for _ in range(n):
        pick = rng.integers(0, len(names), len(names))
        idx = np.concatenate([members[names[j]] for j in pick])
        v = _map_of(fa, fb, classes, k, idx)
        if v is not None:
            d.append(v)
    d = np.asarray(d)
    return {"delta": _map_of(fa, fb, classes, k), "p_gain": float((d > 0).mean()) if len(d) else None,
            "ci90": [float(np.percentile(d, 5)), float(np.percentile(d, 95))] if len(d) else None, "n_groups": len(names)}


def leave_one_group_out(fa: dict, fb: dict, classes_with_gt: list[str], groups: list[str], k: str = "3d@0.5") -> dict:
    """S10 rule 14: the mAP delta (b - a) with each group removed in turn. Returns {group: delta}."""
    classes = [c for c in classes_with_gt if c in fa and c in fb and ap_from_flags(fa[c], k) is not None]
    g = np.asarray(groups)
    return {name: _map_of(fa, fb, classes, k, np.flatnonzero(g != name)) for name in sorted(set(groups))}


def class_gate(delta_b: float, p_gain: float | None, delta_a: float | None,
               min_gain: float = 0.01, min_p: float = 0.9, max_a_drop: float = 0.005) -> bool:
    """The class gate of docs/decisions/README.md Section 3.2."""
    return (delta_b >= min_gain and p_gain is not None and p_gain >= min_p
            and (delta_a is None or delta_a >= -max_a_drop))


def pooled_gate(inc: dict, new: dict, c: str, n: int = 200, seed: int = 0, min_p: float = 0.9,
                k: str = "3d@0.5") -> dict:
    """Pooled condition of the class gate (docs/decisions/README.md Section 3.2, from R3 on): the change must also gain
    on the realval-A and realval-B frames pooled into one set, with paired bootstrap P(gain) >= min_p. inc and new:
    {split: per-frame flags of class c} over the same splits and frames. Checked on the 17 class changes of S3-S5:
    agrees with the leaderboard sign 16 times; rejects S5 LUMPI Car (pooled P 0.64, leaderboard -0.010)."""
    splits = [s_ for s_ in ("val", "valB") if s_ in inc and s_ in new]
    fa = [r for s_ in splits for r in inc[s_]]
    fb = [r for s_ in splits for r in new[s_]]
    b = paired_bootstrap({c: fa}, {c: fb}, [c], n, seed, k).get(c)
    if b is None:
        return {"delta": None, "p_gain": None, "ok": False}
    return {"delta": b["delta"], "p_gain": b["p_gain"],
            "ok": b["p_gain"] is not None and b["delta"] > 0 and b["p_gain"] >= min_p}


def combined_estimate(m_ap: float, r: float, clip: bool = True) -> float:
    """0.6 * clip(mAP / 0.7) + 0.4 * R, the official combination. The upload gate uses clip=False from R3 on: a local
    B-mAP can pass 0.7 (V2X 0.709) while the leaderboard mAP stays far below (0.589), and the clip would freeze the gate."""
    m = max(m_ap / 0.7, 0.0)
    return 0.6 * (min(m, 1.0) if clip else m) + 0.4 * r


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
