#!/usr/bin/env python
"""S9 engine v6 scalar calibrations (docs/decisions/2026-11-02-s9-clean-twin-plan.md). Writes small JSON files that the
generator reads instead of real label rows:

    python common/tools/s9_calibrate.py scalars --track lumpi     # gen/walker_scalars_v6.json, gen/size_scalars_v6.json
    python common/tools/s9_calibrate.py bowl --track lumpi --syn pcdet/g1-v4 --out gen/ground_bowl_v1.json

scalars: from the legal label summaries already on disk (gen/person_prior_m4.npz or gen/walker_prior_v1.npz, and
gen/size_prior_g2.npz): walker box mixture, range histogram, 19 size quantiles per dimension and class.
bowl: the 5-constant ground surface (bdc26.render.v6.GroundBowl) from per-cell 5th-percentile ground heights of
legal unlabeled realval frames (the split minus every realism proxy, through the guard, as fit_density_prior.py)
against the synthetic corpus's training frames.
"""
import argparse
import json
import re

import numpy as np

from _common import data_path, load_track
from bdc26.guard import ForbiddenGuard
from bdc26.render import v6


def scalars(t):
    prior = t.gen / ("person_prior_m4.npz" if t.name.startswith("lumpi") else "walker_prior_v1.npz")
    d = np.load(prior)
    if t.name.startswith("lumpi"):
        from bdc26.io import lumpi
        sess = lumpi.read_sessions(t.real / "raw" / "meta.json", t, experiment=4)
        sxy = [tuple(np.asarray(s.extrinsic_local)[:2, 3]) for _, s in sorted(sess.items())]
    else:
        sxy = [(0.0, 0.0)]                                   # V2X frames are in the sensor frame
    ws = v6.walker_scalars(d["lwh"], d["xy"], sensors_xy=sxy)
    ws["source"] = f"summary of {prior.name} (legal label rows; only these scalars reach the generator)"
    (t.gen / "walker_scalars_v6.json").write_text(json.dumps(ws, indent=1))
    sz = np.load(t.gen / "size_prior_g2.npz")
    ss = v6.size_scalars({k: sz[k] for k in sz.files})
    ss["source"] = "19 quantiles per dimension of gen/size_prior_g2.npz (legal realval label sizes)"
    (t.gen / "size_scalars_v6.json").write_text(json.dumps(ss, indent=1))
    print(json.dumps({"walkers": {k: ws[k] for k in ("boxes", "range_share")}, "size_classes": [k for k in ss if k != "source"]}))


def bowl(t, syn_rel, out, n=400):
    rroot, sroot = data_path(t, "pcdet/realval-v1"), data_path(t, syn_rel)
    proxies = set()
    for d in t.pcdet.glob("realism-proxy-*"):
        proxies |= {f.stem for f in (d / "points").glob("*.npy")}
    rids = [i for i in (rroot / "ImageSets" / "val.txt").read_text().split() if i not in proxies]
    rids = rids[:: max(1, len(rids) // n)][:n]
    keys = []
    for i in rids:
        m = re.match(r"(.+)__(\d+)$", i)
        keys.append((m.group(1), int(m.group(2))) if m else (i, 0))
    allowed = set(ForbiddenGuard.for_track(t, quiet=True).filter(keys, purpose=f"S9 ground bowl fit ({out})"))
    rids = [i for i, k in zip(rids, keys) if k in allowed]
    sids = (sroot / "ImageSets" / "train.txt").read_text().split()
    sids = sids[:: max(1, len(sids) // n)][:n]
    real = v6.cell_ground([np.load(rroot / "points" / f"{i}.npy") for i in rids])
    syn = v6.cell_ground([np.load(sroot / "points" / f"{i}.npy") for i in sids])
    b, st = v6.fit_bowl(real, syn)
    b.save(t.root / out, {"real": f"pcdet/realval-v1:val minus realism proxies ({len(rids)} frames, guard-filtered)",
                          "syn": f"{syn_rel}:train ({len(sids)} frames)", "form": "a + b x + c y + d r + e r^2", **st})
    print(json.dumps({"coef": b.coef.round(6).tolist(), **st}))
    for r0, r1 in ((0, 10), (10, 20), (20, 30), (30, 40), (40, 57)):
        a = np.deg2rad(np.arange(0, 360, 15))
        rr = (r0 + r1) / 2
        print(f"  r {r0:2d}-{r1:2d} m: mean offset {b.offset(rr * np.cos(a), rr * np.sin(a)).mean():+.3f} m")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["scalars", "bowl"])
    ap.add_argument("--track", required=True)
    ap.add_argument("--syn", default="pcdet/g1-v4")
    ap.add_argument("--out", default="gen/ground_bowl_v1.json")
    a = ap.parse_args()
    t = load_track(a.track)
    scalars(t) if a.what == "scalars" else bowl(t, a.syn, a.out)
