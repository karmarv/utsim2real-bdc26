"""Training augmentations of bdc26, registered into OpenPCDet's DataAugmentor by register() (strategy S5).

bdc_object_scaling: class-wise random object scaling (ROS, as in ST3D, R40). Each object's points and box are scaled
independently along the box's length, width and height in the box frame, about the box BOTTOM, so objects stay on
the ground (OpenPCDet's random_local_scaling is isotropic, class-blind and scales about the centre, which pushes
enlarged objects through the ground). A scale is skipped when the scaled box would overlap another box in BEV.
Per-class ranges cover the real label sizes the twin lacks (S5 review, docs/02-STRATEGY.md Section 8.5: LUMPI
Bicycle synthetic 1.66 x 0.58 x 1.62 m vs real 2.00 x 0.85 x 1.90 m; trucks at most 8.47 m vs real up to 13-17 m);
the box size must then be read from the points instead of memorized from the twin's few asset sizes.
CLASS_MAX (R3) caps the scaled box per class at the real label size (99th percentile of l, w, h): on a corpus with
real sizes already (g1-v4), a length range alone created 19-20 m trucks that no real frame has, and the detector then
fitted them onto long static structures (V2X: about one 19.7 m false truck per real frame).

    - NAME: bdc_object_scaling          # after gt_sampling, so pasted objects are scaled too
      PROB: 0.7                         # per object; the rest keep their native size
      DEFAULT: {l: [0.9, 1.1], w: [0.9, 1.1], h: [0.95, 1.05]}
      CLASS_RANGES: {truck: {l: [0.9, 1.8], w: [1.0, 1.3], h: [1.0, 1.3]}}
      CLASS_MAX: {truck: [13.4, 3.2, 3.9]}   # optional: l, w, h never scaled beyond these (a box already larger keeps its size)
      CLASS_CENTER: {Car: [0.941, 1.005, 1.058]}   # S10 C1, optional: statistical normalization (below)
      CLASS_PROB: {Car: 1.0}                       # optional per-class PROB

Statistical normalization (S10 lever C1, docs/decisions/2026-11-08-s10-clean-final-plan.md; Wang et al., CVPR 2020):
CLASS_CENTER multiplies the sampled l, w, h scales of a class by the ratio of the real to the synthetic median box size
(legal real labels: box-size statistics, which the organizers allow), so the detector learns real object sizes and the
box centres that go with them; the class's range then only jitters about that target. CLASS_PROB 1.0 normalizes
every object of the class.

bdc_range_jitter (S10 lever C2): Gaussian range noise along each point's ray from its nearest sensor. The UrbanTwin
clouds carry no range noise (CARLA), while real lidars have about 2 cm (Huch et al., T-IV 2023: 2 cm jitter in
simulation raised real AP3D@0.7). Points closer than 0.1 m to a sensor (the zero padding) are left alone.

    - NAME: bdc_range_jitter
      SIGMA: 0.02                                   # m
      SENSORS: [[0.0, 0.0, 0.0]]                    # frame coordinates; with several, the nearest in BEV
      PROB: 1.0                                     # per frame
"""
from __future__ import annotations

from functools import partial

import numpy as np


def _points_in_box(points: np.ndarray, box: np.ndarray) -> np.ndarray:
    """Boolean mask of the points inside one (7,) box (same convention as OpenPCDet: centre, dims, heading)."""
    c, s = np.cos(-box[6]), np.sin(-box[6])
    dx, dy = points[:, 0] - box[0], points[:, 1] - box[1]
    lx, ly = dx * c - dy * s, dx * s + dy * c
    dz = points[:, 2] - box[2]
    return (np.abs(lx) <= box[3] / 2) & (np.abs(ly) <= box[4] / 2) & (np.abs(dz) <= box[5] / 2)


def _bev_overlap(box: np.ndarray, others: np.ndarray) -> bool:
    if not len(others):
        return False
    import torch
    from pcdet.ops.iou3d_nms import iou3d_nms_utils
    iou = iou3d_nms_utils.boxes_bev_iou_cpu(torch.from_numpy(box[None, :7].astype(np.float32)),
                                            torch.from_numpy(others[:, :7].astype(np.float32)))
    return bool((iou.numpy() > 0).any())


