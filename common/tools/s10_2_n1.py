#!/usr/bin/env python
"""S10-2 lever B (release 10.2, docs/decisions/2026-11-12-s10-10.2-clean-final-push.md Section 5): N1, the
2 x 2 x 0.5 m nearest-support density prior, applied inside the LUMPI generator to every frame of a training corpus.
The organizers' answer of 2026-11-12 allows it on these terms: the same calibration in the training data, the
detector retrained on it, and the 50 frames taken from that data.

fit    Every point of the legal fit frames (unlabelled; realism proxies 1-3, Measurement4 frames below 6400) goes to
       its nearest synthetic point, pooled over the 50 frames of `--ids` in `--corpus`. Per voxel of that synthetic
       support, weight = real share / synthetic share (no clip). Only these per-voxel scalars are saved; no real point
       or coordinate is kept. Identical to the research3 `safe_frames` fit (S10 record 15.16).
build  Every frame of `src` is re-drawn to its own point count by systematic sampling with probability ~ weight of
       its voxel (1.0 where the fit support has no voxel). Points inside a labelled box (0.1 m footprint margin, up
       to the box top) are kept as generated (`--no-box-guard` re-draws them too). A point drawn more than once is
       copied with N(0, 2 cm) jitter, clipped to the range. Draws are seeded per frame ([seed, frame id]), so a
       packaged frame and its corpus frame are the same bytes. Labels and ImageSets are copied; the card's
       `real_data_use` gains the N1 item, which rule 1b (clean_check.py) checks.

    python common/tools/s10_2_n1.py fit lumpi --corpus pcdet/g1-v6pq --ids <50 ids> --out gen/s10_2_n1_weights.npz
    python common/tools/s10_2_n1.py build lumpi pcdet/g1-v6pq pcdet/g1-v6n1 --weights gen/s10_2_n1_weights.npz
    then: python common/tools/pcdet_build_infos.py <member> --data pcdet/g1-v6n1
"""
import argparse
import hashlib
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
from s10_beamfix import in_footprints, read_boxes  # noqa: E402

LO, HI = np.array([-40, -40, -5], np.float32), np.array([40, 40, 5], np.float32)
FIT = ["realism-proxy-1", "realism-proxy-2", "realism-proxy-3"]
RECORD = "docs/decisions/2026-11-12-s10-10.2-clean-final-push.md Section 5"


def item(weights: str) -> str:
    """The card's real-data item for N1 (the same text on every corpus built with these weights)."""
    return (f"S10-2 N1 density prior: per-voxel weights (2 x 2 x 0.5 m) fitted on legal unlabelled Measurement4 frames "
            f"below 6400 (realism proxies 1-3) by nearest-support assignment ({Path(weights).name}), every frame "
            f"re-drawn to its own point count, points in labelled boxes kept")   # no ';': clean_check splits items at ';'


def guard_fit(name: str):
    stem = os.path.basename(name)
    if "kit" in name or "test" in name.lower():
        raise SystemExit(f"guard: {name} is not a legal fit set")
    if stem.startswith("Measurement4__") and 6400 <= int(stem.split("__")[1][:6]) <= 8199:
        raise SystemExit(f"guard: {name} is in the self-excluded Measurement4 6400-8199 window")


def in_range(p: np.ndarray) -> np.ndarray:
    return np.all((p >= LO) & (p <= HI), axis=1)


def voxel_key(P: np.ndarray, vox) -> np.ndarray:
    """Voxel index, computed in float64 as in the fit (float32 would move boundary points to a neighbouring cell)."""
    P = np.asarray(P, dtype=np.float64)
    vx, vy, vz = vox
    return ((np.floor((P[:, 0] + 40) / vx).astype(np.int64) * 100000 + np.floor((P[:, 1] + 40) / vy).astype(np.int64)) * 1000
            + np.floor((P[:, 2] + 5) / vz).astype(np.int64))


def fit_weights(S: list, real: np.ndarray, vox) -> tuple:
    """(voxel keys, weights) of the pooled synthetic support S against the real points (nearest-support shares)."""
    from scipy.spatial import cKDTree
    SP = np.concatenate(S).astype(np.float64)
    _, nn = cKDTree(SP).query(real.astype(np.float64), k=1, workers=8)
    uk, inv = np.unique(voxel_key(SP, vox), return_inverse=True)
    ns = np.bincount(inv, minlength=len(uk)).astype(np.float64)
    mr = np.bincount(inv[nn], minlength=len(uk)).astype(np.float64)
    return uk, (mr / mr.sum()) / (ns / ns.sum())


def lookup(P: np.ndarray, uk: np.ndarray, wv: np.ndarray, vox) -> np.ndarray:
    k = voxel_key(P, vox)
    i = np.clip(np.searchsorted(uk, k), 0, len(uk) - 1)
    return np.where(uk[i] == k, wv[i], 1.0)


def redraw(P: np.ndarray, w: np.ndarray, guard: np.ndarray, rng: np.random.Generator, jit: float = 0.02) -> tuple:
    """P re-drawn to len(P) points: guarded points kept, the rest by systematic sampling ~ w; (points, copies).
    With no guarded point this is exactly the research3 frame re-draw."""
    n = len(P)
    keep, free = np.flatnonzero(guard), np.flatnonzero(~guard)
    m = n - len(keep)
    u = (rng.random() + np.arange(m)) / m
    pw = w[free] / w[free].sum()
    sel = free[np.minimum(np.searchsorted(np.cumsum(pw), u), len(free) - 1)]
    idx = np.sort(np.concatenate([keep, sel])) if len(keep) else sel
    Q = P[idx].copy()
    dup = np.zeros(n, bool)
    dup[1:] = idx[1:] == idx[:-1]
    Q[dup] += rng.normal(0, jit, (int(dup.sum()), 3)).astype(np.float32)
    Q = np.clip(Q, LO, HI).astype(np.float32)[rng.permutation(n)]
    return Q, int(dup.sum())


