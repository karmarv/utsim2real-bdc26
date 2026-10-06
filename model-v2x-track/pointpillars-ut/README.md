# `pointpillars-ut` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M4 baseline |
| Architecture | PointPillars (anchor-based), 0.15625 m pillars, xyz only |
| Training data | `pcdet/ut-v1` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/ut-v1` (random 50 of the val split until selected) |
| Status | baseline: trained and tuned (realval A 0.465 / B 0.419; truck 0.822) |

First legal submission and data-path check (Gate A). Superseded by models trained on G1/G2 data.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/pointpillars-ut/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ut/validation/tune_and_eval.sh model-v2x-track/pointpillars-ut/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ut/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ut/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-ut/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 8 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.5, size_scale [1.08, 1.08, 1.08] |
| pedestrian | nms_iou 0.7, recenter 0.25 |
| truck | nms_iou 0.5, z_offset -0.1, size_scale [1.08, 1.08, 0.92] |
| hedges | truck -> vehicle x0.3; vehicle -> truck x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.465** | 0.574 | 0.000 | 0.822 |
| realval-B | 0.419 | 0.585 | 0.000 | 0.673 |

