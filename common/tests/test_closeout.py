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
    assert sc.combined_estimate(0.77, 0.9) == pytest.approx(0.96) and sc.combined_estimate(0.77, 0.9, clip=False) == pytest.approx(0.6 * 1.1 + 0.36)


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


def test_merge_route_keeps_each_class_from_its_member():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import route_predictions as rp
    a = {"f1": [{"box": [0] * 7, "score": 0.9, "class": "pedestrian"}, {"box": [1] * 7, "score": 0.8, "class": "vehicle"}]}
    b = {"f1": [{"box": [2] * 7, "score": 0.7, "class": "pedestrian"}], "f2": [{"box": [3] * 7, "score": 0.6, "class": "truck"}]}
    out = rp.merge_route({"pedestrian": "b", "vehicle": "a", "truck": "b"}, {"a": a, "b": b})
    assert [d["box"][0] for d in out["f1"]] == [1, 2] and [d["class"] for d in out["f2"]] == ["truck"]


def test_upload_copy_is_track_prefixed_and_identical(tmp_path):
    import hashlib
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import package_submission as ps
    z = tmp_path / "submission.zip"
    z.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    (tmp_path / "manifest.json").write_text("{}")
    up = ps.upload_copy(z, V2X, {"strategy": "S1+C1"})
    assert up.name == "v2x_s1-c1_submission.zip" and up.read_bytes() == z.read_bytes()
    man = json.loads((tmp_path / "manifest.json").read_text())
    assert man["upload_file"] == {"name": up.name, "md5": hashlib.md5(z.read_bytes()).hexdigest()}
    assert ps.upload_copy(z, load_track("lumpi"), {"strategy": "S2"}).name == "lumpi_s2_submission.zip"
    assert ps.upload_copy(z, V2X, {"strategy": "S6"}, "s6b").name == "v2x_s6b_submission.zip"   # a variant of S6
    assert ps.upload_copy(z, V2X, {"strategy": "S6"}, "s6").name == "v2x_s6_submission.zip"
    assert ps.upload_copy(z, V2X, {"strategy": "S1"}, "first").name == "v2x_s1_submission.zip"


def test_centerhead_targets_keep_class_labels():
    """OpenPCDet CenterHead.assign_targets relabels boxes in place across head groups; bdc26 patches it."""
    torch = pytest.importorskip("torch")
    pytest.importorskip("pcdet")
    from easydict import EasyDict
    from bdc26.detect.pcdet_dataset import register
    from pcdet.models.dense_heads.center_head import CenterHead
    register()
    cfg = EasyDict({"CLASS_AGNOSTIC": False, "CLASS_NAMES_EACH_HEAD": [["pedestrian"], ["vehicle"], ["truck"]],
                    "SHARED_CONV_CHANNEL": 8, "USE_BIAS_BEFORE_NORM": True, "NUM_HM_CONV": 2,
                    "SEPARATE_HEAD_CFG": {"HEAD_ORDER": ["center", "center_z", "dim", "rot"],
                                          "HEAD_DICT": {"center": {"out_channels": 2, "num_conv": 2}, "center_z": {"out_channels": 1, "num_conv": 2},
                                                        "dim": {"out_channels": 3, "num_conv": 2}, "rot": {"out_channels": 2, "num_conv": 2}}},
                    "TARGET_ASSIGNER_CONFIG": {"FEATURE_MAP_STRIDE": 8, "NUM_MAX_OBJS": 50, "GAUSSIAN_OVERLAP": 0.1, "MIN_RADIUS": 2},
                    "LOSS_CONFIG": {"LOSS_WEIGHTS": {"cls_weight": 1.0, "loc_weight": 2.0, "code_weights": [1.0] * 8}},
                    "POST_PROCESSING": {"SCORE_THRESH": 0.1, "POST_CENTER_LIMIT_RANGE": [-40, -40, -8, 40, 40, 2], "MAX_OBJ_PER_SAMPLE": 50,
                                        "NMS_CONFIG": {"NMS_TYPE": "nms_gpu", "NMS_THRESH": 0.9, "NMS_PRE_MAXSIZE": 100, "NMS_POST_MAXSIZE": 50}}})
    head = CenterHead(cfg, input_channels=16, num_class=3, class_names=["vehicle", "pedestrian", "truck"],
                      grid_size=np.array([800, 800, 40]), point_cloud_range=np.array([-40, -40, -8, 40, 40, 2.0]),
                      voxel_size=[0.1, 0.1, 0.25], predict_boxes_when_training=False)
    gt = torch.tensor([[[10.0, 0, -1, 4.5, 1.9, 1.6, 0, 1], [-10.0, 0, -1, 0.7, 0.7, 1.7, 0, 2], [0, 20.0, -1, 8, 2.5, 3, 0, 3]]])
    t = head.assign_targets(gt.clone(), feature_map_size=[100, 100])
    ped, veh, trk = (t["heatmaps"][k][0, 0] for k in range(3))
    assert float(veh[50, 37]) == 0.0 and float(veh[50, 62]) == 1.0      # no vehicle target at the pedestrian
    assert float(ped[50, 37]) == 1.0 and float(ped[50, 62]) == 0.0
    assert float(trk[75, 50]) == 1.0 and float(trk[50, 37]) == 0.0
    gt2 = gt.clone()
    head.assign_targets(gt2, feature_map_size=[100, 100])
    assert torch.equal(gt2, gt)                                            # the caller's labels are untouched


