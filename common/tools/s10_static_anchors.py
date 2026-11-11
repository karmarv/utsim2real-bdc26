#!/usr/bin/env python
"""S10 R1 twin completion, the anchors (docs/decisions/2026-11-08-s10-clean-final-plan.md Sections 15.13 and 15.14).
Allowed by the organizers' answer to question (c) (2026-11-10): static structures may be located in unlabelled,
non-forbidden real frames and our own synthetic geometry added there, with no real point copied; describe it in the
report. clean_check.py still fails an anchored corpus unless BDC_ALLOW_R1=1, so every R1 corpus is a deliberate choice.

Where do unlabelled legal real frames show persistent static geometry that the UrbanTwin twin lacks? On a 0.5 m BEV
grid, a cell is static-real when points stand at least 0.3 m above its ground (the 5th percentile of z in the cell) in at
least 60% of the real frames, and twin-covered when the same holds in at least 30% of the UrbanTwin frames. The
static-real cells the twin does not cover are grouped into connected clusters. Vehicle-sized clusters (3.5-6.5 m by
1.0-3.0 m: parked cars, which are labelled objects) are dropped: no real object position becomes a structure (audit
rule b). Each other cluster becomes one block anchor, or several of at most 5 m along its long axis: centre, heading
(principal axis of its cells), length, width and height (the 90th percentile of the points' height above the cell
ground, 0.3-8 m). No label is read and no real point is copied; the generator ray-casts synthetic blocks there.
v2 (default): the anchor frames exclude every realism-proxy frame (as the density prior does), so the held-out proxies
4-5 that judge R1's realism never fed the anchors (v1 shared 30-38% of their frames).

v2m: the mass calibration (--calibrate, see calibrate()) adds each block's kept share of returns.

    python common/tools/s10_static_anchors.py lumpi            # writes <track gen>/static_anchors_r1_v2.json
    python common/tools/s10_static_anchors.py lumpi --calibrate pcdet/g1-v6 pcdet/g1-v6r1   # writes ..._v2m.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path, load_track  # noqa: E402

CELL, R, LIFT = 0.5, 40.0, 0.3


def _grid(frames):
    n = int(2 * R / CELL)
    P = np.concatenate(frames)
    P = P[np.any(P != 0, 1) & (np.abs(P[:, 0]) < R) & (np.abs(P[:, 1]) < R)]
    ij = np.floor((P[:, :2] + R) / CELL).astype(int)
    key = ij[:, 0] * n + ij[:, 1]
    ground = np.full(n * n, np.nan)
    order = np.argsort(key)
    ks, st = np.unique(key[order], return_index=True)
    for kk, a, b in zip(ks, st, list(st[1:]) + [len(order)]):
        if b - a >= 10:
            ground[kk] = np.percentile(P[order[a:b], 2], 5)
    occ, mass = np.zeros(n * n), np.zeros(n * n)
    heights = [[] for _ in range(n * n)]
    for f in frames:
        f = f[np.any(f != 0, 1) & (np.abs(f[:, 0]) < R) & (np.abs(f[:, 1]) < R)]
        kij = np.floor((f[:, :2] + R) / CELL).astype(int)
        kk = kij[:, 0] * n + kij[:, 1]
        dz = f[:, 2] - np.nan_to_num(ground[kk], nan=1e9)
        up = dz > LIFT
        occ[np.unique(kk[up])] += 1
        np.add.at(mass, kk[up], 1)
        for c, h in zip(kk[up][::7], dz[up][::7]):              # a thinned sample of heights per cell
            heights[c].append(h)
    return n, (occ / len(frames)).reshape(n, n), (mass / len(frames)).reshape(n, n), heights


def _frames(track, spec, ids, k):
    root = data_path(track, spec)
    ids = ids[:: max(1, len(ids) // k)][:k]
    return [np.load(root / "points" / f"{i}.npy")[:, :3].astype(np.float64) for i in ids]


def proxy_ids(track, k=5):
    """Frame IDs of the realism proxies 1..k (the realism judges), kept out of the anchor frames."""
    out = set()
    for j in range(1, k + 1):
        p = data_path(track, f"pcdet/realism-proxy-{j}") / "points"
        out |= {x.stem for x in p.glob("*.npy")}
    return out


def anchors(track, n_frames=300, static_p=0.6, twin_p=0.3, max_len=5.0, exclude=frozenset()):
    root = data_path(track, "pcdet/realval-v1")
    ids = (root / "ImageSets" / "val.txt").read_text().split()
    if track.name.lower().startswith("lumpi"):
        ids = [i for i in ids if i.startswith("Measurement4") and int(i.split("__")[1]) < 6400]
    ids = [i for i in ids if i not in exclude]
    ut = sorted(p.stem for p in (data_path(track, "pcdet/ut-v1") / "points").glob("*.npy"))
    n, pr, mr, hr = _grid(_frames(track, "pcdet/realval-v1", ids, n_frames))
    _, pu, _, _ = _grid(_frames(track, "pcdet/ut-v1", ut, n_frames))
    missing = (pr >= static_p) & (pu < twin_p)
    lab, k = ndimage.label(missing)
    out, dropped = [], 0.0
    for c in range(1, k + 1):
        ii, jj = np.nonzero(lab == c)
        xy = np.stack([ii * CELL - R + CELL / 2, jj * CELL - R + CELL / 2], 1)
        if len(xy) >= 2:
            w_, v = np.linalg.eigh(np.cov(xy.T))
            ax = v[:, np.argmax(w_)]
        else:
            ax = np.array([1.0, 0.0])
        yaw = float(np.arctan2(ax[1], ax[0]))
        u = xy @ ax
        q = xy @ np.array([-ax[1], ax[0]])
        L, W = float(np.ptp(u) + CELL), float(np.ptp(q) + CELL)
        flat = (ii * n + jj)
        hs = np.concatenate([np.asarray(hr[f]) for f in flat if hr[f]] or [np.zeros(1)])
        H = float(np.clip(np.percentile(hs, 90), LIFT, 8.0))
        m = float(mr[ii, jj].sum())
        if 3.5 <= L <= 6.5 and 1.0 <= W <= 3.0:
            dropped += m
            continue
        q0 = float(np.mean(q))
        parts = max(1, int(np.ceil(L / max_len)))
        for p_ in range(parts):
            lo, hi = u.min() - CELL / 2 + p_ * L / parts, u.min() - CELL / 2 + (p_ + 1) * L / parts
            cu = (lo + hi) / 2
            cx, cy = cu * ax[0] - q0 * ax[1], cu * ax[1] + q0 * ax[0]
            out.append({"x": round(float(cx), 3), "y": round(float(cy), 3), "yaw": round(yaw, 4), "l": round(hi - lo, 3),
                        "w": round(W, 3), "h": round(H, 3), "cluster": c, "mass_points_per_frame": round(m / parts, 1)})
    return out, {"clusters": int(k), "vehicle_sized_dropped_points_per_frame": round(dropped, 1),
                 "missing_mass_points_per_frame": round(float(mr[missing].sum()), 1)}


def _in_footprint(P, r, pad):
    c, s = np.cos(r["yaw"]), np.sin(r["yaw"])
    d = P[:, :2] - [r["x"], r["y"]]
    near = np.nonzero(np.abs(d).max(1) < (max(r["l"], r["w"]) / 2 + pad + 0.1) * 1.5)[0]
    u, v = d[near] @ [c, s], d[near] @ [-s, c]
    return near[(np.abs(u) < r["l"] / 2 + pad) & (np.abs(v) < r["w"] / 2 + pad)]


def footprint_counts(P, rows, pad=0.25, ground=None):
    """(len(rows),) points of P inside each anchor's footprint grown by pad (BEV); with ground ((len(rows),) z), only
    the points more than LIFT above it, as the anchors' real mass is counted."""
    out = np.zeros(len(rows))
    for k, r in enumerate(rows):
        idx = _in_footprint(P, r, pad)
        out[k] = len(idx) if ground is None else np.count_nonzero(P[idx, 2] > ground[k] + LIFT)
    return out


