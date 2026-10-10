# Decisions, submissions and gates

> The one place for what was submitted, why it was decision-ready, and the gates every submission passes. Strategies (what each one builds and its steps) are in [`02-STRATEGY.md` Section 8](../02-STRATEGY.md#8-strategy-routes-after-s1); per-class tables and diagnostics are in the track model READMEs ([LUMPI](../../model-lumpi-track/README.md), [V2X](../../model-v2x-track/README.md)) Sections 7 and 9.

**Contents:** [1 How this folder works](#1-how-this-folder-works) · [2 Submission register](#2-submission-register) · [3 Evaluation protocol and gates](#3-evaluation-protocol-and-gates) · [4 Progression tracker](#4-progression-tracker) · [5 Calendar and compute plan](#5-calendar-and-compute-plan) · [6 Decision records](#6-decision-records)

## 1. How this folder works

| Rule | Description |
|---|---|
| When to write a record | A version becomes decision-ready for submission (it passed the upload gate, or a gate result changes the plan), or a rule, data-use, legal or organizer question is decided. Diagnostics, ablations and per-class tables stay in the model READMEs. |
| File name | `YYYY-MM-DD-<scope>-<topic>.md`. Scope: the strategy code in lowercase (`s1`, `s2`, ...; a variant keeps its parent code, for example `s1-closeout-...` for S1+C1), `rules` (data use, integrity, legal, organizer answers) or `plan`. |
| Size | About 40 lines at most: version, numbers, gate, decision. Long evidence is linked, not copied. |
| Template | Version, Context, Evidence, Gate, Decision, Outcome, Consequences (below). |
| Updates | The leaderboard outcome and later facts are added to the same record. A replaced record gets a first line `Superseded by <record>` and stays. |
| Index | Every record has one row in Section 6; every upload and every decision-ready version has one row in Section 2. |

```
# <date> <strategy or scope>: <decision in a few words>
**Version.** model folder and submissions/<date>_<tag>/ (strategy code)
**Context.** what was being decided and why now (one paragraph)
**Evidence.** realval-A/B per class with bootstrap intervals, R, estimate, kit-scorer check (a table)
**Gate.** which gate of Section 3, the numbers against its thresholds, passed or failed
**Decision.** what we do
**Outcome.** CodaBench id, leaderboard numbers, confirmation passed or failed (added after the upload)
**Consequences.** what changes for later strategies, configs or rules
```

## 2. Submission register

Every CodaBench upload and every decision-ready version, newest first. Leaderboards: [Track 1 (16684)](https://www.codabench.org/competitions/16684/#/results-tab), [Track 2 (16685)](https://www.codabench.org/competitions/16685/#/results-tab). Server records (`codabench_<id>.json`) sit in each submission folder.

| Date | Version | Track | Model / submission folder | Local A / B mAP, R, estimate (B) | Gate | CodaBench id | Leaderboard combined (mAP, R) | Rank | Record |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-09 | **S3** | V2X | [`routed-g3`](../../model-v2x-track/routed-g3) / [`2026-10-09_s3`](../../model-v2x-track/routed-g3/submissions/2026-10-09_s3) | 0.661 / 0.664, 0.919, 0.937 | **upload gate passed** (+0.109); kit scorer 74 s, 10,671 boxes; **confirmed** | [974400](../../model-v2x-track/routed-g3/submissions/2026-10-09_s3/codabench_974400.json) (2026-10-10) | **0.8381** (0.5483, 0.9203) | **1 of 19**
| 2026-10-09 | **S3** | LUMPI | [`routed-g3`](../../model-lumpi-track/routed-g3) / [`2026-10-09_s3`](../../model-lumpi-track/routed-g3/submissions/2026-10-09_s3) | 0.301 / 0.184 (late-A 0.298), 0.905, 0.520 | **upload gate passed** (+0.015); kit scorer 181 s, 17,193 boxes; confirmed by the scorer log | 974348 (2026-10-10; status Running after the scorer finished) | **0.5015** (0.1692, 0.8912) by the scorer log | not on the leaderboard yet (would lead: 0.4784)
| 2026-10-09 | S2 | LUMPI | [`routed-g2`](../../model-lumpi-track/routed-g2) / [`2026-10-09_s2`](../../model-lumpi-track/routed-g2/submissions/2026-10-09_s2) | 0.272 / 0.170 (late-A 0.271), 0.905, 0.508 | class gate passed for Bicycle; **upload gate failed** (+0.003 < 0.005) | not uploaded (`lumpi_s2_submission.zip` checked: valid, 156 s) | - | - | [s2 center-routed](2026-10-09-s2-center-routed.md) |
| 2026-10-09 | S2 | V2X | [`routed-g2`](../../model-v2x-track/routed-g2) | 0.585 / 0.537 (equal to S1+C1) | no class passed the class gate | - | - | - | [s2 center-routed](2026-10-09-s2-center-routed.md) |
| 2026-10-09 | **S1+C1** | V2X | [`routed-g1z`](../../model-v2x-track/routed-g1z) / [`2026-10-09_zcal`](../../model-v2x-track/routed-g1z/submissions/2026-10-09_zcal) | 0.585 / 0.537, 0.919, 0.828 | upload gate passed (+0.014); confirmed | [972563](../../model-v2x-track/routed-g1z/submissions/2026-10-09_zcal/codabench_972563.json) | **0.7855** (0.4869, 0.9203) | 1 of 19 | [s1 close-out](2026-10-09-s1-closeout-z-calibration.md) |
| 2026-10-09 | S1+C1 | LUMPI | none | calibration at most +0.004 on B | class gate failed for every class | - | - | - | [s1 close-out](2026-10-09-s1-closeout-z-calibration.md) |
| 2026-10-06 | **S1** | V2X | [`routed-g1`](../../model-v2x-track/routed-g1) / [`2026-10-02_first`](../../model-v2x-track/routed-g1/submissions/2026-10-02_first) | 0.572 / 0.520, 0.919, 0.814 | first upload (Gate A) | [965633](../../model-v2x-track/routed-g1/submissions/2026-10-02_first/codabench_965633.json) | 0.7665 (0.4648, 0.9203) | 1 (Oct 6) | [s1 first submission](2026-10-06-s1-first-submission.md) |
| 2026-10-06 | **S1** | LUMPI | [`routed-g1`](../../model-lumpi-track/routed-g1) / [`2026-10-02_first`](../../model-lumpi-track/routed-g1/submissions/2026-10-02_first) | 0.260 / 0.166, 0.905, 0.505 | first upload (Gate A) | [965614](../../model-lumpi-track/routed-g1/submissions/2026-10-02_first/codabench_965614.json) | **0.4728** (0.1357, 0.8912) | 1 (Oct 6); **2 of 18 since Oct 7** | [s1 first submission](2026-10-06-s1-first-submission.md) |
| 2026-10-02 | S1, hand-edited copy | V2X | - | | not the packaged zip | 957439 | cancelled after 4 days with no log | - | [s1 first submission](2026-10-06-s1-first-submission.md) |
| 2026-10-02 | S1, hand-edited copy | LUMPI | - | | not the packaged zip | 957399 | Failed, no score | - | [s1 first submission](2026-10-06-s1-first-submission.md) |

**Current entries:** V2X 974400 (S3, [`v2x_s3_submission.zip`](../../model-v2x-track/routed-g3/submissions/2026-10-09_s3/v2x_s3_submission.zip)); LUMPI 965614 (S1, [`submission_lumpi.zip`](../../model-lumpi-track/routed-g1/submissions/2026-10-02_first/submission_lumpi.zip)) until the S3 upload 974348 ([`lumpi_s3_submission.zip`](../../model-lumpi-track/routed-g3/submissions/2026-10-09_s3/lumpi_s3_submission.zip), scored 0.5015 by the scorer log) leaves the Running status; both S3 files in release 3.0 ([`RELEASES.md`](../../RELEASES.md)). **Budget used** (development, 100 per track, 5 per day): LUMPI 2 (965614, 974348; failed uploads do not count), V2X 4 (957439, 965633, 972563, 974400). **Competition (2026-10-10):** LUMPI leader Raj Patil (966997, Oct 7) 0.4784 with mAP 0.1185 and realism R 0.942 (CD 0.877, MMD 0.0001, EMD 1.108, FPD 0.498), close to the real-vs-real ceiling; the LUMPI S3 score (0.5015) is above it by detection alone. V2X runner-up linyongchun 0.6616. Details: [`01-CHALLENGE-FACTS.md`](../01-CHALLENGE-FACTS.md) Section 7.

## 3. Evaluation protocol and gates

### 3.1 Scorecard

Every model and every candidate gets the same numbers from [`scorecard.py`](../../common/tools/scorecard.py) (stored as `validation/results/scorecard.json`; `--vs <model>` adds the paired bootstrap and the class gate):

| Metric | Definition | Why it is in the scorecard |
|---|---|---|
| B-mAP (**primary**) | realval-B, official 3D mAP@0.5 R40 over the classes with test GT | predicted the leaderboard mAP best (leaderboard / B: LUMPI 0.82, V2X 0.89 and 0.91) |
| A-mAP and late-A mAP | realval-A; late-A (LUMPI only) is its Measurement4 frames 4800-6399, the legal frames closest to the excluded test window | A is the selection split; late-A follows the drift toward the test window (LUMPI Person 0.42 early, 0.20 late) |
| B/A ratio | B-mAP / A-mAP | transfer signature (S5 should raise it) |
| Per-class B AP | with the paired-bootstrap interval of the change vs the previous version | gates are per class |
| BEV-3D gap (B) | B mAP_bev@0.5 minus B mAP_3d@0.5 | height and z error (the V2X target of S2-S4) |
| 3D mAP@0.7 (B) | | localization quality |
| R | official realism score, mean of held-out proxies 4 and 5 (exact EMD) | changes only with the 50 frames |
| Combined estimate (B) | `0.6 * clip(B-mAP / 0.7) + 0.4 * R` | the number an upload must beat; still optimistic (S1: LUMPI 0.505 vs 0.473, V2X 0.814 vs 0.767; S1+C1 0.828 vs 0.786; S3: LUMPI 0.520 vs 0.501, V2X 0.937 vs 0.838) |
| Leaderboard projection | previous leaderboard mAP + 0.8 x the A-mAP gain | the S3 gains transferred at 0.80 (V2X) and 0.81 (LUMPI) x the realval-A gain but at 0.48 and 1.89 x the realval-B gain; fitted on S3, re-checked at every upload; for expectations only, the gates stay on B |
| Server cost | `check_submission.py --official` wall time and box count | must stay under 400 s (3x margin under the 1,200 s limit) |
| Leaderboard (after upload) | combined, mAP, R, per-class AP; leaderboard / B | confirmation only |

### 3.2 Gates

| Gate | Applies to | Rule | Rationale |
|---|---|---|---|
| Class gate | each member, route, TTA variant, calibration or knob for one class | realval-B AP up by at least 0.01; paired frame bootstrap (200 resamples) P(gain) >= 0.9; realval-A down by at most 0.005 | B predicted the leaderboard; the bootstrap rejects noise on rare classes; the A guard stops trading away the selection split |
| Upload gate | each development upload, per track | combined estimate (B) at least 0.005 above the best previous uploaded version (now LUMPI 0.505, V2X 0.828; after the S3 uploads 0.520 and 0.937); kit scorer valid in under 400 s; LUMPI late-A not lower | one upload per version; the development leaderboard is the test set, so uploads confirm and never tune |
| Confirmation | after each upload | leaderboard combined not below the previous best; otherwise stop and diagnose transfer before the next strategy | S1+C1 passed (0.7855 vs 0.7665); S3 passed (V2X 0.8381 vs 0.7855; LUMPI 0.5015 vs 0.4728 by the scorer log) |
| Gate E: freeze | Sun Oct 25 | no new features after this; final-phase candidates are confirmed versions only | [`02-STRATEGY.md` Section 4](../02-STRATEGY.md#4-decision-gates) |
| Final submissions | Nov 1-14 | 1 per day, 5 in total, hidden leaderboard, no carry-over; each a confirmed version | [`02-STRATEGY.md` Section 8.8](../02-STRATEGY.md#88-final-phase-plan-nov-1-14) |

### 3.3 Recording a version

1. Candidate: registry rows (with the `strategy` column), `scorecard.json`, a row in Section 4.
2. Decision-ready (upload gate passed): a record in this folder named for its strategy, a row in Section 2.
3. Upload: the packager's track-prefixed copy `<track>_<strategy>_submission.zip` (byte-identical to `submission.zip`), unchanged; save the scoring log as `codabench_<id>.json`; `package_submission.py <model> --tag <tag> --record <id> <json>`; fill the Outcome of the record and the rows in Sections 2 and 4, the track model README Section 9 and the root README Section 9; when the version becomes a leaderboard entry, commit its upload copy `<track>_<strategy>_submission.zip` next to the manifest (1.0 entries: `submission_<track>.zip`) and add it to [`RELEASES.md`](../../RELEASES.md) under the release tag (the entrant chooses the tags).

## 4. Progression tracker

One row per version and track; realism R is the mean of held-out proxies 4-5.

| Version | Track | A-mAP | B-mAP | B/A | BEV-3D gap (B) | 3D@0.7 (B) | R | Estimate (B) | Check time / boxes | LB combined | LB mAP | LB R | LB / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | LUMPI | 0.260 (late-A 0.255) | 0.166 | 0.64 | 0.025 | 0.051 | 0.905 | 0.505 | 133 s / 17,095 | 0.4728 | 0.1357 | 0.8912 | 0.82 |
| S1 | V2X | 0.572 | 0.520 | 0.91 | 0.146 | 0.058 | 0.919 | 0.814 | 90 s / 18,728 | 0.7665 | 0.4648 | 0.9203 | 0.89 |
| S1+C1 | V2X | 0.585 | 0.537 | 0.92 | 0.129 | 0.055 | 0.919 | 0.828 | 86 s / 18,728 | **0.7855** | **0.4869** | 0.9203 | 0.91 |
| S2 | LUMPI | 0.272 (late-A 0.271) | 0.170 | 0.62 | 0.025 | 0.052 | 0.905 | 0.508 | 156 s / 24,639 | below the upload gate | | | |
| S2 | V2X | 0.585 | 0.537 | 0.92 | 0.129 | 0.055 | 0.919 | 0.828 | (equal to S1+C1) | no new version | | | |
| S3 | LUMPI | 0.301 (late-A 0.298) | 0.184 | 0.61 | 0.021 | 0.062 | 0.905 | 0.520 | 181 s / 17,193 | **0.5015** (log) | **0.1692** | 0.8912 | 0.92 |
| S3 | V2X | 0.661 | 0.664 | 1.00 | 0.062 | 0.078 | 0.919 | 0.937 | 74 s / 10,671 | **0.8381** | **0.5483** | 0.9203 | 0.83 |
| S4 | LUMPI / V2X | | | | | | | | | | | | |
| S5 | LUMPI / V2X | | | | | | | | | | | | |

## 5. Calendar and compute plan

| Dates | Development work | GPUs 0-3 (LUMPI) | GPUs 4-7 (V2X) | Gate / upload | Status |
|---|---|---|---|---|---|
| Fri Oct 9 | S1 close-out (tools, diagnostics, C1); V2X S1+C1 upload (972563); **S2 complete** (CenterPoint stride 8 and 4 on both tracks, label-bug fix, gates); R1-R2; **S3 complete** (TTA variants of all members, fusion, score floors; decision-ready on both tracks, 3 days ahead) | S2 runs; S3 TTA tuning | S2 runs; S3 TTA tuning | 972563; S2: no upload-ready version; **S3 gate passed on both tracks** | done |
| Sat Oct 10 - Mon Oct 12 | S3 uploads by the entrant and their confirmation; R3 engine G2-lite: static clutter as hard negatives (poles, signs, trees, parked-car rows) and 12-20 m trucks (CPU; promoted by S2, still the walker lever after S3) | S4 smoke (measures the cost), then PV-RCNN++ | S4 smoke, then PV-RCNN++ | **S3 uploads** (Oct 10): V2X 974400 confirmed (0.8381, rank 1); LUMPI scored 0.5015, status Running | next |
| Tue Oct 13 | S4 into `routed-g4` (plain and TTA variants; `fuse` and `budget` re-run); R3 continues | S4 tuning | S4 tuning | | planned |
| Wed Oct 14 - Thu Oct 15 | S4 into the portfolio; R3 corpus `g1-v4` built and checked (static false-positive rate, realism on proxies) | `g1-v4` retrain of the kept LUMPI members | `g1-v4` retrain of the V2X members | **S4 gate, uploads (Thu)** | planned |
| Fri Oct 16 - Sat Oct 17 | R3/R4 gate: `g1-v4` members vs `g1-v3` (static false positives, class gate), realism frames from `g1-v4` | | | **R3 gate, uploads** | planned |
| Sun Oct 18 - Thu Oct 22 | S5 (GBlobs) on the best voxel member, runs a-c | S5 runs | S5 runs | **S5 gate (Thu)** | planned |
| Fri Oct 23 | extra seeds of kept members | seeds | seeds | | planned |
| Sat Oct 24 | final portfolio and realism frames; dry-run packaging | | | | planned |
| Sun Oct 25 | **Gate E: feature freeze** | | | | planned |
| Mon Oct 26 - Fri Oct 30 | at most 2 confirmation uploads per track; report outline; S6 smoke as research | S6 smoke | | dev phase closes Fri Oct 30, 17:00 PDT | planned |
| Nov 1 - Nov 14 | final phase ([`02` Section 8.8](../02-STRATEGY.md#88-final-phase-plan-nov-1-14)) | | | 1 per day, 5 in total | planned |

If a route slips by more than a day, the next route starts on time and the slipped one is dropped or moved after the freeze; nothing is added after Gate E. This calendar replaces the Week 2-4 rows of [`05-SCHEDULE-AND-RUNBOOK.md`](../05-SCHEDULE-AND-RUNBOOK.md).

## 6. Decision records

| Date | Scope | Record | Decision |
|---|---|---|---|
| 2026-10-09 | S3 | [`2026-10-09-s3-fused-portfolio.md`](2026-10-09-s3-fused-portfolio.md) | S3 decision-ready on both tracks: TTA variants, cross-architecture fusion and score floors (V2X B 0.537 -> 0.664, estimate 0.937; LUMPI B 0.170 -> 0.184, estimate 0.520); uploaded 2026-10-10: V2X 974400 0.8381 (rank 1), LUMPI scored 0.5015 (status Running); both confirmed |
| 2026-10-09 | S2 | [`2026-10-09-s2-center-routed.md`](2026-10-09-s2-center-routed.md) | no S2 upload: LUMPI Bicycle moves to CenterPoint but the upload gate fails (+0.003); V2X unchanged; OpenPCDet CenterHead bug fixed; static false positives found to be the main walker error (R3 promoted) |
| 2026-10-09 | S1+C1 | [`2026-10-09-s1-closeout-z-calibration.md`](2026-10-09-s1-closeout-z-calibration.md) | V2X range-dependent z calibration kept for vehicle and pedestrian (972563: 0.7855, confirmed); none for LUMPI |
| 2026-10-06 | S1 | [`2026-10-06-s1-first-submission.md`](2026-10-06-s1-first-submission.md) | S1 uploaded unchanged on both tracks (965614: 0.4728, 965633: 0.7665) after two hand-edited copies failed; gates rank on realval-B from now on |
| 2026-09-30 | S1 | [`2026-09-30-s1-g1-generator.md`](2026-09-30-s1-g1-generator.md) | engine G1: ray-cast walkers, UT Van as Van, calibrated background density (gray area, disclosed), walker v2, V2X calibration on legal real data |
| 2026-09-30 | rules | [`2026-09-30-rules-real-data-download.md`](2026-09-30-rules-real-data-download.md) | real LUMPI and V2X-Real downloaded on the entrant's instruction; used only through the guard; licence sign-off open |
| 2026-09-30 | rules | [`2026-09-30-rules-research-exposure.md`](2026-09-30-rules-research-exposure.md) | real data touched during research before the guard existed, and its follow-up check |
| 2026-09-30 | plan | [`2026-09-30-plan-review.md`](2026-09-30-plan-review.md) | review of the earlier plan set and what replaced it (historical) |
