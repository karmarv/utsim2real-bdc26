#!/usr/bin/env python
"""Seed bags (strategy S6, docs/02-STRATEGY.md Section 8.6): one routable member made by fusing several seeds of one
configuration, to average out member noise (seed spread up to 0.17 AP per class on realval-B in R5).

A bag is a model folder model-<track>/bag-<config>/ whose model.yaml has `type: bag`, `members` (model folders, each
with its epoch-40 checkpoint, plain and TTA tuned) and `iou` ({default: 0.5, <class>: <thr>}). It has no checkpoint:
its predictions are the per-frame weighted box fusion (bdc26.detect.fusion.fuse_dets: scores averaged over all seeds,
so a box only one seed finds is demoted) of the seeds' own post-processed predictions.

    python common/tools/bag_predictions.py model-lumpi-track/bag-voxelrcnn-ros-g1v4            # realval A/B, plain + TTA
    CUDA_VISIBLE_DEVICES=0 python common/tools/bag_predictions.py <bag> --kit --variant tta --out predictions_x.json [--refresh]

Realval: writes validation/output/<data>_<split>_bag_checkpoint_epoch_40[_tta].json, the names a routed model reads for
a member {model: bag-..., ckpt: train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth[, tta: ...]} (the ckpt
path only names the files), and validation/results/local_scores[_tta].json. Kit: predicts the 50 kit frames with every
seed (cached in test/output/), then fuses. No knob is tuned on the bag itself.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

from _common import REPO, load_track

CK = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"
TAG = "bag_checkpoint_epoch_40"
TTA = "flip4+yaw+z"


def bag_card(bag: Path) -> dict:
    card = yaml.safe_load((bag / "model.yaml").read_text())
    if card.get("type") != "bag":
        raise SystemExit(f"{bag} is not a bag (model.yaml type: bag)")
    return card


def fuse_files(files: list[Path], iou: dict) -> dict:
    from bdc26.detect.fusion import fuse_dets
    preds = [json.loads(f.read_text()) for f in files]
    ids = sorted(set().union(*[set(p) for p in preds]))
    return {i: fuse_dets([p.get(i, []) for p in preds], iou) for i in ids}


def realval(bag: Path, card: dict, track) -> None:
    from bdc26 import scorecard as sc
    from bdc26.evalap import evaluate
    data = card["data"]["realval"]
    D = data.replace("/", "_")
    out, res = bag / "validation" / "output", bag / "validation" / "results"
    out.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    root = track.pcdet / data.replace("pcdet/", "")
    cwg = list(track["classes_with_test_gt"])
    for suf in ("", "_tta"):
        scores = {"run": f"bag of {len(card['members'])} seeds{' (TTA)' if suf else ''}", "members": card["members"]}
        for split, k in (("val", "A"), ("valB", "B")):
            files = [bag.parent / m / "validation" / "output" / f"{D}_{split}_run1_checkpoint_epoch_40{suf}.json" for m in card["members"]]
            missing = [str(f) for f in files if not f.exists()]
            if missing:
                raise SystemExit(f"missing member predictions: {missing}")
            fused = fuse_files(files, card["iou"])
            (out / f"{D}_{split}_{TAG}{suf}.json").write_text(json.dumps(fused))
            gts = sc.load_split(root, split)
            pc = evaluate({i: fused.get(i, []) for i in gts}, gts, track.classes)["per_class"]
            per = {c: (pc[c]["3d@0.5"]["AP_R40"] if pc[c]["3d@0.5"] else None) for c in pc}
            vals = [per[c] for c in cwg if per.get(c) is not None]
            scores[f"realval_{k}_mAP_3d_0.5_R40"] = sum(vals) / max(len(vals), 1)
            scores[f"realval_{k}_per_class"] = per
        (res / f"local_scores{suf}.json").write_text(json.dumps(scores, indent=2))
        print(f"{bag.name}{suf}: A {scores['realval_A_mAP_3d_0.5_R40']:.4f} B {scores['realval_B_mAP_3d_0.5_R40']:.4f}", flush=True)


def kit(bag: Path, card: dict, variant: str, out_path: Path, cache_dir: Path | None = None, refresh: bool = False) -> None:
    """Seed predictions are cached in cache_dir (default <bag>/test/output) and redone when the cache is older than the
    seed's checkpoint or post-processing file, or always with refresh (reproduction scripts)."""
    files = []
    cache_dir = cache_dir or bag / "test" / "output"
    for m in card["members"]:
        md = bag.parent / m
        pp = md / "test" / ("postprocess_tta.yaml" if variant == "tta" else "postprocess.yaml")
        f = cache_dir / f"kit_{m}{'_tta' if variant == 'tta' else ''}.json"
        if refresh or not f.exists() or f.stat().st_mtime < max((md / CK).stat().st_mtime, pp.stat().st_mtime):
            f.parent.mkdir(parents=True, exist_ok=True)
            cmd = [sys.executable, str(REPO / "common" / "tools" / "pcdet_predict.py"), str(md), "--ckpt", str(md / CK), "--frames", "kit",
                   "--postprocess", str(pp), "--out", str(f)]
            if variant == "tta":
                cmd += ["--tta", TTA]
            subprocess.run(cmd, check=True)
        files.append(f)
    fused = fuse_files(files, card["iou"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(fused))
    print(f"{bag.name} kit ({variant}): {sum(len(v) for v in fused.values())} boxes -> {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bag")
    ap.add_argument("--kit", action="store_true", help="predict the 50 kit frames with every seed and fuse")
    ap.add_argument("--variant", choices=["plain", "tta"], default="plain")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cache-dir", default=None, help="kit mode: where the seed predictions are kept (default <bag>/test/output)")
    ap.add_argument("--refresh", action="store_true", help="kit mode: predict every seed again even if a cache exists")
    a = ap.parse_args()
    bag = Path(a.bag).resolve()
    card = bag_card(bag)
    track = load_track(card["track"])
    if a.kit:
        kit(bag, card, a.variant, Path(a.out) if a.out else bag / "test" / "output" / f"predictions_kit_{a.variant}.json",
            Path(a.cache_dir) if a.cache_dir else None, a.refresh)
    else:
        realval(bag, card, track)


if __name__ == "__main__":
    main()
