"""Release 10.2 (S10-2): the calibrated generators (LUMPI N1, V2X aw) and the member folders."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common"))
sys.path.insert(0, str(REPO / "common" / "tools"))


def test_n1_redraw_keeps_the_count_the_guard_and_is_seeded():
    import s10_2_n1 as n
    rng = np.random.default_rng(0)
    P = rng.uniform([-30, -30, -3], [30, 30, 3], (5000, 3)).astype(np.float32)
    uk = np.unique(n.voxel_key(P[:2500], (2, 2, 0.5)))
    wv = np.linspace(0.2, 3.0, len(uk))
    w = n.lookup(P, uk, wv, (2, 2, 0.5))
    assert np.all(w[2500:][~np.isin(n.voxel_key(P[2500:], (2, 2, 0.5)), uk)] == 1.0)     # unseen voxels: weight 1
    g = np.zeros(len(P), bool)
    g[:300] = True
    Q, ncopy = n.redraw(P, w, g, np.random.default_rng([0, 7]))
    assert Q.shape == P.shape and ncopy > 0 and n.in_range(Q).all()
    assert {tuple(x) for x in P[:300]} <= {tuple(x) for x in Q}                            # guarded points stay
    Q2, _ = n.redraw(P, w, g, np.random.default_rng([0, 7]))
    assert np.array_equal(Q, Q2)


def test_n1_voxel_key_is_computed_in_float64():
    import s10_2_n1 as n
    P = np.array([[1.9999999, 0.0, 0.0]], dtype=np.float32)                               # a cell boundary in float32
    assert n.voxel_key(P, (2, 2, 0.5))[0] == n.voxel_key(P.astype(np.float64), (2, 2, 0.5))[0]


def test_n1_item_has_no_separator():
    import s10_2_n1 as n
    assert ";" not in n.item("gen/s10_2_n1_weights.npz")                                   # rule 1b splits items at ';'


def test_aw_keeps_nulls_and_box_points_and_the_count():
    import s10_2_aw as aw
    K = int(360 / aw.AZ) * int(np.ceil(35 / aw.EL))
    rng = np.random.default_rng(1)
    donors = rng.uniform([-30, -30, -2], [30, 30, 1], (20000, 3)).astype(np.float32)
    bd, _ = aw.abin(donors.astype(np.float64))
    order = np.argsort(bd, kind="stable")
    qs = np.linspace(0, 1, aw.NQ)
    keys = np.unique(aw.wbin(*aw.sph(donors.astype(np.float64))[:2]))
    aw._C.update(Ts={int(k): qs * 40 for k in keys}, Tr={int(k): qs * 38 for k in keys}, w=np.full(K, 1.0),
                 Sd=donors, order=order, starts=np.searchsorted(bd[order], np.arange(K + 1)))
    from bdc26.frames import with_nulls
    P = rng.uniform([-30, -30, -2], [30, 30, 1], (3500, 3)).astype(np.float32)
    P50 = with_nulls(P, 0.31, 5000, np.random.default_rng([1234, 5]))
    boxes = np.array([[5.0, 5.0, 0.0, 4.0, 2.0, 2.0, 0.3]])
    Q, nrep, mv = aw.aw_frame(P50, boxes, "000005")
    nul = np.all(P50 == 0, 1)
    inb = aw.in_boxes(P50.astype(np.float64), boxes) & ~nul
    assert Q.shape == P50.shape and abs(np.all(Q == 0, 1).mean() - 0.31) < 1e-3
    assert np.array_equal(Q[nul], P50[nul]) and np.array_equal(Q[inb], P50[inb]) and mv > 0


def test_s10_2_member_names_swap_the_corpus_tag():
    import s10_2_members as sm
    assert sm.new_name("voxelrcnn-rosf-g1v6j", "pcdet/g1-v6j", "g1-v6jn1") == "voxelrcnn-rosf-g1v6jn1"
    assert sm.new_name("voxelrcnn-ros-g1v6d2", "pcdet/g1-v6d2", "g1-v6d2aw") == "voxelrcnn-ros-g1v6d2aw"
    assert sm.new_name("voxelrcnn-rosf-gblobs-g1v6", "pcdet/g1-v6", "g1-v6n1") == "voxelrcnn-rosf-gblobs-g1v6n1"


# S10-2 P (record Section 11.4): route_predictions.apply_final_adjust, the last stage of the routed merge
P_SPEC = {"size": {"Person": {"target": [0.76, 0.74, 1.9], "alpha_h": 0.5},
                   "Bicycle": {"target": [2.0, 0.85, 1.9], "alpha_lw": 0.25}},
          "copies": {"Person": {"r": 0.2, "n": 4, "lw_scale": 1.1, "min_score": 0.3}}}


def _p_toy(seed=0, n_frames=20):
    rng = np.random.default_rng(seed)
    preds, gts = {}, {}
    for k in range(n_frames):
        g = np.column_stack([rng.uniform(-20, 20, (6, 2)), np.full((6, 1), -1.0), np.tile([0.7, 0.7, 1.8, 0.0], (6, 1))])
        b = g.copy()
        b[:, :2] += rng.normal(0, 0.2, (6, 2))
        b[:, 3:6] *= rng.uniform(0.8, 1.2, (6, 3))
        fp = np.column_stack([rng.uniform(-20, 20, (4, 2)), np.full((4, 1), -1.0), np.tile([0.7, 0.7, 1.7, 0.0], (4, 1))])
        boxes = np.vstack([b, fp])
        scores = rng.uniform(0.05, 1.0, len(boxes))
        preds[f"f{k}"] = ([{"box": list(map(float, x)), "score": float(s), "class": "Person"} for x, s in zip(boxes, scores)]
                          + [{"box": [5.0, 5.0, -1.0, 1.7, 0.6, 1.2, 0.3], "score": 0.6, "class": "Bicycle"},
                             {"box": [9.0, 1.0, -0.8, 4.4, 1.9, 1.6, 0.0], "score": 0.9, "class": "Car"}])
        gts[f"f{k}"] = g
    return preds, gts


def test_final_adjust_size_moves_toward_the_target_and_keeps_the_bottom():
    from route_predictions import apply_final_adjust
    preds, _ = _p_toy()
    out = apply_final_adjust(preds, {"size": P_SPEC["size"]})
    for f in preds:
        assert len(out[f]) == len(preds[f])                                   # no box added or removed
        for d0, d1 in zip(preds[f], out[f]):
            b0, b1 = np.array(d0["box"]), np.array(d1["box"])
            assert d1["score"] == d0["score"] and d1["class"] == d0["class"]
            if d0["class"] == "Person":
                assert np.isclose(b1[5], b0[5] + 0.5 * (1.9 - b0[5])) and np.allclose(b1[3:5], b0[3:5])
            elif d0["class"] == "Bicycle":
                assert np.allclose(b1[3:5], b0[3:5] + 0.25 * (np.array([2.0, 0.85]) - b0[3:5])) and b1[5] == b0[5]
            else:
                assert np.array_equal(b1, b0)
            assert np.isclose(b1[2] - b1[5] / 2, b0[2] - b0[5] / 2)        # the box bottom stays
            assert np.allclose(b1[[0, 1, 6]], b0[[0, 1, 6]])
    assert preds["f0"][0]["box"] != out["f0"][0]["box"]                        # the input is not modified in place


def test_final_adjust_copies_rank_below_every_box_and_never_lower_ap():
    from bdc26.evalap import ap_for_class
    from route_predictions import apply_final_adjust

    def ap(p, g):
        fr = []
        for f in g:
            v = [d for d in p[f] if d["class"] == "Person"]
            fr.append((np.array([d["box"] for d in v]).reshape(-1, 7), np.array([d["score"] for d in v]), g[f]))
        return ap_for_class(fr, 0.5, "3d")["AP_R40"]

    for seed in range(5):
        preds, gts = _p_toy(seed)
        sized = apply_final_adjust(preds, {"size": P_SPEC["size"]})
        out = apply_final_adjust(preds, P_SPEC)
        orig = [d["score"] for v in sized.values() for d in v if d["class"] == "Person"]
        new = [d for f in out for d in out[f][len(sized[f]):]]
        assert len(new) == 4 * sum(s >= 0.3 for s in orig) and all(d["class"] == "Person" for d in new)
        assert max(d["score"] for d in new) < min(orig)
        for f in sized:                                                       # the sized boxes first, unchanged
            assert out[f][:len(sized[f])] == sized[f]
            src = [d for d in sized[f] if d["class"] == "Person" and d["score"] >= 0.3]
            cps = out[f][len(sized[f]):]
            for i, d in enumerate(src):
                for j in range(4):
                    c = np.array(cps[4 * i + j]["box"])
                    b = np.array(d["box"])
                    assert np.isclose(np.hypot(*(c[:2] - b[:2])), 0.2) and np.allclose(c[3:5], 1.1 * b[3:5])
        assert ap(out, gts) >= ap(sized, gts) - 1e-12
        assert sum(d["class"] != "Person" for v in out.values() for d in v) == 2 * len(preds)


def test_final_adjust_is_the_last_stage_and_a_stage_field():
    import route_predictions as rp
    preds, _ = _p_toy()
    card = {"route": {"Person": "m", "Bicycle": "m", "Car": "m"}, "tail_copies": {"Person": {"r": 0.2, "n": 4}},
            "size_calibration": {"classes": {"Person": {"dh": 0.03}}}}
    base = rp.merge_card(card, {"m": preds})
    assert rp.merge_card({**card, "final_adjust": P_SPEC}, {"m": preds}) == rp.apply_final_adjust(base, P_SPEC)
    assert rp.merge_card({**card, "final_adjust": None}, {"m": preds}) == base
    ci, cn = rp._class_config(card, "Person"), rp._class_config({**card, "final_adjust": P_SPEC}, "Person")
    assert rp._only_stage_change(cn, ci)                                      # P alone is a stage change
    assert rp._class_config({**card, "final_adjust": P_SPEC}, "Car") == rp._class_config(card, "Car")


# S10-4 L8 (record 2026-11-14-s10-10.4-plan.md Section 3): cross-class copies, the last part of final_adjust
def test_final_adjust_cross_copies_rank_below_the_receiving_class_and_never_lower_its_ap():
    from bdc26.evalap import ap_for_class
    from route_predictions import apply_final_adjust

    def ap(p, g, c):
        fr = []
        for f in g:
            v = [d for d in p[f] if d["class"] == c]
            fr.append((np.array([d["box"] for d in v]).reshape(-1, 7), np.array([d["score"] for d in v]), g[f]))
        return ap_for_class(fr, 0.5, "3d")["AP_R40"]

    spec = {"cross_copies": {"Bicycle": {"from": "Person", "target": [2.0, 0.85, 1.9]}, "Car": {"from": "Bicycle"}}}
    for seed in range(5):
        preds, gts = _p_toy(seed)
        out = apply_final_adjust(preds, spec)
        for f in preds:
            assert out[f][:len(preds[f])] == preds[f]                        # every original box unchanged, first
            new = out[f][len(preds[f]):]
            src = [d for d in preds[f] if d["class"] == "Person"]
            assert [d["class"] for d in new] == ["Bicycle"] * len(src) + ["Car"]   # one copy per donor, none of a copy
            for d, c in zip(src, new):
                b, cb = np.array(d["box"]), np.array(c["box"])
                assert np.allclose(cb[[0, 1, 6]], b[[0, 1, 6]]) and np.allclose(cb[3:6], [2.0, 0.85, 1.9])
                assert np.isclose(cb[2] - cb[5] / 2, b[2] - b[5] / 2)          # the box bottom stays
            assert np.array_equal(np.array(new[-1]["box"]), np.array(preds[f][-2]["box"]))  # no target: geometry kept
        for c in ("Bicycle", "Car"):
            orig = [d["score"] for v in preds.values() for d in v if d["class"] == c]
            cps = [d["score"] for f in out for d in out[f][len(preds[f]):] if d["class"] == c]
            assert max(cps) < min(orig)
            g = {f: gts[f] for f in gts}
            assert ap(out, g, c) >= ap(preds, g, c) - 1e-12
        assert apply_final_adjust(preds, {"cross_copies": {"Bus": {"from": "Truck"}}}) == preds   # no donor: nothing