def test_tta_views_invert_exactly_and_keep_points_in_boxes():
    from bdc26.boxes import points_in_boxes
    from bdc26.detect import tta
    rng = np.random.default_rng(5)
    boxes = np.c_[rng.uniform(-30, 30, (20, 2)), rng.uniform(-2, 0, 20), rng.uniform(0.5, 6, (20, 3)), rng.uniform(-np.pi, np.pi, 20)]
    pts = np.concatenate([b[:3] + rng.uniform(-0.3, 0.3, (30, 3)) * b[3:6] for b in boxes]).astype(np.float32)
    inside = points_in_boxes(pts, boxes)
    for v in tta.parse("flip4+yaw+z"):
        back = tta.inverse_boxes(tta.forward_boxes(boxes, v), v)
        d = back - boxes
        d[:, 6] = (d[:, 6] + np.pi) % (2 * np.pi) - np.pi
        assert np.abs(d).max() < 1e-9, v
        assert np.array_equal(points_in_boxes(tta.forward_points(pts, v), tta.forward_boxes(boxes, v)), inside), v
    assert [v.name for v in tta.parse("flip4")] == ["id", "fx", "fy", "fxy"]


def test_wbf_merges_agreeing_sources_and_demotes_lonely_boxes():
    from bdc26.detect.fusion import fuse_dets, wbf
    a = [1.0, 2.0, -1.0, 4.0, 2.0, 1.5, 0.3]
    b = [1.1, 2.0, -1.1, 4.2, 2.0, 1.5, 0.3]
    lonely = [20.0, 5.0, -1.0, 0.7, 0.7, 1.7, 0.0]
    fb, fs, n = wbf(np.array([a, b, lonely]), np.array([0.8, 0.6, 0.9]), np.array([0, 1, 0]), 2, 0.5)
    order = np.argsort(-fs)
    assert len(fb) == 2 and n[order[0]] == 2                      # the two agreeing boxes became one cluster
    assert fs[order[0]] == pytest.approx(0.7) and fs[order[1]] == pytest.approx(0.45)
    assert fb[order[0]][0] == pytest.approx((1.0 * 0.8 + 1.1 * 0.6) / 1.4)
    out = fuse_dets([[{"box": a, "score": 0.8, "class": "vehicle"}], [{"box": b, "score": 0.6, "class": "vehicle"}]], 0.5, [1.0, 0.5])
    assert len(out) == 1 and out[0]["score"] == pytest.approx((0.8 + 0.5 * 0.6) / 1.5)


