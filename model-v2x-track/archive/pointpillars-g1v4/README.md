# `pointpillars-g1v4` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) |
| Architecture | PointPillars (as pointpillars-g1v3), truck anchors at the g1-v4 label sizes |
| Training data | `pcdet/g1-v4` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | R3 wave 0: trained 40 epochs, tuned plain (A 0.578 / B 0.529) and TTA (0.612 / 0.567); every class passes against pointpillars-g1v3 |

R3 (docs/02-STRATEGY.md Section 8.7.1): trained on pcdet/g1-v4 = the g1-v3 recipe plus engine G2-lite (actors re-cast at real size and density, real-sized trucks, buses and two-wheelers with riders, unlabeled static clutter as hard negatives). Data-only ablation against pointpillars-g1v3 (same detector; the truck anchors follow the new label sizes).

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/pointpillars-g1v4/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1v4/validation/tune_and_eval.sh model-v2x-track/pointpillars-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1v4/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1v4/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/pointpillars-g1v4/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 8 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.7, size_scale [1.0, 1.0, 1.16], z_offset -0.1 |
| pedestrian | nms_iou 0.6, recenter 0.25, z_offset -0.1, size_scale [1.0, 1.0, 1.0] |
| truck | nms_iou 0.7, z_offset 0.3, size_scale [1.16, 1.16, 1.0] |
| hedges | vehicle -> truck x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.578** | 0.646 | 0.285 | 0.803 |
| realval-B | 0.529 | 0.627 | 0.262 | 0.697 |

