"""Range-dependent z calibration per class (S1 close-out candidate C1, docs/02-STRATEGY.md Section 8.1.2).

    z_new = z + z0 + z_per_m * hypot(x, y)          (x, y: box centre in the frame; the V2X origin is the sensor)

The S1 diagnostics showed a z bias that changes with distance (V2X pedestrians: about +0.16 m at 0-10 m,
-0.11 m beyond 30 m) that a single per-class z_offset cannot remove. The two scalars are selected per class on
realval-A by the official AP (a grid search, hyperparameter selection on the real train split) and kept only
if realval-B passes the class gate; the calibration runs after per-class routing. A z shift leaves the BEV
intersections unchanged, so they are computed once per frame and only the vertical overlap is recomputed for
each candidate.
"""
from __future__ import annotations

import copy

import numpy as np

from ..evalap import _greedy_tp, _interp_ap, bev_intersection


def apply(preds: dict, calib: dict) -> dict:
    """Copy of preds with z shifted for every class in calib ({class: {"z0": a, "z_per_m": k}})."""
    if not calib:
        return preds
    lc = {c.lower(): v for c, v in calib.items()}
    out = {}
    for fid, dets in preds.items():
        new = []
        for d in dets:
            cc = lc.get(str(d.get("class", "Car")).lower())
            if cc:
                d = copy.copy(d)
                b = list(d["box"])
                b[2] = float(b[2] + cc.get("z0", 0.0) + cc.get("z_per_m", 0.0) * np.hypot(b[0], b[1]))
                d["box"] = b
            new.append(d)
        out[fid] = new
    return out


class ZSearch:
    """Official 3D AP@thr of one class under candidate (z0, z_per_m) shifts, with cached BEV intersections."""

    def __init__(self, preds: dict, gts: dict, cls: str, thr: float = 0.5, exact: bool | None = False):
        self.thr, self.frames, self.n_gt = float(thr), [], 0
        lc = cls.lower()
        for fid, (gb, gn) in gts.items():
            gm = np.array([str(n).lower() == lc for n in gn], dtype=bool)
            g = np.asarray(gb, dtype=np.float64).reshape(-1, 7)[gm]
            ps = [p for p in preds.get(fid, []) if str(p.get("class", "Car")).lower() == lc]
            self.n_gt += len(g)
            if not ps:
                continue
            b = np.array([p["box"] for p in ps], dtype=np.float64).reshape(-1, 7)
            s = np.array([p["score"] for p in ps], dtype=np.float64)
            if len(g):
                o = np.argsort(-s, kind="stable")
                b, s = b[o], s[o]
                inter = bev_intersection(b, g, exact=exact)
            else:
                inter = np.zeros((len(b), 0))
            self.frames.append((b, s, g, inter, np.hypot(b[:, 0], b[:, 1])))

    def ap(self, z0: float = 0.0, k: float = 0.0) -> float:
        if self.n_gt == 0:
            return float("nan")
        scores, tps = [], []
        for b, s, g, inter, r in self.frames:
            scores.append(s)
            if not len(g):
                tps.append(np.zeros(len(s), dtype=np.int64))
                continue
            zc = b[:, 2] + z0 + k * r
            top = np.minimum(zc[:, None] + b[:, None, 5] / 2, g[None, :, 2] + g[None, :, 5] / 2)
            bot = np.maximum(zc[:, None] - b[:, None, 5] / 2, g[None, :, 2] - g[None, :, 5] / 2)
            v = inter * np.maximum(top - bot, 0.0)
            vol = (b[:, 3] * b[:, 4] * b[:, 5])[:, None] + (g[:, 3] * g[:, 4] * g[:, 5])[None, :] - v
            iou = np.where((v > 0) & (vol > 0), v / np.where(vol > 0, vol, 1.0), 0.0)
            tps.append(_greedy_tp(np.ascontiguousarray(iou), self.thr))
        sc, tp = np.concatenate(scores), np.concatenate(tps)
        return _interp_ap(tp[np.argsort(-sc)], self.n_gt)[0]

    def search(self, z0_grid, k_grid) -> dict:
        """Best (z0, z_per_m) on the grid; ties go to the smaller correction."""
        base = self.ap(0.0, 0.0)
        best = (base, 0.0, 0.0)
        for k in k_grid:
            for z0 in z0_grid:
                a = self.ap(z0, k)
                if a > best[0] + 1e-9 or (abs(a - best[0]) <= 1e-9 and abs(z0) + 30 * abs(k) < abs(best[1]) + 30 * abs(best[2])):
                    best = (a, float(z0), float(k))
        return {"ap_base": base, "ap_best": best[0], "z0": best[1], "z_per_m": best[2]}


Z0_GRID = np.round(np.arange(-0.30, 0.301, 0.025), 3)
K_GRID = np.round(np.arange(-0.015, 0.0151, 0.0025), 4)
