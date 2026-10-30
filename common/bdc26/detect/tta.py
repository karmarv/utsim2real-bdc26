"""Test-time augmentation views for 3D detection (strategy S3, docs/02-STRATEGY.md Section 8.3).

A view transforms the input points (flip, then rotation about z, then z shift, with OpenPCDet's training-augmentation
conventions so every view stays inside the training distribution: random_world_flip on x and y, rotation +/-10 deg),
and its inverse maps the predicted boxes back to the original frame. Views of one frame run as one batch; their boxes
are fused class by class with bdc26.detect.fusion.wbf.

    parse("flip4")         -> identity, flip-x, flip-y, flip-xy
    parse("flip4+yaw")     -> + rotations of +/-5 deg
    parse("flip4+yaw+z")   -> + z shifts of +/-0.25 m (the height TTA of the RoboSense 2025 report, R39)
    parse("flip4+yaw+z+scale") -> + global scale 0.95 / 1.05 on the identity and on the xy flip (S8, 12 views; inside
                              the training augmentation WORLD_SCALE_RANGE [0.95, 1.05]; applied after the other steps)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class View:
    name: str
    flip_x: bool = False          # mirror y (OpenPCDet random_flip_along_x)
    flip_y: bool = False          # mirror x (OpenPCDet random_flip_along_y)
    rot: float = 0.0              # radians, counter-clockwise about z
    dz: float = 0.0               # metres added to z
    scale: float = 1.0            # global scale of x, y, z (box centres and sizes scale with it)


def parse(spec: str, yaw_deg: float = 5.0, dz: float = 0.25, scales: tuple = (0.95, 1.05)) -> list[View]:
    parts = set(spec.split("+"))
    unknown = parts - {"flip4", "flip2", "yaw", "z", "scale", "id"}
    if unknown:
        raise ValueError(f"unknown TTA parts {sorted(unknown)} in {spec!r}")
    views = [View("id")]
    if "flip2" in parts:
        views.append(View("fxy", True, True))
    if "flip4" in parts:
        views += [View("fx", flip_x=True), View("fy", flip_y=True), View("fxy", True, True)]
    if "yaw" in parts:
        r = np.deg2rad(yaw_deg)
        views += [View("r+", rot=r), View("r-", rot=-r)]
    if "z" in parts:
        views += [View("z+", dz=dz), View("z-", dz=-dz)]
    if "scale" in parts:
        lo, hi = scales
        views += [View("s-", scale=lo), View("s+", scale=hi), View("fxy_s-", True, True, scale=lo),
                  View("fxy_s+", True, True, scale=hi)]
    return views


def _rot(xy: np.ndarray, a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.stack([xy[:, 0] * c - xy[:, 1] * s, xy[:, 0] * s + xy[:, 1] * c], 1)


def forward_points(points: np.ndarray, v: View) -> np.ndarray:
    p = np.array(points, dtype=np.float32, copy=True)
    if v.flip_x:
        p[:, 1] = -p[:, 1]
    if v.flip_y:
        p[:, 0] = -p[:, 0]
    if v.rot:
        p[:, :2] = _rot(p[:, :2].astype(np.float64), v.rot)
    if v.dz:
        p[:, 2] += v.dz
    if v.scale != 1.0:
        p[:, :3] *= v.scale
    return p


def forward_boxes(boxes: np.ndarray, v: View) -> np.ndarray:
    """Boxes transformed like the points (used by the tests and for checking the inverse)."""
    b = np.array(boxes, dtype=np.float64, copy=True).reshape(-1, 7)
    if v.flip_x:
        b[:, 1], b[:, 6] = -b[:, 1], -b[:, 6]
    if v.flip_y:
        b[:, 0], b[:, 6] = -b[:, 0], -(b[:, 6] + np.pi)
    if v.rot:
        b[:, :2] = _rot(b[:, :2], v.rot)
        b[:, 6] += v.rot
    if v.dz:
        b[:, 2] += v.dz
    if v.scale != 1.0:
        b[:, :6] *= v.scale
    return b


def inverse_boxes(boxes: np.ndarray, v: View) -> np.ndarray:
    """Boxes predicted in view v, mapped back to the original frame (heading wrapped to [-pi, pi))."""
    b = np.array(boxes, dtype=np.float64, copy=True).reshape(-1, 7)
    if v.scale != 1.0:
        b[:, :6] /= v.scale
    if v.dz:
        b[:, 2] -= v.dz
    if v.rot:
        b[:, :2] = _rot(b[:, :2], -v.rot)
        b[:, 6] -= v.rot
    if v.flip_y:
        b[:, 0], b[:, 6] = -b[:, 0], -b[:, 6] - np.pi
    if v.flip_x:
        b[:, 1], b[:, 6] = -b[:, 1], -b[:, 6]
    b[:, 6] = (b[:, 6] + np.pi) % (2 * np.pi) - np.pi
    return b


SMALL = {"pedestrian", "person", "bicycle", "motorcycle"}


def default_iou(classes: list[str]) -> dict:
    """Per-class BEV IoU for fusing views: 0.3 for walker- and bike-sized classes (a few cm of jitter between views
    already costs half their IoU), 0.5 otherwise."""
    return {c: (0.3 if c.lower() in SMALL else 0.5) for c in classes}
