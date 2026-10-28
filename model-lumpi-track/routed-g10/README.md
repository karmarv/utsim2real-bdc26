# `routed-g10` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (TTA and fusion) with two-stage members |
| Architecture | per-class routing and box fusion (up to 3 members) of PointPillars, CenterPoint and two-stage members trained on g1-v3 and on the R3 corpus g1-v4 (engine G2-lite), with test-time augmentation |
| Members | `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1_tta` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3_tta` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp_tta` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4_tta` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vr` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vr_tta` = [`voxelrcnn-g1v3`](../voxelrcnn-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pv` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pv_tta` = [`pvrcnnpp-g1v3`](../pvrcnnpp-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrgb` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrgb_tta` = [`voxelrcnn-gblobs-g1v3`](../voxelrcnn-gblobs-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros_tta` = [`voxelrcnn-ros-g1v3`](../voxelrcnn-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros_tta` = [`pvrcnnpp-ros-g1v3`](../pvrcnnpp-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros_tta` = [`pointpillars-ros-g1v3`](../pointpillars-ros-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pp4` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pp4_tta` = [`pointpillars-g1v4`](../pointpillars-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4_tta` = [`voxelrcnn-ros-g1v4`](../voxelrcnn-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4_tta` = [`pvrcnnpp-ros-g1v4`](../pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `ppros4` = [`pointpillars-ros-g1v4`](../pointpillars-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `ppros4_tta` = [`pointpillars-ros-g1v4`](../pointpillars-ros-g1v4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4s2` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4s2_tta` = [`voxelrcnn-ros-g1v4-s2`](../voxelrcnn-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4s2` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4s2_tta` = [`pvrcnnpp-ros-g1v4-s2`](../pvrcnnpp-ros-g1v4-s2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4s3` = [`voxelrcnn-ros-g1v4-s3`](../voxelrcnn-ros-g1v4-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4s3_tta` = [`voxelrcnn-ros-g1v4-s3`](../voxelrcnn-ros-g1v4-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4s4` = [`voxelrcnn-ros-g1v4-s4`](../voxelrcnn-ros-g1v4-s4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4s4_tta` = [`voxelrcnn-ros-g1v4-s4`](../voxelrcnn-ros-g1v4-s4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4s3` = [`pvrcnnpp-ros-g1v4-s3`](../pvrcnnpp-ros-g1v4-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4s3_tta` = [`pvrcnnpp-ros-g1v4-s3`](../pvrcnnpp-ros-g1v4-s3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4s4` = [`pvrcnnpp-ros-g1v4-s4`](../pvrcnnpp-ros-g1v4-s4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4s4_tta` = [`pvrcnnpp-ros-g1v4-s4`](../pvrcnnpp-ros-g1v4-s4) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagvr4` = [`bag-voxelrcnn-ros-g1v4`](../bag-voxelrcnn-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagvr4_tta` = [`bag-voxelrcnn-ros-g1v4`](../bag-voxelrcnn-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagpv4` = [`bag-pvrcnnpp-ros-g1v4`](../bag-pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagpv4_tta` = [`bag-pvrcnnpp-ros-g1v4`](../bag-pvrcnnpp-ros-g1v4) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4d2` = [`voxelrcnn-ros-g1v4d2`](../voxelrcnn-ros-g1v4d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4d2_tta` = [`voxelrcnn-ros-g1v4d2`](../voxelrcnn-ros-g1v4d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `vrros4d3` = [`voxelrcnn-ros-g1v4d3`](../voxelrcnn-ros-g1v4d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `vrros4d3_tta` = [`voxelrcnn-ros-g1v4d3`](../voxelrcnn-ros-g1v4d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4d2` = [`pvrcnnpp-ros-g1v4d2`](../pvrcnnpp-ros-g1v4d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4d2_tta` = [`pvrcnnpp-ros-g1v4d2`](../pvrcnnpp-ros-g1v4d2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `pvros4d3` = [`pvrcnnpp-ros-g1v4d3`](../pvrcnnpp-ros-g1v4d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `pvros4d3_tta` = [`pvrcnnpp-ros-g1v4d3`](../pvrcnnpp-ros-g1v4d3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagvr4x` = [`bag-voxelrcnn-ros-g1v4x`](../bag-voxelrcnn-ros-g1v4x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagvr4x_tta` = [`bag-voxelrcnn-ros-g1v4x`](../bag-voxelrcnn-ros-g1v4x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`), `bagpv4x` = [`bag-pvrcnnpp-ros-g1v4x`](../bag-pvrcnnpp-ros-g1v4x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`), `bagpv4x_tta` = [`bag-pvrcnnpp-ros-g1v4x`](../bag-pvrcnnpp-ros-g1v4x) (`train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth`, TTA `flip4+yaw+z`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v4` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S7.6, the LUMPI entry and F1: submitted 1014495, combined 0.522846 (mAP 0.1749), rank 1 of 22 (2026-10-27); routed-g9 before its final-check freeze, the extended bags swapped into the incumbent fusions, the pooled budget (docs/decisions/2026-10-26-s7-final-revisions.md) |

S7.6 amendment (docs/decisions/2026-10-26-s7-final-revisions.md).

## Route (class -> member)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| ppros4_tta | pv_tta | vrros_tta | g1v3 | pp4_tta | pvros4d2_tta | g1 | g1 |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration; also a gain on the pooled A+B frames (P(gain) >= 0.9).

## Fusion (classes replaced by the fused members, `route_predictions.py fuse`)

| Class | Members | Weights | BEV IoU | Member z calibration |
|---|---|---|---|---|
| Car | pvros_tta + bagpv4x_tta | [1.0, 1.0] | 0.7 | - |
| Bicycle | vrros_tta + pvros4_tta + pp4_tta | [1.0, 1.0, 1.0] | 0.7 | - |
| Bus | ppros4_tta + vrros_tta | [1.0, 1.0] | 0.3 | - |
| Van | vrros + vrros4_tta + g1_tta | [1.0, 1.0, 1.0] | 0.5 | - |
| Person | pp4_tta + vrros4s2_tta | [1.0, 1.0] | 0.5 | - |
| Truck | pvros4d2_tta + ppros_tta | [1.0, 1.0] | 0.3 | - |

## Score floors (server-cost budget, `route_predictions.py budget`)

| Person | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|
| 0.01 | 0.02 | 0.3 | 0.075 | 0.03 | 0.05 | 0.075 |

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g10 --rule joint --calibrated                                  # choose the route
python common/tools/route_predictions.py fuse model-lumpi-track/routed-g10 --max-members 3                                    # per-class fusion (class gate)
python common/tools/route_predictions.py budget model-lumpi-track/routed-g10                                  # per-class score floors
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g10/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + fusion (Bicycle, Bus, Car, Person, Truck, Van) + budget`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.388** | 0.465 | 0.905 | 0.600 | 0.008 | 0.079 | 0.487 | 0.173 | 0.002 |
| realval-B | 0.225 | 0.160 | 0.798 | 0.264 | 0.013 | 0.134 | 0.205 | 0.002 | - |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-27_s7s` | 1014495 | combined 0.5228, mAP 0.1749, R 0.9323 |
