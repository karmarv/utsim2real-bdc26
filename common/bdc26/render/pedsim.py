"""Procedural pedestrians ray-cast with a real sensor rig and inserted ray-consistently into a frame (engine G1).

Why: neither UT dataset contains a single walking pedestrian (UT-LUMPI has no Person class, UT-V2X only
riders), while Person is 1/7 of the LUMPI score and pedestrians are 62% of the V2X test objects.

Pieces:
  Sensor        one spinning lidar: pose in the frame (4x4 sensor -> frame), per-beam elevation table, azimuth step
  human()       an articulated walker as 16 ellipsoids (body frame: feet at z=0, facing +x), parameterized by
                height, build, gait phase and stride; accessories (backpack) optional
  cast_ellipsoids()  analytic ray / ellipsoid intersection, vectorized
  assign_sensor()    which sensor produced each frame point (beam-quantization residual), for occlusion
  insert_pedestrians()  places walkers, casts every sensor's rays at them, removes the frame points they
                occlude (exact ray test), and drops walker returns hidden behind existing geometry (per-sensor
                range image built from the frame's own points)

Everything is synthetic: real data only enters through sensor metadata (poses, beam tables) and label
statistics (box sizes, placement), both allowed by the Rules tab. No real point is copied.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..boxes import bev_corners


# --------------------------------------------------------------------------------------------
# Sensors
# --------------------------------------------------------------------------------------------
@dataclass
class Sensor:
    T: np.ndarray                    # 4x4 sensor -> frame
    elev_deg: np.ndarray             # per-beam elevation (any order)
    az_res_deg: float                # azimuth step between columns
    min_range: float = 0.5
    max_range: float = 120.0
    name: str = ""
    beams: np.ndarray = field(init=False)
    n_cols: int = field(init=False)

    def __post_init__(self):
        self.T = np.asarray(self.T, dtype=np.float64)
        self.elev_deg = np.asarray(self.elev_deg, dtype=np.float64)
        self.beams = np.sort(self.elev_deg)
        self.n_cols = int(round(360.0 / self.az_res_deg))

    @property
    def origin(self) -> np.ndarray:
        return self.T[:3, 3]

    def to_sensor(self, p: np.ndarray) -> np.ndarray:
        return (np.asarray(p, dtype=np.float64) - self.origin) @ self.T[:3, :3]

    def spherical(self, p: np.ndarray):
        q = self.to_sensor(p)
        rxy = np.hypot(q[:, 0], q[:, 1])
        return (np.degrees(np.arctan2(q[:, 1], q[:, 0])), np.degrees(np.arctan2(q[:, 2], rxy)),
                np.sqrt(rxy ** 2 + q[:, 2] ** 2))

    def beam_index(self, el_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Nearest beam (index into the sorted table) and the residual in degrees."""
        b = self.beams
        i = np.clip(np.searchsorted(b, el_deg), 1, len(b) - 1)
        left = np.abs(el_deg - b[i - 1]) <= np.abs(el_deg - b[i])
        idx = np.where(left, i - 1, i)
        return idx, np.abs(el_deg - b[idx])

    def col_index(self, az_deg: np.ndarray) -> np.ndarray:
        return np.mod(np.round(az_deg / self.az_res_deg).astype(np.int64), self.n_cols)


def assign_sensor(points: np.ndarray, sensors: list[Sensor], tol_deg: float = 0.08) -> np.ndarray:
    """(N,) index of the sensor whose beam table best explains each point; -1 if none within tol_deg.

    With one sensor every point is assigned to it (its native pattern may differ from the table)."""
    if len(sensors) == 1:
        return np.zeros(len(points), dtype=np.int64)
    res = np.stack([s.beam_index(s.spherical(points)[1])[1] for s in sensors], 1)
    best = res.argmin(1)
    best[res.min(1) > tol_deg] = -1
    return best


