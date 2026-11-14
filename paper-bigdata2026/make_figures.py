#!/usr/bin/env python
"""Figures of the two track reports (report_lumpi.md, report_v2x.md), made from the repository's records and legal data.

    source common/env/activate.sh && python paper-bigdata2026/make_figures.py [--track lumpi v2x] [--only NAME ...]

Every figure reads committed records (codabench_<id>.json, the routed validation outputs, the decision records' tables,
which are copied below as constants with their source) or legal real-validation and synthetic frames under $BDC_DATA.
No test frame of the starting kit is read. Output: paper-bigdata2026/figures/fig_<track>_<name>.png at 300 dpi, sized
for the IEEE columns (3.45 in) or the full text width (7.1 in).
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates  # noqa: E402
import matplotlib.ticker  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "common"))
from bdc26.evalap import iou_matrix  # noqa: E402

DATA = Path(os.environ.get("BDC_DATA", REPO.parent / "bdc26-data"))
OUT = HERE / "figures"
COL, WIDE = 3.45, 7.1

# reference categorical palette (dataviz skill, light mode), fixed order; text in ink, never in series colour
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
INK, INK2, GRID, PTS = "#0b0b0b", "#52514e", "#d9d8d4", "#9a9994"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"], "font.size": 7,
    "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.4, "axes.axisbelow": True, "lines.linewidth": 1.2,
    "savefig.dpi": 300, "figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
})

TRACKS = {16684: "lumpi", 16685: "v2x"}
NAME = {"lumpi": "LUMPI", "v2x": "V2X-Real"}
CLASSES = {"lumpi": ["Person", "Car", "Bicycle", "Motorcycle", "Bus", "Truck", "Van"],
           "v2x": ["vehicle", "pedestrian", "truck"]}
FIRST_QUALIFYING = {"lumpi": 1042287, "v2x": 1042294}     # organizers' ruling of 2026-11-09
FRAMES_RULE_FAIL = {1047204, 1047231}                     # organizers' ruling of 2026-11-12
ENTRY = {"lumpi": 1051832, "v2x": 1051825}                # best qualifying upload per track (release 10.4)
FINAL_CARD = {"lumpi": ("routed-s10-4-l8", "2026-11-13_s10-4-l8"), "v2x": ("routed-s10-4-v4", "2026-11-13_s10-4-v4")}


def save(fig, t, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"fig_{t}_{name}.png"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", path)


def track_dir(t):
    return REPO / f"model-{t}-track"


# ------------------------------------------------------------------------------------------------------------------
# records
# ------------------------------------------------------------------------------------------------------------------
def submissions():
    """Every scored upload with its official scores and its status under the organizers' rulings."""
    rows = []
    for f in glob.glob(str(REPO / "model-*-track/*/submissions/*/codabench_*.json")):
        d = json.load(open(f))
        t = TRACKS[d["codabench_competition"]]
        sid = int(d["codabench_submission_id"])
        m = re.search(r"2026-\d\d-\d\d", str(d.get("submitted", "")))
        phase = "final" if str(d.get("phase", "")).lower().startswith("final") else "development"
        if phase == "development":
            status = "development"
        elif sid in FRAMES_RULE_FAIL:
            status = "frames rule"
        elif sid < FIRST_QUALIFYING[t]:
            status = "removed"
        else:
            status = "qualifying"
        rows.append({"track": t, "id": sid, "date": m.group(0) if m else None, "phase": phase, "status": status,
                     "model": Path(f).parts[-4], "scores": d["scores"]})
    return sorted(rows, key=lambda r: r["id"])


# ------------------------------------------------------------------------------------------------------------------
# Fig: the system as two stacks and their checks
# ------------------------------------------------------------------------------------------------------------------
# The iterations (release tags) with their named approaches; Fig. 1 timeline, Fig. 4 labels, Table IV.
ITERATIONS = [("1", "Calibrated Twin", "I"), ("2", "Center-Routed", "I"), ("3", "Fused Portfolio", "I"),
              ("4", "Two-Stage", "I"), ("5", "Size-Aware", "I"), ("5.1", "Re-cast Twin", "I"),
              ("5.2", "Realism-Led", "I"), ("6", "Seed Bags", "I"), ("7", "Visibility Rule", "I"),
              ("8", "Twelve-View", "I"), ("9", "Label-Free Twin", "II"), ("10", "Clean Final", "III")]
NOT_ADOPTED = {"2"}

PIPE = {
    "lumpi": {
        "gen": [("UT-LUMPI CARLA twin, 10k frames", "base"),
                ("5-lidar rig: 50,000 points, beam tables", "1"),
                ("actor scale 1/0.78; 19 real size quantiles", "1, 5.1"),
                ("walkers (16 per frame), riders, scene map", "1, 9"),
                ("Car, Van, Truck, Bus re-cast at real size", "5.1"),
                ("clutter: poles, trees, hedges, fences, walls", "5.1"),
                ("background density prior, 8 x 8 x 2.5 m", "5.2"),
                ("CompleteTwin: label-free draws of 10k frames", "9, 10")],
        "det": [("trained on CompleteTwin only, from scratch", "1, 10"),
                ("13 members, PointPillars to DSVT-Pillar", "1, 4, 9"),
                ("object scaling; sampling off (rosf, rosn)", "5, 9"),
                ("seed bags and generator-draw bags", "6, 7"),
                ("8- or 12-view test-time augmentation", "3, 8, 10"),
                ("per-class routes, fusion of up to 3 members", "3, 9"),
                ("floors, low-score and cross-class copies", "3, 8, 10"),
                ("anchored sizes; Person, Bicycle, Car steps", "9, 10")],
        "groups": "28 windows of 100 s",
        "split": "realval-A, realval-B,",
        "split2": "late-A; realism proxies 1-5",
    },
    "v2x": {
        "gen": [("UT-V2X-Real-IC CARLA twin, 10k frames", "base"),
                ("OS1-64 beam table, field of view, 35k points", "1"),
                ("19 real size quantiles; trucks at real length", "5.1"),
                ("walkers (16 per frame), riders, scene map", "1, 9"),
                ("vehicles and trucks re-cast at real size", "5.1"),
                ("clutter: poles, trees, bollards, bins", "5.1"),
                ("background density prior, 8 x 8 x 2.5 m", "5.2"),
                ("CompleteTwin: 5 label-free draws, 10k each", "9, 10")],
        "det": [("trained on CompleteTwin only, from scratch", "1, 10"),
                ("6 members: Voxel R-CNN and DSVT-Pillar", "1, 4, 9"),
                ("object scaling to the real size ceiling", "5"),
                ("seed bags; generator-draw bags (truck: 5)", "6, 10"),
                ("8- or 12-view test-time augmentation", "3, 8"),
                ("per-class routes, cross-architecture fusion", "3, 10"),
                ("visibility ranking, overhead demotion", "7, 10"),
                ("anchored sizes; pedestrian, vehicle steps", "9, 10")],
        "groups": "57 scenes",
        "split": "realval-A, realval-B",
        "split2": "(disjoint scenes); proxies 1-5",
    },
}


