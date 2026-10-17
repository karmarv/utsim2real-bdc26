#!/usr/bin/env python
"""Run a trained model on frames and write a challenge predictions.json (with bdc26 post-processing).

    # the 50 starting-kit test frames (inference only; nothing is fitted to them)
    python common/tools/pcdet_predict.py model-v2x-track/pointpillars-ut --ckpt CKPT --frames kit \
        --out model-v2x-track/pointpillars-ut/test/output/predictions.json
    # a dataset split (synthetic val or real val) for validation
    python common/tools/pcdet_predict.py model-v2x-track/pointpillars-ut --ckpt CKPT --frames pcdet/realval-v1 --split val \
        --out model-v2x-track/pointpillars-ut/validation/output/realval-v1.json
Post-processing: <model>/test/postprocess.yaml (override with --postprocess; use --raw to skip it).
Test-time augmentation (strategy S3): --tta flip4[+yaw][+z] runs every frame in all views as one batch, maps the
boxes back (bdc26.detect.tta) and fuses them class by class (bdc26.detect.fusion.wbf) before post-processing; the
fused output keeps the raw format, so tune_postprocess.py tunes the TTA variant like any member.
Two-stage members (strategy S4): --score-blend A overrides the final-score blend stage1^A x stage2^(1-A) of the config
(bdc26.detect.pcdet_patches), for choosing A on real validation.
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
    ap.add_argument("--stride", type=int, default=1, help="keep every k-th frame of the split (learning curves on a fixed subset)")
    ap.add_argument("--tta", default=None, help="views: flip4, flip4+yaw, flip4+yaw+z (bdc26.detect.tta.parse)")
    ap.add_argument("--tta-iou", default=None, help="per-class view-fusion IoU, e.g. pedestrian=0.3,vehicle=0.5 (default: 0.3 small classes, 0.5 others)")
    ap.add_argument("--score-blend", type=float, default=None,
                    help="two-stage members: override ROI_HEAD.SCORE_BLEND_ALPHA (final score = stage1^a x stage2^(1-a))")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    cfg = load_pcdet_cfg(model_dir, data_path(track, card["data"]["train"]))
    if a.score_blend is not None:
        if "ROI_HEAD" not in cfg.MODEL:
            raise SystemExit("--score-blend needs a two-stage model (MODEL.ROI_HEAD)")
        cfg.MODEL.ROI_HEAD.SCORE_BLEND_ALPHA = a.score_blend

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
    from bdc26.detect import tta
    from bdc26.detect.fusion import wbf
    views = tta.parse(a.tta) if a.tta else None
    tta_iou = tta.default_iou(list(cfg.CLASS_NAMES))
    if a.tta_iou:
        tta_iou.update({k: float(v) for k, v in (x.split("=") for x in a.tta_iou.split(","))})
    preds = {}
    with torch.no_grad():
        for k, (fid, pts) in enumerate(frames_iter(track, a.frames, a.split)):
            if a.limit is not None and k >= a.limit:
                break
            if k % max(a.stride, 1):
                continue
            p = strip_nulls(pts)[:, :3]
            if views is None:
                batch = ds.collate_batch([ds.prepare_data({"points": p, "frame_id": fid})])
                load_data_to_gpu(batch)
                out, _ = model.forward(batch)
                boxes = out[0]["pred_boxes"].cpu().numpy().astype(np.float64)
                scores = out[0]["pred_scores"].cpu().numpy().astype(np.float64)
                labels = [cfg.CLASS_NAMES[int(i) - 1] for i in out[0]["pred_labels"].cpu().numpy()]
            else:
                batch = ds.collate_batch([ds.prepare_data({"points": tta.forward_points(p, v), "frame_id": fid}) for v in views])
                load_data_to_gpu(batch)
                out, _ = model.forward(batch)
                rows = {}
                for j, v in enumerate(views):
                    vb = tta.inverse_boxes(out[j]["pred_boxes"].cpu().numpy().astype(np.float64), v)
                    vs = out[j]["pred_scores"].cpu().numpy().astype(np.float64)
                    for b_, s_, l_ in zip(vb, vs, out[j]["pred_labels"].cpu().numpy()):
                        rows.setdefault(cfg.CLASS_NAMES[int(l_) - 1], []).append((b_, s_, j))
                boxes, scores, labels = [], [], []
                for c, r in rows.items():
                    fb, fs, _ = wbf(np.array([x[0] for x in r]), np.array([x[1] for x in r]), np.array([x[2] for x in r]),
                                    len(views), tta_iou.get(c, 0.5))
                    boxes.append(fb); scores.append(fs); labels += [c] * len(fs)
                boxes = np.concatenate(boxes) if boxes else np.zeros((0, 7))
                scores = np.concatenate(scores) if scores else np.zeros(0)
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
