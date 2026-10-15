# `routed-g7` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage members trained on g1-v3 and on the R3 corpus g1-v4 (engine G2-lite), with test-time augmentation |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ut_tta` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2_tta` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrgb` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrgb_tta` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros_tta` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros_tta` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros_tta` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp4` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp4_tta` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4_tta` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4_tta` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4s2` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4s2_tta` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4s2` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4s2_tta` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp5` = [`pointpillars-g1v5`](../pointpillars-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp5_tta` = [`pointpillars-g1v5`](../pointpillars-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5` = [`voxelrcnn-ros-g1v5`](../voxelrcnn-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5_tta` = [`voxelrcnn-ros-g1v5`](../voxelrcnn-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5` = [`pvrcnnpp-ros-g1v5`](../pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5_tta` = [`pvrcnnpp-ros-g1v5`](../pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | R5: decision-ready (A 0.714 / B 0.710, R 0.937, estimate 0.983, upload gate passed); package submissions/2026-10-14_r5 |

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
| vehicle | pvros4s2_tta + vrros4s2_tta + vrros5_tta | [1.0, 1.0, 1.0] | 0.7 | pvros4s2_tta (-0.075, 0.005) |
| pedestrian | vrros_tta + vrros4_tta | [1.0, 1.0] | 0.5 | - |
| truck | ut_tta + vrros_tta + pvros_tta | [1.0, 1.0, 1.0] | 0.5 | ut_tta (0.0, 0.0075) |

## Score floors (server-cost budget, `route_predictions.py budget`)

| vehicle | pedestrian | truck |
|---|---|---|
| 0.01 | 0.1 | 0.1 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g7 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-v2x-track/routed-g7 --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-v2x-track/routed-g7                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g7/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + calibration + fusion (pedestrian, truck, vehicle) + budget`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.714** | 0.857 | 0.380 | 0.905 |
| realval-B | 0.710 | 0.864 | 0.418 | 0.848 |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-14_r5` | 990255 | combined 0.8852, mAP 0.5972, R 0.9332 |
