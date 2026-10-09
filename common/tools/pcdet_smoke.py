#!/usr/bin/env python
"""Smoke test of an OpenPCDet model folder before a full run (the "smoke run" step of every strategy).

    CUDA_VISIBLE_DEVICES=0 python common/tools/pcdet_smoke.py model-v2x-track/centerpoint-g1v3 --iters 40

Builds the training data loader (with GT sampling and augmentation) and the network from the model's train/
configs, runs a few training iterations with real backward passes, then one inference pass, and reports: loss at
the start and the end, seconds per iteration (wall time with data loading, and GPU compute only), peak GPU
memory, raw boxes per frame and their classes at inference, and the projected epoch and full-run time for the
configured batch size and --ngpus. It catches configuration errors in minutes instead of after an epoch and
replaces the GPU-hour estimate of the plan with a measured one. Nothing is written to the model folder.
"""
import argparse
import json
import sys
import time

import numpy as np

from _common import data_path, load_pcdet_cfg, model_info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir")
    ap.add_argument("--iters", type=int, default=40)
    ap.add_argument("--batch", type=int, default=None, help="per-GPU batch (default: the config's)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--ngpus", type=int, default=4, help="GPUs of the planned full run (for the projection)")
    ap.add_argument("--data", default=None, help="dataset (default: model.yaml data.train)")
    a = ap.parse_args()
    model_dir, card, track = model_info(a.model_dir)
    from bdc26.detect.pcdet_dataset import register

    register()
    cfg = load_pcdet_cfg(model_dir, data_path(track, a.data or card["data"]["train"]))
    import torch
    from pcdet.datasets import build_dataloader
    from pcdet.models import build_network, load_data_to_gpu
    from pcdet.utils import common_utils

    logger = common_utils.create_logger()
    bs = a.batch or cfg.OPTIMIZATION.BATCH_SIZE_PER_GPU
    ds, loader, _ = build_dataloader(dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, batch_size=bs, dist=False,
                                     workers=a.workers, logger=logger, training=True)
    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=ds).cuda()
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    torch.cuda.reset_peak_memory_stats()
    it = iter(loader)
    wall, gpu, losses = [], [], []
    t_prev = time.time()
    for _ in range(a.iters):
        batch = next(it)
        load_data_to_gpu(batch)
        torch.cuda.synchronize()
        t0 = time.time()
        ret, tb, _ = model(batch)
        loss = ret["loss"].mean()
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 10)
        opt.step()
        torch.cuda.synchronize()
        t1 = time.time()
        gpu.append(t1 - t0)
        wall.append(t1 - t_prev)
        t_prev = t1
        losses.append(float(loss))
    model.eval()
    with torch.no_grad():
        batch = next(it)
        load_data_to_gpu(batch)
        preds, _ = model(batch)
    n_boxes = [int(len(p["pred_boxes"])) for p in preds]
    labels = np.concatenate([p["pred_labels"].cpu().numpy() for p in preds]) if preds else np.zeros(0)
    by_class = {cfg.CLASS_NAMES[int(c) - 1]: int((labels == c).sum()) for c in np.unique(labels)}
    skip = min(5, max(len(wall) - 1, 0))
    s_wall, s_gpu = float(np.median(wall[skip:])), float(np.median(gpu[skip:]))
    iters_epoch = len(ds) / (bs * a.ngpus)
    epochs = int(cfg.OPTIMIZATION.NUM_EPOCHS)
    out = {
        "model": card["name"], "train_frames": len(ds), "batch_per_gpu": bs, "iters": a.iters,
        "loss_first5": float(np.mean(losses[:5])), "loss_last5": float(np.mean(losses[-5:])),
        "s_per_iter_wall": round(s_wall, 3), "s_per_iter_gpu": round(s_gpu, 3),
        "peak_gpu_mem_gb": round(torch.cuda.max_memory_allocated() / 1e9, 1),
        "inference_boxes_per_frame": n_boxes, "inference_boxes_by_class": by_class,
        "projected_epoch_min": round(iters_epoch * s_wall / 60, 1),
        "projected_run_h": round(iters_epoch * s_wall * epochs / 3600, 2), "ngpus": a.ngpus, "epochs": epochs,
        "projected_gpu_hours": round(iters_epoch * s_wall * epochs / 3600 * a.ngpus, 1),
    }
    print(json.dumps(out, indent=2))
    if not np.isfinite(losses).all():
        sys.exit("non-finite loss")


if __name__ == "__main__":
    main()
