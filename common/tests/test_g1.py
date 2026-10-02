"""Tests for the G1 generator pieces (walker ray casting, insertion, density calibration) and new helpers.

Synthetic fixtures only (no real data)."""
import numpy as np

from bdc26.density import DensityPrior, fit, inclusion_probs, resample_calibrated
from bdc26.detect.postprocess import apply_hedge, postprocess_class
from bdc26.frames import null_mask, with_nulls
from bdc26.render.pedsim import (InsertParams, Sensor, Walker, assign_sensor, bev_overlaps, cast_ellipsoids, human,
                                 insert_pedestrians, place)


def test_cast_ellipsoid_matches_sphere():
    w = Walker(np.array([[10.0, 0, 0]]), np.array([[1.0, 1.0, 1.0]]), np.eye(3)[None])
    d = np.array([[1.0, 0, 0], [0, 1.0, 0], [np.cos(0.05), np.sin(0.05), 0]])
    t = cast_ellipsoids(np.zeros(3), d, w)
    assert abs(t[0] - 9.0) < 1e-9
    assert np.isinf(t[1])
    # closed form for a ray at angle a to the centre direction: t = 10 cos a - sqrt(1 - 100 sin^2 a)
    a = 0.05
    assert abs(t[2] - (10 * np.cos(a) - np.sqrt(1 - 100 * np.sin(a) ** 2))) < 1e-9


def test_human_extent_and_placement():
    rng = np.random.default_rng(0)
    w = human(1.75, rng, shoulder=0.44, phase=0.0, stride_deg=0.0, backpack_prob=0.0)
    e = w.extent()
    assert abs(e[5] - 1.75) < 0.03 and e[2] < 0.05            # head top at the height, feet on the ground
    assert 0.35 < e[4] - e[1] < 0.75                            # shoulder width plus arms
    p = place(w, 5.0, -3.0, -2.0, np.pi / 2)
    e2 = p.extent()
    assert abs((e2[2] + e2[5]) / 2 - (-2.0 + (e[2] + e[5]) / 2)) < 1e-6


def _ground_scene(sensor):
    """Ground plane z = -2 seen by a 32-beam sensor at the origin (dense ring points)."""
    pts = []
    for el in sensor.beams[sensor.beams < -2]:
        r = 2.0 / np.tan(np.radians(-el))
        if r > 60:
            continue
        az = np.radians(np.arange(0, 360, sensor.az_res_deg))
        pts.append(np.stack([r * np.cos(az), r * np.sin(az), np.full_like(az, -2.0)], 1))
    return np.concatenate(pts)


def test_insert_occludes_and_is_blocked():
    s = Sensor(np.eye(4), np.linspace(-25, 5, 32), 0.4)
    pts = _ground_scene(s)
    rng = np.random.default_rng(1)
    w = place(human(1.8, rng, stride_deg=0.0, backpack_prob=0.0), 8.0, 0.0, -2.0, 0.0)
    out, keep, wid, hits = insert_pedestrians(pts, np.zeros(len(pts), np.int64), [s], [w], rng, InsertParams(drop_prob=0.0))
    assert hits[0] > 30
    removed = pts[~keep]
    assert len(removed) > 0
    az = np.degrees(np.arctan2(removed[:, 1], removed[:, 0]))
    assert np.all(np.abs(az) < 6) and np.all(np.hypot(removed[:, 0], removed[:, 1]) > 7.5)   # only the shadow behind
    new = out[len(pts) - (~keep).sum():]
    assert np.all(np.abs(new[:, 0] - 8.0) < 0.5) and new[:, 2].max() < -0.1
    # a wall at x = 5 in front of the walker blocks every walker return
    yy, zz = np.meshgrid(np.linspace(-3, 3, 200), np.linspace(-2, 1, 100))
    wall = np.stack([np.full(yy.size, 5.0), yy.ravel(), zz.ravel()], 1)
    pts2 = np.concatenate([pts, wall])
    out2, keep2, _, hits2 = insert_pedestrians(pts2, np.zeros(len(pts2), np.int64), [s], [w], rng,
                                               InsertParams(drop_prob=0.0, block_nbr=(1, 1)))
    assert hits2[0] == 0


