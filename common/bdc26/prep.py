"""Frame conversion shared by the per-track preparation scripts (data-<track>/prepare_*.py).

`convert_ut_frame` turns one organizer synthetic frame into a training frame in the challenge convention:
  1. map UT classes to the track classes (drop unmapped),
  2. optionally insert synthetic objects ray-consistently (engine G1, `inserter`; before the scale fix, while
     every UT point still lies on its sensor's beam),
  3. optionally scale every actor about its bottom centre (UT-LUMPI actors are 0.78x real size),
  4. mask to the range and resample to the real density (optionally with a calibrated background density,
     bdc26.density; object points always keep the uniform rate),
  5. keep boxes whose centre is in range and that still contain >= min_points points.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from .boxes import boxes_center_in_range, count_points_in_boxes, points_in_boxes, scale_actors
from .classmap import map_ut
from .config import Track
from .frames import resample
from .io import ut


@dataclass
class UTConvertParams:
    n_points: int                 # points per output frame after masking (valid returns; no nulls in UT)
    scale_fix: float = 1.0        # actor scale about the bottom centre
    min_points: int = 1           # drop boxes with fewer points after resampling
    margin: float = 5.0           # process boxes whose centre is within range + margin (labels cover the whole map)
    seed: int = 1234
    class_map: dict | None = field(default=None)   # overrides track.yaml ut.class_map
    density_prior: str | None = None              # bdc26.density prior (.npz): calibrated background resampling


_PRIORS: dict = {}


def _prior(path: str):
    if path not in _PRIORS:
        from .density import DensityPrior
        _PRIORS[path] = DensityPrior.load(Path(path))
    return _PRIORS[path]


def scaled_boxes(boxes: np.ndarray, scale: float) -> np.ndarray:
    """Boxes as they will be after scale_actors (dimensions x scale about the bottom centre)."""
    b = np.array(boxes, dtype=np.float64, copy=True).reshape(-1, 7)
    bottom = b[:, 2] - b[:, 5] / 2
    b[:, 3:6] *= scale
    b[:, 2] = bottom + b[:, 5] / 2
    return b


def convert_ut_frame(track: Track, idx: int, p: UTConvertParams, inserter: Callable | None = None):
    """inserter(points, boxes_after_scale_fix, names, rng) -> (points_out, keep_mask, extra_boxes, extra_names, stats),
    where points_out = points[keep_mask] followed by the inserted points."""
    pts = ut.read_points(track, idx)
    lab = ut.read_labels(track, idx)
    names = map_ut(lab.names, track, p.class_map)
    x0, y0, z0, x1, y1, z1 = track.pc_range
    wide = [x0 - p.margin, y0 - p.margin, z0 - p.margin, x1 + p.margin, y1 + p.margin, z1 + p.margin]
    keep = (names != "") & boxes_center_in_range(lab.boxes, wide)
    boxes, names, actor_ids = lab.boxes[keep], names[keep], lab.actor_ids[keep]
    stats = {"scaled": 0}
    owner = None
    if (p.scale_fix != 1.0 and len(boxes)) or inserter is not None:
        ins = ut.read_instance_ids(track, idx)
        if ins is not None and len(ins) == len(pts):
            lut = {int(a): i for i, a in enumerate(actor_ids)}
            owner = np.array([lut.get(int(v), -1) for v in ins], dtype=np.int64) if len(lut) else np.full(len(pts), -1)
        else:
            owner = points_in_boxes(pts, boxes) if len(boxes) else np.full(len(pts), -1)
    extra_b, extra_n = np.zeros((0, 7)), np.array([], dtype=object)
    if inserter is not None:
        rng_ins = np.random.default_rng([p.seed, idx, 7919])
        out, kept, extra_b, extra_n, st = inserter(pts, scaled_boxes(boxes, p.scale_fix), names, rng_ins)
        owner = np.concatenate([owner[kept], np.full(len(out) - int(kept.sum()), -1, dtype=np.int64)])
        pts = out.astype(np.float32)
        stats.update(st)
    if p.scale_fix != 1.0 and len(boxes):
        pts, boxes, _ = scale_actors(pts, boxes, p.scale_fix, owner)
        stats["scaled"] = len(boxes)
    if len(extra_b):
        boxes = np.concatenate([boxes.reshape(-1, 7), np.asarray(extra_b, dtype=np.float64).reshape(-1, 7)])
        names = np.concatenate([names, np.asarray(extra_n, dtype=object)])
    rng = np.random.default_rng(p.seed + idx)
    if p.density_prior:
        from .density import resample_calibrated
        is_obj = points_in_boxes(pts, boxes, margin=0.1) >= 0 if len(boxes) else np.zeros(len(pts), dtype=bool)
        pts = resample_calibrated(pts, p.n_points, rng, track.pc_range, _prior(p.density_prior), is_obj)
    else:
        pts = resample(pts, p.n_points, rng, track.pc_range)
    inr = boxes_center_in_range(boxes, track.pc_range)
    boxes, names = boxes[inr], names[inr]
    npts = count_points_in_boxes(pts, boxes) if len(boxes) else np.zeros(0, dtype=np.int64)
    vis = npts >= p.min_points
    stats.update(n_boxes=int(vis.sum()), n_dropped_empty=int((~vis).sum()))
    for c in np.unique(names[vis]) if vis.any() else []:
        stats[f"n_{c}"] = int(np.sum(names[vis] == c))
    return pts.astype(np.float32), boxes[vis], names[vis], stats