# --------------------------------------------------------------------------------------------
# Walker model
# --------------------------------------------------------------------------------------------
def _frame_from_axis(u: np.ndarray) -> np.ndarray:
    """3x3 rotation whose third column is the unit vector u."""
    u = u / np.linalg.norm(u)
    a = np.array([1.0, 0.0, 0.0]) if abs(u[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = np.cross(a, u)
    e1 /= np.linalg.norm(e1)
    return np.stack([e1, np.cross(u, e1), u], 1)


def _segment(p0, p1, r) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    return (p0 + p1) / 2, np.array([r, r, L / 2 + 0.3 * r]), _frame_from_axis(p1 - p0)


@dataclass
class Walker:
    centers: np.ndarray     # (K, 3) body frame
    radii: np.ndarray       # (K, 3)
    rots: np.ndarray        # (K, 3, 3), columns = local axes in the body frame

    def extent(self) -> np.ndarray:
        """Axis-aligned extent [xmin, ymin, zmin, xmax, ymax, zmax] in the body frame (ellipsoid bounds)."""
        half = np.sqrt(np.einsum("kij,kj->ki", self.rots ** 2, self.radii ** 2))
        return np.r_[(self.centers - half).min(0), (self.centers + half).max(0)]


def human(height: float, rng: np.random.Generator, shoulder: float | None = None, phase: float | None = None,
          stride_deg: float | None = None, backpack_prob: float = 0.15, depth_range=(0.9, 1.15),
          arm_swing: float = 0.8, sidebag_prob: float = 0.0, front_item_prob: float = 0.0) -> Walker:
    """An adult walker (or a standing person when stride_deg is ~0); feet on z=0, facing +x.

    depth_range scales the torso front-to-back (clothing); arm_swing is the arm/leg swing ratio; side bags
    and carried items add mass beside or in front of the body. Defaults reproduce the G1 v1 walker."""
    H = float(height)
    s = H / 1.75
    sw = float(shoulder) if shoulder is not None else float(np.clip(rng.normal(0.43, 0.03) * s, 0.36, 0.52))
    ph = float(rng.uniform(0, 2 * np.pi)) if phase is None else float(phase)
    A = np.radians(float(rng.choice([rng.uniform(0, 4), rng.uniform(14, 30)], p=[0.25, 0.75]))
                   if stride_deg is None else stride_deg)
    depth = float(rng.uniform(*depth_range))
    C, R, Q = [], [], []

    def add(c, r, q=np.eye(3)):
        C.append(np.asarray(c, float)); R.append(np.asarray(r, float)); Q.append(q)

    add([0, 0, H - 0.115 * s], [0.095 * s, 0.08 * s, 0.115 * s])                        # head
    add([0, 0, H - 0.25 * s], [0.05 * s, 0.05 * s, 0.06 * s])                           # neck
    add([0.0, 0, 0.715 * H], [0.115 * s * depth, sw / 2 - 0.035, 0.14 * H])             # chest
    add([0.0, 0, 0.565 * H], [0.105 * s * depth, sw / 2 - 0.06, 0.085 * H])             # abdomen / pelvis
    for side, sgn in ((1, 1.0), (-1, -1.0)):
        # legs: thigh swing +/-A, knee flexes on the forward swing
        swing = sgn * A * np.sin(ph)
        knee = max(0.0, 1.2 * A * np.sin(ph + sgn * np.pi / 2))
        hip = np.array([0.0, side * 0.09 * s, 0.52 * H])
        lt, ls = 0.245 * H, 0.245 * H
        kneep = hip + lt * np.array([np.sin(swing), 0, -np.cos(swing)])
        a2 = swing - knee
        ankle = kneep + ls * np.array([np.sin(a2), 0, -np.cos(a2)])
        ankle[2] = max(ankle[2], 0.045 * s)
        add(*_segment(hip, kneep, 0.075 * s))
        add(*_segment(kneep, ankle, 0.055 * s))
        add(ankle + np.array([0.05 * s, 0, -0.01 * s]), [0.12 * s, 0.045 * s, 0.035 * s])  # foot
        # arms swing opposite to the leg on the same side
        aswing = -arm_swing * swing
        sh = np.array([0.0, side * (sw / 2), 0.815 * H])
        elbow = sh + 0.19 * H * np.array([np.sin(aswing), side * 0.06, -np.cos(aswing)])
        fa = aswing + abs(aswing) * 0.6 + np.radians(8)
        wrist = elbow + 0.16 * H * np.array([np.sin(fa), 0, -np.cos(fa)])
        add(*_segment(sh, elbow, 0.045 * s))
        add(*_segment(elbow, wrist, 0.038 * s))
    if rng.uniform() < backpack_prob:
        add([-0.115 * s * depth - 0.09, 0, 0.70 * H], [0.10, sw / 2 - 0.08, 0.17])
    if rng.uniform() < sidebag_prob:
        side = rng.choice([-1.0, 1.0])
        add([rng.uniform(-0.05, 0.08), side * (sw / 2 + 0.06), 0.50 * H], [0.14, 0.06, 0.14])
    if rng.uniform() < front_item_prob:
        add([0.115 * s * depth + 0.12, 0, 0.62 * H], [0.10, 0.16, 0.12])
    return Walker(np.array(C), np.array(R), np.array(Q))


def place(w: Walker, x: float, y: float, z_ground: float, yaw: float) -> Walker:
    c, s = np.cos(yaw), np.sin(yaw)
    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return Walker(w.centers @ Rz.T + np.array([x, y, z_ground]), w.radii, np.einsum("ij,kjl->kil", Rz, w.rots))


# --------------------------------------------------------------------------------------------
# Ray casting
# --------------------------------------------------------------------------------------------
def cast_ellipsoids(origin: np.ndarray, dirs: np.ndarray, w: Walker) -> np.ndarray:
    """(N,) nearest positive hit distance of rays origin + t*dirs (unit dirs) with the walker; inf if none."""
    if len(dirs) == 0:
        return np.zeros(0)
    ol = np.einsum("kj,kjm->km", origin[None, :] - w.centers, w.rots) / w.radii          # (K,3)
    dl = np.einsum("nj,kjm->nkm", dirs, w.rots) / w.radii[None]                            # (N,K,3)
    a = (dl ** 2).sum(-1)
    b = 2 * (dl * ol[None]).sum(-1)
    c = (ol ** 2).sum(-1)[None] - 1.0
    disc = b ** 2 - 4 * a * c
    ok = disc >= 0
    sq = np.sqrt(np.where(ok, disc, 0.0))
    t = (-b - sq) / (2 * a)
    t = np.where(ok & (t > 1e-6), t, np.inf)
    return t.min(1)


def _sphere(w: Walker) -> tuple[np.ndarray, float]:
    e = w.extent()
    c = (e[:3] + e[3:]) / 2
    return c, float(np.linalg.norm(e[3:] - e[:3]) / 2)


def _rays_toward(sensor: Sensor, center: np.ndarray, radius: float):
    """Beam/column grid covering a sphere as seen by the sensor: (keys (M,) int64, dirs_frame (M,3))."""
    q = sensor.to_sensor(center[None])[0]
    dist = float(np.linalg.norm(q))
    if dist <= radius + sensor.min_range or dist - radius > sensor.max_range:
        return np.zeros(0, np.int64), np.zeros((0, 3))
    ang = np.degrees(np.arcsin(min(1.0, radius / dist)))
    az_c = np.degrees(np.arctan2(q[1], q[0]))
    el_c = np.degrees(np.arctan2(q[2], np.hypot(q[0], q[1])))
    bi = np.nonzero(np.abs(sensor.beams - el_c) <= ang)[0]
    span = ang / max(np.cos(np.radians(min(abs(el_c) + ang, 89.0))), 1e-3)
    k0, k1 = int(np.ceil((az_c - span) / sensor.az_res_deg)), int(np.floor((az_c + span) / sensor.az_res_deg))
    ks = np.arange(k0, k1 + 1)
    if len(bi) == 0 or len(ks) == 0:
        return np.zeros(0, np.int64), np.zeros((0, 3))
    B, K = np.meshgrid(bi, ks, indexing="ij")
    el = np.radians(sensor.beams[B.ravel()])
    az = np.radians(K.ravel() * sensor.az_res_deg)
    d = np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], 1)
    keys = B.ravel().astype(np.int64) * sensor.n_cols + np.mod(K.ravel(), sensor.n_cols)
    return keys, d @ sensor.T[:3, :3].T


