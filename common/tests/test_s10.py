"""S10 Clean Final: statistical normalization in bdc_object_scaling, the range-jitter augmentation and the clean-member
check (docs/decisions/2026-11-08-s10-clean-final-plan.md)."""
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common"))
sys.path.insert(0, str(REPO / "common" / "tools"))

from bdc26.detect.augment import object_scaling, range_jitter  # noqa: E402


def test_class_center_scales_to_the_target_about_the_bottom():
    boxes = np.array([[2.0, 1.0, 0.75, 4.0, 2.0, 1.5, 0.3]])
    pts = np.array([[2.0, 1.0, 0.0], [2.0, 1.0, 1.5], [2.5, 1.2, 0.7]], dtype=np.float32)
    cfg = {"PROB": 0.0, "DEFAULT": {"l": [1.0, 1.0], "w": [1.0, 1.0], "h": [1.0, 1.0]},
           "CLASS_CENTER": {"Car": [0.9, 1.1, 1.2]}, "CLASS_PROB": {"Car": 1.0}}
    b, p = object_scaling(boxes, np.array(["Car"]), pts, cfg, rng=np.random.RandomState(0))
    assert np.allclose(b[0, 3:6], [3.6, 2.2, 1.8])
    assert np.isclose(b[0, 2] - b[0, 5] / 2, 0.0)                # the bottom stays on the ground
    assert np.allclose(p[0], [2.0, 1.0, 0.0]) and np.allclose(p[1], [2.0, 1.0, 1.8], atol=1e-5)


def test_class_prob_zero_and_unlisted_classes_keep_the_old_draws():
    boxes = np.array([[0.0, 0.0, 0.9, 0.7, 0.7, 1.8, 0.0], [10.0, 0.0, 0.8, 4.5, 1.9, 1.6, 0.0]])
    pts = np.zeros((0, 3), dtype=np.float32)
    names = np.array(["Person", "Car"])
    base = {"PROB": 1.0, "DEFAULT": {"l": [0.9, 1.1], "w": [0.9, 1.1], "h": [0.95, 1.05]}}
    b0, _ = object_scaling(boxes, names, pts, base, rng=np.random.RandomState(3))
    b1, _ = object_scaling(boxes, names, pts, {**base, "CLASS_CENTER": {"Bus": [2.0, 2.0, 2.0]}}, rng=np.random.RandomState(3))
    assert np.allclose(b0, b1)                                   # same random stream without a listed class present
    b2, _ = object_scaling(boxes, names, pts, {**base, "CLASS_PROB": {"Person": 0.0}}, rng=np.random.RandomState(3))
    assert np.allclose(b2[0], boxes[0])


def test_range_jitter_moves_points_along_their_rays_only():
    rng = np.random.RandomState(1)
    pts = np.concatenate([rng.uniform(-30, 30, (5000, 3)), np.zeros((10, 3))]).astype(np.float32)
    out = range_jitter(pts, {"SIGMA": 0.02, "SENSORS": [[0.0, 0.0, 0.0]]}, rng=np.random.RandomState(2))
    d = (out - pts).astype(np.float64)
    assert np.allclose(out[-10:], 0.0)                           # zero padding untouched
    cross = np.linalg.norm(np.cross(d[:-10], pts[:-10].astype(np.float64)), axis=1) / np.linalg.norm(pts[:-10], axis=1)
    assert cross.max() < 1e-3                                    # no move across the ray
    unit = pts[:-10].astype(np.float64) / np.linalg.norm(pts[:-10], axis=1)[:, None]
    step = (d[:-10] * unit).sum(1)                               # signed move along the ray
    assert abs(step.mean()) < 0.002 and 0.018 < step.std() < 0.022


def test_range_jitter_uses_the_nearest_sensor_in_bev():
    sensors = [[0.0, 0.0, 0.0], [100.0, 0.0, 5.0]]
    pts = np.array([[99.0, 1.0, 0.0]], dtype=np.float32)
    out = range_jitter(pts, {"SIGMA": 0.5, "SENSORS": sensors}, rng=np.random.RandomState(0))
    ray = pts[0] - np.array(sensors[1], dtype=np.float32)
    assert np.linalg.norm(np.cross(out[0] - pts[0], ray)) < 1e-4


