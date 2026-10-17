#!/usr/bin/env python
"""Per-class score blend of a two-stage member (strategy S4, docs/02-STRATEGY.md Section 8.4.1).

    CUDA_VISIBLE_DEVICES=0 python common/tools/score_blend.py model-lumpi-track/voxelrcnn-ros-g1v4-s3

The final score of a two-stage member is stage1^a x stage2^(1-a) (ROI_HEAD.SCORE_BLEND_ALPHA, applied by
bdc26.detect.pcdet_patches). For a in {0, 0.5, 1} the epoch-40 checkpoint predicts realval-A and realval-B raw
(pcdet_predict.py --raw --score-blend a), the member's current test/postprocess.yaml is applied as a neutral
post-processing, and per class the a with the best realval-A AP is kept (ties: 0.5); realval-B is reported only.
The choice is written into train/pcdet_model.yaml (SCORE_BLEND_ALPHA, CLASS_NAMES order); predictions go to
validation/output/score_blend/, the table to validation/results/score_blend.json. Replaces the S4-R5 session scripts
(s4_alpha.sh, s4_alpha_eval.py, s4_alpha_apply.py) with the same procedure.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

from _common import model_info

ALPHAS = ("0", "0.5", "1")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--ckpt", default="train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    from bdc26 import scorecard as sc
    from bdc26.detect.postprocess import postprocess
    from bdc26.evalap import evaluate
    cfg_path = model_dir / "train" / "pcdet_model.yaml"
    text = cfg_path.read_text()
    if "SCORE_BLEND_ALPHA" not in text:
        raise SystemExit(f"{cfg_path} has no ROI_HEAD.SCORE_BLEND_ALPHA (not a two-stage member)")
    out = model_dir / "validation" / "output" / "score_blend"
    out.mkdir(parents=True, exist_ok=True)
    data = card["data"]["realval"]
    for split in ("val", "valB"):
        for al in ALPHAS:
            f = out / f"raw_{split}_a{al}.json"
            if not f.exists():
                subprocess.run([sys.executable, str(Path(__file__).parent / "pcdet_predict.py"), str(model_dir), "--ckpt",
                                str(model_dir / a.ckpt), "--frames", data, "--split", split, "--raw", "--score-blend", al,
                                "--out", str(f)], check=True)
    neutral = yaml.safe_load((model_dir / "test" / "postprocess.yaml").read_text())
    root = track.pcdet / data.replace("pcdet/", "")
    cwg = list(track["classes_with_test_gt"])
    res = {}
    for split in ("val", "valB"):
        gts = sc.load_split(root, split)
        pts = {f: np.load(root / "points" / f"{f}.npy")[:, :3] for f in gts}
        for al in ALPHAS:
            raw = json.loads((out / f"raw_{split}_a{al}.json").read_text())
            pp = {}
            for f in gts:
                r = raw.get(f, [])
                b = np.array([d["box"] for d in r]).reshape(-1, 7)
                s = np.array([d["score"] for d in r])
                pp[f] = postprocess(b, s, [d["class"] for d in r], neutral, points=pts[f])
            pc = evaluate(pp, gts, track.classes)["per_class"]
            res[f"{split}_a{al}"] = {c: pc[c]["3d@0.5"]["AP_R40"] for c in cwg if pc[c]["3d@0.5"]}
            print(f"{split} a={al}: mAP {np.mean(list(res[f'{split}_a{al}'].values())):.4f}", flush=True)
    names = yaml.safe_load(text)["CLASS_NAMES"]
    choice, rows = [], {}
    for c in names:
        A = {al: res[f"val_a{al}"].get(c) for al in ALPHAS}
        if A["0.5"] is None:
            choice.append(0.5); rows[c] = "no realval-A GT: 0.5"; continue
        best = max(("0.5", "0", "1"), key=lambda al: A[al])          # 0.5 first: wins ties
        choice.append(float(best))
        rows[c] = {"a": float(best), "A": A, "B": {al: res[f"valB_a{al}"].get(c) for al in ALPHAS}}
    line = f"        SCORE_BLEND_ALPHA: {choice}            # per class in CLASS_NAMES order, chosen on realval-A (score_blend.py)\n"
    new, n = re.subn(r"        SCORE_BLEND_ALPHA: .*\n", line, text, count=1)
    if n != 1:
        raise SystemExit("could not find the SCORE_BLEND_ALPHA line to replace")
    cfg_path.write_text(new)
    (model_dir / "validation" / "results").mkdir(parents=True, exist_ok=True)
    (model_dir / "validation" / "results" / "score_blend.json").write_text(json.dumps({"choice": choice, "classes": rows,
                                                                                      "results": res}, indent=2))
    print(f"{track.name} {model_dir.name} {choice}")


if __name__ == "__main__":
    main()
