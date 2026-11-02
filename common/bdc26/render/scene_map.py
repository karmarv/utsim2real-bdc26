"""Engine v6 (strategy S9, docs/decisions/2026-11-02-s9-clean-twin-plan.md): the static scene map of a roadside twin,
built from the twin alone.

A roadside rig never moves, so every UT frame sees the same static scene. Aggregating the per-point CARLA semantic
tags (`sem_seg`: 1 road, 2 sidewalk, 10 terrain, 24 road line) over frames gives a BEV map of the twin's ground
classes with the median ground height per cell; aggregating the UT actor boxes (`lbl`) gives where vehicles drive
and in which direction. No real frame and no real label is read here.

The map replaces the real label rows that placed walkers and clutter before S9 (audit item 4, contingency C2):
- `WalkerSampler`: walkers on walkable cells (curbside strips, open terrain, crossings on the road, and the band just
  beyond the twin's modelled ground), headings along or across the local traffic direction, groups of 1-4, and a
  target range histogram (scalars);
- `anchor_points`: points near the curbside where unlabeled clutter (hard negatives) stands;
- `structure_points`: terrain and beyond-the-twin cells away from the road, where map-placed static structure goes.

    python -c "from bdc26.config import load_track; from bdc26.render.scene_map import build; build(load_track('lumpi-track'))"
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

TAGS = {"road": 1, "sidewalk": 2, "terrain": 10, "roadline": 24}
VEHICLES = ("Car", "Van", "Truck", "Bus")          # UT class names whose boxes trace the lanes


@dataclass
class SceneMap:
    origin: np.ndarray        # (2,) x, y of the corner of cell (0, 0)
    cell: float
    counts: np.ndarray        # (4, H, W) points per tag in TAGS order
    ground_z: np.ndarray      # (H, W) median z of the ground-tag points, nan where none
    lane_count: np.ndarray    # (H, W) vehicle box centres seen per cell
    lane_dir: np.ndarray      # (H, W, 2) unit heading (axial: sign-free) of the vehicles in the cell

    @property
    def shape(self):
        return self.counts.shape[1:]

    def save(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, origin=self.origin, cell=self.cell, counts=self.counts, ground_z=self.ground_z,
                            lane_count=self.lane_count, lane_dir=self.lane_dir)

    @classmethod
    def load(cls, path: Path) -> "SceneMap":
        d = np.load(path)
        return cls(d["origin"], float(d["cell"]), d["counts"], d["ground_z"], d["lane_count"], d["lane_dir"])

    def index(self, x, y):
        i = np.floor((np.asarray(x) - self.origin[0]) / self.cell).astype(int)
        j = np.floor((np.asarray(y) - self.origin[1]) / self.cell).astype(int)
        return i, j

    def centres(self):
        H, W = self.shape
        xs = self.origin[0] + (np.arange(H) + 0.5) * self.cell
        ys = self.origin[1] + (np.arange(W) + 0.5) * self.cell
        return np.meshgrid(xs, ys, indexing="ij")

    def dominant(self) -> np.ndarray:
        """(H, W) tag code of the most frequent ground tag per cell, 0 where the twin has no ground point."""
        codes = np.array(list(TAGS.values()))
        return np.where(self.counts.sum(0) > 0, codes[self.counts.argmax(0)], 0)

    def distance_to(self, mask: np.ndarray) -> np.ndarray:
        """(H, W) metres from each cell to the nearest cell of mask (inf when mask is empty)."""
        from scipy.ndimage import distance_transform_edt
        if not mask.any():
            return np.full(mask.shape, np.inf)
        return distance_transform_edt(~mask) * self.cell

    def axial_dir_near(self, i, j, radius: int = 6) -> np.ndarray | None:
        """Mean axial traffic direction of the lane cells within radius cells of (i, j), or None."""
        H, W = self.shape
        i0, i1, j0, j1 = max(i - radius, 0), min(i + radius + 1, H), max(j - radius, 0), min(j + radius + 1, W)
        c = self.lane_count[i0:i1, j0:j1]
        if c.sum() <= 0:
            return None
        d = self.lane_dir[i0:i1, j0:j1]                                  # (h, w, 2) doubled-angle vectors
        v = (d * c[..., None]).sum((0, 1))
        if np.hypot(*v) < 1e-6:
            return None
        a = 0.5 * np.arctan2(v[1], v[0])
        return np.array([np.cos(a), np.sin(a)])


def _frame_stats(args):
    root, idx, origin, cell, shape = args
    p = np.load(root / "pcd" / f"{idx:06d}.npy")
    s = np.fromfile(root / "sem_seg" / f"{idx:06d}.label", dtype=np.uint32) & 0xFFFF
    H, W = shape
    i = np.floor((p[:, 0] - origin[0]) / cell).astype(int)
    j = np.floor((p[:, 1] - origin[1]) / cell).astype(int)
    ok = (i >= 0) & (i < H) & (j >= 0) & (j < W)
    counts = np.zeros((len(TAGS), H, W), np.int32)
    zsum = np.zeros((H, W)); zn = np.zeros((H, W), np.int32)
    for k, tag in enumerate(TAGS.values()):
        m = ok & (s == tag)
        np.add.at(counts[k], (i[m], j[m]), 1)
        np.add.at(zsum, (i[m], j[m]), p[m, 2])
        np.add.at(zn, (i[m], j[m]), 1)
    lane_c = np.zeros((H, W), np.int32); lane_v = np.zeros((H, W, 2))
    for line in (root / "lbl" / f"{idx:06d}.txt").read_text().splitlines():
        r = line.split()
        if len(r) < 8 or r[7] not in VEHICLES:
            continue
        x, y, yaw = float(r[0]), float(r[1]), float(r[6])
        a, b = int(np.floor((x - origin[0]) / cell)), int(np.floor((y - origin[1]) / cell))
        if 0 <= a < H and 0 <= b < W:
            lane_c[a, b] += 1
            lane_v[a, b] += (np.cos(2 * yaw), np.sin(2 * yaw))           # axial: a lane has two directions
    return counts, zsum, zn, lane_c, lane_v


def build(track, stride: int = 20, cell: float = 0.5, half: float = 64.0, workers: int = 48,
          out: Path | None = None) -> Path:
    """Aggregate every stride-th UT frame of the track into gen/scene_map_v1.npz (a square of +/- half metres)."""
    from multiprocessing import Pool
    from ..io.ut import ut_dir
    root = ut_dir(track)
    origin = np.array([-half, -half])
    shape = (int(2 * half / cell), int(2 * half / cell))
    frames = list(range(0, track["ut"]["n_frames"], stride))
    with Pool(workers) as pool:
        res = pool.map(_frame_stats, [(root, i, origin, cell, shape) for i in frames], chunksize=4)
    counts = sum(r[0] for r in res); zsum = sum(r[1] for r in res); zn = sum(r[2] for r in res)
    lane_c = sum(r[3] for r in res); lane_v = sum(r[4] for r in res)
    ground_z = np.where(zn > 0, zsum / np.maximum(zn, 1), np.nan)
    norm = np.hypot(lane_v[..., 0], lane_v[..., 1])[..., None]
    lane_dir = np.where(norm > 0, lane_v / np.maximum(norm, 1e-9), 0.0)
    m = SceneMap(origin, cell, counts, ground_z, lane_c.astype(np.float32), lane_dir)
    out = out or track.gen / "scene_map_v1.npz"
    m.save(out)
    return out


# --------------------------------------------------------------------------------------------
# Samplers on the map
# --------------------------------------------------------------------------------------------
@dataclass
class WalkerConfig:
    """Walker placement and box convention, all scalars (no real label row is copied).
    weights: share of walkers per area kind before the range reweighting; edge_m: width of the curbside strip;
    beyond_m: how far past the twin's modelled ground a walker may stand; range_bins / range_share: the target range
    histogram (from the frame origin); boxes: mixture of (share, median l, w, h, sd l, w, h); groups: size shares."""
    weights: dict
    edge_m: float = 4.0
    beyond_m: float = 6.0
    range_bins: tuple = ()
    range_share: tuple = ()
    boxes: tuple = ()
    groups: tuple = (0.6, 0.25, 0.1, 0.05)
    group_gap: tuple = (0.6, 1.0)
    standing_share: float = 0.25
    heading_sd: float = 0.3
    pc_range: tuple = (-40, -40, -5, 40, 40, 5)
    range_from: tuple = ((0.0, 0.0),)       # range = distance to the nearest of these points (the sensors' xy)
    map_ground: bool = False                # stand walkers on the map's ground height (LUMPI: terrain is raised)
    max_step: float = 0.6                   # with map_ground: skip cells whose ground is higher above the road level


class WalkerSampler:
    """Callable(rng) -> (x, y, yaw, (l, w, h)), the pose interface of bdc26.render.g1.WalkerInserter."""

    def __init__(self, scene: SceneMap, cfg: WalkerConfig):
        self.m, self.cfg = scene, cfg
        dom = scene.dominant()
        road = dom == TAGS["road"]
        walk = np.isin(dom, [TAGS["sidewalk"], TAGS["terrain"], TAGS["roadline"]])
        d_road = scene.distance_to(road)
        d_ground = scene.distance_to(dom > 0)
        X, Y = scene.centres()
        x0, y0, _, x1, y1, _ = cfg.pc_range
        inside = (X > x0 + 0.5) & (X < x1 - 0.5) & (Y > y0 + 0.5) & (Y < y1 - 0.5)
        self.ground = MapGround(scene) if cfg.map_ground else None
        if self.ground is not None:
            ok_step = ~np.isfinite(scene.ground_z) | (scene.ground_z - self.ground.road_z <= cfg.max_step)
            walk, road = walk & ok_step, road & ok_step
        kinds = {
            "curb": walk & (d_road <= cfg.edge_m),
            "open": walk & (d_road > cfg.edge_m),
            "road": road,
            "beyond": (dom == 0) & (d_ground <= cfg.beyond_m),
        }
        cells, w = [], []
        for k, mask in kinds.items():
            mask = mask & inside
            n = int(mask.sum())
            if n == 0 or cfg.weights.get(k, 0.0) <= 0:
                continue
            ii, jj = np.nonzero(mask)
            cells.append(np.stack([ii, jj], 1)); w.append(np.full(n, cfg.weights[k] / n))
        self.cells = np.concatenate(cells)
        w = np.concatenate(w)
        if len(cfg.range_bins) and len(cfg.range_share):
            cx, cy = X[self.cells[:, 0], self.cells[:, 1]], Y[self.cells[:, 0], self.cells[:, 1]]
            r = np.min([np.hypot(cx - sx, cy - sy) for sx, sy in cfg.range_from], axis=0)
            b = np.clip(np.digitize(r, cfg.range_bins) - 1, 0, len(cfg.range_share) - 1)
            have = np.bincount(b, weights=w, minlength=len(cfg.range_share))
            target = np.asarray(cfg.range_share, float)
            w = w * np.where(have[b] > 0, target[b] / np.maximum(have[b], 1e-12), 0.0)
        self.p = w / w.sum()
        self.kind_of = np.concatenate([np.full(int((m & inside).sum()), k, dtype=object)
                                       for k, m in kinds.items() if (m & inside).any() and cfg.weights.get(k, 0.0) > 0])
        self._queue: list = []

    def _box(self, rng):
        B = self.cfg.boxes
        k = rng.choice(len(B), p=np.array([b[0] for b in B]) / sum(b[0] for b in B))
        _, l, w, h, sl, sw, sh = B[k]
        return (float(np.clip(rng.normal(l, sl), 0.4, 2.2)), float(np.clip(rng.normal(w, sw), 0.4, 1.3)),
                float(np.clip(rng.normal(h, sh), 1.45, 2.15)))

    def _group(self, rng):
        c = rng.choice(len(self.p), p=self.p)
        i, j = self.cells[c]
        x = self.m.origin[0] + (i + rng.uniform()) * self.m.cell
        y = self.m.origin[1] + (j + rng.uniform()) * self.m.cell
        d = self.m.axial_dir_near(i, j)
        if d is None or rng.uniform() < self.cfg.standing_share:
            yaw = rng.uniform(-np.pi, np.pi)
        else:
            base = np.arctan2(d[1], d[0]) + (np.pi / 2 if self.kind_of[c] == "road" else 0.0)   # cross the road
            yaw = base + rng.normal(0, self.cfg.heading_sd) + (np.pi if rng.uniform() < 0.5 else 0.0)
        g = self.cfg.groups
        n = 1 + int(rng.choice(len(g), p=np.asarray(g) / sum(g)))
        side = np.array([-np.sin(yaw), np.cos(yaw)])
        out = []
        for k in range(n):
            off = (k - (n - 1) / 2) * rng.uniform(*self.cfg.group_gap)
            px, py = float(x + off * side[0]), float(y + off * side[1])
            pose = (px, py, float(yaw + rng.normal(0, 0.15)), self._box(rng))
            if self.ground is not None:
                z = self.ground.at(px, py)
                if z is not None:
                    pose = pose + (z,)
            out.append(pose)
        return out

    def __call__(self, rng):
        if not self._queue:
            self._queue = self._group(rng)
        return self._queue.pop()


class MapGround:
    """Ground height from the map: the cell's median ground-tag z when the cell has ground and is at most max_step
    above the road level, else `default` (None: the caller's own estimate). Callable as a G2/G1 ground
    (points, x, y) -> z."""

    def __init__(self, scene: SceneMap, default: float | None = None, max_step: float = 0.6):
        self.m, self.default, self.max_step = scene, default, max_step
        road = scene.dominant() == TAGS["road"]
        self.road_z = float(np.nanmedian(scene.ground_z[road])) if road.any() else float(np.nanmedian(scene.ground_z))

    def at(self, x, y):
        i, j = self.m.index(x, y)
        H, W = self.m.shape
        if 0 <= i < H and 0 <= j < W:
            z = self.m.ground_z[i, j]
            if np.isfinite(z) and z - self.road_z <= self.max_step:
                return float(z)
        return self.default

    def __call__(self, points, x, y):
        return self.at(x, y)


def anchor_points(scene: SceneMap, edge_m: float = 4.0, pc_range=(-40, -40, -5, 40, 40, 5)) -> np.ndarray:
    """(N, 2) centres of the curbside cells (walkable within edge_m of the road): where clutter anchors stand."""
    dom = scene.dominant()
    walk = np.isin(dom, [TAGS["sidewalk"], TAGS["terrain"], TAGS["roadline"]])
    m = walk & (scene.distance_to(dom == TAGS["road"]) <= edge_m)
    X, Y = scene.centres()
    x0, y0, _, x1, y1, _ = pc_range
    m &= (X > x0) & (X < x1) & (Y > y0) & (Y < y1)
    return np.stack([X[m], Y[m]], 1)


def structure_points(scene: SceneMap, min_road_m: float = 2.0, beyond_m: float = 12.0,
                     pc_range=(-40, -40, -5, 40, 40, 5)) -> tuple[np.ndarray, np.ndarray]:
    """Cells where static structure may stand: terrain or sidewalk at least min_road_m from the road, and cells beyond
    the twin's modelled ground (up to beyond_m past it). Returns ((N, 2) centres, (N,) metres to the road)."""
    dom = scene.dominant()
    d_road = scene.distance_to(dom == TAGS["road"])
    d_ground = scene.distance_to(dom > 0)
    m = ((np.isin(dom, [TAGS["sidewalk"], TAGS["terrain"]]) & (d_road >= min_road_m))
         | ((dom == 0) & (d_ground <= beyond_m) & (d_road >= min_road_m)))
    X, Y = scene.centres()
    x0, y0, _, x1, y1, _ = pc_range
    m &= (X > x0) & (X < x1) & (Y > y0) & (Y < y1)
    return np.stack([X[m], Y[m]], 1), d_road[m]