def test_clean_check_reads_the_corpus_cards(tmp_path, monkeypatch):
    import clean_check as cc

    def card(name, **kw):
        (tmp_path / name).mkdir()
        (tmp_path / name / "dataset.yaml").write_text(yaml.safe_dump(kw))
    card("ut", source="UT-LUMPI (doi, CC0)")
    card("old", source="UT + G1", real_data_use="legal M4 Person label rows (placement, box sizes)", params={"persons": 16.0})
    card("v6", source="UT + G1", real_data_use="walker box mixture and range histogram as scalars",
         params={"persons": 16.0, "g2": True, "v6": {"placement": "map", "clutter_anchors": "map"}})
    card("v6clutter", source="UT + G1", real_data_use="scalars", params={"g2": True, "v6": {"placement": "map"}})
    card("union", source="union", parts=[{"data": "v6"}, {"data": "ut"}])
    card("badunion", source="union", parts=[{"data": "v6"}, {"data": "old"}])
    monkeypatch.setattr(cc, "data_path", lambda track, corpus: tmp_path / corpus)
    ok = {c: cc.corpus_status(None, c)[0] for c in ("ut", "old", "v6", "v6clutter", "union", "badunion", "missing")}
    assert ok == {"ut": True, "old": False, "v6": True, "v6clutter": False, "union": True, "badunion": False, "missing": False}


def test_overhead_demotion_ranks_boxes_with_points_above_last():
    from route_predictions import apply_overhead_demotion, merge_card, overhead_point_counts
    ped = lambda x, s: {"box": [x, 0.0, 0.9, 0.6, 0.6, 1.8, 0.0], "score": s, "class": "pedestrian"}
    preds = {"f": [ped(0.0, 0.9), ped(5.0, 0.8), ped(10.0, 0.3), {"box": [20.0, 0, 0.8, 4.5, 1.9, 1.6, 0], "score": 0.9, "class": "vehicle"}]}
    pole = np.array([[5.0, 0.0, z] for z in np.linspace(2.1, 3.5, 8)] + [[0.0, 2.0, 2.5]] + [[0.0, 0.0, 0.0]] * 3)
    counts = overhead_point_counts(preds, {"pedestrian"}, lambda f: pole)
    assert counts["f"].tolist() == [0, 8, 0, -1]                  # only the box under the pole; nulls and off-footprint skipped
    out = apply_overhead_demotion(preds, {"pedestrian": 5}, lambda f: pole)
    s = [d["score"] for d in out["f"]]
    assert s[0] == 0.9 and s[2] == 0.3 and s[3] == 0.9           # untouched
    assert s[1] < 0.3                                            # below every other pedestrian; nothing deleted
    assert apply_overhead_demotion(preds, {"pedestrian": 9}, lambda f: pole) == preds
    card = {"route": {"pedestrian": "a", "vehicle": "a"}, "overhead_demotion": {"pedestrian": 5}}
    assert merge_card(card, {"a": preds}, lambda f: pole)["f"][1]["score"] == s[1]


def test_class_config_carries_the_overhead_and_point_rescore_stages():
    from route_predictions import _class_config
    card = {"route": {"pedestrian": "a"}, "overhead_demotion": {"pedestrian": 5}, "point_rescore": {"pedestrian": 0.1}}
    cfg = _class_config(card, "pedestrian")
    assert cfg[6] == 5 and cfg[7] == 0.1 and cfg[8] is None and len(cfg) == 9


def test_gate_revert_restores_the_incumbents_size_entry():
    """C1 dry run (2026-11-09): a class reverted to C0's route must also get C0's size calibration back."""
    from route_predictions import _class_config, _restore_size_entry
    anc = [[1.0, 2.0]]
    inc = {"route": {"Person": "a", "Car": "b"},
           "size_calibration": {"anchors": anc, "classes": {"Person": {"dh": 0.03}, "Car": {"dl": -0.2, "dw": 0.08}}}}
    new = {"route": {"Person": "a", "Car": "b"}, "size_calibration": {"anchors": anc, "classes": {"Car": {"dl": -0.2, "dw": 0.04}}}}
    assert _class_config(new, "Person") != _class_config(inc, "Person")    # a size entry alone makes the class differ
    for c in ("Person", "Car"):
        _restore_size_entry(new, inc, c)
        assert _class_config(new, c) == _class_config(inc, c)
    _restore_size_entry(new, {"route": {}}, "Person")                      # an incumbent without one removes it
    assert "Person" not in new["size_calibration"]["classes"] and "Car" in new["size_calibration"]["classes"]
    other = {"size_calibration": {"anchors": [[0.0, 0.0]], "classes": {"Car": {"dh": 0.1}}}}
    with pytest.raises(SystemExit):                                         # never mixes two anchor sets
        _restore_size_entry(other, inc, "Person")


