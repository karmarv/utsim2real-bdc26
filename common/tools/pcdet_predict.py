#!/usr/bin/env python
"""Run a trained model on frames and write a challenge predictions.json (with bdc26 post-processing).

    # the 50 starting-kit test frames (inference only; nothing is fitted to them)
    python common/tools/pcdet_predict.py model-v2x-track/pointpillars-ut --ckpt CKPT --frames kit \
        --out model-v2x-track/pointpillars-ut/test/output/predictions.json
    # a dataset split (synthetic val or real val) for validation
    python common/tools/pcdet_predict.py model-v2x-track/pointpillars-ut --ckpt CKPT --frames pcdet/realval-v1 --split val \
        --out model-v2x-track/pointpillars-ut/validation/output/realval-v1.json
Post-processing: <model>/test/postprocess.yaml (override with --postprocess; use --raw to skip it).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from _common import data_path, load_pcdet_cfg, model_info


def frames_iter(track, spec: str, split: str):
    from bdc26.io.kit import read_test_frame, test_ids

    if spec == "kit":
        for fid in test_ids(track):
            yield fid, read_test_frame(track, fid)
        return
    root = data_path(track, spec)
    for fid in (root / "ImageSets" / f"{split}.txt").read_text().split():
        yield fid, np.load(root / "points" / f"{fid}.npy").astype(np.float32)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--frames", default="kit", help="'kit' or a dataset folder (relative to $BDC_DATA/<track>)")
    ap.add_argument("--split", default="val")
    ap.add_argument("--out", required=True)
    ap.add_argument("--postprocess", default=None)
    ap.add_argument("--raw", action="store_true", help="skip bdc26 post-processing (write OpenPCDet outputs)")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    cfg = load_pcdet_cfg(model_dir, data_path(track, card["data"]["train"]))

    import torch
    from bdc26.detect.pcdet_dataset import register

    register()                                   # BDCDataset and the OpenPCDet runtime fixes
    from pcdet.datasets import DatasetTemplate
    from pcdet.models import build_network, load_data_to_gpu
    from pcdet.utils import common_utils

    from bdc26.detect.postprocess import postprocess
    from bdc26.frames import strip_nulls

    class InferenceSet(DatasetTemplate):
        def __init__(self):
            super().__init__(dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, training=False,
                             root_path=Path(cfg.DATA_CONFIG.DATA_PATH), logger=common_utils.create_logger())

        def __len__(self):
            return 0

    ds = InferenceSet()
    logger = common_utils.create_logger()
    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=ds)
    model.load_params_from_file(filename=a.ckpt, logger=logger, to_cpu=True)
    model.cuda().eval()
    pp_cfg = yaml.safe_load(Path(a.postprocess or model_dir / "test" / "postprocess.yaml").read_text())
    preds = {}
    with torch.no_grad():
        for k, (fid, pts) in enumerate(frames_iter(track, a.frames, a.split)):
            if a.limit is not None and k >= a.limit:
                break
            p = strip_nulls(pts)[:, :3]
            batch = ds.collate_batch([ds.prepare_data({"points": p, "frame_id": fid})])
            load_data_to_gpu(batch)
            out, _ = model.forward(batch)
            boxes = out[0]["pred_boxes"].cpu().numpy().astype(np.float64)
            scores = out[0]["pred_scores"].cpu().numpy().astype(np.float64)
            labels = [cfg.CLASS_NAMES[int(i) - 1] for i in out[0]["pred_labels"].cpu().numpy()]
            if a.raw:
                preds[fid] = [{"box": b.tolist(), "score": float(s), "class": c} for b, s, c in zip(boxes, scores, labels)]
            else:
                preds[fid] = postprocess(boxes, scores, labels, pp_cfg, points=p)
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(preds))
    print(f"{len(preds)} frames, {sum(len(v) for v in preds.values())} boxes -> {out_path}")


if __name__ == "__main__":
    main()
