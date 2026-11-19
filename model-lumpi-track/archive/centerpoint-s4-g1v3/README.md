# `centerpoint-s4-g1v3` (lumpi-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M10 (detector routing by class) |
| Architecture | CenterPoint, stride-4 heads (0.4 m BEV cells), sparse 3D voxels 0.1 x 0.1 x 0.25 m, xyz only |
| Training data | `pcdet/g1-v3` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v3` (random 50 of the val split until selected) |
| Status | S2 variant: trained 40 epochs, tuned (realval A 0.230 / B 0.153); no class won |

S2 step 5 variant: Person and Motorcycle missed the class gate with stride 8 and the S1 diagnostics show sparse misses (Person recall 0.24 below 10 points).

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/centerpoint-s4-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/centerpoint-s4-g1v3/validation/tune_and_eval.sh model-lumpi-track/centerpoint-s4-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/centerpoint-s4-g1v3/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/centerpoint-s4-g1v3/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/centerpoint-s4-g1v3/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['Person', 'Car', 'Bicycle', 'Motorcycle', 'Bus', 'Truck', 'Van', 'Unknown'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| Person | nms_iou 0.7, recenter 0.5, z_offset 0.1, size_scale [0.85, 0.85, 0.92] |
| Car | nms_iou 0.5 |
| Bicycle | nms_iou 0.1, recenter 0.5, z_offset 0.1, size_scale [1.16, 1.16, 1.0] |
| Motorcycle | nms_iou 0.4, recenter 0.25 |
| Bus | nms_iou 0.1 |
| Truck | nms_iou 0.6, z_offset -0.1, size_scale [1.08, 1.08, 1.08] |
| Van | defaults |
| Unknown | defaults |
| hedges | Van -> Car x0.6, Truck x0.3; Motorcycle -> Bicycle x0.6; Truck -> Bus x0.6; Car -> Van x0.3 |

## Latest real-validation result (official metric, 3D AP@0.5 R40)

Checkpoint: `checkpoint_epoch_40.pth`.

| Split | mAP (classes with test GT) | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | Unknown |
|---|---|---|---|---|---|---|---|---|---|
| realval-A | **0.230** | 0.168 | 0.844 | 0.318 | 0.057 | 0.017 | 0.118 | 0.087 | 0.000 |
| realval-B | 0.153 | 0.047 | 0.749 | 0.134 | 0.023 | 0.007 | 0.109 | 0.001 | - |

