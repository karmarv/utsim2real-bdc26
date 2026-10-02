"""Engine G1 (first version): UT frames plus ray-cast procedural walkers, as a convert_ut_frame inserter.

    ins = WalkerInserter(sensors, sample_pose, n_mean=16, ground=FlatGround(-2.152), pc_range=T.pc_range)
    pts, boxes, names, stats = convert_ut_frame(T, idx, params, inserter=ins)

`sample_pose(rng) -> (x, y, yaw, (l, w, h)[, z_ground])` decides where walkers go and the annotation box they get
(track-specific: LUMPI and V2X g1-v3 draw from legal real walker labels; V2X g1-v1/v2 from free ground). When it
returns z_ground (the real box bottom), the frame-based ground estimate is skipped.
`body_from_box(l, w, h, rng) -> (height, shoulder)` fits the walker inside the annotators' box.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .pedsim import InsertParams, Sensor, assign_sensor, bev_overlaps, human, insert_pedestrians, is_free, local_ground, place


@dataclass
class FlatGround:
    z: float

    def __call__(self, points, x, y):
        return self.z


@dataclass
class LocalGround:
    radius: float = 1.5
    min_pts: int = 8

    def __call__(self, points, x, y):
        return local_ground(points, x, y, self.radius, self.min_pts)


def body_from_box_default(l, w, h, rng):
    """Annotators draw person boxes with a margin: body about 6-20 cm shorter and 24-34 cm narrower."""
    return (float(np.clip(h - rng.uniform(0.06, 0.20), 1.45, 1.98)),
            float(np.clip(w - rng.uniform(0.24, 0.34), 0.36, 0.52)))


@dataclass
class WalkerInserter:
    sensors: list[Sensor]
    sample_pose: Callable
    n_mean: float
    ground: Callable
    pc_range: list
    class_name: str = "Person"
    body_from_box: Callable = body_from_box_default
    params: InsertParams = field(default_factory=InsertParams)
    min_dist_xy: float = 1.0        # from the nearest sensor
    box_margin: float = 0.3         # clearance to existing (scale-fixed) boxes
    walker_margin: float = 0.05     # clearance between walkers
    max_tries: int = 6
    assign_tol_deg: float = 0.08
    walker_style: dict = field(default_factory=dict)   # bdc26.render.pedsim.human keyword arguments
    body_yaw_sigma: float = 0.0                         # rad, body orientation scatter about the box heading

    def __call__(self, points, boxes, names, rng):
        pts = np.asarray(points, dtype=np.float64)[:, :3]
        x0, y0, _, x1, y1, _ = self.pc_range
        n = int(rng.poisson(self.n_mean))
        sensor_xy = np.array([s.origin[:2] for s in self.sensors])
        placed, walkers = [], []
        tries = 0
        while len(placed) < n and tries < n * self.max_tries:
            tries += 1
            pose = self.sample_pose(rng)                 # (x, y, yaw, (l, w, h)[, z_ground])
            x, y, yaw, (l, w, h) = pose[:4]
            z_given = pose[4] if len(pose) > 4 else None
            if not (x0 + 0.5 < x < x1 - 0.5 and y0 + 0.5 < y < y1 - 0.5):
                continue
            if np.min(np.hypot(*(sensor_xy - [x, y]).T)) < self.min_dist_xy:
                continue
            box = np.array([x, y, 0.0, l, w, h, yaw])
            if bev_overlaps(box, np.asarray(boxes).reshape(-1, 7), self.box_margin):
                continue
            if placed and bev_overlaps(box, np.array(placed), self.walker_margin):
                continue
            zg = z_given if z_given is not None else self.ground(pts, x, y)
            if zg is None or not is_free(pts, x, y, zg):
                continue
            H, sw = self.body_from_box(l, w, h, rng)
            body_yaw = yaw + (rng.normal(0, self.body_yaw_sigma) if self.body_yaw_sigma > 0 else 0.0)
            walkers.append(place(human(H, rng, shoulder=sw, **self.walker_style), x, y, zg, body_yaw))
            box[2] = zg + h / 2
            placed.append(box)
        if not walkers:
            return pts, np.ones(len(pts), dtype=bool), np.zeros((0, 7)), np.array([], dtype=object), {"n_walkers": 0}
        sensor_of = assign_sensor(pts, self.sensors, self.assign_tol_deg)
        out, keep, wid, hits = insert_pedestrians(pts, sensor_of, self.sensors, walkers, rng, self.params)
        ok = hits > 0
        # walkers without a single return are kept out of the labels (their removal of occluded points stays,
        # which is what a real unseen-but-present object would do)
        return (out, keep, np.array(placed)[ok], np.array([self.class_name] * int(ok.sum()), dtype=object),
                {"n_walkers": int(ok.sum()), "walker_hits_median": float(np.median(hits[ok])) if ok.any() else 0.0,
                 "occluded_removed": int((~keep).sum()), "unassigned_frac": float(np.mean(sensor_of < 0))})
