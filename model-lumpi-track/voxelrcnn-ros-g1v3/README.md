# `voxelrcnn-ros-g1v3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | Voxel R-CNN (as voxelrcnn-g1v3) trained with class-wise random object scaling (ROS) |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S5 run b: trained 40 epochs, tuned plain (A 0.301 / B 0.175) and TTA (0.322 / 0.189); above voxelrcnn-g1v3 (TTA B +0.019: Bicycle +0.025, Truck +0.024, Bus +0.067) |

S5 run b (docs/02-STRATEGY.md Section 8.5): only the augmentation changes against voxelrcnn-g1v3.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/voxelrcnn-ros-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-ros-g1v3/validation/tune_and_eval.sh model-lumpi-track/voxelrcnn-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-ros-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-ros-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-ros-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.7, recenter 0.5, size_scale [0.92, 0.92, 1.0] |
| Car | nms_iou 0.7 |
| Bicycle | nms_iou 0.6, recenter 0.5, size_scale [1.08, 1.08, 1.0] |
| Motorcycle | nms_iou 0.4, recenter 0.25 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.01, size_scale [1.08, 1.08, 1.08] |
| Van | nms_iou 0.1 |
| Unknown | defaults |
| hedges | Bicycle -> Person x0.3; Van -> Car x0.6, Truck x0.3, Unknown x0.1; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Car -> Van x0.1 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.301** | 0.209 | 0.879 | 0.492 | 0.015 | 0.015 | 0.337 | 0.160 | 0.005 |
| realval-B | 0.175 | 0.073 | 0.776 | 0.182 | 0.007 | 0.058 | 0.132 | 0.001 | - |

