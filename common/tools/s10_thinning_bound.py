#!/usr/bin/env python
"""S10 increment 5c bound (docs/decisions/2026-11-08-s10-clean-final-plan.md Section 15.6): how much realism a cell-wise
return-probability (thinning) correction could earn, before any generator change. Read-only.

The correction is fitted on the FIT proxies only (default 1-3): per cell, w = real share / synthetic share of the masked
points, keep probability w / max(w) with w capped at --cap. It is applied to the 50 synthetic frames, which are then
scored exactly (bdc26.realism, the scorer's own protocol) against the HELD-OUT proxies (default 4-5). Cells: BEV squares
of --bev metres, optionally split into z bands (--z edges). A cell without synthetic points cannot be corrected; its
real share stays unmatched. No real point enters the frames: the frames lose points, nothing is added or moved.

    python common/tools/s10_thinning_bound.py v2x model-v2x-track/routed-c0/submissions/2026-11-07_c0/submission.zip --bev 10
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
from bdc26 import realism  # noqa: E402
from _common import load_track  # noqa: E402
from score_realism import load_frames  # noqa: E402


def cell_index(P, bev, z_edges):
    ix = np.floor((P[:, 0] + 40) / bev).astype(int).clip(0, int(80 / bev) - 1)
    iy = np.floor((P[:, 1] + 40) / bev).astype(int).clip(0, int(80 / bev) - 1)
    k = ix * int(80 / bev) + iy
    if z_edges:
        iz = np.clip(np.digitize(P[:, 2], z_edges) - 1, 0, len(z_edges) - 2)
        k = k * (len(z_edges) - 1) + iz
    return k


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", choices=["v2x", "lumpi"])
    ap.add_argument("syn")
    ap.add_argument("--fit", nargs="+", default=["pcdet/realism-proxy-1", "pcdet/realism-proxy-2", "pcdet/realism-proxy-3"])
    ap.add_argument("--held", nargs="+", default=["pcdet/realism-proxy-4", "pcdet/realism-proxy-5"])
    ap.add_argument("--bev", type=float, default=10.0)
    ap.add_argument("--z", type=float, nargs="*", default=None, help="z band edges (masked range ends included)")
    ap.add_argument("--cap", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    t = load_track(a.track)
    box = realism.RANGES[t.name]
    syn = load_frames(t, a.syn)
    S_all = realism.concat_and_mask(syn, box)
    ncell = int(80 / a.bev) ** 2 * ((len(a.z) - 1) if a.z else 1)
    ks = cell_index(S_all, a.bev, a.z)
    ms = np.bincount(ks, minlength=ncell) / len(ks)
    mr = np.zeros(ncell)
    for f in a.fit:
        R_all = realism.concat_and_mask(load_frames(t, f), box)
        mr += np.bincount(cell_index(R_all, a.bev, a.z), minlength=ncell) / len(R_all) / len(a.fit)
    w = np.where(ms > 0, np.minimum(mr / np.maximum(ms, 1e-12), a.cap), 0.0)
    keep = w / w.max()
    unmatched = float(mr[ms == 0].sum())
    # thin each frame with the same per-cell probability; points outside the mask are kept as they are (never scored)
    rng = np.random.default_rng(a.seed)
    thinned = []
    for c in syn:
        c = np.asarray(c)[:, :3]
        x0, y0, z0, x1, y1, z1 = box
        inside = (c[:, 0] >= x0) & (c[:, 0] <= x1) & (c[:, 1] >= y0) & (c[:, 1] <= y1) & (c[:, 2] >= z0) & (c[:, 2] <= z1)
        p = np.ones(len(c))
        p[inside] = keep[cell_index(c[inside], a.bev, a.z)]
        thinned.append(c[rng.random(len(c)) < p])
    out = {"track": a.track, "syn": a.syn, "bev": a.bev, "z": a.z, "cap": a.cap, "kept_share": float(sum(len(c) for c in thinned) / sum(len(c) for c in syn)),
           "unmatched_real_share": unmatched, "held": {}}
    for h in a.held:
        ref = load_frames(t, h)
        base = realism.score(syn, ref, t.name, exact_emd=True)
        new = realism.score(thinned, ref, t.name, exact_emd=True)
        out["held"][h] = {k: {"CD": r["CD"], "EMD": r["EMD"], "FPD": r["FPD"], "MMD": r["MMD"], "R": r["R"]} for k, r in (("base", base), ("thinned", new))}
        print(h, f"R {base['R']:.4f} -> {new['R']:.4f} | EMD {base['EMD']:.3f} -> {new['EMD']:.3f} | FPD {base['FPD']:.3f} -> {new['FPD']:.3f} | CD {base['CD']:.3f} -> {new['CD']:.3f}", flush=True)
    print(json.dumps({k: v for k, v in out.items() if k != "held"}))


if __name__ == "__main__":
    main()
