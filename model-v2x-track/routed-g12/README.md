# `routed-g12` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage members trained on g1-v3 and on the R3 corpus g1-v4 (engine G2-lite), with test-time augmentation |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ut_tta` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2_tta` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrgb` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrgb_tta` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros_tta` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros_tta` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros_tta` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp4` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp4_tta` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4_tta` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4_tta` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4s2` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4s2_tta` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4s2` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4s2_tta` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp5` = [`pointpillars-g1v5`](../pointpillars-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp5_tta` = [`pointpillars-g1v5`](../pointpillars-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5` = [`voxelrcnn-ros-g1v5`](../voxelrcnn-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5_tta` = [`voxelrcnn-ros-g1v5`](../voxelrcnn-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5` = [`pvrcnnpp-ros-g1v5`](../pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5_tta` = [`pvrcnnpp-ros-g1v5`](../pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5s2` = [`voxelrcnn-ros-g1v5-s2`](../voxelrcnn-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5s2_tta` = [`voxelrcnn-ros-g1v5-s2`](../voxelrcnn-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5s3` = [`voxelrcnn-ros-g1v5-s3`](../voxelrcnn-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5s3_tta` = [`voxelrcnn-ros-g1v5-s3`](../voxelrcnn-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5s2` = [`pvrcnnpp-ros-g1v5-s2`](../pvrcnnpp-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5s2_tta` = [`pvrcnnpp-ros-g1v5-s2`](../pvrcnnpp-ros-g1v5-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5s3` = [`pvrcnnpp-ros-g1v5-s3`](../pvrcnnpp-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5s3_tta` = [`pvrcnnpp-ros-g1v5-s3`](../pvrcnnpp-ros-g1v5-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagvr5` = [`bag-voxelrcnn-ros-g1v5`](../bag-voxelrcnn-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagvr5_tta` = [`bag-voxelrcnn-ros-g1v5`](../bag-voxelrcnn-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagpv5` = [`bag-pvrcnnpp-ros-g1v5`](../bag-pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagpv5_tta` = [`bag-pvrcnnpp-ros-g1v5`](../bag-pvrcnnpp-ros-g1v5) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagvr4` = [`bag-voxelrcnn-ros-g1v4`](../bag-voxelrcnn-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagvr4_tta` = [`bag-voxelrcnn-ros-g1v4`](../bag-voxelrcnn-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagpv4` = [`bag-pvrcnnpp-ros-g1v4`](../bag-pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagpv4_tta` = [`bag-pvrcnnpp-ros-g1v4`](../bag-pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5d2` = [`voxelrcnn-ros-g1v5d2`](../voxelrcnn-ros-g1v5d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5d2_tta` = [`voxelrcnn-ros-g1v5d2`](../voxelrcnn-ros-g1v5d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros5d3` = [`voxelrcnn-ros-g1v5d3`](../voxelrcnn-ros-g1v5d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros5d3_tta` = [`voxelrcnn-ros-g1v5d3`](../voxelrcnn-ros-g1v5d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5d2` = [`pvrcnnpp-ros-g1v5d2`](../pvrcnnpp-ros-g1v5d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5d2_tta` = [`pvrcnnpp-ros-g1v5d2`](../pvrcnnpp-ros-g1v5d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros5d3` = [`pvrcnnpp-ros-g1v5d3`](../pvrcnnpp-ros-g1v5d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros5d3_tta` = [`pvrcnnpp-ros-g1v5d3`](../pvrcnnpp-ros-g1v5d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagvr5x` = [`bag-voxelrcnn-ros-g1v5x`](../bag-voxelrcnn-ros-g1v5x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagvr5x_tta` = [`bag-voxelrcnn-ros-g1v5x`](../bag-voxelrcnn-ros-g1v5x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagpv5x` = [`bag-pvrcnnpp-ros-g1v5x`](../bag-pvrcnnpp-ros-g1v5x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagpv5x_tta` = [`bag-pvrcnnpp-ros-g1v5x`](../bag-pvrcnnpp-ros-g1v5x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S7.6, the V2X entry and F1: submitted 1014682, combined 0.898172, identical to 1001919 (routed-g9) in every metric (2026-10-27); routed-g11 before its final-check freeze, the extended bags swapped into the incumbent fusions, the pooled budget; no class changed (docs/decisions/2026-10-26-s7-final-revisions.md) |

S7.6 amendment (docs/decisions/2026-10-26-s7-final-revisions.md).

## Route (class -> member)

| vehicle | pedestrian | truck |
|---|---|---|
| pv_tta | vrros_tta | ut_tta |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration; also a gain on the pooled A+B frames (P(gain) >= 0.9).

Range-dependent z calibration of the routed classes (z += z0 + z_per_m x range): truck (0.0, 0.0075).

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| pedestrian | vrros_tta + vrros4_tta | [1.0, 1.0] | 0.5 | - |
| vehicle | bagvr5_tta + pvros4s2_tta | [1.0, 1.0] | 0.7 | pvros4s2_tta (-0.075, 0.005) |
| truck | pp5_tta + bagvr5_tta + bagpv5 | [1.0, 1.0, 1.0] | 0.5 | - |

## Score floors (server-cost budget, `route_predictions.py budget`)

| vehicle | pedestrian | truck |
|---|---|---|
| 0.01 | 0.1 | 0.075 |

## Sparse-box demotion (S7, `route_predictions.py sparse`)

A box with fewer points inside it than the threshold ranks below every other box of its class (nothing is deleted).

| vehicle | pedestrian |
|---|---|
| 5 | 6 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g12 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-v2x-track/routed-g12 --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-v2x-track/routed-g12                                  # per-class score floors
python common/tools/route_predictions.py sparse model-v2x-track/routed-g12                                  # S7 sparse-box demotion
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g12/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + calibration + fusion (pedestrian, truck, vehicle) + budget + sparse demotion`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.734** | 0.868 | 0.399 | 0.936 |
| realval-B | 0.721 | 0.872 | 0.441 | 0.848 |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-27_s7s` | 1014682 | combined 0.8982, mAP 0.6124, R 0.9332 |
