# `routed-g4` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage (Voxel R-CNN, PV-RCNN++) members, with test-time augmentation |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ut_tta` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2_tta` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S4 submitted 2026-10-11: 975938 combined 0.8485 (mAP 0.5605, R 0.9203), rank 1 of 19; realval-A 0.684, realval-B 0.679, estimate (B) 0.950 |

S4 Two-Stage Refinement (docs/02-STRATEGY.md Section 8.4): the routed-g3 portfolio (its route, fusion and score floors are the incumbents) plus the two-stage members voxelrcnn-g1v3 and pvrcnnpp-g1v3 and their TTA variants; every change passes the class gate against the S3 choice.

## Route (class -> member)

| vehicle | pedestrian | truck |
|---|---|---|
| pv_tta | pv_tta | ut_tta |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration.

Range-dependent z calibration of the routed classes (z += z0 + z_per_m x range): truck (0.0, 0.0075).

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| vehicle | pv_tta + vr_tta | [1.0, 1.0] | 0.7 | - |
| pedestrian | g1v3_tta + cp4_tta | [1.0, 1.0] | 0.5 | g1v3_tta (-0.225, 0.0075) |
| truck | g1v3_tta + g1v2_tta + vr_tta | [1.0, 1.0, 1.0] | 0.7 | g1v3_tta (0.05, 0.005) |

## Score floors (server-cost budget, `route_predictions.py budget`)

| vehicle | pedestrian | truck |
|---|---|---|
| 0.01 | 0.075 | 0.1 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g4 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-v2x-track/routed-g4 --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-v2x-track/routed-g4                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g4/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + calibration + fusion (pedestrian, truck, vehicle) + budget`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.684** | 0.806 | 0.350 | 0.896 |
| realval-B | 0.679 | 0.843 | 0.361 | 0.834 |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-10_s4` | 975938 | combined 0.8485, mAP 0.5605, R 0.9203 |
