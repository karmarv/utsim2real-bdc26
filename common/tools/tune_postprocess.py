#!/usr/bin/env python
"""Select per-class post-processing on a real validation split and confirm it on a second one (module M11).

    python common/tools/tune_postprocess.py model-lumpi-track/pointpillars-g1 \
        --raw-a validation/output/raw_realval-A.json --raw-b validation/output/raw_realval-B.json \
        --data pcdet/realval-v1 --split-a val --split-b valB --out test/postprocess.yaml

Inputs are RAW predictions (pcdet_predict.py --raw: the model's near-raw boxes, score >= 0.01). Per-class AP is
independent of the other classes, so each class is tuned on its own by coordinate descent, in two phases:
  1. detector behaviour (should transfer across measurements): nms_iou, recenter (small classes);
     guarded by split B (kept at the start values if B drops by more than --guard-b);
  2. box convention (annotation habits differ by measurement; the test frames are LUMPI Measurement4 like split A):
     z_offset, size_scale (common l/w factor, then h); only for classes with >= --min-gt-convention GT in A;
then greedy cross-class hedges (receiving class: own boxes + discounted copies of other classes).
Everything is scored with bdc26.evalap (3D AP@0.5, R40, the challenge metric) on split A; split B is reported. This is hyperparameter selection on the real train split, which the
Rules tab allows; the 50 test frames are never involved.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from _common import data_path, model_info
from bdc26 import evalap
from bdc26.detect.postprocess import calibrate_stage, nms_stage, recenter_stage
from bdc26.evalap import ap_for_class
from bdc26.pcdet_export import read_labels_txt

NMS = [0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
RECENTER = [0.0, 0.25, 0.5]
ZOFF = [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3]
SLW = [0.85, 0.92, 1.0, 1.08, 1.16]
SH = [0.85, 0.92, 1.0, 1.08, 1.16]
HEDGE = [0.0, 0.1, 0.3, 0.6]
SMALL = {"person", "pedestrian", "bicycle", "motorcycle"}


def load(raw_path, root, split, classes, need_points):
    raw = json.loads(Path(raw_path).read_text())
    ids = [i for i in (root / "ImageSets" / f"{split}.txt").read_text().split() if i in raw]
    frames = []
    for i in ids:
        r = raw[i]
        b = np.array([d["box"] for d in r], dtype=np.float64).reshape(-1, 7)
        s = np.array([d["score"] for d in r], dtype=np.float64)
        l = np.array([d["class"] for d in r], dtype=object)
        gb, gn = read_labels_txt(root / "labels" / f"{i}.txt")
        pts = np.load(root / "points" / f"{i}.npy")[:, :3] if need_points else None
        frames.append({"b": b, "s": s, "l": l, "gb": np.asarray(gb).reshape(-1, 7), "gn": np.asarray(gn), "p": pts})
    n_gt = {c: int(sum((f["gn"] == c).sum() for f in frames)) for c in classes}
    return frames, n_gt


_CACHE: dict = {}


def class_boxes(frames, c, cc):
    """Per-frame (boxes, scores) of class c after post-processing. NMS and re-centering outputs are cached per
    (split, class, score floor, pre_max, nms_iou[, recenter]) because only the cheap calibration stage changes
    during most of the search."""
    k1 = (id(frames), c, cc.get("score_floor", 0.01), cc.get("pre_max", 400), cc.get("nms_iou", 0.2))
    if k1 not in _CACHE:
        _CACHE[k1] = [nms_stage(f["b"][f["l"] == c], f["s"][f["l"] == c], cc) for f in frames]
    k2 = k1 + (cc.get("recenter", 0.0),)
    if k2 not in _CACHE:
        _CACHE[k2] = [recenter_stage(b, s, cc, f["p"]) for (b, s), f in zip(_CACHE[k1], frames)]
    return [calibrate_stage(b, s, cc) for b, s in _CACHE[k2]]


def ap(frames, c, own, extra=None):
    """3D AP@0.5 R40 of class c from per-frame (boxes, scores) lists, optionally with extra (boxes, scores)."""
    fr = []
    for k, f in enumerate(frames):
        b, s = own[k]
        if extra is not None:
            b = np.concatenate([b, extra[k][0]]); s = np.concatenate([s, extra[k][1]])
        fr.append((b, s, f["gb"][f["gn"] == c]))
    r = ap_for_class(fr, 0.5, "3d")
    return r["AP_R40"] if r else None


def hedge_of(hedge, t):
    """(source, factor) pairs already hedging into target t."""
    return [(src, f) for src, pairs in hedge.items() for dst, f in pairs if dst == t]


def _search(frames, c, cc, best, steps):
    for key, grid in steps:
        for v in grid:
            trial = dict(cc)
            if key == "size_lw":
                sc = list(trial.get("size_scale", [1.0, 1.0, 1.0])); sc[0] = sc[1] = v; trial["size_scale"] = sc
            elif key == "size_h":
                sc = list(trial.get("size_scale", [1.0, 1.0, 1.0])); sc[2] = v; trial["size_scale"] = sc
            else:
                trial[key] = v
            a = ap(frames, c, class_boxes(frames, c, trial))
            if a is not None and a > best + 1e-4:
                best, cc = a, trial
    return cc, best


def tune_class(frames, c, base, convention=True):
    """Phase 1, detector behaviour (transfers across measurements): NMS IoU, re-centering for small classes.
    Phase 2, box convention (measurement-specific annotation habits): z offset and size scale."""
    best = ap(frames, c, class_boxes(frames, c, base))
    steps = [("nms_iou", NMS)] + ([("recenter", RECENTER)] if c.lower() in SMALL else [])
    cc1, a1 = _search(frames, c, dict(base), best, steps)
    if not convention:
        return cc1, a1, cc1, a1
    cc2, a2 = _search(frames, c, cc1, a1, [("z_offset", ZOFF), ("size_lw", SLW), ("size_h", SH)])
    return cc1, a1, cc2, a2


def _conv(cc):
    return {k: cc[k] for k in ("z_offset", "size_scale") if k in cc}


def main():
    ap_ = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap_.add_argument("model_dir")
    ap_.add_argument("--raw-a", required=True)
    ap_.add_argument("--raw-b", default=None)
    ap_.add_argument("--data", required=True)
    ap_.add_argument("--split-a", default="val")
    ap_.add_argument("--split-b", default="valB")
    ap_.add_argument("--start", default=None, help="starting postprocess.yaml (default: the model's)")
    ap_.add_argument("--out", required=True)
    ap_.add_argument("--no-size", action="store_true", help="do not tune size_scale / z_offset")
    ap_.add_argument("--guard-b", type=float, default=0.005,
                     help="keep a class's start NMS / re-centering if tuning them lowers its split-B AP by more than this "
                          "(0 = off). Box-convention knobs (z offset, size scale) are not guarded: annotation conventions "
                          "differ by measurement (LUMPI M4 Person 0.77 x 0.74 x 1.90 m vs M5 0.99 x 0.80 x 1.83 m) and the "
                          "test frames are M4, like split A")
    ap_.add_argument("--min-gt-convention", type=int, default=500,
                     help="tune z offset / size scale only for classes with at least this many GT boxes in split A")
    a = ap_.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    evalap.EXACT_IOU = False             # fast float32 IoUs for the search; tune_and_eval.sh re-scores exactly
    root = data_path(track, a.data)
    classes = [c for c in track.classes]
    start = yaml.safe_load(Path(a.start or model_dir / "test" / "postprocess.yaml").read_text())
    A, nA = load(a.raw_a, root, a.split_a, classes, True)
    B, nB = load(a.raw_b, root, a.split_b, classes, True) if a.raw_b else (None, None)
    if a.no_size:
        global ZOFF, SLW, SH
        ZOFF, SLW, SH = [0.0], [1.0], [1.0]
    default = start.get("default", {})
    tuned, report = {}, {}
    for c in classes:
        if nA[c] == 0:
            continue
        base = {**default, **(start.get("classes") or {}).get(c, {})}
        a0 = ap(A, c, class_boxes(A, c, base))
        cc1, a1, cc2, a2 = tune_class(A, c, base, convention=nA[c] >= a.min_gt_convention)
        row = {"n_gt_A": nA[c], "A_start": a0, "A_behaviour": a1, "A_tuned": a2,
               "behaviour_cfg": {k: v for k, v in cc1.items() if default.get(k) != v}, "convention_cfg": _conv(cc2)}
        final = cc2
        if B is not None and nB[c]:
            b0, b1 = ap(B, c, class_boxes(B, c, base)), ap(B, c, class_boxes(B, c, cc1))
            row.update(n_gt_B=nB[c], B_start=b0, B_behaviour=b1, B_tuned=ap(B, c, class_boxes(B, c, cc2)))
            if a.guard_b and b1 < b0 - a.guard_b:      # behaviour knobs that do not transfer: keep the start values
                final = {**base, **_conv(cc2)}
                row["behaviour_kept_start"] = True
                row["A_tuned"] = ap(A, c, class_boxes(A, c, final))
                row["B_tuned"] = ap(B, c, class_boxes(B, c, final))
        tuned[c] = {k: v for k, v in final.items() if default.get(k) != v}
        report[c] = row
        print(c, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}), "->", tuned[c], flush=True)
    # cross-class hedges: target gets discounted copies of a source's (tuned) boxes
    hedge = {}
    cfg_of = {c: {**default, **tuned.get(c, (start.get("classes") or {}).get(c, {}))} for c in classes}
    ownA = {c: class_boxes(A, c, cfg_of[c]) for c in classes}
    for t in classes:
        if nA[t] == 0:
            continue
        cur_ap, ext = ap(A, t, ownA[t]), None       # greedy: add the best (source, factor) given the hedges so far
        while True:
            best = None
            for s_ in classes:
                if s_ == t or any(s_ == h for h, _ in hedge_of(hedge, t)):
                    continue
                for f in HEDGE[1:]:
                    add = [(b, sc * f) for b, sc in ownA[s_]]
                    trial = add if ext is None else [(np.concatenate([e[0], a_[0]]), np.concatenate([e[1], a_[1]]))
                                                     for e, a_ in zip(ext, add)]
                    v = ap(A, t, ownA[t], trial)
                    if v > cur_ap + 2e-3 and (best is None or v > best[0]):
                        best = (v, s_, f, trial)
            if best is None:
                break
            v, s_, f, ext = best
            hedge.setdefault(s_, []).append([t, f])
            report[t][f"hedge_from_{s_}"] = {"factor": f, "A": v}
            print(f"hedge {s_} -> {t} x{f}: A {cur_ap:.4f} -> {v:.4f}", flush=True)
            cur_ap = v
    out = {"default": default, "classes": tuned, "hedge": hedge,
           "selected_on": f"{a.data}:{a.split_a} (real train split, guard-allowed)", "checked_on": f"{a.data}:{a.split_b}",
           "b_guard": a.guard_b if B is not None else None}
    Path(a.out).write_text("# Selected by common/tools/tune_postprocess.py on real validation (see report json).\n"
                           + yaml.safe_dump(out, sort_keys=False))
    Path(a.out).with_suffix(".report.json").write_text(json.dumps(report, indent=2))
    mA = np.mean([r["A_tuned"] for r in report.values()])
    print(f"mean tuned AP on A over {len(report)} classes: {mA:.4f} (without hedges)")


if __name__ == "__main__":
    main()
