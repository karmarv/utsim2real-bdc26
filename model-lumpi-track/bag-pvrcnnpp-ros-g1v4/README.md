# `bag-pvrcnnpp-ros-g1v4` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (fusion) |
| Architecture | seed bag of pvrcnnpp-ros-g1v4: weighted box fusion of the seeds' tuned predictions (common/tools/bag_predictions.py) |
| Seeds (weighted box fusion, IoU {'default': 0.5, 'Car': 0.7, 'Van': 0.7}) | [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4), [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2), [`pvrcnnpp-ros-g1v4-s3`](../pvrcnnpp-ros-g1v4-s3), [`pvrcnnpp-ros-g1v4-s4`](../pvrcnnpp-ros-g1v4-s4) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v4` (random 50 of the val split until selected) |
| Status | planned (S6) |

S6 seed bag (docs/02-STRATEGY.md Section 8.6): seeds 666, 1666, 2666, 3666. No checkpoint and no tuned knob of its own.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/bag_predictions.py model-lumpi-track/bag-pvrcnnpp-ros-g1v4                                 # fuse the seeds' realval-A/B predictions (plain + TTA)
CUDA_VISIBLE_DEVICES=0 python common/tools/bag_predictions.py model-lumpi-track/bag-pvrcnnpp-ros-g1v4 --kit --variant tta   # the 50 kit frames
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `bag of 4 seeds`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.348** | 0.394 | 0.898 | 0.540 | 0.067 | 0.023 | 0.385 | 0.132 | 0.004 |
| realval-B | 0.192 | 0.098 | 0.778 | 0.234 | 0.044 | 0.046 | 0.145 | 0.001 | - |


## Latest real-validation result (official metric, 3D AP@0.5 R40, TTA)

Checkpoint: `bag of 4 seeds (TTA)`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.356** | 0.432 | 0.899 | 0.568 | 0.048 | 0.023 | 0.387 | 0.137 | 0.004 |
| realval-B | 0.200 | 0.123 | 0.789 | 0.250 | 0.038 | 0.042 | 0.153 | 0.001 | - |

