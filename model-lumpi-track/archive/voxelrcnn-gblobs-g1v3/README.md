# `voxelrcnn-gblobs-g1v3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | Voxel R-CNN (as voxelrcnn-g1v3) with GBlobs inputs: per voxel the mean's offset from the voxel centre and the covariance over its 0.4 x 0.4 x 0.5 m cell (12 values, no absolute xyz) |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S5 run a: trained 40 epochs, tuned plain (A 0.248 / B 0.154) and TTA (0.276 / 0.162); below voxelrcnn-g1v3 (Person 0.189 -> 0.098 on A) |

S5 run a (docs/02-STRATEGY.md Section 8.5): only the VFE changes against voxelrcnn-g1v3.

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/voxelrcnn-gblobs-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-gblobs-g1v3/validation/tune_and_eval.sh model-lumpi-track/voxelrcnn-gblobs-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-gblobs-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-gblobs-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/voxelrcnn-gblobs-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.7, recenter 0.5, size_scale [0.85, 0.85, 1.0] |
| Car | nms_iou 0.5 |
| Bicycle | nms_iou 0.01, recenter 0.5, size_scale [1.16, 1.16, 1.08] |
| Motorcycle | nms_iou 0.4 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.01, size_scale [1.16, 1.16, 1.08] |
| Van | nms_iou 0.1, size_scale [0.92, 0.92, 1.0] |
| Unknown | defaults |
| hedges | Van -> Car x0.6, Truck x0.1; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Bus -> Truck x0.3; Car -> Van x0.1 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.248** | 0.098 | 0.883 | 0.422 | 0.079 | 0.010 | 0.127 | 0.114 | 0.000 |
| realval-B | 0.154 | 0.027 | 0.779 | 0.159 | 0.029 | 0.009 | 0.071 | 0.001 | - |

