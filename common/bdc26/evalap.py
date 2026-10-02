"""3D detection AP exactly as the challenge scores it, plus the KITTI variant for reference (CPU).

Official protocol (starting kit `scoring_program/detection_eval.py`, verified bit-for-bit by
common/tests/test_official_parity.py): per class and IoU threshold,
  1. per frame, predictions of the class sorted by score (stable); each takes the UNUSED GT of the class with the
     highest IoU and is a true positive if that IoU >= thr (VOC-style greedy matching, prediction-centric);
     predictions in frames without GT of the class are false positives;
  2. all predictions of the class pooled and ordered by score (np.argsort(-score));
  3. precision / recall curve; AP_R40 = mean over r in {1/40, ..., 1} of max precision at recall >= r
     (AP_R11: r in {0, 0.1, ..., 1});
  4. 3D IoU = BEV polygon intersection x z overlap / union volume; BEV IoU = polygon IoU; classes without GT are
     excluded from the mean (NaN); class names compare case-insensitively; no difficulty filter.
`evaluate()` / `ap_for_class()` implement this protocol. `evaluate_kitti()` / `ap_for_class_kitti()` keep
OpenPCDet's KITTI statistics (GT-centric matching, TP-score thresholds) for comparison with KITTI-style numbers.

Speed: IoUs are computed once per class and frame (C++ rotated BEV IoU from OpenPCDet when importable,
otherwise Python polygon clipping on nearby pairs only); matching loops run under numba when available
(pure-Python fallback with identical results).
"""
from __future__ import annotations

import numpy as np

from .boxes import bev_corners

N_SAMPLE_PTS = 41

try:  # optional accelerators
    from numba import njit
except ImportError:  # pragma: no cover
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f

try:  # shapely (GEOS, float64): the official scorer's polygon arithmetic, used when installed (exact parity)
    import shapely
    _HAVE_SHAPELY = int(shapely.__version__.split(".")[0]) >= 2
except Exception:  # pragma: no cover
    _HAVE_SHAPELY = False

# Exact (shapely) IoUs for every evaluation by default. Searches that score thousands of candidate settings
# (common/tools/tune_postprocess.py) set this to False and use OpenPCDet's float32 C++ op: decisions do not change,
# final numbers are always recomputed exactly.
EXACT_IOU = True

try:  # OpenPCDet's CPU rotated BEV IoU (C++, float32), the fast fallback
    import torch
    from pcdet.ops.iou3d_nms.iou3d_nms_utils import boxes_bev_iou_cpu as _pcdet_bev_iou
except Exception:  # pragma: no cover
    _pcdet_bev_iou = None


# --------------------------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------------------------
def _clip(subject: np.ndarray, clipper: np.ndarray) -> np.ndarray:
    """Sutherland-Hodgman clipping of convex polygon `subject` by convex CCW polygon `clipper`."""
    out = subject
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        if len(out) == 0:
            break
        inp, out = out, []
        edge = b - a
        def side(p): return edge[0] * (p[1] - a[1]) - edge[1] * (p[0] - a[0])
        for j in range(len(inp)):
            cur, prev = inp[j], inp[j - 1]
            sc, sp = side(cur), side(prev)
            if sc >= 0:
                if sp < 0:
                    t = sp / (sp - sc)
                    out.append(prev + t * (cur - prev))
                out.append(cur)
            elif sp >= 0:
                t = sp / (sp - sc)
                out.append(prev + t * (cur - prev))
        out = np.array(out) if out else np.zeros((0, 2))
    return out


def _area(poly: np.ndarray) -> float:
    if len(poly) < 3:
        return 0.0
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _official_corners(b: np.ndarray) -> np.ndarray:
    """(N, 4, 2) BEV corners computed exactly like the scorer's _box_corners_2d (same order and arithmetic)."""
    hx, hy = b[:, 3] / 2.0, b[:, 4] / 2.0
    local = np.stack([np.stack([hx, hy], 1), np.stack([hx, -hy], 1), np.stack([-hx, -hy], 1), np.stack([-hx, hy], 1)], 1)
    c, s = np.cos(b[:, 6]), np.sin(b[:, 6])
    x = local[..., 0] * c[:, None] + local[..., 1] * (-s[:, None])          # corners @ rot.T, rot = [[c, -s], [s, c]]
    y = local[..., 0] * s[:, None] + local[..., 1] * c[:, None]
    return np.stack([x + b[:, None, 0], y + b[:, None, 1]], -1)


