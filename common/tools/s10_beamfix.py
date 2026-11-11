#!/usr/bin/env python
"""S10 L1/L2, the PandarQT near-field re-cast (docs/decisions/2026-11-08-s10-clean-final-plan.md Sections 15.15.3,
15.15.5 and 15.15.7). Metadata only: no real point, label or frame enters.

The UrbanTwin twin's PandarQT (LUMPI Measurement4 session 36) lacks the sensor's steep beams (-52 to -30 deg), so its
ground returns near the sensor do not form the real ring pattern. For every frame, the flat-ground points
(|z - ground_z| < tol) within `radius` m (bird's-eye view) of the sensor are moved radially (azimuth kept) onto one
ground ring of the sensor's real beam table (meta.json elevations; ring distance h / tan(-elevation), h = sensor
height above the ground). Each point draws one ring uniformly among the rings in (0.3 m, radius], with 1% radial
jitter. The point count is kept. A point inside a labelled box's footprint column (all classes, 0.1 m margin, up to
the box top) is never moved, and a point whose destination falls in such a column stays where it is, so every box
keeps exactly its points (the GT database does not change). The draws are seeded per frame ([seed, frame id]), so
the corpus and a packaged frame taken from it are the same bytes.

    python common/tools/s10_beamfix.py lumpi pcdet/g1-v6 pcdet/g1-v6pq        # sensor 36, radius 7 m, seed 0
    then: python common/tools/pcdet_build_infos.py <member> --data pcdet/g1-v6pq

The held-out realism check of record 15.15.3 used the same re-cast without the box guard (research2/realism/beamfix.py).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from bdc26.io import lumpi  # noqa: E402

TOL, MARGIN, JITTER, RMIN = 0.12, 0.1, 0.01, 0.3


def sensor_rings(extrinsic: np.ndarray, elevation_deg: np.ndarray, ground_z: float, radius: float):
    """(sensor xyz in the local frame, sorted ground-ring distances in (RMIN, radius]) of one sensor."""
    o = np.asarray(extrinsic, dtype=np.float64)[:3, 3]
    h = o[2] - ground_z
    b = np.asarray(elevation_deg, dtype=np.float64)
    b = b[b < -0.5]
    d = h / np.tan(np.radians(-b))
    return o, np.sort(d[(d > RMIN) & (d <= radius)])


def in_footprints(xy: np.ndarray, z: np.ndarray, boxes: np.ndarray, margin: float = MARGIN) -> np.ndarray:
    """Points inside any box's footprint column (x y z dx dy dz yaw; xy margin, from below up to the box top)."""
    m = np.zeros(len(xy), dtype=bool)
    for x, y, zc, dx, dy, dz, yaw in boxes[:, :7]:
        c, s = np.cos(yaw), np.sin(yaw)
        px, py = xy[:, 0] - x, xy[:, 1] - y
        lx, ly = c * px + s * py, -s * px + c * py
        m |= (np.abs(lx) <= dx / 2 + margin) & (np.abs(ly) <= dy / 2 + margin) & (z <= zc + dz / 2)
    return m


def recast(P: np.ndarray, boxes: np.ndarray, sensors: list, radius: float, ground_z: float,
           rng: np.random.Generator, tol: float = TOL) -> tuple:
    """The re-cast frame (a copy; extra columns kept) and the number of points moved."""
    P = P.copy()
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 7) if len(boxes) else np.zeros((0, 7))
    moved = 0
    for o, d in sensors:
        if len(d) == 0:
            continue
        dx, dy = P[:, 0] - o[0], P[:, 1] - o[1]
        r = np.hypot(dx, dy)
        m = (r <= radius) & (r > 0.05) & (np.abs(P[:, 2] - ground_z) < tol)
        if len(boxes):
            m &= ~in_footprints(P[:, :2], P[:, 2], boxes)
        idx = np.flatnonzero(m)
        if len(idx) == 0:
            continue
        nd = d[rng.integers(0, len(d), len(idx))] * (1 + rng.normal(0, JITTER, len(idx)))
        nx = o[0] + dx[idx] / r[idx] * nd
        ny = o[1] + dy[idx] / r[idx] * nd
        if len(boxes):
            ok = ~in_footprints(np.stack([nx, ny], 1), P[idx, 2], boxes)
            idx, nx, ny = idx[ok], nx[ok], ny[ok]
        P[idx, 0], P[idx, 1] = nx, ny
        moved += len(idx)
    return P, moved


