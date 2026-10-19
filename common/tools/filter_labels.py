#!/usr/bin/env python
"""S7 (docs/02-STRATEGY.md Section 8.11): derive a dataset whose labels follow a per-class visibility rule.

The frames are the source dataset's (points/ is a symlink, ImageSets/ copied); only labels/ changes: a box of class c
is kept when at least min_points[c] points of its frame lie inside it (counted per box, null returns excluded,
bdc26.boxes.count_points_per_box). The thresholds come from legal real label statistics (S7 record), so the synthetic
labels drop the sparse objects the real annotators do not label. dataset.yaml records the source, the rule and the
removed counts.

    python common/tools/filter_labels.py --track v2x --src pcdet/g1-v5 --dst pcdet/g1-v5m \
        --min-points pedestrian=6 vehicle=8 truck=18
    # thresholds only: the per-class percentiles of points per label box of a labelled dataset (realval A and B)
    python common/tools/filter_labels.py --track v2x --src pcdet/realval-v1 --stats val valB
"""
import argparse
import os
import shutil
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import yaml

from _common import data_path, load_track
from bdc26.boxes import count_points_per_box
from bdc26.pcdet_export import git_sha, read_labels_txt


def _counts(job):
    root, fid = job
    b, names = read_labels_txt(root / "labels" / f"{fid}.txt")
    if not len(b):
        return fid, b, names, np.zeros(0, dtype=np.int64)
    return fid, b, names, count_points_per_box(np.load(root / "points" / f"{fid}.npy"), b)


def stats(root: Path, splits, workers: int) -> dict:
    ids = [i for s in splits for i in (root / "ImageSets" / f"{s}.txt").read_text().split()]
    per = {}
    with ProcessPoolExecutor(workers) as ex:
        for _, _, names, k in ex.map(_counts, [(root, i) for i in ids], chunksize=16):
            for n, v in zip(names, k):
                per.setdefault(str(n), []).append(int(v))
    return {c: {"n": len(v), **{f"p{q}": float(np.percentile(v, q)) for q in (1, 2, 5)},
                "share_below_6": float(np.mean(np.array(v) < 6))} for c, v in sorted(per.items())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", default=None)
    ap.add_argument("--min-points", nargs="*", default=[], help="class=k pairs")
    ap.add_argument("--stats", nargs="*", default=None, help="print per-class points-per-box percentiles of these splits")
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    track = load_track(a.track)
    src = data_path(track, a.src)
    if a.stats is not None:
        print(yaml.safe_dump(stats(src, a.stats or ["val", "valB"], a.workers), sort_keys=False))
        return
    if not a.dst or not a.min_points:
        raise SystemExit("--dst and --min-points are needed to write a dataset")
    rule = {k: int(v) for k, v in (s.split("=", 1) for s in a.min_points)}
    dst = data_path(track, a.dst)
    if dst.exists():
        raise SystemExit(f"{dst} exists; remove it first")
    (dst / "labels").mkdir(parents=True)
    os.symlink(src / "points", dst / "points")
    shutil.copytree(src / "ImageSets", dst / "ImageSets")
    ids = sorted({i for f in (src / "ImageSets").glob("*.txt") for i in f.read_text().split()})
    kept, removed = Counter(), Counter()
    with ProcessPoolExecutor(a.workers) as ex:
        for fid, b, names, k in ex.map(_counts, [(src, i) for i in ids], chunksize=16):
            lines = []
            for box, n, v in zip(b, names, k):
                if v < rule.get(str(n), 0):
                    removed[str(n)] += 1
                    continue
                kept[str(n)] += 1
                lines.append(" ".join(f"{x:.4f}" for x in box) + f" {n}")
            (dst / "labels" / f"{fid}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
    src_card = yaml.safe_load((src / "dataset.yaml").read_text()) if (src / "dataset.yaml").exists() else {}
    card = {**src_card, "derived_from": a.src, "label_rule": {"min_points_per_box": rule,
            "counting": "points inside each box, per box, (0,0,0) nulls excluded (bdc26.boxes.count_points_per_box)"},
            "label_rule_removed": dict(removed), "boxes_per_class": dict(kept), "n_frames": len(ids), "git_sha": git_sha(),
            "points": f"symlink to {a.src}/points (frames unchanged)"}
    (dst / "dataset.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
    print(yaml.safe_dump({"kept": dict(kept), "removed": dict(removed)}, sort_keys=False))


if __name__ == "__main__":
    main()
