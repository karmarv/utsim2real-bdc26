# `pointpillars-ut` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M4 baseline |
| Architecture | PointPillars (anchor-based), 0.15625 m pillars, xyz only, 8 classes |
| Training data | `pcdet/ut-v1` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/ut-v1` (random 50 of the val split until selected) |
| Status | baseline / ablation: run2 trained and tuned (realval A 0.168 / B 0.127) |

First legal submission and data-path check (Gate A). The 0.78x scale fix is on by default; ablate with a model trained on pcdet/ut-noscale-v1 (prepare_ut.py --scale-fix 1.0).

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pointpillars-ut/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ut/validation/tune_and_eval.sh model-lumpi-track/pointpillars-ut/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ut/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ut/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ut/test/make_submission.sh <ckpt> <tag> "<team>"               # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 6 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.6, recenter 0.25 |
| Car | nms_iou 0.6 |
| Bicycle | nms_iou 0.01, recenter 0.25, z_offset 0.1, size_scale [1.16, 1.16, 1.08] |
| Motorcycle | nms_iou 0.4, recenter 0.25 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.3, size_scale [1.16, 1.16, 1.08] |
| Van | nms_iou 0.1 |
| Unknown | defaults |
| hedges | Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Car -> Truck x0.1, Van x0.1 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.168** | 0.000 | 0.843 | 0.124 | 0.005 | 0.006 | 0.166 | 0.034 | 0.000 |
| realval-B | 0.127 | 0.000 | 0.757 | 0.045 | 0.011 | 0.008 | 0.065 | 0.002 | - |

