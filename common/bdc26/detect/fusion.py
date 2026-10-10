"""Rotated 3D weighted box fusion (strategy S3, docs/02-STRATEGY.md Section 8.3).

One function serves both uses of S3:
- test-time augmentation (TTA): the sources are the views of one model (identity, flips, small yaw and z shifts),
  each mapped back to the original frame;
- cross-member fusion: the sources are different members (for example PointPillars and CenterPoint) for one class.

Clustering is leader-based in score order: the highest-scored unassigned box opens a cluster and takes every
unassigned box whose rotated BEV IoU with it reaches iou_thr (centre distance prunes the IoU computations, so a
frame with thousands of boxes stays cheap). Per cluster:
- centre, size: weighted mean of the members, weight = source weight x score;
- yaw: the leader's (averaging headings is ill-defined near the +/- pi flip);
- score: sum over sources of (source weight x the source's best score in the cluster) / sum of all source weights.
  A box that only some sources produce is demoted in proportion (weighted box fusion "avg" with the
  min(n_boxes, n_sources) rescaling); a box every source agrees on keeps its score.
Per-class AP depends only on the score order and the boxes, so fusion helps when the sources make different
mistakes: the S2 diagnosis showed CenterPoint and the pillars disagree on which static structures look like walkers.
"""
from __future__ import annotations

import numpy as np

from ..evalap import iou_pair


def wbf(boxes: np.ndarray, scores: np.ndarray, sources: np.ndarray, n_sources: int, iou_thr: float,
        source_weights=None, min_score: float = 0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fuse (N, 7) boxes from n_sources sources. Returns (boxes (K, 7), scores (K,), sources per cluster (K,))."""
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 7)
    scores = np.asarray(scores, dtype=np.float64).reshape(-1)
    sources = np.asarray(sources, dtype=np.int64).reshape(-1)
    w = np.ones(n_sources) if source_weights is None else np.asarray(source_weights, dtype=np.float64)
    keep = scores >= min_score
    boxes, scores, sources = boxes[keep], scores[keep], sources[keep]
    n = len(boxes)
    if n == 0:
        return np.zeros((0, 7)), np.zeros(0), np.zeros(0, dtype=np.int64)
    order = np.argsort(-scores, kind="stable")
    boxes, scores, sources = boxes[order], scores[order], sources[order]
    radius = np.hypot(boxes[:, 3], boxes[:, 4]) / 2
    free = np.ones(n, dtype=bool)
    out_b, out_s, out_n = [], [], []
    wsum = w.sum()
    for i in range(n):
        if not free[i]:
            continue
        cand = np.flatnonzero(free)
        d = np.hypot(boxes[cand, 0] - boxes[i, 0], boxes[cand, 1] - boxes[i, 1])
        cand = cand[d < radius[cand] + radius[i]]
        members = cand
        if len(cand) > 1:
            ib = iou_pair(boxes[i:i + 1], boxes[cand], exact=False)[1][0]
            members = cand[(ib >= iou_thr) | (cand == i)]
        free[members] = False
        sw = w[sources[members]] * scores[members]
        geo = (boxes[members, :6] * sw[:, None]).sum(0) / sw.sum()
        best = np.zeros(n_sources)
        np.maximum.at(best, sources[members], scores[members])
        out_b.append(np.r_[geo, boxes[i, 6]])
        out_s.append(float((w * best).sum() / wsum))
        out_n.append(len(np.unique(sources[members])))
    return np.array(out_b), np.array(out_s), np.array(out_n, dtype=np.int64)


def fuse_dets(dets_by_source: list[list[dict]], iou_thr: dict | float, source_weights=None, min_score: float = 0.0) -> list[dict]:
    """Fuse challenge-format detections ([{"box", "score", "class"}, ...] per source) class by class.
    iou_thr: one value or {class: value} (a "default" key applies to the other classes)."""
    by_class: dict = {}
    for k, dets in enumerate(dets_by_source):
        for d in dets:
            by_class.setdefault(d["class"], []).append((d["box"], d["score"], k))
    out = []
    for c, rows in by_class.items():
        thr = iou_thr if not isinstance(iou_thr, dict) else iou_thr.get(c, iou_thr.get("default", 0.5))
        b = np.array([r[0] for r in rows], dtype=np.float64)
        s = np.array([r[1] for r in rows], dtype=np.float64)
        src = np.array([r[2] for r in rows], dtype=np.int64)
        fb, fs, _ = wbf(b, s, src, len(dets_by_source), thr, source_weights, min_score)
        out += [{"box": bb.tolist(), "score": float(ss), "class": c} for bb, ss in zip(fb, fs)]
    return out
