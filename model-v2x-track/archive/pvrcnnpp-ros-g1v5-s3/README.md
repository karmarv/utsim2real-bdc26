# `pvrcnnpp-ros-g1v5-s3` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) |
| Architecture | PV-RCNN++ (as pvrcnnpp-ros-g1v3) with ROS (truck length range removed) |
| Training data | `pcdet/g1-v5` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (random 50 of the val split until selected) |
| Status | planned (S6 seed run, seed 2666) |

S6 (docs/02-STRATEGY.md Section 8.6): pvrcnnpp-ros-g1v5 retrained with --fix_random_seed --seed 2666; member of the seed bag bag-pvrcnnpp-ros-g1v5.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/pvrcnnpp-ros-g1v5-s3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5-s3/validation/tune_and_eval.sh model-v2x-track/pvrcnnpp-ros-g1v5-s3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5-s3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5-s3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5-s3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.6, size_scale [1.0, 1.0, 1.08], z_offset -0.1 |
| pedestrian | nms_iou 0.7, recenter 0.25, z_offset -0.1 |
| truck | nms_iou 0.7, z_offset 0.1, size_scale [1.16, 1.16, 1.0] |
| hedges | vehicle -> truck x0.6 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.623** | 0.764 | 0.313 | 0.791 |
| realval-B | 0.611 | 0.759 | 0.338 | 0.736 |

