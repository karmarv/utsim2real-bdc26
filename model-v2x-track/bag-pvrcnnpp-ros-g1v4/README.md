# `bag-pvrcnnpp-ros-g1v4` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (fusion) |
| Architecture | seed bag of pvrcnnpp-ros-g1v4: weighted box fusion of the seeds' tuned predictions (common/tools/bag_predictions.py) |
| Seeds (weighted box fusion, IoU {'default': 0.5, 'vehicle': 0.7}) | [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4), [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v4` (random 50 of the val split until selected) |
| Status | planned (S6) |

S6 seed bag (docs/02-STRATEGY.md Section 8.6): seeds 666 and 1666 (amendment of 2026-10-15: no training needed). No checkpoint and no tuned knob of its own.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/bag_predictions.py model-v2x-track/bag-pvrcnnpp-ros-g1v4                                 # fuse the seeds' realval-A/B predictions (plain + TTA)
CUDA_VISIBLE_DEVICES=0 python common/tools/bag_predictions.py model-v2x-track/bag-pvrcnnpp-ros-g1v4 --kit --variant tta   # the 50 kit frames
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `bag of 2 seeds`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.671** | 0.826 | 0.337 | 0.849 |
| realval-B | 0.671 | 0.825 | 0.370 | 0.817 |


## Latest real-validation result (official metric, 3D AP@0.5 R40, TTA)

Checkpoint: `bag of 2 seeds (TTA)`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.679** | 0.843 | 0.342 | 0.850 |
| realval-B | 0.680 | 0.832 | 0.384 | 0.825 |

