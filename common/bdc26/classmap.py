"""Class mapping from each source taxonomy to the track's challenge classes (config in track.yaml)."""
from __future__ import annotations

import numpy as np

from .config import Track


def map_ut(names, track: Track, class_map: dict | None = None) -> np.ndarray:
    """UT class names -> challenge class names; '' where the class is not mapped (dropped).

    class_map overrides track.yaml ut.class_map (dataset variants, e.g. the g1 map with UT Van -> Van)."""
    cmap = class_map if class_map is not None else track["ut"]["class_map"]
    return np.array([cmap.get(str(n), "") for n in names], dtype=object)


def map_lumpi_ids(class_ids, track: Track) -> np.ndarray:
    cmap = {int(k): v for k, v in track["real"]["class_id_to_track"].items()}
    return np.array([cmap.get(int(c), "") for c in class_ids], dtype=object)


def v2x_super_class(obj_type: str, track: Track) -> str:
    for sup, members in track["real"]["super_class_map"].items():
        if obj_type in members:
            return sup
    return ""