def bev_intersection(dets: np.ndarray, gts: np.ndarray, exact: bool | None = None) -> np.ndarray:
    """(D, G) area of the oriented BEV intersection. exact (default: when shapely is installed) uses GEOS in
    float64 like the official scorer; otherwise OpenPCDet's C++ op (float32) or Python polygon clipping."""
    D, G = len(dets), len(gts)
    if D == 0 or G == 0:
        return np.zeros((D, G))
    exact = (_HAVE_SHAPELY and EXACT_IOU) if exact is None else exact
    rd, rg = np.hypot(dets[:, 3], dets[:, 4]) / 2, np.hypot(gts[:, 3], gts[:, 4]) / 2
    dist = np.hypot(dets[:, None, 0] - gts[None, :, 0], dets[:, None, 1] - gts[None, :, 1])
    ii, jj = np.nonzero(dist < rd[:, None] + rg[None, :] + 1e-6)
    out = np.zeros((D, G))
    if len(ii) == 0:
        return out
    if exact:
        pd_, pg = shapely.polygons(_official_corners(dets)), shapely.polygons(_official_corners(gts))
        out[ii, jj] = shapely.area(shapely.intersection(pd_[ii], pg[jj]))
        return out
    area_d, area_g = dets[:, 3] * dets[:, 4], gts[:, 3] * gts[:, 4]
    if _pcdet_bev_iou is not None:
        iou = _pcdet_bev_iou(torch.from_numpy(np.ascontiguousarray(dets[:, :7], dtype=np.float32)),
                             torch.from_numpy(np.ascontiguousarray(gts[:, :7], dtype=np.float32))).numpy().astype(np.float64)
        return iou * (area_d[:, None] + area_g[None, :]) / (1.0 + iou)
    cd, cg = bev_corners(dets), bev_corners(gts)
    for i, j in zip(ii, jj):
        out[i, j] = _area(_clip(cd[i], cg[j]))
    return out


def iou_pair(dets: np.ndarray, gts: np.ndarray, exact: bool | None = None) -> tuple[np.ndarray, np.ndarray]:
    """((D, G) 3D IoU, (D, G) BEV IoU) from one BEV-intersection pass (formulas of the official scorer).
    exact=None: shapely when installed and EXACT_IOU; False: OpenPCDet's float32 op (fast)."""
    dets = np.asarray(dets, dtype=np.float64).reshape(-1, 7)
    gts = np.asarray(gts, dtype=np.float64).reshape(-1, 7)
    exact = (_HAVE_SHAPELY and EXACT_IOU) if exact is None else (exact and _HAVE_SHAPELY)
    inter = bev_intersection(dets, gts, exact=exact)
    if inter.size == 0:
        return inter, inter.copy()
    if exact:
        area_d = shapely.area(shapely.polygons(_official_corners(dets)))
        area_g = shapely.area(shapely.polygons(_official_corners(gts)))
    else:
        area_d, area_g = dets[:, 3] * dets[:, 4], gts[:, 3] * gts[:, 4]
    union = area_d[:, None] + area_g[None, :] - inter
    bev = np.where(union > 0, inter / np.where(union > 0, union, 1.0), 0.0)
    top = np.minimum(dets[:, None, 2] + dets[:, None, 5] / 2.0, gts[None, :, 2] + gts[None, :, 5] / 2.0)
    bot = np.maximum(dets[:, None, 2] - dets[:, None, 5] / 2.0, gts[None, :, 2] - gts[None, :, 5] / 2.0)
    z = np.maximum(top - bot, 0.0)
    v = inter * z
    vol = (dets[:, 3] * dets[:, 4] * dets[:, 5])[:, None] + (gts[:, 3] * gts[:, 4] * gts[:, 5])[None, :] - v
    iou3d = np.where((inter > 0) & (z > 0) & (vol > 0), v / np.where(vol > 0, vol, 1.0), 0.0)
    return iou3d, np.where(inter > 0, bev, 0.0)


