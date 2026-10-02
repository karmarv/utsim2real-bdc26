# `pointpillars-g1` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M8 (G1 first version) |
| Architecture | PointPillars (anchor-based), 0.15625 m pillars, xyz only; pedestrian anchors for walkers and riders |
| Training data | `pcdet/g1-v1` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v1` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | trained and tuned (realval A 0.459 / B 0.404) |

First G1 model. Real validation needs the starting kit (V2X guard); until then compare on the UT val split only.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/pointpillars-g1/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1/validation/tune_and_eval.sh model-v2x-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1/test/make_submission.sh <ckpt> <tag> "<team>"               # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 8 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.3, size_scale [1.08, 1.08, 1.08] |
| pedestrian | nms_iou 0.4, recenter 0.25 |
| truck | nms_iou 0.7, z_offset -0.2, size_scale [1.08, 1.08, 0.92] |
| hedges | truck -> vehicle x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.459** | 0.620 | 0.118 | 0.639 |
| realval-B | 0.404 | 0.647 | 0.103 | 0.462 |

