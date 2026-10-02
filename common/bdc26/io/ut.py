"""Organizer synthetic datasets (UT-LUMPI, UT-V2X-Real-IC): fetch and read.

Layout inside each split zip: `<zip_root>/{pcd,lbl,sem_seg,ins_seg}/000000..009999.{npy,txt,label,label}`.
- pcd/*.npy   float32 (N, 3) xyz, no intensity, in the track frame (UT-LUMPI: LUMPI Measurement4 local
              frame; UT-V2X: the V2X-Real agent -1 sensor frame).
- lbl/*.txt   one line per CARLA actor on the WHOLE map: `x y z dx dy dz heading Class actor_id`
              (OpenPCDet 7-DoF, z = box centre, heading CCW from +x). Crop to range and filter by points.
- sem_seg / ins_seg  uint32 per point (SemanticKITTI style); ins = CARLA actor id (matches lbl), 0 = background.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import Track
from . import fetch


@dataclass
class UTLabels:
    boxes: np.ndarray      # (M, 7) float64
    names: np.ndarray      # (M,) str, UT class names
    actor_ids: np.ndarray  # (M,) int64


def ut_dir(track: Track) -> Path:
    return track.ut / track["ut"]["zip_root"]


def read_points(track: Track, idx: int) -> np.ndarray:
    return np.load(ut_dir(track) / "pcd" / f"{idx:06d}.npy").astype(np.float32, copy=False)


def read_labels(track: Track, idx: int) -> UTLabels:
    rows = [l.split() for l in (ut_dir(track) / "lbl" / f"{idx:06d}.txt").read_text().splitlines() if l.strip()]
    if not rows:
        return UTLabels(np.zeros((0, 7)), np.array([], dtype=str), np.zeros(0, dtype=np.int64))
    boxes = np.array([[float(v) for v in r[:7]] for r in rows])
    names = np.array([r[7] for r in rows])
    ids = np.array([int(r[8]) if len(r) > 8 else -1 for r in rows], dtype=np.int64)
    return UTLabels(boxes, names, ids)


def read_instance_ids(track: Track, idx: int) -> np.ndarray | None:
    p = ut_dir(track) / "ins_seg" / f"{idx:06d}.label"
    return np.fromfile(p, dtype=np.uint32) if p.exists() else None


def fetch_ut(track: Track, members: list[str], workers: int = 24, keep_zips: bool = False,
             extract_workers: int = 8, log=print) -> None:
    """Download all zip parts in parallel (MD5-checked), then extract the requested member folders."""
    parts = fetch.dataverse_parts(track.repo_dir / track["ut"]["listing"])
    zip_dir = track.ut / "zip"
    total = sum(p["size"] for p in parts)
    log(f"[{track.name}] {len(parts)} parts, {total / 1e9:.1f} GB -> {zip_dir}")
    local = []
    for k, p in enumerate(parts, 1):
        log(f"[{track.name}] part {k}/{len(parts)} {p['filename']} ({p['size'] / 1e9:.2f} GB)")
        local.append(fetch.download(fetch.dataverse_resolver(p["id"]), zip_dir / p["filename"],
                                    size=p["size"], md5=p["md5"], workers=workers, log=log))
    root = track["ut"]["zip_root"]
    zf = fetch.open_zip(local)
    names = [n for n in zf.namelist() if any(n.startswith(f"{root}/{m}/") for m in members)]
    zf.close()
    log(f"[{track.name}] extracting {len(names)} files of {members}")
    fetch.extract_members(lambda: fetch.open_zip(local), names, track.ut, workers=extract_workers, log=log)
    if not keep_zips:
        for p in local:
            p.unlink()
        log(f"[{track.name}] deleted zip parts")


def check_ut(track: Track, members: list[str]) -> dict:
    """Counts per member folder; a complete dataset has n_frames files in each."""
    return {m: len(list((ut_dir(track) / m).glob("*"))) for m in members}