def test_merge_card_fuses_listed_classes_with_member_calibration():
    """Classes in `fusion` come from the fused members (each with its own z calibration), the others from the route."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import route_predictions as rp
    ped = lambda x, z, s: {"box": [x, 0.0, z, 0.8, 0.8, 1.7, 0.0], "score": s, "class": "pedestrian"}
    a = {"f1": [ped(10.0, 0.0, 0.8), {"box": [5.0, 5.0, 0.0, 4.0, 2.0, 1.5, 0.0], "score": 0.9, "class": "vehicle"}]}
    b = {"f1": [ped(10.0, 0.5, 0.6), ped(30.0, 0.0, 0.5)]}
    card = {"route": {"pedestrian": "a", "vehicle": "a"},
            "fusion": {"pedestrian": {"members": ["a", "b"], "weights": [1.0, 1.0], "iou": 0.3,
                                      "calibration": {"b": {"z0": -0.5, "z_per_m": 0.0}}}}}
    assert rp.used_members(card) == ["a", "b"]
    out = rp.merge_card(card, {"a": a, "b": b})["f1"]
    peds = sorted((d for d in out if d["class"] == "pedestrian"), key=lambda d: d["box"][0])
    assert [d["class"] for d in out].count("vehicle") == 1 and len(peds) == 2
    assert peds[0]["score"] == pytest.approx(0.7) and peds[0]["box"][2] == pytest.approx(0.0)   # b's z calibrated onto a's
    assert peds[1]["score"] == pytest.approx(0.25)                                              # only b saw it


def test_static_fp_share_separates_repeating_structures_from_moving_errors():
    gt = (np.array([[0.0, 0.0, 0.0, 0.8, 0.8, 1.7, 0.0]]), np.array(["pedestrian"]))
    ped = lambda x, y: {"box": [x, y, 0.0, 0.8, 0.8, 1.7, 0.0], "score": 0.9, "class": "pedestrian"}
    gts = {f"s__{k:06d}": gt for k in range(10)}
    preds = {f: [ped(0.0, 0.0), ped(20.0, 5.0), ped(-10.0 + 3 * k, 8.0)] for k, f in enumerate(gts)}  # TP, pole, mover
    r = dg.static_fp_share(preds, gts, "pedestrian")
    assert r["unmatched_per_frame"] == 2 and r["static_per_frame"] == 1 and r["static_share"] == pytest.approx(0.5)


def test_budget_floor_ap_equals_ap_of_truncated_flags():
    """Greedy matching runs in score order, so removing boxes below a floor never changes the matches above it:
    the official AP of the filtered predictions equals the AP of the truncated flags (route_predictions budget)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import route_predictions as rp
    preds, gts = _toy(seed=3, spurious=8)
    fl = sc.frame_flags(preds, gts, ["pedestrian"])["pedestrian"]
    for floor in (0.2, 0.45):
        kept = rp.apply_budget(preds, {"pedestrian": floor})
        official = evalap.evaluate(kept, gts, ["pedestrian"])["per_class"]["pedestrian"]["3d@0.5"]["AP_R40"]
        tr = [{"n_gt": r["n_gt"], "scores": r["scores"][r["scores"] >= floor], "3d@0.5": r["3d@0.5"][r["scores"] >= floor]} for r in fl]
        assert sc.ap_from_flags(tr, "3d@0.5") == pytest.approx(official, abs=1e-9)
        assert all(d["score"] >= floor for v in kept.values() for d in v if d["class"] == "pedestrian")


def test_two_stage_score_blend():
    """S4: final score = stage1^a x stage2^(1-a); a = 0 is OpenPCDet's IoU score; padded proposals score 0."""
    torch = pytest.importorskip("torch")
    from bdc26.detect.pcdet_patches import blend_scores
    roi = torch.tensor([[0.81, 0.25, 0.0]])
    logit = torch.logit(torch.tensor([[[0.64], [0.36], [0.9]]]))
    half = blend_scores(roi, logit, 0.5).squeeze(-1)[0]
    assert torch.allclose(half, torch.tensor([0.72, 0.30, 0.0]), atol=1e-6)
    assert torch.allclose(blend_scores(roi, logit, 0.0).squeeze(-1)[0], torch.tensor([0.64, 0.36, 0.0]), atol=1e-6)
    assert torch.allclose(blend_scores(roi, logit, 1.0).squeeze(-1)[0], torch.tensor([0.81, 0.25, 0.0]), atol=1e-6)
    per_class = blend_scores(roi, logit, [1.0, 0.5], torch.tensor([[1, 2, 2]])).squeeze(-1)[0]   # class 1: a=1, class 2: a=0.5
    assert torch.allclose(per_class, torch.tensor([0.81, 0.30, 0.0]), atol=1e-6)