def iou_matrix(dets: np.ndarray, gts: np.ndarray, kind: str = "3d", exact: bool | None = None) -> np.ndarray:
    """(D, G) IoU between (D,7) and (G,7) boxes; kind '3d' or 'bev'; exact as in iou_pair."""
    iou3d, bev = iou_pair(dets, gts, exact)
    return iou3d if kind == "3d" else bev


# --------------------------------------------------------------------------------------------
# KITTI-style statistics on sparse (CSR, per GT) overlaps
# --------------------------------------------------------------------------------------------
@njit(cache=True)
def _stats_csr(indptr, indices, ovs, scores, thr, score_thresh, compute_fp):
    D = scores.shape[0]
    G = indptr.shape[0] - 1
    assigned = np.zeros(D, dtype=np.bool_)
    tp, fp, fn, ntp = 0, 0, 0, 0
    tp_scores = np.empty(max(G, 1), dtype=np.float64)
    for g in range(G):
        best, best_val, max_ov = -1, -1e18, 0.0
        for k in range(indptr[g], indptr[g + 1]):
            d = indices[k]
            if assigned[d] or ovs[k] <= thr:
                continue
            if compute_fp:
                if scores[d] < score_thresh:
                    continue
                if ovs[k] > max_ov:
                    best, max_ov = d, ovs[k]
            elif scores[d] > best_val:
                best, best_val = d, scores[d]
        if best < 0:
            fn += 1
        else:
            tp += 1
            tp_scores[ntp] = scores[best]
            ntp += 1
            assigned[best] = True
    if compute_fp:
        for d in range(D):
            if not assigned[d] and scores[d] >= score_thresh:
                fp += 1
    return tp, fp, fn, tp_scores[:ntp]


def _to_csr(ov: np.ndarray, scores) -> tuple:
    """(indptr, det_index, overlap, scores): per-GT lists of the detections with non-zero overlap.

    Within a GT the detections stay in index order, so ties break exactly as in the dense loop.
    """
    D, G = ov.shape
    g_idx, d_idx = np.nonzero(ov.T > 0)          # row-major over (G, D): GT-major, detections ascending
    indptr = np.zeros(G + 1, dtype=np.int64)
    np.add.at(indptr, g_idx + 1, 1)
    return (np.cumsum(indptr), d_idx.astype(np.int64), ov.T[g_idx, d_idx].astype(np.float64),
            np.asarray(scores, dtype=np.float64).reshape(D))


def _concat_csr(frames_csr: list) -> tuple:
    """Merge per-frame CSRs into one; detection indices are offset so frames stay independent."""
    if not frames_csr:
        return np.zeros(1, np.int64), np.zeros(0, np.int64), np.zeros(0), np.zeros(0)
    ptrs, idx, ovs, scs = [np.zeros(1, np.int64)], [], [], []
    n_edges = n_dets = 0
    for indptr, ind, ov, sc in frames_csr:
        ptrs.append(indptr[1:] + n_edges)
        idx.append(ind + n_dets)
        ovs.append(ov)
        scs.append(sc)
        n_edges += len(ind)
        n_dets += len(sc)
    return np.concatenate(ptrs), np.concatenate(idx), np.concatenate(ovs), np.concatenate(scs)


def _thresholds(scores, num_gt: int) -> list[float]:
    s = np.sort(np.asarray(scores, dtype=np.float64))[::-1]
    cur, out = 0.0, []
    for i, sc in enumerate(s):
        l_rec = (i + 1) / num_gt
        r_rec = (i + 2) / num_gt if i < len(s) - 1 else l_rec
        if (r_rec - cur) < (cur - l_rec) and i < len(s) - 1:
            continue
        out.append(sc)
        cur += 1.0 / (N_SAMPLE_PTS - 1.0)
    return out


