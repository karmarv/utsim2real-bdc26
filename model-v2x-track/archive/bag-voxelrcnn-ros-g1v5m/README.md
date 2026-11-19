# `bag-voxelrcnn-ros-g1v5m` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (fusion) |
| Architecture | seed bag of voxelrcnn-ros-g1v5m: weighted box fusion of the seeds' tuned predictions (common/tools/bag_predictions.py) |
| Seeds (weighted box fusion, IoU {'default': 0.5, 'vehicle': 0.7}) | [`voxelrcnn-ros-g1v5m`](../voxelrcnn-ros-g1v5m), [`voxelrcnn-ros-g1v5m-s2`](../voxelrcnn-ros-g1v5m-s2), [`voxelrcnn-ros-g1v5m-s3`](../voxelrcnn-ros-g1v5m-s3) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (random 50 of the val split until selected) |
| Status | planned (S7) |

S7 seed bag: seeds 666, 1666, 2666 on the S7 labels; compared with bag-voxelrcnn-ros-g1v5 (same seeds, raw labels). No checkpoint and no tuned knob of its own.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/bag_predictions.py model-v2x-track/bag-voxelrcnn-ros-g1v5m                                 # fuse the seeds' realval-A/B predictions (plain + TTA)
CUDA_VISIBLE_DEVICES=0 python common/tools/bag_predictions.py model-v2x-track/bag-voxelrcnn-ros-g1v5m --kit --variant tta   # the 50 kit frames
```
