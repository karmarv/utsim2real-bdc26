"""S9 engine v6: the LUMPI vehicle size convention, the quantile size sampler, the walker sampler on a scene map, the
map-placed structure meshes and the world tilt augmentation (docs/decisions/2026-11-02-s9-clean-twin-plan.md)."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common"))

from bdc26.detect.augment import world_tilt  # noqa: E402
from bdc26.render import scene_map as smap  # noqa: E402
from bdc26.render import v6  # noqa: E402
from bdc26.render.g2 import STRUCTURE_KINDS, structure_mesh  # noqa: E402


def box(l, w, h):
    return [0.0, 0.0, h / 2, l, w, h, 0.0]


def test_lumpi_class_rule_moves_transporters_to_truck_and_keeps_trucks():
    b = np.array([box(4.5, 1.9, 1.6), box(5.9, 2.0, 2.45), box(4.9, 1.95, 2.05), box(5.7, 2.0, 1.9), box(4.4, 1.8, 2.5),
                  box(4.2, 1.8, 1.6)])
    names = ["Car", "Van", "Car", "Car", "Van", "Truck"]
    assert list(v6.lumpi_class_rule(b, names)) == ["Car", "Truck", "Van", "Truck", "Truck", "Truck"]


def test_quantile_sizes_follow_the_quantiles_and_stay_comonotonic():
    rng = np.random.default_rng(0)
    real = np.c_[rng.uniform(5, 17, 4000), rng.uniform(2.0, 2.6, 4000), rng.uniform(2.2, 4.0, 4000)]
    real = np.sort(real, axis=0)                           # comonotonic: long ones are wide and tall
    spec = v6.size_scalars({"Truck": real})["Truck"]
    s = v6.QuantileSizes(spec).sample(20000, np.random.default_rng(1))
    assert abs(np.median(s[:, 0]) - np.median(real[:, 0])) < 0.3
    assert s[:, 0].min() >= np.percentile(real[:, 0], 5) - 1e-3 and s[:, 0].max() <= np.percentile(real[:, 0], 95) + 1e-3   # 4-decimal scalars
    assert np.corrcoef(s[:, 0], s[:, 2])[0, 1] > 0.9


def _toy_map():
    """A 40 x 40 m map: a road band along x, sidewalk strips beside it, terrain beyond, nothing in one corner."""
    cell, n = 0.5, 80
    counts = np.zeros((4, n, n))
    ys = (np.arange(n) + 0.5) * cell - 20
    for j, y in enumerate(ys):
        k = 0 if abs(y) < 4 else (1 if abs(y) < 6 else 2)  # road, sidewalk, terrain (TAGS order: road, sidewalk, terrain, line)
        counts[k, :, j] = 10
    counts[:, :10, :10] = 0                                # no ground in a corner
    gz = np.where(counts.sum(0) > 0, -2.0, np.nan)
    gz[:, np.abs(ys) >= 6] = -1.8                          # terrain 0.2 m above the road
    lane = np.zeros((n, n)); lane[:, np.abs(ys) < 4] = 5
    d = np.zeros((n, n, 2)); d[..., 0] = 1.0               # traffic along x (doubled angle 0)
    return smap.SceneMap(np.array([-20.0, -20.0]), cell, counts, gz, lane, d)


def test_walker_sampler_uses_map_cells_ground_and_traffic_direction():
    m = _toy_map()
    cfg = smap.WalkerConfig(weights={"curb": 0.5, "road": 0.5}, boxes=((1.0, 0.7, 0.7, 1.8, 0.05, 0.05, 0.1),),
                            pc_range=(-20, -20, -5, 20, 20, 5), map_ground=True, groups=(1.0,))
    s = smap.WalkerSampler(m, cfg)
    rng = np.random.default_rng(0)
    poses = [s(rng) for _ in range(400)]
    ys = np.array([p[1] for p in poses])
    assert np.all(np.abs(ys) < 4.0 + 4.0 + 0.5)            # road or curb strip, never the far terrain
    z = np.array([p[4] for p in poses])
    assert set(np.round(z, 2)) <= {-2.0, -1.8}             # the map's ground, curb raised
    yaw_road = np.array([p[2] for p in poses])[np.abs(ys) < 3.5]
    assert np.median(np.abs(np.sin(yaw_road))) > 0.7       # crossing the road: across the traffic direction


def test_structure_meshes_are_finite_and_footprints_cover_them():
    rng = np.random.default_rng(0)
    for kind in STRUCTURE_KINDS:
        for _ in range(5):
            V, F, (L, W) = structure_mesh(kind, rng)
            assert np.isfinite(V).all() and F.max() < len(V) and V[:, 2].min() >= -0.1   # hedge ellipsoids bulge a few cm below ground
            assert np.abs(V[:, 0]).max() <= L / 2 + 0.6 and np.abs(V[:, 1]).max() <= max(W, 0.3) / 2 + 0.6


def test_world_tilt_moves_points_and_box_centres_together():
    rng = np.random.RandomState(0)
    b = np.array([[20.0, 5.0, -1.0, 4.0, 2.0, 1.6, 0.3]])
    p = np.array([[20.0, 5.0, -1.0], [0.0, 0.0, 0.0]])
    nb, np_ = world_tilt(b, p, {"MAX_DEG": 1.5, "PROB": 1.0}, rng)
    assert np.allclose(nb[0, :3], np_[0]) and np.allclose(np_[1], 0)
    assert np.allclose(nb[0, 3:], b[0, 3:]) and abs(np.linalg.norm(np_[0]) - np.linalg.norm(p[0])) < 1e-9


def test_torch_scatter_stand_in_matches_a_loop():
    import torch
    from bdc26.detect.pcdet_patches import _TorchScatter
    g = torch.Generator().manual_seed(0)
    src, idx = torch.randn(500, 3, generator=g), torch.randint(0, 40, (500,), generator=g)
    mean, mx = _TorchScatter.scatter_mean(src, idx), _TorchScatter.scatter_max(src, idx)[0]
    for k in range(int(idx.max()) + 1):
        sel = src[idx == k]
        if len(sel):
            assert torch.allclose(mean[k], sel.mean(0), atol=1e-6) and torch.allclose(mx[k], sel.max(0).values)
        else:
            assert torch.all(mean[k] == 0) and torch.all(mx[k] == 0)
