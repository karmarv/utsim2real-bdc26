# `pointpillars-g1` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M8 (G1 first version) |
| Architecture | PointPillars (anchor-based), 0.15625 m pillars, xyz only, 8 classes |
| Training data | `pcdet/g1-v2` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v2` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | trained and tuned (realval A 0.253 / B 0.156); member of routed-g1 |

First G1 model. Compare with pointpillars-ut on realval-A (Measurement4) per class; confirm on realval-B.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pointpillars-g1/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-g1/validation/tune_and_eval.sh model-lumpi-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-g1/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-g1/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-g1/test/make_submission.sh <ckpt> <tag> "<team>"               # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 6 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.3, recenter 0.5, size_scale [0.85, 0.85, 1.0] |
| Car | nms_iou 0.5 |
| Bicycle | nms_iou 0.1, recenter 0.5, z_offset 0.1, size_scale [1.16, 1.16, 1.08] |
| Motorcycle | nms_iou 0.4, recenter 0.5 |
| Bus | nms_iou 0.4 |
| Truck | nms_iou 0.01, size_scale [1.16, 1.16, 1.08] |
| Van | nms_iou 0.1, size_scale [0.85, 0.85, 1.0] |
| Unknown | defaults |
| hedges | Van -> Car x0.6, Truck x0.6, Unknown x0.1; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Car -> Van x0.1 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.253** | 0.341 | 0.874 | 0.265 | 0.010 | 0.006 | 0.154 | 0.122 | 0.004 |
| realval-B | 0.156 | 0.091 | 0.770 | 0.102 | 0.013 | 0.009 | 0.105 | 0.001 | - |

