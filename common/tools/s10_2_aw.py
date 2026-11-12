#!/usr/bin/env python
"""S10-2 lever V3 (release 10.2, docs/decisions/2026-11-12-s10-10.2-clean-final-push.md Section 5): the V2X `aw_mid`
calibration (S10 record 15.16) applied inside the generator to every frame of a training corpus, with the sensor's
no-return points stored in the corpus. The organizers' answer of 2026-11-12 allows "the V2X range mapping" as part
of the data generator when the detector is retrained on it and the 50 frames come from that data.

fit    From legal unlabelled V2X frames (realism proxies 1-3; no forbidden frame, none within 20 frames of one) and a
       synthetic pool of 150 `g1-v6` frames outside the 50 submitted ids (seed 0, 34,500 valid points each):
       A: per (10 deg azimuth x 2.125 deg elevation) bin, weight = (real share / synthetic share) ** 0.5, clipped to
          [0.1, 10], 1.0 where the twin barely covers the bin; donors = the pool's points outside labelled boxes.
       W: per bin, 21 range quantiles of the pool and of the real frames.
       Only these scalars and the synthetic donor points are saved; no real point is kept.
build  Every frame of `src` (valid points only) is written as the packaged frame would be: 50,000 points with 31%
       (0,0,0) no-returns (`bdc26.frames.with_nulls`, seeded [seed, frame id]). Then A: per bin, the frame keeps its
       own points up to the bin's target and fills the deficit with donor points of that bin (never inside a box);
       then W: each non-box point moves along its own ray so that the bin's range quantiles map onto the real ones
       (a point that would enter a box or leave the range stays). Nulls and box points are never changed. The
       detector's loader strips the no-returns in training and at inference, as before.

    python common/tools/s10_2_aw.py fit v2x --ids <50 ids> --out gen/s10_2_aw_tables.npz
    python common/tools/s10_2_aw.py build v2x pcdet/g1-v6 pcdet/g1-v6aw --tables gen/s10_2_aw_tables.npz
    python common/tools/s10_2_aw.py check v2x --tables ... --zip <c1av5 zip> --ref <research aw_mid dir>   # port check
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import data_path  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from bdc26.frames import with_nulls  # noqa: E402

AZ, EL, NQ, GAMMA, CLIP, MINPTS, NPOOL, NPT = 10.0, 2.125, 21, 0.5, 10.0, 300, 150, 34500
RECORD = "docs/decisions/2026-11-12-s10-10.2-clean-final-push.md Section 5"
ITEM_A = ("S10-2 V2X A angular mass prior: per (10 x 2.125 deg) bin weights from legal unlabelled realism proxies 1-3 "
          "against 150 synthetic g1-v6 frames, deficits filled with the twin's own non-box points")
ITEM_W = ("S10-2 V2X W range calibration: per-bin range quantiles (21) of legal unlabelled realism proxies 1-3, "
          "points moved along their own rays, box points untouched")
ITEM_N = "S10-2 V2X no-return points stored as (0,0,0) at the sensor's rate (0.31, legal realval) in the training frames"


def in_boxes(P, boxes, margin=0.1):
    m = np.zeros(len(P), bool)
    for x, y, zc, dx, dy, dz, yaw in boxes:
        c, s = np.cos(yaw), np.sin(yaw)
        px, py = P[:, 0] - x, P[:, 1] - y
        lx, ly = c * px + s * py, -s * px + c * py
        m |= (np.abs(lx) <= dx / 2 + margin) & (np.abs(ly) <= dy / 2 + margin) & (P[:, 2] <= zc + dz / 2 + margin)
    return m


def read_boxes(root: Path, fid: str) -> np.ndarray:
    f = root / "labels" / f"{fid}.txt"
    rows = [ln.split()[:7] for ln in f.read_text().splitlines() if ln.strip()] if f.exists() else []
    return np.array(rows, float).reshape(-1, 7)


def nonnull(P):
    return P[~np.all(P == 0, 1)]


def sph(P):
    r3 = np.linalg.norm(P, axis=1)
    return (np.degrees(np.arctan2(P[:, 1], P[:, 0])), np.degrees(np.arcsin(np.clip(P[:, 2] / np.maximum(r3, 1e-9), -1, 1))), r3)


def wbin(az, el):     # the W bins (research qmap.bins)
    ia = np.clip(((az + 180) / AZ).astype(int), 0, int(360 / AZ) - 1)
    ie = np.clip(((el + 17.5) / EL).astype(int), 0, int(np.ceil(34 / EL)) - 1)
    return ia * 100 + ie


def abin(P):          # the A bins (research angw.abin)
    r3 = np.maximum(np.linalg.norm(P, axis=1), 1e-9)
    az, el = np.degrees(np.arctan2(P[:, 1], P[:, 0])), np.degrees(np.arcsin(np.clip(P[:, 2] / r3, -1, 1)))
    na, ne = int(360 / AZ), int(np.ceil(35 / EL))
    return np.clip(((az + 180) / AZ).astype(int), 0, na - 1) * ne + np.clip(((el + 17.5) / EL).astype(int), 0, ne - 1), na * ne


def fit_table(P):
    az, el, r = sph(P)
    b, tab, qs = wbin(az, el), {}, np.linspace(0, 1, NQ)
    for k in np.unique(b):
        m = b == k
        if m.sum() >= MINPTS:
            tab[int(k)] = np.quantile(r[m], qs)
    return tab


def pools(root: Path, exclude: set):
    """The research pools: 150 frames (seed 0), 34,500 valid points each; with boxes (A shares, W) and without (donors)."""
    fs = sorted(root.glob("points/*.npy"))
    fs = [f for f in fs if f.stem not in exclude]
    rng = np.random.default_rng(0)
    pick = rng.choice(len(fs), NPOOL, replace=False)
    full, nobox = [], []
    for i in pick:
        p = nonnull(np.load(fs[i])[:, :3])
        p = p[rng.choice(len(p), NPT, replace=False)]
        bx = read_boxes(root, fs[i].stem)
        full.append(p)
        nobox.append(p[~in_boxes(p.astype(np.float64), bx)] if len(bx) else p)
    return np.concatenate(full), np.concatenate(nobox)


def cmd_fit(a):
    T = load_track(a.track)
    ids = set(Path(a.ids).read_text().split())
    real = []
    for k in (1, 2, 3):
        d = T.root / "pcdet" / f"realism-proxy-{k}" / "points"
        real += [nonnull(np.load(f)[:, :3].astype(np.float32)) for f in sorted(d.glob("*.npy"))]
    Rf = np.concatenate(real)
    Sp, Sd = pools(data_path(T, "pcdet/g1-v6"), ids)
    Ts, Tr = fit_table(Sp), fit_table(Rf)
    keys = np.array(sorted(set(Ts) & set(Tr)))
    br, K = abin(Rf)
    bs, _ = abin(Sp)
    hs = np.bincount(bs, minlength=K) / len(bs)
    bd, _ = abin(Sd)
    hr = np.bincount(br, minlength=K) / len(br)
    w = np.clip((hr + 1e-6) / (hs + 1e-6), 1 / CLIP, CLIP) ** GAMMA
    w[hs < 50 / len(bd)] = 1.0          # as the research code: the threshold counts the donor pool
    out = data_path(T, a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, keys=keys, syn=np.array([Ts[k] for k in keys]), real=np.array([Tr[k] for k in keys]),
                        w=w, donors=Sd.astype(np.float32), donor_bins=bd)
    meta = {"ids_excluded": len(ids), "pool_frames": NPOOL, "real_frames": len(real), "w_bins": int(len(keys)),
            "a_bins": int(K), "donors": int(len(Sd)), "az": AZ, "el": EL, "nq": NQ, "gamma": GAMMA,
            "created": time.strftime("%Y-%m-%d %H:%M"), "record": RECORD}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta))


_C = {}


def _init(tables):
    d = np.load(tables)
    bd = d["donor_bins"]
    order = np.argsort(bd, kind="stable")
    _C.update(Ts={int(k): s for k, s in zip(d["keys"], d["syn"])}, Tr={int(k): r for k, r in zip(d["keys"], d["real"])},
              w=d["w"], Sd=d["donors"], order=order, starts=np.searchsorted(bd[order], np.arange(len(d["w"]) + 1)))


def calib_a(P, boxes, rng):
    """Research angw (--nobox) on one frame: returns the frame and the number of replaced points."""
    w, Sd, order, starts = _C["w"], _C["Sd"], _C["order"], _C["starts"]
    K = len(w)
    P = P.copy()
    nul = np.all(P == 0, 1)
    free = ~nul & ~(in_boxes(P.astype(np.float64), boxes) if len(boxes) else np.zeros(len(P), bool))
    I = np.flatnonzero(free)
    b, _ = abin(P[I].astype(np.float64))
    own = np.bincount(b, minlength=K).astype(float)
    M = len(I)
    t = own * w
    t = t / t.sum() * M
    tb = np.floor(t).astype(int)
    rem = M - tb.sum()
    fr = t - tb
    tb[np.argsort(-fr)[:rem]] += 1
    slots, fills = [], []
    for bb in np.flatnonzero(own > tb):
        slots.append(rng.choice(I[b == bb], int(own[bb] - tb[bb]), replace=False))
    need = np.maximum(tb - own.astype(int), 0)
    for bb in np.flatnonzero(need):
        pool_idx = order[starts[bb]:starts[bb + 1]]
        if len(pool_idx) == 0:          # no donor in this bin (never met on the research frames): leave it
            continue
        fills.append(Sd[rng.choice(pool_idx, need[bb], replace=len(pool_idx) < need[bb])])
    slots = np.concatenate(slots) if slots else np.zeros(0, int)
    fills = np.concatenate(fills) if fills else np.zeros((0, 3))
    n = min(len(slots), len(fills))
    slots = rng.permutation(slots)[:n]
    newp = fills[:n].astype(np.float32)
    okb = ~in_boxes(newp.astype(np.float64), boxes) if len(boxes) else np.ones(n, bool)
    P[slots[okb]] = newp[okb]
    return P, int(okb.sum())


def calib_w(P, boxes):
    """Research qmap.apply (strength 1, no move limit) on one frame."""
    Ts, Tr = _C["Ts"], _C["Tr"]
    P = P.astype(np.float64)
    Q = P.copy()
    m = ~np.all(P == 0, 1)
    if len(boxes):
        m &= ~in_boxes(P, boxes)
    idx = np.flatnonzero(m)
    az, el, r = sph(P[idx])
    b = wbin(az, el)
    rn = r.copy()
    qs = np.linspace(0, 1, NQ)
    for k in np.unique(b):
        if int(k) not in Ts or int(k) not in Tr:
            continue
        s = b == k
        rn[s] = np.interp(np.interp(r[s], Ts[int(k)], qs), qs, Tr[int(k)])
    new = P[idx] * (rn / np.maximum(r, 1e-9))[:, None]
    if len(boxes):
        bad = in_boxes(new, boxes)
        new[bad] = P[idx][bad]
    ok = (np.abs(new[:, 0]) <= 40) & (np.abs(new[:, 1]) <= 40) & (new[:, 2] >= -8) & (new[:, 2] <= 2)
    new[~ok] = P[idx][~ok]
    Q[idx] = new
    return Q.astype(np.float32), float(np.mean(np.abs(rn - r)))


def aw_frame(P50k, boxes, fid: str):
    Q, nrep = calib_a(P50k, boxes, np.random.default_rng([3, int(fid)]))
    Q, mv = calib_w(Q, boxes)
    return Q, nrep, mv


def _one(fid, src, dst, seed, nulls, npts):
    P = np.load(src / "points" / f"{fid}.npy")[:, :3].astype(np.float32)
    P50 = with_nulls(P, nulls, npts, np.random.default_rng([int(seed), int(fid)]))
    Q, nrep, mv = aw_frame(P50, read_boxes(src, fid), fid)
    np.save(dst / "points" / f"{fid}.npy", Q)
    return nrep, mv


def cmd_build(a):
    T = load_track(a.track)
    src, dst = data_path(T, a.src), data_path(T, a.dst)
    if dst.exists():
        raise SystemExit(f"{dst} exists; choose a new corpus name")
    nulls, npts = float(T["resample"]["null_fraction"]), int(T["resample"]["n_points"])
    (dst / "points").mkdir(parents=True)
    shutil.copytree(src / "labels", dst / "labels")
    shutil.copytree(src / "ImageSets", dst / "ImageSets")
    fids = sorted(p.stem for p in (src / "points").glob("*.npy"))
    t0 = time.time()
    with Pool(a.workers, initializer=_init, initargs=(str(data_path(T, a.tables)),)) as pool:
        res = pool.map(partial(_one, src=src, dst=dst, seed=a.seed, nulls=nulls, npts=npts), fids, chunksize=16)
    card = yaml.safe_load((src / "dataset.yaml").read_text())
    card.update({
        "derived_from": a.src,
        "real_data_use": f"{card.get('real_data_use', '')}; {ITEM_A}; {ITEM_W}; {ITEM_N}".lstrip("; "),
        "aw": {"tool": "common/tools/s10_2_aw.py", "tables": a.tables,
               "tables_md5": hashlib.md5(data_path(T, a.tables).read_bytes()).hexdigest(),
               "az": AZ, "el": EL, "nq": NQ, "gamma": GAMMA, "null_fraction": nulls, "n_points": npts, "seed": a.seed,
               "replaced_per_frame_mean": round(float(np.mean([r for r, _ in res])), 1),
               "mean_abs_range_move_m": round(float(np.mean([m for _, m in res])), 3), "record": RECORD},
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "git_sha": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                  cwd=Path(__file__).resolve().parent).stdout.strip(),
        "n_frames": len(fids),
    })
    (dst / "dataset.yaml").write_text(yaml.safe_dump(card, sort_keys=False, width=120))
    print(json.dumps({"dst": str(dst), "frames": len(fids), **{k: card["aw"][k] for k in ("replaced_per_frame_mean", "mean_abs_range_move_m")},
                      "wall_s": round(time.time() - t0, 1)}))
    print(f"next: python common/tools/pcdet_build_infos.py <member> --data {a.dst}")


def cmd_check(a):
    """Port check: the research aw_mid frames from the c1av5 zip's own frames (their nulls as packaged)."""
    T = load_track(a.track)
    _init(str(data_path(T, a.tables)))
    root = data_path(T, "pcdet/g1-v6")
    ids = Path(a.ids).read_text().split()
    with zipfile.ZipFile(a.zip) as zf:
        names = sorted(x for x in zf.namelist() if x.startswith("synthetic/") and x.endswith(".bin"))
        frames = [np.frombuffer(zf.read(x), dtype=np.float32).reshape(-1, 3).copy() for x in names]
    same = 0
    for P, fid, nm in zip(frames, ids, names):
        Q, _, _ = aw_frame(P, read_boxes(root, fid), fid)
        R = np.fromfile(Path(a.ref) / Path(nm).name, dtype=np.float32).reshape(-1, 3)
        same += bool(np.array_equal(Q, R))
    print(f"byte-identical to the research frames: {same} of {len(frames)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit")
    f.add_argument("track")
    f.add_argument("--ids", required=True)
    f.add_argument("--out", required=True)
    b = sub.add_parser("build")
    b.add_argument("track")
    b.add_argument("src")
    b.add_argument("dst")
    b.add_argument("--tables", required=True)
    b.add_argument("--seed", type=int, default=1234)
    b.add_argument("--workers", type=int, default=48)
    c = sub.add_parser("check")
    c.add_argument("track")
    c.add_argument("--tables", required=True)
    c.add_argument("--ids", required=True)
    c.add_argument("--zip", required=True)
    c.add_argument("--ref", required=True)
    a = ap.parse_args()
    if load_track(a.track).name != "v2x-track":
        raise SystemExit("aw is the V2X calibration")
    {"fit": cmd_fit, "build": cmd_build, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    main()
