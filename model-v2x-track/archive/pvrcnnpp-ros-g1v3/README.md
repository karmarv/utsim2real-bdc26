# `pvrcnnpp-ros-g1v3` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | PV-RCNN++ (as pvrcnnpp-g1v3) trained with class-wise random object scaling (ROS) |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S5 extension: trained 40 epochs, per-class score blend, tuned plain (A 0.589 / B 0.596) and TTA (0.642 / 0.650); TTA truck B +0.059 over pvrcnnpp-g1v3, vehicle and pedestrian slightly down |

S5 extension (docs/02-STRATEGY.md Section 8.5): ROS passed as run b on Voxel R-CNN; the same augmentation on pvrcnnpp-g1v3, nothing else changes.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/pvrcnnpp-ros-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v3/validation/tune_and_eval.sh model-v2x-track/pvrcnnpp-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.7, size_scale [1.08, 1.08, 1.0] |
| pedestrian | nms_iou 0.7, recenter 0.25, z_offset -0.1 |
| truck | nms_iou 0.7, z_offset 0.2, size_scale [1.08, 1.08, 1.0] |
| hedges | vehicle -> truck x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.589** | 0.747 | 0.275 | 0.744 |
| realval-B | 0.596 | 0.770 | 0.308 | 0.710 |

