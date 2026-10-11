# `pointpillars-ros-g1v3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M8 (G1, walker v2) |
| Architecture | PointPillars (as pointpillars-g1v3) trained with class-wise random object scaling (ROS) |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S5 extension: trained 40 epochs, tuned plain (A 0.270 / B 0.178) and TTA (0.287 / 0.187); TTA B +0.017 over pointpillars-g1v3 (Truck +0.036, Person +0.023 on B, Person -0.049 on A) |

S5 extension (docs/02-STRATEGY.md Section 8.5): ROS passed as run b on Voxel R-CNN; the same augmentation on pointpillars-g1v3, nothing else changes.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pointpillars-ros-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v3/validation/tune_and_eval.sh model-lumpi-track/pointpillars-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 6 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.7, recenter 0.5, size_scale [0.85, 0.85, 1.0] |
| Car | nms_iou 0.3 |
| Bicycle | nms_iou 0.01, recenter 0.5, size_scale [1.08, 1.08, 1.0] |
| Motorcycle | nms_iou 0.4, recenter 0.25 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.7, size_scale [1.16, 1.16, 1.16] |
| Van | nms_iou 0.01 |
| Unknown | defaults |
| hedges | Bicycle -> Person x0.3; Van -> Car x0.6, Truck x0.6; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Car -> Van x0.1 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.270** | 0.335 | 0.878 | 0.239 | 0.004 | 0.021 | 0.312 | 0.101 | 0.000 |
| realval-B | 0.178 | 0.115 | 0.778 | 0.107 | 0.012 | 0.046 | 0.183 | 0.001 | - |