def fig_pipeline(t, subs):
    """Two stacks (generator, detector system) beside the evaluation and rule checks, over the iteration timeline."""
    cfg = PIPE[t]
    fig, ax = plt.subplots(figsize=(WIDE, 3.45))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52.8)
    ax.axis("off")
    lh, lg, y0 = 3.55, 0.62, 11.2                       # layer height, gap, first layer bottom

    def layer(x, w, k, text, tag, col, alpha, bold=False):
        y = y0 + k * (lh + lg)
        ax.add_patch(FancyBboxPatch((x, y), w, lh, boxstyle="round,pad=0.0,rounding_size=0.7", linewidth=0.7,
                                    edgecolor=col, facecolor=matplotlib.colors.to_rgba(col, alpha)))
        ax.text(x + 1.0, y + lh / 2, text, ha="left", va="center", fontsize=5.3, color=INK,
                fontweight="bold" if bold else "normal")
        if tag:
            tw = 0.62 * len(tag) + 1.6
            ax.add_patch(FancyBboxPatch((x + w - tw - 0.6, y + 0.65), tw, lh - 1.3,
                                        boxstyle="round,pad=0.0,rounding_size=0.6", linewidth=0.45,
                                        edgecolor=INK2, facecolor="white"))
            ax.text(x + w - tw / 2 - 0.6, y + lh / 2, tag, ha="center", va="center", fontsize=4.6, color=INK2)
        return y

    gen, det = cfg["gen"], cfg["det"]
    xg, xd, w = 0.8, 37.4, 32.6
    for k, (txt, tag) in enumerate(gen):
        layer(xg, w, k, txt, tag, C1, 0.06 + 0.035 * k, bold=(k == len(gen) - 1))
    for k, (txt, tag) in enumerate(det):
        layer(xd, w, k, txt, tag, C2, 0.06 + 0.035 * k)
    top = y0 + len(gen) * (lh + lg) - lg                 # top of both stacks
    for x, title, col in [(xg, "A. Synthetic generator stack", C1), (xd, "B. Detector system stack", C2)]:
        ax.text(x + w / 2, y0 - 1.6, title, ha="center", va="center", fontsize=6.6, fontweight="bold", color=INK)
        ax.plot([x, x + w], [y0 - 0.55, y0 - 0.55], color=col, linewidth=1.6, solid_capstyle="butt")
    # outputs on top of each stack
    cap_y, cap_h = top + 0.9, 2.9
    frames = "50 realism frames from the training corpus" if t == "lumpi" else "50 training frames + (0,0,0) at 0.309"
    for x, txt, col in [(xg, frames, C1), (xd, "boxes for the 50 real test frames", C2)]:
        ax.add_patch(FancyBboxPatch((x + 2.0, cap_y), w - 4.0, cap_h, boxstyle="round,pad=0.0,rounding_size=0.7",
                                    linewidth=0.7, edgecolor=col, facecolor="white", linestyle=(0, (3, 1.5))))
        ax.text(x + w / 2, cap_y + cap_h / 2, txt, ha="center", va="center", fontsize=5.5, color=INK)
        ax.add_patch(FancyArrowPatch((x + w / 2, top + 0.05), (x + w / 2, cap_y - 0.05), arrowstyle="-|>",
                                     mutation_scale=5, linewidth=0.7, color=col))
    # training corpora: from the generator's top layer down the gap into the detector's base
    xa = (xg + w + xd) / 2
    yt = y0 + (len(gen) - 1) * (lh + lg) + lh / 2
    yb = y0 + lh / 2
    ax.plot([xg + w, xa], [yt, yt], color=C1, linewidth=0.9)
    ax.plot([xa, xa], [yt, yb], color=C1, linewidth=0.9)
    ax.add_patch(FancyArrowPatch((xa, yb), (xd - 0.1, yb), arrowstyle="-|>", mutation_scale=6, linewidth=0.9, color=C1))
    ax.text(xa - 0.55, (yt + yb) / 2, "training corpora", rotation=90, ha="center", va="center", fontsize=5.2,
            color=INK2, bbox=dict(facecolor="white", edgecolor="none", pad=0.4))
    # C. evaluation and rule checks: legal validation at the base, then gates and checks, the hidden test at the top
    xe, we = 74.0, 25.2
    checks = [("legal real frames: " + cfg["split"], cfg["split2"], 0.10),
              ("class gate: pooled A+B frames,", "paired bootstrap P(gain) >= 0.9", 0.10),
              ("upload gate: grouped bootstrap", "over " + cfg["groups"], 0.10),
              ("rule 1: no real label row in", "any member's training data", 0.16),
              ("rule 1b: frames from the", "shipped members' training corpus", 0.16),
              ("kit check under 1,200 s,", "upload audit, disclosure", 0.10)]
    eh, eg = 4.35, 0.78
    for k, (a, b, al) in enumerate(checks):
        y = y0 + k * (eh + eg)
        ax.add_patch(FancyBboxPatch((xe, y), we, eh, boxstyle="round,pad=0.0,rounding_size=0.7", linewidth=0.7,
                                    edgecolor=C3, facecolor=matplotlib.colors.to_rgba(C3, al)))
        ax.text(xe + we / 2, y + eh / 2 + 0.9, a, ha="center", va="center", fontsize=5.4, color=INK)
        ax.text(xe + we / 2, y + eh / 2 - 0.95, b, ha="center", va="center", fontsize=5.4, color=INK)
        if k:
            ax.add_patch(FancyArrowPatch((xe + we / 2, y - eg + 0.05), (xe + we / 2, y - 0.05), arrowstyle="-|>",
                                         mutation_scale=4.5, linewidth=0.6, color=C3))
    yt_box = y0 + len(checks) * (eh + eg)
    ht = 52.3 - yt_box
    ax.add_patch(FancyArrowPatch((xe + we / 2, yt_box - eg + 0.05), (xe + we / 2, yt_box - 0.05), arrowstyle="-|>",
                                 mutation_scale=4.5, linewidth=0.6, color=C3))
    ax.add_patch(FancyBboxPatch((xe, yt_box), we, ht, boxstyle="round,pad=0.0,rounding_size=0.7", linewidth=0.9,
                                edgecolor=C3, facecolor=matplotlib.colors.to_rgba(C3, 0.38)))
    ax.text(xe + we / 2, yt_box + ht / 2 + 0.95, f"CodaBench hidden test ({NAME[t]})", ha="center", va="center",
            fontsize=5.9, fontweight="bold", color=INK)
    ax.text(xe + we / 2, yt_box + ht / 2 - 1.0, "50 test + 50 realism frames", ha="center", va="center",
            fontsize=5.4, color=INK)
    ax.text(xe + we / 2, y0 - 1.6, "C. Evaluation and rule checks", ha="center", va="center", fontsize=6.6,
            fontweight="bold", color=INK)
    ax.plot([xe, xe + we], [y0 - 0.55, y0 - 0.55], color=C3, linewidth=1.6, solid_capstyle="butt")
    # both outputs go to the hidden test, through the checks; the server score confirms only
    yl = 51.3
    ax.plot([xg + w / 2, xg + w / 2], [cap_y + cap_h, yl], color=C1, linewidth=0.8)
    ax.add_patch(FancyArrowPatch((xg + w / 2, yl), (xe - 0.1, yl), arrowstyle="-|>", mutation_scale=6,
                                 linewidth=0.8, color=C1))
    ax.plot([xd + w / 2, xd + w / 2], [cap_y + cap_h, yl - 2.2], color=C2, linewidth=0.8)
    ax.add_patch(FancyArrowPatch((xd + w / 2, yl - 2.2), (xe - 0.1, yl - 2.2), arrowstyle="-|>", mutation_scale=6,
                                 linewidth=0.8, color=C2))
    # feedback lane: validation sets scalars only
    yf = 6.35
    ax.plot([xe + we / 2, xe + we / 2], [y0 - 2.8, yf], color=INK2, linewidth=0.7, linestyle=(0, (3, 2)))
    ax.plot([xg + w / 2, xe + we / 2], [yf, yf], color=INK2, linewidth=0.7, linestyle=(0, (3, 2)))
    for x in (xg + w / 2, xd + w / 2):
        ax.add_patch(FancyArrowPatch((x, yf), (x, y0 - 2.8), arrowstyle="-|>", mutation_scale=5, linewidth=0.7,
                                     color=INK2))
    ax.text(45.0, yf - 1.45, "legal validation and label statistics set scalars only (sizes, densities, frame "
            "choice, routes, floors, offsets); no real frame, label or point enters training",
            ha="center", va="center", fontsize=5.0, color=INK2, style="italic")
    # iteration timeline (release tags); the tags in the stacks refer to it
    yi, hi = 0.25, 3.7
    names = list(ITERATIONS)
    wts = [max(len(n2), 9) + 2.5 for _, n2, _ in names]
    gap = 0.55
    scale = (99.2 - 0.8 - gap * (len(names) - 1)) / sum(wts)
    x = 0.8
    for (n, n2, ph), wt in zip(names, wts):
        cw = wt * scale
        face = {"I": matplotlib.colors.to_rgba(INK2, 0.07), "II": matplotlib.colors.to_rgba(INK2, 0.16),
                "III": matplotlib.colors.to_rgba(INK2, 0.28)}[ph]
        ax.add_patch(FancyBboxPatch((x, yi), cw, hi, boxstyle="round,pad=0.0,rounding_size=0.7", linewidth=0.55,
                                    edgecolor=INK2, facecolor="white" if n in NOT_ADOPTED else face,
                                    linestyle=(0, (2, 1.2)) if n in NOT_ADOPTED else "-"))
        ax.text(x + cw / 2, yi + hi / 2 + 0.85, n, ha="center", va="center", fontsize=5.4, fontweight="bold", color=INK)
        ax.text(x + cw / 2, yi + hi / 2 - 0.85, n2, ha="center", va="center", fontsize=4.8, color=INK)
        if n != names[-1][0]:
            ax.add_patch(FancyArrowPatch((x + cw + 0.02, yi + hi / 2), (x + cw + gap - 0.02, yi + hi / 2),
                                         arrowstyle="-|>", mutation_scale=3.5, linewidth=0.5, color=INK2))
        x += cw + gap
    save(fig, t, "pipeline")


