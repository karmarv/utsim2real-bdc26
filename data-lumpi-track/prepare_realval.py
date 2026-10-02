#!/usr/bin/env python
"""Build the real LUMPI validation set and realism proxy sets from guard-allowed frames (module M5.1, M5.4).

Never used for training. Inputs (fetch_real.py): guarded Label.csv files and raw PLY frames of
Measurement4 (below the blocked window) and Measurements 5-6 (all five sensors; M0-M3 have only three).
Conversion (the organizers' protocol): all scanners merged, mask to the range, resample to exactly 50,000 points;
labels mapped with track.yaml real.class_id_to_track (HYPOTHESIS: LUMPI id 6 "unknown" = challenge "Van";
check class_report.json), box centres in range.
Output ($BDC_DATA/lumpi-track/pcdet/):
  realval-v1/            points/, labels/, ImageSets/val.txt (realval-A = Measurement4), ImageSets/valB.txt
                         (realval-B = Measurements 5-6), dataset.yaml, class_report.json
  realism-proxy-{1..5}/  points/ of 50 disjoint legal Measurement4 frames each (score_realism.py --ref)

    python prepare_realval.py
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.boxes import boxes_center_in_range, count_points_in_boxes  # noqa: E402
from bdc26.classmap import map_lumpi_ids  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from bdc26.frames import resample  # noqa: E402
from bdc26.guard import ForbiddenGuard  # noqa: E402
from bdc26.io import lumpi  # noqa: E402
from bdc26.pcdet_export import write_card, write_frame, write_splits  # noqa: E402

T = load_track("lumpi-track")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="realval-v1")
    ap.add_argument("--proxy-sets", type=int, default=5)
    a = ap.parse_args()
    guard = ForbiddenGuard.for_track(T)
    out = T.pcdet / a.name
    rng = np.random.default_rng(1234)
    splits = {"val": [], "valB": []}
    report = defaultdict(lambda: {"n": 0, "dims": [], "manual": 0, "pts": []})
    for meas in T["real"]["measurements_all_sensors"]:
        csv = T.real / "labels" / f"{meas}_Label.guarded.csv"
        frames_dir = T.real / "raw" / meas / "lidar"
        if not csv.exists() or not frames_dir.exists():
            print(f"skip {meas}: missing {csv.name} or {frames_dir}")
            continue
        lab = lumpi.read_labels_guarded(csv, meas, guard, purpose=f"build {a.name}")
        local = sorted(int(p.stem) for p in frames_dir.glob("*.ply"))
        for _, f in guard.filter([(meas, f) for f in local], purpose=f"build {a.name}"):
            m = lab.frame == f
            if not m.any():
                continue
            pts = lumpi.ply_xyz(lumpi.read_ply(frames_dir / f"{f:06d}.ply"))
            boxes, cls = lab.boxes[m], lab.class_id[m]
            names = map_lumpi_ids(cls, T)
            keep = (names != "") & boxes_center_in_range(boxes, T.pc_range)
            sampled = resample(pts, T.n_points, rng, T.pc_range)
            fid = f"{meas}__{f:06d}"
            write_frame(out, fid, sampled, boxes[keep], names[keep])
            splits["val" if meas == T["guard"]["test_id_measurement"] else "valB"].append(fid)
            npts = count_points_in_boxes(sampled, boxes[keep])
            for c, b, s, n in zip(cls[keep], boxes[keep], lab.score[m][keep], npts):
                r = report[int(c)]
                r["n"] += 1
                r["dims"].append(b[3:6])
                r["manual"] += int(s == 4)
                r["pts"].append(int(n))
    write_splits(out, splits)
    rep = {str(c): {"track_class": T["real"]["class_id_to_track"].get(c), "sdk_name": T["real"]["sdk_class_names"].get(c),
                    "n_boxes": r["n"], "median_lwh": np.median(r["dims"], 0).round(2).tolist() if r["dims"] else None,
                    "manual_fraction": r["manual"] / max(r["n"], 1), "median_points_at_50k": float(np.median(r["pts"])) if r["pts"] else None}
           for c, r in sorted(report.items())}
    (out / "class_report.json").write_text(json.dumps(rep, indent=2))
    write_card(out, {"track": T.name, "source": "real LUMPI (guard-allowed, labels)", "n_realval_A": len(splits["val"]),
                     "n_realval_B": len(splits["valB"]), "resample": T["resample"],
                     "class_map": "track.yaml real.class_id_to_track (verify with class_report.json)",
                     "use": "validation only; never train on it"})
    pool = splits["val"]
    perm = rng.permutation(len(pool))
    for k in range(a.proxy_sets):
        chosen = [pool[i] for i in perm[k * 50:(k + 1) * 50]]
        if len(chosen) < 50:
            break
        pdir = T.pcdet / f"realism-proxy-{k + 1}" / "points"
        pdir.mkdir(parents=True, exist_ok=True)
        for fid in chosen:
            (pdir / f"{fid}.npy").write_bytes((out / "points" / f"{fid}.npy").read_bytes())
    print(f"A {len(splits['val'])} / B {len(splits['valB'])} frames -> {out}; class report: {out / 'class_report.json'}")
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