def test_assign_sensor_by_beam_residual():
    a = Sensor(np.eye(4), np.linspace(-15, 15, 16), 0.2)
    T = np.eye(4); T[:3, 3] = [30.0, 0, 0]
    b = Sensor(T, np.linspace(-15.5, 14.5, 16), 0.2)
    el = np.radians(a.beams[3]); pa = np.array([[10 * np.cos(el), 0.0, 10 * np.sin(el)]])
    elb = np.radians(b.beams[5]); pb = np.array([[30 - 12 * np.cos(elb), 0.0, 12 * np.sin(elb)]])
    got = assign_sensor(np.concatenate([pa, pb]), [a, b], tol_deg=0.05)
    assert got.tolist() == [0, 1]


def test_bev_overlaps():
    box = np.array([0, 0, 0, 1.0, 1.0, 1.7, 0.0])
    others = np.array([[1.2, 0, 0, 1.0, 1.0, 1.7, 0.0], [5, 5, 0, 1, 1, 1, 0]])
    assert bev_overlaps(box, others, 0.3)
    assert not bev_overlaps(box, others, 0.0)


def test_inclusion_probs_sum_and_proportionality():
    w = np.array([0.1, 1.0, 1.0, 5.0, 100.0])
    p = inclusion_probs(w, 2)
    assert abs(p.sum() - 2) < 1e-6 and p[-1] == 1.0
    assert abs(p[1] / p[0] - 10) < 1e-3


def test_density_resample_keeps_objects_uniform():
    rng = np.random.default_rng(0)
    bg = np.c_[rng.uniform(-40, 40, (100000, 2)), np.full(100000, -2.0)]
    obj = np.c_[rng.normal(0, 0.3, (4000, 2)), rng.uniform(-2, 0, 4000)]
    pts = np.concatenate([bg, obj]).astype(np.float32)
    is_obj = np.r_[np.zeros(len(bg), bool), np.ones(len(obj), bool)]
    real = [np.c_[rng.uniform(0, 40, (5000, 1)), rng.uniform(-40, 40, (5000, 1)), np.full((5000, 1), -2.0)]]   # x > 0 only
    syn = [bg[:5000]]
    pr = fit(real, syn, (-40, -40, -5, 40, 40, 5), cell=(8, 8, 2.5), alpha=0.1, clip=(0.01, 100))
    out = resample_calibrated(pts, 20000, rng, (-40, -40, -5, 40, 40, 5), pr, is_obj)
    assert len(out) == 20000
    n_obj = np.sum(np.hypot(out[:, 0], out[:, 1]) < 1.2)
    assert abs(n_obj / 4000 - 20000 / len(pts)) < 0.03        # object keep rate stays uniform
    assert np.mean(out[:, 0] > 0) > 0.85                        # background follows the real density
    assert isinstance(pr, DensityPrior)


def test_with_nulls():
    rng = np.random.default_rng(0)
    p = rng.normal(size=(35000, 3)).astype(np.float32)
    f = with_nulls(p, 0.31, 50000, rng)
    assert f.shape == (50000, 3) and abs(null_mask(f).mean() - 0.31) < 1e-4


def test_postprocess_size_scale_and_hedge():
    b = np.array([[0, 0, -1.0, 4.0, 2.0, 2.0, 0.0], [10, 0, -1.0, 4.0, 2.0, 2.0, 0.0]])
    s = np.array([0.9, 0.5])
    bb, ss = postprocess_class(b, s, {"nms_iou": 0.1, "size_scale": [1.1, 1.0, 0.8], "z_offset": 0.1})
    assert np.allclose(bb[:, 3:6], [[4.4, 2.0, 1.6]] * 2)
    assert np.allclose(bb[:, 2], -2.0 + 0.8 + 0.1)              # bottom kept at -2, then offset
    out = [{"box": list(bb[0]), "score": 0.9, "class": "Car"}]
    h = apply_hedge(out, {"Car": [["Van", 0.3], ["Truck", 0.1]]})
    assert [d["class"] for d in h] == ["Car", "Van", "Truck"] and abs(h[1]["score"] - 0.27) < 1e-9


def test_recenter_moves_toward_interior_points():
    from bdc26.detect.postprocess import recenter
    rng = np.random.default_rng(0)
    pts = np.c_[rng.normal([0.3, 0.0], 0.05, (50, 2)), np.full(50, -1.0)]
    b = np.array([[0.0, 0.0, -1.0, 1.0, 1.0, 1.8, 0.0], [10.0, 10.0, -1.0, 1.0, 1.0, 1.8, 0.0]])
    out = recenter(b, pts, 0.5)
    assert abs(out[0, 0] - 0.15) < 0.02 and np.allclose(out[1], b[1])
