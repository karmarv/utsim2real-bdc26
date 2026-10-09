"""Tests of the S1 close-out tools: scorecard and bootstrap, z calibration, diagnostics, registry migration."""
import csv
import json

import numpy as np
import pytest

from bdc26 import diagnostics as dg
from bdc26 import evalap, registry
from bdc26 import scorecard as sc
from bdc26.config import load_track
from bdc26.detect import zcalib

V2X = load_track("v2x")


def _toy(seed=0, n_frames=40, noise=0.15, z_bias=None, spurious=3):
    """GT pedestrians and vehicles per frame plus noisy, partly missed, partly spurious predictions."""
    rng = np.random.default_rng(seed)
    gts, preds = {}, {}
    for f in range(n_frames):
        fid = f"f{f:03d}"
        boxes, names, dets = [], [], []
        for _ in range(rng.integers(1, 6)):
            cls, size = (("pedestrian", [0.7, 0.7, 1.7]) if rng.random() < 0.6 else ("vehicle", [4.5, 1.9, 1.6]))
            x, y = rng.uniform(-35, 35, 2)
            b = [x, y, -1.0, *size, rng.uniform(-np.pi, np.pi)]
            boxes.append(b)
            names.append(cls)
            if rng.random() < 0.85:
                p = np.array(b) + np.r_[rng.normal(0, noise, 3), rng.normal(0, 0.05, 3), rng.normal(0, 0.05)]
                if z_bias is not None:
                    p[2] += z_bias(np.hypot(x, y))
                dets.append({"box": p.tolist(), "score": float(rng.uniform(0.3, 1.0)), "class": cls})
        for _ in range(rng.integers(0, spurious)):
            dets.append({"box": [*rng.uniform(-35, 35, 2), -1.0, 0.7, 0.7, 1.7, 0.0], "score": float(rng.uniform(0, 0.6)),
                         "class": "pedestrian"})
        gts[fid] = (np.array(boxes), np.array(names))
        preds[fid] = dets
    return preds, gts


def test_scorecard_flags_reproduce_official_ap():
    preds, gts = _toy()
    classes = ["vehicle", "pedestrian", "truck"]
    ref = evalap.evaluate(preds, gts, classes)
    s = sc.summarize(sc.frame_flags(preds, gts, classes), ["vehicle", "pedestrian", "truck"])
    for c in ("vehicle", "pedestrian"):
        for k in ("3d@0.5", "bev@0.5", "3d@0.7"):
            assert s["per_class"][c][k] == pytest.approx(ref["per_class"][c][k]["AP_R40"], abs=1e-12)
    assert s["per_class"]["truck"]["3d@0.5"] is None                     # no GT: excluded from the mean
    assert s["mAP"]["3d@0.5"] == pytest.approx(ref["mAP_3d_0.5_R40"], abs=1e-12)


def test_paired_bootstrap_and_class_gate():
    preds, gts = _toy(1, n_frames=60, spurious=8)
    classes = ["vehicle", "pedestrian"]
    fa = sc.frame_flags(preds, gts, classes)
    same = sc.paired_bootstrap(fa, fa, classes, n=50, seed=0)
    assert same["pedestrian"]["delta"] == 0.0 and same["pedestrian"]["p_gain"] == 0.0
    better = {fid: [dict(d, score=d["score"] * 0.1) if d["score"] < 0.6 and d["box"][3] < 1 and
                    not any(np.hypot(d["box"][0] - g[0], d["box"][1] - g[1]) < 0.5 for g in gts[fid][0]) else d
                    for d in dets] for fid, dets in preds.items()}          # demote the spurious pedestrians
    fb = sc.frame_flags(better, gts, classes)
    boot = sc.paired_bootstrap(fa, fb, classes, n=100, seed=0)
    assert boot["pedestrian"]["delta"] > 0.01 and boot["pedestrian"]["p_gain"] >= 0.9
    assert sc.class_gate(boot["pedestrian"]["delta"], boot["pedestrian"]["p_gain"], 0.0)
    assert not sc.class_gate(0.02, 0.5, 0.0) and not sc.class_gate(0.02, 0.95, -0.01) and not sc.class_gate(0.005, 1.0, 0.0)
    assert sc.combined_estimate(0.35, 0.9) == pytest.approx(0.6 * 0.5 + 0.36)


