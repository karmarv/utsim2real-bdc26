# `routed-g1` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M11 (per-class routing) |
| Architecture | per-class routing of PointPillars G1 models |
| Members | `ut` = [`pointpillars-ut`](../pointpillars-ut) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1` = [`pointpillars-g1`](../pointpillars-g1) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v2` = [`pointpillars-g1v2`](../pointpillars-g1v2) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`), `g1v3` = [`pointpillars-g1v3`](../pointpillars-g1v3) (`train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`) |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (selected list: [`test/synthetic_ids.txt`](test/synthetic_ids.txt)) |
| Status | selected; first submission packaged 2026-10-02 (submissions/2026-10-02_first) |

Route chosen on real validation (see route_selection): vehicle from g1v2, pedestrian from g1v3 (walkers calibrated on legal real walkers, FOV mask), truck from the UT-only baseline. Realism frames from g1-v3 (FOV-masked, the corpus of the pedestrian member).

## Route (class -> member)

| vehicle | pedestrian | truck |
|---|---|---|
| g1v2 | g1v3 | ut |

Rule: best realval-A AP; within 0.005 of the best, the higher realval-B AP.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g1                                  # choose the route
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g1/test/make_submission.sh <tag> "<team>"                      # zip + validation + local score
```

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `routed (official metric)`.

| Split | mAP (classes with test GT) | vehicle | pedestrian | truck |
|---|---|---|---|---|
| realval-A | **0.572** | 0.627 | 0.266 | 0.822 |
| realval-B | 0.520 | 0.662 | 0.226 | 0.673 |

Realism on held-out legal proxies: realism-proxy-4 R 0.9188, realism-proxy-5 R 0.9192.
Combined estimate: A 0.8577, B 0.8136.

## Submissions

| Folder | CodaBench id | Leaderboard |
|---|---|---|
| `2026-10-02_first` | - | - |
