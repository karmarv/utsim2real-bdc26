# `voxelrcnn-ros-g1v4` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) |
| Architecture | Voxel R-CNN (as voxelrcnn-ros-g1v3) with ROS (truck length range removed) |
| Training data | `pcdet/g1-v4` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | R3: trained 40 epochs with ROS capped at real sizes (run1; the uncapped run0_rostail lost trucks), tuned plain (0.637 / 0.638) and TTA (0.673 / 0.670); vehicle passes; pedestrian fusion of routed-g6 |

R3 (docs/02-STRATEGY.md Section 8.7.1): trained on pcdet/g1-v4 = the g1-v3 recipe plus engine G2-lite (actors re-cast at real size and density, real-sized trucks, buses and two-wheelers with riders, unlabeled static clutter as hard negatives). The ROS ranges keep only the generic jitter (and the V2X truck width/height range) because the corpus now has real label sizes: the S5 Bicycle and Truck length ranges would scale real-sized objects a second time.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/voxelrcnn-ros-g1v4/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v4/validation/tune_and_eval.sh model-v2x-track/voxelrcnn-ros-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v4/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v4/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v4/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.7, size_scale [1.0, 1.0, 1.08] |
| pedestrian | nms_iou 0.7, recenter 0.25, z_offset 0.0 |
| truck | nms_iou 0.6, z_offset 0.3, size_scale [1.08, 1.08, 1.0] |
| hedges | vehicle -> truck x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.637** | 0.787 | 0.324 | 0.800 |
| realval-B | 0.638 | 0.786 | 0.358 | 0.771 |

