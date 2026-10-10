"""Error breakdowns of predictions against real-validation labels (S1 close-out diagnostics, docs/02-STRATEGY.md Section 8.1.2).

- box_errors: centre, bottom, top and size errors of predictions matched to GT in bird's-eye view, to tell a
  height or z problem (BEV right, 3D wrong) from a detection problem;
- ap_by_range: official AP with GT and predictions restricted to a range band around the frame origin;
- recall_by_points: recall of GT boxes by the number of real points inside them.
All of it runs on legal real validation data; nothing here touches the test frames.
"""
from __future__ import annotations

import numpy as np

from .boxes import count_points_in_boxes
from .evalap import _greedy_tp, _official_ap, iou_pair


def _class_rows(preds: dict, gts: dict, cls: str, score_min: float = 0.0):
    lc = cls.lower()
    for fid, (gb, gn) in gts.items():
        gm = np.array([str(n).lower() == lc for n in gn], dtype=bool)
        g = np.asarray(gb, dtype=np.float64).reshape(-1, 7)[gm]
        ps = [p for p in preds.get(fid, []) if str(p.get("class", "Car")).lower() == lc and p["score"] >= score_min]
        b = np.array([p["box"] for p in ps], dtype=np.float64).reshape(-1, 7)
        s = np.array([p["score"] for p in ps], dtype=np.float64)
        yield fid, b, s, g


def matched_pairs(preds: dict, gts: dict, cls: str, score_min: float = 0.1, bev_thr: float = 0.5) -> dict:
    """Greedy (score order) matches at BEV IoU >= bev_thr per frame. Returns gt, pred (N,7), score, iou3d (N,)."""
    G, P, S, I3 = [], [], [], []
    for fid, b, s, g in _class_rows(preds, gts, cls, score_min):
        if not len(b) or not len(g):
            continue
        order = np.argsort(-s, kind="stable")
        i3, ib = iou_pair(b[order], g, exact=False)
        used = np.zeros(len(g), bool)
        for k in range(len(order)):
            cand = np.where(~used, ib[k], -1.0)
            j = int(np.argmax(cand))
            if cand[j] >= bev_thr:
                used[j] = True
                G.append(g[j]); P.append(b[order[k]]); S.append(s[order[k]]); I3.append(i3[k, j])
    z = np.zeros((0, 7))
    return {"gt": np.array(G).reshape(-1, 7) if G else z, "pred": np.array(P).reshape(-1, 7) if P else z,
            "score": np.array(S), "iou3d": np.array(I3)}


def box_errors(pairs: dict) -> dict:
    """Per matched pair: dz (centre), dbottom, dtop, dh, dl, dw (pred minus GT, metres), |dyaw| (deg, mod 180),
    range (BEV distance of the GT centre from the origin) and GT bottom height."""
    g, p = pairs["gt"], pairs["pred"]
    dyaw = np.abs((p[:, 6] - g[:, 6] + np.pi / 2) % np.pi - np.pi / 2)
    return {"dz": p[:, 2] - g[:, 2], "dbottom": (p[:, 2] - p[:, 5] / 2) - (g[:, 2] - g[:, 5] / 2),
            "dtop": (p[:, 2] + p[:, 5] / 2) - (g[:, 2] + g[:, 5] / 2), "dh": p[:, 5] - g[:, 5],
            "dl": p[:, 3] - g[:, 3], "dw": p[:, 4] - g[:, 4], "dyaw_deg": np.degrees(dyaw),
            "range": np.hypot(g[:, 0], g[:, 1]), "gt_bottom": g[:, 2] - g[:, 5] / 2, "iou3d": pairs["iou3d"]}


def _stats(x: np.ndarray) -> dict:
    if not len(x):
        return {"median": None, "iqr": None}
    q1, q2, q3 = np.percentile(x, [25, 50, 75])
    return {"median": float(q2), "iqr": float(q3 - q1)}


def error_table(err: dict, range_bins: list[float]) -> dict:
    """Summary of box_errors overall and per range band, plus how much of the dz spread a linear model in
    (range, GT bottom height) explains: a high R^2 means a position-dependent z bias (slope), not noise."""
    def block(m):
        n = int(m.sum())
        out = {"n": n, "share_3d_iou_ge_0.5": float((err["iou3d"][m] >= 0.5).mean()) if n else None}
        for k in ("dz", "dbottom", "dtop", "dh", "dl", "dw", "dyaw_deg"):
            out[k] = _stats(err[k][m])
        return out
    allm = np.ones(len(err["dz"]), bool)
    res = {"all": block(allm), "by_range": {}}
    edges = list(range_bins) + [np.inf]
    for lo, hi in zip(edges[:-1], edges[1:]):
        res["by_range"][f"{lo:g}-{hi:g}"] = block((err["range"] >= lo) & (err["range"] < hi))
    if len(err["dz"]) > 10:
        X = np.stack([np.ones_like(err["range"]), err["range"], err["gt_bottom"]], 1)
        coef, *_ = np.linalg.lstsq(X, err["dz"], rcond=None)
        resid = err["dz"] - X @ coef
        var = float(np.var(err["dz"]))
        res["dz_linear_fit"] = {"intercept": float(coef[0]), "per_m_range": float(coef[1]), "per_m_gt_bottom": float(coef[2]),
                                "r2": float(1 - np.var(resid) / var) if var > 0 else None}
    return res


