# `pvrcnnpp-ros-g1v4` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) |
| Architecture | PV-RCNN++ (as pvrcnnpp-ros-g1v3) with generic ROS |
| Training data | `pcdet/g1-v4` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | R3: trained 40 epochs (ROS capped), tuned plain and TTA (0.342 / 0.191); Person, Bicycle and Motorcycle pass; Bicycle and Truck fusions of routed-g6 |

R3 (docs/02-STRATEGY.md Section 8.7.1): trained on pcdet/g1-v4 = the g1-v3 recipe plus engine G2-lite (actors re-cast at real size and density, real-sized trucks, buses and two-wheelers with riders, unlabeled static clutter as hard negatives). The ROS ranges keep only the generic jitter (and the V2X truck width/height range) because the corpus now has real label sizes: the S5 Bicycle and Truck length ranges would scale real-sized objects a second time.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pvrcnnpp-ros-g1v4/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v4/validation/tune_and_eval.sh model-lumpi-track/pvrcnnpp-ros-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v4/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v4/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pvrcnnpp-ros-g1v4/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.7, recenter 0.5, size_scale [0.92, 0.92, 1.0] |
| Car | nms_iou 0.7 |
| Bicycle | nms_iou 0.6, recenter 0.5, size_scale [1.0, 1.0, 1.0] |
| Motorcycle | nms_iou 0.4, recenter 0.25 |
| Bus | nms_iou 0.7 |
| Truck | nms_iou 0.4, z_offset 0.0, size_scale [1.16, 1.16, 1.0] |
| Van | nms_iou 0.1 |
| Unknown | defaults |
| hedges | Bicycle -> Person x0.3; Van -> Car x0.6, Truck x0.1; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.3; Bus -> Truck x0.6; Car -> Van x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.317** | 0.329 | 0.874 | 0.452 | 0.056 | 0.017 | 0.353 | 0.136 | 0.000 |
| realval-B | 0.179 | 0.077 | 0.764 | 0.199 | 0.034 | 0.072 | 0.107 | 0.001 | - |

