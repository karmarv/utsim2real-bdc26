# `routed-g5` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage members, including the S5 GBlobs and object-scaling Voxel R-CNN runs, with test-time augmentation |
| Members | `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrgb` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrgb_tta` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros_tta` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros_tta` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros_tta` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v2` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S5 submitted 2026-10-11: 978931 combined 0.5039 (mAP 0.1720), 0.00007 below the S4 entry (not listed, confirmation failed, diagnosed); realval-A 0.350, realval-B 0.209, estimate (B) 0.541 |

S5 Geometry-Invariant Inputs (docs/02-STRATEGY.md Section 8.5): the routed-g4 portfolio (route, fusion and score floors are the incumbents) plus the kept S5 runs as plain and TTA members; every change passes the class gate against the S4 choice.

## Route (class -> member)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| g1v3 | pv_tta | vrros_tta | g1v3 | vrros_tta | g1v3_tta | g1 | g1 |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration.

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| Person | g1v3_tta + g1_tta | [1.0, 1.0] | 0.5 | - |
| Car | pvros_tta + vrgb_tta + ppros_tta | [1.0, 1.0, 1.0] | 0.7 | - |
| Bicycle | vrros_tta + pvros_tta + pv_tta | [1.0, 1.0, 1.0] | 0.7 | - |
| Truck | pvros_tta + ppros_tta | [1.0, 1.0] | 0.3 | - |

## Score floors (server-cost budget, `route_predictions.py budget`)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| 0.02 | 0.05 | 0.03 | 0.3 | 0.2 | 0.01 | 0.075 | 0.075 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g5 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-lumpi-track/routed-g5 --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-lumpi-track/routed-g5                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g5/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + fusion (Bicycle, Car, Person, Truck) + budget`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.350** | 0.396 | 0.909 | 0.565 | 0.008 | 0.016 | 0.433 | 0.120 | 0.002 |
| realval-B | 0.209 | 0.145 | 0.806 | 0.225 | 0.013 | 0.075 | 0.200 | 0.001 | - |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-11_s5` | 978931 | combined 0.5039, mAP 0.1720, R 0.8912 |
