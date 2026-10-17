# 2026-10-09 S3 Fused Portfolio with TTA: decision-ready on both tracks; uploaded and confirmed (V2X 974400, LUMPI 974348)

**Version.** `model-<track>/routed-g3` (strategy S3): the `routed-g2` members, their 8-view TTA variants (`<member>_tta`, each with its own tuned `test/postprocess_tta.yaml`), per-class fusion of two members and per-class score floors (`model.yaml` `route`, `calibration`, `fusion`, `budget`). Packages `routed-g3/submissions/2026-10-09_s3/` with the upload copies `v2x_s3_submission.zip` and `lumpi_s3_submission.zip`. Strategy: [`02-STRATEGY.md` Section 8.3](../02-STRATEGY.md#83-s3-fused-portfolio-with-tta), results in 8.3.1.

**Context.** S2 left complementary members (pillars and CenterPoint disagree per class and per split) and a diagnosis that static structures dominate the walker errors. S3 tests whether test-time augmentation and score-averaging fusion turn that disagreement into AP without new training, and whether the server cost stays inside the budget.

**Evidence** (official 3D AP@0.5 R40, realval-A / realval-B; every route, fusion and floor passed the class gate against the previous step):

| Track / class | S2 (entry route) | S3 | dB vs S2 (bootstrap P, 90% interval) |
|---|---|---|---|
| V2X vehicle | 0.641 / 0.685 | **0.757 / 0.819** (`cp_tta` + `g1v2_tta`) | +0.134 (1.00) |
| V2X pedestrian | 0.290 / 0.252 | **0.350 / 0.361** (`g1v3_tta` + `cp4_tta`) | +0.109 (1.00) |
| V2X truck | 0.822 / 0.673 | **0.876 / 0.812** (`ut_tta` + `g1v2_tta`) | +0.139 (1.00) |
| V2X mAP | 0.585 / 0.537 | **0.661 / 0.664** | +0.127 (+0.114 to +0.137) |
| LUMPI Person / Car / Bicycle / Truck | 0.340 / 0.134, 0.874 / 0.770, 0.350 / 0.128, 0.200 / 0.131 | 0.396 / 0.145, 0.898 / 0.792, 0.444 / 0.173, 0.231 / 0.153 | +0.011, +0.022, +0.045, +0.023 (all 1.00) |
| LUMPI mAP (late-A) | 0.272 / 0.170 (0.271) | **0.301 / 0.184 (0.298)** | +0.014 (+0.012 to +0.016); Motorcycle and Bus -0.001 each from their score floors |

Selection on realval-A alone keeps B-mAP at 0.653 (V2X) and 0.181 (LUMPI): the gains are not a selection artifact, except the LUMPI Person fusion (its A-only pair loses on B). V2X BEV-3D gap on B 0.129 -> 0.062, 3D@0.7 0.055 -> 0.078. Realism unchanged (same 50 frames): V2X 0.919, LUMPI 0.905.

**Gate.** Upload gate ([README](README.md#32-gates)): V2X combined estimate (B) 0.828 -> **0.937** (+0.109, bar 0.833); LUMPI 0.505 (best uploaded; S2 0.508) -> **0.520** (+0.015, bar 0.510), late-A 0.255 (S1) -> 0.298, not lower. Kit scorer (`check_submission.py --official`): V2X 74 s, 10,671 boxes; LUMPI 181 s, 17,193 boxes (unbudgeted V2X: 48,110 boxes, 224 s). Strategy success (3 of 3 V2X, 4 of 7 LUMPI classes up on B): met. **Passed on both tracks.**

**Decision.** Upload both S3 packages unchanged (the entrant uploads: `v2x_s3_submission.zip` to 16685, `lumpi_s3_submission.zip` to 16684), then record them with `package_submission.py --record`. Confirmation rule: the leaderboard combined must not fall (V2X 0.7855, LUMPI 0.4728). Not used: the LUMPI Motorcycle fusion (A 0.008 -> 0.143 but B +0.008, P 0.92: class gate failed).

**Outcome** (2026-10-10). Both uploads were the packaged upload copies, unchanged (server realism identical to the previous entries: same 50 frames).

| | V2X 974400 | LUMPI 974348 |
|---|---|---|
| Status | Finished, on the leaderboard: **rank 1 of 19** (runner-up 0.6616) | scorer log reached DONE, but CodaBench kept the submission in Running after scoring; not on the leaderboard yet (965614 still shows, rank 2 behind 0.4784) |
| Combined (mAP, R) | **0.8381** (0.5483, 0.9203); was 0.7855 | **0.5015** (0.1692, 0.8912) by the log; was 0.4728 |
| Per class | vehicle 0.681, pedestrian 0.346, truck 0.619 (+0.076, +0.064, +0.044) | Person 0.157, Car 0.652, Bicycle **0.224**, Truck 0.033, Van 0.117 (+0.040, +0.019, +0.171, +0.005, -0.001) |
| 3D@0.7, BEV@0.5 | 0.0755, 0.6179 (BEV-3D gap 0.083 -> 0.070) | 0.0609, 0.1781 |
| Confirmation | **passed** (+0.053) | **passed by the log** (+0.029, above the 0.4784 leader) |
| Leaderboard / estimate (B) | 0.838 vs 0.937 | 0.501 vs 0.520 |

Transfer: the leaderboard mAP gain was 0.48 x the realval-B gain on V2X (truck 0.32) but 1.89 x on LUMPI (Bicycle 2.4, Person 3.6), while it was 0.80 x (V2X) and 0.81 x (LUMPI) the realval-A gain. Leaderboard levels still track B (leaderboard / B: V2X 0.83, LUMPI 0.92).

**Consequences.** Leaderboard projection for later uploads: previous leaderboard mAP + 0.8 x the realval-A mAP gain (fitted on these two uploads; checked again on the next one); the gates stay on realval-B. S4 starts from `routed-g3`; its V2X height target is already met, so it is judged on 3D@0.7 and LUMPI Truck and Car. Every new member joins as plain and TTA variants, and `fuse` and `budget` are re-run. Static false positives ranked above the median true-positive score fall 6.2 -> 1.8 per frame (V2X pedestrian) and 9.7 -> 4.1 (LUMPI Person), but most remaining unmatched walker boxes are still static: R3 stays the next walker lever. Process: raw files for tuning come only from `pcdet_predict.py --raw` (a reused pilot output was post-processed twice and was caught by the tuner-versus-evaluation mismatch).

**Reproduce (weights and test run).** Generated on 2026-10-15 by `common/tools/reproduce_submission.py`, which also wrote each `test/reproduce_<tag>.sh`. The script runs the test-frame inference of every used member from the checkpoint listed (checkpoints are not in git; their md5s are in `validation/results/reproduce_<tag>.json`), merges with the committed `model.yaml`, compares with the scored zip, repackages the same 50 frames and runs the official kit scorer. It uses the members' current post-processing files: for the exact files of the time, check out release tag 3.0 first; the compare step reports any difference. Checked on 2026-10-15: the saved member predictions re-merge to the scored predictions exactly for every upload, and S1 LUMPI re-run from its checkpoints gives identical boxes and frames.

**Reproduce (LUMPI, `model-lumpi-track/routed-g3`, tag `s3`).** Scored zip `model-lumpi-track/routed-g3/submissions/2026-10-09_s3/lumpi_s3_submission.zip` (md5 `9133dd7d9d8b377ec9228b79b75065a0`, CodaBench 974348); realism frames `pcdet/g1-v2` listed in `model-lumpi-track/routed-g3/submissions/2026-10-09_s3/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (17193 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `cp4_tta` | `model-lumpi-track/centerpoint-s4-g1v3` | `model-lumpi-track/centerpoint-s4-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `740f83d5cea0` | - | flip4+yaw+z | `model-lumpi-track/centerpoint-s4-g1v3/test/postprocess_tta.yaml` |
| `cp_tta` | `model-lumpi-track/centerpoint-g1v3` | `model-lumpi-track/centerpoint-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `25e4c0acf63d` | 6.0: `lumpi.centerpoint-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/centerpoint-g1v3/test/postprocess_tta.yaml` |
| `g1` | `model-lumpi-track/pointpillars-g1` | `model-lumpi-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `16e68b8b9142` | 6.0: `lumpi.pointpillars-g1.epoch40.pth` | - | `model-lumpi-track/pointpillars-g1/test/postprocess.yaml` |
| `g1_tta` | `model-lumpi-track/pointpillars-g1` | `model-lumpi-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `16e68b8b9142` | 6.0: `lumpi.pointpillars-g1.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pointpillars-g1/test/postprocess_tta.yaml` |
| `g1v3` | `model-lumpi-track/pointpillars-g1v3` | `model-lumpi-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `e403acdc3ae3` | 6.0: `lumpi.pointpillars-g1v3.epoch40.pth` | - | `model-lumpi-track/pointpillars-g1v3/test/postprocess.yaml` |
| `g1v3_tta` | `model-lumpi-track/pointpillars-g1v3` | `model-lumpi-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `e403acdc3ae3` | 6.0: `lumpi.pointpillars-g1v3.epoch40.pth` | flip4+yaw+z | `model-lumpi-track/pointpillars-g1v3/test/postprocess_tta.yaml` |

```bash
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g3/test/reproduce_s3.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g3/test/reproduce_s3_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-lumpi-track/routed-g3 --tag s3   # quick check: re-merge the saved member predictions
```

**Reproduce (V2X, `model-v2x-track/routed-g3`, tag `s3`).** Scored zip `model-v2x-track/routed-g3/submissions/2026-10-09_s3/v2x_s3_submission.zip` (md5 `5e46f9450feb7846455c4b8428483641`, CodaBench 974400); realism frames `pcdet/g1-v3` listed in `model-v2x-track/routed-g3/submissions/2026-10-09_s3/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (10671 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `cp4_tta` | `model-v2x-track/centerpoint-s4-g1v3` | `model-v2x-track/centerpoint-s4-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `0440576e97ae` | - | flip4+yaw+z | `model-v2x-track/centerpoint-s4-g1v3/test/postprocess_tta.yaml` |
| `cp_tta` | `model-v2x-track/centerpoint-g1v3` | `model-v2x-track/centerpoint-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `2ffc3ad60f99` | - | flip4+yaw+z | `model-v2x-track/centerpoint-g1v3/test/postprocess_tta.yaml` |
| `g1v2_tta` | `model-v2x-track/pointpillars-g1v2` | `model-v2x-track/pointpillars-g1v2/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `7c3e9a1c074a` | - | flip4+yaw+z | `model-v2x-track/pointpillars-g1v2/test/postprocess_tta.yaml` |
| `g1v3_tta` | `model-v2x-track/pointpillars-g1v3` | `model-v2x-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `b330667c2981` | - | flip4+yaw+z | `model-v2x-track/pointpillars-g1v3/test/postprocess_tta.yaml` |
| `ut_tta` | `model-v2x-track/pointpillars-ut` | `model-v2x-track/pointpillars-ut/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `2081ca05e332` | - | flip4+yaw+z | `model-v2x-track/pointpillars-ut/test/postprocess_tta.yaml` |

```bash
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g3/test/reproduce_s3.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g3/test/reproduce_s3_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-v2x-track/routed-g3 --tag s3   # quick check: re-merge the saved member predictions
```