# ------------------------------------------------------------------------------------------------------------------
# BEV helpers
# ------------------------------------------------------------------------------------------------------------------
GROUP = {"Person": "walker", "pedestrian": "walker", "Bicycle": "two-wheeler", "Motorcycle": "two-wheeler",
         "Car": "vehicle", "vehicle": "vehicle", "Van": "vehicle", "Truck": "large", "Bus": "large", "truck": "large"}
GROUP_COLOR = {"walker": C2, "two-wheeler": C4, "vehicle": C1, "large": C3}


def corners(b):
    x, y, _, l, w, _, yaw = b[:7]
    c, s = np.cos(yaw), np.sin(yaw)
    pts = np.array([[l / 2, w / 2], [l / 2, -w / 2], [-l / 2, -w / 2], [-l / 2, w / 2]])
    return pts @ np.array([[c, s], [-s, c]]) + [x, y]


def read_labels(path):
    rows = [l.split() for l in Path(path).read_text().splitlines() if l.strip()]
    return np.array([[float(v) for v in r[:7]] for r in rows]).reshape(-1, 7), [r[7] for r in rows]


def bev(ax, pts, rng=40.0, size=0.04):
    m = (np.abs(pts[:, 0]) <= rng) & (np.abs(pts[:, 1]) <= rng) & np.any(pts != 0, axis=1)
    ax.scatter(pts[m, 0], pts[m, 1], s=size, c=PTS, linewidths=0, rasterized=True)
    ax.set_xlim(-rng, rng)
    ax.set_ylim(-rng, rng)
    ax.set_aspect("equal")
    ax.grid(False)
    ax.tick_params(length=2, pad=1)


