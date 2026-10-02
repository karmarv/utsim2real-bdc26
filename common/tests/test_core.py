"""Unit tests for the shared library. Synthetic fixtures only: no real labeled frame is used."""
import json
import zipfile

import numpy as np
import pytest

from bdc26 import boxes as B
from bdc26 import evalap, frames, submit
from bdc26.classmap import map_lumpi_ids, map_ut, v2x_super_class
from bdc26.config import load_track
from bdc26.detect.postprocess import postprocess, rotated_nms
from bdc26.guard import ForbiddenFrameError, ForbiddenGuard
from bdc26.io import lumpi, v2x

V2X, LUMPI = load_track("v2x"), load_track("lumpi")


# ---------------------------------------------------------------- frames
def test_resample_masks_then_draws_exactly_n():
    rng = np.random.default_rng(0)
    pts = np.concatenate([rng.uniform(-60, 60, (70000, 3)), np.zeros((20000, 3))]).astype(np.float32)
    out = frames.resample(pts, 50000, rng, V2X.pc_range)
    assert out.shape == (50000, 3)
    assert frames.in_range_mask(out, V2X.pc_range).all()
    assert frames.null_mask(out).mean() > 0.2          # nulls at the origin are kept


def test_resample_with_replacement_when_short():
    rng = np.random.default_rng(0)
    out = frames.resample(np.ones((10, 3), np.float32), 50, rng, V2X.pc_range)
    assert out.shape == (50, 3)


def test_null_mask_ignores_intensity():
    p = np.array([[0, 0, 0, 3.0], [1, 0, 0, 0]], np.float32)
    assert frames.null_mask(p).tolist() == [True, False]


# ---------------------------------------------------------------- boxes
def test_points_in_rotated_box():
    box = np.array([[10, 0, 0, 4, 2, 2, np.pi / 2]])     # long axis along +y after rotation
    pts = np.array([[10, 1.8, 0], [11.8, 0, 0], [10, 0, 0.9]])
    assert B.points_in_boxes(pts, box).tolist() == [0, -1, 0]


def test_scale_actors_about_bottom_centre():
    box = np.array([[0, 0, 0.5, 2, 1, 1, 0.0]])          # bottom at z = 0
    pts = np.array([[0.9, 0, 0.9], [0.5, 0.2, 0.1], [1.2, 0, 0.5]], np.float32)   # last point is background
    owner = np.array([0, 0, -1])
    p2, b2, keep = B.scale_actors(pts, box, 1.5, owner)
    assert np.allclose(b2[0, 3:6], [3, 1.5, 1.5]) and np.isclose(b2[0, 2] - b2[0, 5] / 2, 0.0)
    assert np.allclose(p2[0], [1.35, 0, 1.35], atol=1e-5)
    assert keep.tolist() == [True, True, False]           # background point now inside the solid object


# ---------------------------------------------------------------- evaluation
def test_iou_identity_and_disjoint():
    a = np.array([[0, 0, 0, 4, 2, 1.5, 0.3]])
    assert np.isclose(evalap.iou_matrix(a, a)[0, 0], 1.0)
    b = a.copy(); b[0, 0] += 10
    assert evalap.iou_matrix(a, b)[0, 0] == 0.0


def test_iou_known_value():
    a = np.array([[0, 0, 0, 2, 2, 2, 0.0]]); b = np.array([[1, 0, 0, 2, 2, 2, 0.0]])
    assert np.isclose(evalap.iou_matrix(a, b)[0, 0], 1 / 3)
    assert np.isclose(evalap.iou_matrix(a, b, "bev")[0, 0], 1 / 3)


def _toy(n_frames=20, jitter=0.0, seed=0):
    rng = np.random.default_rng(seed)
    gts, preds = {}, {}
    for f in range(n_frames):
        g = np.array([[*rng.uniform(-30, 30, 2), -1.2, 4.5, 1.9, 1.6, rng.uniform(-3, 3)] for _ in range(5)])
        gts[str(f)] = (g, np.array(["vehicle"] * 5))
        p = g.copy(); p[:, :2] += rng.normal(0, jitter, (5, 2))
        preds[str(f)] = [{"box": b.tolist(), "score": float(s), "class": "vehicle"} for b, s in zip(p, rng.random(5))]
    return preds, gts


def test_ap_perfect_is_one_and_empty_class_excluded():
    preds, gts = _toy()
    r = evalap.evaluate(preds, gts, ["vehicle", "pedestrian", "truck"])
    assert np.isclose(r["per_class"]["vehicle"]["3d@0.5"]["AP_R40"], 1.0)
    assert r["per_class"]["pedestrian"]["3d@0.5"] is None
    assert np.isclose(r["mAP_3d_0.5_R40"], 1.0)


