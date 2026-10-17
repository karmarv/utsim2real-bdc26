#!/usr/bin/env python
"""Realval learning curves of a trained member in TensorBoard (monitoring only; S6 rule: the epoch-40 checkpoint is
always the one used, these curves never pick an epoch).

    CUDA_VISIBLE_DEVICES=0 python common/tools/tb_realval.py model-v2x-track/voxelrcnn-ros-g1v5-s2 [--every 5]

For every saved checkpoint whose epoch is a multiple of --every (and the last one), the member predicts a fixed
subset of realval-A (every 8th frame) and realval-B (every 6th frame) with its tuned test/postprocess.yaml, and the
official 3D AP@0.5 R40 per class and the challenge mAP are written as TensorBoard scalars (tag realval_A/<class>,
realval_B/<class>, step = epoch) into train/output/pcdet_model/<run>/tensorboard_realval/, next to OpenPCDet's own
training curves in tensorboard/ (losses, learning rate). A json copy goes to validation/results/realval_curves.json.
Legal real validation frames only (the train split outside the guard's windows).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from _common import model_info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--run", default="run1")
    ap.add_argument("--every", type=int, default=5)
    ap.add_argument("--stride-a", type=int, default=8)
    ap.add_argument("--stride-b", type=int, default=6)
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    from tensorboardX import SummaryWriter
    from bdc26 import scorecard as sc
    from bdc26.evalap import evaluate
    run = model_dir / "train" / "output" / "pcdet_model" / a.run
    ckpts = {int(re.search(r"epoch_(\d+)", p.name).group(1)): p for p in (run / "ckpt").glob("checkpoint_epoch_*.pth")}
    if not ckpts:
        raise SystemExit(f"no checkpoints in {run / 'ckpt'}")
    last = max(ckpts)
    epochs = sorted(e for e in ckpts if e % a.every == 0 or e == last)
    data = card["data"]["realval"]
    root = track.pcdet / data.replace("pcdet/", "")
    cwg = list(track["classes_with_test_gt"])
    tmp = model_dir / "validation" / "output" / "curves"
    tmp.mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(str(run / "tensorboard_realval"))
    out = {}
    for split, k, stride in (("val", "A", a.stride_a), ("valB", "B", a.stride_b)):
        ids = (root / "ImageSets" / f"{split}.txt").read_text().split()[::stride]
        gts_all = sc.load_split(root, split)
        gts = {i: gts_all[i] for i in ids if i in gts_all}
        for e in epochs:
            f = tmp / f"{split}_e{e}.json"
            if not f.exists():
                subprocess.run([sys.executable, str(Path(__file__).parent / "pcdet_predict.py"), str(model_dir), "--ckpt",
                                str(ckpts[e]), "--frames", data, "--split", split, "--stride", str(stride),
                                "--postprocess", str(model_dir / "test" / "postprocess.yaml"), "--out", str(f)], check=True)
            pred = json.loads(f.read_text())
            pc = evaluate({i: pred.get(i, []) for i in gts}, gts, track.classes)["per_class"]
            ap_c = {c: pc[c]["3d@0.5"]["AP_R40"] for c in cwg if pc[c]["3d@0.5"]}
            mAP = sum(ap_c.values()) / max(len(ap_c), 1)
            writer.add_scalar(f"realval_{k}/mAP", mAP, e)
            for c, v in ap_c.items():
                writer.add_scalar(f"realval_{k}/{c}", v, e)
            out.setdefault(k, {})[e] = {"mAP": mAP, **ap_c}
            print(f"{model_dir.name} {k} epoch {e}: mAP {mAP:.4f}", flush=True)
    writer.close()
    res = model_dir / "validation" / "results" / "realval_curves.json"
    res.write_text(json.dumps({"frames": {"A": f"every {a.stride_a}th", "B": f"every {a.stride_b}th"},
                               "note": "monitoring only; the epoch-40 checkpoint is always used", "curves": out}, indent=2))
    print(f"wrote {run / 'tensorboard_realval'} and {res}")


if __name__ == "__main__":
    main()
