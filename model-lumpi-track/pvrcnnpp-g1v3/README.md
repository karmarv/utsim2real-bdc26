# `pvrcnnpp-g1v3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | PV-RCNN++: CenterPoint proposals (sparse 3D voxels 0.1 x 0.1 x 0.25 m, VoxelResBackBone8x), 2,048 proposal-centric keypoints with raw-point, voxel and BEV features (VectorPool), RoI grid pooling with an IoU-quality score, xyz only |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S4 member: trained 40 epochs, per-class score blend chosen on A, tuned plain (A 0.264 / B 0.151) and TTA (0.312 / 0.167); in the routed-g4 Bicycle fusion |

S4 Two-Stage Refinement (docs/02-STRATEGY.md Section 8.4): the point-based second stage, next to the voxel-based voxelrcnn-g1v3; same stage 1, corpus and augmentation.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pvrcnnpp-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-g1v3/validation/tune_and_eval.sh model-lumpi-track/pvrcnnpp-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.6, recenter 0.5, size_scale [0.92, 0.92, 1.0] |
| Car | nms_iou 0.5 |
| Bicycle | nms_iou 0.6, recenter 0.5, z_offset 0.1, size_scale [1.16, 1.16, 1.0] |
| Motorcycle | nms_iou 0.4 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.01, size_scale [1.08, 1.08, 1.16] |
| Van | nms_iou 0.5 |
| Unknown | defaults |
| hedges | Van -> Car x0.6, Truck x0.1; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Bus -> Truck x0.6; Car -> Van x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.264** | 0.174 | 0.878 | 0.409 | 0.067 | 0.004 | 0.219 | 0.101 | 0.000 |
| realval-B | 0.151 | 0.037 | 0.779 | 0.144 | 0.013 | 0.005 | 0.079 | 0.001 | - |

