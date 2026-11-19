# Track 1 (LUMPI): the final system `routed-s10-5-l12e`

Final ranked entry of Team KarmaRV on the LUMPI track (CodaBench competition 16684): **submission 1053789**, combined
**0.542997** (3D mAP@0.5 R40 0.197537, realism R 0.9342), **2nd of 44 teams**. The organizers confirmed 1053789 as the
entry on record on Nov 18, 2026. Release [10.5](https://github.com/karmarv/utsim2real-bdc26/releases/tag/10.5) holds its
checkpoints. To reproduce it, follow the [root README](../README.md#4-reproduce-the-final-submissions). The track's
development history is in [`DEVELOPMENT.md`](DEVELOPMENT.md).

## 1. What is in this folder

| Folder | Role in the final system |
|---|---|
| [`routed-s10-5-l12e/`](routed-s10-5-l12e) | the system card [`model.yaml`](routed-s10-5-l12e/model.yaml) (members, routes, fusion, stages), the reproduction scripts in `test/`, the scored zip, the server record and the saved member test predictions in `submissions/2026-11-15_s10-5-l12e/` |
| [`voxelrcnn-rosf-g1v6`](voxelrcnn-rosf-g1v6), [`voxelrcnn-rosf-g1v6d2`](voxelrcnn-rosf-g1v6d2) | Voxel R-CNN with class-wise random object scaling (ROS), GT-sampling fade (off in the last 5 epochs) and +/-1.5 deg pitch and roll; generator draws 1 and 2 |
| [`voxelrcnn-rosn-g1v6`](voxelrcnn-rosn-g1v6), [`voxelrcnn-rosn-g1v6d2`](voxelrcnn-rosn-g1v6d2) | the same without GT sampling; draws 1 and 2 |
| [`voxelrcnn-rosf-g1v6j`](voxelrcnn-rosf-g1v6j) | `voxelrcnn-rosf` trained on both draws together (`g1-v6j`, 18,000 frames) |
| [`pvrcnnpp-ros-g1v6`](pvrcnnpp-ros-g1v6), [`pvrcnnpp-ros-g1v6d2`](pvrcnnpp-ros-g1v6d2), [`pvrcnnpp-ros-g1v6j`](pvrcnnpp-ros-g1v6j) | PV-RCNN++ with ROS; draw 1, draw 2, both draws |
| [`pointpillars-ros-g1v6`](pointpillars-ros-g1v6), [`pointpillars-ros-g1v6d2`](pointpillars-ros-g1v6d2), [`pointpillars-rosf-g1v6`](pointpillars-rosf-g1v6) | PointPillars with ROS (anchors at the training-label medians); draws 1 and 2; with fade and pitch/roll |
| [`voxelnext-rosn-g1v6`](voxelnext-rosn-g1v6), [`voxelnext-rosf-g1v6d2`](voxelnext-rosf-g1v6d2) | VoxelNeXt with ROS, without GT sampling (draw 1) and with fade (draw 2) |
| [`dsvt-rosf-g1v6`](dsvt-rosf-g1v6) | DSVT-Pillar with ROS, fade and pitch/roll |
| [`bag-voxelrcnn-rosf-g1v6x`](bag-voxelrcnn-rosf-g1v6x), [`bag-voxelrcnn-rosn-g1v6x`](bag-voxelrcnn-rosn-g1v6x), [`bag-pvrcnnpp-ros-g1v6x`](bag-pvrcnnpp-ros-g1v6x) | seed bags: weighted box fusion of the draw-1 and draw-2 members (no checkpoint of their own) |
| [`registry.csv`](registry.csv) | the track's model registry (all models of the development) |
| [`archive/`](archive) | every other model folder of the development; not needed to reproduce the entry |

Each member folder holds `model.yaml` (architecture, corpus, seed), `train/` (OpenPCDet config `pcdet_model.yaml` and
`train.sh`), `test/` (the tuned post-processing files `postprocess*.yaml` used at inference) and `validation/results/`
(scores on real validation data).

## 2. The system

All 14 checkpoints are trained on synthetic data only (the UT-LUMPI-based `g1-v6` corpus family). At test time:

1. **Members with test-time augmentation**: 4 views (`tta`: flips, yaw, z shift) or 12 views (`tta12`: also scale).

| Class | Members | Combination |
|---|---|---|
| Person | `vrrosn6_tta12` + `bvrrosf6x_tta12` | fusion, IoU 0.7 |
| Car | `vrrosf6_tta12` + `bvrrosn6x_tta` + `vrrosf6j_tta12` | fusion, IoU 0.7 |
| Bicycle | `ppros6d2_tta` + `dsrosf6_tta12` + `pvros6j_tta12` | fusion, IoU 0.5 |
| Motorcycle | `vnrosn6_tta12` + `vnrosf6d2_tta` | fusion, IoU 0.7 |
| Truck | `bpvros6x_tta` + `pvros6j_tta` | fusion, IoU 0.7 |
| Bus | `ppros6_tta` | routed |
| Van | `dsrosf6_tta12` | routed |
| Unknown (not scored; no test labels) | `pprosf6_tta` | routed |

2. **Stages**, in order (all in [`common/tools/route_predictions.py`](../common/tools/route_predictions.py)):
   - score floor per class (0.01; Unknown 0.075); tail copies (shifted copies of Bus boxes and of Person boxes above
     score 0.75), each copy ranked below every box of its class;
   - anchored size calibration around five scene anchors (Car length -0.20 m, width +0.08 m, height +0.07 m; Person
     height +0.03 m);
   - final adjustment: a size step toward the median real box sizes of the organizers' train split (Person height 50%
     of the way to 1.90 m; Car length and width 25% of the way to 4.48 x 1.99 m; Bicycle 25% of the way to 2.00 x
     0.85 m); Person duplicate copies; cross-class copies (Bus and Van boxes copied into Truck, Truck into Bus,
     Motorcycle into Bicycle, the top half of Bicycle into Person, the top 20% of Car into Van), each ranked below every
     box of the target class. Copies duplicate the detector's own boxes; no box is placed where the detectors placed
     none.
3. **Packaging**: 38,047 boxes and 50 synthetic frames from `g1-v6`
   ([`synthetic_ids.txt`](routed-s10-5-l12e/test/synthetic_ids.txt)), byte-identical to the corpus frames.

## 3. Scores

| | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | mAP | R | Combined |
|---|---|---|---|---|---|---|---|---|---|---|
| Leaderboard 1053789 (test) | 0.3159 | 0.6833 | 0.1427 | 0.0179 | 0.0004 | 0.0700 | 0.1525 | 0.1975 | 0.9342 | **0.5430** |
| realval-A (local, legal real frames) | 0.6101 | 0.9086 | 0.6545 | 0.2400 | 0.0108 | 0.3881 | 0.1086 | 0.4172 | | |
| realval-B (local) | 0.2502 | 0.8034 | 0.2868 | 0.0497 | 0.0645 | 0.2422 | 0.0012 | 0.2426 | | |

The gap between validation and test is discussed in the LUMPI report in
[`docs/paper-bigdata2026/final-report/`](../docs/paper-bigdata2026/final-report).

## 4. Reproduce

Check 1, exact re-merge (no GPU, no checkpoint; the starting kit ingested): the saved member predictions merged with
the committed card give the scored `predictions.json` identically.

```bash
python common/tools/reproduce_submission.py model-lumpi-track/routed-s10-5-l12e --tag s10-5-l12e --saved
```

Check 2, full re-inference from the released checkpoints (one GPU):

```bash
python common/tools/release_weights.py fetch --tag 10.5 --version lumpi:s10-5-l12e
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-s10-5-l12e/test/reproduce_s10-5-l12e.sh
```

Setup (prerequisites, environment, starting kits, checkpoints): [root README Sections 4.1-4.4](../README.md#4-reproduce-the-final-submissions).
Expected output of both commands: [root README Section 4.6](../README.md#46-lumpi-track-reproduce-entry-1053789).
With the real validation data prepared, `test/reproduce_s10-5-l12e_validation.sh` recomputes the local scores above.
