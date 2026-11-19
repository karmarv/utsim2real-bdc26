# `routed-g3` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) |
| Architecture | per-class routing and box fusion of PointPillars and CenterPoint members, with test-time augmentation |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ut_tta` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2_tta` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S3 submitted 2026-10-10: 974400 combined 0.8381 (mAP 0.5483, R 0.9203), rank 1 of 19; realval-A 0.661, realval-B 0.664, estimate (B) 0.937 |

S3 Fused Portfolio with TTA (docs/02-STRATEGY.md Section 8.3.1): the members of routed-g2 and their 8-view TTA variants (<member>_tta, tune_and_eval.sh --tta); route by select --rule joint --calibrated, per-class fusion of two checkpoints by fuse, per-class score floors by budget; every choice passed the class gate.

## Route (class -> member)

| vehicle | pedestrian | truck |
|---|---|---|
| cp_tta | g1v3_tta | ut_tta |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration.

Range-dependent z calibration of the routed classes (z += z0 + z_per_m x range): pedestrian (-0.225, 0.0075), truck (0.0, 0.0075).

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| vehicle | cp_tta + g1v2_tta | [1.0, 1.0] | 0.5 | - |
| pedestrian | g1v3_tta + cp4_tta | [1.0, 1.0] | 0.5 | g1v3_tta (-0.225, 0.0075) |
| truck | ut_tta + g1v2_tta | [1.0, 1.0] | 0.5 | ut_tta (0.0, 0.0075) |

## Score floors (server-cost budget, `route_predictions.py budget`)

| vehicle | pedestrian | truck |
|---|---|---|
| 0.05 | 0.075 | 0.2 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g3 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-v2x-track/routed-g3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-v2x-track/routed-g3                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g3/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + calibration + fusion (pedestrian, truck, vehicle) + budget`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.661** | 0.757 | 0.350 | 0.876 |
| realval-B | 0.664 | 0.819 | 0.361 | 0.812 |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-09_s3` | 974400 | combined 0.8381, mAP 0.5483, R 0.9203 |
