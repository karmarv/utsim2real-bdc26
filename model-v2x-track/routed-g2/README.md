# `routed-g2` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | per-class routing of PointPillars G1 models and a CenterPoint G1 model |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp` = [`centerpoint-g1v3`](../centerpoint-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `cp4` = [`centerpoint-s4-g1v3`](../centerpoint-s4-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | S2 candidate: route and calibration equal to S1+C1 (realval A 0.585 / B 0.537); no new version |

S2 Center-Routed Small Objects (docs/02-STRATEGY.md Section 8.2): the members of routed-g1z plus centerpoint-g1v3 (cp). The route starts from the S1+C1 route (the incumbent); a class moves to another member only through the class gate (route_predictions.py select --rule joint --calibrated), and the z calibration is re-selected with the route. Realism frames unchanged from routed-g1z.

## Route (class -> member)

| vehicle | pedestrian | truck |
|---|---|---|
| g1v2 | g1v3 | ut |

Rule: joint: rank members by the mean of realval-A and realval-B AP; a class leaves its current member only through the class gate (dB >= 0.01, paired bootstrap x200 P(gain) >= 0.9, dA >= -0.005); members compared with their gated z calibration.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g2                                  # choose the route
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g2/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric) + calibration`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.585** | 0.641 | 0.290 | 0.822 |
| realval-B | 0.537 | 0.685 | 0.252 | 0.673 |

