# `routed-g1` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (per-class routing) |
| Architecture | per-class routing of PointPillars G1 models |
| Members | `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v2` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | selected; first submission packaged and validated 2026-10-02 (submissions/2026-10-02_first) |

Route chosen on real validation (see route_selection). Members differ only in the walker model (v1 / v2).

## Route (class -> member)

| Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|
| g1v3 | g1 | g1 | g1v3 | g1v3 | g1v3 | g1 | g1 |

Rule: best realval-A AP; within 0.005 of the best, the higher realval-B AP.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g1                                  # choose the route
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g1/test/make_submission.sh <tag> "<team>"                      # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric)`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.260** | 0.340 | 0.874 | 0.265 | 0.008 | 0.011 | 0.200 | 0.122 | 0.004 |
| realval-B | 0.166 | 0.134 | 0.770 | 0.102 | 0.015 | 0.012 | 0.131 | 0.001 | - |

Realism on held-out legal proxies: realism-proxy-4 R 0.9057, realism-proxy-5 R 0.9049.
Combined estimate: A 0.5849, B 0.5047.

## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-02_first` | - | - |
