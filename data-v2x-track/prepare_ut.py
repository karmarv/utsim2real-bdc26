#!/usr/bin/env python
"""Build an OpenPCDet training dataset from UT-V2X-Real-IC (module M4; engine G1 input).

Track-specific steps (see data-v2x-track/README.md Sections 4 and 7):
  - UT classes -> super-classes (Car, Unknown -> vehicle; Van, Truck, Bus -> truck; riders -> pedestrian).
    UT has NO walking pedestrians and NO TrashCan objects: engine G1 inserts them.
  - Density: real OS1-64 frames are resampled by the organizers to 50,000 points INCLUDING about 31%
    (0,0,0) no-returns, i.e. about 35k valid points in range. UT-V2X emulates a wider, denser sensor
    (about 69k valid points in range), so UT frames are resampled to --n-valid points (default from
    track.yaml resample.n_valid_points; re-measure it on legal real frames in M5.3).
Output: $BDC_DATA/v2x-track/pcdet/<name>/ (points/, labels/, ImageSets/{train,val}.txt, dataset.yaml).
Split: frames 0-8999 train, 9000-9999 val (contiguous, because UT is one sequence).

    python prepare_ut.py --name ut-v1
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

T = load_track("v2x-track")


def work(args):
    idx, out, params = args
    pts, boxes, names, st = convert_ut_frame(T, idx, params)
    write_frame(out, f"{idx:06d}", pts, boxes, names)
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="ut-v1")
    ap.add_argument("--n-valid", type=int, default=T["resample"]["n_valid_points"])
    ap.add_argument("--min-points", type=int, default=1)
    ap.add_argument("--frames", type=int, default=T["ut"]["n_frames"], help="number of frames (smoke tests: fewer)")
    ap.add_argument("--stride", type=int, default=1, help="take every k-th frame (smoke tests across the sequence)")
    ap.add_argument("--val-from", type=int, default=9000)
    ap.add_argument("--workers", type=int, default=48)
    a = ap.parse_args()
    out = T.pcdet / a.name
    params = UTConvertParams(n_points=a.n_valid, scale_fix=T["ut"]["actor_scale_fix"], min_points=a.min_points)
    with Pool(a.workers) as pool:
        frames = list(range(0, T["ut"]["n_frames"], a.stride))[: a.frames]
        stats = pool.map(work, [(i, out, params) for i in frames], chunksize=16)
    ids = [f"{i:06d}" for i in frames]
    write_splits(out, {"train": [i for i in ids if int(i) < a.val_from], "val": [i for i in ids if int(i) >= a.val_from]})
    write_card(out, {"track": T.name, "source": "UT-V2X-Real-IC (doi:10.7910/DVN/N6N4UR, CC0)", "engine": "UT",
                     "params": vars(params), "class_map": T["ut"]["class_map"],
                     "mean_boxes_per_frame": sum(s["n_boxes"] for s in stats) / max(len(stats), 1),
                     "dropped_empty_boxes": sum(s["n_dropped_empty"] for s in stats)})
    print(f"wrote {len(ids)} frames to {out}")
