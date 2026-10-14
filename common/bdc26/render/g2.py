"""Engine G2-lite (strategy R3, docs/02-STRATEGY.md Section 8.7): objects re-rendered as meshes with the real sensor
rig and inserted ray-consistently, after the actor scale fix.

Why (R3 review): on LUMPI every UT actor class except the ray-cast walkers has 0.33-0.6x the real point density at
the same range (Car 230 vs 505 points at 10-20 m), because UT renders the actors at 0.78x size and the scale fix
stretches their points by 1/0.78 afterwards (fewer returns spread over the true size); UT two-wheelers have 8-11
points against 64-82 for real ones (riders included); the UT bus is a single 10.27 x 3.94 x 4.25 m asset (real
12.0 x 2.9 x 3.3 m); synthetic trucks stop at 8.47 m (real 5.6-17 m); and the twin has none of the poles, signs,
trees and bins that cause most walker false positives (S2-S5). Pieces:

  mesh primitives      box, vertical cylinder, ellipsoid (triangle meshes, local frame: base at z=0, facing +x)
  hull_mesh            convex hull of an actor's own (scaled) points in its box frame, stretched per axis to target
                       dimensions about the box bottom; vehicle_template when the actor has too few points
  rider_mesh           a two-wheeler (wheels, frame or motorcycle body) with a seated rider, fitted to a label box
  clutter_mesh         pole (with sign or arm), tree, bollard, utility box, bin, barrier: unlabeled hard negatives
  insert_meshes        per sensor: rays over the objects' angular footprints cast against one Open3D (Embree)
                       scene of all object meshes, returns hidden behind the frame's own geometry dropped (range
                       image), frame points that a new object occludes removed (exact ray test)
  G2Pass               the per-frame pass used by convert_ut_frame(post_inserter=...): re-casts the chosen actor
                       classes, replaces two-wheelers by riders, adds clutter, returns the new points and boxes

Everything is synthetic: real data enters only through sensor metadata and legal label statistics (sizes, walker
positions as clutter anchors), as for engine G1.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..boxes import points_in_boxes
from .pedsim import InsertParams, Sensor, _rays_toward, bev_overlaps, is_free


# --------------------------------------------------------------------------------------------
# Mesh primitives (local frame: base at z = 0, +x forward)
# --------------------------------------------------------------------------------------------
def box_mesh(l: float, w: float, h: float, z0: float = 0.0, x0: float = 0.0, y0: float = 0.0):
    x, y = np.array([-l / 2, l / 2]) + x0, np.array([-w / 2, w / 2]) + y0
    z = np.array([z0, z0 + h])
    V = np.array([[x[i], y[j], z[k]] for k in range(2) for j in range(2) for i in range(2)], dtype=np.float64)
    F = np.array([[0, 2, 1], [1, 2, 3], [4, 5, 6], [5, 7, 6], [0, 1, 4], [1, 5, 4],
                  [2, 6, 3], [3, 6, 7], [0, 4, 2], [2, 4, 6], [1, 3, 5], [3, 7, 5]], dtype=np.int64)
    return V, F


def cylinder_mesh(r: float, h: float, z0: float = 0.0, n: int = 12, x0: float = 0.0, y0: float = 0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.stack([r * np.cos(a) + x0, r * np.sin(a) + y0], 1)
    V = np.concatenate([np.c_[ring, np.full(n, z0)], np.c_[ring, np.full(n, z0 + h)], [[x0, y0, z0], [x0, y0, z0 + h]]])
    F = []
    for i in range(n):
        j = (i + 1) % n
        F += [[i, j, n + i], [j, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
    return V, np.array(F, dtype=np.int64)


def ellipsoid_mesh(center, radii, R=np.eye(3), n: int = 8):
    """UV ellipsoid: n latitude bands, 2n longitudes; R columns = local axes."""
    th = np.linspace(0, np.pi, n + 1)[1:-1]
    ph = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing="ij")
    unit = np.stack([np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), np.cos(T)], -1).reshape(-1, 3)
    unit = np.concatenate([unit, [[0, 0, 1], [0, 0, -1]]])
    V = (unit * np.asarray(radii, float)) @ np.asarray(R, float).T + np.asarray(center, float)
    m, F = 2 * n, []
    top, bot = len(unit) - 2, len(unit) - 1
    for i in range(n - 2):
        for j in range(m):
            a, b, c, d = i * m + j, i * m + (j + 1) % m, (i + 1) * m + j, (i + 1) * m + (j + 1) % m
            F += [[a, c, b], [b, c, d]]
    for j in range(m):
        F += [[top, j, (j + 1) % m], [bot, (n - 2) * m + (j + 1) % m, (n - 2) * m + j]]
    return V, np.array(F, dtype=np.int64)


def _axis_frame(u):
    u = np.asarray(u, float) / np.linalg.norm(u)
    a = np.array([1.0, 0.0, 0.0]) if abs(u[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = np.cross(a, u); e1 /= np.linalg.norm(e1)
    return np.stack([e1, np.cross(u, e1), u], 1)


def segment_mesh(p0, p1, r: float, n: int = 6):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    return ellipsoid_mesh((p0 + p1) / 2, [r, r, L / 2 + 0.3 * r], _axis_frame(p1 - p0), n)


def merge(parts):
    Vs, Fs, k = [], [], 0
    for V, F in parts:
        Vs.append(V); Fs.append(F + k); k += len(V)
    return np.concatenate(Vs), np.concatenate(Fs)


def place_mesh(V, x, y, z, yaw):
    c, s = np.cos(yaw), np.sin(yaw)
    return V @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]]).T + np.array([x, y, z])


def to_box_frame(points, box):
    """Points in the box frame with the origin at the box BOTTOM centre."""
    c, s = np.cos(box[6]), np.sin(box[6])
    d = np.asarray(points, float)[:, :3] - np.array([box[0], box[1], box[2] - box[5] / 2])
    return np.stack([c * d[:, 0] + s * d[:, 1], -s * d[:, 0] + c * d[:, 1], d[:, 2]], 1)


# --------------------------------------------------------------------------------------------
# Assets
# --------------------------------------------------------------------------------------------
def vehicle_template(l, w, h, kind="car"):
    """Coarse vehicle when an actor has too few points for a hull: car = body + cabin, else a box body."""
    if kind == "car":
        return merge([box_mesh(l, w, 0.42 * h, z0=0.16 * h), box_mesh(0.55 * l, 0.92 * w, 0.42 * h, z0=0.58 * h, x0=-0.08 * l)])
    return merge([box_mesh(l, w, 0.88 * h, z0=0.12 * h)])


def hull_mesh(local_points, cur_lwh, target_lwh, min_points=40, kind="car", mirror=True, exemplar=None):
    """Convex hull of the actor's points (box frame, bottom origin), stretched about the bottom centre from the
    current box dimensions to the target ones; vehicle_template(target) if the hull is not usable. mirror: add the
    points mirrored about the box's long axis first (vehicles are left-right symmetric), so an actor seen from one
    side only still gets its full width instead of a wedge. exemplar: hull vertices of a well-sampled actor of the
    class in the same frame (fitted to cur_lwh), joined to the actor's points (sparse actors: R3 measured hulls of
    0.44 of the box volume at 40-100 points against 0.65 for well-sampled UT cars), and used alone below min_points."""
    from scipy.spatial import ConvexHull, QhullError
    sx, sy, sz = (np.asarray(target_lwh, float) / np.maximum(np.asarray(cur_lwh, float), 1e-3))
    local_points = np.asarray(local_points, float).reshape(-1, 3)
    if exemplar is not None:
        local_points = np.concatenate([local_points, exemplar]) if len(local_points) >= min_points else np.asarray(exemplar, float)
    if len(local_points) >= min_points or exemplar is not None:
        q = np.asarray(local_points, float) * np.array([sx, sy, sz])
        if mirror:
            q = np.concatenate([q, q * np.array([1.0, -1.0, 1.0])])
        try:
            h = ConvexHull(q)
            return q, h.simplices.astype(np.int64)
        except (QhullError, ValueError):
            pass
    return vehicle_template(*target_lwh, kind=kind)


def rider_mesh(l, w, h, kind, rng):
    """A two-wheeler with a seated rider filling the label box (l, w, h): wheels as thin discs, a frame of tubes
    (bicycle) or a body block (motorcycle), and a rider leaning forward with hands on the bar, head near the top."""
    moto = kind == "motorcycle"
    rw = float(np.clip(rng.uniform(0.30, 0.36) if not moto else rng.uniform(0.29, 0.34), 0.25, l / 4))
    xw = l / 2 - rw - 0.02
    tw = 0.05 if not moto else rng.uniform(0.10, 0.16)
    parts = [ellipsoid_mesh([xw, 0, rw], [rw, tw / 2, rw]), ellipsoid_mesh([-xw, 0, rw], [rw, tw / 2, rw])]
    seat = np.array([-0.18 * l, 0.0, rng.uniform(0.82, 0.95) if not moto else rng.uniform(0.70, 0.82)])
    bar = np.array([0.30 * l, 0.0, rng.uniform(0.95, 1.08) if not moto else rng.uniform(0.92, 1.02)])
    if moto:
        parts += [ellipsoid_mesh([0.0, 0, 0.52], [0.42 * l / 2, max(w * 0.22, 0.16), 0.24]),
                  segment_mesh([0.15 * l, 0, rw + 0.05], bar, 0.05)]
    else:
        bb = np.array([0.0, 0, rw + 0.02])
        for a, b in ((bb, seat - [0, 0, 0.05]), (bb, bar - [0.05, 0, 0.1]), (seat - [0, 0, 0.05], bar - [0.05, 0, 0.1]),
                     (bb, [-xw, 0, rw]), (bar - [0.05, 0, 0.1], [xw, 0, rw])):
            parts.append(segment_mesh(a, b, 0.025))
    top = h - rng.uniform(0.02, 0.10)
    head_r = 0.11 if not moto else 0.15                       # helmet on a motorcycle
    lean = np.radians(rng.uniform(20, 45) if not moto else rng.uniform(10, 30))
    shoulder_z = top - 2 * head_r - 0.06
    torso_len = max(shoulder_z - seat[2], 0.3) / np.cos(lean)
    shoulder = seat + np.array([torso_len * np.sin(lean), 0, torso_len * np.cos(lean)])
    sw = float(np.clip(w - rng.uniform(0.15, 0.30), 0.34, 0.50))
    parts.append(segment_mesh(seat + [0, 0, 0.08], shoulder, 0.15 * (sw / 0.42)))
    parts.append(ellipsoid_mesh(shoulder + [0.04, 0, head_r + 0.06], [head_r, head_r * 0.9, head_r * 1.1]))
    phase = rng.uniform(0, 2 * np.pi)
    for side in (1.0, -1.0):
        sh = shoulder + [0, side * sw / 2, -0.03]
        hand = bar + [0, side * min(w / 2 - 0.05, 0.30), 0]
        elbow = (sh + hand) / 2 + [0, side * 0.04, -0.06]
        parts += [segment_mesh(sh, elbow, 0.045), segment_mesh(elbow, hand, 0.04)]
        hip = seat + [0, side * 0.10, 0.02]
        pedal = np.array([0.02 * l + 0.17 * np.cos(phase + (0 if side > 0 else np.pi)), side * 0.14,
                          rw + 0.02 + 0.17 * np.sin(phase + (0 if side > 0 else np.pi))]) if not moto \
            else np.array([0.05 * l, side * 0.22, 0.35])
        knee = (hip + pedal) / 2 + [0.18, side * 0.03, 0.12]
        parts += [segment_mesh(hip, knee, 0.075), segment_mesh(knee, pedal, 0.055)]
    return merge(parts)


class HullBank:
    """Exemplar shapes of well-sampled UT actors, per class: hull vertices in the unit box frame (x / l, y / w, z / h,
    origin at the box bottom centre, mirrored about the long axis). Collected by running convert_ut_frame with the
    bank as post_inserter (it changes nothing), saved once per corpus recipe (synthetic UT data only)."""

    def __init__(self, classes=(), min_points: int = 800, shapes: dict | None = None):
        self.classes, self.min_points = set(classes), int(min_points)
        self.shapes = shapes if shapes is not None else {c: [] for c in self.classes}

    def __call__(self, points, boxes, names, owner, rng):
        from scipy.spatial import ConvexHull, QhullError
        pts = np.asarray(points, float)[:, :3]
        for i, (b, n) in enumerate(zip(np.asarray(boxes).reshape(-1, 7), names)):
            if str(n) not in self.classes:
                continue
            m = owner == i
            if m.sum() < self.min_points:
                continue
            q = to_box_frame(pts[m], b)
            q = np.concatenate([q, q * np.array([1.0, -1.0, 1.0])]) / np.asarray(b[3:6], float)
            try:
                self.shapes[str(n)].append(q[ConvexHull(q).vertices].astype(np.float32))
            except (QhullError, ValueError):
                pass
        return points, boxes, names, {}

    def sample(self, name, lwh, rng):
        S = self.shapes.get(str(name)) or []
        return S[rng.integers(len(S))] * np.asarray(lwh, float) if len(S) else None

    def save(self, path):
        from pathlib import Path
        out = {}
        for c, S in self.shapes.items():
            out[f"{c}__v"] = np.concatenate(S) if S else np.zeros((0, 3), np.float32)
            out[f"{c}__n"] = np.array([len(x) for x in S], dtype=np.int64)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, min_points=self.min_points, **out)

    @classmethod
    def load(cls, path) -> "HullBank":
        d = np.load(path)
        shapes = {}
        for k in d.files:
            if k.endswith("__v"):
                c = k[:-3]
                shapes[c] = np.split(d[k], np.cumsum(d[f"{c}__n"])[:-1]) if len(d[f"{c}__n"]) else []
        return cls(shapes.keys(), int(d["min_points"]), shapes)

    def summary(self) -> dict:
        return {c: len(S) for c, S in self.shapes.items()}


CLUTTER_KINDS = {"pole": 0.35, "tree": 0.20, "bollard": 0.15, "utility_box": 0.15, "bin": 0.10, "barrier": 0.05}


def clutter_mesh(kind, rng):
    """Unlabeled static structure (local frame, base at z = 0). The walker-height band (0.3-1.9 m) of every kind is
    a hard negative for walkers and two-wheelers."""
    if kind == "pole":
        r, h = rng.uniform(0.05, 0.15), rng.uniform(3.0, 8.0)
        parts = [cylinder_mesh(r, h)]
        u = rng.uniform()
        if u < 0.4:                                            # sign plate
            sw_, sh_ = rng.uniform(0.4, 0.9), rng.uniform(0.4, 0.9)
            parts.append(box_mesh(0.04, sw_, sh_, z0=rng.uniform(1.9, 2.8), x0=r + 0.03))
        elif u < 0.7:                                          # street-light arm
            arm = rng.uniform(1.0, 2.5)
            parts.append(box_mesh(arm, 0.12, 0.12, z0=h - 0.3, x0=arm / 2))
        return merge(parts)
    if kind == "tree":
        r, ht = rng.uniform(0.10, 0.30), rng.uniform(2.2, 4.0)
        cr, cz = rng.uniform(1.2, 2.6), rng.uniform(1.0, 2.2)
        return merge([cylinder_mesh(r, ht + 0.5), ellipsoid_mesh([0, 0, ht + 0.8 * cz], [cr, cr * rng.uniform(0.8, 1.0), cz], n=10)])
    if kind == "bollard":
        return cylinder_mesh(rng.uniform(0.07, 0.15), rng.uniform(0.6, 1.2))
    if kind == "utility_box":
        return box_mesh(rng.uniform(0.4, 1.2), rng.uniform(0.3, 0.8), rng.uniform(0.8, 1.6))
    if kind == "bin":
        return cylinder_mesh(rng.uniform(0.25, 0.40), rng.uniform(0.8, 1.1)) if rng.uniform() < 0.5 else \
            box_mesh(rng.uniform(0.5, 0.8), rng.uniform(0.5, 0.8), rng.uniform(0.9, 1.3))
    if kind == "barrier":
        return box_mesh(rng.uniform(1.0, 2.0), rng.uniform(0.2, 0.4), rng.uniform(0.8, 1.1))
    raise ValueError(kind)


def clutter_footprint(kind) -> float:
    """Radius kept clear of labeled boxes and other clutter in BEV."""
    return {"pole": 0.4, "tree": 1.0, "bollard": 0.3, "utility_box": 0.8, "bin": 0.5, "barrier": 1.1}[kind]


# --------------------------------------------------------------------------------------------
# Ray-consistent mesh insertion
# --------------------------------------------------------------------------------------------
def sensor_candidates(points: np.ndarray, sensors: list[Sensor], tol_deg: float = 0.08) -> np.ndarray:
    """(N, S) bool: the sensors whose beam table explains each point within tol_deg (all sensors if none does).

    A merged multi-lidar frame does not record which sensor produced a point, and the beam residual alone cannot
    tell (R3 check on UT-LUMPI: azimuths are not on a column grid, and 45% of the points fit a second sensor within
    0.08 deg, mostly the Pandar64 whose 64 beams are 0.17 deg apart). Picking the best fit sends those points to a
    wrong origin, from where a new object seems to hide them: on frame 2500 that removed 49% of the frame."""
    if len(sensors) == 1:
        return np.ones((len(points), 1), dtype=bool)
    res = np.stack([s.beam_index(s.spherical(points)[1])[1] for s in sensors], 1)
    cand = res <= tol_deg
    cand[~cand.any(1)] = True
    return cand


@dataclass
class MeshObj:
    V: np.ndarray            # (n, 3) frame coordinates
    F: np.ndarray            # (m, 3)
    box_index: int = -1      # index of its label box (in the boxes passed to the pass), -1 for clutter
    drop: float | tuple | None = None  # per-ray drop probability (None: InsertParams.drop_prob); (near, far, r0, r1):
                                       # near up to hit range r0, far from r1, linear in between

    def sphere(self):
        lo, hi = self.V.min(0), self.V.max(0)
        c = (lo + hi) / 2
        return c, float(np.linalg.norm(hi - lo) / 2)


def _drop_ramp(d) -> tuple:
    if np.ndim(d) == 0:
        return (float(d), float(d), 0.0, 1.0)
    dn, df, r0, r1 = (float(v) for v in d)
    return (dn, df, r0, r1)


def insert_meshes(points: np.ndarray, sensor_of_point: np.ndarray, sensors: list[Sensor], objects: list[MeshObj],
                  rng: np.random.Generator, p: InsertParams = InsertParams(), nthreads: int = 1):
    """Returns (points_out (M,3), keep_mask over input points, object_id (M,) or -1, hits_per_object (K,)).
    sensor_of_point: (N,) sensor index (-1: none) or an (N, S) bool candidate mask (sensor_candidates). A frame point
    is removed only if a new object hides it from every candidate sensor, and it enters the blocking range image of
    each candidate. Per-ray dropout uses each object's own `drop` (glass and dark paint return less than a closed
    hull). nthreads=1: one Embree thread per call (the corpus builders run one process per core)."""
    import open3d as o3d
    pts = np.asarray(points, dtype=np.float64)[:, :3]
    keep = np.ones(len(pts), dtype=bool)
    hits = np.zeros(len(objects), dtype=np.int64)
    cand = np.asarray(sensor_of_point)
    if cand.ndim == 1:
        cand = cand[:, None] == np.arange(len(sensors))[None, :]
    hidden = np.ones(len(pts), dtype=bool) & cand.any(1)       # hidden from every candidate sensor tested so far
    if not objects:
        return pts.copy(), keep, np.full(len(pts), -1, dtype=np.int64), hits
    scene = o3d.t.geometry.RaycastingScene(nthreads=nthreads)
    gid2obj = {}
    for k, ob in enumerate(objects):
        g = scene.add_triangles(o3d.core.Tensor(ob.V.astype(np.float32)), o3d.core.Tensor(ob.F.astype(np.uint32)))
        gid2obj[int(g)] = k
    lut = np.full(max(gid2obj) + 2, -1, dtype=np.int64)
    for g, k in gid2obj.items():
        lut[g] = k
    spheres = [ob.sphere() for ob in objects]
    drops = np.array([_drop_ramp(p.drop_prob if ob.drop is None else ob.drop) for ob in objects])   # (K, 4)

    def cast(origin, dirs):
        rays = np.concatenate([np.broadcast_to(origin, dirs.shape), dirs], 1).astype(np.float32)
        r = scene.cast_rays(o3d.core.Tensor(rays), nthreads=nthreads)
        t = r["t_hit"].numpy().astype(np.float64)
        g = r["geometry_ids"].numpy().astype(np.int64)
        obj = np.where(np.isfinite(t) & (g >= 0) & (g < len(lut)), lut[np.clip(g, 0, len(lut) - 1)], -1)
        return np.where(obj >= 0, t, np.inf), obj

    new_pts, new_id = [], []
    for si, s in enumerate(sensors):
        mine = np.nonzero(cand[:, si])[0]
        rimg = np.full((len(s.beams), s.n_cols), np.inf)
        if len(mine):
            az, el, rr = s.spherical(pts[mine])
            bidx, _ = s.beam_index(el)
            cidx = s.col_index(az)
            np.minimum.at(rimg, (bidx, cidx), rr)
        keys, dirs = [], []
        for c, r in spheres:
            k, d = _rays_toward(s, c, r)
            keys.append(k); dirs.append(d)
        keys = np.concatenate(keys); dirs = np.concatenate(dirs)
        if len(keys):
            keys, first = np.unique(keys, return_index=True)
            dirs = dirs[first]
            t, obj = cast(s.origin, dirs)
            ok = np.isfinite(t) & (t >= s.min_range) & (t <= s.max_range)
            dn, df, r0, r1 = drops[np.clip(obj, 0, None)].T
            dr = dn + (df - dn) * np.clip((np.where(np.isfinite(t), t, 0.0) - r0) / np.maximum(r1 - r0, 1e-6), 0.0, 1.0)
            ok &= rng.random(len(t)) >= np.where(obj >= 0, dr, 1.0)
            b, col = keys // s.n_cols, keys % s.n_cols
            db, dc = p.block_nbr
            near = np.full(len(t), np.inf)
            for ob_ in range(-db, db + 1):
                for oc_ in range(-dc, dc + 1):
                    near = np.minimum(near, rimg[np.clip(b + ob_, 0, len(s.beams) - 1), np.mod(col + oc_, s.n_cols)])
            ok &= ~(near < t - p.block_margin)
            tt = t[ok] + rng.normal(0, p.range_noise, ok.sum())
            hp = s.origin + dirs[ok] * tt[:, None]
            if p.sensor_jitter_xy > 0 or p.sensor_jitter_z > 0:
                off = rng.normal(0, 1, (len(objects), 3)) * np.array([p.sensor_jitter_xy, p.sensor_jitter_xy, p.sensor_jitter_z])
                hp = hp + off[obj[ok]]
            new_pts.append(hp); new_id.append(obj[ok])
            np.add.at(hits, obj[ok], 1)
        if len(mine):                                         # frame points the new objects now occlude
            v = pts[mine] - s.origin
            rr = np.linalg.norm(v, axis=1)
            t, _ = cast(s.origin, v / np.maximum(rr, 1e-9)[:, None])
            hidden[mine[t >= rr - p.occlude_eps]] = False
    keep = ~hidden
    out = pts[keep]
    ids = np.full(len(out), -1, dtype=np.int64)
    if new_pts:
        out = np.concatenate([out, np.concatenate(new_pts)])
        ids = np.concatenate([ids, np.concatenate(new_id)])
    return out, keep, ids, hits


# --------------------------------------------------------------------------------------------
# The per-frame pass
# --------------------------------------------------------------------------------------------
@dataclass
class G2Config:
    recast: dict = field(default_factory=dict)          # class -> template kind ("car", "box"): re-cast from the hull
    resize: dict = field(default_factory=dict)          # class -> (N, 3) real l, w, h samples: re-cast at a real size
    stretch: dict = field(default_factory=dict)         # class -> {"prob": p, "lengths": (N,) real lengths}
    riders: dict = field(default_factory=dict)          # class -> "bicycle" | "motorcycle" (sizes from resize)
    clutter_mean: float = 0.0
    clutter_anchor_xy: np.ndarray | None = None         # walker positions: clutter placed 1-4 m from them
    anchor_share: float = 0.6
    drop: dict = field(default_factory=dict)            # class (or "clutter") -> per-ray drop probability
    bank: HullBank | None = None                        # exemplar shapes joined to sparse actors
    complete_below: int = 400                           # actors with fewer points get an exemplar joined
    fit_step: float = 0.5                               # m: a real-size actor without room is shortened in these steps
    min_hull_points: int = 40
    params: InsertParams = field(default_factory=InsertParams)


@dataclass
class G2Pass:
    sensors: list[Sensor]
    cfg: G2Config
    ground: object                                      # callable(points, x, y) -> z or None
    pc_range: list
    assign_tol_deg: float = 0.08

    def _target_lwh(self, name, lwh, rng):
        if name in self.cfg.resize:
            S = self.cfg.resize[name]
            return S[rng.integers(len(S))] * rng.uniform(0.97, 1.03, 3)
        return np.array(lwh, float)

    def _fit_box(self, i, b, name, boxes, rng):
        """The re-cast box of actor i: one target size (resize sample, stretch), tried centred, with its front kept and
        with its rear kept; if no placement is clear of the other boxes in BEV, the target is shortened in steps of
        fit_step m, never below the current length, until one is. Resampling instead would bias the sizes short
        (R3: buses median 8.9 m against the real 12.0 m), and one centred try left 53% of the LUMPI trucks and 63% of
        the buses at the UT size. Returns (box, target, grown); the current box when nothing fits."""
        others = np.delete(boxes, i, axis=0)
        bottom = b[2] - b[5] / 2
        c, s_ = np.cos(b[6]), np.sin(b[6])
        target = self._target_lwh(name, b[3:6], rng)
        if name in self.cfg.stretch and rng.uniform() < self.cfg.stretch[name]["prob"]:
            L = self.cfg.stretch[name]["lengths"]
            target = target.copy(); target[0] = max(target[0], float(L[rng.integers(len(L))]))
        lengths = [target[0]]
        if target[0] > b[3]:
            lengths += list(np.arange(target[0] - self.cfg.fit_step, b[3], -self.cfg.fit_step)) + [b[3]]
        for L in lengths:
            t = np.array([L, target[1], target[2]])
            nb = b.copy(); nb[3:6] = t; nb[2] = bottom + t[2] / 2
            if not (t[0] > b[3] * 1.05 or t[1] > b[4] * 1.05):
                return nb, t, False
            dl = (t[0] - b[3]) / 2
            for shift in (0.0, -dl, dl):                     # centred, front kept, rear kept
                cand = nb.copy(); cand[0] += shift * c; cand[1] += shift * s_
                if not bev_overlaps(cand, others, 0.1):
                    return cand, t, True
        return b.copy(), np.array(b[3:6]), False

    def __call__(self, points, boxes, names, owner, rng):
        """points (N,3) after the scale fix, boxes (M,7) and names (M,), owner (N,) box index or -1.
        Returns (points_out, boxes_out, names_out, stats)."""
        pts = np.asarray(points, dtype=np.float64)[:, :3]
        boxes = np.array(boxes, dtype=np.float64).reshape(-1, 7)
        names = np.asarray(names, dtype=object)
        objects, drop = [], np.zeros(len(pts), dtype=bool)
        st = {"g2_recast": 0, "g2_riders": 0, "g2_resized": 0, "g2_grown": 0, "g2_clutter": 0, "g2_completed": 0}
        for i, (b, n) in enumerate(zip(boxes, names)):
            n = str(n)
            if n not in self.cfg.recast and n not in self.cfg.riders:
                continue
            nb, target, grown = self._fit_box(i, b, n, boxes, rng)
            st["g2_resized"] += int(np.abs(np.asarray(target) - b[3:6]).max() > 0.05)
            mine = owner == i
            if n in self.cfg.riders:
                V, F = rider_mesh(target[0], target[1], target[2], self.cfg.riders[n], rng)
                st["g2_riders"] += 1
            else:
                loc = to_box_frame(pts[mine], b)
                ex = self.cfg.bank.sample(n, b[3:6], rng) if self.cfg.bank is not None and len(loc) < self.cfg.complete_below else None
                V, F = hull_mesh(loc, b[3:6], target, self.cfg.min_hull_points, self.cfg.recast[n], exemplar=ex)
                st["g2_completed"] = st.get("g2_completed", 0) + int(ex is not None)
                st["g2_recast"] += 1
                st["g2_grown"] += int(grown)
            objects.append(MeshObj(place_mesh(V, nb[0], nb[1], nb[2] - nb[5] / 2, nb[6]), F, i, self.cfg.drop.get(n)))
            drop |= mine
            boxes[i] = nb
        if self.cfg.clutter_mean > 0:
            for kind, x, y, z in self._clutter_poses(pts[~drop], boxes, rng):
                V, F = clutter_mesh(kind, rng)
                objects.append(MeshObj(place_mesh(V, x, y, z, rng.uniform(-np.pi, np.pi)), F, -1, self.cfg.drop.get("clutter")))
                st["g2_clutter"] += 1
        base = pts[~drop]
        sensor_of = sensor_candidates(base, self.sensors, self.assign_tol_deg)
        out, keep, oid, hits = insert_meshes(base, sensor_of, self.sensors, objects, rng, self.cfg.params)
        st["g2_hits_median"] = float(np.median(hits)) if len(hits) else 0.0
        st["g2_occluded_removed"] = int((~keep).sum())
        return out.astype(np.float32), boxes, names, st

    def _clutter_poses(self, pts, boxes, rng):
        x0, y0, _, x1, y1, _ = self.pc_range
        n = int(rng.poisson(self.cfg.clutter_mean))
        placed, out, tries = [], [], 0
        sensor_xy = np.array([s.origin[:2] for s in self.sensors])
        kinds, probs = list(CLUTTER_KINDS), np.array(list(CLUTTER_KINDS.values()))
        while len(out) < n and tries < 8 * n:
            tries += 1
            kind = str(rng.choice(kinds, p=probs / probs.sum()))
            A = self.cfg.clutter_anchor_xy
            if A is not None and len(A) and rng.uniform() < self.cfg.anchor_share:
                a = A[rng.integers(len(A))]; d = rng.uniform(1.0, 4.0); t = rng.uniform(-np.pi, np.pi)
                x, y = a[0] + d * np.cos(t), a[1] + d * np.sin(t)
            else:
                x, y = rng.uniform(x0 + 1, x1 - 1), rng.uniform(y0 + 1, y1 - 1)
            if not (x0 + 1 < x < x1 - 1 and y0 + 1 < y < y1 - 1):
                continue
            if np.min(np.hypot(*(sensor_xy - [x, y]).T)) < 2.0:
                continue
            r = clutter_footprint(kind)
            probe = np.array([x, y, 0.0, 2 * r, 2 * r, 1.0, 0.0])
            if bev_overlaps(probe, boxes, 0.3) or (placed and bev_overlaps(probe, np.array(placed), 0.2)):
                continue
            z = self.ground(pts, x, y)
            if z is None or not is_free(pts, x, y, z, radius=r):
                continue
            placed.append(probe); out.append((kind, x, y, z))
        return out


def size_prior_from_labels(root, splits, filters: dict, cache=None) -> dict:
    """{class: (N, 3) l, w, h} from legal real label files (pcdet layout, realval splits), each class kept inside its
    (lo, hi) length filter (drops mislabeled rows such as 2 m "Bus" boxes); cached as an .npz when cache is given."""
    from pathlib import Path
    from ..pcdet_export import read_labels_txt
    if cache is not None and Path(cache).exists():
        d = np.load(cache)
        return {k: d[k] for k in d.files}
    out = {c: [] for c in filters}
    for split in splits:
        for i in (Path(root) / "ImageSets" / f"{split}.txt").read_text().split():
            b, names = read_labels_txt(Path(root) / "labels" / f"{i}.txt")
            b = np.asarray(b).reshape(-1, 7)
            for c, (lo, hi) in filters.items():
                m = np.array([n == c for n in names], dtype=bool)
                if m.any():
                    s = b[m, 3:6]
                    out[c].append(s[(s[:, 0] >= lo) & (s[:, 0] <= hi)])
    res = {c: np.concatenate(v) if v else np.zeros((0, 3)) for c, v in out.items()}
    if cache is not None:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache, **res)
    return res