def test_adding_low_score_false_positives_never_lowers_ap():
    preds, gts = _toy(jitter=0.3)
    base = evalap.evaluate(preds, gts, ["vehicle"])["mAP_3d_0.5_R40"]
    for fid in preds:
        preds[fid] += [{"box": [50, 50, 0, 4, 2, 1.5, 0], "score": 1e-4, "class": "vehicle"}] * 3
    assert evalap.evaluate(preds, gts, ["vehicle"])["mAP_3d_0.5_R40"] >= base - 1e-12


def test_nms_and_postprocess():
    b = np.array([[0, 0, 0, 1, 1, 1.7, 0], [0.05, 0, 0, 1, 1, 1.7, 0], [3, 0, 0, 1, 1, 1.7, 0]])
    s = np.array([0.9, 0.8, 0.7])
    assert sorted(rotated_nms(b, s, 0.5).tolist()) == [0, 2]
    cfg = {"default": {"score_floor": 0.01, "nms_iou": 0.5}, "hedge": {"Car": ["Van", 0.3]}}
    out = postprocess(b, s, ["Car"] * 3, cfg)
    assert len([o for o in out if o["class"] == "Car"]) == 2 and len([o for o in out if o["class"] == "Van"]) == 2


# ---------------------------------------------------------------- class maps
def test_class_maps():
    assert map_ut(["Car", "Van", "Unknown", "Bicycle"], LUMPI).tolist() == ["Car", "Car", "Car", "Bicycle"]
    assert map_ut(["BicycleRider", "Van", "Bus"], V2X).tolist() == ["pedestrian", "truck", "truck"]
    assert map_lumpi_ids([0, 6, 7], LUMPI).tolist() == ["Person", "Van", "Unknown"]
    assert v2x_super_class("TrashCan", V2X) == "truck" and v2x_super_class("Barrier", V2X) == ""


# ---------------------------------------------------------------- guard
def test_lumpi_guard_blocks_window_and_forbidden(tmp_path):
    g = ForbiddenGuard(LUMPI, forbidden_ids=["006498", "008100"], log_path=tmp_path / "log.csv")
    assert g.is_blocked("Measurement4", 6450) and g.is_blocked("Measurement4", 8150)
    assert not g.is_blocked("Measurement4", 6399) and not g.is_blocked("Measurement5", 6498)
    with pytest.raises(ForbiddenFrameError):
        g.check("Measurement4", 7000, "test")
    assert g.filter([("Measurement5", 1), ("Measurement4", 7000)], "test") == [("Measurement5", 1)]
    assert (tmp_path / "log.csv").read_text().count("\n") == 2   # header + 1 allowed access


def test_v2x_guard_refuses_until_mapping_resolved(tmp_path):
    g = ForbiddenGuard(V2X, forbidden_ids=["10_000043"], id_mapping=None, log_path=tmp_path / "l.csv")
    g.id_mapping = None
    assert g.is_blocked("any_folder", 1)
    g2 = ForbiddenGuard(V2X, forbidden_ids=["10_000043"], id_mapping={"10": "scen_A"}, log_path=tmp_path / "l.csv")
    assert g2.is_blocked("scen_A", 43 + 20) and not g2.is_blocked("scen_A", 43 + 21) and not g2.is_blocked("scen_B", 43)


