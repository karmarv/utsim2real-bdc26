"""Write OpenPCDet `CustomDataset` layouts from canonical frames.

    <out>/points/<fid>.npy       float32 (N, 3) xyz in the track frame (nulls stripped for detection)
    <out>/labels/<fid>.txt       one box per line: "x y z dx dy dz heading ClassName"
    <out>/ImageSets/{train,val}.txt
    <out>/dataset.yaml           provenance card (source, transforms, counts, git sha)

Coordinates are stored as float32, never float16 (3 cm quantization at 32-64 m).
"""
from __future__ import annotations

import subprocess
import time
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from .config import REPO


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def write_frame(out: Path, fid: str, points: np.ndarray, boxes: np.ndarray, names) -> None:
    (out / "points").mkdir(parents=True, exist_ok=True)
    (out / "labels").mkdir(parents=True, exist_ok=True)
    np.save(out / "points" / f"{fid}.npy", np.ascontiguousarray(points[:, :3], dtype=np.float32))
    lines = [" ".join(f"{v:.4f}" for v in b) + f" {n}" for b, n in zip(np.asarray(boxes).reshape(-1, 7), names)]
    (out / "labels" / f"{fid}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))


def write_splits(out: Path, splits: dict[str, list[str]]) -> None:
    (out / "ImageSets").mkdir(parents=True, exist_ok=True)
    for name, ids in splits.items():
        (out / "ImageSets" / f"{name}.txt").write_text("\n".join(ids) + "\n")


def write_card(out: Path, card: dict) -> None:
    labels = Counter()
    for f in (out / "labels").glob("*.txt"):
        labels.update(l.rsplit(" ", 1)[-1] for l in f.read_text().splitlines() if l.strip())
    card = {**card, "created": time.strftime("%Y-%m-%d %H:%M"), "git_sha": git_sha(),
            "n_frames": len(list((out / "points").glob("*.npy"))), "boxes_per_class": dict(labels)}
    (out / "dataset.yaml").write_text(yaml.safe_dump(card, sort_keys=False))


def read_labels_txt(path: Path) -> tuple[np.ndarray, np.ndarray]:
    rows = [l.split() for l in Path(path).read_text().splitlines() if l.strip()]
    if not rows:
        return np.zeros((0, 7)), np.array([], dtype=object)
    return np.array([[float(v) for v in r[:7]] for r in rows]), np.array([r[7] for r in rows], dtype=object)
