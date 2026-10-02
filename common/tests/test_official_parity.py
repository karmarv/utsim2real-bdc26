"""Parity with the official CodaBench scorer shipped in the starting kit (scoring_program/), on synthetic inputs.

Skipped unless the kit is ingested ($BDC_DATA/lumpi-track/kit/scoring_program) and shapely + POT are installed.
No real or test data is used: every box and point here is random.
"""
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest

from bdc26 import evalap, realism

SCORING = Path(os.environ.get("BDC_DATA", Path(__file__).resolve().parents[3] / "bdc26-data")) / "lumpi-track/kit/scoring_program"


def _official(name):
    if not (SCORING / f"{name}.py").exists():
        pytest.skip("starting kit not ingested")
    pytest.importorskip("shapely")
    pytest.importorskip("ot")
    sys.path.insert(0, str(SCORING))
    spec = importlib.util.spec_from_file_location(f"official_{name}", SCORING / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _scene(rng, n_frames=40, classes=("vehicle", "pedestrian", "truck")):
    preds, gts_official, gts_ours = {}, {}, {}
    sizes = {"vehicle": (4.5, 1.9, 1.6), "pedestrian": (0.8, 0.7, 1.8), "truck": (8.0, 2.6, 3.2)}
    for f in range(n_frames):
        fid = f"{f:06d}"
        g, names = [], []
        for c in classes:
            for _ in range(rng.integers(0, 6)):
                l, w, h = np.array(sizes[c]) * rng.uniform(0.85, 1.15, 3)
                g.append([*rng.uniform(-35, 35, 2), rng.uniform(-2, -1), l, w, h, rng.uniform(-np.pi, np.pi)])
                names.append(c)
        g = np.array(g).reshape(-1, 7)
        p = []
        for b, c in zip(g, names):                           # noisy detections, duplicates and class swaps
            for _ in range(rng.integers(0, 3)):
                q = b.copy(); q[:3] += rng.normal(0, 0.25 if c != "pedestrian" else 0.1, 3)
                q[3:6] *= rng.uniform(0.85, 1.15, 3); q[6] += rng.normal(0, 0.1)
                p.append({"box": q.tolist(), "score": float(rng.uniform()), "class": c if rng.uniform() > 0.1 else str(rng.choice(classes))})
        for _ in range(rng.integers(0, 8)):                  # clutter
            c = str(rng.choice(classes)); l, w, h = sizes[c]
            p.append({"box": [*rng.uniform(-35, 35, 2), -1.5, l, w, h, rng.uniform(-np.pi, np.pi)], "score": float(rng.uniform()), "class": c})
        preds[fid] = p
        gts_official[fid] = [{"box": b.tolist(), "class": c} for b, c in zip(g, names)]
        gts_ours[fid] = (g, np.array(names))
    return preds, gts_official, gts_ours, list(classes)


@pytest.mark.parametrize("seed", [0, 1])
def test_detection_matches_official(seed):
    official = _official("detection_eval")
    preds, gto, gt, classes = _scene(np.random.default_rng(seed))
    ours = evalap.evaluate(preds, gt, classes)
    for kind in ("3d", "bev"):
        ref = official.evaluate_3d_detection(preds, gto, classes, iou_thresholds=(0.5, 0.7), iou_type=kind)
        for thr in (0.5, 0.7):
            for interp in ("R40", "R11"):
                assert abs(ours[f"mAP_{kind}_{thr}_{interp}"] - ref[f"mAP_{thr}_{interp}"]) < 1e-6, (kind, thr, interp)
            for c in classes:
                assert abs(ours["per_class"][c][f"{kind}@{thr}"]["AP_R40"] - ref["per_class"][c][f"AP_{thr}_R40"]) < 1e-6
                assert ours["per_class"][c][f"{kind}@{thr}"]["n_pred"] == ref["per_class"][c]["n_pred"]


def test_detection_class_without_gt_is_excluded():
    official = _official("detection_eval")
    preds, gto, gt, _ = _scene(np.random.default_rng(3))
    classes = ["vehicle", "pedestrian", "truck", "Unknown"]
    ref = official.evaluate_3d_detection(preds, gto, classes, iou_thresholds=(0.5,), iou_type="3d")
    ours = evalap.evaluate(preds, gt, classes, iou_thresholds=(0.5,))
    assert ours["per_class"]["Unknown"]["3d@0.5"] is None and np.isnan(ref["per_class"]["Unknown"]["AP_0.5_R40"])
    assert abs(ours["mAP_3d_0.5_R40"] - ref["mAP_0.5_R40"]) < 1e-6


def test_realism_matches_official():
    official = _official("metrics")
    rng = np.random.default_rng(0)
    rng_box = (-40, -40, -8, 40, 40, 2)
    def frame(shift):
        p = np.c_[rng.uniform(-45, 45, (3000, 2)) + shift, rng.uniform(-6, 1, 3000)].astype(np.float32)
        p[:900] = 0.0                                         # null returns, inside the range
        return p
    syn = [frame(0.0) for _ in range(50)]
    ref = [frame(1.0) for _ in range(50)]
    a = realism.score(syn, ref, rng_box, exact_emd=True)
    b = official.compute_realism(syn, ref, rng_box, seed=1234)
    for k in ("CD", "EMD", "FPD"):
        assert abs(a[k] - b[k]) <= 1e-6 * max(1.0, abs(b[k])), k
    assert abs(a["MMD"] - b["MMD"]) < 1e-9 and abs(a["MMD_gamma"] - b["MMD_gamma"]) < 1e-12
    assert a["n_syn_points_pre_subsample"] == b["n_syn_points_pre_subsample"]
