# `routed-g8b` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage members trained on g1-v3 and on the R3 corpus g1-v4 (engine G2-lite), with test-time augmentation |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ut_tta` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2_tta` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrgb` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrgb_tta` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros_tta` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros_tta` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros_tta` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp4` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp4_tta` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4_tta` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4_tta` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4s2` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4s2_tta` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4s2` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4s2_tta` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp5` = [`pointpillars-g1v5`](../pointpillars-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp5_tta` = [`pointpillars-g1v5`](../pointpillars-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5` = [`voxelrcnn-ros-g1v5`](../voxelrcnn-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5_tta` = [`voxelrcnn-ros-g1v5`](../voxelrcnn-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5` = [`pvrcnnpp-ros-g1v5`](../pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5_tta` = [`pvrcnnpp-ros-g1v5`](../pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5s2` = [`voxelrcnn-ros-g1v5-s2`](../voxelrcnn-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5s2_tta` = [`voxelrcnn-ros-g1v5-s2`](../voxelrcnn-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5s3` = [`voxelrcnn-ros-g1v5-s3`](../voxelrcnn-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5s3_tta` = [`voxelrcnn-ros-g1v5-s3`](../voxelrcnn-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5s2` = [`pvrcnnpp-ros-g1v5-s2`](../pvrcnnpp-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5s2_tta` = [`pvrcnnpp-ros-g1v5-s2`](../pvrcnnpp-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5s3` = [`pvrcnnpp-ros-g1v5-s3`](../pvrcnnpp-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5s3_tta` = [`pvrcnnpp-ros-g1v5-s3`](../pvrcnnpp-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagvr5` = [`bag-voxelrcnn-ros-g1v5`](../bag-voxelrcnn-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagvr5_tta` = [`bag-voxelrcnn-ros-g1v5`](../bag-voxelrcnn-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagpv5` = [`bag-pvrcnnpp-ros-g1v5`](../bag-pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagpv5_tta` = [`bag-pvrcnnpp-ros-g1v5`](../bag-pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagvr4` = [`bag-voxelrcnn-ros-g1v4`](../bag-voxelrcnn-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagvr4_tta` = [`bag-voxelrcnn-ros-g1v4`](../bag-voxelrcnn-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagpv4` = [`bag-pvrcnnpp-ros-g1v4`](../bag-pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagpv4_tta` = [`bag-pvrcnnpp-ros-g1v4`](../bag-pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S6 variant b (2026-10-16), not through the upload gate: the S6 portfolio with, per class, the fuse step's best joint-ranked candidate wherever the pooled A+B condition holds (P >= 0.9) without the +0.01 realval-B requirement; vehicle and truck change, pedestrian stays at R5 (pooled P 0.725). A complete system for a leaderboard comparison with routed-g8. |

R3 Engine G2-lite (docs/02-STRATEGY.md Section 8.7.1): the confirmed S5 portfolio routed-g5 (route, fusion and score floors are the incumbents) plus the R3 g1-v4 members; every change passes the class gate with the pooled A+B condition.

## Route (class -> member)

| vehicle | pedestrian | truck |
|---|---|---|
| pv_tta | vrros_tta | ut_tta |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration; also a gain on the pooled A+B frames (P(gain) >= 0.9).

Range-dependent z calibration of the routed classes (z += z0 + z_per_m x range): truck (0.0, 0.0075).

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| vehicle | bagvr5_tta + pvros4s2_tta | [1.0, 1.0] | 0.7 | pvros4s2_tta (-0.075, 0.005) |
| pedestrian | vrros_tta + vrros4_tta | [1.0, 1.0] | 0.5 | - |
| truck | pp5_tta + bagvr5_tta + bagpv5 | [1.0, 1.0, 1.0] | 0.5 | - |

## Score floors (server-cost budget, `route_predictions.py budget`)

| vehicle | pedestrian | truck |
|---|---|---|
| 0.01 | 0.1 | 0.075 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g8b --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-v2x-track/routed-g8b --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-v2x-track/routed-g8b                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g8b/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + calibration + fusion (pedestrian, truck, vehicle) + budget`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.727** | 0.865 | 0.380 | 0.936 |
| realval-B | 0.712 | 0.869 | 0.418 | 0.848 |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-16_s6b` | 995877 | combined 0.8931, mAP 0.6065, R 0.9332 |
