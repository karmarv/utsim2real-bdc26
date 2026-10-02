#!/usr/bin/env python
"""Build an OpenPCDet training dataset from UT-LUMPI (module M4; engine G1 input).

Track-specific steps (see data-lumpi-track/README.md Section 8.4):
  - UT classes -> challenge classes (UT Van and Unknown -> Car by default; the challenge "Van" is probably
    LUMPI id 6 "unknown" objects, which UT does not contain).
  - Actor scale fix: every actor's points (by instance id) and box are scaled by 1/0.78 about the box bottom
    centre; background points left inside an enlarged object are removed. Without this, no UT-LUMPI box can
    reach 3D IoU 0.5 with a real box (0.78^3 = 0.47).
  - Resample to 50,000 points inside the range (the organizers' protocol for real LUMPI frames).
Output: $BDC_DATA/lumpi-track/pcdet/<name>/ (points/, labels/, ImageSets/{train,val}.txt, dataset.yaml).
Split: frames 0-8999 train, 9000-9999 val (contiguous, because UT is one sequence at 10 Hz).

    python prepare_ut.py --name ut-v1
    python prepare_ut.py --name ut-noscale-v1 --scale-fix 1.0     # ablation: the organizers' actor size
"""
import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from bdc26.config import load_track  # noqa: E402
from bdc26.pcdet_export import write_card, write_frame, write_splits  # noqa: E402
from bdc26.prep import UTConvertParams, convert_ut_frame  # noqa: E402

T = load_track("lumpi-track")


def work(args):
    idx, out, params = args
    pts, boxes, names, st = convert_ut_frame(T, idx, params)
    write_frame(out, f"{idx:06d}", pts, boxes, names)
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="ut-v1")
    ap.add_argument("--scale-fix", type=float, default=T["ut"]["actor_scale_fix"])
    ap.add_argument("--n-points", type=int, default=T.n_points)
    ap.add_argument("--min-points", type=int, default=1)
    ap.add_argument("--frames", type=int, default=T["ut"]["n_frames"], help="number of frames (smoke tests: fewer)")
    ap.add_argument("--stride", type=int, default=1, help="take every k-th frame (smoke tests across the sequence)")
    ap.add_argument("--val-from", type=int, default=9000)
    ap.add_argument("--workers", type=int, default=48)
    a = ap.parse_args()
    out = T.pcdet / a.name
    params = UTConvertParams(n_points=a.n_points, scale_fix=a.scale_fix, min_points=a.min_points)
    with Pool(a.workers) as pool:
        frames = list(range(0, T["ut"]["n_frames"], a.stride))[: a.frames]
        stats = pool.map(work, [(i, out, params) for i in frames], chunksize=16)
    ids = [f"{i:06d}" for i in frames]
    write_splits(out, {"train": [i for i in ids if int(i) < a.val_from], "val": [i for i in ids if int(i) >= a.val_from]})
    write_card(out, {"track": T.name, "source": "UT-LUMPI (doi:10.7910/DVN/D9SSWD, CC0)", "engine": "UT",
                     "params": vars(params), "class_map": T["ut"]["class_map"],
                     "mean_boxes_per_frame": sum(s["n_boxes"] for s in stats) / max(len(stats), 1),
                     "dropped_empty_boxes": sum(s["n_dropped_empty"] for s in stats)})
    print(f"wrote {len(ids)} frames to {out}")
