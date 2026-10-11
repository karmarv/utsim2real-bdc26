# Releases

Each release tag fixes the code, the documentation and the submission files of the leaderboard entries at that point. The zip of every leaderboard entry is committed next to its manifest, byte for byte the file that was scored (md5 below and in the folder's `manifest.json`): in 1.0 as `submission_<track>.zip`; from S2 on under its upload name `<track>_<strategy>_submission.zip`, written by the packager (the upload copies of leaderboard entries are committed; the ignore rule for upload copies was lifted on 2026-10-10). The full submission register, with the gate result of every version, is [`docs/decisions/README.md` Section 2](docs/decisions/README.md#2-submission-register).

## 5.0 (pre-release, 2026-10-11)

**Leaderboard** (development phase; public leaderboards checked 2026-10-11): V2X has a new entry; the LUMPI entry stays the 4.0 one (975871).

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 2 V2X-Real (16685) | S5 | 978945 | 2026-10-11 20:20 | **0.8730** | 0.5890 | 0.9203 | **1 of 19** | [`v2x_s5_submission.zip`](model-v2x-track/routed-g5/submissions/2026-10-11_s5/v2x_s5_submission.zip) (`e5b258652c9aa0f783f3cdfbd614d687`) | [s5 object scaling](docs/decisions/2026-10-11-s5-object-scaling.md) |
| 1 LUMPI (16684) | S5 | 978931 | 2026-10-11 20:12 | 0.5039 | 0.1720 | 0.8912 | not listed (0.00007 below the S4 entry, which stays rank 1 of 18) | [`lumpi_s5_submission.zip`](model-lumpi-track/routed-g5/submissions/2026-10-11_s5/lumpi_s5_submission.zip) (`9f2c925c3976679b5b2038bfde5f7566`) | same |

Server records: [`codabench_978945.json`](model-v2x-track/routed-g5/submissions/2026-10-11_s5/codabench_978945.json), [`codabench_978931.json`](model-lumpi-track/routed-g5/submissions/2026-10-11_s5/codabench_978931.json). V2X against S4: pedestrian +0.046, truck +0.029, vehicle +0.011. LUMPI against S4: Truck +0.038, Bicycle -0.030, Car -0.010 (confirmation failed; diagnosed in [`docs/02-STRATEGY.md` 8.5.1](docs/02-STRATEGY.md#851-results-2026-10-11)).

**What 5.0 contains**
- Strategy S5, *Geometry-Invariant Inputs* ([`docs/02-STRATEGY.md` Sections 8.5 and 8.5.1](docs/02-STRATEGY.md#851-results-2026-10-11); [decision record](docs/decisions/2026-10-11-s5-object-scaling.md)): the review (voxel occupancy: GBlobs as published degenerates at our density; real vs synthetic label sizes: bicycles and trucks are the gap); `common/bdc26/detect/gblobs_vfe.py` (`GBlobsVFE` ported with its BSD-3 notice, `GBlobsCellVFE`) and `common/bdc26/detect/augment.py` (class-wise object scaling `bdc_object_scaling`); runs `voxelrcnn-gblobs-g1v3`, `voxelrcnn-ros-g1v3`, `pvrcnnpp-ros-g1v3`, `pointpillars-ros-g1v3` on both tracks (plain and TTA); models `routed-g5`.
- Findings: object scaling lifts every anchor-free and two-stage member and hurts the anchor-based V2X pillars; GBlobs loses as a member and helps inside fusions; the LUMPI test window answers the size-augmented Bicycle members with false positives no local split shows; from R3 on the class gate also requires a pooled A+B gain (agrees with the leaderboard on 16 of the 17 class changes of S3-S5).
- Tests: 56 (`python -m pytest -q common/tests`).

## 4.0 (pre-release, 2026-10-11)

**Leaderboard entries** (development phase; public leaderboards checked 2026-10-11): **rank 1 on both tracks.**

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 2 V2X-Real (16685) | S4 | 975938 | 2026-10-11 00:16 | **0.8485** | 0.5605 | 0.9203 | **1 of 19** | [`v2x_s4_submission.zip`](model-v2x-track/routed-g4/submissions/2026-10-10_s4/v2x_s4_submission.zip) (`29c8f7a9887d1443cd7f23289ecfc8b1`) | [s4 two-stage](docs/decisions/2026-10-10-s4-two-stage.md) |
| 1 LUMPI (16684) | S4 | 975871 | 2026-10-10 23:50 | **0.5040** | 0.1721 | 0.8912 | **1 of 18** | [`lumpi_s4_submission.zip`](model-lumpi-track/routed-g4/submissions/2026-10-10_s4/lumpi_s4_submission.zip) (`ce3dc93c3f7defd7e0ca74bd0efc702a`) | same |

Per-class AP, realism terms and the scoring logs: [`codabench_975938.json`](model-v2x-track/routed-g4/submissions/2026-10-10_s4/codabench_975938.json), [`codabench_975871.json`](model-lumpi-track/routed-g4/submissions/2026-10-10_s4/codabench_975871.json). Against the S3 entries: V2X 0.8381 -> 0.8485 (vehicle +0.027, truck +0.010, pedestrian identical); LUMPI 0.5015 (S3 log; 974348 was never listed) -> 0.5040 (Bicycle 0.224 -> 0.244, every other class identical). The LUMPI package was below its upload gate (estimate +0.003) and uploaded by the entrant's call. Field on 2026-10-11: LUMPI second 0.4784, V2X runner-up 0.6616.

**What 4.0 contains**
- Strategy S4, *Two-Stage Refinement* ([`docs/02-STRATEGY.md` Sections 8.4 and 8.4.1](docs/02-STRATEGY.md#841-results-2026-10-10); [decision record](docs/decisions/2026-10-10-s4-two-stage.md)): the review of the S3 losses (AP-loss decomposition and near-miss analysis, `bdc26.diagnostics.ap_loss_decomposition`, now in every scorecard) and the revised plan; members `voxelrcnn-g1v3` and `pvrcnnpp-g1v3` on both tracks (stage 1 = the S2 CenterPoint; plain and TTA variants); a per-class two-stage score blend (`common/bdc26/detect/pcdet_patches.py`, `pcdet_predict.py --score-blend`); `route_predictions.py fuse --max-members 3` with incumbent-aware selection; models `routed-g4`.
- Findings: refinement halves the vehicle localization loss (3D@0.7 on the V2X leaderboard 0.0755 -> 0.1118) but leaves walker localization unchanged; the leaderboard gain had the right sign at all five uploads with a local change but was 0.25-1.9 x any local gain, so projections use 0.6 x the mean of the realval-A and B gains.
- Tests: 54 (`python -m pytest -q common/tests`).

## 3.0 (pre-release, 2026-10-10)

**Leaderboard entries** (development phase; public leaderboards checked 2026-10-10):

| Track | Version | CodaBench id | Scored | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 2 V2X-Real (16685) | S3 | 974400 | 2026-10-10 11:18 UTC (06:18 CDT) | **0.8381** | 0.5483 | 0.9203 | **1 of 19** | [`v2x_s3_submission.zip`](model-v2x-track/routed-g3/submissions/2026-10-09_s3/v2x_s3_submission.zip) (`5e46f9450feb7846455c4b8428483641`) | [s3 fused portfolio](docs/decisions/2026-10-09-s3-fused-portfolio.md) |
| 1 LUMPI (16684) | S3 | 974348 | 2026-10-10 05:48 CDT; scorer log DONE, CodaBench status Running afterwards | **0.5015** (log) | 0.1692 | 0.8912 | not listed yet (would lead: 0.4784); listed LUMPI entry 965614 (S1, rank 2) | [`lumpi_s3_submission.zip`](model-lumpi-track/routed-g3/submissions/2026-10-09_s3/lumpi_s3_submission.zip) (`9133dd7d9d8b377ec9228b79b75065a0`) | same |

Per-class AP, realism terms and the scoring logs: [`codabench_974400.json`](model-v2x-track/routed-g3/submissions/2026-10-09_s3/codabench_974400.json), [`codabench_974348.json`](model-lumpi-track/routed-g3/submissions/2026-10-09_s3/codabench_974348.json). Against the previous entries: V2X 0.7855 -> 0.8381 (vehicle +0.076, pedestrian +0.064, truck +0.044); LUMPI 0.4728 -> 0.5015 (Person +0.040, Car +0.019, Bicycle 0.053 -> 0.224). Realism is identical (same 50 frames): every change is detection. Field on 2026-10-10: LUMPI leader 0.4784, V2X runner-up 0.6616.

**What 3.0 contains**
- Strategy S3, *Fused Portfolio with TTA* ([`docs/02-STRATEGY.md` Section 8.3.1](docs/02-STRATEGY.md#831-results-2026-10-09); [decision record](docs/decisions/2026-10-09-s3-fused-portfolio.md)), built on the S2 members without new training: 8-view test-time augmentation (`common/bdc26/detect/tta.py`: flips, yaw +/-5 deg, z +/-0.25 m) and rotated weighted box fusion (`common/bdc26/detect/fusion.py`); `pcdet_predict.py --tta`; `tune_and_eval.sh --tta` in every member folder (each TTA variant tunes its own `test/postprocess_tta.yaml`); `route_predictions.py` with TTA members, `fuse` (per-class pairs of two checkpoints, class gate, A-only selection-bias check) and `budget` (per-class score floors costing at most 0.002 AP, exact from truncated match flags); models `routed-g3` on both tracks.
- Real validation: V2X realval-A / B 0.585 / 0.537 -> 0.661 / 0.664 (BEV-3D gap on B 0.129 -> 0.062); LUMPI 0.272 / 0.170 -> 0.301 / 0.184 (late-A 0.271 -> 0.298). Upload gate passed on both tracks; kit scorer 74 s (10,671 boxes) and 181 s (17,193 boxes).
- Transfer finding: leaderboard levels follow realval-B (0.83-0.92 x B), but the S3 gains were 0.80 (V2X) and 0.81 (LUMPI) x the realval-A gain against 0.48 and 1.89 x the B gain; the scorecard protocol adds a leaderboard projection (previous leaderboard mAP + 0.8 x the A gain), the gates stay on B.
- Scorecard: static false-positive share at a fixed score and ranked above the median true-positive score (fusion cut the ranked static walker boxes 6.2 -> 1.8 per frame on V2X, 9.7 -> 4.1 on LUMPI); registry rows of TTA runs carry strategy S3.
- Submission files: the S3 upload copies above, and the checked S2 candidate [`lumpi_s2_submission.zip`](model-lumpi-track/routed-g2/submissions/2026-10-09_s2/lumpi_s2_submission.zip) (md5 `3d972c963a5949fcdd87d85c5a8e30bc`, never uploaded) for traceability. Upload copies are tracked from this release on.
- Tests: 52 (`python -m pytest -q common/tests`).

## 2.0 (pre-release, 2026-10-09)

**Leaderboard entries:** unchanged from 1.0 (LUMPI 965614, S1, combined 0.4728, rank 2 of 18; V2X 972563, S1+C1, combined 0.7855, rank 1 of 19). Their files are the 1.0 files above. No S2 version passed the upload gate, so 2.0 adds no entry file; the checked LUMPI S2 candidate `model-lumpi-track/routed-g2/submissions/2026-10-09_s2/lumpi_s2_submission.zip` was kept local in 2.0 and is committed in 3.0 for traceability (checked, never uploaded).

**What 2.0 contains**
- Strategy S2, *Center-Routed Small Objects* ([`docs/02-STRATEGY.md` Section 8.2.1](docs/02-STRATEGY.md#821-results-2026-10-09); [decision record](docs/decisions/2026-10-09-s2-center-routed.md)): CenterPoint members at stride 8 and 4 on both tracks (`centerpoint-g1v3`, `centerpoint-s4-g1v3`), routed models `routed-g2`. Gates: LUMPI Bicycle moves to CenterPoint (realval-B 0.102 -> 0.128) but the combined estimate gains +0.003, below the +0.005 upload gate; V2X keeps S1+C1.
- A runtime fix for OpenPCDet's `CenterHead.assign_targets`, which relabeled classes across head groups (V2X pedestrians trained the vehicle head): `common/bdc26/detect/pcdet_patches.py`, applied by `register()`, with a regression test.
- Diagnosis that static structures cause 72-77% (V2X) and 50-69% (LUMPI) of the unmatched walker detections (oracle bound: V2X pedestrian realval-B 0.252 -> 0.346), which promotes static hard negatives (R3) in the plan.
- Tools: `pcdet_smoke.py` (measured training cost), `route_predictions.py validate` and `select --rule joint --calibrated`, `scorecard.py --realism-from`, track-prefixed upload copies `<track>_<strategy>_submission.zip` from the packager.
- R track: legal late-A realism proxies; the frame re-selection (R2) failed its gate, S1 frames kept.
- Tests: 47 (`python -m pytest -q common/tests`).

## 1.0 (pre-release, 2026-10-09)

**Leaderboard entries** (development phase; public leaderboards checked 2026-10-09):

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S1 | 965614 | 2026-10-06 21:37 | 0.4728 | 0.1357 | 0.8912 | 2 of 18 (1 until Oct 7) | [`submission_lumpi.zip`](model-lumpi-track/routed-g1/submissions/2026-10-02_first/submission_lumpi.zip) (`ea2c76393d6f8868762d6bac1ac03fa8`) | [s1 first submission](docs/decisions/2026-10-06-s1-first-submission.md) |
| 2 V2X-Real (16685) | S1+C1 | 972563 | 2026-10-09 15:17 | **0.7855** | 0.4869 | 0.9203 | **1 of 19** | [`submission_v2x.zip`](model-v2x-track/routed-g1z/submissions/2026-10-09_zcal/submission_v2x.zip) (`7fbb973e2c1715dea66d7850b8bde11f`) | [s1 close-out](docs/decisions/2026-10-09-s1-closeout-z-calibration.md) |

Per-class AP, realism terms and the scoring logs: [`codabench_965614.json`](model-lumpi-track/routed-g1/submissions/2026-10-02_first/codabench_965614.json), [`codabench_972563.json`](model-v2x-track/routed-g1z/submissions/2026-10-09_zcal/codabench_972563.json). The LUMPI file was uploaded as `submission_lumpi_karmarv.zip` (same bytes; also a release-0.1 asset). Field on 2026-10-09: LUMPI leader 0.4784 (mAP 0.1185, realism R 0.942); V2X runner-up 0.6616.

**What 1.0 contains**
- Strategy S1, *Calibrated Twin, Routed Pillars* ([`docs/02-STRATEGY.md` Section 8.1](docs/02-STRATEGY.md#81-s1-calibrated-twin-routed-pillars)): engine G1 synthetic data, PointPillars members, per-class post-processing and routing; models `model-<track>/routed-g1`.
- S1 close-out: joint routing with the class gate, `scorecard.py` with a paired frame bootstrap, the `strategy` registry column, evaluation subsets and error breakdowns, and the range-dependent z calibration C1, which gives the V2X version S1+C1 (`model-v2x-track/routed-g1z`, +0.019 combined on the leaderboard).
- Documentation: the strategy routes S2-S6 with steps and gates, the decisions folder (submission register, evaluation protocol and gates, progression tracker, calendar, dated records), named references R1-R42.
- Tests: 44 (`python -m pytest -q common/tests`).

## Earlier tags

0.1 (S1 first submission, 2026-10-06; zips as release assets), 0.2 (documentation of the strategy routes). 1.0 to 5.0 are described above.
