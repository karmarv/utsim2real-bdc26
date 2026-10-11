# `pointpillars-ros-g1v3` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M8 (G1, calibrated on legal V2X-Real walkers) |
| Architecture | PointPillars (as pointpillars-g1v3) trained with class-wise random object scaling (ROS) |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S5 extension: trained 40 epochs, tuned plain (A 0.499 / B 0.456) and TTA (0.531 / 0.482); below pointpillars-g1v3: stretched trucks no longer match the single truck anchor (truck TTA B 0.704 -> 0.546) |

S5 extension (docs/02-STRATEGY.md Section 8.5): ROS passed as run b on Voxel R-CNN; the same augmentation on pointpillars-g1v3, nothing else changes.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/pointpillars-ros-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ros-g1v3/validation/tune_and_eval.sh model-v2x-track/pointpillars-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ros-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ros-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ros-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 8 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.7, size_scale [1.08, 1.08, 1.08] |
| pedestrian | nms_iou 0.7, recenter 0.25 |
| truck | nms_iou 0.7, size_scale [1.0, 1.0, 0.92] |
| hedges | vehicle -> truck x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.499** | 0.622 | 0.267 | 0.608 |
| realval-B | 0.456 | 0.623 | 0.235 | 0.509 |

