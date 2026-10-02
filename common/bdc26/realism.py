"""Realism score exactly as the challenge computes it (starting kit `scoring_program/metrics.py`), CPU only.

Protocol (verified bit-for-bit against the kit by common/tests/test_official_parity.py):
  1. concatenate the 50 synthetic frames and the 50 reference frames (float32),
  2. mask both to the track range, bounds INCLUSIVE ((0,0,0) null returns are inside the range and are kept),
  3. one numpy Generator(seed 1234) draws, in this order: the 10,000-point synthetic subsample, the 10,000-point
     real subsample, then 1,000 + 1,000 points for the MMD bandwidth (median heuristic, zero distances dropped),
  4. CD (squared L2, symmetric), unbiased RBF MMD^2, EMD = sqrt(W1) with POT `ot.emd2(numItermax=10_000_000)`
     (converged), FPD = Frechet distance between 3-variate Gaussians of the xyz points,
  5. normalize with config.json: CD [2, 30], MMD [0, 0.5], EMD [0, 5], FPD [0, 50]; R = 1 - mean(clip terms).

The reference frames must be LEGAL real frames (never the forbidden frames, never the starting kit's test frames).

Usage (CLI wrapper: common/tools/score_realism.py):
  python -m bdc26.realism --syn /path/to/synthetic_bins --ref /path/to/legal_real_bins --track v2x
"""
import argparse
import glob
import os

import numpy as np
from scipy import linalg
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

RANGES = {"v2x-track": (-40, -40, -8, 40, 40, 2), "lumpi-track": (-40, -40, -5, 40, 40, 5)}
NORM = {"CD": (2.0, 30.0), "MMD": (0.0, 0.5), "EMD": (0.0, 5.0), "FPD": (0.0, 50.0)}
AP_MAX = 0.70
N_SUBSAMPLE = 10_000


def load_bin(path):
    """The scorer's reader: float32 N x 3, or N x 4 with intensity dropped."""
    a = np.fromfile(path, dtype=np.float32)
    if a.size == 0:
        return np.zeros((0, 3), dtype=np.float32)
    if a.size % 3 == 0:
        return a.reshape(-1, 3)
    if a.size % 4 == 0:
        return a.reshape(-1, 4)[:, :3]
    raise ValueError(f"{path}: {a.size} float32s is not divisible by 3 or 4")


def _mask(pts, pc_range):
    x0, y0, z0, x1, y1, z1 = pc_range
    m = (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1) & (pts[:, 2] >= z0) & (pts[:, 2] <= z1)
    return pts[m]


def concat_and_mask(clouds, pc_range):
    parts = [_mask(np.asarray(c)[:, :3], pc_range) for c in clouds]
    parts = [q for q in parts if q.shape[0] > 0]
    if not parts:
        return np.zeros((0, 3), dtype=np.float32)
    return np.concatenate(parts, axis=0).astype(np.float32, copy=False)


def subsample(P, n, rng):
    return P[rng.choice(P.shape[0], n, replace=P.shape[0] < n)]


def chamfer(P, Q):
    d_pq, _ = cKDTree(Q).query(P, k=1)
    d_qp, _ = cKDTree(P).query(Q, k=1)
    return float(np.mean(d_pq ** 2) + np.mean(d_qp ** 2))


def _gamma(X, Y, rng, sample_size=1000):
    nx, ny = min(sample_size, X.shape[0]), min(sample_size, Y.shape[0])
    Xs = X[rng.choice(X.shape[0], nx, replace=False)]
    Ys = Y[rng.choice(Y.shape[0], ny, replace=False)]
    D2 = cdist(np.vstack([Xs, Ys]), np.vstack([Xs, Ys]), "sqeuclidean")
    med = float(np.median(D2[D2 > 0])) if (D2 > 0).any() else 1.0
    return 1.0 / max(2.0 * med, 1e-12)


def mmd_unbiased(X, Y, rng, chunk=2500):
    """Unbiased RBF MMD^2 (chunked; equals the kit's dense computation up to float summation order)."""
    gamma = _gamma(X, Y, rng)

    def ksum(A, B, same):
        tot = 0.0
        for i in range(0, len(A), chunk):
            K = np.exp(-gamma * cdist(A[i:i + chunk], B, "sqeuclidean"))
            if same:
                K[np.arange(K.shape[0]), np.arange(i, i + K.shape[0])] = 0.0
            tot += K.sum()
        return tot

    n, m = len(X), len(Y)
    mmd = ksum(X, X, True) / (n * (n - 1)) + ksum(Y, Y, True) / (m * (m - 1)) - 2.0 * ksum(X, Y, False) / (n * m)
    return float(mmd), float(gamma)