def test_ap_loss_decomposition_separates_localization_ranking_and_misses():
    preds, gts = _toy(seed=5, noise=0.0, spurious=1)          # spurious=1: no spurious boxes
    exact = dg.ap_loss_decomposition(preds, gts, "pedestrian")
    assert exact["AP_3d50"] == pytest.approx(exact["oracle25"]) and exact["loss_localization"] == pytest.approx(0.0)
    off = {f: [{**d, "box": [d["box"][0] + 0.2, *d["box"][1:]]} for d in v] for f, v in preds.items()}  # 0.2 m shift
    r = dg.ap_loss_decomposition(off, gts, "pedestrian")
    assert r["AP_3d50"] < 0.2 and r["AP_3d25"] == pytest.approx(exact["AP_3d25"]) and r["loss_localization"] > 0.5
    assert r["loss_miss"] == pytest.approx(exact["loss_miss"]) and r["loss_miss"] > 0.05      # 15% of objects never predicted
    official = evalap.evaluate(off, gts, ["pedestrian"])["per_class"]["pedestrian"]["3d@0.5"]["AP_R40"]
    assert r["AP_3d50"] == pytest.approx(official, abs=1e-6)


def test_gblobs_voxel_and_cell_match_numpy():
    """S5: the published voxel covariance and the bdc26 cell covariance against numpy (ddof=1), offsets, width 12."""
    torch = pytest.importorskip("torch")
    from bdc26.detect.gblobs_vfe import gblobs_cell, gblobs_voxel
    vs, pcr = [0.1, 0.1, 0.25], [-40.0, -40.0, -8.0, 40.0, 40.0, 2.0]
    rng = np.random.default_rng(0)
    coords = torch.tensor([[0, 30, 400, 400], [0, 30, 400, 401], [0, 31, 401, 403], [0, 30, 404, 400]], dtype=torch.int32)
    centres = np.array([[(c[3] + 0.5) * vs[0] + pcr[0], (c[2] + 0.5) * vs[1] + pcr[1], (c[1] + 0.5) * vs[2] + pcr[2]] for c in coords.numpy()])
    counts = [4, 3, 1, 2]
    vox = np.zeros((4, 5, 3), dtype=np.float32)
    for k, n in enumerate(counts):
        vox[k, :n] = centres[k] + rng.uniform(-0.04, 0.04, (n, 3)) * np.array([1, 1, 2.5])
    V, N = torch.from_numpy(vox), torch.tensor(counts)
    fv = gblobs_voxel(V, N, coords, vs, pcr).numpy()
    assert fv.shape == (4, 12)
    for k, n in enumerate(counts):
        p = vox[k, :n].astype(np.float64)
        assert np.allclose(fv[k, :3], p.mean(0) - centres[k], atol=1e-5)
        assert np.allclose(fv[k, 3:].reshape(3, 3), np.cov(p.T, ddof=1) if n > 1 else 0.0, atol=1e-6)
    fc = gblobs_cell(V, N, coords, vs, pcr, factor=(4, 4, 2)).numpy()
    cell = np.concatenate([vox[k, :counts[k]] for k in (0, 1, 2)]).astype(np.float64)   # voxels 0-2 share cell (0,15,100,100)
    for k in (0, 1, 2):
        assert np.allclose(fc[k, 3:].reshape(3, 3), np.cov(cell.T, ddof=1), atol=1e-6)
    assert np.allclose(fc[3, 3:].reshape(3, 3), np.cov(vox[3, :2].astype(np.float64).T, ddof=1), atol=1e-6)  # alone in its cell
    assert np.allclose(fc[:, :3], fv[:, :3], atol=1e-6)