def draw_boxes(ax, boxes, names, lw=0.6, style="-", color=None):
    for b, n in zip(boxes, names):
        col = color or GROUP_COLOR.get(GROUP.get(n, "vehicle"))
        ax.add_patch(Polygon(corners(b), closed=True, fill=False, edgecolor=col, linewidth=lw, linestyle=style))


def synthetic_ids(t):
    card, sub = FINAL_CARD[t]
    return (track_dir(t) / card / "submissions" / sub / "synthetic_ids.txt").read_text().split()


def real_frame(t):
    root = DATA / f"{t}-track" / "pcdet" / "realval-v1"
    return "Measurement4__003000" if t == "lumpi" else (root / "ImageSets" / "val.txt").read_text().split()[120]


def fig_frames(t, subs):
    """The released twin frame, the same frame completed (CompleteTwin, one of the 50 submitted), and a real frame."""
    pc = DATA / f"{t}-track" / "pcdet"
    sid = synthetic_ids(t)[0]
    rid = real_frame(t)
    panels = [(f"(a) released UrbanTwin, frame {sid}", pc / "ut-v1", sid),
              (f"(b) the same frame in CompleteTwin (submitted)", pc / "g1-v6", sid),
              ("(c) real, realval-A" + (f" frame {rid.split('__')[-1]}" if t == "lumpi" else ""), pc / "realval-v1", rid)]
    fig, axs = plt.subplots(1, 3, figsize=(WIDE, 2.5))
    for ax, (title, root, fid) in zip(axs, panels):
        pts = np.load(root / "points" / f"{fid}.npy")
        boxes, names = read_labels(root / "labels" / f"{fid}.txt")
        bev(ax, pts, size=0.05)
        draw_boxes(ax, boxes, names)
        valid = int(np.any(pts != 0, axis=1).sum())
        cnt = defaultdict(int)
        for n in names:
            cnt[GROUP.get(n, "vehicle")] += 1
        plural = {"walker": "walkers", "two-wheeler": "two-wheelers", "vehicle": "vehicles", "large": "large"}
        sub = ", ".join(f"{cnt[g]} {plural[g]}" for g in ["walker", "two-wheeler", "vehicle", "large"] if cnt[g])
        ax.set_title(f"{title}\n{valid:,} valid points\n{sub}", fontsize=6.1, pad=2, linespacing=1.15)
        ax.set_xlabel("x (m)", labelpad=1)
    axs[0].set_ylabel("y (m)", labelpad=1)
    handles = [plt.Line2D([], [], color=GROUP_COLOR[g], linewidth=1.2, label=g) for g in ["walker", "two-wheeler", "vehicle", "large"]]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(w_pad=1.2)
    save(fig, t, "frames")


# ------------------------------------------------------------------------------------------------------------------
# Fig: data statistics, released twin against CompleteTwin against real (legal realval-A and B)
# ------------------------------------------------------------------------------------------------------------------
SOURCES = [("ut-v1", "released UrbanTwin", C2), ("g1-v6", "CompleteTwin (draw 1)", C1), ("realval-v1", "real (realval-A + B)", INK)]


def label_rows(root, every):
    fs = sorted(glob.glob(str(root / "labels" / "*.txt")))[::every]
    for f in fs:
        rows = [l.split() for l in open(f) if len(l.split()) >= 8]
        yield Path(f).stem, rows


def points_in_boxes(root, fid, rows):
    pts = np.load(root / "points" / f"{fid}.npy")[:, :3]
    pts = pts[np.any(pts != 0, axis=1)]
    tree = cKDTree(pts[:, :2])
    out = []
    for r in rows:
        x, y, z, l, w, h, yaw = map(float, r[:7])
        idx = tree.query_ball_point([x, y], np.hypot(l, w) / 2)
        k = 0
        if idx:
            q = pts[idx] - [x, y, z]
            c, s = np.cos(yaw), np.sin(yaw)
            lx, ly = q[:, 0] * c + q[:, 1] * s, -q[:, 0] * s + q[:, 1] * c
            k = int(((np.abs(lx) <= l / 2) & (np.abs(ly) <= w / 2) & (np.abs(q[:, 2]) <= h / 2)).sum())
        out.append((r[7], float(np.hypot(x, y)), k))
    return out