# ---------------------------------------------------------------- readers
def test_lumpi_ply_roundtrip():
    fields = [("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("time", "<u4"), ("id", "u1"), ("intensity", "u1"),
              ("ray", "u1"), ("azimuth", "<u2"), ("distance", "<u2")]
    v = np.zeros(3, dtype=fields); v["x"] = [1, 2, 3]; v["id"] = [34, 35, 36]
    header = ("ply\nformat binary_little_endian 1.0\nelement vertex 3\nproperty float x\nproperty float y\n"
              "property float z\nproperty uint time\nproperty uchar id\nproperty uchar intensity\nproperty uchar ray\n"
              "property ushort azimuth\nproperty ushort distance\nend_header\n").encode()
    r = lumpi.read_ply(header + v.tobytes())
    assert r["x"].tolist() == [1, 2, 3] and r["id"].tolist() == [34, 35, 36]


def test_lumpi_labels_guarded(tmp_path):
    rows = ["0.1,1,0,0,1,1,4,1,10,1,2,-1.2,4.5,1.9,1.6,0.1",      # frame 1 (allowed)
            "700.0,2,0,0,1,1,4,0,10,1,2,-1.2,0.8,0.7,1.8,0.0"]    # frame 7000 (blocked window)
    p = tmp_path / "Label.csv"; p.write_text("\n".join(rows) + "\n")
    g = ForbiddenGuard(LUMPI, forbidden_ids=["006498"], log_path=tmp_path / "log.csv")
    lab = lumpi.read_labels_guarded(p, "Measurement4", g, "test")
    assert lab.frame.tolist() == [1] and lab.class_id.tolist() == [1]


def test_v2x_box_transform_identity_pose():
    y = {"lidar_pose": [0, 0, 0, 0, 0, 0],
         "vehicles": {0: {"location": [10, 5, -1], "center": [0, 0, 0], "extent": [2, 1, 0.8],
                          "angle": [0, 90, 0], "obj_type": "Car", "attribute": ""}}}
    L = v2x.labels_in_sensor_frame(y, V2X)
    assert np.allclose(L.boxes[0], [10, 5, -1, 4, 2, 1.6, np.pi / 2]) and L.names[0] == "vehicle"


def test_v2x_box_transform_translated_rotated_pose():
    # sensor at (10, 0, 2) yawed 90 deg: a world point at (10, 5) is 5 m ahead of the sensor (+x)
    y = {"lidar_pose": [10, 0, 2, 0, 90, 0],
         "vehicles": {0: {"location": [10, 5, 1], "center": [0, 0, 0], "extent": [1, 1, 1],
                          "angle": [0, 90, 0], "obj_type": "Pedestrian", "attribute": ""}}}
    L = v2x.labels_in_sensor_frame(y, V2X)
    assert np.allclose(L.boxes[0, :3], [5, 0, -1], atol=1e-9) and np.isclose(L.boxes[0, 6], 0, atol=1e-9)


# ---------------------------------------------------------------- submission
def test_package_and_validate(tmp_path):
    rng = np.random.default_rng(0)
    syn = [rng.uniform(-30, 30, (50000, 3)).astype(np.float32) for _ in range(50)]
    preds = {"0_000001": [{"box": [1, 2, -1, 4, 2, 1.6, 0.1], "score": 0.9, "class": "vehicle"}], "0_000002": []}
    z = submit.package(tmp_path / "sub", preds, syn, V2X, meta={"model": "toy"}, test_ids=list(preds))
    errors, info = submit.validate(z, V2X, list(preds))
    assert errors == [] and info["n_boxes"] == 1
    m = json.loads((tmp_path / "sub" / "manifest.json").read_text())
    assert m["validation_errors"] == [] and m["track"] == "v2x-track"
    with zipfile.ZipFile(z) as zz:
        assert len([n for n in zz.namelist() if n.startswith("synthetic/")]) == 50


def test_validate_rejects_nx4_ambiguity(tmp_path):
    zp = tmp_path / "bad.zip"
    with zipfile.ZipFile(zp, "w") as z:
        for i in range(50):
            z.writestr(f"synthetic/{i:04d}.bin", np.zeros((1000, 4), np.float32).tobytes())   # 16000 bytes: N x 4, not N x 3
        z.writestr("predictions.json", "{}")
        z.writestr("declaration.txt", submit.DECLARATION)
    errors, _ = submit.validate(zp, V2X)
    assert any("multiple of 12" in e for e in errors)


# ---------------------------------------------------------------- realism
def test_realism_normalization_reproduces_leaderboard():
    from bdc26 import realism
    _, R = realism.normalize({"CD": 2.0307, "MMD": 1.4558e-3, "EMD": 1.3815, "FPD": 0.9705})   # ECCV V2X winner
    assert abs(realism.combined(0.4382, R) - 0.7457) < 2e-4


def test_realism_score_runs():
    pytest.importorskip("ot")
    from bdc26 import realism
    rng = np.random.default_rng(0)
    frames_ = [rng.uniform(-30, 30, (2000, 3)).astype(np.float32) for _ in range(50)]
    out = realism.score(frames_, frames_, "v2x", exact_emd=False)
    assert 0.0 <= out["R"] <= 1.0 and out["CD"] >= 0


def test_v2x_guard_wildcard_for_unresolved_index(tmp_path):
    g = ForbiddenGuard(V2X, forbidden_ids=["10_000043", "17_000100"], id_mapping={"10": "scen_A"}, log_path=tmp_path / "l.csv")
    assert g.is_blocked("scen_A", 43) and not g.is_blocked("scen_B", 43)
    assert g.is_blocked("scen_B", 100) and g.is_blocked("scen_A", 110)     # index 17 unresolved -> every folder
