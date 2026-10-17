# 2026-10-16 S6 Variance-Controlled Final Portfolio: uploaded and confirmed on both tracks (LUMPI 995869 0.5228, V2X variant b 995877 0.8931), rank 1 on both

**Version.** Strategy S6: the confirmed R5 portfolios (`routed-g7`) plus eight new seed runs (LUMPI `voxelrcnn-ros-g1v4-s3/-s4`, `pvrcnnpp-ros-g1v4-s3/-s4`; V2X `voxelrcnn-ros-g1v5-s2/-s3`, `pvrcnnpp-ros-g1v5-s2/-s3`) and six seed bags (`bag-*`: weighted box fusion of the seeds' tuned predictions, scores averaged over all seeds), plain and TTA. Leaderboard versions: **LUMPI `model-lumpi-track/routed-g8`**, package `submissions/2026-10-16_s6/lumpi_s6_submission.zip` (md5 `02c731ecbd162a84d6eae5537856bc4a`); **V2X `model-v2x-track/routed-g8b`** (variant b), package `submissions/2026-10-16_s6b/v2x_s6b_submission.zip` (md5 `00a80bb32c5019b6d9913555efebc6b6`). The gated V2X `routed-g8` equals the R5 entry (same predictions and frames as 990255) and was not uploaded. Plan, refinements and pre-registered rules: [`02-STRATEGY.md` Section 8.6](../02-STRATEGY.md#86-s6-variance-controlled-final-portfolio-re-planned-2026-10-15); results 8.6.1; close-out and plan 8.6.2. Runs: `$BDC_DATA/logs/s6` and `$BDC_DATA/logs/s6close` (`common/pipeline/`, detached; `STATUS.md`, `events.txt`). Weights: assets of release 6.0 (`releases/6.0/weights.json`).

**Context.** The R5 retrospective (8.10) ranked member noise as the largest remaining lever (seed spread up to 0.17 AP per class on realval-B) and found that realval-B cannot judge LUMPI Van (its class 6 labels are person- or two-wheeler-sized), which had kept Van at the S1 member since S1.

**Evidence** (official 3D AP@0.5 R40, TTA, realval-A / realval-B):

| Item | Result |
|---|---|
| Seed bags against their best seed | V2X PV-RCNN++ **0.702 / 0.694** (0.689 / 0.680); V2X Voxel R-CNN **0.708 / 0.697** (0.690 / 0.691; truck seed spread 0.135 on B); LUMPI PV-RCNN++ **0.356 / 0.200** (0.343 / 0.196; late-A Person 0.334 against 0.316-0.328); LUMPI Voxel R-CNN **0.348 / 0.192** (0.336 / 0.189): every bag at or above its best seed on both split means |
| V2X select / fuse | select routed every class to a bag (A 0.707, B 0.703 before fusion); fuse kept the three R5 fusions: vehicle dB +0.005 (P 0.94; A +0.008, pooled +0.007), pedestrian -0.006, truck -0.001 (A +0.030, pooled +0.022); final gate: identical predictions, all reverted |
| LUMPI Van (judge: early-A ranks, late-A gate) | `vrros` + `vrros4_tta` + `g1_tta` (IoU 0.5, floor 0.05): A 0.120 -> **0.173**, late-A 0.118 -> **0.173** (+0.055, P 1.00 on the final predictions) |
| LUMPI other classes | Person: late-A candidates (bags) failed B (-0.009 to -0.015); Car +0.007 (P 1.00) under the bar; Truck -0.004; Motorcycle passed (+0.023) but frozen at R5 (rule 4), as Bicycle and Bus |
| V2X variant b (`routed-g8b`, built at the entrant's request) | per class the fuse step's best joint-ranked candidate wherever the pooled A+B condition holds (P >= 0.9), without the +0.01-on-B requirement: vehicle `bagvr5_tta` + `pvros4s2_tta` (IoU 0.7), truck `pp5_tta` + `bagvr5_tta` + `bagpv5` (IoU 0.5), pedestrian R5; on the final predictions vehicle pooled +0.0073, truck +0.0238 (both P 1.00) |
| Realism (item 9) | frames from the whole `g1-v4` corpus: 0.9344 (FPD) and 0.9313 (FPD + EMD) against 0.9337 for the R5 frames as packaged (bar 0.9367): **R5 frames kept**; over 10 subsample seeds the three sets are within 0.001 (sd 0.0012-0.0025), and the frame order alone moves one set by up to 0.006 |

**Gate.** Upload gate (unclipped estimate at least 0.005 above the R5 upload, LUMPI with Van read from realval-A (rule 3); LUMPI late-A not lower; kit scorer under 400 s):

| Track | A-mAP | B-mAP | late-A | R (as packaged) | Estimate | Bar | Kit scorer | Gate |
|---|---|---|---|---|---|---|---|---|
| LUMPI | 0.377 -> 0.384 | 0.2234 -> 0.2235 (judged 0.2404 -> **0.2480**) | 0.351 -> **0.358** | 0.934 (R5 frames) | judged 0.5796 -> **0.5860** (B 0.5649 -> 0.5650) | 0.5846 | 160 s, 15,082 boxes | **passed** (+0.0065) |
| V2X (gated S6, `routed-g8`) | 0.714 | 0.710 | | 0.937 | 0.983 | 0.988 | 146 s, 24,759 boxes | not met (equal to R5) |
| V2X variant b (`routed-g8b`) | 0.714 -> **0.727** | 0.7101 -> 0.7118 (P 0.82) | | 0.937 | 0.9847 | 0.988 | 137 s, 24,284 boxes | not met (+0.0014); uploaded as a comparison of complete systems |

**Decision.** LUMPI: upload `lumpi_s6_submission.zip` unchanged (16684); it differs from the R5 entry only in Van (1,472 boxes against 1,399; every other class box-for-box identical, same 50 frames), so the upload tests one change; projection 0.523-0.526. V2X: the gated package is the R5 entry; at the entrant's request the complete variant b system was packaged and uploaded for a leaderboard comparison of complete systems (allowed: rules review, "choose between complete systems"; its per-class numbers are not used to assemble a portfolio); projection 0.885-0.889.

**Outcome** (2026-10-17 UTC; both uploaded unchanged; public leaderboard API):

| | LUMPI 995869 (S6) | V2X 995877 (S6 variant b) |
|---|---|---|
| Combined (mAP, R) | **0.5228** (0.1748, 0.9323); was 0.5198 (0.1714, 0.9323) | **0.8931** (0.6065, 0.9332); was 0.8852 (0.5972, 0.9332) |
| Per class (against R5) | **Van 0.117 -> 0.141 (+0.024)**; every other class identical | **vehicle 0.721 -> 0.735 (+0.014), truck 0.657 -> 0.671 (+0.014)**; pedestrian identical |
| Other columns | 3D mAP@0.7 0.065 -> 0.083; BEV mAP 0.183 -> 0.186 | 3D mAP@0.7 0.187 -> 0.165; BEV mAP 0.648 -> 0.658 |
| Rank | **1 of 21** (Raj Patil 0.4914) | **1 of 23** (Raj Patil 0.7555) |
| Confirmation | **passed** (+0.0029; projected +0.003 to +0.006: at the low end) | **passed** (+0.0079; projected +0.000 to +0.004: above the range) |

**Transfer.** LUMPI Van: +0.024 on the leaderboard against +0.053 on realval-A and +0.055 on late-A (0.45 x), +0.0006 on B; the level ratio leaderboard / realval-A fell from 0.97 (R5) to 0.81, so the A gain is an upper bound for a judged class. V2X vehicle: +0.014 against A +0.008 and B +0.005 (1.7 x A, 2.7 x B); truck: +0.014 against A +0.030 and B -0.000 (0.45 x A). The B-based upload estimate predicted +0.0014 for V2X; the leaderboard gave +0.0079 (5.6 x); the projection rule (0.6 x the mean of the A and B gains) gave +0.0037 (2.1 x). The pooled condition on the final predictions had the sign right for both V2X classes, and Van's judge (late-A) for Van. V2X 3D mAP@0.7 fell (0.187 -> 0.165) although it rose on B (0.170 -> 0.221): box tightness at IoU 0.7 in the test window is not represented by realval-B (not scored).

**Close-out (2026-10-17).** The pooled rule (Consequence 1) applied to LUMPI as to V2X: only Car qualified in `fuse` (`pvros_tta` + `vrros_tta` + `pvros4s2_tta`, IoU 0.7; pooled +0.0055, P 1.00), so `model-lumpi-track/routed-g8b` is the S6 entry plus that fusion, every other class pinned (`common/pipeline/s6b_lumpi.sh`). On the final predictions Car gains on A (+0.0074) and on B (+0.0074) separately but loses on the pooled frames (-0.0022, P 0.24): the fused scores rank differently on the two splits, the pattern that reverted LUMPI Car in S5 and R5. **Not adopted**; nothing packaged; the S6 entries stay. The same check passes for V2X variant b (vehicle +0.0073, truck +0.0238, both P 1.00). Reproduction from the weights (on idle GPUs, `$BDC_DATA/logs/s6close`): the test-frame scripts of both entries give **IDENTICAL** predictions (maximum difference 0.0) and identical frames, both from the corpus and, as in a fresh clone, from the scored zip; the kit check is valid (LUMPI 189 s, V2X 159 s). The validation scripts recompute realval-A and realval-B (and late-A) from the weights: split mAP identical to four decimals on both tracks (LUMPI A 0.3842, B 0.2235, late-A 0.3584 against 0.3583; V2X A 0.7272, B 0.7118), every class within 4e-4 AP: **EQUIVALENT**. 41 of the 48 member prediction files are bit-identical to the recorded ones; the other 7, all TTA predictions of two-stage members (6 of them on realval-A) recorded on GPUs that training jobs were using at the time, differ in the last digits (99% of the boxes within 7 cm and 0.0015 in score). The 21 checkpoints and both zips are attached to release 6.0 (`releases/6.0/weights.json`: asset names, paths, md5, the versions using them; `common/tools/release_weights.py fetch`).

**Consequences.**
1. **The +0.01-on-B requirement was too strict for complete systems.** It rejected V2X vehicle and truck, which gained +0.014 each on the leaderboard; the pooled A+B condition on the final predictions had both signs right, and it rejects the false LUMPI Car gains of S5, R5 and the close-out. From 6.0 on, the pooled rule replaces it ([decisions README Section 3.2](README.md#32-gates), pre-registered 2026-10-17).
2. **Bags transfer through fusions.** Every bag beat its best seed locally; on the leaderboard the gain came from fusing bags with other architectures (vehicle: Voxel R-CNN bag + a PV-RCNN++ seed; truck: pillars + both bags).
3. **A judge on the right split unlocks a class, at about half its local gain.** Van moved for the first time since S1; a class whose labels differ between the splits needs its own judging split, pre-registered before the run, and its A gain is an upper bound.
4. **Realism frame changes are inside the scorer's noise:** +0.003 is about 1.5-2 sd of one subsample draw; candidates are scored in the packaged order (the server's draw).
5. **Reproduction is exact on an idle GPU** (both entries, all members), and possible from a fresh clone: weights from the release, frames from the committed zip.

**Reproduce (weights and test run).** Generated on 2026-10-17 by `common/tools/reproduce_submission.py` and `common/tools/reproduce_validation.py`. Every checkpoint below is an asset of release 6.0; `release_weights.py fetch` downloads it to the path shown and checks its md5. The test-frame script re-runs the inference of every used member (for a bag, every seed), merges with the committed `model.yaml`, compares with the scored zip, repackages the same 50 frames into `test/output/repro-<tag>/` (from the corpus if present, else from the scored zip), runs the official kit scorer and compares predictions and frames again; the validation script recomputes realval-A, realval-B and late-A per class and compares with `validation/results/scorecard.json`. Run both on an idle GPU.

**Reproduce (LUMPI, `model-lumpi-track/routed-g8`, tag `s6`).** Scored zip `model-lumpi-track/routed-g8/submissions/2026-10-16_s6/lumpi_s6_submission.zip` (md5 `02c731ecbd162a84d6eae5537856bc4a`, CodaBench 995869); realism frames `pcdet/g1-v4` listed in `model-lumpi-track/routed-g8/submissions/2026-10-16_s6/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (15082 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `cp_tta` | `model-lumpi-track/centerpoint-g1v3` | `model-lumpi-track/centerpoint-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `25e4c0acf63d` | 6.0: `lumpi.centerpoint-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/centerpoint-g1v3/test/postprocess_tta.yaml` |
| `g1` | `model-lumpi-track/pointpillars-g1` | `model-lumpi-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `16e68b8b9142` | 6.0: `lumpi.pointpillars-g1.epoch40.pth` | - | `model-lumpi-track/pointpillars-g1/test/postprocess.yaml` |
| `g1_tta` | `model-lumpi-track/pointpillars-g1` | `model-lumpi-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `16e68b8b9142` | 6.0: `lumpi.pointpillars-g1.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pointpillars-g1/test/postprocess_tta.yaml` |
| `g1v3` | `model-lumpi-track/pointpillars-g1v3` | `model-lumpi-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `e403acdc3ae3` | 6.0: `lumpi.pointpillars-g1v3.epoch40.pth` | - | `model-lumpi-track/pointpillars-g1v3/test/postprocess.yaml` |
| `g1v3_tta` | `model-lumpi-track/pointpillars-g1v3` | `model-lumpi-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `e403acdc3ae3` | 6.0: `lumpi.pointpillars-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pointpillars-g1v3/test/postprocess_tta.yaml` |
| `pp4_tta` | `model-lumpi-track/pointpillars-g1v4` | `model-lumpi-track/pointpillars-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `46e9f504fd05` | 6.0: `lumpi.pointpillars-g1v4.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pointpillars-g1v4/test/postprocess_tta.yaml` |
| `ppros4_tta` | `model-lumpi-track/pointpillars-ros-g1v4` | `model-lumpi-track/pointpillars-ros-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `97be701cb39c` | 6.0: `lumpi.pointpillars-ros-g1v4.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pointpillars-ros-g1v4/test/postprocess_tta.yaml` |
| `ppros_tta` | `model-lumpi-track/pointpillars-ros-g1v3` | `model-lumpi-track/pointpillars-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `590e9f16fe22` | 6.0: `lumpi.pointpillars-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pointpillars-ros-g1v3/test/postprocess_tta.yaml` |
| `pvros4_tta` | `model-lumpi-track/pvrcnnpp-ros-g1v4` | `model-lumpi-track/pvrcnnpp-ros-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `3fffacf2d0ba` | 6.0: `lumpi.pvrcnnpp-ros-g1v4.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pvrcnnpp-ros-g1v4/test/postprocess_tta.yaml` |
| `pvros_tta` | `model-lumpi-track/pvrcnnpp-ros-g1v3` | `model-lumpi-track/pvrcnnpp-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `66c1f05a2e60` | 6.0: `lumpi.pvrcnnpp-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pvrcnnpp-ros-g1v3/test/postprocess_tta.yaml` |
| `vrros` | `model-lumpi-track/voxelrcnn-ros-g1v3` | `model-lumpi-track/voxelrcnn-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `5415c1ceb113` | 6.0: `lumpi.voxelrcnn-ros-g1v3.epoch40.pth` | - | `model-lumpi-track/voxelrcnn-ros-g1v3/test/postprocess.yaml` |
| `vrros4_tta` | `model-lumpi-track/voxelrcnn-ros-g1v4` | `model-lumpi-track/voxelrcnn-ros-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `5c061261f002` | 6.0: `lumpi.voxelrcnn-ros-g1v4.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/voxelrcnn-ros-g1v4/test/postprocess_tta.yaml` |
| `vrros4s2_tta` | `model-lumpi-track/voxelrcnn-ros-g1v4-s2` | `model-lumpi-track/voxelrcnn-ros-g1v4-s2/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `4d877e50e453` | 6.0: `lumpi.voxelrcnn-ros-g1v4-s2.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/voxelrcnn-ros-g1v4-s2/test/postprocess_tta.yaml` |
| `vrros_tta` | `model-lumpi-track/voxelrcnn-ros-g1v3` | `model-lumpi-track/voxelrcnn-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `5415c1ceb113` | 6.0: `lumpi.voxelrcnn-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/voxelrcnn-ros-g1v3/test/postprocess_tta.yaml` |

```bash
python common/tools/release_weights.py fetch --tag 6.0 --version lumpi:s6   # the weights above, md5-verified
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g8/test/reproduce_s6.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g8/test/reproduce_s6_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-lumpi-track/routed-g8 --tag s6   # quick check: re-merge the saved member predictions
```

**Reproduce (V2X, `model-v2x-track/routed-g8b`, tag `s6b`).** Scored zip `model-v2x-track/routed-g8b/submissions/2026-10-16_s6b/v2x_s6b_submission.zip` (md5 `00a80bb32c5019b6d9913555efebc6b6`, CodaBench 995877); realism frames `pcdet/g1-v5` listed in `model-v2x-track/routed-g8b/submissions/2026-10-16_s6b/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (24284 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `bagpv5` (bag) | `model-v2x-track/pvrcnnpp-ros-g1v5` | `model-v2x-track/pvrcnnpp-ros-g1v5/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `4bceaa59aeb5` | 6.0: `v2x.pvrcnnpp-ros-g1v5.epoch40.pth` | - | `model-v2x-track/pvrcnnpp-ros-g1v5/test/postprocess.yaml` |
| `bagpv5` (bag) | `model-v2x-track/pvrcnnpp-ros-g1v5-s2` | `model-v2x-track/pvrcnnpp-ros-g1v5-s2/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `f36f0300036e` | 6.0: `v2x.pvrcnnpp-ros-g1v5-s2.epoch40.pth` | - | `model-v2x-track/pvrcnnpp-ros-g1v5-s2/test/postprocess.yaml` |
| `bagpv5` (bag) | `model-v2x-track/pvrcnnpp-ros-g1v5-s3` | `model-v2x-track/pvrcnnpp-ros-g1v5-s3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `106fcb7d15e7` | 6.0: `v2x.pvrcnnpp-ros-g1v5-s3.epoch40.pth` | - | `model-v2x-track/pvrcnnpp-ros-g1v5-s3/test/postprocess.yaml` |
| `bagvr5_tta` (bag) | `model-v2x-track/voxelrcnn-ros-g1v5` | `model-v2x-track/voxelrcnn-ros-g1v5/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `a90a13b7e297` | 6.0: `v2x.voxelrcnn-ros-g1v5.epoch40.pth` | flip4+yaw+z | `model-v2x-track/voxelrcnn-ros-g1v5/test/postprocess_tta.yaml` |
| `bagvr5_tta` (bag) | `model-v2x-track/voxelrcnn-ros-g1v5-s2` | `model-v2x-track/voxelrcnn-ros-g1v5-s2/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `be6acbf7d91f` | 6.0: `v2x.voxelrcnn-ros-g1v5-s2.epoch40.pth` | flip4+yaw+z | `model-v2x-track/voxelrcnn-ros-g1v5-s2/test/postprocess_tta.yaml` |
| `bagvr5_tta` (bag) | `model-v2x-track/voxelrcnn-ros-g1v5-s3` | `model-v2x-track/voxelrcnn-ros-g1v5-s3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `3a4f716b778d` | 6.0: `v2x.voxelrcnn-ros-g1v5-s3.epoch40.pth` | flip4+yaw+z | `model-v2x-track/voxelrcnn-ros-g1v5-s3/test/postprocess_tta.yaml` |
| `pp5_tta` | `model-v2x-track/pointpillars-g1v5` | `model-v2x-track/pointpillars-g1v5/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `62070b22bce0` | 6.0: `v2x.pointpillars-g1v5.epoch40.pth` | flip4+yaw+z | `model-v2x-track/pointpillars-g1v5/test/postprocess_tta.yaml` |
| `pvros4s2_tta` | `model-v2x-track/pvrcnnpp-ros-g1v4-s2` | `model-v2x-track/pvrcnnpp-ros-g1v4-s2/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `30b8d6036c6f` | 6.0: `v2x.pvrcnnpp-ros-g1v4-s2.epoch40.pth` | flip4+yaw+z | `model-v2x-track/pvrcnnpp-ros-g1v4-s2/test/postprocess_tta.yaml` |
| `vrros4_tta` | `model-v2x-track/voxelrcnn-ros-g1v4` | `model-v2x-track/voxelrcnn-ros-g1v4/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `b85264eaec17` | 6.0: `v2x.voxelrcnn-ros-g1v4.epoch40.pth` | flip4+yaw+z | `model-v2x-track/voxelrcnn-ros-g1v4/test/postprocess_tta.yaml` |
| `vrros_tta` | `model-v2x-track/voxelrcnn-ros-g1v3` | `model-v2x-track/voxelrcnn-ros-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `5677c039b8cc` | 6.0: `v2x.voxelrcnn-ros-g1v3.epoch40.pth` | flip4+yaw+z | `model-v2x-track/voxelrcnn-ros-g1v3/test/postprocess_tta.yaml` |

```bash
python common/tools/release_weights.py fetch --tag 6.0 --version v2x:s6b   # the weights above, md5-verified
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g8b/test/reproduce_s6b.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g8b/test/reproduce_s6b_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-v2x-track/routed-g8b --tag s6b   # quick check: re-merge the saved member predictions
```

The gated V2X package (`model-v2x-track/routed-g8`, tag `s6`, `test/reproduce_s6.sh`) has the R5 entry's predictions and frames; its members are those of the R5 record.
