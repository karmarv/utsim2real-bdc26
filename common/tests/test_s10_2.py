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
