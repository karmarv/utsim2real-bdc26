# `voxelrcnn-g1v3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | Voxel R-CNN: CenterPoint proposals (sparse 3D voxels 0.1 x 0.1 x 0.25 m, VoxelResBackBone8x) refined by voxel RoI grid pooling (6 x 6 x 6) with an IoU-quality score, xyz only |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S4 member: trained 40 epochs, per-class score blend chosen on A, tuned plain (A 0.263 / B 0.158) and TTA (0.295 / 0.170); in the routed-g4 Bicycle fusion |

S4 Two-Stage Refinement (docs/02-STRATEGY.md Section 8.4): same corpus, voxels, head groups and augmentation as centerpoint-g1v3; only the second stage is added, so the comparison isolates the refinement.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/voxelrcnn-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-g1v3/validation/tune_and_eval.sh model-lumpi-track/voxelrcnn-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.6, recenter 0.25, z_offset 0.1, size_scale [0.92, 0.92, 1.0] |
| Car | nms_iou 0.6 |
| Bicycle | nms_iou 0.1, recenter 0.5, z_offset 0.1, size_scale [1.16, 1.16, 1.08] |
| Motorcycle | nms_iou 0.4 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.6, z_offset -0.1, size_scale [1.16, 1.16, 1.16] |
| Van | defaults |
| Unknown | defaults |
| hedges | Bicycle -> Person x0.3; Van -> Car x0.6, Truck x0.1; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Bus -> Truck x0.6; Car -> Van x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.263** | 0.189 | 0.879 | 0.431 | 0.083 | 0.008 | 0.136 | 0.114 | 0.000 |
| realval-B | 0.158 | 0.041 | 0.775 | 0.163 | 0.033 | 0.006 | 0.089 | 0.001 | - |