def data_stats(t):
    """Objects per frame, box sizes and points per box by range for the three sources (cached in the scratch dir)."""
    stats = {}
    for key, _, _ in SOURCES:
        root = DATA / f"{t}-track" / "pcdet" / key
        yml = (root / "dataset.yaml").read_text() if (root / "dataset.yaml").exists() else ""
        m = re.search(r"scale_fix:\s*([\d.]+)", yml)
        scale = float(m.group(1)) if (key == "ut-v1" and m) else 1.0          # released sizes = stored / scale fix
        n_frames, counts, sizes = 0, defaultdict(int), defaultdict(list)
        every = 10 if key != "realval-v1" else 1
        for fid, rows in label_rows(root, every):
            n_frames += 1
            for r in rows:
                counts[r[7]] += 1
                sizes[r[7]].append([float(v) / scale for v in r[3:6]])
        ppb = []
        for fid, rows in label_rows(root, 50 if key != "realval-v1" else (10 if t == "lumpi" else 5)):
            ppb += points_in_boxes(root, fid, rows)
        stats[key] = {"frames": n_frames, "per_frame": {c: v / n_frames for c, v in counts.items()},
                      "sizes": {c: np.array(v) for c, v in sizes.items()}, "ppb": ppb}
    return stats


def fig_data(t, subs):
    st = data_stats(t)
    classes = CLASSES[t]
    fig, axs = plt.subplots(1, 3, figsize=(WIDE, 2.15), gridspec_kw={"width_ratios": [1.0, 1.0, 1.15]})
    # (a) objects per frame
    ax = axs[0]
    k = len(SOURCES)
    bh = 0.8 / k
    y = np.arange(len(classes))[::-1]
    for j, (key, lab, col) in enumerate(SOURCES):
        vals = [st[key]["per_frame"].get(c, 0.0) for c in classes]
        ax.barh(y + (k - 1 - j - (k - 1) / 2) * bh, vals, bh * 0.92, color=col, label=lab, edgecolor="white",
                linewidth=0.3)
    ax.set_yticks(y, classes)
    ax.set_xlabel("labelled objects per frame")
    ax.set_title("(a) class mix", pad=2)
    ax.grid(axis="y", visible=False)
    # (b) box length: median and interquartile range
    ax = axs[1]
    for j, (key, lab, col) in enumerate(SOURCES):
        for i, c in enumerate(classes):
            v = st[key]["sizes"].get(c)
            if v is None or len(v) < 10:
                continue
            q1, q2, q3 = np.percentile(v[:, 0], [25, 50, 75])
            yy = y[i] + (k - 1 - j - (k - 1) / 2) * bh
            ax.plot([q1, q3], [yy, yy], color=col, linewidth=1.0, solid_capstyle="butt")
            ax.plot([q2], [yy], marker="o", markersize=2.8, color=col, markeredgewidth=0)
    ax.set_yticks(y, classes)
    ax.set_xlabel("box length (m): median and quartiles")
    ax.set_title("(b) object size", pad=2)
    ax.grid(axis="y", visible=False)
    # (c) points per box against range, for the most frequent vehicle and walker classes
    ax = axs[2]
    pair = [("Car", "-"), ("Person", (0, (3, 1.5)))] if t == "lumpi" else [("vehicle", "-"), ("pedestrian", (0, (3, 1.5)))]
    if t == "v2x":
        pair.append(("truck", (0, (1, 1))))
    edges = np.arange(0, 45, 5)
    for key, lab, col in SOURCES:
        for c, ls in pair:
            arr = np.array([(r, n) for cc, r, n in st[key]["ppb"] if cc == c]).reshape(-1, 2)
            if not len(arr):
                continue
            xs, ys = [], []
            for a, b in zip(edges, edges[1:]):
                sel = arr[(arr[:, 0] >= a) & (arr[:, 0] < b), 1]
                if len(sel) >= 12:
                    xs.append((a + b) / 2)
                    ys.append(max(np.median(sel), 0.8))
            ax.plot(xs, ys, color=col, linestyle=ls, linewidth=1.0, marker="o", markersize=2.2, markeredgewidth=0)
    ax.set_yscale("log")
    ticks = [5, 10, 30, 100, 300, 1000, 3000]
    lo, hi = ax.get_ylim()
    ax.set_yticks([v for v in ticks if lo <= v <= hi], [f"{v:,}" for v in ticks if lo <= v <= hi])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("distance from the sensor origin (m)")
    ax.set_ylabel("median points per box")
    ax.set_title("(c) points on objects", pad=2)
    styles = [plt.Line2D([], [], color=INK2, linestyle=ls, linewidth=1.0, label=c) for c, ls in pair]
    ax.legend(handles=styles, loc="upper right", frameon=False, fontsize=6.0, handlelength=2.2)
    handles = [plt.Rectangle((0, 0), 1, 1, color=col, label=lab) for _, lab, col in SOURCES]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout(w_pad=0.9)
    save(fig, t, "data")
    # the numbers the text quotes
    for key, lab, _ in SOURCES:
        meds = {c: np.round(np.median(st[key]["sizes"][c], 0), 2).tolist() for c in classes if c in st[key]["sizes"]}
        pf = {c: round(st[key]["per_frame"].get(c, 0.0), 2) for c in classes}
        print(f"  {t} {key}: frames {st[key]['frames']}; per frame {pf}; median l, w, h {meds}")
        for c in classes:
            arr = np.array([(r, n) for cc, r, n in st[key]["ppb"] if cc == c]).reshape(-1, 2)
            if len(arr):
                near = arr[(arr[:, 0] >= 10) & (arr[:, 0] < 20), 1]
                print(f"    {c}: {len(arr)} boxes, median points {np.median(arr[:, 1]):.0f}, at 10-20 m "
                      f"{np.median(near) if len(near) else float('nan'):.0f}, empty {np.mean(arr[:, 1] == 0):.3f}")


