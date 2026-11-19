# 2026-10-11 S5 Geometry-Invariant Inputs: object scaling wins, GBlobs only inside fusions; V2X confirmed (0.8730), LUMPI flat (not confirmed, diagnosed)

**Version.** `model-<track>/routed-g5` (strategy S5): the `routed-g4` portfolio plus four S5 Voxel R-CNN, PV-RCNN++ and PointPillars runs (plain and TTA): `voxelrcnn-gblobs-g1v3` (run a), `voxelrcnn-ros-g1v3` (run b), `pvrcnnpp-ros-g1v3` and `pointpillars-ros-g1v3` (ROS extension). Packages `routed-g5/submissions/2026-10-11_s5/` with the upload copies `v2x_s5_submission.zip` and `lumpi_s5_submission.zip`. Strategy: [`02-STRATEGY.md` Section 8.5](../02-STRATEGY.md#85-s5-geometry-invariant-inputs) (review and revised plan), results in 8.5.1.

**Context.** S5 tested two source-only ways to make the detector read geometry from the points. The review changed both: GBlobs as published computes a covariance per voxel, but 80-83% of our 0.1 m voxels hold one point (its own failure case), so the covariance is taken over 0.4 x 0.4 x 0.5 m cells; and legal real label statistics showed the size gap is in bicycles and trucks, not walkers, which set the class-wise object scaling (ROS) ranges. Dropout augmentations were dropped (no density gap).

**Evidence** (official 3D AP@0.5 R40, realval-A / realval-B; TTA members against `voxelrcnn-g1v3`: GBlobs V2X 0.635 / 0.621 vs 0.647 / 0.632, LUMPI 0.276 / 0.162 vs 0.295 / 0.170; ROS V2X **0.664 / 0.667**, LUMPI **0.322 / 0.189**):

| Track / class | S4 | S5 | Source | dB vs S4 (P) |
|---|---|---|---|---|
| V2X pedestrian | 0.350 / 0.361 | **0.350 / 0.397** | `vrros_tta` + `pv_tta` | +0.036 (1.00) |
| V2X truck | 0.896 / 0.834 | **0.905 / 0.848** | `ut_tta` + `vrros_tta` + `pvros_tta` | +0.014 (0.98) |
| V2X vehicle | 0.806 / 0.843 | **0.828 / 0.852** | `vrgb_tta` + `pv_tta` + `pvros_tta` | +0.009 (0.99; +0.011 before the score floors) |
| V2X mAP | 0.684 / 0.679 | **0.694 / 0.699** | | +0.020 (+0.012 to +0.024) |
| LUMPI Truck / Bus / Bicycle / Car | 0.231 / 0.153, 0.011 / 0.011, 0.525 / 0.202, 0.898 / 0.792 | 0.433 / 0.200, 0.016 / 0.075, 0.565 / 0.225, 0.909 / 0.806 | ROS two-stage and pillar members; GBlobs in the Car fusion | +0.047, +0.064, +0.023, +0.014 |
| LUMPI mAP (late-A) | 0.313 / 0.188 (0.304) | **0.350 / 0.209 (0.335)** | | +0.021 (+0.017 to +0.024) |

ROS fixes what the size gap breaks: V2X truck localization loss on B 0.050 -> 0.009, LUMPI Bus recall at IoU 0.5 0.20 -> 0.42. GBlobs as a member loses (LUMPI Person 0.189 -> 0.098 on A): absolute position is real signal at a fixed intersection. ROS hurts the anchor-based V2X pillars (truck 0.704 -> 0.546 on B; one truck anchor). Selection on realval-A alone keeps or still gains for every switched class. Realism unchanged (same 50 frames).

**Gate.** Upload gate ([README](README.md#32-gates)): **V2X** combined estimate (B) 0.950 -> **0.967** (bar 0.955), kit scorer valid in 58 s with 8,896 boxes; **LUMPI** 0.523 -> **0.541** (bar 0.528), late-A 0.304 -> 0.335, kit scorer valid in 146 s with 13,831 boxes. Strategy success: met. **Passed on both tracks.**

**Decision.** Upload both S5 packages unchanged (`v2x_s5_submission.zip` to 16685, `lumpi_s5_submission.zip` to 16684), then record them. Projection (previous leaderboard mAP + 0.6 x the mean of the A and B gains): V2X about 0.856 (0.852-0.868), LUMPI about 0.519 (0.514-0.541). Run c (GBlobs + ROS) not run: its precondition failed.

**Outcome** (2026-10-11). Both packages uploaded unchanged; realism identical to the previous entries.

| | V2X 978945 | LUMPI 978931 |
|---|---|---|
| Combined (mAP) | **0.8730** (0.5890); was 0.8485 | 0.5039 (0.1720); was 0.5040 |
| Per class (vs S4) | pedestrian 0.391 (+0.046), truck 0.657 (+0.029), vehicle 0.718 (+0.011); 3D@0.7 0.196 (was 0.112) | Truck 0.072 (+0.038), Bicycle 0.215 (-0.030), Car 0.642 (-0.010), Bus 0.001; Person, Van, Motorcycle identical |
| Rank | **1 of 19** | not listed; the S4 entry 975871 stays rank 1 of 18 (Raj Patil 0.4794 second) |
| Confirmation | **passed** (+0.024; above the projected 0.852-0.868) | **failed** (-0.00007): stop and diagnose |

**LUMPI diagnosis** (no test labels used). Test-size bootstrap (realval frames resampled to the test window's GT counts, paired S5 - S4): Bicycle local +0.031, 90% range -0.018 to +0.054, leaderboard -0.030 (P 0.02); Car +0.001, -0.006 to +0.016, leaderboard -0.010 (P 0.00); Truck +0.124, +0.066 to +0.149, leaderboard +0.038 (P 0.01): the shortfall is not sampling noise, the test window responds differently. Our predictions on the 50 test frames: S5 Bicycle boxes have the same size as S4's but are 18% more frequent among confident boxes (3.72 vs 3.16 per frame; realval-A +4%), while the window holds 1.6 real bicycles per frame; motorcycle confusion (23x more motorcycles in the test window) is present in both portfolios (0.56 vs 0.63 confident Bicycle boxes per realval-B motorcycle) and explains only about 0.04 of the 0.56 extra boxes per frame. The rest are false positives on test-window content the realval frames lack, as for the static walker false positives (S2) and the realism reference (R1-R2). The Car change was weak locally too (pooled A+B +0.001; B +0.014 at P 0.91). The LUMPI entry stays S4; choosing LUMPI classes from these leaderboard numbers would tune on the test set and is not done.

**Consequences.** The LUMPI diagnosis adds a class-gate condition from the next strategy on: the change must also gain on the pooled A+B frames with paired bootstrap P(gain) >= 0.9. Checked on all 17 class changes of S3-S5 against their leaderboard deltas, it agrees in sign 16 times, rejects only S5 LUMPI Car (P 0.64, leaderboard -0.010) and blocks no change that transferred (V2X S5 pedestrian: P 0.97, leaderboard +0.046); S5 LUMPI Bicycle stays the exception no local split predicts. and LUMPI Bicycle false positives on unseen content join the R3 targets (static hard negatives, motorcycles as negatives for Bicycle). Size realism is a generator-level lever: R3 should add real-sized assets (long trucks and trailers, bicycles with riders, buses) next to static clutter, and the size-gap classes are where ROS keeps helping until then. Members with anchor-based heads need class-wise anchors before they can profit from size augmentation. GBlobs stays out of single-member use but in the candidate pool for fusions. LUMPI Person (B 0.145 since S3) has not moved under S3-S5: static hard negatives (R3) and LUMPI realism remain its levers.

**Reproduce (weights and test run).** Generated on 2026-10-15 by `common/tools/reproduce_submission.py`, which also wrote each `test/reproduce_<tag>.sh`. The script runs the test-frame inference of every used member from the checkpoint listed (checkpoints are not in git; their md5s are in `validation/results/reproduce_<tag>.json`), merges with the committed `model.yaml`, compares with the scored zip, repackages the same 50 frames and runs the official kit scorer. It uses the members' current post-processing files: for the exact files of the time, check out release tag 5.0 first; the compare step reports any difference. Checked on 2026-10-15: the saved member predictions re-merge to the scored predictions exactly for every upload, and S1 LUMPI re-run from its checkpoints gives identical boxes and frames.

**Reproduce (LUMPI, `model-lumpi-track/archive/routed-g5`, tag `s5`).** Scored zip `model-lumpi-track/archive/routed-g5/submissions/2026-10-11_s5/lumpi_s5_submission.zip` (md5 `9f2c925c3976679b5b2038bfde5f7566`, CodaBench 978931); realism frames `pcdet/g1-v2` listed in `model-lumpi-track/archive/routed-g5/submissions/2026-10-11_s5/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (13831 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `g1` | `model-lumpi-track/archive/pointpillars-g1` | `model-lumpi-track/archive/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `16e68b8b9142` | 6.0: `lumpi.pointpillars-g1.epoch40.pth` | - | `model-lumpi-track/archive/pointpillars-g1/test/postprocess.yaml` |
| `g1_tta` | `model-lumpi-track/archive/pointpillars-g1` | `model-lumpi-track/archive/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `16e68b8b9142` | 6.0: `lumpi.pointpillars-g1.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/archive/pointpillars-g1/test/postprocess_tta.yaml` |
| `g1v3` | `model-lumpi-track/archive/pointpillars-g1v3` | `model-lumpi-track/archive/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `e403acdc3ae3` | 6.0: `lumpi.pointpillars-g1v3.epoch40.pth` | - | `model-lumpi-track/archive/pointpillars-g1v3/test/postprocess.yaml` |
| `g1v3_tta` | `model-lumpi-track/archive/pointpillars-g1v3` | `model-lumpi-track/archive/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `e403acdc3ae3` | 6.0: `lumpi.pointpillars-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/archive/pointpillars-g1v3/test/postprocess_tta.yaml` |
| `ppros_tta` | `model-lumpi-track/archive/pointpillars-ros-g1v3` | `model-lumpi-track/archive/pointpillars-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `590e9f16fe22` | 6.0: `lumpi.pointpillars-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/archive/pointpillars-ros-g1v3/test/postprocess_tta.yaml` |
| `pv_tta` | `model-lumpi-track/archive/pvrcnnpp-g1v3` | `model-lumpi-track/archive/pvrcnnpp-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `fd25c22b76cf` | - | flip4+yaw+z | `model-lumpi-track/archive/pvrcnnpp-g1v3/test/postprocess_tta.yaml` |
| `pvros_tta` | `model-lumpi-track/archive/pvrcnnpp-ros-g1v3` | `model-lumpi-track/archive/pvrcnnpp-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `66c1f05a2e60` | 6.0: `lumpi.pvrcnnpp-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/archive/pvrcnnpp-ros-g1v3/test/postprocess_tta.yaml` |
| `vrgb_tta` | `model-lumpi-track/archive/voxelrcnn-gblobs-g1v3` | `model-lumpi-track/archive/voxelrcnn-gblobs-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `c9dc86caa2ca` | - | flip4+yaw+z | `model-lumpi-track/archive/voxelrcnn-gblobs-g1v3/test/postprocess_tta.yaml` |
| `vrros_tta` | `model-lumpi-track/archive/voxelrcnn-ros-g1v3` | `model-lumpi-track/archive/voxelrcnn-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `5415c1ceb113` | 6.0: `lumpi.voxelrcnn-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/archive/voxelrcnn-ros-g1v3/test/postprocess_tta.yaml` |

```bash
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/archive/routed-g5/test/reproduce_s5.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/archive/routed-g5/test/reproduce_s5_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-lumpi-track/archive/routed-g5 --tag s5   # quick check: re-merge the saved member predictions
```

**Reproduce (V2X, `model-v2x-track/archive/routed-g5`, tag `s5`).** Scored zip `model-v2x-track/archive/routed-g5/submissions/2026-10-11_s5/v2x_s5_submission.zip` (md5 `e5b258652c9aa0f783f3cdfbd614d687`, CodaBench 978945); realism frames `pcdet/g1-v3` listed in `model-v2x-track/archive/routed-g5/submissions/2026-10-11_s5/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (8896 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `pv_tta` | `model-v2x-track/archive/pvrcnnpp-g1v3` | `model-v2x-track/archive/pvrcnnpp-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `d6018accd313` | - | flip4+yaw+z | `model-v2x-track/archive/pvrcnnpp-g1v3/test/postprocess_tta.yaml` |
| `pvros_tta` | `model-v2x-track/archive/pvrcnnpp-ros-g1v3` | `model-v2x-track/archive/pvrcnnpp-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `eea352738f9a` | - | flip4+yaw+z | `model-v2x-track/archive/pvrcnnpp-ros-g1v3/test/postprocess_tta.yaml` |
| `ut_tta` | `model-v2x-track/archive/pointpillars-ut` | `model-v2x-track/archive/pointpillars-ut/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `2081ca05e332` | - | flip4+yaw+z | `model-v2x-track/archive/pointpillars-ut/test/postprocess_tta.yaml` |
| `vrgb_tta` | `model-v2x-track/archive/voxelrcnn-gblobs-g1v3` | `model-v2x-track/archive/voxelrcnn-gblobs-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `f028ceffefe4` | - | flip4+yaw+z | `model-v2x-track/archive/voxelrcnn-gblobs-g1v3/test/postprocess_tta.yaml` |
| `vrros_tta` | `model-v2x-track/archive/voxelrcnn-ros-g1v3` | `model-v2x-track/archive/voxelrcnn-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `5677c039b8cc` | 6.0: `v2x.voxelrcnn-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-v2x-track/archive/voxelrcnn-ros-g1v3/test/postprocess_tta.yaml` |

```bash
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/archive/routed-g5/test/reproduce_s5.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/archive/routed-g5/test/reproduce_s5_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-v2x-track/archive/routed-g5 --tag s5   # quick check: re-merge the saved member predictions
```
