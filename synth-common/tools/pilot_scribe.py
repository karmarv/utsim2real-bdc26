#!/usr/bin/env python
"""Pilot P0 for the scribe paper (synth-docs/RESEARCH-AGENDA.md Section 13): is there a labelling (scribe) gap between
the real dataset and our synthetic corpus, and do LUMPI's five unsynchronized sensors smear moving objects?

Read-only, CPU only. Real data: realval-A only (pcdet/realval-v1/ImageSets/val.txt; LUMPI: Measurement4 labels read
through the guard with bdc26.io.lumpi.read_labels_guarded; V2X: the prepared labels, frames passed through the guard);
statistics only, nothing is trained. Synthetic data: a prepared corpus (default g1-v5). Measures (both tracks unless noted):
  visibility  share of boxes by points at 50k (0, 1-2, 3-5, 6-10, 11-30, >30), per class and range band, real vs synthetic
  fill        point extent / box size along l, w, h, and the gaps (m) between the box bottom / top and the lowest /
              highest point, for boxes with >= MIN_FILL points at 50k, real vs synthetic
  regimes     LUMPI real only: the same by the manual flag (score == 4: manually corrected)
  tracks      LUMPI real only: within-track vs between-track sd of l, w, h (one object id = one rigid object)
  timing      LUMPI real only, raw PLY: per moving object and pair of sensors, displacement of the sensor's points along
              the heading against speed x time difference; the reference time of the label inside the 100 ms sweep

    python synth-common/tools/pilot_scribe.py --track lumpi-track --out synth-lumpi-track/experiments/P0-scribe-pilot/results.json
    python synth-common/tools/pilot_scribe.py --track v2x-track --out synth-v2x-track/experiments/P0-scribe-pilot/results.json
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "common"))
from bdc26.boxes import boxes_center_in_range, points_in_boxes  # noqa: E402
from bdc26.classmap import map_lumpi_ids  # noqa: E402
from bdc26.config import load_track  # noqa: E402
from bdc26.guard import ForbiddenGuard  # noqa: E402
from bdc26.io import lumpi  # noqa: E402

T = None                                    # set in main() from --track
PURPOSE = "synth pilot P0: label and point statistics of realval-A (no training)"
TRACK_CLASSES = {"lumpi-track": ["Person", "Car", "Bicycle", "Motorcycle", "Bus", "Truck", "Van"],
                 "v2x-track": ["vehicle", "pedestrian", "truck"]}
CLASSES: list[str] = []
RANGES = [(0, 15), (15, 30), (30, 57)]
VIS_BINS = [0, 1, 3, 6, 11, 31, 10**9]
VIS_NAMES = ["0", "1-2", "3-5", "6-10", "11-30", ">30"]
MIN_FILL = 15


def range_band(boxes):
    d = np.hypot(boxes[:, 0], boxes[:, 1])
    return np.digitize(d, [r[1] for r in RANGES[:-1]])


def box_local(points, box):
    d = points[:, :3] - box[:3]
    c, s = np.cos(-box[6]), np.sin(-box[6])
    return np.stack([c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1], d[:, 2]], axis=1)


def frame_stats(points, boxes, names, acc, extra=None):
    """Points per box (visibility) and fill ratios, accumulated per (class, range band[, extra])."""
    idx = points_in_boxes(points, boxes)
    counts = np.bincount(idx[idx >= 0], minlength=len(boxes))
    bands = range_band(boxes)
    for i, (n, name) in enumerate(zip(counts, names)):
        if name not in CLASSES:
            continue
        key = (name, int(bands[i])) + ((extra[i],) if extra is not None else ())
        acc["count"][key].append(int(n))
        acc["size"][key].append(boxes[i, 3:6].tolist())
        if n >= MIN_FILL:
            loc = box_local(points[idx == i], boxes[i])
            ext = loc.max(0) - loc.min(0)
            mid = (loc.max(0) + loc.min(0)) / 2
            acc["fill"][key].append((ext / boxes[i, 3:6]).tolist())
            acc["offset"][key].append((mid / boxes[i, 3:6]).tolist())
            acc["gap"][key].append([float(loc[:, 2].min() + boxes[i, 5] / 2), float(boxes[i, 5] / 2 - loc[:, 2].max())])


def summarize(acc):
    out = {}
    for key in sorted(acc["count"]):
        c = np.array(acc["count"][key])
        hist = np.histogram(c, bins=VIS_BINS)[0] / max(len(c), 1)
        f = np.array(acc["fill"].get(key, []), dtype=float).reshape(-1, 3)
        o = np.array(acc["offset"].get(key, []), dtype=float).reshape(-1, 3)
        sz = np.array(acc["size"][key], dtype=float).reshape(-1, 3)
        g = np.array(acc["gap"].get(key, []), dtype=float).reshape(-1, 2)
        out["|".join(map(str, key))] = {
            "n": int(len(c)), "points_median": float(np.median(c)),
            "visibility": dict(zip(VIS_NAMES, np.round(hist, 4).tolist())),
            "n_fill": int(len(f)),
            "fill_median_lwh": np.round(np.median(f, 0), 3).tolist() if len(f) else None,
            "fill_p90_lwh": np.round(np.percentile(f, 90, 0), 3).tolist() if len(f) else None,
            "offset_median_lwh": np.round(np.median(o, 0), 3).tolist() if len(o) else None,
            "bottom_top_gap_median_m": np.round(np.median(g, 0), 3).tolist() if len(g) else None,
            "size_median_lwh": np.round(np.median(sz, 0), 3).tolist(),
        }
    return out


def new_acc():
    return {"count": defaultdict(list), "fill": defaultdict(list), "offset": defaultdict(list), "size": defaultdict(list),
            "gap": defaultdict(list)}


def real_side_v2x(guard, ids_a):
    """V2X: the prepared realval-A frames (labels already mapped to the challenge classes), through the guard."""
    keys = [(i.rsplit("__", 1)[0], int(i.rsplit("__", 1)[1])) for i in ids_a]
    allowed = set(guard.filter(keys, PURPOSE))
    d = T.pcdet / "realval-v1"
    acc = new_acc()
    for i, k in zip(ids_a, keys):
        if k not in allowed:
            continue
        rows = [l.split() for l in (d / "labels" / f"{i}.txt").read_text().splitlines() if l.strip()]
        if not rows:
            continue
        boxes = np.array([[float(x) for x in r[:7]] for r in rows])
        names = np.array([r[7] for r in rows], dtype=object)
        frame_stats(np.load(d / "points" / f"{i}.npy"), boxes, names, acc)
    return summarize(acc), len(allowed)


def real_side(guard, frames_a, timing_frames, rng):
    lab = lumpi.read_labels_guarded(T.real / "labels" / "Measurement4_Label.guarded.csv", "Measurement4", guard, PURPOSE)
    names_all = map_lumpi_ids(lab.class_id, T)
    in_a = np.isin(lab.frame, frames_a)
    acc, acc_flag = new_acc(), new_acc()
    pts_dir = T.pcdet / "realval-v1" / "points"
    by_frame = defaultdict(list)
    for k in np.flatnonzero(in_a):
        by_frame[int(lab.frame[k])].append(k)
    for f in frames_a:
        rows = np.array(by_frame.get(int(f), []), dtype=int)
        if len(rows) == 0:
            continue
        boxes = lab.boxes[rows]
        keep = boxes_center_in_range(boxes, T.pc_range)
        rows, boxes = rows[keep], boxes[keep]
        pts = np.load(pts_dir / f"Measurement4__{int(f):06d}.npy")
        frame_stats(pts, boxes, names_all[rows], acc)
        flag = np.where(lab.score[rows] == 4, "manual", "auto")
        frame_stats(pts, boxes, names_all[rows], acc_flag, extra=flag)
    # tracks: within-object vs between-object size spread (realval-A frames only)
    tracks = {}
    for cname in ["Car", "Van", "Truck", "Bus", "Person", "Bicycle"]:
        m = in_a & (names_all == cname)
        ids = lab.object_id[m]
        dims = lab.boxes[m, 3:6]
        within, means = [], []
        for oid in np.unique(ids):
            d = dims[ids == oid]
            if len(d) >= 5:
                within.append(d.std(0))
                means.append(d.mean(0))
        if means:
            tracks[cname] = {"n_tracks": len(means), "within_sd_lwh": np.round(np.median(within, 0), 3).tolist(),
                             "between_sd_lwh": np.round(np.std(means, 0), 3).tolist(),
                             "share_tracks_size_changes": float(np.mean(np.max(within, 1) > 0.05))}
    timing = timing_side(guard, lab, names_all, frames_a, timing_frames, rng)
    return summarize(acc), summarize(acc_flag), tracks, timing


def timing_side(guard, lab, names_all, frames_a, n_frames, rng):
    """Multi-sensor timing on raw PLY frames (full density, per-point time and sensor id)."""
    raw = T.real / "raw" / "Measurement4" / "lidar"
    cand = [int(f) for f in frames_a if (raw / f"{int(f):06d}.ply").exists()]
    pick = sorted(rng.choice(cand, size=min(n_frames, len(cand)), replace=False).tolist()) if cand else []
    pos = {(int(f), int(o)): b for f, o, b in zip(lab.frame, lab.object_id, lab.boxes)}
    pairs, per_sensor, span = [], [], []
    for f in pick:
        guard.check("Measurement4", f, PURPOSE)
        v = lumpi.read_ply(raw / f"{f:06d}.ply")
        xyz = lumpi.ply_xyz(v)
        t_us = v["time"].astype(np.int64) - f * 100_000
        sid = v["id"].astype(np.int64)
        rows = np.flatnonzero((lab.frame == f) & np.isin(names_all, ["Car", "Van", "Truck", "Bus"]))
        if len(rows) == 0:
            continue
        boxes = lab.boxes[rows]
        idx = points_in_boxes(xyz, boxes, margin=0.3)
        for j, r in enumerate(rows):
            o = int(lab.object_id[r])
            a, b = pos.get((f - 1, o)), pos.get((f + 1, o))
            if a is None or b is None:
                continue
            vel = (b[:2] - a[:2]) / 0.2
            head = np.array([np.cos(boxes[j, 6]), np.sin(boxes[j, 6])])
            v_h = float(vel @ head)
            m = idx == j
            stats = []
            for s in np.unique(sid[m]):
                ms = m & (sid == s)
                if ms.sum() < 8:
                    continue
                u = float(((xyz[ms, :2] - boxes[j, :2]) @ head).mean())
                t = float(t_us[ms].mean()) / 1e6
                stats.append((int(s), t, u))
                per_sensor.append((v_h, t, u))
            if len(stats) >= 2:
                ts = [x[1] for x in stats]
                span.append((abs(v_h), max(ts) - min(ts)))
            for p in range(len(stats)):
                for q in range(p + 1, len(stats)):
                    dt = stats[p][1] - stats[q][1]
                    pairs.append((v_h, dt, stats[p][2] - stats[q][2]))
    out = {"frames": len(pick), "pairs": len(pairs)}
    if pairs:
        P = np.array(pairs)
        mov = np.abs(P[:, 0]) > 1.5
        sta = np.abs(P[:, 0]) < 0.3
        pred, du = P[:, 0] * P[:, 1], P[:, 2]
        if mov.sum() > 10:
            A = np.stack([pred[mov], np.ones(mov.sum())], 1)
            coef, *_ = np.linalg.lstsq(A, du[mov], rcond=None)
            r = np.corrcoef(pred[mov], du[mov])[0, 1]
            out["moving"] = {"pairs": int(mov.sum()), "slope_du_on_v_dt": round(float(coef[0]), 3), "corr": round(float(r), 3),
                             "median_abs_dt_ms": round(float(np.median(np.abs(P[mov, 1]))) * 1e3, 1),
                             "median_abs_v_dt_m": round(float(np.median(np.abs(pred[mov]))), 3),
                             "p90_abs_v_dt_m": round(float(np.percentile(np.abs(pred[mov]), 90)), 3),
                             "median_abs_du_m": round(float(np.median(np.abs(du[mov]))), 3)}
        if sta.sum() > 10:
            out["static"] = {"pairs": int(sta.sum()), "median_abs_dt_ms": round(float(np.median(np.abs(P[sta, 1]))) * 1e3, 1),
                             "median_abs_du_m": round(float(np.median(np.abs(du[sta]))), 3)}
    if per_sensor:
        S = np.array(per_sensor)
        mov = np.abs(S[:, 0]) > 1.5
        if mov.sum() > 10:     # u = v (t - tau) + c  ->  regress u on [v t, v, 1]; tau = -coef[1]
            A = np.stack([S[mov, 0] * S[mov, 1], S[mov, 0], np.ones(mov.sum())], 1)
            coef, *_ = np.linalg.lstsq(A, S[mov, 2], rcond=None)
            out["label_reference_time_ms"] = round(float(-coef[1]) * 1e3, 1)
            out["label_reference_slope"] = round(float(coef[0]), 3)
    if span:
        sp = np.array(span)
        mv = sp[:, 0] > 1.5
        out["sensor_time_span_ms_median"] = round(float(np.median(sp[:, 1])) * 1e3, 1)
        if mv.any():
            out["moving_smear_m_median"] = round(float(np.median(sp[mv, 0] * sp[mv, 1])), 3)
            out["moving_smear_m_p90"] = round(float(np.percentile(sp[mv, 0] * sp[mv, 1], 90)), 3)
    return out


def synth_side(corpus, n_frames, rng):
    d = T.pcdet / corpus
    files = sorted((d / "labels").glob("*.txt"))
    pick = rng.choice(len(files), size=min(n_frames, len(files)), replace=False)
    acc = new_acc()
    for k in sorted(pick):
        lf = files[k]
        rows = [l.split() for l in lf.read_text().splitlines() if l.strip()]
        if not rows:
            continue
        boxes = np.array([[float(x) for x in r[:7]] for r in rows])
        names = np.array([r[7] for r in rows], dtype=object)
        pts = np.load(d / "points" / (lf.stem + ".npy"))
        frame_stats(pts, boxes, names, acc)
    return summarize(acc)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", default="lumpi-track", choices=sorted(TRACK_CLASSES))
    ap.add_argument("--corpus", default="g1-v5")
    ap.add_argument("--synth-frames", type=int, default=1280)
    ap.add_argument("--timing-frames", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    global T
    T = load_track(a.track)
    CLASSES[:] = TRACK_CLASSES[a.track]
    rng = np.random.default_rng(a.seed)
    guard = ForbiddenGuard.for_track(T)
    ids = (T.pcdet / "realval-v1" / "ImageSets" / "val.txt").read_text().split()
    res = {"track": a.track, "corpus": a.corpus, "classes": CLASSES, "range_bands_m": RANGES, "min_points_for_fill": MIN_FILL}
    if a.track == "lumpi-track":
        frames_a = np.array(sorted(int(s.split("__")[1]) for s in ids if s.startswith("Measurement4__")))
        real, real_flag, tracks, timing = real_side(guard, frames_a, a.timing_frames, rng)
        res.update({"real": "realval-A (Measurement4, %d frames)" % len(frames_a), "real_stats": real,
                    "real_by_manual_flag": real_flag, "real_tracks": tracks, "real_timing": timing})
    else:
        real, n = real_side_v2x(guard, ids)
        timing, tracks = {}, {}
        res.update({"real": "realval-A (%d frames)" % n, "real_stats": real})
    res["synth_stats"] = synth_side(a.corpus, a.synth_frames, rng)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({"timing": timing, "tracks": tracks}, indent=1))


if __name__ == "__main__":
    main()