def object_scaling(gt_boxes: np.ndarray, gt_names, points: np.ndarray, config, rng=np.random) -> tuple:
    """Returns scaled copies of (gt_boxes, points). gt_boxes (N, 7+), points (M, 3+C)."""
    boxes, pts = gt_boxes.copy(), points.copy()
    ranges = {str(k).lower(): v for k, v in (config.get("CLASS_RANGES") or {}).items()}
    default = config.get("DEFAULT", {"l": [1.0, 1.0], "w": [1.0, 1.0], "h": [1.0, 1.0]})
    prob = float(config.get("PROB", 1.0))
    cmax = {str(k).lower(): np.asarray(v, dtype=np.float64) for k, v in (config.get("CLASS_MAX") or {}).items()}
    centers = {str(k).lower(): np.asarray(v, dtype=np.float64) for k, v in (config.get("CLASS_CENTER") or {}).items()}
    cprob = {str(k).lower(): float(v) for k, v in (config.get("CLASS_PROB") or {}).items()}
    for i in rng.permutation(len(boxes)):
        name = str(gt_names[i]).lower()
        if rng.rand() >= cprob.get(name, prob):
            continue
        r = ranges.get(name, default)
        sl, sw, sh = (rng.uniform(*r[k]) for k in ("l", "w", "h"))
        cen = centers.get(name)
        if cen is not None:                                          # S10 C1: statistical normalization
            sl, sw, sh = sl * cen[0], sw * cen[1], sh * cen[2]
        b = boxes[i].copy()
        mx = cmax.get(name)
        if mx is not None:                                           # no scaled size beyond the real maximum
            sl, sw, sh = (min(f, max(1.0, m / max(d, 1e-6))) for f, m, d in zip((sl, sw, sh), mx, b[3:6]))
        bottom = b[2] - b[5] / 2
        nb = b.copy()
        nb[3:6] = b[3:6] * np.array([sl, sw, sh])
        nb[2] = bottom + nb[5] / 2
        if _bev_overlap(nb, np.delete(boxes, i, axis=0)):
            continue
        m = _points_in_box(pts, b)
        if m.any():
            c, s = np.cos(b[6]), np.sin(b[6])
            dx, dy, dz = pts[m, 0] - b[0], pts[m, 1] - b[1], pts[m, 2] - bottom
            lx, ly = dx * c + dy * s, -dx * s + dy * c                    # into the box frame
            lx, ly, dz = lx * sl, ly * sw, dz * sh
            pts[m, 0] = b[0] + lx * c - ly * s                             # back to the frame
            pts[m, 1] = b[1] + lx * s + ly * c
            pts[m, 2] = bottom + dz
        boxes[i] = nb
    return boxes, pts


def world_tilt(gt_boxes: np.ndarray, points: np.ndarray, config, rng=np.random) -> tuple:
    """S9 (docs/decisions/2026-11-02-s9-clean-twin-plan.md, arm M1): rotate the whole scene by a small random pitch
    and roll about the frame origin, so the detector does not memorize the twin's flat ground and exact sensor pose
    (the real LUMPI ground lies 0.12-0.17 m lower than the twin's beyond 20 m). Box centres rotate with the points;
    sizes and heading stay (a 7-DoF box cannot tilt; at 1.5 deg the corner error is under 3 cm per metre).

    - NAME: bdc_world_tilt
      MAX_DEG: 1.5          # pitch and roll each uniform in [-MAX_DEG, MAX_DEG]
      PROB: 1.0
    """
    if rng.rand() >= float(config.get("PROB", 1.0)):
        return gt_boxes, points
    m = np.deg2rad(float(config.get("MAX_DEG", 1.5)))
    a, b = rng.uniform(-m, m), rng.uniform(-m, m)                     # roll about x, pitch about y
    ca, sa, cb, sb = np.cos(a), np.sin(a), np.cos(b), np.sin(b)
    rot = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]]) @ np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    pts, boxes = points.copy(), gt_boxes.copy()
    pts[:, :3] = pts[:, :3] @ rot.T
    if len(boxes):
        boxes[:, :3] = boxes[:, :3] @ rot.T
    return boxes, pts


def range_jitter(points: np.ndarray, config, rng=np.random) -> np.ndarray:
    """S10 lever C2 (see the module docstring): returns a copy of points moved along their rays by N(0, SIGMA)."""
    if rng.rand() >= float(config.get("PROB", 1.0)) or not len(points):
        return points
    pts = points.copy()
    sensors = np.asarray(config.get("SENSORS", [[0.0, 0.0, 0.0]]), dtype=np.float64).reshape(-1, 3)
    xyz = pts[:, :3].astype(np.float64)
    if len(sensors) == 1:
        origin = np.broadcast_to(sensors[0], xyz.shape)
    else:
        d2 = ((xyz[:, None, :2] - sensors[None, :, :2]) ** 2).sum(-1)
        origin = sensors[d2.argmin(1)]
    ray = xyz - origin
    r = np.linalg.norm(ray, axis=1)
    ok = r > 0.1
    step = rng.normal(0.0, float(config.get("SIGMA", 0.02)), ok.sum())
    xyz[ok] += ray[ok] / r[ok, None] * step[:, None]
    pts[:, :3] = xyz.astype(pts.dtype)
    return pts


def register() -> None:
    from pcdet.datasets.augmentor.data_augmentor import DataAugmentor

    def bdc_object_scaling(self, data_dict=None, config=None):
        if data_dict is None:
            return partial(self.bdc_object_scaling, config=config)
        data_dict["gt_boxes"], data_dict["points"] = object_scaling(data_dict["gt_boxes"], data_dict["gt_names"],
                                                                    data_dict["points"], config)
        return data_dict

    def bdc_world_tilt(self, data_dict=None, config=None):
        if data_dict is None:
            return partial(self.bdc_world_tilt, config=config)
        data_dict["gt_boxes"], data_dict["points"] = world_tilt(data_dict["gt_boxes"], data_dict["points"], config)
        return data_dict

    def bdc_range_jitter(self, data_dict=None, config=None):
        if data_dict is None:
            return partial(self.bdc_range_jitter, config=config)
        data_dict["points"] = range_jitter(data_dict["points"], config)
        return data_dict

    DataAugmentor.bdc_object_scaling = bdc_object_scaling
    DataAugmentor.bdc_world_tilt = bdc_world_tilt
    DataAugmentor.bdc_range_jitter = bdc_range_jitter