def test_point_rescore_favours_well_sampled_boxes_and_never_raises_a_score():
    from route_predictions import apply_point_rescore, merge_card
    pts = np.array([[0.0, 0.0, 0.5]] * 30 + [[10.0, 0.0, 0.5]] * 2 + [[0.0, 0.0, 0.0]] * 50)   # nulls are not counted
    box = lambda x: [x, 0.0, 0.5, 0.8, 0.8, 1.8, 0.0]
    preds = {"f": [{"box": box(0.0), "score": 0.5, "class": "Person"}, {"box": box(10.0), "score": 0.6, "class": "Person"},
                   {"box": box(20.0), "score": 0.9, "class": "Car"}]}
    out = apply_point_rescore(preds, {"Person": 0.5}, lambda f: pts)
    s = [d["score"] for d in out["f"]]
    assert s[0] == 0.5                                   # the best-sampled box of the class keeps its score
    assert s[1] < s[0] < 0.6                             # the 2-point box falls below the 30-point one; nothing rises
    assert s[2] == 0.9 and len(out["f"]) == 3            # other classes untouched; nothing deleted
    assert apply_point_rescore(preds, None) is preds
    card = {"route": {"Person": "a", "Car": "a"}, "point_rescore": {"Person": 0.5}}
    assert [d["score"] for d in merge_card(card, {"a": preds}, lambda f: pts)["f"]] == s


def _rec(fid, tp, n_gt):
    """One frame's record for one class: scores descending, true-positive flags at 3D@0.5."""
    tp = np.asarray(tp, dtype=bool)
    return {"fid": fid, "n_gt": n_gt, "scores": np.linspace(0.9, 0.5, len(tp)) if len(tp) else np.zeros(0), "3d@0.5": tp}


def test_frame_group_uses_scenarios_on_v2x_and_100s_windows_on_lumpi():
    from bdc26.scorecard import frame_group
    assert frame_group("Measurement4__001234", "lumpi-track") == "Measurement4:1"
    assert frame_group("Measurement6__012200", "lumpi-track") == "Measurement6:12"
    assert frame_group("2023-03-17-15-53-02_1_0__000005", "v2x-track") == "2023-03-17-15-53-02_1_0"


def test_grouped_bootstrap_and_leave_one_group_out_see_a_gain_carried_by_one_group():
    from bdc26.scorecard import grouped_bootstrap, leave_one_group_out
    groups = [g for g in "abcd" for _ in range(5)]
    fids = [f"{g}{i}" for i, g in enumerate(groups)]
    # a: one true and one false box per frame. b: the same, except group "a" where b's false box becomes true.
    fa = {"Car": [_rec(f, [True, False], 2) for f in fids]}
    fb = {"Car": [_rec(f, [True, g == "a"], 2) for f, g in zip(fids, groups)]}
    r = grouped_bootstrap(fa, fb, ["Car"], groups, n=300, seed=1)
    assert r["delta"] > 0 and r["n_groups"] == 4
    assert 0.5 < r["p_gain"] < 1.0                     # the resample misses group "a" about (3/4)^4 = 32% of the time
    logo = leave_one_group_out(fa, fb, ["Car"], groups)
    assert abs(logo["a"]) < 1e-12 and all(logo[g] > 0 for g in "bcd")


def test_static_blocks_stand_on_the_ground_and_never_cover_a_labeled_box():
    from bdc26.render.g2 import G2Config, G2Pass
    from bdc26.render.pedsim import Sensor
    cfg = G2Config(static_anchors=[(10.0, 0.0, 0.0, 2.0, 0.4, 1.2), (0.0, 12.0, 0.0, 0.3, 0.3, 3.0),
                                   (20.0, 0.0, 0.0, 1.0, 1.0, 1.0), (1.0, 1.0, 0.0, 1.0, 1.0, 1.0)])
    g = G2Pass(sensors=[Sensor(np.eye(4), [0.0], 0.2)], cfg=cfg, ground=lambda pts, x, y: -2.0, pc_range=[-40, -40, -5, 40, 40, 5])
    boxes = np.array([[20.0, 0.0, -1.2, 4.0, 2.0, 1.6, 0.0]])            # an actor at the third anchor
    out = g._static_blocks(np.zeros((0, 3)), boxes, np.random.default_rng(0))
    assert len(out) == 2                                                  # the actor's anchor and the one by the sensor skipped
    for V, F, keep in out:
        assert abs(V[:, 2].min() + 2.0) < 1e-6 and keep == 1.0           # base on the ground; uncalibrated anchors keep all
    assert {round(float(np.ptp(V[:, 2])), 3) for V, _, _ in out} == {1.2, 3.0}   # the wall-like box and the pole keep their heights


