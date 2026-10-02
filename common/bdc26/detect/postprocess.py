"""Post-processing of raw detector outputs into challenge predictions (module M11; numpy only).

Every step is configured per class in the model's `test/postprocess.yaml` and selected on the real
validation set, never on the leaderboard:
  score_floor        keep boxes with score >= floor (never threshold aggressively: AP cannot drop by adding
                     lower-scored boxes)
  pre_max            keep the top pre_max boxes per class before NMS (default 400; speed only)
  nms_iou            per-class rotated BEV NMS IoU (pedestrians cluster: ~0.7; vehicles ~0.1-0.3)
  max_boxes          per-frame cap after NMS (the server has no cap; keep it generous)
  recenter           alpha in [0, 1]: move the BEV centre toward the centroid of in-box points (small classes)
  size_scale         [sl, sw, sh] box-size calibration about the bottom centre (default [1, 1, 1]); a
                     hyperparameter selected on real val (prefer fixing sizes in the generator)
  z_offset           metres added to the box centre z (default 0)
  hedge              {source_class: [target_class, score_factor]}: emit discounted duplicates (per-class AP is
                     independent, so a well-discounted copy can only help the receiving class)
OpenPCDet's MULTI_CLASSES_NMS asserts on single-head multi-class models, so NMS is done here instead.
"""
from __future__ import annotations

import numpy as np

from ..evalap import iou_matrix


def rotated_nms(boxes: np.ndarray, scores: np.ndarray, iou_thr: float) -> np.ndarray:
    order = np.argsort(-scores)
    keep = []
    suppressed = np.zeros(len(boxes), bool)
    # fast float32 IoU (OpenPCDet's op when importable): NMS needs speed and the same result at tuning and inference
    ious = iou_matrix(boxes, boxes, kind="bev", exact=False) if len(boxes) else np.zeros((0, 0))
    for i in order:
        if suppressed[i]:
            continue
        keep.append(i)
        suppressed |= ious[i] > iou_thr
    return np.array(keep, dtype=np.int64)


def recenter(boxes: np.ndarray, points: np.ndarray, alpha: float, min_points: int = 3, margin: float = 0.02) -> np.ndarray:
    """Move each box's BEV centre a fraction alpha toward the centroid of the points inside it (KD-tree lookup)."""
    if alpha <= 0 or len(boxes) == 0 or len(points) == 0:
        return boxes
    from scipy.spatial import cKDTree
    b = boxes.copy()
    p = np.asarray(points)[:, :3]
    tree = cKDTree(p[:, :2])
    cand = tree.query_ball_point(b[:, :2], np.hypot(b[:, 3], b[:, 4]) / 2 + margin)
    for i, idx in enumerate(cand):
        if len(idx) < min_points:
            continue
        q = p[idx]
        d = q - b[i, :3]
        c, s = np.cos(-b[i, 6]), np.sin(-b[i, 6])
        lx, ly = c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1]
        inside = ((np.abs(lx) <= b[i, 3] / 2 + margin) & (np.abs(ly) <= b[i, 4] / 2 + margin)
                  & (np.abs(d[:, 2]) <= b[i, 5] / 2 + margin))
        if inside.sum() >= min_points:
            b[i, :2] = (1 - alpha) * b[i, :2] + alpha * q[inside, :2].mean(0)
    return b


def nms_stage(boxes: np.ndarray, scores: np.ndarray, cc: dict):
    """Score floor, pre-NMS cap (top pre_max by score), rotated BEV NMS. Returns (boxes, scores)."""
    m = scores >= cc.get("score_floor", 0.01)
    b, s = boxes[m], scores[m]
    if len(b) == 0:
        return b.reshape(0, 7), s
    pre = int(cc.get("pre_max", 400))
    if len(b) > pre:
        top = np.argsort(-s)[:pre]
        b, s = b[top], s[top]
    k = rotated_nms(b, s, cc.get("nms_iou", 0.2))
    return b[k], s[k]


def recenter_stage(b: np.ndarray, s: np.ndarray, cc: dict, points: np.ndarray | None = None):
    if points is not None and cc.get("recenter", 0.0) > 0 and len(b):
        b = recenter(b, points, cc["recenter"])
    return b, s


def calibrate_stage(b: np.ndarray, s: np.ndarray, cc: dict):
    """Size calibration about the bottom centre, z offset, cap. Returns (boxes, scores)."""
    b = b.copy()
    sc = cc.get("size_scale")
    if sc is not None and any(float(v) != 1.0 for v in sc) and len(b):
        bottom = b[:, 2] - b[:, 5] / 2
        b[:, 3:6] *= np.asarray(sc, dtype=np.float64)
        b[:, 2] = bottom + b[:, 5] / 2
    if cc.get("z_offset", 0.0) and len(b):
        b[:, 2] += float(cc["z_offset"])
    top = np.argsort(-s)[: cc.get("max_boxes", 500)]
    return b[top], s[top]


def adjust_stage(b: np.ndarray, s: np.ndarray, cc: dict, points: np.ndarray | None = None):
    """After NMS: re-centering (x, y from in-box points), then size calibration, z offset and cap."""
    return calibrate_stage(*recenter_stage(b, s, cc, points), cc)


def postprocess_class(boxes: np.ndarray, scores: np.ndarray, cc: dict, points: np.ndarray | None = None):
    """One class: score floor, pre-NMS cap, rotated NMS, re-centering, size calibration, z offset, cap."""
    b, s = nms_stage(boxes, scores, cc)
    return adjust_stage(b, s, cc, points)


def class_cfg(cfg: dict, c: str) -> dict:
    return {**cfg.get("default", {}), **(cfg.get("classes") or {}).get(str(c), {})}


def apply_hedge(out: list[dict], hedge: dict | None) -> list[dict]:
    """hedge: {source: [target, factor]} or {source: [[target, factor], ...]}."""
    extra = []
    for src, spec in (hedge or {}).items():
        pairs = spec if spec and isinstance(spec[0], (list, tuple)) else [spec]
        for dst, factor in pairs:
            if float(factor) > 0:
                extra += [{"box": d["box"], "score": d["score"] * float(factor), "class": dst} for d in out if d["class"] == src]
    return out + extra


def postprocess(boxes: np.ndarray, scores: np.ndarray, labels: list[str], cfg: dict,
                points: np.ndarray | None = None) -> list[dict]:
    """boxes (D,7), scores (D,), labels (D,) class names -> list of challenge prediction dicts."""
    out = []
    labels = np.asarray(labels, dtype=object)
    for c in np.unique(labels):
        m = labels == c
        b, s = postprocess_class(boxes[m], scores[m], class_cfg(cfg, c), points)
        out += [{"box": [float(v) for v in bb], "score": float(ss), "class": str(c)} for bb, ss in zip(b, s)]
    return apply_hedge(out, cfg.get("hedge"))
