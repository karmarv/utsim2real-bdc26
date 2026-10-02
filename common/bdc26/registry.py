"""Experiment registry: one CSV row per training run, evaluation or submission, per track.

Location: model-<track>/registry.csv (tracked in git; small). It is the source of the report's ablation
tables, so record every run, including failed ideas.
"""
from __future__ import annotations

import csv
import time
from pathlib import Path

from .config import Track
from .pcdet_export import git_sha

FIELDS = ["time", "kind", "model", "run", "git_sha", "data_version", "config", "seed", "metric_source",
          "mAP_3d_0.5_R40", "per_class", "realism_R", "codabench_id", "leaderboard_combined", "notes"]


def append(track: Track, **row) -> Path:
    path = track.model_dir / "registry.csv"
    new = not path.exists()
    row = {"time": time.strftime("%Y-%m-%d %H:%M"), "git_sha": git_sha(), **row}
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)
    return path
