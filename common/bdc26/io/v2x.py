"""Real V2X-Real readers (UCLA academic licence; see data-v2x-track/README.md before downloading).

- `<split>/<scenario>/<agent>/<frame>.bin`: float32 (N, 4) x, y, z, intensity in the agent's sensor
  frame. Agent -1 (Ouster OS1-64) is organized 64 x 1024, row 0 = top beam; no-return points are
  xyz = (0, 0, 0) with a non-zero intensity.
- `<frame>.yaml` (OPV2V format): lidar_pose [x, y, z, roll, yaw, pitch] (deg, world); vehicles{id: {
  location (world box centre), center (offset), extent (HALF sizes), angle [roll, yaw, pitch] (deg, world),
  obj_type, attribute}}.
Boxes are converted exactly as OpenCOOD does (x1_to_x2 of object pose into the lidar pose), keeping yaw only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from ..config import Track
from ..classmap import v2x_super_class


def read_bin(src) -> np.ndarray:
    buf = Path(src).read_bytes() if isinstance(src, (str, Path)) else bytes(src)
    return np.frombuffer(buf, dtype=np.float32).reshape(-1, 4)


def x_to_world(pose) -> np.ndarray:
    """OpenCOOD transformation_utils.x_to_world: pose = [x, y, z, roll, yaw, pitch] in degrees."""
    x, y, z, roll, yaw, pitch = [float(v) for v in pose]
    cy, sy = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    cr, sr = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    cp, sp = np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
    m = np.eye(4)
    m[0, 3], m[1, 3], m[2, 3] = x, y, z
    m[0, 0] = cp * cy
    m[0, 1] = cy * sp * sr - sy * cr
    m[0, 2] = -cy * sp * cr - sy * sr
    m[1, 0] = sy * cp
    m[1, 1] = sy * sp * sr + cy * cr
    m[1, 2] = -sy * sp * cr + cy * sr
    m[2, 0] = sp
    m[2, 1] = -cp * sr
    m[2, 2] = cp * cr
    return m


def x1_to_x2(x1, x2) -> np.ndarray:
    return np.linalg.inv(x_to_world(x2)) @ x_to_world(x1)


@dataclass
class V2XLabels:
    boxes: np.ndarray      # (M, 7) sensor frame
    names: np.ndarray      # (M,) challenge super-class ('' = dropped type)
    obj_types: np.ndarray  # (M,) raw obj_type
    static: np.ndarray     # (M,) bool, attribute == 'static'


def read_yaml(src) -> dict:
    text = Path(src).read_text() if isinstance(src, (str, Path)) else src.decode()
    return yaml.safe_load(text)


def labels_in_sensor_frame(y: dict, track: Track) -> V2XLabels:
    lidar_pose = y["lidar_pose"]
    boxes, names, types, static = [], [], [], []
    for obj in (y.get("vehicles") or {}).values():
        loc, ctr, ang, ext = obj["location"], obj.get("center", [0, 0, 0]), obj["angle"], obj["extent"]
        pose = [loc[0] + ctr[0], loc[1] + ctr[1], loc[2] + ctr[2], ang[0], ang[1], ang[2]]
        T = x1_to_x2(pose, lidar_pose)
        c = T[:3, 3]
        yaw = np.arctan2(T[1, 0], T[0, 0])
        boxes.append([c[0], c[1], c[2], 2 * ext[0], 2 * ext[1], 2 * ext[2], yaw])
        t = str(obj.get("obj_type", ""))
        types.append(t)
        names.append(v2x_super_class(t, track))
        static.append(str(obj.get("attribute", "")) == "static")
    return V2XLabels(np.array(boxes, dtype=np.float64).reshape(-1, 7), np.array(names, dtype=object),
                     np.array(types, dtype=object), np.array(static, dtype=bool))


def member_names(split: str, scenario: str, agent: str, frame: int) -> tuple[str, str]:
    base = f"{split}/{scenario}/{agent}/{frame:06d}"
    return base + ".bin", base + ".yaml"