def test_calibrated_static_blocks_keep_their_share_of_returns():
    from bdc26.render.g2 import G2Config, G2Pass, thinned_drop
    from bdc26.render.pedsim import Sensor
    assert thinned_drop(0.0, 0.25) == (0.75, 0.75, 0.0, 1.0)
    dn, df, r0, r1 = thinned_drop((0.1, 0.5, 10.0, 50.0), 0.5)
    assert abs(dn - 0.55) < 1e-12 and abs(df - 0.75) < 1e-12 and (r0, r1) == (10.0, 50.0)
    cfg = G2Config(static_anchors=[(10.0, 0.0, 0.0, 2.0, 0.4, 1.2, 0.3)])
    g = G2Pass(sensors=[Sensor(np.eye(4), [0.0], 0.2)], cfg=cfg, ground=lambda pts, x, y: -2.0, pc_range=[-40, -40, -5, 40, 40, 5])
    (_, _, keep), = g._static_blocks(np.zeros((0, 3)), np.zeros((0, 7)), np.random.default_rng(0))
    assert keep == 0.3


def test_clean_check_blocks_r1_corpora_until_allowed(tmp_path, monkeypatch):
    import clean_check
    (tmp_path / "dataset.yaml").write_text(yaml.safe_dump({"real_data_use": "Measurement4 sensor metadata; S10 R1 static-block anchors",
                                                           "params": {"g2": True, "persons": 0,
                                                                      "v6": {"placement": "map", "clutter_anchors": "map",
                                                                             "static_anchors": "anchors.json"}}}))
    monkeypatch.setattr(clean_check, "data_path", lambda track, corpus: tmp_path)
    monkeypatch.delenv("BDC_ALLOW_R1", raising=False)
    ok, why = clean_check.corpus_status(None, "pcdet/g1-r1")
    assert not ok and "question (c)" in why
    monkeypatch.setenv("BDC_ALLOW_R1", "1")
    assert clean_check.corpus_status(None, "pcdet/g1-r1")[0]


def test_final_gate_waives_the_route_bar_only_for_stage_changes():
    """R5 and rule 11: a class whose only change is a post-processing stage is not held to R3's +0.01 bar."""
    from route_predictions import _class_config, _only_stage_change
    inc = {"route": {"pedestrian": "a"}, "fusion": {"pedestrian": {"members": ["a", "b"], "iou": 0.5}}}
    v5 = {**inc, "overhead_demotion": {"pedestrian": 5}}
    rs = {**inc, "point_rescore": {"pedestrian": 0.1}, "tail_copies": {"pedestrian": {"r": 0.15, "n": 4}}}
    moved = {**v5, "route": {"pedestrian": "c"}}
    sized = {**v5, "size_calibration": {"anchors": [[0, 0]], "classes": {"pedestrian": {"dh": 0.03}}}}
    ci = _class_config(inc, "pedestrian")
    assert _only_stage_change(_class_config(v5, "pedestrian"), ci)
    assert _only_stage_change(_class_config(rs, "pedestrian"), ci)
    assert not _only_stage_change(_class_config(moved, "pedestrian"), ci)    # a route change keeps the +0.01 bar
    assert not _only_stage_change(_class_config(sized, "pedestrian"), ci)    # so does a size change
    assert not _only_stage_change(ci, ci)


def test_disjoint_pool_adds_one_member_only_when_no_pair_is_possible():
    import sys
    sys.path.insert(0, "common/tools")
    from route_predictions import disjoint_pool
    W = {"x4": {1, 2, 3, 4}, "x3": {1, 2, 3}, "x5": {1, 2, 3, 4, 5}, "d3": {3}, "rosn": {7, 8}, "pv": {9}}
    w = W.__getitem__
    assert disjoint_pool(["x4", "x3", "x5"], ["x4", "x3", "x5", "d3", "rosn", "pv"], w) == ["x4", "x3", "x5", "rosn"]
    assert disjoint_pool(["x4", "rosn"], ["x4", "rosn", "pv"], w) == ["x4", "rosn"]          # a valid pair: unchanged
    assert disjoint_pool(["x4", "x3"], ["x4", "x3", "d3"], w) == ["x4", "x3"]                # nothing can pair: unchanged