def footprint_ground(frames, rows, pad=0.75):
    """(len(rows),) the 5th percentile of z near each footprint over the (unanchored) frames, nan where too few points."""
    zs = [[] for _ in rows]
    for P in frames:
        for k, r in enumerate(rows):
            zs[k].append(P[_in_footprint(P, r, pad), 2])
    return np.array([np.percentile(np.concatenate(z), 5) if sum(map(len, z)) >= 10 else np.nan for z in zs])


def calibrate(track, base, anchored, rows, n_frames=200, floor=0.02):
    """The mass calibration: solid synthetic blocks return more points than the porous real structures they stand for
    (2026-11-10, R1.0: LUMPI 4.35x and V2X 1.44x the real missing mass in the stored frames). Over n_frames frames of an
    anchored corpus and its unanchored twin (same recipe and seed, so the same scenes), the extra stored points in each
    anchor's footprint more than LIFT above the local ground (as the real mass is counted; a net count would miss the ground
    each block hides) estimate its returns; the block then keeps the share mass / returns of its rays (floor..1). Uses only
    the anchors' real missing mass (unlabelled frames, already part of R1) and synthetic frames."""
    ids = sorted(p.stem for p in (data_path(track, anchored) / "points").glob("*.npy"))
    ids = ids[:: max(1, len(ids) // n_frames)][:n_frames]
    B = [np.load(data_path(track, base) / "points" / f"{i}.npy")[:, :3] for i in ids]
    g = footprint_ground(B, rows)
    g = np.where(np.isfinite(g), g, np.nanmedian(g))
    extra = np.zeros(len(rows))
    for i, b in zip(ids, B):                        # points LIFT above the ground, as the real mass is counted
        a = np.load(data_path(track, anchored) / "points" / f"{i}.npy")[:, :3]
        extra += footprint_counts(a, rows, ground=g) - footprint_counts(b, rows, ground=g)
    extra /= len(ids)
    mass = np.array([r["mass_points_per_frame"] for r in rows])
    keep = np.where(extra > mass, np.clip(mass / np.maximum(extra, 1e-9), floor, 1.0), 1.0)
    out = [{**r, "measured_points_per_frame": round(float(e), 1), "keep": round(float(k), 4)} for r, e, k in zip(rows, extra, keep)]
    return out, {"frames": len(ids), "base": base, "anchored": anchored, "mass": round(float(mass.sum()), 1),
                 "measured": round(float(extra.sum()), 1), "expected_after": round(float((extra * keep).sum()), 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--out", default=None)
    ap.add_argument("--v1", action="store_true", help="the v1 anchors (proxy frames not excluded)")
    ap.add_argument("--calibrate", nargs=2, metavar=("BASE", "ANCHORED"), default=None,
                    help="write the mass-calibrated anchors (static_anchors_r1_v2m.json) from the v2 file, an anchored corpus "
                         "and its unanchored twin, e.g. pcdet/g1-v6 pcdet/g1-v6r1")
    a = ap.parse_args()
    t = load_track(a.track)
    if a.calibrate:
        src = t.gen / "static_anchors_r1_v2.json"
        d = json.loads(src.read_text())
        rows, info = calibrate(t, a.calibrate[0], a.calibrate[1], d["anchors"], n_frames=min(a.frames, 200))
        out = Path(a.out) if a.out else t.gen / "static_anchors_r1_v2m.json"
        out.write_text(json.dumps({**d, "calibration": {"from": src.name, **info}, "anchors": rows}, indent=1))
        print(f"{t.name}: calibrated {len(rows)} anchors -> {out} ({info})")
        return
    excl = frozenset() if a.v1 else frozenset(proxy_ids(t))
    rows, info = anchors(t, a.frames, exclude=excl)
    out = Path(a.out) if a.out else t.gen / f"static_anchors_r1_{'v1' if a.v1 else 'v2'}.json"
    out.write_text(json.dumps({"track": t.name, "use": "S10 R1, allowed by the organizers' answer to question (c), 2026-11-10",
                               "source": "unlabelled legal realval-v1 frames (val split" + (", Measurement4 < 6400" if
                                         t.name.lower().startswith("lumpi") else "") +
                                         ("" if a.v1 else f", the {len(excl)} realism-proxy frames excluded") +
                                         ") against pcdet/ut-v1; no label read",
                               "cell_m": CELL, **info, "anchors": rows}, indent=1))
    print(f"{t.name}: {len(rows)} anchors from {info['clusters']} clusters -> {out} ({info})")


if __name__ == "__main__":
    main()