def test_object_scaling_keeps_points_in_box_and_bottom_on_ground():
    """S5 ROS: points stay inside the scaled box, the box bottom stays put, overlapping scales are skipped."""
    pytest.importorskip("pcdet")
    from bdc26.detect.augment import _points_in_box, object_scaling
    rng = np.random.RandomState(0)
    truck = np.array([10.0, 5.0, -0.5, 6.0, 2.5, 3.0, 0.6])
    car = np.array([30.0, -5.0, -1.0, 4.5, 2.0, 1.5, -1.2])
    pts = np.concatenate([truck[:3] + (rng.uniform(-0.5, 0.5, (300, 3)) * truck[3:6]) @ np.diag([1, 1, 1]),
                          rng.uniform(-40, 40, (200, 3))])
    # rotate the truck points into its heading
    c, s = np.cos(truck[6]), np.sin(truck[6]); d = pts[:300, :2] - truck[:2]
    pts[:300, :2] = truck[:2] + d @ np.array([[c, s], [-s, c]])
    inside = _points_in_box(pts, truck)
    cfg = {"PROB": 1.0, "DEFAULT": {"l": [1.0, 1.0], "w": [1.0, 1.0], "h": [1.0, 1.0]},
           "CLASS_RANGES": {"truck": {"l": [1.6, 1.6], "w": [1.2, 1.2], "h": [1.1, 1.1]}}}
    boxes, out = object_scaling(np.stack([truck, car]), ["truck", "vehicle"], pts, cfg, rng=np.random.RandomState(1))
    assert np.allclose(boxes[0, 3:6], truck[3:6] * [1.6, 1.2, 1.1])
    assert np.isclose(boxes[0, 2] - boxes[0, 5] / 2, truck[2] - truck[5] / 2)           # bottom unchanged
    assert _points_in_box(out[inside], boxes[0] + np.r_[0, 0, 0, 1e-6, 1e-6, 1e-6, 0]).all()
    assert np.allclose(out[~inside], pts[~inside]) and np.allclose(boxes[1], car)
    near = np.array([10.0, 9.0, -1.0, 4.5, 2.0, 1.5, 0.6])                              # a growing truck would hit it
    b2, _ = object_scaling(np.stack([truck, near]), ["truck", "vehicle"], pts, {**cfg, "CLASS_RANGES": {"truck": {"l": [3.0, 3.0], "w": [3.0, 3.0], "h": [1.0, 1.0]}}},
                           rng=np.random.RandomState(1))
    assert np.allclose(b2[0], truck)


def _toy_sensor():
    from bdc26.render.pedsim import Sensor
    return Sensor(np.eye(4), np.linspace(-15, 15, 31), 0.5, min_range=0.5, max_range=100.0)


def test_g2_mesh_insertion_occludes_and_hits_at_the_right_range():
    """R3: a box mesh in front of a wall removes the wall points behind it and returns points on its front face."""
    pytest.importorskip("open3d")
    from bdc26.render.g2 import MeshObj, box_mesh, insert_meshes, place_mesh
    from bdc26.render.pedsim import InsertParams
    s = _toy_sensor()
    yy, zz = np.meshgrid(np.linspace(-6, 6, 121), np.linspace(-2, 2, 41))
    wall = np.c_[np.full(yy.size, 10.0), yy.ravel(), zz.ravel()]
    V, F = box_mesh(1.0, 2.0, 2.0)
    ob = MeshObj(place_mesh(V, 5.0, 0.0, -1.0, 0.0), F, 0)
    p = InsertParams(drop_prob=0.0, range_noise=0.0)
    out, keep, oid, hits = insert_meshes(wall, np.zeros(len(wall), dtype=np.int64), [s], [ob], np.random.default_rng(0), p)
    behind = (np.abs(wall[:, 1]) < 0.9 * 2.0) & (np.abs(wall[:, 2]) < 0.9)           # well inside the shadow
    assert not keep[behind].any() and keep[np.abs(wall[:, 1]) > 3.0].all()
    new = out[oid == 0]
    assert hits[0] == len(new) > 20 and np.allclose(new[:, 0], 4.5, atol=0.02)          # the front face at x = 4.5


