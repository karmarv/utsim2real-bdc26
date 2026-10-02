"""ForbiddenGuard: the single gate every real-data reader goes through.

The challenge forbids training, validating, tuning on, or observing ground truth of the 100 frames in
`forbidden_frames.txt`. On top of that we self-exclude near-duplicates:
  - LUMPI: all 100 forbidden IDs are Measurement4 frames 006497-008109, so the whole window
    Measurement4 [6400, 8199] is blocked (track.yaml guard.blocked_windows).
  - V2X-Real: IDs are "<scenario index>_<frame>"; the index -> scenario-folder mapping is resolved from
    the starting kit (data-v2x-track/resolve_test_ids.py -> kit/id_mapping.json). Every forbidden frame
    plus +/- buffer_frames in the same folder is blocked; an index mapped to a LIST of candidate folders is
    blocked in all of them, and "*" blocks the frame number in every folder. Without the mapping, V2X real data
    is refused.

Raw keys are (group, frame): group is the LUMPI measurement ("Measurement5") or the V2X-Real scenario
folder name ("2023-03-17-15-59-02_7_0"); frame is the integer frame index. Every allowed access is
appended to $BDC_DATA/<track>/real/access_log.csv with its purpose (kept for the challenge report).
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from .config import Track


class ForbiddenFrameError(PermissionError):
    pass


def read_forbidden_ids(track: Track) -> list[str]:
    p = track.kit / "forbidden_frames.txt"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing: download the starting kit and run data-{track.name}/ingest_kit.py")
    return [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]


class ForbiddenGuard:
    def __init__(self, track: Track, forbidden_ids: list[str] | None = None, id_mapping: dict | None = None,
                 log_path: Path | None = None):
        self.track = track
        self.forbidden_ids = set(forbidden_ids if forbidden_ids is not None else read_forbidden_ids(track))
        self.log_path = Path(log_path) if log_path else track.real / "access_log.csv"
        g = track["guard"]
        self.blocked: dict[str, list[tuple[int, int]]] = {}
        if track.name == "lumpi-track":
            for grp, (lo, hi) in g.get("blocked_windows", {}).items():
                self.blocked.setdefault(grp, []).append((int(lo), int(hi)))
            meas = g["test_id_measurement"]
            for fid in self.forbidden_ids:
                self.blocked.setdefault(meas, []).append((int(fid), int(fid)))
        else:
            if id_mapping is None:
                mp = track.kit / "id_mapping.json"
                id_mapping = json.loads(mp.read_text()) if mp.exists() else None
            self.id_mapping = id_mapping
            buf = int(g["buffer_frames"])
            if id_mapping is not None:
                for fid in self.forbidden_ids:
                    idx, frame = fid.split("_")
                    # an index that could not be resolved maps to "*": block that frame number in EVERY folder
                    folder = id_mapping.get(idx, "*")
                    # a list = candidate folders (monotone-subset bounds, resolve_test_ids.py): block in each
                    for fo in (folder if isinstance(folder, list) else [folder]):
                        self.blocked.setdefault(fo, []).append((int(frame) - buf, int(frame) + buf))

    @classmethod
    def for_track(cls, track: Track, quiet: bool = False) -> "ForbiddenGuard":
        """The guard from the ingested kit; before the kit, LUMPI falls back to its blocked window, which
        already contains all 100 forbidden frames. V2X without the kit refuses everything."""
        try:
            return cls(track)
        except FileNotFoundError:
            if not quiet:
                print(f"note: {track.name} starting kit not ingested; guarding with the blocked windows only"
                      + ("" if track.name == "lumpi-track" else " (V2X: every real frame is refused)"))
            return cls(track, forbidden_ids=[])

    @property
    def resolved(self) -> bool:
        return self.track.name == "lumpi-track" or getattr(self, "id_mapping", None) is not None

    def is_blocked(self, group: str, frame: int) -> bool:
        if not self.resolved:
            return True                       # refuse everything until the V2X mapping is known
        windows = self.blocked.get(group, []) + self.blocked.get("*", [])
        return any(lo <= int(frame) <= hi for lo, hi in windows)

    def filter(self, keys, purpose: str) -> list[tuple[str, int]]:
        """Allowed subset of (group, frame) keys; logs the allowed ones with `purpose`."""
        keys = [(str(g), int(f)) for g, f in keys]
        allowed = [k for k in keys if not self.is_blocked(*k)]
        self._log(allowed, purpose)
        return allowed

    def check(self, group: str, frame: int, purpose: str) -> None:
        if self.is_blocked(group, frame):
            raise ForbiddenFrameError(f"{self.track.name}: frame {group}/{frame} is forbidden or self-excluded")
        self._log([(group, int(frame))], purpose)

    def _log(self, keys, purpose: str) -> None:
        if not keys:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.log_path.exists()
        with open(self.log_path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["unix_time", "purpose", "group", "frame"])
            t = f"{time.time():.0f}"
            w.writerows([t, purpose, g, fr] for g, fr in keys)
