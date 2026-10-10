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

FIELDS = ["time", "kind", "model", "strategy", "run", "git_sha", "data_version", "config", "seed", "metric_source",
          "mAP_3d_0.5_R40", "per_class", "realism_R", "codabench_id", "leaderboard_combined", "notes"]


def model_strategy(track: Track, model: str | None) -> str:
    """The `strategy` field of model-<track>/<model>/model.yaml ('' when absent)."""
    if not model:
        return ""
    card = track.model_dir / model / "model.yaml"
    if not card.exists():
        return ""
    import yaml
    return str((yaml.safe_load(card.read_text()) or {}).get("strategy", "") or "")


def migrate(path: Path, default_strategy=None) -> bool:
    """Rewrite an older registry.csv with the current FIELDS (new columns empty, or default_strategy(row) for
    `strategy`). Returns True when the file was rewritten."""
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        header, rows = r.fieldnames or [], list(r)
    if header == FIELDS:
        return False
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            if not row.get("strategy") and default_strategy is not None:
                row["strategy"] = default_strategy(row)
            w.writerow(row)
    return True


def append(track: Track, **row) -> Path:
    path = track.model_dir / "registry.csv"
    new = not path.exists()
    if not new:
        migrate(path, lambda r: model_strategy(track, r.get("model")))
    row = {"time": time.strftime("%Y-%m-%d %H:%M"), "git_sha": git_sha(), **row}
    tta = str(row.get("run", "")).endswith("_tta")             # a member's TTA variant belongs to S3 (its own folder may be S1)
    row.setdefault("strategy", "S3" if tta else model_strategy(track, row.get("model")))
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)
    return path
