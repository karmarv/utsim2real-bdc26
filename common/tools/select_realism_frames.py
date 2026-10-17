#!/usr/bin/env python
"""Choose the 50 submitted synthetic frames from a generated split by matching LEGAL real proxies (module M12).

    python common/tools/select_realism_frames.py --track lumpi --syn pcdet/g1-v2 --split val \
        --fit-ref pcdet/realism-proxy-1 --fit-ref pcdet/realism-proxy-2 --fit-ref pcdet/realism-proxy-3 \
        --test-ref pcdet/realism-proxy-4 --test-ref pcdet/realism-proxy-5 --out <model>/test/synthetic_ids.txt

Objective: the Frechet distance between the pooled xyz Gaussian of the chosen frames and that of the fit
proxies (the FPD term), computed exactly from per-frame sufficient statistics, minimized by greedy swaps from a
random start. --objective fpd+emd (R5) then refines the selection by greedy swaps on the realism terms that matter,
EMD / 5 + FPD / 50 (CD and MMD are about zero), with EMD approximated by the sliced Wasserstein-1 distance between a
fixed 400-point sample of every frame and a fixed sample of the fit proxies (64 directions), scaled once to the
exact EMD of the FPD selection. The held-out proxies give the honest R estimate (full realism score, before and after).
Held-out scores are computed in the packaged (sorted) frame order, as the server draws its 10,000-point subsample:
the order alone moves R by up to 0.006 for one set (S6 noise study: sd 0.0012-0.0025 over subsample seeds).
--split train+val (S6) takes the pool from the whole corpus: every frame comes from the generator configuration the
detectors were trained with, so the frames stay representative of the training data.
Frames are only chosen, never modified (V2X frames are scored with the (0,0,0) nulls the packager adds);
the 50 test frames are never involved.
"""
import argparse
from pathlib import Path

import numpy as np
from scipy.linalg import sqrtm

from _common import data_path, load_track
from bdc26 import realism
from bdc26.frames import in_range_mask


def suff(p, pc_range):
    q = p[in_range_mask(p, pc_range)].astype(np.float64)
    return len(q), q.sum(0), q.T @ q


def gauss(stats):
    n = sum(s[0] for s in stats)
    m = sum(s[1] for s in stats) / n
    C = sum(s[2] for s in stats) / n - np.outer(m, m)
    return m, C


def frechet(a, b):
    (m1, C1), (m2, C2) = a, b
    return float(((m1 - m2) ** 2).sum() + np.trace(C1 + C2 - 2 * sqrtm(C1 @ C2).real))