def ap_by_range(preds: dict, gts: dict, classes: list[str], range_bins: list[float], thr: float = 0.5) -> dict:
    """Official 3D AP@thr per class in each range band (GT and predictions both restricted by centre range)."""
    edges = list(range_bins) + [np.inf]
    out = {}
    for c in classes:
        rows = list(_class_rows(preds, gts, c))
        out[c] = {}
        for lo, hi in zip(edges[:-1], edges[1:]):
            frames = []
            for _, b, s, g in rows:
                rb, rg = np.hypot(b[:, 0], b[:, 1]), np.hypot(g[:, 0], g[:, 1])
                mb, mg = (rb >= lo) & (rb < hi), (rg >= lo) & (rg < hi)
                frames.append((b[mb], s[mb], g[mg]))
            r = _official_ap(frames, thr, "3d")
            out[c][f"{lo:g}-{hi:g}"] = None if r is None else {"AP": r["AP_R40"], "n_gt": r["n_gt"]}
    return out


def recall_by_points(preds: dict, gts: dict, points_of, classes: list[str], point_bins: list[int],
                     score_min: float = 0.3, thr: float = 0.5) -> dict:
    """Recall (3D IoU >= thr, predictions with score >= score_min) of GT boxes grouped by the number of real
    points inside them. points_of(fid) returns the frame's (N, 3+) points."""
    edges = list(point_bins) + [np.inf]
    out = {c: {f"{lo:g}-{hi:g}": [0, 0] for lo, hi in zip(edges[:-1], edges[1:])} for c in classes}
    for fid in gts:
        pts = points_of(fid)[:, :3]
        for c in classes:
            (_, b, s, g), = list(_class_rows(preds, {fid: gts[fid]}, c, score_min))
            if not len(g):
                continue
            npts = count_points_in_boxes(pts, g)
            hit = np.zeros(len(g), bool)
            if len(b):
                order = np.argsort(-s, kind="stable")
                i3, _ = iou_pair(b[order], g, exact=False)
                tp = _greedy_tp(np.ascontiguousarray(i3, dtype=np.float64), float(thr))
                for k in np.where(tp == 1)[0]:
                    hit[int(np.argmax(np.where(hit, -1.0, i3[k])))] = True
            for lo, hi in zip(edges[:-1], edges[1:]):
                m = (npts >= lo) & (npts < hi)
                out[c][f"{lo:g}-{hi:g}"][0] += int((m & hit).sum())
                out[c][f"{lo:g}-{hi:g}"][1] += int(m.sum())
    return {c: {k: {"recall": (v[0] / v[1]) if v[1] else None, "n_gt": v[1]} for k, v in d.items()} for c, d in out.items()}


def static_fp_share(preds: dict, gts: dict, cls: str, score_min: float | None = 0.5, min_frac: float = 0.2, cell: float = 1.0) -> dict:
    """Unmatched boxes of a class (BEV IoU < 0.3 with every GT) that repeat at the same cell in at least min_frac of
    their scene's frames: static structures detected as objects (the S2 diagnosis, docs/02-STRATEGY.md 8.2.1).
    Scenes come from the frame id before the last "__". score_min=None ranks instead of thresholding: only boxes
    scoring at least the median score of the class's true detections (BEV IoU >= 0.5) count, which stays comparable
    when fusion rescales the scores. Returns counts per frame, the static share and the threshold used."""
    from collections import Counter
    scene = lambda f: f.rsplit("__", 1)[0]
    frames = Counter(scene(f) for f in gts)
    per_frame = []
    for f, (gb, gn) in gts.items():
        gb = np.asarray(gb, dtype=np.float64).reshape(-1, 7)
        d = [x for x in preds.get(f, []) if x["class"] == cls]
        b = np.array([x["box"] for x in d]).reshape(-1, 7)
        sc_ = np.array([x["score"] for x in d])
        ib = iou_pair(b, gb, exact=False)[1].max(1) if len(b) and len(gb) else np.zeros(len(b))
        per_frame.append((f, b, sc_, ib))
    if score_min is None:
        tp = np.concatenate([s_[i_ >= 0.5] for _, _, s_, i_ in per_frame] + [np.zeros(0)])
        score_min = float(np.median(tp)) if len(tp) else 0.5
    hits, n_unmatched, n_boxes = Counter(), 0, 0
    for f, b, s_, ib in per_frame:
        k = s_ >= score_min
        n_boxes += int(k.sum())
        un = b[k & (ib < 0.3)]
        n_unmatched += len(un)
        hits.update((scene(f), int(round(x / cell)), int(round(y / cell))) for x, y in un[:, :2])
    static = sum(c for k, c in hits.items() if c >= min_frac * frames[k[0]])
    n = max(len(gts), 1)
    return {"score_min": score_min, "boxes_per_frame": n_boxes / n, "unmatched_per_frame": n_unmatched / n,
            "static_per_frame": static / n, "static_share": static / max(n_unmatched, 1)}
