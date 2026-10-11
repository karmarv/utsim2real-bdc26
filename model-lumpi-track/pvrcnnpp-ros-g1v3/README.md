# `pvrcnnpp-ros-g1v3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | PV-RCNN++ (as pvrcnnpp-g1v3) trained with class-wise random object scaling (ROS) |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S5 extension: trained 40 epochs, per-class score blend, tuned plain (A 0.274 / B 0.169) and TTA (0.312 / 0.186); TTA B +0.019 over pvrcnnpp-g1v3 (Truck +0.054, Bicycle +0.019, Bus +0.053) |

S5 extension (docs/02-STRATEGY.md Section 8.5): ROS passed as run b on Voxel R-CNN; the same augmentation on pvrcnnpp-g1v3, nothing else changes.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pvrcnnpp-ros-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v3/validation/tune_and_eval.sh model-lumpi-track/pvrcnnpp-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.6, recenter 0.5, size_scale [0.85, 0.85, 1.0] |
| Car | nms_iou 0.7 |
| Bicycle | nms_iou 0.01, recenter 0.5, size_scale [1.08, 1.08, 1.0] |
| Motorcycle | nms_iou 0.4 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.01, z_offset 0.1, size_scale [1.08, 1.08, 1.0] |
| Van | nms_iou 0.1 |
| Unknown | defaults |
| hedges | Bicycle -> Person x0.1; Van -> Car x0.6, Truck x0.1, Unknown x0.1; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Car -> Van x0.1 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.274** | 0.134 | 0.870 | 0.403 | 0.043 | 0.017 | 0.363 | 0.087 | 0.006 |
| realval-B | 0.169 | 0.037 | 0.774 | 0.150 | 0.015 | 0.057 | 0.148 | 0.001 | - |