# ------------------------------------------------------------------------------------------------------------------
# Fig: score trajectory of every scored upload
# ------------------------------------------------------------------------------------------------------------------
STATUS_STYLE = {
    "development": dict(marker="o", mfc="white", mec=C1, label="development phase"),
    "removed": dict(marker="X", mfc=INK2, mec=INK2, label="final, removed (label-placed walkers)"),
    "frames rule": dict(marker="v", mfc="white", mec=C2, label="final, frames rule (not qualifying)"),
    "qualifying": dict(marker="s", mfc=C3, mec=C3, label="final, qualifying"),
}
PHASES = [(datetime(2026, 10, 3), datetime(2026, 11, 1)), (datetime(2026, 11, 1), datetime(2026, 11, 8)),
          (datetime(2026, 11, 8), datetime(2026, 11, 15))]                  # development; label-free twin; clean final


def fig_trajectory(t, subs):
    fig, ax = plt.subplots(figsize=(COL, 2.05))
    rows = [r for r in subs if r["track"] == t and r["date"]]
    x = [datetime.strptime(r["date"], "%Y-%m-%d") for r in rows]
    y = [r["scores"]["score_combined"] for r in rows]
    ax.plot(x, y, color=GRID, linewidth=0.8, zorder=1)
    present = []
    for st, sty in STATUS_STYLE.items():
        pts = [(xi, yi) for xi, yi, r in zip(x, y, rows) if r["status"] == st]
        if pts:
            present.append(st)
            ax.plot(*zip(*pts), linestyle="none", markersize=4.2, markeredgewidth=0.8, zorder=3,
                    **{k: v for k, v in sty.items() if k != "label"}, label=sty["label"])
    best = next(r for r in rows if r["id"] == ENTRY[t])
    ax.annotate(f"final entry {best['id']}\n{best['scores']['score_combined']:.4f}",
                xy=(datetime.strptime(best["date"], "%Y-%m-%d"), best["scores"]["score_combined"]),
                xytext=(-62, -32) if t == "v2x" else (-48, -62), textcoords="offset points", fontsize=6.2, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, linewidth=0.6))
    first = rows[0]
    ax.annotate(f"first upload (iteration 1)\n{first['scores']['score_combined']:.4f}",
                xy=(datetime.strptime(first["date"], "%Y-%m-%d"), first["scores"]["score_combined"]),
                xytext=(24, -4) if t == "v2x" else (28, 4), textcoords="offset points", fontsize=6.2, color=INK)
    for (a, b), shade in zip(PHASES[1:], (0.06, 0.13)):
        ax.axvspan(a, b, color=INK2, alpha=shade, linewidth=0, zorder=0)
    for (a, b), lab in zip(PHASES, ["Phase I: iterations 1-8", "II: 9", "III: 10"]):
        ax.text(a + (b - a) / 2, 0.03, lab, transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                fontsize=5.8, color=INK2)
    ax.set_ylabel("combined score")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(matplotlib.dates.WeekdayLocator(byweekday=matplotlib.dates.MO))
    handles = [plt.Line2D([], [], linestyle="none", markersize=4.2, markeredgewidth=0.8,
                          **{k: v for k, v in STATUS_STYLE[s].items() if k != "label"}, label=STATUS_STYLE[s]["label"])
               for s in present]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.13))
    fig.tight_layout()
    save(fig, t, "trajectory")


# ------------------------------------------------------------------------------------------------------------------
# Fig: per-class AP
# ------------------------------------------------------------------------------------------------------------------
PERCLASS = {"lumpi": [(965614, "first upload (iteration 1)"), (1022492, "best development upload (iteration 8)"),
                      (1038963, "best upload before the ruling (iteration 9)"),
                      (1042287, "clean rebuild C0 (iteration 10.1)"), (1051832, "final entry L8 (iteration 10.4)")],
            "v2x": [(965633, "first upload (iteration 1)"), (1022246, "best development upload (iteration 8)"),
                    (1038966, "best upload before the ruling (iteration 9)"),
                    (1042294, "clean rebuild C0 (iteration 10.1)"), (1051825, "final entry V4 (iteration 10.4)")]}


def fig_perclass(t, subs):
    by_id = {r["id"]: r for r in subs}
    classes, stages = CLASSES[t], PERCLASS[t]
    fig, ax = plt.subplots(figsize=(COL, 2.15))
    colors = [GRID, PTS, INK2, C1, C2]
    k = len(stages)
    bw = 0.84 / k
    for j, (sid, lab) in enumerate(stages):
        s = by_id[sid]["scores"]
        vals = [s.get(f"AP_3d_0.5_R40_{c}") or 0.0 for c in classes]
        ax.bar(np.arange(len(classes)) + (j - (k - 1) / 2) * bw, vals, bw * 0.92, color=colors[j], label=lab,
               edgecolor="white", linewidth=0.3)
    ent = by_id[ENTRY[t]]["scores"]
    for i, c in enumerate(classes):
        v = ent.get(f"AP_3d_0.5_R40_{c}") or 0.0
        ax.text(i + (k - 1) / 2 * bw, v + 0.012, f"{v:.3f}", ha="center", va="bottom", fontsize=5.0, color=INK,
                rotation=90 if t == "lumpi" else 0)
    ax.set_xticks(range(len(classes)), classes, fontsize=6.2 if t == "lumpi" else 6.8)
    ax.set_ylabel("3D AP@0.5 (R40), hidden test")
    ax.set_ylim(0, 0.84 if t == "v2x" else 0.82)
    ax.grid(axis="x", visible=False)
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.17), fontsize=5.9)
    fig.tight_layout()
    save(fig, t, "perclass")