@dataclass
class InsertParams:
    drop_prob: float = 0.02         # per-ray dropout on walker returns
    range_noise: float = 0.015      # m, Gaussian
    block_margin: float = 0.25      # a walker return is hidden if the frame has a return this much closer
    block_nbr: tuple = (0, 1)       # (beam, column) neighbourhood of the range-image blocking test
    occlude_eps: float = 0.05       # frame points farther than the walker hit by this much are removed
    sensor_jitter_xy: float = 0.0   # m, per (walker, sensor) offset: extrinsic calibration error and the walker's
    sensor_jitter_z: float = 0.0    # motion between the unsynchronised sensors of a merged multi-lidar frame


def insert_pedestrians(points: np.ndarray, sensor_of_point: np.ndarray, sensors: list[Sensor],
                       walkers: list[Walker], rng: np.random.Generator, p: InsertParams = InsertParams()):
    """Ray-consistent insertion. Returns (points_out (M,3), keep_mask over input points, walker_id (M,) or -1,
    hits_per_walker (W,))."""
    pts = np.asarray(points, dtype=np.float64)[:, :3]
    keep = np.ones(len(pts), dtype=bool)
    new_pts, new_wid = [], []
    hits = np.zeros(len(walkers), dtype=np.int64)
    spheres = [_sphere(w) for w in walkers]
    for si, s in enumerate(sensors):
        mine = np.nonzero(sensor_of_point == si)[0]
        az, el, rr = s.spherical(pts[mine]) if len(mine) else (np.zeros(0),) * 3
        bidx, _ = s.beam_index(el) if len(mine) else (np.zeros(0, np.int64), None)
        cidx = s.col_index(az) if len(mine) else np.zeros(0, np.int64)
        rimg = np.full((len(s.beams), s.n_cols), np.inf)
        if len(mine):
            np.minimum.at(rimg, (bidx, cidx), rr)
        # 1. walker returns: rays over the union of the walkers' angular footprints, nearest walker wins
        keys, dirs = [], []
        for c, r in spheres:
            k, d = _rays_toward(s, c, r)
            keys.append(k); dirs.append(d)
        if keys:
            keys = np.concatenate(keys); dirs = np.concatenate(dirs)
            keys, first = np.unique(keys, return_index=True)
            dirs = dirs[first]
        if len(keys):
            t = np.full(len(keys), np.inf); wid = np.full(len(keys), -1)
            for wi, (w, (c, r)) in enumerate(zip(walkers, spheres)):
                oc = c - s.origin
                along = dirs @ oc
                perp2 = (oc ** 2).sum() - along ** 2
                cand = np.nonzero((along > 0) & (perp2 <= r * r))[0]
                if len(cand) == 0:
                    continue
                tw = cast_ellipsoids(s.origin, dirs[cand], w)
                better = tw < t[cand]
                t[cand[better]] = tw[better]; wid[cand[better]] = wi
            ok = np.isfinite(t) & (t >= s.min_range) & (t <= s.max_range)
            ok &= rng.random(len(t)) >= p.drop_prob
            b, col = keys // s.n_cols, keys % s.n_cols
            # hidden behind the frame's own geometry (range image of this sensor's returns)
            db, dc = p.block_nbr
            near = np.full(len(t), np.inf)
            for ob in range(-db, db + 1):
                for oc_ in range(-dc, dc + 1):
                    bb = np.clip(b + ob, 0, len(s.beams) - 1)
                    near = np.minimum(near, rimg[bb, np.mod(col + oc_, s.n_cols)])
            ok &= ~(near < t - p.block_margin)
            tt = t[ok] + rng.normal(0, p.range_noise, ok.sum())
            hp = s.origin + dirs[ok] * tt[:, None]
            if p.sensor_jitter_xy > 0 or p.sensor_jitter_z > 0:
                off = rng.normal(0, 1, (len(walkers), 3)) * np.array([p.sensor_jitter_xy, p.sensor_jitter_xy, p.sensor_jitter_z])
                hp = hp + off[wid[ok]]
            new_pts.append(hp)
            new_wid.append(wid[ok])
            np.add.at(hits, wid[ok], 1)
        # 2. frame points of this sensor that a walker now occludes (exact ray test toward each point)
        if len(mine):
            for w, (c, r) in zip(walkers, spheres):
                oc = c - s.origin
                dist = np.linalg.norm(oc)
                v = pts[mine] - s.origin
                along = v @ (oc / dist)
                cosang = along / np.maximum(rr, 1e-9)
                cand = np.nonzero((rr > dist - r) & (cosang >= np.cos(np.arcsin(min(1.0, r / dist)))))[0]
                if len(cand) == 0:
                    continue
                d = v[cand] / rr[cand, None]
                tw = cast_ellipsoids(s.origin, d, w)
                keep[mine[cand[tw < rr[cand] - p.occlude_eps]]] = False
    out = pts[keep]
    wid_all = np.full(len(out), -1, dtype=np.int64)
    if new_pts:
        add = np.concatenate(new_pts) if new_pts else np.zeros((0, 3))
        out = np.concatenate([out, add])
        wid_all = np.concatenate([wid_all, np.concatenate(new_wid)])
    return out, keep, wid_all, hits


