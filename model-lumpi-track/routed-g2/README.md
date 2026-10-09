# `routed-g2` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | per-class routing of PointPillars G1 models and a CenterPoint G1 model |
| Members | `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v2` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S2 candidate: Bicycle from cp (realval A 0.272 / B 0.170); below the upload gate (+0.003); package 2026-10-09_s2 checked, not uploaded |

S2 Center-Routed Small Objects (docs/02-STRATEGY.md Section 8.2): the members of routed-g1 plus centerpoint-g1v3 (cp). The route starts from the S1 route (the incumbent); a class moves to another member only through the class gate (route_predictions.py select --rule joint --calibrated), and the z calibration is re-selected with the route. Realism frames unchanged from routed-g1.

## Route (class -> member)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| g1v3 | g1 | cp | g1v3 | g1v3 | g1v3 | g1 | g1 |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g2                                  # choose the route
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g2/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric)`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.272** | 0.340 | 0.874 | 0.350 | 0.008 | 0.011 | 0.200 | 0.122 | 0.004 |
| realval-B | 0.170 | 0.134 | 0.770 | 0.128 | 0.015 | 0.012 | 0.131 | 0.001 | - |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-09_s2` | - | - |