# ------------------------------------------------------------------------------------------------------------------
# Fig: qualitative results on legal real validation (realval-B)
# ------------------------------------------------------------------------------------------------------------------
def match(preds, gts, gnames, thr=0.5, score_min=0.3):
    """Greedy official-IoU matching per class: TP / wrong class / FP for predictions, missed GT."""
    P = [p for p in preds if p["score"] >= score_min]
    pb = np.array([p["box"] for p in P]).reshape(-1, 7)
    pn = [p["class"] for p in P]
    order = np.argsort([-p["score"] for p in P])
    ious = iou_matrix(pb, gts, kind="3d") if len(pb) and len(gts) else np.zeros((len(pb), len(gts)))
    used = np.zeros(len(gts), bool)
    kind = ["fp"] * len(P)
    for i in order:
        same = [j for j in range(len(gts)) if gnames[j] == pn[i] and not used[j]]
        if same:
            j = max(same, key=lambda j: ious[i, j])
            if ious[i, j] >= thr:
                used[j] = True
                kind[i] = "tp"
                continue
        if len(gts) and ious[i].max() >= thr and gnames[int(ious[i].argmax())] != pn[i]:
            kind[i] = "wrong class"
    return pb, pn, kind, ~used


# Three frames per track, chosen by fixed rules over a deterministic third of realval-B (frames with at least 8
# labelled objects): the best case (most TP minus FP minus wrong-class boxes) and two error cases named for the track.
# On V2X, the false-positive case is taken only from scene parts that have pedestrian labels; the third case is the
# frame with the most false positives overall, which lies in a scene part without any pedestrian label.
QUAL_RULES = {"lumpi": [("best case", lambda c: c["tp"] - c["fp"] - c["wc"], None),
                        ("most wrong-class boxes", lambda c: c["tp"] + 2 * c["wc"], None),
                        ("most missed objects", lambda c: c["missed"] + 0.01 * c["tp"], None)],
              "v2x": [("best case", lambda c: c["tp"] - c["fp"] - c["wc"], None),
                      ("most false positives (labelled scene)", lambda c: c["fp"] + 0.01 * c["tp"], "labelled"),
                      ("no pedestrian label in the scene part", lambda c: c["fp"] + 0.01 * c["tp"], "unlabelled")]}


