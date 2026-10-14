# `routed-g6` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage members trained on g1-v3 and on the R3 corpus g1-v4 (engine G2-lite), with test-time augmentation |
| Members | `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrgb` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrgb_tta` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros_tta` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros_tta` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros_tta` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp4` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp4_tta` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4_tta` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4_tta` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros4` = [`pointpillars-ros-g1v4`](../pointpillars-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros4_tta` = [`pointpillars-ros-g1v4`](../pointpillars-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v4` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | R3 submitted 2026-10-13 (scored 2026-10-14 UTC): 986489 combined 0.5169 (mAP 0.1680, R 0.9323), rank 1 of 21, confirmed through realism (mAP -0.004: Bicycle -0.056, diagnosed); realval-A 0.367, realval-B 0.221, late-A 0.341, estimate (B) 0.563 |

R3 Engine G2-lite (docs/02-STRATEGY.md Section 8.7.1): the confirmed S4 portfolio routed-g4 (route, fusion and score floors are the incumbents) plus the S5 members and the R3 g1-v4 members; every change, the S5 ones included, passes the class gate with the pooled A+B condition.

## Route (class -> member)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| g1v3 | pv_tta | vrros_tta | g1v3 | pp4_tta | g1v3_tta | g1 | g1 |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration; also a gain on the pooled A+B frames (P(gain) >= 0.9).

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| Person | g1v3_tta + g1_tta | [1.0, 1.0] | 0.5 | - |
| Car | g1v3_tta + cp_tta | [1.0, 1.0] | 0.7 | - |
| Bicycle | vrros_tta + pvros4_tta + pp4_tta | [1.0, 1.0, 1.0] | 0.7 | - |
| Bus | ppros4_tta + vrros_tta | [1.0, 1.0] | 0.3 | - |
| Truck | pvros_tta + ppros_tta + pvros4_tta | [1.0, 1.0, 1.0] | 0.3 | - |

## Score floors (server-cost budget, `route_predictions.py budget`)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| 0.02 | 0.02 | 0.02 | 0.3 | 0.075 | 0.03 | 0.075 | 0.075 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g6 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-lumpi-track/routed-g6 --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-lumpi-track/routed-g6                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g6/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + fusion (Bicycle, Bus, Car, Person, Truck) + budget`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.367** | 0.396 | 0.898 | 0.600 | 0.008 | 0.079 | 0.466 | 0.120 | 0.002 |
| realval-B | 0.221 | 0.145 | 0.792 | 0.264 | 0.013 | 0.134 | 0.200 | 0.001 | - |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-12_r3` | 986489 | combined 0.5169, mAP 0.1680, R 0.9323 |