def test_late_a_ids():
    lumpi = load_track("lumpi")
    ids = ["Measurement4__004795", "Measurement4__004800", "Measurement4__006395", "Measurement5__005000"]
    assert sc.late_a_ids(lumpi, ids) == ["Measurement4__004800", "Measurement4__006395"]
    assert sc.late_a_ids(V2X, ids) == []


def test_zcalib_recovers_a_range_dependent_bias():
    bias = lambda r: 0.3 - 0.01 * r                                       # predicted too high near, too low far
    preds, gts = _toy(2, n_frames=60, noise=0.03, z_bias=bias)
    zs = zcalib.ZSearch(preds, gts, "pedestrian", thr=0.7)               # at 0.5 this bias rarely flips a match
    ref = evalap.evaluate(preds, gts, ["pedestrian"])["per_class"]["pedestrian"]["3d@0.7"]["AP_R40"]
    assert zs.ap(0, 0) == pytest.approx(ref, abs=1e-6)                    # same AP as the official evaluator
    res = zs.search(zcalib.Z0_GRID, zcalib.K_GRID)
    assert res["ap_best"] > res["ap_base"] + 0.05
    r = np.concatenate([np.hypot(g[:, 0], g[:, 1]) for g, _ in gts.values()])
    residual = np.median(np.abs(bias(r) + res["z0"] + res["z_per_m"] * r))   # AP is flat between steps, so check
    assert residual < 0.4 * np.median(np.abs(bias(r)))                        # the bias left, not the exact scalars
    fixed = zcalib.apply(preds, {"pedestrian": {"z0": res["z0"], "z_per_m": res["z_per_m"]}})
    after = evalap.evaluate(fixed, gts, ["pedestrian"])["per_class"]["pedestrian"]["3d@0.7"]["AP_R40"]
    assert after == pytest.approx(res["ap_best"], abs=1e-6)
    d0 = next(d for d in preds["f000"] if d["class"] == "vehicle") if any(d["class"] == "vehicle" for d in preds["f000"]) else None
    if d0 is not None:                                                    # other classes untouched
        assert next(d for d in fixed["f000"] if d["class"] == "vehicle")["box"] == d0["box"]


def test_box_errors_and_breakdowns():
    preds, gts = _toy(3, noise=0.0, z_bias=lambda r: 0.2)
    pairs = dg.matched_pairs(preds, gts, "pedestrian", score_min=0.3)
    err = dg.box_errors(pairs)
    assert len(err["dz"]) > 20 and np.allclose(err["dz"], 0.2, atol=0.02) and np.allclose(err["dh"], 0, atol=0.2)
    tab = dg.error_table(err, [0, 10, 20, 30])
    assert tab["all"]["dz"]["median"] == pytest.approx(0.2, abs=0.02)
    apr = dg.ap_by_range(preds, gts, ["pedestrian"], [0, 20])
    assert set(apr["pedestrian"]) == {"0-20", "20-inf"}
    pts = {fid: np.concatenate([np.random.default_rng(0).uniform(b[:3] - b[3:6] / 3, b[:3] + b[3:6] / 3, (20, 3))
                                for b in g]) for fid, (g, _) in gts.items()}
    rec = dg.recall_by_points(preds, gts, lambda f: pts[f], ["pedestrian"], [1, 10, 30], score_min=0.3)
    assert rec["pedestrian"]["10-30"]["n_gt"] > 0 and rec["pedestrian"]["10-30"]["recall"] is not None


def test_registry_migration_adds_strategy(tmp_path):
    p = tmp_path / "registry.csv"
    old = ["time", "kind", "model", "run", "notes"]
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=old)
        w.writeheader()
        w.writerow({"time": "t", "kind": "eval", "model": "m1", "run": "r", "notes": "n, with comma"})
    assert registry.migrate(p, lambda r: "S1")
    rows = list(csv.DictReader(open(p)))
    assert list(rows[0]) == registry.FIELDS and rows[0]["strategy"] == "S1" and rows[0]["notes"] == "n, with comma"
    assert not registry.migrate(p, lambda r: "S1")                        # already current
