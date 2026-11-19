# `bag-voxelrcnn-ros-g1v5` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (fusion) |
| Architecture | seed bag of voxelrcnn-ros-g1v5: weighted box fusion of the seeds' tuned predictions (common/tools/bag_predictions.py) |
| Seeds (weighted box fusion, IoU {'default': 0.5, 'vehicle': 0.7}) | [`voxelrcnn-ros-g1v5`](../voxelrcnn-ros-g1v5), [`voxelrcnn-ros-g1v5-s2`](../voxelrcnn-ros-g1v5-s2), [`voxelrcnn-ros-g1v5-s3`](../voxelrcnn-ros-g1v5-s3) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (random 50 of the val split until selected) |
| Status | planned (S6) |

S6 seed bag (docs/02-STRATEGY.md Section 8.6): seeds 666, 1666, 2666. No checkpoint and no tuned knob of its own.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/bag_predictions.py model-v2x-track/bag-voxelrcnn-ros-g1v5                                 # fuse the seeds' realval-A/B predictions (plain + TTA)
CUDA_VISIBLE_DEVICES=0 python common/tools/bag_predictions.py model-v2x-track/bag-voxelrcnn-ros-g1v5 --kit --variant tta   # the 50 kit frames
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `bag of 3 seeds`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.696** | 0.838 | 0.360 | 0.892 |
| realval-B | 0.676 | 0.835 | 0.388 | 0.805 |


## Latest real-validation result (official metric, 3D AP@0.5 R40, TTA)

Checkpoint: `bag of 3 seeds (TTA)`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.708** | 0.856 | 0.370 | 0.899 |
| realval-B | 0.697 | 0.861 | 0.407 | 0.822 |

