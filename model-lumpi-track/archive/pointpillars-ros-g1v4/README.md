# `pointpillars-ros-g1v4` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) |
| Architecture | PointPillars (as pointpillars-ros-g1v3), anchors at the g1-v4 label medians, generic ROS |
| Training data | `pcdet/g1-v4` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | R3: trained 40 epochs (ROS capped), tuned plain and TTA (0.327 / 0.193); Bicycle passes; Bus fusion of routed-g6 |

R3 (docs/02-STRATEGY.md Section 8.7.1): trained on pcdet/g1-v4 = the g1-v3 recipe plus engine G2-lite (actors re-cast at real size and density, real-sized trucks, buses and two-wheelers with riders, unlabeled static clutter as hard negatives). The ROS ranges keep only the generic jitter (and the V2X truck width/height range) because the corpus now has real label sizes: the S5 Bicycle and Truck length ranges would scale real-sized objects a second time.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pointpillars-ros-g1v4/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v4/validation/tune_and_eval.sh model-lumpi-track/pointpillars-ros-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v4/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v4/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-ros-g1v4/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 6 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.5, recenter 0.5, size_scale [0.85, 0.85, 1.0] |
| Car | nms_iou 0.5 |
| Bicycle | recenter 0.5, size_scale [1.0, 1.0, 1.0] |
| Motorcycle | nms_iou 0.4, recenter 0.25 |
| Bus | nms_iou 0.6 |
| Truck | nms_iou 0.5, size_scale [1.16, 1.16, 1.16], z_offset -0.3 |
| Van | nms_iou 0.01, size_scale [1.08, 1.08, 1.0] |
| Unknown | defaults |
| hedges | Bicycle -> Person x0.3; Van -> Car x0.6, Truck x0.6; Truck -> Car x0.1; Motorcycle -> Bicycle x0.6; Car -> Van x0.1 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.297** | 0.333 | 0.876 | 0.452 | 0.002 | 0.006 | 0.288 | 0.123 | 0.000 |
| realval-B | 0.178 | 0.107 | 0.752 | 0.203 | 0.009 | 0.021 | 0.151 | 0.001 | - |

