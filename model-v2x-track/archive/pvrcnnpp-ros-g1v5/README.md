# `pvrcnnpp-ros-g1v5` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) |
| Architecture | PV-RCNN++ (as pvrcnnpp-ros-g1v3) with ROS (truck length range removed) |
| Training data | `pcdet/g1-v5` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (random 50 of the val split until selected) |
| Status | R5: trained 40 epochs on g1-v5, tuned plain and TTA (TTA 0.684 / 0.669) |

R5 (docs/02-STRATEGY.md Section 8.9): the pvrcnnpp-ros-g1v4 config on pcdet/g1-v5 = the g1-v4 recipe with the background density prior gen/density_prior_v1.npz (first V2X background density prior). Object points keep their sampling rate, so the change is in the background only.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/pvrcnnpp-ros-g1v5/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5/validation/tune_and_eval.sh model-v2x-track/pvrcnnpp-ros-g1v5/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pvrcnnpp-ros-g1v5/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.7, size_scale [1.0, 1.0, 1.08], z_offset -0.1 |
| pedestrian | nms_iou 0.7, recenter 0.25, z_offset -0.1 |
| truck | nms_iou 0.5, z_offset 0.2, size_scale [1.08, 1.08, 1.0] |
| hedges | vehicle -> truck x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.646** | 0.763 | 0.325 | 0.849 |
| realval-B | 0.629 | 0.772 | 0.345 | 0.770 |