def emd(P, Q, num_iter_max=10_000_000):
    import ot                                 # POT; exact network simplex, converged at 10M iterations
    a = np.full(len(P), 1.0 / len(P))
    b = np.full(len(Q), 1.0 / len(Q))
    w1 = ot.emd2(a, b, cdist(P, Q, metric="euclidean"), numItermax=int(num_iter_max))
    return float(np.sqrt(max(w1, 0.0)))


def fpd(P, Q, eps=1e-6):
    m1, m2 = P.mean(0), Q.mean(0)
    C1, C2 = np.cov(P, rowvar=False), np.cov(Q, rowvar=False)
    cm, _ = linalg.sqrtm(C1 @ C2, disp=False)
    if not np.isfinite(cm).all():
        off = np.eye(C1.shape[0]) * eps
        cm = linalg.sqrtm((C1 + off) @ (C2 + off))
    if np.iscomplexobj(cm):
        cm = cm.real
    d = m1 - m2
    return float(d @ d + np.trace(C1) + np.trace(C2) - 2.0 * np.trace(cm))


def normalize(metrics):
    terms = {k: float(np.clip((metrics[k] - lo) / (hi - lo), 0.0, 1.0)) for k, (lo, hi) in NORM.items()}
    return terms, 1.0 - float(np.mean(list(terms.values())))


def combined(map_3d, realism):
    return 0.6 * float(np.clip(map_3d / AP_MAX, 0.0, 1.0)) + 0.4 * realism


def score(syn_clouds, ref_clouds, track, exact_emd=True, seed=1234):
    """track: a track name ('v2x-track', 'lumpi-track', or alias 'v2x'/'lumpi') or an explicit range tuple.
    exact_emd=False caps the EMD solver at 100k iterations (faster; over-estimates EMD by a few percent)."""
    rng_box = RANGES[{"v2x": "v2x-track", "lumpi": "lumpi-track"}.get(track, track)] if isinstance(track, str) else tuple(track)
    rng = np.random.default_rng(seed)
    S_all, R_all = concat_and_mask(syn_clouds, rng_box), concat_and_mask(ref_clouds, rng_box)
    S, R = subsample(S_all, N_SUBSAMPLE, rng), subsample(R_all, N_SUBSAMPLE, rng)
    null_frac = lambda clouds: float(np.mean(np.concatenate([np.all(np.asarray(c)[:, :3] == 0, 1) for c in clouds])))
    out = {"CD": chamfer(S, R)}
    out["MMD"], out["MMD_gamma"] = mmd_unbiased(S, R, rng)
    out["EMD"] = emd(S, R, 10_000_000 if exact_emd else 100_000)
    out["FPD"] = fpd(S, R)
    out["terms"], out["R"] = normalize(out)
    out["n_syn_points_pre_subsample"], out["n_real_points_pre_subsample"] = int(len(S_all)), int(len(R_all))
    out["null_frac_syn"], out["null_frac_ref"] = null_frac(syn_clouds), null_frac(ref_clouds)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--syn", required=True, help="dir of synthetic .bin frames (float32 N x 3)")
    ap.add_argument("--ref", required=True, help="dir of LEGAL real reference .bin frames")
    ap.add_argument("--track", choices=list(RANGES) + ["v2x", "lumpi"], required=True)
    ap.add_argument("--map", type=float, default=None, help="optional real-val mAP to print a combined score")
    ap.add_argument("--no-exact", action="store_true")
    args = ap.parse_args()
    syn = [load_bin(p) for p in sorted(glob.glob(os.path.join(args.syn, "*.bin")))]
    ref = [load_bin(p) for p in sorted(glob.glob(os.path.join(args.ref, "*.bin")))]
    assert len(syn) == 50, f"expected 50 synthetic frames, got {len(syn)}"
    res = score(syn, ref, args.track, exact_emd=not args.no_exact)
    for k, v in res.items():
        print(f"{k:14s} {v}")
    if args.map is not None:
        print(f"{'combined':14s} {combined(args.map, res['R']):.4f}")