def fig_qualitative(t, subs):
    card, _ = FINAL_CARD[t]
    root = DATA / f"{t}-track/pcdet/realval-v1"
    preds = json.load(open(track_dir(t) / card / "validation/output/pcdet_realval-v1_valB_routed.json"))
    ids = (root / "ImageSets" / "valB.txt").read_text().split()
    scene_ped = defaultdict(int)                            # labelled walkers per scene part (V2X scene id)
    for fid in ids:
        _, gn = read_labels(root / "labels" / f"{fid}.txt")
        scene_ped[fid.split("__")[0]] += sum(n in ("pedestrian", "Person") for n in gn)
    cand = []
    for fid in ids[::3]:                                   # a deterministic third of the split
        gts, gn = read_labels(root / "labels" / f"{fid}.txt")
        if len(gts) < 8:
            continue
        pb, pn, kind, missed = match(preds.get(fid, []), gts, gn)
        cand.append({"fid": fid, "gts": gts, "gn": gn, "pb": pb, "pn": pn, "kind": kind, "missed_mask": missed,
                     "tp": kind.count("tp"), "wc": kind.count("wrong class"), "fp": kind.count("fp"),
                     "missed_n": int(missed.sum()), "labelled": scene_ped[fid.split("__")[0]] > 0})
    for c in cand:
        c["missed"] = c["missed_n"]
    fig, axs = plt.subplots(1, 3, figsize=(WIDE, 2.5))
    chosen = []
    for ax, (rule_name, key, scope) in zip(axs, QUAL_RULES[t]):
        pool = [c for c in cand if c["fid"] not in chosen and (scope is None or c["labelled"] == (scope == "labelled"))]
        c = max(pool, key=key)
        chosen.append(c["fid"])
        fid, gts, gn, pb, pn, kind = c["fid"], c["gts"], c["gn"], c["pb"], c["pn"], c["kind"]
        missed = c["missed_mask"]
        bev(ax, np.load(root / "points" / f"{fid}.npy"), size=0.05)
        hit = np.flatnonzero(~missed)
        draw_boxes(ax, gts[hit], [gn[i] for i in hit], lw=0.6, color=INK)
        draw_boxes(ax, gts[missed], [gn[i] for i in np.flatnonzero(missed)], lw=0.9, style=(0, (2, 1.2)), color=INK)
        for b, kk in zip(pb, kind):
            col = {"tp": C3, "wrong class": C4, "fp": C2}[kk]
            ax.add_patch(Polygon(corners(b), closed=True, fill=False, edgecolor=col, linewidth=0.8))
        counts = f"TP {c['tp']}, wrong class {c['wc']}, FP {c['fp']}, missed {c['missed_n']}"
        frame = (fid.replace("Measurement", "Measurement ").replace("__", ", frame ") if t == "lumpi"
                 else "scene part " + fid.split("__")[0].split("_", 1)[-1] + ", frame " + fid.split("__")[-1])
        ax.set_title(f"({'abc'[len(chosen) - 1]}) {rule_name}\n{frame}\n{counts}", fontsize=6.0, pad=2,
                     linespacing=1.15)
        ax.set_xlabel("x (m)", labelpad=1)
        per = defaultdict(lambda: [0, 0, 0])
        for n, kk in zip(pn, kind):
            per[n][{"tp": 0, "wrong class": 1, "fp": 2}[kk]] += 1
        print(f"  {t} {rule_name} {fid}: {counts}; per class (TP, WC, FP) {dict(per)}; "
              f"missed {[gn[i] for i in np.flatnonzero(missed)]}; scene part labelled walkers {scene_ped[fid.split('__')[0]]}")
    axs[0].set_ylabel("y (m)", labelpad=1)
    handles = [plt.Line2D([], [], color=INK, linewidth=0.8, label="ground truth"),
               plt.Line2D([], [], color=INK, linewidth=0.9, linestyle=(0, (2, 1.2)), label="missed ground truth"),
               plt.Line2D([], [], color=C3, linewidth=1.2, label="true positive"),
               plt.Line2D([], [], color=C4, linewidth=1.2, label="overlaps another class"),
               plt.Line2D([], [], color=C2, linewidth=1.2, label="false positive")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(w_pad=0.9)
    save(fig, t, "qualitative")


# ------------------------------------------------------------------------------------------------------------------
# Fig: what each step bought on the leaderboard (combined change split into detection and realism parts)
# ------------------------------------------------------------------------------------------------------------------
# The entry path: each upload replaced the previous entry (iteration 5 on LUMPI did not, so it is not on the path).
PATHS = {
    "lumpi": [(965614, "1 Calibrated Twin"), (974348, "3 Fused Portfolio"), (975871, "4 Two-Stage Refinement"),
              (986489, "5.1 Re-cast Twin"), (990245, "5.2 Realism-Led Refinement"), (995869, "6 Seed Bags"),
              (1014495, "7 generator-draw bags"), (1022492, "8 Twelve-View Completion"),
              (1028541, "9 Label-Free Twin: walkers"), (1031132, "9 Person and Car routes"),
              (1038963, "9 anchored size calibration"), (1042287, "10.1 clean rebuild (C0)"),
              (1051465, "10.3 final size adjustment (L5)"),
              (1051832, "10.4 Car size, class copies (L8)")],
    "v2x": [(965633, "1 Calibrated Twin"), (972563, "1 range-dependent z offset"), (974400, "3 Fused Portfolio"),
            (975938, "4 Two-Stage Refinement"), (978945, "5 Size-Aware Augmentation"),
            (986496, "5.1 Re-cast Twin"), (990255, "5.2 Realism-Led Refinement"), (995877, "6 Seed Bags"),
            (1001919, "7 Visibility Rule"), (1022246, "8 twelve-view ensembles"), (1028491, "9 re-fusion, new bags"),
            (1038966, "9 anchored size calibration"), (1042294, "10.1 clean rebuild (C0)"),
            (1046758, "10.1 overhead demotion (OD)"), (1050253, "10.2 truck route (V1)"),
            (1051825, "10.4 final size adjustment (V4)")],
}


def det_score(s):
    return s.get("score_detection") if s.get("score_detection") is not None else min(s["mAP_3d_0.5_R40"] / 0.7, 1.0)


def fig_levers(t, subs):
    by_id = {r["id"]: r for r in subs}
    path = PATHS[t]
    fig, ax = plt.subplots(figsize=(COL, 0.15 * len(path) + 0.7))
    labels, det, real = [], [], []
    for (a, _), (b, lab) in zip(path, path[1:]):
        sa, sb = by_id[a]["scores"], by_id[b]["scores"]
        det.append(0.6 * (det_score(sb) - det_score(sa)))
        real.append(0.4 * (sb["score_realism"] - sa["score_realism"]))
        labels.append(lab)
    y = np.arange(len(labels))[::-1]
    for yi, d, r in zip(y, det, real):
        pos, neg = 0.0, 0.0
        for v, col in [(d, C1), (r, C3)]:
            if v >= 0:
                ax.barh(yi, v, left=pos, height=0.62, color=col, edgecolor="white", linewidth=0.3)
                pos += v
            else:
                ax.barh(yi, v, left=neg, height=0.62, color=col, edgecolor="white", linewidth=0.3)
                neg += v
        ax.text(max(pos, 0) + 0.0006, yi, f"{d + r:+.4f}", va="center", ha="left", fontsize=5.6, color=INK)
    ax.set_yticks(y, labels, fontsize=6.0)
    ax.axvline(0, color=INK2, linewidth=0.6)
    ax.set_xlabel("change in combined score")
    s0, s1 = by_id[path[0][0]]["scores"]["score_combined"], by_id[path[-1][0]]["scores"]["score_combined"]
    ax.set_title(f"{NAME[t]}: {s0:.4f} to {s1:.4f} ({s1 - s0:+.4f})", pad=2)
    ax.grid(axis="y", visible=False)
    lo = min(min(det + real), 0) - 0.002
    ax.set_xlim(lo, max(np.add(np.clip(det, 0, None), np.clip(real, 0, None))) + 0.011)
    handles = [plt.Rectangle((0, 0), 1, 1, color=C1, label="detection, 0.6 x change of clip(mAP / 0.7)"),
               plt.Rectangle((0, 0), 1, 1, color=C3, label="realism, 0.4 x change of R")]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=5.8, handlelength=1.4)
    fig.tight_layout()
    save(fig, t, "levers")


FIGS = {"pipeline": fig_pipeline, "frames": fig_frames, "data": fig_data, "trajectory": fig_trajectory,
        "perclass": fig_perclass, "qualitative": fig_qualitative, "levers": fig_levers}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", nargs="*", choices=["lumpi", "v2x"], default=["lumpi", "v2x"])
    ap.add_argument("--only", nargs="*", choices=sorted(FIGS))
    a = ap.parse_args()
    subs = submissions()
    for t in a.track:
        for name in a.only or FIGS:
            FIGS[name](t, subs)


if __name__ == "__main__":
    main()