def test_beamfix_moves_near_ground_points_onto_the_real_rings_and_spares_boxes():
    from s10_beamfix import frame_rng, recast, sensor_rings
    ext = np.eye(4)
    ext[:3, 3] = [0.0, 0.0, 3.0]                                        # sensor 5 m above the ground at z = -2
    o, d = sensor_rings(ext, [-50.0, -40.0, -30.0, -10.0, 0.0, 5.0], -2.0, 7.0)
    assert np.allclose(d, np.sort(5.0 / np.tan(np.radians([50.0, 40.0]))))   # -30 deg lands at 8.7 m: beyond 7 m
    rng = np.random.default_rng(1)
    ground = np.c_[rng.uniform(-6, 6, (400, 2)), np.full(400, -2.0)]
    ground = ground[np.hypot(ground[:, 0], ground[:, 1]) < 6.5]
    far = np.array([[20.0, 0.0, -2.0], [1.0, 1.0, -1.0]])                # beyond the radius; above the ground
    box = np.array([[3.0, 0.0, -1.3, 1.0, 1.0, 1.4, 0.0]])              # a walker standing at x = 3
    feet = np.array([[3.05, 0.02, -2.0]])
    P = np.vstack([ground, far, feet]).astype(np.float32)
    Q, n = recast(P, box, [(o, d)], 7.0, -2.0, frame_rng(0, "000017"))
    assert Q.shape == P.shape and 0 < n <= len(ground)
    assert np.array_equal(Q[len(ground):], P[len(ground):])              # far, elevated and in-box points stay
    moved = np.any(Q != P, axis=1)
    r = np.hypot(Q[moved, 0], Q[moved, 1])
    assert np.all(np.min(np.abs(r[:, None] / d[None, :] - 1), axis=1) < 0.05)   # on a ring, within the 1% jitter
    az0, az1 = np.arctan2(P[moved, 1], P[moved, 0]), np.arctan2(Q[moved, 1], Q[moved, 0])
    assert np.allclose(np.cos(az0 - az1), 1.0, atol=1e-5)               # azimuth kept
    from s10_beamfix import in_footprints
    assert not in_footprints(Q[moved, :2], Q[moved, 2], box).any()      # nothing moved into the box's column
    Q2, _ = recast(P, box, [(o, d)], 7.0, -2.0, frame_rng(0, "000017"))
    assert np.array_equal(Q, Q2)                                        # seeded per frame: reproducible bytes


def test_rule_14b_drops_the_route_bar_only_when_asked():
    from route_predictions import b_bar
    assert b_bar(False) == 0.01                     # R3: a route change needs +0.01 on B
    assert b_bar(True) == 1e-9                      # rule 11: a stage-only change needs a gain
    assert b_bar(False, 0.0) == 1e-9                # rule 14b (C2): a route change needs a gain
    assert b_bar(False, 0.02) == 0.02


def test_rule_15_needs_a_late_a_gain():
    from route_predictions import late_gate_ok
    assert late_gate_ok(0.002, 0.7)
    assert not late_gate_ok(-0.0055, 0.02)          # C1's Person route (record 15.15.8)
    assert not late_gate_ok(0.001, 0.4)             # a gain below P 0.5
    assert not late_gate_ok(0.0, 0.5) and not late_gate_ok(None, None)


def test_release_zip_assets_get_unique_names_when_versions_share_a_file_name():
    from release_weights import zip_assets
    z = [{"name": "lumpi_s10_submission.zip", "qualified": "lumpi.routed-c0.c0.lumpi_s10_submission.zip", "path": "a"},
         {"name": "lumpi_s10_submission.zip", "qualified": "lumpi.routed-c0.c0pq.lumpi_s10_submission.zip", "path": "b"},
         {"name": "v2x_s9f_submission.zip", "qualified": "v2x.routed-g19.s9f.v2x_s9f_submission.zip", "path": "c"}]
    out = zip_assets(z)
    assert [a["name"] for a in out] == ["lumpi.routed-c0.c0.lumpi_s10_submission.zip", "lumpi.routed-c0.c0pq.lumpi_s10_submission.zip",
                                        "v2x_s9f_submission.zip"]                    # a unique file name keeps its name
    assert [a["path"] for a in out] == ["a", "b", "c"] and all("qualified" not in a for a in out)
