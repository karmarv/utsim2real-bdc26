"""Engine v6 (strategy S9, docs/decisions/2026-11-02-s9-clean-twin-plan.md): scalar calibrations that replace real
label rows in the generator.

- `walker_scalars` / `size_scalars`: summaries of legal label statistics (shares, medians, spreads, a range histogram
  and 19 quantiles per dimension). They are computed once and written to gen/*_v6.json; the generator reads only
  those numbers, never a label row (audit item 4, contingencies C1/C2; audit rule b: scalars only).
- `QuantileSizes`: comonotonic sampler of (l, w, h) from the quantile scalars (a long truck is also wide and tall).
- `lumpi_class_rule`: the LUMPI vehicle convention as four size thresholds. S0 on legal realval-A: transporter-sized
  vehicles (median 5.75 x 2.21 x 2.23 m) are labeled Truck, and the twin labels them Van (median 5.92 x 1.99 x 2.43 m);
  "Truck if l >= 5.6 or h >= 2.40, Van if l >= 4.6 and h >= 2.00, else Car" keeps 97.7% of the real trucks and 93.9%
  of the real cars in their class.
- `GroundBowl`: z offset a + b x + c y + d r + e r^2 fitted to the per-cell ground height of legal unlabeled
  realval-A frames against the generator's output (5 constants, audit rule e); applied to every point and box.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

QS = np.arange(5, 96, 5)                    # 19 quantiles per dimension


def size_scalars(samples: dict) -> dict:
    """{class: (N, 3) l, w, h} -> {class: {"q": QS, "lwh": 3 x 19 quantiles}}."""
    return {c: {"q": QS.tolist(), "lwh": np.percentile(np.asarray(v, float), QS, axis=0).T.round(4).tolist()}
            for c, v in samples.items() if len(v)}


class QuantileSizes:
    """Sample (l, w, h) by one uniform u per object through each dimension's quantile function (linear between the
    stored quantiles, flat beyond), with a small independent jitter."""

    def __init__(self, spec: dict):
        self.q = np.asarray(spec["q"], float) / 100.0
        self.lwh = np.asarray(spec["lwh"], float)          # (3, 19)

    def sample(self, n: int, rng) -> np.ndarray:
        u = np.clip(rng.uniform(self.q[0], self.q[-1], n)[:, None] + rng.normal(0, 0.03, (n, 3)), self.q[0], self.q[-1])
        return np.stack([np.interp(u[:, k], self.q, self.lwh[k]) for k in range(3)], 1)


def lumpi_class_rule(boxes: np.ndarray, names, rule: dict | None = None) -> np.ndarray:
    """Relabel Car and Van boxes by size (Truck boxes stay Truck)."""
    r = {"truck_l": 5.6, "truck_h": 2.40, "van_l": 4.6, "van_h": 2.00, **(rule or {})}
    names = np.array(names, dtype=object)
    b = np.asarray(boxes, float).reshape(-1, 7)
    veh = np.isin(names, ["Car", "Van"])
    truck = veh & ((b[:, 3] >= r["truck_l"]) | (b[:, 5] >= r["truck_h"]))
    van = veh & ~truck & (b[:, 3] >= r["van_l"]) & (b[:, 5] >= r["van_h"])
    out = names.copy()
    out[truck] = "Truck"
    out[van] = "Van"
    out[veh & ~truck & ~van] = "Car"
    return out


def walker_scalars(lwh: np.ndarray, xy: np.ndarray, split_l: float = 1.0,
                   range_bins=(0, 5, 10, 15, 20, 25, 30, 35, 40, 50, 70), sensors_xy=((0.0, 0.0),)) -> dict:
    """Box mixture (two modes split at l = split_l: share, medians, robust sd) and the histogram (shares) of the
    distance to the nearest sensor, which sets how many returns a walker gets."""
    lwh, xy = np.asarray(lwh, float), np.asarray(xy, float)
    modes = []
    for m in (lwh[:, 0] < split_l, lwh[:, 0] >= split_l):
        if m.sum() < 10:
            continue
        q25, q50, q75 = np.percentile(lwh[m], [25, 50, 75], axis=0)
        modes.append([round(float(m.mean()), 4), *q50.round(4).tolist(), *((q75 - q25) / 1.349).round(4).tolist()])
    r = np.min([np.hypot(xy[:, 0] - sx, xy[:, 1] - sy) for sx, sy in sensors_xy], axis=0)
    h, _ = np.histogram(r, bins=range_bins)
    return {"boxes": modes, "range_bins": list(range_bins), "range_share": (h / h.sum()).round(5).tolist(),
            "range_from": [list(map(float, v)) for v in sensors_xy]}


@dataclass
class GroundBowl:
    coef: np.ndarray                         # a, b, c, d, e

    def offset(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        r = np.hypot(x, y)
        a, b, c, d, e = self.coef
        return a + b * x + c * y + d * r + e * r * r

    def apply(self, points: np.ndarray, boxes: np.ndarray):
        p = np.array(points, copy=True)
        p[:, 2] += self.offset(p[:, 0], p[:, 1]).astype(p.dtype)
        b = np.array(boxes, dtype=np.float64, copy=True).reshape(-1, 7)
        if len(b):
            b[:, 2] += self.offset(b[:, 0], b[:, 1])
        return p, b

    def save(self, path: Path, meta: dict) -> None:
        Path(path).write_text(json.dumps({"coef": [float(v) for v in self.coef], **meta}, indent=1))

    @classmethod
    def load(cls, path: Path) -> "GroundBowl":
        return cls(np.asarray(json.loads(Path(path).read_text())["coef"], float))


def cell_ground(points_list, cell: float = 4.0, half: float = 40.0, q: float = 5.0, min_pts: int = 200) -> dict:
    """{(i, j): (q-th percentile z, n)} over the pooled frames, for cells with at least min_pts points."""
    P = np.concatenate([p[:, :3] for p in points_list])
    P = P[(np.abs(P[:, 0]) < half) & (np.abs(P[:, 1]) < half) & ~np.all(P == 0, 1)]
    i = np.floor((P[:, 0] + half) / cell).astype(int)
    j = np.floor((P[:, 1] + half) / cell).astype(int)
    key = i * 1000 + j
    order = np.argsort(key, kind="stable")
    key, z = key[order], P[order, 2]
    u, st = np.unique(key, return_index=True)
    st = list(st) + [len(key)]
    return {int(k): (float(np.percentile(z[st[n]:st[n + 1]], q)), st[n + 1] - st[n])
            for n, k in enumerate(u) if st[n + 1] - st[n] >= min_pts}


def fit_bowl(real_cells: dict, syn_cells: dict, cell: float = 4.0, half: float = 40.0) -> tuple[GroundBowl, dict]:
    """Weighted least squares of (real - synthetic) ground height per common cell on [1, x, y, r, r^2]."""
    ks = [k for k in real_cells if k in syn_cells]
    x = np.array([(k // 1000) * cell - half + cell / 2 for k in ks])
    y = np.array([(k % 1000) * cell - half + cell / 2 for k in ks])
    dz = np.array([real_cells[k][0] - syn_cells[k][0] for k in ks])
    w = np.sqrt(np.array([real_cells[k][1] for k in ks], float))
    r = np.hypot(x, y)
    A = np.stack([np.ones_like(x), x, y, r, r * r], 1)
    coef, *_ = np.linalg.lstsq(A * w[:, None], dz * w, rcond=None)
    res = dz - A @ coef
    stats = {"cells": len(ks), "dz_median_before": float(np.median(dz)), "dz_mad_before": float(np.median(np.abs(dz - np.median(dz)))),
             "abs_dz_weighted_before": float(np.average(np.abs(dz), weights=w ** 2)),
             "abs_dz_weighted_after": float(np.average(np.abs(res), weights=w ** 2))}
    return GroundBowl(coef), stats
