# `routed-g3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) |
| Architecture | per-class routing and box fusion of PointPillars and CenterPoint members, with test-time augmentation |
| Members | `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v2` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S3 submitted 2026-10-10: 974348 combined 0.5015 by the scorer log (mAP 0.1692, R 0.8912), never listed (CodaBench status Running after scoring); superseded by routed-g4 (975871) |

S3 Fused Portfolio with TTA (docs/02-STRATEGY.md Section 8.3.1): the members of routed-g2 and their 8-view TTA variants (<member>_tta, tune_and_eval.sh --tta); route by select --rule joint --calibrated, per-class fusion of two checkpoints by fuse, per-class score floors by budget; every choice passed the class gate.

## Route (class -> member)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| g1v3 | g1 | cp4_tta | g1v3 | g1v3 | g1v3_tta | g1 | g1 |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration.

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| Person | g1v3_tta + g1_tta | [1.0, 1.0] | 0.5 | - |
| Car | g1v3_tta + cp_tta | [1.0, 1.0] | 0.7 | - |
| Bicycle | cp4_tta + cp_tta | [1.0, 1.0] | 0.5 | - |

## Score floors (server-cost budget, `route_predictions.py budget`)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| 0.02 | 0.02 | 0.03 | 0.3 | 0.3 | 0.03 | 0.075 | 0.075 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g3 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-lumpi-track/routed-g3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-lumpi-track/routed-g3                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g3/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + fusion (Bicycle, Car, Person) + budget`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.301** | 0.396 | 0.898 | 0.444 | 0.008 | 0.011 | 0.231 | 0.120 | 0.002 |
| realval-B | 0.184 | 0.145 | 0.792 | 0.173 | 0.013 | 0.011 | 0.153 | 0.001 | - |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-09_s3` | 974348 | combined 0.5015, mAP 0.1692, R 0.8912 |
