# `voxelrcnn-ros-g1v5-s2` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) |
| Architecture | Voxel R-CNN (as voxelrcnn-ros-g1v3) with ROS (truck length range removed) |
| Training data | `pcdet/g1-v5` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (random 50 of the val split until selected) |
| Status | planned (S6 seed run, seed 1666) |

S6 (docs/02-STRATEGY.md Section 8.6): voxelrcnn-ros-g1v5 retrained with --fix_random_seed --seed 1666; member of the seed bag bag-voxelrcnn-ros-g1v5.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/voxelrcnn-ros-g1v5-s2/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5-s2/validation/tune_and_eval.sh model-v2x-track/voxelrcnn-ros-g1v5-s2/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5-s2/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5-s2/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5-s2/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.7, size_scale [1.0, 1.0, 1.08] |
| pedestrian | nms_iou 0.7, recenter 0.25, z_offset -0.1 |
| truck | nms_iou 0.6, z_offset 0.0, size_scale [1.08, 1.08, 1.08] |
| hedges | vehicle -> truck x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.654** | 0.794 | 0.333 | 0.836 |
| realval-B | 0.647 | 0.801 | 0.363 | 0.777 |

