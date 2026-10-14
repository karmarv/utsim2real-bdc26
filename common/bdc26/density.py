"""Scene-density calibration of synthetic frames (engine G1, realism stage).

Problem: the UT twins miss static structure that the real sensors see (LUMPI: 2-17x more real points at
y = +10..+40 m and more above-ground returns), so uniformly resampled UT frames have the wrong spatial
distribution: raw UT-LUMPI frames reach only R ~0.59 (our proxy and the ECCV winner's report agree).

Fix (a generator setting, applied identically to the training corpus and the submitted frames):
  ratio(cell) = real density / synthetic density on a 3D grid, both measured on frames already resampled the
  organizers' way. Real densities come from LEGAL unlabeled real frames (guard-allowed, disjoint from the
  realism proxy sets used for scoring); synthetic densities from the generator's own uniform output.
  At resampling time, object points (UT actors and inserted walkers) keep the uniform rate, so the density
  on objects, which the detector sees, is unchanged; background points are drawn with probability
  proportional to ratio(cell). No real point is copied, and the 50 test frames are never involved.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .frames import in_range_mask


@dataclass
class DensityPrior:
    edges: tuple            # (ex, ey, ez) bin edges
    ratio: np.ndarray       # (nx, ny, nz)
    meta: dict

    def cell_ratio(self, pts: np.ndarray) -> np.ndarray:
        idx = [np.clip(np.searchsorted(e, pts[:, k], side="right") - 1, 0, len(e) - 2) for k, e in enumerate(self.edges)]
        return self.ratio[idx[0], idx[1], idx[2]]

    def save(self, path: Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, ex=self.edges[0], ey=self.edges[1], ez=self.edges[2], ratio=self.ratio,
                            meta=np.array(repr(self.meta)))

    @classmethod
    def load(cls, path: Path) -> "DensityPrior":
        d = np.load(path, allow_pickle=False)
        return cls((d["ex"], d["ey"], d["ez"]), d["ratio"], {"source": str(path), "fit": str(d["meta"])})


def histogram(frames, edges) -> np.ndarray:
    h = np.zeros([len(e) - 1 for e in edges])
    for f in frames:
        p = f[:, :3][~np.all(f[:, :3] == 0, 1)]
        h += np.histogramdd(p, bins=edges)[0]
    return h


def fit(real_frames, syn_frames, pc_range, cell=(2.0, 2.0, 0.5), alpha=0.5, clip=(0.05, 20.0), meta=None) -> DensityPrior:
    x0, y0, z0, x1, y1, z1 = pc_range
    edges = (np.arange(x0, x1 + 1e-6, cell[0]), np.arange(y0, y1 + 1e-6, cell[1]), np.arange(z0, z1 + 1e-6, cell[2]))
    hr, hs = histogram(real_frames, edges), histogram(syn_frames, edges)
    K = hr.size
    pr = (hr + alpha) / (hr.sum() + alpha * K)
    ps = (hs + alpha) / (hs.sum() + alpha * K)
    ratio = np.clip(pr / ps, *clip)
    return DensityPrior(edges, ratio, dict(meta or {}, n_real=len(real_frames), n_syn=len(syn_frames), cell=cell,
                                           alpha=alpha, clip=clip))


def inclusion_probs(w: np.ndarray, m: int) -> np.ndarray:
    """Bernoulli inclusion probabilities min(1, c * w) whose sum is m (bisection on c)."""
    if m >= len(w):
        return np.ones(len(w))
    lo, hi = 0.0, m / max(w.min(), 1e-12)
    for _ in range(60):
        c = (lo + hi) / 2
        if np.minimum(1.0, c * w).sum() > m:
            hi = c
        else:
            lo = c
    return np.minimum(1.0, lo * w)


def resample_calibrated(points: np.ndarray, n: int, rng: np.random.Generator, pc_range, prior: DensityPrior | None,
                        is_object: np.ndarray, n_ref: int | None = None) -> np.ndarray:
    """Mask to range; object points kept at the uniform rate n / N; background points kept with probability
    proportional to the prior ratio of their cell (exact Bernoulli inclusion probabilities; uniform without a
    prior), then the frame is trimmed or padded to exactly n points.
    n_ref: take N from a reference frame instead (engine G2: the in-range count before the G2 pass, so added
    clutter returns and the larger shadows of re-cast actors do not move the object sampling rate that the G1
    calibration matched; R3)."""
    from .frames import resample
    inr = in_range_mask(points, pc_range)
    p, obj = points[inr], np.asarray(is_object, dtype=bool)[inr]
    N = len(p) if n_ref is None else max(int(n_ref), 1)
    if len(p) <= n:
        return resample(p, n, rng, None, mask_first=False)
    q = min(1.0, n / N)
    keep = obj & (rng.random(len(p)) < q)
    bg = np.nonzero(~obj)[0]
    m = n - int(keep.sum())
    if m > 0 and len(bg):
        pr = inclusion_probs(prior.cell_ratio(p[bg]) if prior is not None else np.ones(len(bg)), m)
        keep[bg[rng.random(len(bg)) < pr]] = True
    return resample(p[keep], n, rng, None, mask_first=False)