# --------------------------------------------------------------------------------------------
# Placement helpers
# --------------------------------------------------------------------------------------------
def bev_overlaps(box: np.ndarray, others: np.ndarray, margin: float) -> bool:
    """True if `box` (7,) grown by margin overlaps any of `others` (M,7) in BEV (separating-axis test)."""
    if len(others) == 0:
        return False
    b = np.array(box, dtype=np.float64).copy()
    b[3:5] += 2 * margin
    cb = bev_corners(b[None])[0]
    co = bev_corners(np.asarray(others, dtype=np.float64).reshape(-1, 7))
    near = np.hypot(*(others[:, :2] - b[:2]).T) < (np.hypot(b[3], b[4]) + np.hypot(others[:, 3], others[:, 4])) / 2
    for o in co[near]:
        sep = False
        for poly in (cb, o):
            for i in range(4):
                e = poly[(i + 1) % 4] - poly[i]
                n = np.array([-e[1], e[0]])
                pa, pb = cb @ n, o @ n
                if pa.max() < pb.min() or pb.max() < pa.min():
                    sep = True
                    break
            if sep:
                break
        if not sep:
            return True
    return False


def local_ground(points: np.ndarray, x: float, y: float, radius: float = 1.5, min_pts: int = 8) -> float | None:
    """Ground height near (x, y) from the frame's own points; None if the area is not observed."""
    m = (np.abs(points[:, 0] - x) < radius) & (np.abs(points[:, 1] - y) < radius)
    z = points[m, 2]
    if len(z) < min_pts:
        return None
    g = np.percentile(z, 5)
    low = z[z < g + 0.3]
    return float(np.median(low))


def is_free(points: np.ndarray, x: float, y: float, z_ground: float, radius: float = 0.35,
            z_lo: float = 0.3, z_hi: float = 1.9, max_pts: int = 2) -> bool:
    """No structure (pole, wall, vegetation) inside the walker's column."""
    m = (np.hypot(points[:, 0] - x, points[:, 1] - y) < radius)
    z = points[m, 2] - z_ground
    return int(np.sum((z > z_lo) & (z < z_hi))) <= max_pts