def refine_emd(t, frames, S, chosen, pool, target, fit_frames, a, k=400, n_dir=64):
    """Greedy swaps on EMD/5 + FPD/50 (R5), EMD from the sliced W1 of fixed per-frame samples (see the docstring)."""
    rng = np.random.default_rng([a.seed, 7])
    D = rng.normal(size=(3, n_dir))
    D /= np.linalg.norm(D, axis=0)
    def samp(p, n):
        q = p[in_range_mask(p, t.pc_range)]
        return q[rng.choice(len(q), n, replace=len(q) < n)].astype(np.float64)
    proj = {i: samp(frames[i], k) @ D for i in pool}                      # (k, n_dir) per frame, fixed
    ref = np.sort(np.concatenate([samp(f, max(1, (50 * k) // len(fit_frames) + 1)) for f in fit_frames])[: 50 * k] @ D, axis=0)
    def sw(ids):
        x = np.sort(np.concatenate([proj[i] for i in ids]), axis=0)
        return float(np.abs(x - ref[: len(x)]).mean())
    sw0 = sw(chosen)
    exact = realism.score([frames[i] for i in chosen], fit_frames[:50], t.name, exact_emd=True)
    scale = exact["EMD"] ** 2 / max(sw0, 1e-12)                            # W1 = scale x SW1 near the FPD selection
    J = lambda ids: np.sqrt(scale * sw(ids)) / 5 + frechet(gauss([S[i] for i in ids]), target) / 50
    rest = [i for i in pool if i not in set(chosen)]
    cur = J(chosen)
    j0 = cur
    for _ in range(a.refine_iters):
        kk, jj = rng.integers(50), rng.integers(len(rest))
        trial = chosen.copy()
        trial[kk] = rest[jj]
        v = J(trial)
        if v < cur:
            rest[jj] = chosen[kk]
            chosen, cur = trial, v
    print(f"EMD refinement: EMD/5 + FPD/50 (sliced-W1 estimate) {j0:.4f} -> {cur:.4f} (exact EMD of the FPD selection "
          f"vs a fit proxy {exact['EMD']:.3f})")
    return chosen


def load_dir(t, spec):
    root = data_path(t, spec)
    return [np.load(f)[:, :3] for f in sorted((root / "points").glob("*.npy"))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", required=True)
    ap.add_argument("--syn", required=True)
    ap.add_argument("--split", default="val", help="split of --syn, or several joined by + (S6: train+val)")
    ap.add_argument("--fit-ref", action="append", required=True)
    ap.add_argument("--test-ref", action="append", default=[])
    ap.add_argument("--iters", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--objective", choices=["fpd", "fpd+emd"], default="fpd")
    ap.add_argument("--refine-iters", type=int, default=3000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t = load_track(a.track)
    if any("kit" in Path(r).parts for r in a.fit_ref + a.test_ref):
        raise SystemExit("refusing starting-kit frames (forbidden)")
    root = data_path(t, a.syn)
    pool = [i for sp in a.split.split("+") for i in (root / "ImageSets" / f"{sp}.txt").read_text().split()]   # S6: train+val
    frames = {i: np.load(root / "points" / f"{i}.npy")[:, :3] for i in pool}
    null_frac = float(t["resample"].get("null_fraction", 0.0))
    if null_frac > 0:                     # V2X: score frames as they will be submitted (with (0,0,0) nulls)
        from bdc26.frames import with_nulls
        frames = {i: with_nulls(f, null_frac, int(t["resample"]["n_points"]), np.random.default_rng([a.seed, k]))
                  for k, (i, f) in enumerate(frames.items())}
    S = {i: suff(f, t.pc_range) for i, f in frames.items()}
    target = gauss([suff(f, t.pc_range) for r in a.fit_ref for f in load_dir(t, r)])
    rng = np.random.default_rng(a.seed)
    chosen = list(rng.choice(pool, 50, replace=False))
    rest = [i for i in pool if i not in set(chosen)]
    cur = frechet(gauss([S[i] for i in chosen]), target)
    start = cur
    for _ in range(a.iters):
        k, j = rng.integers(50), rng.integers(len(rest))
        trial = chosen.copy()
        trial[k] = rest[j]
        v = frechet(gauss([S[i] for i in trial]), target)
        if v < cur:
            rest[j] = chosen[k]
            chosen, cur = trial, v
    print(f"pooled FPD to fit proxies: random start {start:.2f} -> selected {cur:.2f}")
    fpd_only = list(chosen)
    if a.objective == "fpd+emd":
        chosen = refine_emd(t, frames, S, chosen, pool, target, [f for r in a.fit_ref for f in load_dir(t, r)], a)
    rand = list(np.random.default_rng(a.seed).choice(pool, 50, replace=False))
    sets = (("random", rand), ("selected", chosen)) if a.objective == "fpd" else (("random", rand), ("fpd only", fpd_only), ("selected", chosen))
    for name, ids in sets:
        syn = [frames[i] for i in sorted(ids)]          # the packaged order: the scorer's subsample depends on it (S6)
        for r in a.test_ref:
            res = realism.score(syn, load_dir(t, r), t.name, exact_emd=True)     # converged EMD, as the server
            print(f"{name:9s} vs {r}: R {res['R']:.4f}  CD {res['CD']:.2f} MMD {res['MMD']:.4f} EMD {res['EMD']:.3f} FPD {res['FPD']:.2f}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(sorted(chosen)) + "\n")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
