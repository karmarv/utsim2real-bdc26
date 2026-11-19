# `voxelrcnn-ros-g1v5m` (v2x-track)

> Model card: [`model.yaml`](model.yaml). Track guide: [`../README.md`](../README.md). Developer guide: [root README](../../README.md).

| | |
|---|---|
| Module | M9 (engine G2-lite) + S7 label visibility rule |
| Architecture | Voxel R-CNN (as voxelrcnn-ros-g1v3) with ROS (truck length range removed) |
| Training data | `pcdet/g1-v5m` |
| Real validation | `pcdet/realval-v1` (split `val` = realval-A, `valB` = realval-B) |
| Realism frames | `pcdet/g1-v5` (random 50 of the val split until selected) |
| Status | planned (S7 run, seed 666) |

S7 (docs/02-STRATEGY.md Section 8.11, record docs/decisions/2026-10-18-s7-visibility-rule.md): the voxelrcnn-ros-g1v5 config, seed 666, on pcdet/g1-v5m = the g1-v5 frames with labels of fewer points than the real 2nd percentile removed (pedestrian 6, vehicle 8, truck 17; common/tools/filter_labels.py). Paired with voxelrcnn-ros-g1v5 (same seed, same frames).

## Commands

From the repository root after `source common/env/activate.sh`:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-v2x-track/voxelrcnn-ros-g1v5m/train/train.sh 4 run1 --fix_random_seed --workers 6      # train
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5m/validation/tune_and_eval.sh model-v2x-track/voxelrcnn-ros-g1v5m/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth   # validate + tune
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5m/validation/tune_and_eval.sh <ckpt> --eval-only                # re-score only
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5m/test/predict.sh <ckpt>                                       # predict the 50 kit frames
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/voxelrcnn-ros-g1v5m/test/make_submission.sh <ckpt> <tag> [team]                 # zip + validation + local score
```

## Configuration

- [`train/pcdet_model.yaml`](train/pcdet_model.yaml) (+ [`train/pcdet_dataset.yaml`](train/pcdet_dataset.yaml)): classes ['vehicle', 'pedestrian', 'truck'], 40 epochs, batch 4 per GPU, adam_onecycle LR 0.003.

## Post-processing ([`test/postprocess.yaml`](test/postprocess.yaml))

Selected by `tune_postprocess.py` on pcdet/realval-v1:val (real train split, guard-allowed).

| Class | Settings |
|---|---|
| vehicle | nms_iou 0.6, size_scale [1.0, 1.0, 1.08] |
| pedestrian | nms_iou 0.7, recenter 0.25, z_offset -0.1 |
| truck | z_offset 0.0, size_scale [1.08, 1.08, 1.0] |
| hedges | truck -> vehicle x0.3; vehicle -> truck x0.3 |
