#!/usr/bin/env python
"""Choose the 50 submitted synthetic frames from a generated split by matching LEGAL real proxies (module M12).

    python common/tools/select_realism_frames.py --track lumpi --syn pcdet/g1-v2 --split val \
        --fit-ref pcdet/realism-proxy-1 --fit-ref pcdet/realism-proxy-2 --fit-ref pcdet/realism-proxy-3 \
        --test-ref pcdet/realism-proxy-4 --test-ref pcdet/realism-proxy-5 --out <model>/test/synthetic_ids.txt

Objective: the Frechet distance between the pooled xyz Gaussian of the chosen frames and that of the fit
proxies (the FPD term), computed exactly from per-frame sufficient statistics, minimized by greedy swaps from a
random start. The held-out proxies give the honest R estimate (full realism score, before and after).
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


def load_dir(t, spec):
    root = data_path(t, spec)
    return [np.load(f)[:, :3] for f in sorted((root / "points").glob("*.npy"))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", required=True)
    ap.add_argument("--syn", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--fit-ref", action="append", required=True)
    ap.add_argument("--test-ref", action="append", default=[])
    ap.add_argument("--iters", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t = load_track(a.track)
    if any("kit" in Path(r).parts for r in a.fit_ref + a.test_ref):
        raise SystemExit("refusing starting-kit frames (forbidden)")
    root = data_path(t, a.syn)
    pool = (root / "ImageSets" / f"{a.split}.txt").read_text().split()
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
    rand = list(np.random.default_rng(a.seed).choice(pool, 50, replace=False))
    for name, ids in (("random", rand), ("selected", chosen)):
        syn = [frames[i] for i in ids]
        for r in a.test_ref:
            res = realism.score(syn, load_dir(t, r), t.name, exact_emd=True)     # converged EMD, as the server
            print(f"{name:9s} vs {r}: R {res['R']:.4f}  CD {res['CD']:.2f} MMD {res['MMD']:.4f} EMD {res['EMD']:.3f} FPD {res['FPD']:.2f}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(sorted(chosen)) + "\n")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
