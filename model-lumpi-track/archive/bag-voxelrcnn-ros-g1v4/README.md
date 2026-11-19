# `bag-voxelrcnn-ros-g1v4` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (fusion) |
| Architecture | seed bag of voxelrcnn-ros-g1v4: weighted box fusion of the seeds' tuned predictions (common/tools/bag_predictions.py) |
| Seeds (weighted box fusion, IoU {'default': 0.5, 'Car': 0.7, 'Van': 0.7}) | [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2), [`voxelrcnn-ros-g1v4-s3`](../voxelrcnn-ros-g1v4-s3), [`voxelrcnn-ros-g1v4-s4`](../voxelrcnn-ros-g1v4-s4) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v4` (random 50 of the val split until selected) |
| Status | planned (S6) |

S6 seed bag (docs/02-STRATEGY.md Section 8.6): seeds 1666, 2666, 3666 of the size-capped configuration (the R3 seed-666 run predates the cap). No checkpoint and no tuned knob of its own.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/bag_predictions.py model-lumpi-track/bag-voxelrcnn-ros-g1v4                                 # fuse the seeds' realval-A/B predictions (plain + TTA)
CUDA_VISIBLE_DEVICES=0 python common/tools/bag_predictions.py model-lumpi-track/bag-voxelrcnn-ros-g1v4 --kit --variant tta   # the 50 kit frames
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `bag of 3 seeds`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.342** | 0.398 | 0.896 | 0.543 | 0.107 | 0.011 | 0.320 | 0.119 | 0.005 |
| realval-B | 0.187 | 0.095 | 0.776 | 0.223 | 0.039 | 0.036 | 0.137 | 0.001 | - |


## Latest real-validation result (official metric, 3D AP@0.5 R40, TTA)

Checkpoint: `bag of 3 seeds (TTA)`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.348** | 0.432 | 0.899 | 0.562 | 0.069 | 0.007 | 0.344 | 0.125 | 0.019 |
| realval-B | 0.192 | 0.128 | 0.780 | 0.241 | 0.041 | 0.013 | 0.140 | 0.002 | - |