def test_g2_rider_and_hull_fit_their_boxes():
    from bdc26.render.g2 import hull_mesh, rider_mesh
    rng = np.random.default_rng(1)
    for kind, (l, w, h) in (("bicycle", (2.0, 0.85, 1.9)), ("motorcycle", (2.2, 0.9, 1.75))):
        V, F = rider_mesh(l, w, h, kind, rng)
        assert V[:, 2].min() >= -0.01 and V[:, 2].max() <= h + 0.01 and np.abs(V[:, 0]).max() <= l / 2 + 0.02
        assert np.abs(V[:, 1]).max() <= w / 2 + 0.05 and len(F) > 100
    pts = np.c_[rng.uniform(-2, 2, 300), rng.uniform(-0.8, 0.8, 300), rng.uniform(0, 1.5, 300)]
    V, F = hull_mesh(pts, (4.0, 1.6, 1.5), (12.0, 2.9, 3.3))
    assert np.allclose(V.max(0) - V.min(0), [12.0, 2.9, 3.3], atol=0.4)
    V2, _ = hull_mesh(pts[:5], (4.0, 1.6, 1.5), (4.5, 1.9, 1.6))                            # too few points: template
    assert np.allclose(V2.max(0) - V2.min(0), [4.5, 1.9, 1.6 * 0.84], atol=0.05)


def test_g2_pass_recasts_actors_and_keeps_clutter_off_labels():
    pytest.importorskip("open3d")
    from bdc26.render.g2 import G2Config, G2Pass
    from bdc26.render.pedsim import InsertParams
    rng = np.random.default_rng(2)
    ground = np.c_[rng.uniform(-30, 30, 20000), rng.uniform(-30, 30, 20000), np.full(20000, -2.0)]
    car = np.array([12.0, 0.0, -1.25, 4.5, 1.9, 1.5, 0.0])
    sparse = car[:3] + rng.uniform(-0.5, 0.5, (60, 3)) * car[3:6]                          # a sparse UT actor
    pts = np.concatenate([ground, sparse]); owner = np.r_[np.full(len(ground), -1), np.zeros(len(sparse), dtype=int)]
    cfg = G2Config(recast={"Car": "car"}, clutter_mean=15, params=InsertParams(drop_prob=0.0))
    g2 = G2Pass([_toy_sensor()], cfg, ground=lambda p, x, y: -2.0, pc_range=[-30, -30, -5, 30, 30, 5])
    out, boxes, names, st = g2(pts, car[None], np.array(["Car"], dtype=object), owner, np.random.default_rng(3))
    assert st["g2_recast"] == 1 and st["g2_clutter"] > 5 and np.allclose(boxes[0], car)
    from bdc26.boxes import count_points_in_boxes
    assert count_points_in_boxes(out, boxes)[0] > 0


def test_g2_occlusion_needs_every_candidate_sensor():
    """R3: a merged multi-lidar frame does not say which sensor saw a point; a point is removed only if the new
    object hides it from every sensor whose beam table fits it, and sensor_candidates falls back to all sensors."""
    pytest.importorskip("open3d")
    from bdc26.render.g2 import MeshObj, box_mesh, insert_meshes, place_mesh, sensor_candidates
    from bdc26.render.pedsim import InsertParams, Sensor
    a = _toy_sensor()
    T = np.eye(4); T[:3, 3] = [0.0, 8.0, 0.0]
    b = Sensor(T, np.linspace(-15, 15, 31), 0.5, min_range=0.5, max_range=100.0)
    yy, zz = np.meshgrid(np.linspace(-1.5, 1.5, 31), np.linspace(-0.8, 0.8, 17))
    wall = np.c_[np.full(yy.size, 10.0), yy.ravel(), zz.ravel()]                       # behind the box as seen from a
    V, F = box_mesh(1.0, 4.0, 3.0)
    ob = MeshObj(place_mesh(V, 5.0, 0.0, -1.5, 0.0), F, 0)
    p, rng = InsertParams(drop_prob=0.0, range_noise=0.0), np.random.default_rng(0)
    only_a = np.c_[np.ones(len(wall), bool), np.zeros(len(wall), bool)]
    _, keep_a, _, _ = insert_meshes(wall, only_a, [a, b], [ob], rng, p)
    _, keep_ab, _, _ = insert_meshes(wall, np.ones((len(wall), 2), bool), [a, b], [ob], rng, p)
    assert not keep_a.any() and keep_ab.all()                                           # b sees the wall past the box
    c = sensor_candidates(np.array([[10.0, 0.0, np.tan(np.radians(3.0)) * 10.0], [10.0, 0.0, np.tan(np.radians(3.5)) * 10.0]]), [a, b], 0.08)
    assert c[0, 0] and c[1].all()                                                      # on a's beam; fits none: all


