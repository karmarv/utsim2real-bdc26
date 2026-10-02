#!/usr/bin/env python
"""Fit the scene-density prior (bdc26.density) from legal real frames and the generator's uniform output.

    python common/tools/fit_density_prior.py --track lumpi --real pcdet/realval-v1 --real-split val \
        --syn pcdet/g1-v1 --out gen/density_prior_v1.npz
Real frames: the split's frames MINUS every realism-proxy-* set (the proxies stay an honest test of the result).
Every real frame used is passed through ForbiddenGuard and logged with its purpose.
"""
import argparse
import re
from pathlib import Path

import numpy as np

from _common import data_path, load_track
from bdc26 import density
from bdc26.guard import ForbiddenGuard


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", required=True)
    ap.add_argument("--real", required=True)
    ap.add_argument("--real-split", default="val")
    ap.add_argument("--syn", required=True)
    ap.add_argument("--syn-split", default="train")
    ap.add_argument("--n-real", type=int, default=400)
    ap.add_argument("--n-syn", type=int, default=400)
    ap.add_argument("--cell", type=float, nargs=3, default=[8.0, 8.0, 2.5],
                    help="cell size in metres (LUMPI sweep on legal proxies: 8 x 8 x 2.5 best among cells dividing the range)")
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--clip", type=float, nargs=2, default=[0.01, 100.0])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t = load_track(a.track)
    rroot, sroot = data_path(t, a.real), data_path(t, a.syn)
    proxies = set()
    for d in t.pcdet.glob("realism-proxy-*"):
        proxies |= {f.stem for f in (d / "points").glob("*.npy")}
    rids = [i for i in (rroot / "ImageSets" / f"{a.real_split}.txt").read_text().split() if i not in proxies]
    rids = rids[:: max(1, len(rids) // a.n_real)][: a.n_real]
    guard = ForbiddenGuard.for_track(t, quiet=True)
    keys = []
    for i in rids:                                  # realval ids look like "Measurement4__000123" (LUMPI)
        m = re.match(r"(.+)__(\d+)$", i)
        keys.append((m.group(1), int(m.group(2))) if m else (i, 0))
    allowed = set(guard.filter(keys, purpose=f"density prior fit ({a.out})"))
    rids = [i for i, k in zip(rids, keys) if k in allowed]
    sids = (sroot / "ImageSets" / f"{a.syn_split}.txt").read_text().split()
    sids = sids[:: max(1, len(sids) // a.n_syn)][: a.n_syn]
    real = [np.load(rroot / "points" / f"{i}.npy") for i in rids]
    syn = [np.load(sroot / "points" / f"{i}.npy") for i in sids]
    prior = density.fit(real, syn, t.pc_range, cell=tuple(a.cell), alpha=a.alpha, clip=tuple(a.clip),
                        meta={"real": f"{a.real}:{a.real_split} minus realism proxies", "syn": f"{a.syn}:{a.syn_split}"})
    out = t.root / a.out
    prior.save(out)
    r = prior.ratio
    print(f"{len(real)} real / {len(syn)} synthetic frames -> {out}; ratio p5/p50/p95 "
          f"{np.percentile(r, 5):.2f}/{np.percentile(r, 50):.2f}/{np.percentile(r, 95):.2f}")


if __name__ == "__main__":
    main()