def cmd_fit(a):
    T = load_track(a.track)
    src = data_path(T, a.corpus)
    ids = sorted(Path(a.ids).read_text().split())
    S = [np.load(src / "points" / f"{i}.npy")[:, :3].astype(np.float32) for i in ids]
    if not all(in_range(f).all() for f in S):
        raise SystemExit("the 50 frames must lie fully in range")
    real, frames = [], []
    for name in a.fit:
        guard_fit(name)
        for f in sorted((T.root / "pcdet" / name / "points").glob("*.npy")):
            guard_fit(f.name)
            p = np.load(f)[:, :3].astype(np.float32)
            real.append(p[in_range(p)])
            frames.append(f.stem)
    vox = tuple(float(v) for v in a.vox.split(","))
    uk, wv = fit_weights(S, np.concatenate(real), vox)
    out = data_path(T, a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, voxel_key=uk, weight=wv, vox=np.array(vox))
    meta = {"corpus": a.corpus, "ids": ids, "fit_sets": a.fit, "fit_frames": len(frames),
            "fit_frame_range": [min(frames), max(frames)], "n_real_points": int(sum(len(r) for r in real)),
            "n_voxels": int(len(uk)), "vox": list(vox), "weight_pct_1_50_99": np.percentile(wv, [1, 50, 99]).round(4).tolist(),
            "created": time.strftime("%Y-%m-%d %H:%M"), "record": RECORD}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ("fit_frames", "fit_frame_range", "n_real_points", "n_voxels")}))


def _one(fid: str, src: Path, dst: Path, uk, wv, vox, seed: int, box_guard: bool) -> tuple:
    P = np.load(src / "points" / f"{fid}.npy")
    X = P[:, :3].astype(np.float32)
    if not in_range(X).all():
        X = np.clip(X, LO, HI)
    guard = np.zeros(len(X), bool)
    if box_guard:
        b = read_boxes(src / "labels" / f"{fid}.txt")
        if len(b):
            guard = in_footprints(X[:, :2], X[:, 2], b, 0.1)
    Q, ncopy = redraw(X, lookup(X, uk, wv, vox), guard, np.random.default_rng([int(seed), int(fid)]))
    np.save(dst / "points" / f"{fid}.npy", Q.astype(P.dtype))
    return ncopy, int(guard.sum())


def cmd_build(a):
    T = load_track(a.track)
    src, dst = data_path(T, a.src), data_path(T, a.dst)
    if dst.exists():
        raise SystemExit(f"{dst} exists; choose a new corpus name")
    W = np.load(data_path(T, a.weights))
    uk, wv, vox = W["voxel_key"], W["weight"], tuple(W["vox"].tolist())
    (dst / "points").mkdir(parents=True)
    shutil.copytree(src / "labels", dst / "labels")
    shutil.copytree(src / "ImageSets", dst / "ImageSets")
    fids = sorted(p.stem for p in (src / "points").glob("*.npy"))
    t0 = time.time()
    with Pool(a.workers) as pool:
        res = pool.map(partial(_one, src=src, dst=dst, uk=uk, wv=wv, vox=vox, seed=a.seed, box_guard=not a.no_box_guard),
                       fids, chunksize=32)
    copies = np.array([c for c, _ in res])
    card = yaml.safe_load((src / "dataset.yaml").read_text())
    card.update({
        "derived_from": a.src,
        "real_data_use": f"{card.get('real_data_use', '')}; {item(a.weights)}".lstrip("; "),
        "n1": {"tool": "common/tools/s10_2_n1.py", "weights": a.weights,
               "weights_md5": hashlib.md5(data_path(T, a.weights).read_bytes()).hexdigest(), "vox": list(vox),
               "seed": a.seed, "jitter": 0.02, "box_guard": not a.no_box_guard,
               "copies_per_frame_mean": round(float(copies.mean()), 1), "record": RECORD},
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "git_sha": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                  cwd=Path(__file__).resolve().parent).stdout.strip(),
        "n_frames": len(fids),
    })
    (dst / "dataset.yaml").write_text(yaml.safe_dump(card, sort_keys=False, width=120))
    print(json.dumps({"dst": str(dst), "frames": len(fids), "copies_mean": round(float(copies.mean()), 1),
                      "guarded_mean": round(float(np.mean([g for _, g in res])), 1), "wall_s": round(time.time() - t0, 1)}))
    print(f"next: python common/tools/pcdet_build_infos.py <member> --data {a.dst}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit")
    f.add_argument("track")
    f.add_argument("--corpus", required=True)
    f.add_argument("--ids", required=True, help="the 50 frame ids whose pooled support is weighted")
    f.add_argument("--fit", nargs="+", default=FIT)
    f.add_argument("--vox", default="2,2,0.5")
    f.add_argument("--out", required=True, help="weights file, relative to $BDC_DATA/<track>")
    b = sub.add_parser("build")
    b.add_argument("track")
    b.add_argument("src")
    b.add_argument("dst")
    b.add_argument("--weights", required=True)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--no-box-guard", action="store_true")
    b.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    if load_track(a.track).name != "lumpi-track":
        raise SystemExit("N1 is the LUMPI density prior")
    cmd_fit(a) if a.cmd == "fit" else cmd_build(a)


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    main()
