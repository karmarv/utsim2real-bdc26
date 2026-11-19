# Track 2 (V2X-Real): the final system `routed-s10-4-v4`

Final ranked entry of Team KarmaRV on the V2X-Real track (CodaBench competition 16685): **submission 1051825**, combined
**0.894399** (3D mAP@0.5 R40 0.604516, realism R 0.940605), **joint 1st of 46 teams**. Release
[10.4](https://github.com/karmarv/utsim2real-bdc26/releases/tag/10.4) holds its checkpoints. To reproduce it, follow the
[root README](../README.md#4-reproduce-the-final-submissions). The track's development history is in
[`DEVELOPMENT.md`](DEVELOPMENT.md).

## 1. What is in this folder

| Folder | Role in the final system |
|---|---|
| [`routed-s10-4-v4/`](routed-s10-4-v4) | the system card [`model.yaml`](routed-s10-4-v4/model.yaml) (members, fusion, stages), the reproduction scripts in `test/`, the scored zip, the server record and the saved member test predictions in `submissions/2026-11-13_s10-4-v4/` |
| [`voxelrcnn-ros-g1v6`](voxelrcnn-ros-g1v6), [`-g1v6d2`](voxelrcnn-ros-g1v6d2), [`-g1v6d3`](voxelrcnn-ros-g1v6d3), [`-g1v6d4`](voxelrcnn-ros-g1v6d4), [`-g1v6d5`](voxelrcnn-ros-g1v6d5) | Voxel R-CNN with class-wise random object scaling (ROS), one per generator draw of the `g1-v6` corpus (training seed 666 each) |
| [`voxelrcnn-rosf-g1v6`](voxelrcnn-rosf-g1v6) | the same detector with GT-sampling fade (off in the last 5 epochs) and +/-1.5 deg pitch and roll augmentation |
| [`dsvt-ros-g1v6`](dsvt-ros-g1v6) | DSVT-Pillar (0.2 m pillars, CenterPoint head) with ROS |
| [`bag-voxelrcnn-ros-g1v6x`](bag-voxelrcnn-ros-g1v6x) | seed bag: weighted box fusion of draws 1 and 2 (no checkpoint of its own) |
| [`bag-voxelrcnn-ros-g1v6x5`](bag-voxelrcnn-ros-g1v6x5) | seed bag of draws 1 to 5 (no checkpoint of its own) |
| [`registry.csv`](registry.csv) | the track's model registry (all models of the development) |
| [`archive/`](archive) | every other model folder of the development; not needed to reproduce the entry |

Each member folder holds `model.yaml` (architecture, corpus, seed), `train/` (OpenPCDet config `pcdet_model.yaml` and
`train.sh`), `test/` (the tuned post-processing files `postprocess*.yaml` used at inference) and `validation/results/`
(scores on real validation data).

## 2. The system

All seven checkpoints are trained on synthetic data only (the `g1-v6` corpus family). At test time:

1. **Members with test-time augmentation**: 4 views (`tta`: flips, yaw, z shift) or 12 views (`tta12`: also scale).

| Class | Fused members (weighted box fusion) | IoU |
|---|---|---|
| vehicle | `bvrros6x_tta12` (2-draw Voxel R-CNN bag, 12 views) + `dsros6_tta` (DSVT, 4 views) | 0.5 |
| pedestrian | `vrros6d2_tta12` + `vrros6_tta12` + `vrrosf6_tta12` (three Voxel R-CNN members, 12 views) | 0.5 |
| truck | `bvrros6x5_tta` (5-draw Voxel R-CNN bag, 4 views) + `vrrosf6_tta12` | 0.7 |

2. **Stages**, in order (all in [`common/tools/route_predictions.py`](../common/tools/route_predictions.py)):
   - score floor per class (vehicle 0.01, pedestrian and truck 0.05), tail copies (pedestrian boxes copied with a
     0.15 m shift, each copy ranked below every pedestrian box);
   - sparse demotion (boxes with fewer points than the real labels' visibility cut ranked last: vehicle 6,
     pedestrian 6, truck 8) and overhead demotion (pedestrian);
   - anchored size calibration (vehicle length -0.3 m, height +0.03 m);
   - final size step: pedestrian height 50% of the way to the realval-A median (1.73 m, bottom kept), vehicle length and
     width 25% of the way to the realval-A median (4.64 x 2.06 m). No box is added, removed or rescored by this step.
3. **Packaging**: predictions plus 50 synthetic frames from `g1-v6`
   ([`synthetic_ids.txt`](routed-s10-4-v4/test/synthetic_ids.txt)); packaging adds the sensor's no-return points
   (31% of each frame).

## 3. Scores

| | vehicle | pedestrian | truck | mAP | R | Combined |
|---|---|---|---|---|---|---|
| Leaderboard 1051825 (test) | 0.7432 | 0.4109 | 0.6595 | 0.6045 | 0.9406 | **0.8944** |
| realval-A (local, legal real frames) | 0.8732 | 0.4091 | 0.9113 | 0.7312 | | |
| realval-B (local) | 0.8810 | 0.4013 | 0.8528 | 0.7117 | | |

Truck's validation scores overstate its test AP (124 test boxes); see the V2X-Real report in
[`docs/paper-bigdata2026/final-report/`](../docs/paper-bigdata2026/final-report).

## 4. Reproduce

Check 1, exact re-merge (no GPU, no checkpoint; the starting kit ingested): the saved member predictions merged with
the committed card give the scored `predictions.json` identically.

```bash
python common/tools/reproduce_submission.py model-v2x-track/routed-s10-4-v4 --tag s10-4-v4 --saved
```

Check 2, full re-inference from the released checkpoints (one GPU):

```bash
python common/tools/release_weights.py fetch --tag 10.4 --version v2x:s10-4-v4
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-s10-4-v4/test/reproduce_s10-4-v4.sh
```

Setup (prerequisites, environment, starting kits, checkpoints): [root README Sections 4.1-4.4](../README.md#4-reproduce-the-final-submissions).
Expected output of both commands: [root README Section 4.5](../README.md#45-v2x-real-track-reproduce-entry-1051825).
With the real validation data prepared, `test/reproduce_s10-4-v4_validation.sh` recomputes the local scores above.
