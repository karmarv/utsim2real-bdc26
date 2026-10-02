"""Point-cloud conventions shared by all sources: range masking, null returns, 50k resampling.

The organizers' protocol for real frames (confirmed from the server's detailed results): mask to the
track range first, then draw exactly 50,000 points uniformly (duplicates only when fewer remain).
Ouster null returns are stored as xyz = (0, 0, 0) (their intensity column may be non-zero); they lie
inside the range and are KEPT in realism frames, but must be stripped before detection.
"""
from __future__ import annotations

import numpy as np


def null_mask(points: np.ndarray) -> np.ndarray:
    return np.all(points[:, :3] == 0.0, axis=1)


def strip_nulls(points: np.ndarray) -> np.ndarray:
    return points[~null_mask(points)]


def in_range_mask(points: np.ndarray, pc_range, inclusive: bool = True) -> np.ndarray:
    x0, y0, z0, x1, y1, z1 = pc_range
    p = points
    if inclusive:
        return (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] >= y0) & (p[:, 1] <= y1) & (p[:, 2] >= z0) & (p[:, 2] <= z1)
    return (p[:, 0] > x0) & (p[:, 0] < x1) & (p[:, 1] > y0) & (p[:, 1] < y1) & (p[:, 2] > z0) & (p[:, 2] < z1)


def mask_to_range(points: np.ndarray, pc_range, inclusive: bool = True) -> np.ndarray:
    return points[in_range_mask(points, pc_range, inclusive)]


def resample(points: np.ndarray, n: int, rng: np.random.Generator, pc_range=None,
             mask_first: bool = True, replace_if_short: bool = True) -> np.ndarray:
    """Organizer-style resampling: optional range mask, then exactly n points drawn uniformly."""
    p = mask_to_range(points, pc_range) if (mask_first and pc_range is not None) else points
    if len(p) == 0:
        return np.zeros((n, points.shape[1]), dtype=points.dtype)
    if len(p) >= n:
        idx = rng.choice(len(p), n, replace=False)
    elif replace_if_short:
        idx = np.concatenate([np.arange(len(p)), rng.choice(len(p), n - len(p), replace=True)])
    else:
        idx = np.arange(len(p))
    return p[np.sort(idx)]


def with_nulls(points: np.ndarray, null_fraction: float, n_total: int, rng: np.random.Generator) -> np.ndarray:
    """A frame of exactly n_total points whose (0,0,0) share is null_fraction (real V2X frames store no-returns
    as (0,0,0); about 31% after the organizers' resampling). Valid points are subsampled uniformly."""
    p = strip_nulls(np.asarray(points)[:, :3])
    n_null = int(round(n_total * null_fraction))
    n_valid = n_total - n_null
    idx = rng.choice(len(p), n_valid, replace=len(p) < n_valid)
    out = np.concatenate([p[np.sort(idx)], np.zeros((n_null, 3), dtype=p.dtype)])
    return out[rng.permutation(len(out))]


def frame_stats(points: np.ndarray, pc_range) -> dict:
    """Format-level statistics (safe to compute on test frames: nothing is fitted to them)."""
    inr = in_range_mask(points, pc_range)
    nn = ~null_mask(points)
    z = points[inr & nn, 2]
    return {
        "n_points": int(len(points)),
        "n_in_range": int(inr.sum()),
        "null_fraction": float(1.0 - nn.mean()) if len(points) else 0.0,
        "xyz_min": points[nn, :3].min(0).round(3).tolist() if nn.any() else None,
        "xyz_max": points[nn, :3].max(0).round(3).tolist() if nn.any() else None,
        "z_p05_p50": [float(np.percentile(z, 5)), float(np.percentile(z, 50))] if len(z) else None,
        "n_columns": int(points.shape[1]),
    }
