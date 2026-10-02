#!/usr/bin/env python
"""Download real LUMPI data from the LUH vault (plain HTTP with Range requests; no login).

LICENCE: LUMPI is CC BY-NC 3.0 (non-commercial). Get written clearance for your organization first;
--accept-licence records that you have it.

Parts:
  --meta               meta.json (sensor extrinsics and elevation tables) and HD_map/ (OpenDRIVE lanes, crosswalks)
  --labels             Label.csv of Measurement4/5/6, filtered through the ForbiddenGuard WHILE streaming: rows of the
                       blocked Measurement4 window never reach disk -> real/labels/<M>_Label.guarded.csv
  --lidar M --range a:b:s   raw PLY frames of measurement M (frames a..b step s), skipping blocked frames
                       -> real/raw/<M>/lidar/<frame>.ply (raw files kept for sensor calibration, M5.3)

    python fetch_real.py --accept-licence --meta --labels
    python fetch_real.py --accept-licence --lidar Measurement4 --range 0:6400:5     # about 1,280 frames, 8 GB
    python fetch_real.py --accept-licence --lidar Measurement5 --range 0:7560:20
"""
import argparse
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
import requests  # noqa: E402

from bdc26.config import load_track  # noqa: E402
from bdc26.guard import ForbiddenGuard  # noqa: E402
from bdc26.io import fetch  # noqa: E402

T = load_track("lumpi-track")
VAULT = T["real"]["vault"]


def guard() -> ForbiddenGuard:
    return ForbiddenGuard.for_track(T)


def remote_zip(parts_urls: list[str]):
    parts = []
    for u in parts_urls:
        res = fetch.static_resolver(u)
        parts.append((res, fetch.remote_size(res)))
    return lambda: fetch.open_zip(parts, buffer=1 << 20)


def fetch_meta(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    (out / "meta.json").write_bytes(requests.get(VAULT + "meta.json", timeout=120).content)
    idx = requests.get(VAULT + "HD_map/", timeout=60).text
    for name in re.findall(r'href="([^"?]+)"', idx):
        if name.startswith(("http", "/", ".")) or name.endswith("/") or "." not in name:
            continue                        # skip external, parent and sub-directory links
        (out / "HD_map").mkdir(exist_ok=True)
        (out / "HD_map" / name).write_bytes(requests.get(VAULT + "HD_map/" + name, timeout=300).content)
    print(f"meta.json and HD_map/ -> {out}")


def fetch_labels(g: ForbiddenGuard, out: Path):
    zopen = remote_zip([VAULT + T["real"]["labels_zip"]])
    zf = zopen()
    out.mkdir(parents=True, exist_ok=True)
    for meas in T["real"]["measurements_all_sensors"]:
        name = next(n for n in zf.namelist() if n.endswith(f"{meas}/Label.csv"))
        kept = dropped = 0
        with zf.open(name) as src, open(out / f"{meas}_Label.guarded.csv", "w") as dst:
            frames_seen = set()
            for line in io.TextIOWrapper(src, encoding="utf-8"):
                if not line.strip():
                    continue
                try:
                    frame = int(float(line.split(",", 1)[0]) * 10 + 1e-6)
                except ValueError:          # header row
                    dst.write(line)
                    continue
                if g.is_blocked(meas, frame):
                    dropped += 1
                    continue
                frames_seen.add(frame)
                dst.write(line)
                kept += 1
        g.filter([(meas, f) for f in sorted(frames_seen)], purpose="download labels")
        print(f"{meas}: kept {kept} label rows, dropped {dropped} rows of blocked frames")


def fetch_lidar(g: ForbiddenGuard, meas: str, spec: str, out: Path, workers: int):
    a, b, s = (int(v) for v in spec.split(":"))
    n_parts = T["real"]["lidar_parts"][meas]
    zopen = remote_zip([f"{VAULT}{meas}/lidar.zip.{i:03d}" for i in range(1, n_parts + 1)])
    allowed = g.filter([(meas, f) for f in range(a, b, s)], purpose="download lidar")
    names = [f"lidar/{f:06d}.ply" for _, f in allowed]
    present = set(zopen().namelist())
    names = [n for n in names if n in present]
    print(f"{meas}: {len(names)} frames")
    fetch.extract_members(zopen, names, out / meas, workers=workers)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--accept-licence", action="store_true", required=True)
    ap.add_argument("--meta", action="store_true")
    ap.add_argument("--labels", action="store_true")
    ap.add_argument("--lidar", default=None, help="measurement, e.g. Measurement4")
    ap.add_argument("--range", default="0:6400:5", help="a:b:step frame range for --lidar")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    raw = T.real / "raw"
    if a.meta:
        fetch_meta(raw)
    g = guard()
    if a.labels:
        fetch_labels(g, T.real / "labels")
    if a.lidar:
        fetch_lidar(g, a.lidar, a.range, raw, a.workers)


if __name__ == "__main__":
    main()
