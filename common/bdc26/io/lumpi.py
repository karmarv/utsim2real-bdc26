"""Real LUMPI readers (CC BY-NC 3.0; see data-lumpi-track/README.md before downloading).

- Frames: binary little-endian PLY, one merged cloud of all scanners per 10 Hz frame, fields
  x, y, z (float, local frame), time (uint, us), id (uchar, session id of the scanner), intensity (uchar),
  ray (uchar, beam index), azimuth (ushort, 0.01 deg), distance (ushort, metres * 200).
- Labels: one Label.csv per measurement: time[s], object id, BEV rect tl.x, tl.y, width, height, score,
  class_id, visibility (cumulative points), x, y, z, length, width, height, heading[rad]. frame = floor(time*10).
  score == 4 marks manually corrected rows.
- meta.json: session[sid] = {extrinsic 4x4 (sensor -> offset frame), angles (JSON string, degrees),
  deviceId, experimentId, horizontal_resolution, fps}. Local frame = offset frame - track.real.frame_offset.
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import Track
from ..guard import ForbiddenGuard

PLY_TYPES = {"char": "i1", "uchar": "u1", "short": "<i2", "ushort": "<u2", "int": "<i4", "uint": "<u4",
             "float": "<f4", "double": "<f8", "int8": "i1", "uint8": "u1", "int16": "<i2", "uint16": "<u2",
             "int32": "<i4", "uint32": "<u4", "float32": "<f4", "float64": "<f8"}


def read_ply(src) -> np.ndarray:
    """Structured array with the PLY vertex properties. `src` is a path, bytes or a binary file."""
    if isinstance(src, (str, Path)):
        data = Path(src).read_bytes()
    elif isinstance(src, (bytes, bytearray)):
        data = bytes(src)
    else:
        data = src.read()
    end = data.index(b"end_header\n") + len(b"end_header\n")
    header = data[:end].decode("ascii").splitlines()
    if "format binary_little_endian 1.0" not in header:
        raise ValueError("only binary_little_endian PLY is supported")
    n, fields = 0, []
    for line in header:
        tok = line.split()
        if tok[:2] == ["element", "vertex"]:
            n = int(tok[2])
        elif tok and tok[0] == "property" and len(tok) == 3:
            fields.append((tok[2], PLY_TYPES[tok[1]]))
    return np.frombuffer(data, dtype=np.dtype(fields), count=n, offset=end)


def ply_xyz(v: np.ndarray) -> np.ndarray:
    return np.stack([v["x"], v["y"], v["z"]], axis=1).astype(np.float32)


@dataclass
class LumpiLabels:
    frame: np.ndarray       # (M,) int
    boxes: np.ndarray       # (M, 7) x, y, z, l, w, h, heading
    class_id: np.ndarray    # (M,) int
    object_id: np.ndarray   # (M,) int
    score: np.ndarray       # (M,) int (4 = manually corrected)
    visibility: np.ndarray  # (M,) cumulative points


def read_labels_guarded(csv_path: Path, measurement: str, guard: ForbiddenGuard, purpose: str) -> LumpiLabels:
    """Parse Label.csv and drop every row of a blocked frame before anything else sees it."""
    lines = [l for l in Path(csv_path).read_text().splitlines() if l.strip()]
    if lines:
        try:
            float(lines[0].split(",", 1)[0])
        except ValueError:                  # header row
            lines = lines[1:]
    arr = np.array([[float(v) for v in l.split(",")[:16]] for l in lines], dtype=np.float64).reshape(-1, 16)
    frame = np.floor(arr[:, 0] * 10 + 1e-6).astype(np.int64)
    uniq = np.unique(frame)
    allowed = {f for _, f in guard.filter([(measurement, int(f)) for f in uniq], purpose)}
    keep = np.isin(frame, list(allowed))
    a, frame = arr[keep], frame[keep]
    return LumpiLabels(frame=frame, boxes=a[:, [9, 10, 11, 12, 13, 14, 15]], class_id=a[:, 7].astype(np.int64),
                       object_id=a[:, 1].astype(np.int64), score=a[:, 6].astype(np.int64),
                       visibility=a[:, 8])


@dataclass
class LumpiSession:
    session_id: int
    device_id: int
    experiment_id: int
    extrinsic_local: np.ndarray   # 4x4 sensor -> local track frame
    elevation_deg: np.ndarray     # per-beam elevation table from meta.json
    horizontal_resolution: float


def read_sessions(meta_path: Path, track: Track, experiment: int) -> dict[int, LumpiSession]:
    meta = json.loads(Path(meta_path).read_text())
    off = np.array(track["real"]["frame_offset"], dtype=np.float64)
    out = {}
    for sid, s in meta["session"].items():
        if int(s.get("experimentId", -1)) != int(experiment) or s.get("type") != "lidar":
            continue
        T = np.array(s["extrinsic"], dtype=np.float64)
        T[:3, 3] -= off
        ang = s.get("angles")
        ang = json.loads(ang) if isinstance(ang, str) else (ang or [])
        out[int(sid)] = LumpiSession(int(sid), int(s["deviceId"]), int(s["experimentId"]), T,
                                     np.array(ang, dtype=np.float64), float(s.get("horizontal_resolution", np.nan)))
    return out


def lidar_member(measurement: str, frame: int) -> str:
    return f"lidar/{frame:06d}.ply"
