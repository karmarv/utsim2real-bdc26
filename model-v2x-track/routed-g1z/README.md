# `routed-g1z` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (per-class routing) |
| Architecture | per-class routing of PointPillars G1 models |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | submitted 2026-10-09 as CodaBench 972563 (S1 + C1), combined 0.7855; the current Track 2 entry |

S1 close-out candidate C1: the members, route and realism frames of routed-g1, plus a range-dependent z calibration after routing (z += z0 + z_per_m * range; vehicle and pedestrian; selected on realval-A, kept by the class gate on realval-B; route_predictions.py calibrate). realval-A 0.572 -> 0.585, realval-B 0.520 -> 0.537. Decision record docs/decisions/2026-10-09-s1-closeout-z-calibration.md.

## Route (class -> member)

| vehicle | pedestrian | truck |
|---|---|---|
| g1v2 | g1v3 | ut |

Rule: best realval-A AP; within 0.005 of the best, the higher realval-B AP.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g1z                                  # choose the route
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g1z/test/make_submission.sh <tag> [team]                        # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed + range-dependent z calibration (official metric)`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.585** | 0.641 | 0.290 | 0.822 |
| realval-B | 0.537 | 0.685 | 0.252 | 0.673 |


## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-09_zcal` | 972563 | combined 0.7855, mAP 0.4869, R 0.9203 |
