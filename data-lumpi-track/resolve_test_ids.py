#!/usr/bin/env python
"""Verify that the challenge's LUMPI frame IDs are Measurement4 frame indices (so the guard blocks the right frames).

For --n test IDs, stream the raw Measurement4 PLY with the same index and check that (nearly) every test point
is an exact raw point. This reads the raw point clouds of those forbidden frames ONLY to confirm what to block
(logged with purpose "id-resolution"); no label is read and nothing is fitted.
Writes $BDC_DATA/lumpi-track/kit/id_check.json.

    python resolve_test_ids.py --accept-licence --n 2
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.config import load_track  # noqa: E402
from bdc26.guard import ForbiddenGuard  # noqa: E402
from bdc26.io import fetch, kit, lumpi  # noqa: E402

T = load_track("lumpi-track")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--accept-licence", action="store_true", required=True)
    ap.add_argument("--n", type=int, default=2)
    a = ap.parse_args()
    meas = T["guard"]["test_id_measurement"]
    vault = T["real"]["vault"]
    parts = []
    for i in range(1, T["real"]["lidar_parts"][meas] + 1):
        res = fetch.static_resolver(f"{vault}{meas}/lidar.zip.{i:03d}")
        parts.append((res, fetch.remote_size(res)))
    zf = fetch.open_zip(parts, buffer=1 << 20)
    g = ForbiddenGuard(T)
    rng = np.random.default_rng(0)
    results = []
    for fid in kit.test_ids(T)[: a.n]:
        g._log([(meas, int(fid))], "id-resolution (raw point cloud only, no labels)")
        raw = lumpi.ply_xyz(lumpi.read_ply(zf.read(f"lidar/{int(fid):06d}.ply")))
        tp = kit.read_test_frame(T, fid)[:, :3]
        sample = tp[rng.choice(len(tp), min(500, len(tp)), replace=False)]
        d, _ = cKDTree(raw).query(sample, k=1)
        results.append({"id": fid, "exact_match_fraction": float((d < 1e-4).mean()), "median_nn_m": float(np.median(d))})
    ok = all(r["exact_match_fraction"] > 0.95 for r in results)
    out = {"measurement": meas, "ids_are_frame_indices": ok, "checks": results,
           "blocked_window": T["guard"]["blocked_windows"][meas]}
    (T.kit / "id_check.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    if not ok:
        sys.exit("test IDs do NOT match Measurement4 frame indices: stop and investigate before using real data")


if __name__ == "__main__":
    main()
