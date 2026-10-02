"""CodaBench starting kit (download manually from each competition's Files tab; login required).

Expected contents: detection_test_frames/<id>.bin (float32 N x 3), detection_test_frame_ids.json,
forbidden_frames.txt, local_eval.py (+ scoring_program/), make_dummy_submission.py, submission_format.md,
declaration_template.pdf, reference_data_local/ (token frames only; a competitor found its realism_reference
byte-identical to the 50 test frames, so never fit anything to it).

The 50 test frames are forbidden frames: read them only to run inference and to check their format.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..config import Track


def test_ids(track: Track) -> list[str]:
    ids = json.loads((track.kit / "detection_test_frame_ids.json").read_text())
    return [str(i) for i in (ids["frame_ids"] if isinstance(ids, dict) and "frame_ids" in ids else ids)]


def test_frame_path(track: Track, fid: str) -> Path:
    d = track.kit / "detection_test_frames"
    for ext in (".bin", ".npy"):
        if (d / f"{fid}{ext}").exists():
            return d / f"{fid}{ext}"
    raise FileNotFoundError(f"no test frame {fid} in {d}")


def read_test_frame(track: Track, fid: str) -> np.ndarray:
    p = test_frame_path(track, fid)
    if p.suffix == ".npy":
        return np.load(p).astype(np.float32)
    a = np.fromfile(p, dtype=np.float32)
    return a.reshape(-1, 3) if a.size % 3 == 0 else a.reshape(-1, 4)


def config_json(track: Track) -> dict | None:
    for p in (track.kit / "reference_data" / "config.json", track.kit / "config.json",
              track.kit / "reference_data_dummy" / "config.json", track.kit / "reference_data_local" / "config.json"):
        if p.exists():
            return json.loads(p.read_text())
    return None


def ingest(track: Track, source: Path) -> dict:
    """Unpack a downloaded starting kit (zip or folder) into $BDC_DATA/<track>/kit and report its format.

    Only format-level statistics of the 50 test frames are computed (points, null fraction, extents); nothing
    is fitted to them. The report is written to kit/kit_report.json.
    """
    import shutil
    import zipfile

    from ..frames import frame_stats

    source = Path(source)
    track.kit.mkdir(parents=True, exist_ok=True)
    if source.is_file() and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as z:
            z.extractall(track.kit)
    elif source.is_dir() and source.resolve() != track.kit.resolve():
        shutil.copytree(source, track.kit, dirs_exist_ok=True)
    # flatten a single top-level folder (e.g. kit/starting_kit/...)
    entries = [p for p in track.kit.iterdir() if p.name not in ("kit_report.json", "id_mapping.json")]
    if len(entries) == 1 and entries[0].is_dir() and not (track.kit / "forbidden_frames.txt").exists():
        for p in entries[0].iterdir():
            shutil.move(str(p), str(track.kit / p.name))
        entries[0].rmdir()
    forb = [l.strip() for l in (track.kit / "forbidden_frames.txt").read_text().splitlines()
            if l.strip() and not l.lstrip().startswith("#")]
    ids = test_ids(track)
    stats = [frame_stats(read_test_frame(track, i), track.pc_range) for i in ids]
    report = {
        "n_forbidden": len(forb), "n_test_ids": len(ids), "test_ids_subset_of_forbidden": set(ids) <= set(forb),
        "files": sorted(str(p.relative_to(track.kit)) for p in track.kit.rglob("*") if p.is_file()
                        and "detection_test_frames" not in p.parts)[:200],
        "config_json": config_json(track),
        "test_frames": {
            "points_per_frame": [min(s["n_points"] for s in stats), max(s["n_points"] for s in stats)],
            "in_range_per_frame": [min(s["n_in_range"] for s in stats), max(s["n_in_range"] for s in stats)],
            "null_fraction_mean": float(np.mean([s["null_fraction"] for s in stats])),
            "z_p05_median": float(np.median([s["z_p05_p50"][0] for s in stats if s["z_p05_p50"]])),
            "n_columns": sorted({s["n_columns"] for s in stats}),
        },
        "warning": ("reference_data_local/realism_reference (older kits) duplicated the test frames: never fit anything to "
                    "any kit reference data" if (track.kit / "reference_data_local").exists() else
                    "kit reference data is a dummy for format checks only: never fit anything to it"),
    }
    (track.kit / "kit_report.json").write_text(json.dumps(report, indent=2, default=str))
    return report
