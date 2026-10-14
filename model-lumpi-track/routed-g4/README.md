# `routed-g4` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage (Voxel R-CNN, PV-RCNN++) members, with test-time augmentation |
| Members | `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v2` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S4 submitted 2026-10-10 (below its upload gate, the entrant's call): 975871 combined 0.5040 (mAP 0.1721, R 0.8912), rank 1 of 18; realval-A 0.313, realval-B 0.188, late-A 0.304, estimate (B) 0.523; superseded as the entry by R3 (986489, 0.5169) on 2026-10-14 |

S4 Two-Stage Refinement (docs/02-STRATEGY.md Section 8.4): the routed-g3 portfolio (its route, fusion and score floors are the incumbents) plus the two-stage members voxelrcnn-g1v3 and pvrcnnpp-g1v3 and their TTA variants; every change passes the class gate against the S3 choice.

## Route (class -> member)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| g1v3 | pv_tta | vr_tta | g1v3 | g1v3 | g1v3_tta | g1 | g1 |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration.

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| Person | g1v3_tta + g1_tta | [1.0, 1.0] | 0.5 | - |
| Car | g1v3_tta + cp_tta | [1.0, 1.0] | 0.7 | - |
| Bicycle | vr_tta + pv_tta | [1.0, 1.0] | 0.7 | - |

## Score floors (server-cost budget, `route_predictions.py budget`)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| 0.02 | 0.02 | 0.02 | 0.3 | 0.3 | 0.03 | 0.075 | 0.075 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g4 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-lumpi-track/routed-g4 --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-lumpi-track/routed-g4                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g4/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + fusion (Bicycle, Car, Person) + budget`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.313** | 0.396 | 0.898 | 0.525 | 0.008 | 0.011 | 0.231 | 0.120 | 0.002 |
| realval-B | 0.188 | 0.145 | 0.792 | 0.202 | 0.013 | 0.011 | 0.153 | 0.001 | - |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-10_s4` | 975871 | combined 0.5040, mAP 0.1721, R 0.8912 |