def test_g2_hull_bank_completes_sparse_actors(tmp_path):
    from bdc26.render.g2 import HullBank, hull_mesh
    rng = np.random.default_rng(4)
    box = np.array([10.0, 2.0, -1.25, 4.5, 1.9, 1.5, 0.3])
    loc = np.c_[rng.uniform(-2.25, 2.25, 1500), rng.uniform(-0.95, 0.95, 1500), rng.uniform(0.0, 1.5, 1500)]
    c, s = np.cos(box[6]), np.sin(box[6])
    pts = np.c_[box[0] + c * loc[:, 0] - s * loc[:, 1], box[1] + s * loc[:, 0] + c * loc[:, 1], box[2] - box[5] / 2 + loc[:, 2]]
    bank = HullBank(["Car"], min_points=800)
    bank(pts, box[None], np.array(["Car"], dtype=object), np.zeros(len(pts), dtype=int), rng)
    bank.save(tmp_path / "bank.npz")
    bank = HullBank.load(tmp_path / "bank.npz")
    assert bank.summary() == {"Car": 1}
    ex = bank.sample("Car", (4.0, 1.8, 1.4), rng)
    assert np.allclose(ex.max(0) - ex.min(0), [4.0, 1.8, 1.4], atol=0.05)
    side = np.c_[rng.uniform(-2, 2, 60), rng.uniform(0.5, 0.9, 60), rng.uniform(0.2, 1.4, 60)]  # one side seen only
    Vs, _ = hull_mesh(side, (4.0, 1.8, 1.4), (4.0, 1.8, 1.4), mirror=False)
    Vc, _ = hull_mesh(side, (4.0, 1.8, 1.4), (4.0, 1.8, 1.4), exemplar=ex)
    assert np.ptp(Vs[:, 1]) < 0.5 and np.ptp(Vc[:, 1]) > 1.7


def test_g2_drop_ramp_follows_hit_range():
    pytest.importorskip("open3d")
    from bdc26.render.g2 import MeshObj, _drop_ramp, box_mesh, insert_meshes, place_mesh
    from bdc26.render.pedsim import InsertParams
    assert _drop_ramp(0.1) == (0.1, 0.1, 0.0, 1.0) and _drop_ramp([0.2, 0.0, 15, 25]) == (0.2, 0.0, 15.0, 25.0)
    V, F = box_mesh(1.0, 1.2, 1.2)
    p = InsertParams(drop_prob=0.0, range_noise=0.0)
    full = insert_meshes(np.zeros((0, 3)), np.zeros(0, np.int64), [_toy_sensor()], [MeshObj(place_mesh(V, 5.0, 0, -0.6, 0), F, 0)], np.random.default_rng(0), p)[3][0]
    ramp = insert_meshes(np.zeros((0, 3)), np.zeros(0, np.int64), [_toy_sensor()],
                         [MeshObj(place_mesh(V, 5.0, 0, -0.6, 0), F, 0, (1.0, 0.0, 4.0, 6.0))], np.random.default_rng(0), p)[3][0]
    assert full > 100 and 0.18 < ramp / full < 0.36                  # front face at 4.5-4.6 m: drop about 0.72


def test_resample_calibrated_keeps_the_reference_object_rate():
    from bdc26.density import resample_calibrated
    rng = np.random.default_rng(5)
    pts = rng.uniform(-10, 10, (10000, 3)).astype(np.float32)
    obj = np.zeros(len(pts), bool); obj[:1000] = True
    rng_range = [-20, -20, -20, 20, 20, 20]
    out_n = resample_calibrated(pts, 1000, np.random.default_rng(6), rng_range, None, obj)
    out_r = resample_calibrated(pts, 1000, np.random.default_rng(6), rng_range, None, obj, n_ref=20000)
    k = lambda o: (o[:, None, :] == pts[None, :1000, :]).all(2).any(1).sum()
    assert len(out_n) == len(out_r) == 1000 and 80 < k(out_n) < 120 and 35 < k(out_r) < 65