def _ap_from_csr(csr: tuple, thr: float) -> dict | None:
    """csr: merged (indptr, det_index, overlap, scores) for one class and IoU kind over all frames."""
    indptr, indices, ovs, scores = csr
    num_gt = len(indptr) - 1
    if num_gt == 0:
        return None
    tp_scores = _stats_csr(indptr, indices, ovs, scores, float(thr), 0.0, False)[3]
    ths = _thresholds(tp_scores, num_gt)
    prec = np.zeros(N_SAMPLE_PTS)
    for k, t in enumerate(ths):
        tp, fp, _, _ = _stats_csr(indptr, indices, ovs, scores, float(thr), float(t), True)
        prec[k] = tp / (tp + fp) if tp + fp else 0.0
    for k in range(len(ths)):
        prec[k] = prec[k:].max()
    return {"AP_R40": float(prec[1:].sum() / 40.0), "AP_R11": float(prec[0::4].sum() / 11.0), "n_gt": int(num_gt),
            "n_pred": int(len(scores))}


def ap_for_class_kitti(frames: list[tuple[np.ndarray, np.ndarray, np.ndarray]], thr: float, kind: str) -> dict | None:
    """KITTI statistics. frames: list of (det_boxes (D,7), det_scores (D,), gt_boxes (G,7)) for one class."""
    return _ap_from_csr(_concat_csr([_to_csr(iou_matrix(d, g, kind), s) for d, s, g in frames]), thr)


def evaluate_kitti(preds: dict, gts: dict, classes: list[str], iou_thresholds=(0.5, 0.7)) -> dict:
    """KITTI statistics. preds: {fid: [{"box": [7], "score": s, "class": c}, ...]}; gts: {fid: (boxes (G,7), names (G,))}.

    Returns {"per_class": {c: {"3d@0.5": {...}, "bev@0.5": {...}, ...}}, "mAP_3d_0.5_R40": ..., ...}.
    """
    lc = {c.lower(): c for c in classes}
    per_class: dict = {c: {} for c in classes}
    for c in classes:
        csr3d, csrbev = [], []
        for fid, (gb, gn) in gts.items():
            gm = np.array([str(n).lower() == c.lower() for n in gn], dtype=bool)
            g = np.asarray(gb, dtype=np.float64).reshape(-1, 7)[gm]
            ps = [p for p in preds.get(fid, []) if lc.get(str(p["class"]).lower()) == c]
            db = np.array([p["box"] for p in ps], dtype=np.float64).reshape(-1, 7)
            ds = np.array([p["score"] for p in ps], dtype=np.float64)
            i3, ib = iou_pair(db, g)
            csr3d.append(_to_csr(i3, ds))
            csrbev.append(_to_csr(ib, ds))
        for kind, csr in (("3d", _concat_csr(csr3d)), ("bev", _concat_csr(csrbev))):
            for thr in iou_thresholds:
                per_class[c][f"{kind}@{thr}"] = _ap_from_csr(csr, thr)
    out = {"per_class": per_class}
    for kind in ("3d", "bev"):
        for thr in iou_thresholds:
            for interp in ("R40", "R11"):
                vals = [per_class[c][f"{kind}@{thr}"][f"AP_{interp}"] for c in classes if per_class[c][f"{kind}@{thr}"]]
                out[f"mAP_{kind}_{thr}_{interp}"] = float(np.mean(vals)) if vals else 0.0
    return out


# --------------------------------------------------------------------------------------------
# Official challenge protocol (VOC-style greedy matching, 40 / 11-point interpolation)
# --------------------------------------------------------------------------------------------
@njit(cache=True)
def _greedy_tp(iou, thr):
    """iou: (P, G) with predictions in descending score order. Returns (P,) 1 for true positives."""
    P, G = iou.shape
    used = np.zeros(G, dtype=np.bool_)
    tp = np.zeros(P, dtype=np.int64)
    for i in range(P):
        best, bj = 0.0, -1
        for j in range(G):
            if used[j]:
                continue
            if iou[i, j] > best:
                best, bj = iou[i, j], j
        if bj >= 0 and best >= thr:
            tp[i] = 1
            used[bj] = True
    return tp


def _interp_ap(tp_sorted: np.ndarray, n_gt: int) -> tuple[float, float]:
    tp = np.cumsum(tp_sorted)
    fp = np.cumsum(1 - tp_sorted)
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / n_gt
    pmax = np.maximum.accumulate(prec[::-1])[::-1]          # max precision over recall >= this point

    def at(r):
        k = np.searchsorted(rec, r - 1e-12, side="left")   # first index with recall >= r (rec is non-decreasing)
        while k < len(rec) and rec[k] < r:                   # guard against the epsilon
            k += 1
        return float(pmax[k]) if k < len(rec) else 0.0

    r40 = float(np.mean([at(r) for r in np.linspace(1.0 / 40.0, 1.0, 40)]))
    r11 = float(np.mean([at(r) for r in np.linspace(0.0, 1.0, 11)]))
    return r40, r11


