"""3D box geometry in the OpenPCDet / challenge convention: [x, y, z, dx, dy, dz, heading].

(x, y, z) is the box centre, (dx, dy, dz) are full extents along the box axes, heading is the rotation
about +z from +x (radians). A 180-degree heading flip does not change the box.
"""
from __future__ import annotations

import numpy as np


def limit_period(a: np.ndarray, offset: float = 0.5, period: float = 2 * np.pi) -> np.ndarray:
    return a - np.floor(a / period + offset) * period


def rot2d(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])


def bev_corners(boxes: np.ndarray) -> np.ndarray:
    """(M, 4, 2) BEV corners in counter-clockwise order."""
    b = np.asarray(boxes, dtype=np.float64).reshape(-1, 7)
    hx, hy = b[:, 3] / 2, b[:, 4] / 2
    local = np.stack([np.stack([hx, hy], -1), np.stack([-hx, hy], -1), np.stack([-hx, -hy], -1), np.stack([hx, -hy], -1)], 1)
    c, s = np.cos(b[:, 6]), np.sin(b[:, 6])
    R = np.stack([np.stack([c, -s], -1), np.stack([s, c], -1)], 1)          # (M, 2, 2)
    return np.einsum("mij,mkj->mki", R, local) + b[:, None, :2]


def boxes_center_in_range(boxes: np.ndarray, pc_range) -> np.ndarray:
    x0, y0, z0, x1, y1, z1 = pc_range
    b = np.asarray(boxes).reshape(-1, 7)
    return (b[:, 0] >= x0) & (b[:, 0] <= x1) & (b[:, 1] >= y0) & (b[:, 1] <= y1) & (b[:, 2] >= z0) & (b[:, 2] <= z1)


def points_in_boxes(points: np.ndarray, boxes: np.ndarray, margin: float = 0.0) -> np.ndarray:
    """Index of the (first) box containing each point, or -1. (N,) int64."""
    p = np.asarray(points)[:, :3]
    b = np.asarray(boxes, dtype=np.float64).reshape(-1, 7)
    out = np.full(len(p), -1, dtype=np.int64)
    if len(b) == 0 or len(p) == 0:
        return out
    radius = np.linalg.norm(b[:, 3:6], axis=1) / 2 + margin
    for i in range(len(b)):
        cand = np.flatnonzero((np.abs(p[:, 0] - b[i, 0]) <= radius[i]) & (np.abs(p[:, 1] - b[i, 1]) <= radius[i])
                              & (np.abs(p[:, 2] - b[i, 2]) <= radius[i]) & (out < 0))
        if len(cand) == 0:
            continue
        d = p[cand] - b[i, :3]
        c, s = np.cos(-b[i, 6]), np.sin(-b[i, 6])
        lx, ly = c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1]
        inside = (np.abs(lx) <= b[i, 3] / 2 + margin) & (np.abs(ly) <= b[i, 4] / 2 + margin) & (np.abs(d[:, 2]) <= b[i, 5] / 2 + margin)
        out[cand[inside]] = i
    return out


def count_points_in_boxes(points: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    idx = points_in_boxes(points, boxes)
    return np.bincount(idx[idx >= 0], minlength=len(np.asarray(boxes).reshape(-1, 7)))


def scale_actors(points: np.ndarray, boxes: np.ndarray, scale: float, point_owner: np.ndarray,
                 clear_margin: float = 0.05, ground_keep: float = 0.15):
    """Scale every actor (its points and its box) by `scale` about the box's bottom centre.

    point_owner: (N,) index of the box that owns each point, or -1 (from instance ids or points_in_boxes).
    After scaling, non-actor points that fall inside an enlarged box (more than `ground_keep` above its
    bottom) are removed, because they would sit inside a solid object. This is a quick fix: occlusion
    behind the enlarged object is not recomputed (the ray-consistent re-render in engine G1 does that).
    Returns (points, boxes, keep_mask_over_input_points).
    """
    p = np.array(points, dtype=np.float64, copy=True)
    b = np.array(boxes, dtype=np.float64, copy=True).reshape(-1, 7)
    bottom = b[:, 2] - b[:, 5] / 2
    for i in range(len(b)):
        m = point_owner == i
        if m.any():
            p[m, 0:2] = b[i, 0:2] + (p[m, 0:2] - b[i, 0:2]) * scale
            p[m, 2] = bottom[i] + (p[m, 2] - bottom[i]) * scale
    b[:, 3:6] *= scale
    b[:, 2] = bottom + b[:, 5] / 2
    keep = np.ones(len(p), dtype=bool)
    if len(b):
        inside = points_in_boxes(p, b, margin=-clear_margin)
        foreign = (inside >= 0) & (inside != point_owner)
        above = np.zeros(len(p), dtype=bool)
        above[foreign] = p[foreign, 2] > bottom[inside[foreign]] + ground_keep
        keep &= ~(foreign & above)
    return p[keep].astype(points.dtype), b, keep