def read_boxes(label_file: Path) -> np.ndarray:
    rows = [ln.split()[:7] for ln in label_file.read_text().splitlines() if ln.strip()] if label_file.exists() else []
    return np.array(rows, dtype=np.float64).reshape(-1, 7)


def frame_rng(seed: int, fid: str) -> np.random.Generator:
    return np.random.default_rng([int(seed), int(fid)])


def _one(fid: str, src: Path, dst: Path, sensors: list, radius: float, ground_z: float, seed: int) -> tuple:
    P = np.load(src / "points" / f"{fid}.npy")
    Q, n = recast(P, read_boxes(src / "labels" / f"{fid}.txt"), sensors, radius, ground_z, frame_rng(seed, fid))
    np.save(dst / "points" / f"{fid}.npy", Q.astype(P.dtype))
    return n, len(P)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--sensors", default="36", help="Measurement4 lidar sessions, comma separated (36 = PandarQT)")
    ap.add_argument("--radius", type=float, default=7.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    T = load_track(a.track)
    if T.name != "lumpi-track":
        raise SystemExit("the re-cast uses the LUMPI Measurement4 beam tables")
    src, dst = data_path(T, a.src), data_path(T, a.dst)
    if dst.exists():
        raise SystemExit(f"{dst} exists; choose a new corpus name")
    gz = float(T["ut"]["ground_z"])
    sess = lumpi.read_sessions(T.real / "raw" / "meta.json", T, experiment=4)
    sids = [int(s) for s in a.sensors.split(",")]
    sensors = [sensor_rings(sess[s].extrinsic_local, sess[s].elevation_deg, gz, a.radius) for s in sids]
    for s, (o, d) in zip(sids, sensors):
        print(f"sensor {s}: at {np.round(o, 3).tolist()}, {len(d)} ground rings in ({RMIN}, {a.radius}] m: {np.round(d, 2).tolist()}")
    (dst / "points").mkdir(parents=True)
    shutil.copytree(src / "labels", dst / "labels")
    shutil.copytree(src / "ImageSets", dst / "ImageSets")
    fids = sorted(p.stem for p in (src / "points").glob("*.npy"))
    t0 = time.time()
    with Pool(a.workers) as pool:
        res = pool.map(partial(_one, src=src, dst=dst, sensors=sensors, radius=a.radius, ground_z=gz, seed=a.seed),
                       fids, chunksize=32)
    moved = np.array([n for n, _ in res])
    card = yaml.safe_load((src / "dataset.yaml").read_text())
    names = T["real"]["sessions_m4"]
    note = (f"S10 near-field re-cast of the {', '.join(f'{names.get(s, s)} (session {s})' for s in sids)} ground "
            f"returns onto its Measurement4 beam table (metadata only)")
    card.update({
        "derived_from": a.src,
        "real_data_use": f"{card.get('real_data_use', '')}; {note}".lstrip("; "),
        "beamfix": {"tool": "common/tools/s10_beamfix.py", "sensors": sids, "radius": a.radius, "tol": TOL,
                    "box_margin": MARGIN, "jitter": JITTER, "seed": a.seed, "ground_z": gz,
                    "moved_per_frame_mean": round(float(moved.mean()), 2), "moved_per_frame_max": int(moved.max()),
                    "frames_touched": int((moved > 0).sum()),
                    "record": "docs/decisions/2026-11-08-s10-clean-final-plan.md Section 15.15.7"},
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "git_sha": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                  cwd=Path(__file__).resolve().parent).stdout.strip(),
        "n_frames": len(fids),
    })
    (dst / "dataset.yaml").write_text(yaml.safe_dump(card, sort_keys=False, width=120))
    print(json.dumps({"dst": str(dst), "frames": len(fids), "moved_mean": round(float(moved.mean()), 2),
                      "moved_max": int(moved.max()), "frames_touched": int((moved > 0).sum()),
                      "wall_s": round(time.time() - t0, 1)}))
    print(f"next: python common/tools/pcdet_build_infos.py <member> --data {a.dst}")


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    main()