def _class_frames(preds: dict, gts: dict, c: str):
    """Per frame (in GT dict order): (pred boxes, scores, in_score_order, gt boxes) of class c."""
    out = []
    lc = c.lower()
    for fid, (gb, gn) in gts.items():
        gm = np.array([str(n).lower() == lc for n in gn], dtype=bool)
        g = np.asarray(gb, dtype=np.float64).reshape(-1, 7)[gm]
        ps = [p for p in preds.get(fid, []) if str(p.get("class", "Car")).lower() == lc]
        b = np.array([p["box"] for p in ps], dtype=np.float64).reshape(-1, 7)
        s_ = np.array([p["score"] for p in ps], dtype=np.float64)
        out.append((b, s_, g))
    return out


def _official_ap(frames: list, thr: float, kind: str, ious: list | None = None) -> dict | None:
    """frames: list of (det_boxes (D,7), det_scores (D,), gt_boxes (G,7)) for one class, in GT-dict order."""
    n_gt = sum(len(g) for _, _, g in frames)
    if n_gt == 0:
        return None
    scores, tps = [], []
    for k, (b, s_, g) in enumerate(frames):
        if len(b) == 0:
            continue
        if len(g) == 0:                                      # all false positives, original order
            scores.append(s_)
            tps.append(np.zeros(len(s_), dtype=np.int64))
            continue
        order = np.argsort(-s_, kind="stable")              # Python's sorted(key=-score) is stable
        iou = ious[k] if ious is not None else iou_matrix(b, g, kind)
        scores.append(s_[order])
        tps.append(_greedy_tp(np.ascontiguousarray(iou[order], dtype=np.float64), float(thr)))
    if not scores:
        return {"AP_R40": 0.0, "AP_R11": 0.0, "n_gt": int(n_gt), "n_pred": 0}
    sc = np.concatenate(scores)
    tp = np.concatenate(tps)
    order = np.argsort(-sc)                                  # same call as the official scorer (ties included)
    r40, r11 = _interp_ap(tp[order], n_gt)
    return {"AP_R40": r40, "AP_R11": r11, "n_gt": int(n_gt), "n_pred": int(len(sc))}


def ap_for_class(frames: list[tuple[np.ndarray, np.ndarray, np.ndarray]], thr: float, kind: str) -> dict | None:
    """Official AP. frames: list of (det_boxes (D,7), det_scores (D,), gt_boxes (G,7)) for one class."""
    return _official_ap(frames, thr, kind)


def evaluate(preds: dict, gts: dict, classes: list[str], iou_thresholds=(0.5, 0.7)) -> dict:
    """Official protocol. preds: {fid: [{"box": [7], "score": s, "class": c}, ...]}; gts: {fid: (boxes (G,7), names)}.

    Only frames present in gts are scored (as the server does). Returns {"per_class": {c: {"3d@0.5": {...},
    "bev@0.5": {...}, ...}}, "mAP_3d_0.5_R40": ..., ...} with None for classes without GT.
    """
    per_class: dict = {c: {} for c in classes}
    for c in classes:
        frames = _class_frames(preds, gts, c)
        pairs = [iou_pair(b, g) if len(b) and len(g) else (None, None) for b, _, g in frames]
        for kind, ix in (("3d", 0), ("bev", 1)):
            ious = [p[ix] for p in pairs]
            for thr in iou_thresholds:
                per_class[c][f"{kind}@{thr}"] = _official_ap(frames, thr, kind, ious)
    out = {"per_class": per_class}
    for kind in ("3d", "bev"):
        for thr in iou_thresholds:
            for interp in ("R40", "R11"):
                vals = [per_class[c][f"{kind}@{thr}"][f"AP_{interp}"] for c in classes if per_class[c][f"{kind}@{thr}"]]
                out[f"mAP_{kind}_{thr}_{interp}"] = float(np.mean(vals)) if vals else 0.0
    return out
