#!/usr/bin/env python
"""Build the real V2X validation set and realism proxy sets from guard-allowed agent -1 frames (module M5.1, M5.4).

Never used for training. Frames: every frame with a local .bin + .yaml that the ForbiddenGuard allows (the
+/-20-frame buffer around forbidden frames is applied), subsampled with --stride.
Conversion (the organizers' protocol for real frames): mask to the range, resample to exactly 50,000 points
KEEPING the (0,0,0) null returns; labels to the sensor frame (OpenCOOD x1_to_x2), official super-class map,
unmapped types dropped, box centres in range.
Output ($BDC_DATA/v2x-track/pcdet/):
  realval-v1/            points/, labels/, ImageSets/val.txt (realval-A: decisions), ImageSets/valB.txt
                         (realval-B: weekly confirmation), dataset.yaml. Split by scenario (no shared sequences).
  realism-proxy-{1..5}/  points/ of 50 disjoint legal frames each (score_realism.py --ref)

    python prepare_realval.py --stride 5
"""
import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.boxes import boxes_center_in_range  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from bdc26.frames import resample  # noqa: E402
from bdc26.guard import ForbiddenGuard  # noqa: E402
from bdc26.io import v2x  # noqa: E402
from bdc26.pcdet_export import write_card, write_frame, write_splits  # noqa: E402

T = load_track("v2x-track")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="realval-v1")
    ap.add_argument("--stride", type=int, default=5)
    ap.add_argument("--b-fraction", type=float, default=0.3, help="share of scenarios held out as realval-B")
    ap.add_argument("--proxy-sets", type=int, default=5)
    a = ap.parse_args()
    guard = ForbiddenGuard(T)
    if not guard.resolved:
        sys.exit("kit/id_mapping.json missing: run ingest_kit.py and resolve_test_ids.py first")
    agent = T["real"]["agent"]
    pairs = sorted((p.parts[-3], int(p.stem), p) for p in (T.real / "raw").glob(f"*/*/{agent}/*.yaml")
                   if p.with_suffix(".bin").exists())
    pairs = [x for x in pairs if x[1] % a.stride == 0]
    allowed = set(guard.filter([(s, f) for s, f, _ in pairs], purpose=f"build {a.name}"))
    pairs = [x for x in pairs if (x[0], x[1]) in allowed]
    out = T.pcdet / a.name
    rng = np.random.default_rng(1234)
    ids_a, ids_b, all_ids = [], [], []
    for scen, frame, yml in pairs:
        pts = v2x.read_bin(yml.with_suffix(".bin"))[:, :3]
        lab = v2x.labels_in_sensor_frame(v2x.read_yaml(yml), T)
        keep = (lab.names != "") & boxes_center_in_range(lab.boxes, T.pc_range)
        fid = f"{scen}__{frame:06d}"
        write_frame(out, fid, resample(pts, T.n_points, rng, T.pc_range), lab.boxes[keep], lab.names[keep])
        in_b = int(hashlib.md5(scen.encode()).hexdigest(), 16) % 1000 < a.b_fraction * 1000
        (ids_b if in_b else ids_a).append(fid)
        all_ids.append(fid)
    write_splits(out, {"val": ids_a, "valB": ids_b})
    write_card(out, {"track": T.name, "source": "V2X-Real agent -1 (guard-allowed, labels)", "stride": a.stride,
                     "n_realval_A": len(ids_a), "n_realval_B": len(ids_b), "resample": T["resample"],
                     "class_map": "SUPER_CLASS_MAP (track.yaml)", "use": "validation only; never train on it"})
    perm = rng.permutation(len(all_ids))
    for k in range(a.proxy_sets):
        chosen = [all_ids[i] for i in perm[k * 50:(k + 1) * 50]]
        if len(chosen) < 50:
            break
        pdir = T.pcdet / f"realism-proxy-{k + 1}" / "points"
        pdir.mkdir(parents=True, exist_ok=True)
        for fid in chosen:
            (pdir / f"{fid}.npy").write_bytes((out / "points" / f"{fid}.npy").read_bytes())
    print(f"{len(all_ids)} frames -> {out} (A {len(ids_a)}, B {len(ids_b)}); {a.proxy_sets} realism proxy sets")


if __name__ == "__main__":
    main()