def test_pooled_gate_needs_a_gain_on_both_splits_together():
    """R3 class-gate condition: a B-only gain that A loses back does not pass on the pooled A+B frames."""
    def spurious(preds, gts, f):
        return {fid: [dict(d, score=min(1.0, d["score"] * f)) if d["box"][3] < 1 and
                      not any(np.hypot(d["box"][0] - g[0], d["box"][1] - g[1]) < 0.5 for g in gts[fid][0]) else d
                      for d in dets] for fid, dets in preds.items()}
    c = "pedestrian"
    (pa, ga), (pb, gb) = _toy(1, n_frames=60, spurious=8), _toy(2, n_frames=60, spurious=8)
    base = {"val": sc.frame_flags(pa, ga, [c])[c], "valB": sc.frame_flags(pb, gb, [c])[c]}
    both = {"val": sc.frame_flags(spurious(pa, ga, 0.1), ga, [c])[c], "valB": sc.frame_flags(spurious(pb, gb, 0.1), gb, [c])[c]}
    b_only = {"val": sc.frame_flags(spurious(pa, ga, 3.0), ga, [c])[c], "valB": both["valB"]}
    g1 = sc.pooled_gate(base, both, c, n=100)
    g2 = sc.pooled_gate(base, b_only, c, n=100)
    assert g1["ok"] and g1["delta"] > 0.01 and g1["p_gain"] >= 0.9
    assert not g2["ok"] and g2["delta"] < 0


def test_g2_fit_box_shortens_real_sizes_to_the_free_road():
    """R3: a real-size sample longer than the room in a queue is shortened (never below the UT length) and placed
    clear of the neighbours; with room it keeps the full sample."""
    from bdc26.render.g2 import G2Config, G2Pass
    from bdc26.render.pedsim import bev_overlaps
    truck = np.array([0.0, 0.0, -0.5, 8.0, 2.5, 3.0, 0.0])
    ahead = np.array([10.0, 0.0, -1.2, 4.5, 1.9, 1.5, 0.0])                  # 5.75 m of road ahead of the truck's front
    behind = np.array([-9.0, 0.0, -1.2, 4.5, 1.9, 1.5, 0.0])                 # 2.75 m behind its rear
    g2 = G2Pass([], G2Config(resize={"Truck": np.array([[16.0, 2.5, 3.0]])}), ground=None, pc_range=[-50, -50, -5, 50, 50, 5])
    boxes = np.stack([truck, ahead, behind])
    rng = np.random.default_rng(0)
    nb, t, grown = g2._fit_box(0, truck, "Truck", boxes, rng)
    assert grown and 8.0 < nb[3] < 14.5 and not bev_overlaps(nb, boxes[1:], 0.1)
    assert np.isclose(nb[2] - nb[5] / 2, truck[2] - truck[5] / 2, atol=0.2)  # still on the ground
    nb2, _, _ = g2._fit_box(0, truck, "Truck", truck[None], rng)              # free road: the whole sample
    assert 15.0 < nb2[3] < 16.6


def test_object_scaling_never_exceeds_the_class_maximum():
    """R3: CLASS_MAX caps scaled sizes at the real maximum; a box already beyond it keeps its size (never shrunk by the cap)."""
    pytest.importorskip("pcdet")
    from bdc26.detect.augment import object_scaling
    rng = np.random.RandomState(0)
    boxes = np.array([[0.0, 0.0, -0.5, 12.0, 2.5, 3.0, 0.0], [30.0, 0.0, -0.5, 15.0, 2.5, 3.0, 0.0], [0.0, 20.0, -0.5, 6.0, 2.5, 3.0, 0.0]])
    pts = np.zeros((1, 3))
    cfg = {"PROB": 1.0, "CLASS_RANGES": {"truck": {"l": [1.4, 1.4], "w": [1.0, 1.0], "h": [1.0, 1.0]}}, "CLASS_MAX": {"truck": [13.4, 3.2, 3.9]}}
    nb, _ = object_scaling(boxes, np.array(["truck"] * 3), pts, cfg, rng)
    assert np.isclose(nb[0, 3], 13.4) and np.isclose(nb[1, 3], 15.0) and np.isclose(nb[2, 3], 8.4)
