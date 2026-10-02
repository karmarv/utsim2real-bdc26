"""Track configuration and data-root layout.

Every track-specific fact (ranges, classes, class maps, data sources, guard windows) lives in
`data-<track>/track.yaml`. Large data lives outside the repository under $BDC_DATA:

    $BDC_DATA/<track>/
        kit/        CodaBench starting kit (read-only; the 50 test frames are forbidden for fitting)
        ut/         organizer synthetic dataset (zip parts, then extracted pcd/lbl/sem_seg/ins_seg)
        real/       real dataset downloads (raw, read-only) and the real-data access log
        canon/      frames converted to the challenge convention (track frame, 50k points)
        pcdet/      OpenPCDet custom datasets built from canon/ (one folder per dataset version)
        gen/        generated corpora (engines G1/G2)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
TRACK_DIRS = {"lumpi-track": REPO / "data-lumpi-track", "v2x-track": REPO / "data-v2x-track"}
ALIASES = {"lumpi": "lumpi-track", "track1": "lumpi-track", "v2x": "v2x-track", "track2": "v2x-track"}


def data_root() -> Path:
    return Path(os.environ.get("BDC_DATA", REPO.parent / "bdc26-data")).expanduser()


@dataclass
class Track:
    name: str
    cfg: dict = field(repr=False)

    @property
    def root(self) -> Path: return data_root() / self.name
    @property
    def kit(self) -> Path: return self.root / "kit"
    @property
    def ut(self) -> Path: return self.root / "ut"
    @property
    def real(self) -> Path: return self.root / "real"
    @property
    def canon(self) -> Path: return self.root / "canon"
    @property
    def pcdet(self) -> Path: return self.root / "pcdet"
    @property
    def gen(self) -> Path: return self.root / "gen"
    @property
    def repo_dir(self) -> Path: return TRACK_DIRS[self.name]
    @property
    def model_dir(self) -> Path: return REPO / f"model-{self.name}"
    @property
    def pc_range(self) -> list[float]: return list(self.cfg["point_cloud_range"])
    @property
    def classes(self) -> list[str]: return list(self.cfg["classes"])
    @property
    def n_points(self) -> int: return int(self.cfg["resample"]["n_points"])

    def __getitem__(self, key):
        return self.cfg[key]


def load_track(name: str) -> Track:
    name = ALIASES.get(name, name)
    if name not in TRACK_DIRS:
        raise KeyError(f"unknown track {name!r}; expected one of {sorted(TRACK_DIRS)}")
    cfg = yaml.safe_load((TRACK_DIRS[name] / "track.yaml").read_text())
    assert cfg["track"] == name, f"track.yaml says {cfg['track']!r}, expected {name!r}"
    return Track(name, cfg)
