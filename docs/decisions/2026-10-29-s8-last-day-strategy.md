# 2026-10-29 S8 last-day strategy: what the last 21 hours of the development phase and the final phase can still buy

**Result (2026-10-30): LUMPI `s8d` (S8.3) 1022492 scored 0.525688, rank 1, the LUMPI entry and F1 (Section 10.3); before it S8.2 `s8c` 1022399 0.525439 (+0.00154 over `s8b`; Car +0.0126). V2X stays `s8v`.** Release 8.0, both uploads confirmed, rank 1 on both tracks: LUMPI `s8b` 1022250 **0.523901** (+0.00106 over 1014495), V2X `s8v` 1022246 **0.902153** (+0.00398 over 1014682); Section 8.5. S8.2 (Section 9) is 8.1.

**Status: adopted 2026-10-30, 09:44 CDT** (the entrant's go: build S8 on LUMPI, U1 then U2, V2X U2 second priority, upload bar (b); Section 7 decisions 1-3). Rule 8 below narrows U2 for the late go and was written before any 12-view result existed. The measurements in Section 4 ran on legal validation frames only, from the session scratchpad, with no change to the repository.

## 1. Situation

**Clock and budget.**
- The development phase closes **Fri Oct 30, 19:00 CDT** (2026-10-31 00:00 UTC), about 21 hours after this record. The closing UTC day allows 5 uploads per track (used so far: LUMPI 8, V2X 11 of 100).
- The final phase runs Nov 1-14: 1 upload per day, 5 in total, scores hidden, **the same test data**, and development submissions are not carried over ([`01-CHALLENGE-FACTS.md` Section 2](../01-CHALLENGE-FACTS.md#2-timeline)). The last day of the development phase is therefore the last time any change can be checked on the test set.
- Compute: 8 x RTX A6000 idle, 255 CPU threads, 704 GB free on `/`.

**Live leaderboard** (public API, 2026-10-30 02:41 UTC; R back-computed from the formula):

| Track | Ours | Second | Third | Lead |
|---|---|---|---|---|
| LUMPI | **0.5228** (1014495; mAP 0.175, R 0.932, EMD 1.30) | Raj Patil 0.5108 (1020065, uploaded Oct 29 23:52 UTC; mAP 0.156, R 0.942, EMD 1.11) | dipper13579 0.4999 (mAP 0.144, R 0.942, EMD 1.10) | **+0.012** |
| V2X | **0.8982** (1001919 = 1014682; mAP 0.612, R 0.933) | Raj Patil 0.8112 (mAP 0.523, R 0.908) | linyongchun 0.7794 (mAP 0.462, R 0.960) | +0.087 |

**Reading.**
- **V2X is safe.** No V2X change is needed for the ranking; one is worth making only if it is free of risk.
- **LUMPI is at risk.** The second entry gained +0.015 in one day (0.4960 on Oct 28, 0.5108 on Oct 29). Our lead is +0.016 on detection (0.6 x D) and -0.004 on realism (0.4 x R).
- **Both LUMPI challengers reach EMD 1.10 against our 1.30.** That is the whole realism gap (0.2 m of EMD = 0.01 R = 0.004 combined). It is a content gap of the generator, not of frame selection: R5 and S6 showed that frame selection on the `g1-v4` pool is saturated and that +0.003 R is within 1.5-2 sd of the scorer's subsample draw.
- **Information use.** Competitors' per-class numbers are computed on the forbidden frames. Under audit rules c and d they inform this threat assessment only and never a per-class choice of ours.

## 2. Where points can still come from

`combined = 0.857 x mAP + 0.4 x R` while mAP <= 0.70.

| | LUMPI | V2X |
|---|---|---|
| Detection headroom (combined) | 0.450 | 0.075 |
| Realism headroom (combined; ceiling real-vs-real) | about 0.006 (R ceiling 0.933-0.947) | about 0.011 (R ceiling 0.961) |
| +0.01 mAP | +0.0086 | +0.0086 |
| +0.01 in one class | +0.0012 (1 of 7) | +0.0029 (1 of 3) |
| Weakest classes on the test set | Motorcycle 0.001, Bus 0.003, Truck 0.063 (frozen since R5: no local split predicts them) | pedestrian 0.429 |
| Realism detail | EMD 1.302 is 96% of the realism loss | EMD 1.182 (88.5%); CD 1.986 sits at the 2.0 clip: any frame change must keep CD below 2.0 |

The retrospective ([`02-STRATEGY.md` Section 8.10](../02-STRATEGY.md#810-retrospective-after-r5-2026-10-15-what-each-step-bought-why-and-what-is-left)) and the S7 reviews leave three kinds of lever:
1. **Inference ensembling** (S3 TTA and fusion: 44% of the V2X and 61% of the LUMPI leaderboard gain, transferred at about 0.8 x realval-A). The view set has not changed since S3.
2. **Provably non-negative completions** (boxes scored below every existing box of their class cannot lower AP; R5 walker tail copies transferred at 1.07 x B).
3. **Generator content** (R3: the largest LUMPI realism gain, +0.041 R). Days, not hours.

Post-processing conventions (sizes, z, heights from points, range limits, re-centring, visibility) are saturated on both tracks (S7 review probes, [audit 2026-10-26](2026-10-26-rules-compliance-audit.md)).

## 3. What the 2024-2026 literature offers, mapped to the rules

| Idea | Evidence | Status here | Verdict |
|---|---|---|---|
| Wider TTA: flip x rotation combinations, global scale views, height shifts | HorizonLiDAR3D (arXiv 2006.15505): z +/-0.2 m and scale TTA with WBF, +3.18 mAPH on Waymo; RoboSense 2025 report (R39) | our members train with flips, rotation +/-10 deg and world scaling 0.95-1.05; the S3 views use only 8 of the in-distribution transforms | **pilot run (Section 4.1)** |
| Low-score completions (floors, tail copies, cross-class copies) | our R5 copies 1.07 x; ECCV winner's truck copies +0.0015 combined | floors cut LUMPI rare classes hard (Motorcycle 164 boxes, Bus 116); Person copies dropped in R5 on server cost only | **probe run (Section 4.2)** |
| Per-member score calibration before fusion | MoCaE (arXiv 2309.14976), up to 2.5 AP on COCO | more knobs fitted on the same two splits (left out in S6 for that reason) | not for the last day |
| Ground-referenced heights, re-centring on interior points | DiffuBox (arXiv 2405.16034): localization dominates cross-domain error | heights from points lost on V2X in the S7 probes; re-centring is in every member's tuned post-processing | no |
| Synthetic-only box refiner (DiffuBox-style, re-implemented: the code licence is NVIDIA "Other") | KITTI -> Lyft pedestrian 3D AP@0.5 14.2 -> 20.5 | our 3D@0.7 / 3D@0.5 ratio (LUMPI 0.085 / 0.175) says localization is open | final-phase research, blind |
| Crop re-scorer for static false positives and confusable classes | indirect (long-tailed 3D detection, arXiv 2211.08691) | static structures the twin lacks are the main walker error (S2) | final-phase research, blind |
| Foreground point generation (SPG, arXiv 2108.06709); rare-class object generators (OLiDM, arXiv 2412.17226) | Waymo -> Kirkland PointPillars vehicle 34.7 -> 41.6; nuScenes +2.4 mAP | needs retraining of every member | days; not before the final |
| Diffusion "realification" with a prior from other real data (DRUM 2603.26263, CoLiGen 2312.15817) | segmentation gains; the RangeLDM redraws of Luo et al. (2609.07590) showed no hidden-set gain on V2X | sensor mismatch with non-roadside priors | no |
| Background subtraction (every published roadside method fits real background scans) | arXiv 2201.04756, 2204.09804, 2510.22390 | off without a ruling (`01-CHALLENGE-FACTS.md` Section 10, Q2); a mask from the twin cannot remove structures the twin lacks, and those are most of the false positives | no |
| Sensor-model refinements (ray-drop, noise) | Synth It Like KITTI (2502.15076): ray-drop about 0, label convention +25-30 car AP | our conventions are already matched | no |

No team of this edition has published its method (GitHub and arXiv searched 2026-10-29); the ECCV repositories are unchanged since 2026-09-02.

## 4. Measured tonight (legal validation frames; scratchpad; no repository change)

### 4.1 Wider TTA pilot

Five routed members, each run with the entry's views (V8 = `flip4+yaw+z`, the baseline) and two wider sets, all through the unchanged `pcdet_predict.py` (views monkeypatched, two-stage members run in chunks of 8 views because the voxel-query kernel fails above 8) and **the members' existing `postprocess_tta.yaml`, tuned for V8**, so the wider sets are measured at a disadvantage:
- **W16:** flip4 x {0, +5, -5 deg} plus z +/-0.25 m on the identity and the xy flip (16 views);
- **S12:** V8 plus global scale 0.95 and 1.05 on the identity and the xy flip (12 views; inside the training range `WORLD_SCALE_RANGE [0.95, 1.05]`).

| Track | Member (role) | Class | V8 on B | W16 B | W16 A | S12 B | S12 A |
|---|---|---|---|---|---|---|---|
| V2X | `voxelrcnn-ros-g1v3` (pedestrian route and fusion) | **mAP** | 0.6670 | +0.0047 | +0.0059 | +0.0073 | +0.0053 |
| | | vehicle | 0.8108 | +0.0050 | +0.0045 | +0.0006 | +0.0014 |
| | | pedestrian | 0.3931 | +0.0116 | +0.0078 | +0.0112 | +0.0117 |
| | | truck | 0.7972 | -0.0025 | +0.0055 | +0.0101 | +0.0026 |
| V2X | `pvrcnnpp-ros-g1v4-s2` (vehicle fusion) | **mAP** | 0.6710 | +0.0003 | -0.0010 | +0.0029 | +0.0022 |
| | | vehicle | 0.8219 | +0.0018 | +0.0036 | +0.0030 | -0.0007 |
| | | pedestrian | 0.3719 | +0.0075 | +0.0014 | +0.0071 | +0.0043 |
| | | truck | 0.8193 | -0.0083 | -0.0080 | -0.0014 | +0.0029 |
| V2X | `pointpillars-g1v5` (truck fusion) | **mAP** | 0.5892 | +0.0013 | +0.0013 | -0.0052 | -0.0015 |
| | | vehicle | 0.6568 | +0.0017 | -0.0037 | -0.0190 | -0.0112 |
| | | pedestrian | 0.2843 | +0.0103 | +0.0039 | +0.0102 | +0.0069 |
| | | truck | 0.8266 | -0.0083 | +0.0037 | -0.0070 | -0.0003 |
| LUMPI | `pointpillars-g1v4` (Person and Bicycle fusions) | **mAP** | 0.1955 | +0.0037 | +0.0197 | +0.0031 | +0.0036 |
| | | Person | 0.1343 | +0.0049 | +0.0192 | +0.0032 | +0.0073 |
| | | Car | 0.7755 | +0.0017 | +0.0017 | +0.0003 | -0.0004 |
| | | Bicycle | 0.2173 | +0.0075 | +0.0091 | +0.0034 | +0.0150 |
| | | Truck | 0.1154 | +0.0049 | +0.0036 | +0.0063 | +0.0028 |
| LUMPI | `pvrcnnpp-ros-g1v3` (Car fusion) | **mAP** | 0.1858 | +0.0041 | +0.0082 | +0.0046 | +0.0070 |
| | | Person | 0.0695 | +0.0059 | +0.0257 | +0.0021 | +0.0295 |
| | | Car | 0.7984 | +0.0032 | +0.0029 | +0.0020 | +0.0026 |
| | | Bicycle | 0.1923 | +0.0121 | +0.0180 | +0.0132 | +0.0260 |
| | | Truck | 0.1646 | +0.0045 | -0.0000 | +0.0072 | +0.0050 |

3D AP@0.5 R40. B is realval-B in full (V2X 298 frames) or every 2nd frame (LUMPI 434); A is every 2nd (V2X 344) or every 4th frame (LUMPI 320). The rare LUMPI classes are left out: realval-A holds almost no Motorcycle or Bus GT, so their deltas are noise.

**Reading.**
- **S12 (scale views) gains on both splits for 4 of 5 members**: V2X Voxel R-CNN +0.0073 / +0.0053, V2X PV-RCNN++ +0.0029 / +0.0022, LUMPI pillars +0.0031 / +0.0036, LUMPI PV-RCNN++ +0.0046 / +0.0070 (B / A). It loses only on the V2X pillars member, vehicle -0.019 on B.
- W16 (more flip and rotation combinations) gains on B for the same four members but less consistently on A, at 2 x the cost of V8 (S12: 1.5 x).
- **Largest class effects:** V2X pedestrian +0.011 on B on its route member, under both sets. LUMPI Bicycle +0.003 to +0.013 on B. LUMPI Person +0.002 to +0.006 on B and +0.007 to +0.030 on A.
- These are single members with post-processing tuned for V8. Inside the portfolio, fusion already averages part of this noise, so the portfolio gain will be smaller than the member gain. That is why U2 is projected at about +0.001, not +0.004.
- Cost measured on 8 GPUs in parallel: a LUMPI PV-RCNN++ member takes 1.1 s per frame with V8, 1.7 s with S12 and 2.1 s with W16.
- Two-stage members need the views in chunks of at most 8: the voxel-query kernel fails above 8 (`CUDA kernel failed: invalid configuration argument`), and a chunked forward fixes it.

### 4.2 Non-negative completion probe (LUMPI entry `routed-g10`, cached member predictions)

| Variant | realval-A mAP | realval-B mAP | Boxes per frame (A) | Classes moved |
|---|---|---|---|---|
| Entry | 0.3881 | 0.2250 | 485 | |
| All score floors removed | +0.0004 | +0.0005 | 946 | Bicycle, Motorcycle (B +0.0015), Bus, Truck, Van |
| Person tail copies (r 0.2 m, 4 copies), every box | +0.0007 | +0.0012 | 930 | Person A +0.0052, B +0.0082 |
| Person tail copies, top half of the scores | +0.0007 | +0.0012 | 707 | same gain at half the cost |
| Person tail copies, top 20% | +0.0006 | +0.0009 | 574 | Person A +0.0039, B +0.0062 |

The floors cost at most 0.0015 AP per class locally, by construction of `budget_select`. They were set for server cost, and the rare LUMPI classes have almost no local GT (realval-A holds 0.02 Motorcycle labels per frame), so the local probe cannot measure what they cost on the test set. Restoring them can only add.

## 5. Recommendation

### 5.1 Last day: at most two complete versions per track

**LUMPI (the track at risk): build S8 tonight and upload twice.** Both versions keep the entry's realism frames byte for byte, so only detection changes and nothing isolates realism.

| Upload | Version | What changes | Cost | Local evidence | Projection (0.6 x mean of the A and B gains, x 0.6 / 0.7) | Risk |
|---|---|---|---|---|---|---|
| **U1**, Fri morning | `routed-g11` / `s8a` | the entry plus the **non-negative completion**: every score floor above 0.01 lowered to 0.01 (Bicycle, Motorcycle, Bus, Truck, Van), and Person tail copies (r 0.2 m, 4 copies, scored below every Person box) for Person boxes scored at or above a constant t, the median of the entry's Person scores on realval-A | CPU, about 2 h including package, kit check and scorecard | Section 4.2: floors A +0.0004, B +0.0005; copies on the top half A +0.0007, B +0.0012 | about +0.0007 | none for AP (proof in `apply_tail_copies`; a floor only removes the lowest boxes); about 35-40k boxes, kit time measured against the 400 s rule (fallback in Section 6) |
| **U2**, Fri by 16:00 CDT | `routed-g11` / `s8b` | U1 plus the wider view set as **additional** TTA variants of every TTA checkpoint (`_tta12` next to `_tta`), so routing, fusion and the final check can pick either variant per class, like any member | GPU about 4 h (raw, tune and final predictions on A, B and the test frames for 15 checkpoints on 8 GPUs), portfolio 2-3 h | Section 4.1: LUMPI members +0.003 to +0.005 mAP on B with the post-processing tuned for V8 | about +0.001 on top of U1 (a guess: fusion absorbs part of each member's gain) | the final check freezes every class that does not gain on the pooled frames and on train-split frames alone; only the upload confirms transfer |

**V2X: optional, second priority.** The pilot gains on both V2X two-stage members, most on the pedestrian route member: pedestrian +0.011 on B and +0.008 to +0.012 on A. It loses on the pillars member (vehicle -0.019 with scale views). The same build can add `_tta12` variants for the 9 V2X TTA checkpoints in about 1 GPU-hour and let the gates choose per class: **U2-V2X**, with tail copies and the sparse stage re-derived as in S7. The lead is 0.087, so this version is worth uploading only if it passes the bar. If time runs short, LUMPI goes first, and F1 stays the S7.6 zip.

**Expected value, honestly.** U1 and U2 together project about +0.002 on LUMPI. That widens the lead from 0.012 to about 0.014; it does not decide the ranking. What they buy besides points is a **confirmed** F1: the leaderboard checks the two versions on the test set before it closes, which the final phase never will.

**Timeline, counted from the go** (a go at Thu 23:30 CDT puts U2's package at about Fri 09:30). U2 is dropped if it cannot be packaged by Fri 15:00 CDT.

| When | Step |
|---|---|
| go - +1.5 h | code: view set `flip4+yaw+z+scale` in `tta.py`, a `--tta-tag` suffix in `tune_and_eval.sh` and `member_tag` so the entry's `_tta` files and `postprocess_tta.yaml` are never overwritten, tail copies with a score threshold, unit tests; record the pre-registration (Section 6) before any run |
| +1.5 h - +3 h | U1: portfolio `routed-g11` with the completion only; package, `check_submission.py --official`, kit time, scorecard, reproduction script |
| +1.5 h - +6 h | GPU: `_tta12` raw, tune and final predictions for the 15 LUMPI TTA checkpoints, then the 9 V2X ones (8 GPUs, one job per GPU: the two-stage members need about 30 GB with chunked views; measured 1.7 s per LUMPI frame for a PV-RCNN++ member with 12 views) |
| +6 h - +10 h | U2: select, fuse (late-A Person rule, Van judge), budget, tail, final check against the entry, package, kit check, scorecard |
| +3 h, or Fri 08:00 CDT if later | the entrant uploads U1 (LUMPI scoring takes about 6-8 min) |
| by Fri 16:00 CDT | the entrant uploads U2 if it passes Section 6; three spare uploads stay unused |
| Fri 16:00 - 19:00 CDT | record both results; F1 chosen by Section 5.2 |

### 5.2 F1 on Nov 1

The best **confirmed** version per track, as its exact scored zip: S8 if it scored above the S7.6 entry on the development leaderboard, otherwise S7.6 (`lumpi_s7s_submission.zip` 1014495, `v2x_s7s_submission.zip` 1014682). Choosing among complete systems by their scored combined value is allowed ("resubmit your best system").

### 5.3 Final phase (Nov 1-14)

The final phase is blind, and LUMPI detection changes have transferred unreliably: LUMPI Car failed twice (S5 -0.010, S7.6 -0.004), and the rare classes follow no local split. **The levers that transfer reliably are realism and provable completions**, so the final phase spends its GPU time there.

| Work package | Track | What | Gate | Expected | When |
|---|---|---|---|---|---|
| **WP1 LUMPI realism content** | LUMPI | Close EMD 1.30 -> about 1.10, where both challengers stand. First, diagnose where our frames and the legal proxies differ in transport, by range ring, height band, sensor and static or dynamic content. Then make generator changes there, for example static structure the twin lacks or the density prior iterated on the G2-lite output (R5: +0.008 R on random frames). The members are retrained only if the corpus changes their input | held-out proxies +0.005 R (2-3 sd of the subsample draw), CD, MMD and FPD not worse; then a detection check of the retrained members through the 6.0 gates | +0.002 to +0.004 combined; realism has transferred at 1.0-1.5 x | Nov 1-7 |
| WP2 wider TTA tuned per view set | LUMPI | the S8 view sets with their own post-processing and both sets (20 views) where memory allows | 6.0 gates | +0.001 | with WP1 |
| WP3 synthetic-only box refiner (DiffuBox-style, re-implemented) | both | localization of Person and Bicycle (3D@0.7 is half of 3D@0.5) | 6.0 gates on realval A and B; research for the paper first | unknown | only if WP1 is done |
| WP4 compliance contingency C2 | both | walker placement without real label rows; retrain every member | only if the organizers' ruling requires it (audit item 19 and the walker rows, moderate risk) | keeps the entry eligible | on the ruling |

**Slots.**
- **F1** Nov 1: per Section 5.2.
- **F2** about Nov 6-8: the best gated candidate from WP1 and WP2.
- **F3** about Nov 11: a second candidate only if it passes every gate.
- **F4 and F5:** reserve for a ruling (WP4) or a packaging failure.
- **Last upload by Nov 13 (CST),** and **the last upload is the best-believed version** (F1's zip again if nothing beat it locally). Whether the best or the last final submission counts is still unanswered (`01-CHALLENGE-FACTS.md` Section 10, Q9), and this order gives the same result under both readings.

**Non-score work in the same period.**
- The disclosure email ([audit Appendix A](2026-10-26-rules-compliance-audit.md)) before the final phase opens. The top three must release code for verification, and the walker rows are the one moderate-risk item.
- The 4-8 page report (Nov 15) from [`docs/paper-bigdata2026/final-report/README.md`](../paper-bigdata2026/final-report/README.md) Sections 3-4.

### 5.4 Not doing, and why

| Lever | Why not |
|---|---|
| Unfreezing LUMPI Motorcycle or Bus routes (the S6 Motorcycle fusion passed its class gate at B +0.023) | the classes stayed frozen under the pre-registered rule; unfreezing them now, after their leaderboard values are known, is a leaderboard-informed change (audit rule d) |
| Any per-class choice informed by competitors' detailed results | computed on the forbidden frames (audit rules c and d) |
| A frames-only upload, or a realism sweep judged by uploads | probing the realism reference (Rules, Forbidden 3) |
| Background maps or persistence across the 50 test frames | outside the rules reading without a written ruling (`01-CHALLENGE-FACTS.md` Section 10, Q2) |
| Test-time adaptation, BN re-estimation, pseudo-labels | real frames as training input (FAQ, Sept 30) |
| A new detector family before the close | 6-8 h per member plus portfolio work; S2 and S6 found no transferable capacity gain |

## 6. Pre-registered rules for S8 (binding only if adopted, written before any S8 run)

1. **Scope.** LUMPI U1 and U2. V2X U2 only, and only after LUMPI is in hand. The realism frames are each entry's, byte for byte.
2. **Completion (U1).**
   - Every score floor above 0.01 is lowered to 0.01. Car (0) and Person (0.01) keep theirs; Unknown has no test GT and keeps its floor.
   - Person tail copies use r 0.2 m and 4 copies (the R5 radius), applied to Person boxes with score >= t. Here t is the median Person score of the entry's realval-A predictions, frozen as a constant (audit rule e: no statistic of the test frames).
   - The completion applies to the frozen classes as well. A change that cannot lower AP is exempt from the freeze, as the R5 copies were exempt from the 0.01 bar. Nothing else of a frozen class changes.
   - **Kit-time fallback:** if the kit scorer exceeds 400 s, the floor changes are undone in order of lowest pooled local AP gain per added box until it fits. Then the copies use t at the 0.8 quantile.
3. **Views (U2).**
   - One wider set, `flip4+yaw+z+scale`: V8 plus global scale 0.95 and 1.05 on the identity and on the xy flip (12 views). It is chosen because S12 gained on both LUMPI members on B at 1.5 x the cost of V8.
   - It is added as a second TTA variant of every checkpoint, never a replacement. The entry's `_tta` files and post-processing stay untouched, so the entry still rebuilds IDENTICAL.
   - Post-processing is tuned per variant with the S3 protocol (tune on A, report on B).
4. **Portfolio (U2).** The 6.0 steps on top of U1:
   - select (joint, calibrated, pooled) and fuse (up to 3 members, the pooled rule, the late-A Person rule, the Van judge);
   - then the floors of rule 2, the tail copies, and the final check against the entry per class.
   - The checks: a pooled A+B gain with P(gain) >= 0.9, neither split down by more than 0.005, and no loss on realval-A alone (audit rule a). A failing class reverts to its U1 configuration.
   - Bicycle, Motorcycle and Bus stay frozen except for the completion.
5. **Upload bar for the last day** (the entrant chooses one, Section 7):
   - **(a)** keep the 6.0 bar: a projection of at least +0.003 and a valid kit check under 400 s;
   - **(b)** a last-day bar: a projection above 0, every changed class through the final check, and the kit check under 400 s. The 6.0 bar protected a scarce upload budget against noise. On the last day 5 uploads remain, and the per-class final check still guards against noise.
6. **F1 rule.** The highest scored combined value among S7.6, U1 and U2 per track, as its exact scored zip.
7. **Audit rules a-e** apply unchanged: no model is fitted on real labels, no statistic of the test frames or the public test GT is used, and nothing is chosen from leaderboard numbers.

8. **Amendment at the go (Fri 09:44 CDT; written before any 12-view result).** The go came about 10 h after the timeline above assumed; the cut-off for U2 (packaged by 15:00 CDT) stands. So that U2 fits:
   - **Folders.** U1 is `model-lumpi-track/archive/routed-g11` (tag `s8a`), U2 is `model-lumpi-track/archive/routed-g11b` (tag `s8b`): the final check compares two folders.
   - **U1 constants.** Floors: Bicycle, Motorcycle, Bus, Truck and Van at 0.01; Person 0.01, Car none and Unknown 0.075 unchanged. Person copies: r 0.2 m, 4 copies, `min_score` t = 0.0508, the median of the 142,612 Person scores of `routed-g10` on realval-A (1,280 frames).
   - **U2 candidates.** The `_tta12` variant (views `flip4+yaw+z+scale`, post-processing tuned on A from the neutral start as for `_tta`, reported on B) only for the 7 TTA checkpoints in the incumbent fusions of the unfrozen classes: Person `pp4`, `vrros4s2`; Car `pvros` (the 6-seed bag `bagpv4x` stays at 8 views: about 6 GPU-hours); Truck `pvros4d2`, `ppros`; Van `vrros4`, `g1`. No select or fuse search: per class **one candidate**, the incumbent fusion with each of these members replaced by its `_tta12` sibling, same IoU and weights (`fuse --pooled-rule --swap-variant tta12`, the S7.6 swap pattern, Person ranked on late-A as in S7.6).
   - **U2 checks.** U1's floors and copies, then the final check against U1 (`s7_check.py check`, the rule 4 conditions; Van by its S6 judge; Bicycle, Motorcycle and Bus frozen at U1). A failing class keeps U1.
   - **V2X U2** runs only if GPUs are free after the LUMPI variants and its package can be ready by 15:00 CDT, under the same pattern (route and fusion members of the 9 V2X TTA checkpoints).

## 7. Decisions for the entrant

| # | Decision | Recommended | Deadline |
|---|---|---|---|
| 1 | Build S8 on LUMPI tonight (U1 completion, U2 wider TTA) | **yes**: about +0.002 projected, construction-safe for U1, and the last chance to confirm anything on the test set | by Fri 03:00 CDT for U2 (about 10 h from go to package); U1 alone needs about 3 h |
| 2 | Upload bar for U2 (Section 6.5) | **(b) last-day bar**: under (a), U2 almost surely stays local, and the final phase could then never confirm it | before U2's portfolio step (+6 h) |
| 3 | V2X U2 (wider views, gates choose per class) | **yes, second priority**: about 1 GPU-hour, pedestrian +0.011 on its route member; the lead is safe, so upload only if it passes the bar | Fri 12:00 CDT |
| 4 | The disclosure email | **send** Oct 30 or 31, as a reply in the LOI thread | before Nov 1 |
| 5 | Final-phase WP1 (LUMPI realism content) | **yes**: it is the one gap both challengers have closed, and realism transfers | Nov 1 |

## 8. Build log (Fri Oct 30, from the go at 09:44 CDT)

Pipeline: `common/pipeline/s8_portfolio.sh` (stages `u1`, `u1pkg`, `u2`, `v2x`); logs and events in `bdc26-data/logs/s8/`. Code added for S8, all of it off the entries' paths, so routed-g10 and routed-g12 still rebuild unchanged:
- `bdc26.detect.tta`: the `scale` view part;
- `pcdet_predict.py`: views in chunks of at most 8 and `--from-raw`;
- the 59 identical `tune_and_eval.sh` copies: `--tta-tag` and `--reuse-raw`;
- `_common.member_tag`: `tta_tag`;
- `route_predictions.py`: tail copies `min_score` and `fuse --swap-variant`;
- tests in `common/tests/test_s8.py`.

### 8.1 U1, `routed-g11` / `s8a`: ready for upload

- **Kit-time fallback (rule 2).** The first package (copies at t = 0.0508) took the kit scorer **437-463 s** (38,495 boxes; the entry took 291 s in the same parallel batch). Timing every cumulative floor undo in the rule's order showed that the floors do not drive the time:

  | Variant | Boxes | Kit time |
  |---|---|---|
  | U1, copies at t = 0.0508 | 38,495 | 437 s |
  | undo Truck, Motorcycle, Bicycle, Van | 33,471 | 435 s |
  | undo all floors | 33,098 | 452 s |
  | all floors undone, copies at q0.8 | 26,682 | 347 s |
  | **all floors kept, copies at q0.8** | **32,079** | **320 s** (318 s in the final package) |

  Floor-added boxes are rare-class boxes and cost almost nothing to score; the Person copies are what cost time. The rule's second step, copies at the 0.8 quantile, is what fits. Undoing floors is needed only until the version fits, and **no undo is needed**, so all floors stay lowered. This reading was decided from the cost timings alone, with no accuracy number from the test frames.
- **Final U1.** Floors at 0.01 for Bicycle, Motorcycle, Bus, Truck and Van. Person copies (r 0.2 m, 4 copies) for boxes scored >= **0.274**, the 0.8 quantile of routed-g10's realval-A Person scores.
- **Local result against routed-g10:**
  - realval-A mAP 0.3891 (+0.0010), realval-B 0.2262 (+0.0012), late-A 0.360;
  - per class on B: Person +0.0062 (pooled +0.0060, P 1.00), Motorcycle +0.0015, Bicycle +0.0005, the rest 0;
  - **projection +0.0006**: above 0, so U1 passes bar (b); it does not meet the 6.0 bar (+0.003).
- **Zip.** `model-lumpi-track/archive/routed-g11/submissions/2026-10-30_s8a/lumpi_s8a_submission.zip`, md5 `055507e5c90c00b257dd0763413086ad`. Official kit check valid, 318 s, 32,079 boxes. The 50 realism frames are byte-identical to the scored `s7s` zip. Reproduction scripts: `test/reproduce_s8a.sh`, `test/reproduce_s8a_validation.sh`.
- The over-budget first package was never uploaded; it was moved out of the repository.

### 8.2 V2X U2, `model-v2x-track/archive/routed-g13` / `s8v`: passes bar (b)

- **Inputs.** `_tta12` variants of the 4 non-bag TTA members in the entry's fusions. The members' own gains on realval-A / B:
  - `voxelrcnn-ros-g1v3`: pedestrian +0.0095 / +0.0112;
  - `voxelrcnn-ros-g1v4`: pedestrian +0.0067 / +0.0127;
  - `pvrcnnpp-ros-g1v4-s2`: vehicle +0.0075 / +0.0098;
  - `pointpillars-g1v5`: vehicle -0.0089 / -0.0189, as in the pilot.
- **Swap and gates.**
  - Pedestrian (`vrros_tta12` + `vrros4_tta12` @ 0.5) passed the pooled rule.
  - Vehicle and truck kept their incumbents: the swap was worse on B.
  - Budget (`--pooled`), copies and the sparse stage were re-derived. Pedestrian's floor moved 0.1 -> 0.15; copies r 0.15 and sparse k 6 are unchanged.
- **Final check against routed-g12.**
  - Pedestrian is kept: dA +0.0070, dB +0.0103, pooled +0.0074 at P 1.00, train-split frames +0.0052.
  - Vehicle and truck are frozen at the entry; their test predictions are identical to the entry's.
- **Local result.** realval-A mAP 0.7363 (+0.0023), realval-B 0.7240 (+0.0034); **projection +0.0015**.
- **Zip.** `model-v2x-track/archive/routed-g13/submissions/2026-10-30_s8v/v2x_s8v_submission.zip`, md5 `b9c82e3de0c37babf146549eeedabbf6`. Kit check valid, 128 s, 21,354 boxes (pedestrian 16,550 -> 13,620). The 50 realism frames are byte-identical to the scored `s7s` zip. Reproduction scripts: `test/reproduce_s8v.sh`, `test/reproduce_s8v_validation.sh`.

### 8.3 LUMPI U2, `routed-g11b` / `s8b`: passes bar (b)

- **Inputs.** `_tta12` variants of the 7 rule 8 checkpoints. The tuned members gain +0.001 to +0.002 mAP each on A and B against their 8-view variants (`pointpillars-g1`, `pointpillars-g1v4`, `pointpillars-ros-g1v3`), mostly Person and Truck.
- **Swap (6.0 pooled rule, Person ranked on late-A).**

  | Class | Candidate | Incumbent A / B | Candidate A / B | Decision |
  |---|---|---|---|---|
  | Person | `pp4_tta12` + `vrros4s2_tta12` @ 0.5 | 0.4652 / 0.1603 | 0.4779 / 0.1632 | **fused**: pooled +0.0087 at P 1.00 |
  | Car | `pvros_tta12` + `bagpv4x_tta` @ 0.7 | 0.9048 / 0.7983 | 0.9057 / 0.7972 | incumbent kept |
  | Truck | `pvros4d2_tta12` + `ppros_tta12` @ 0.3 | 0.4873 / 0.2056 | 0.4863 / 0.2082 | kept: pooled P 0.87 < 0.9 |
  | Van | `vrros` + `vrros4_tta12` + `g1_tta12` @ 0.5 | 0.1740 / 0.0016 | 0.1715 / 0.0017 | incumbent kept |

- **Final check against U1.**
  - Person is kept: dA +0.0129, dB +0.0029, pooled +0.0071 at P 1.00, realval-A alone +0.0129.
  - Every other class is frozen at U1; its test predictions are identical to U1's.
- **Local result.**
  - realval-A mAP 0.3909, realval-B 0.2266, late-A 0.3605;
  - **projection +0.0011 against the entry, +0.0006 against U1**.
- **Zip.** `model-lumpi-track/archive/routed-g11b/submissions/2026-10-30_s8b/lumpi_s8b_submission.zip`, md5 `c85189b48795db4647119189f7a5a2d3`. Kit check valid, 328 s, 32,038 boxes. Realism frames byte-identical to `s7s`. Reproduction scripts: `test/reproduce_s8b.sh`, `test/reproduce_s8b_validation.sh`.

### 8.4 Uploads (the entrant uploads) and F1

| Order | Track | Zip | Isolates | Projection |
|---|---|---|---|---|
| 1 | LUMPI | `s8a` (U1) | the completion alone | +0.0006 |
| 2 | LUMPI | `s8b` (U2) | the 12-view Person fusion on top of U1 | +0.0011 vs the entry |
| 3 | V2X | `s8v` | the 12-view pedestrian fusion | +0.0015 |

All three pass bar (b): projection above 0, every changed class through the final check, and the kit check under 400 s. This uses 2 of LUMPI's 5 uploads today and 1 of V2X's 5. F1 (rule 6) is the highest scored combined value per track among S7.6, U1 and U2, submitted as its exact zip. Record each result with `package_submission.py <model> --tag <tag> --record <id> <leaderboard.json>`.

What S8 showed: the 12-view set gained only for walkers (LUMPI Person, V2X pedestrian), where 8-view fusion was weakest. Car, Truck and Van stayed flat.

**Entry unchanged by the S8 code.** After all S8 changes, `model-lumpi-track/archive/routed-g10/test/reproduce_s7s.sh` rebuilt the scored `s7s` zip **IDENTICAL**: 23,270 boxes, 0 frames differing, realism frames identical, kit check 261 s. The test suite (`common/tests`, 106 tests) passes.

### 8.5 Leaderboard results (release 8.0)

The entrant uploaded `s8v` and `s8b` unchanged; `s8a` (U1) was not uploaded, because `s8b` contains it. Both scored zips are byte for byte the packaged files (md5 in each `manifest.json`).

| Track | Version | CodaBench id | Uploaded (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank (2026-10-30 20:09 UTC) | Change against S7.6 |
|---|---|---|---|---|---|---|---|---|
| LUMPI | `routed-g11b` / `s8b` | [1022250](../../model-lumpi-track/archive/routed-g11b/submissions/2026-10-30_s8b/codabench_1022250.json) | 19:57 | **0.523901** | 0.1762 | 0.9323 | **1 of 22** (Raj Patil 0.5118, 1021347) | +0.00106: Person 0.1802 -> 0.1865 (+0.0063), Truck 0.0632 -> 0.0653 (+0.0021), Motorcycle +0.0003; Car, Bicycle, Bus, Van and realism identical |
| V2X | `routed-g13` / `s8v` | [1022246](../../model-v2x-track/archive/routed-g13/submissions/2026-10-30_s8v/codabench_1022246.json) | 19:52 | **0.902153** | 0.6170 | 0.9332 | **1 of 25** (Raj Patil 0.8112, 1016446) | +0.00398: pedestrian 0.4288 -> 0.4428 (+0.0139); vehicle, truck and realism identical |

**Reading.**
- **Every change transferred with the sign the local checks gave.** LUMPI projected +0.0011 and scored +0.00106. V2X projected +0.0015 and scored +0.0040: pedestrian gained +0.0139 on the test frames against +0.0103 on realval-B and +0.0070 on realval-A.
- **The non-negative completion did what the proof says.** The lowered floors added Truck +0.0021 and Motorcycle +0.0003 on the test frames, where realval had measured 0 and +0.0015. No class lost.
- The Person gain (+0.0063) mixes the copies and the 12-view fusion; `s8a` would have separated them, and it stays local.
- **F1 (rule 6): `lumpi_s8b_submission.zip` and `v2x_s8v_submission.zip`** at release 8.0. LUMPI F1 became `lumpi_s8c_submission.zip` once S8.2 scored higher (Section 9.1). The S7.6 zips are the fallback.
- **Budget used:** LUMPI 9 of 100, V2X 12 of 100.

## 9. S8.2: the dropped 12-view scope (pre-registered 2026-10-30, 13:15 CDT, before any S8.2 result)

The entrant asked, at 12:50 CDT, for the 12-view approach in the scope rule 8 had dropped. TTA needs no training, so this means running it on the dropped members.

**Why the bags.** The route tables rank the 8-view seed bags first for the walker classes: LUMPI Person `bagvr4x_tta` (joint 0.290), V2X pedestrian `bagvr5_tta` and `bagvr5x_tta` (0.388). S8 showed that the 12-view set gains for walkers. Rule 8 left every bag at 8 views.

1. **Members.** `_tta12` variants (tuned on A from the neutral start, reported on B, as rule 3) of every seed of the four extended bags not yet run:
   - LUMPI: `voxelrcnn-ros-g1v4-s3/-s4/d2/d3` and `pvrcnnpp-ros-g1v4/-s2/-s3/-s4/d3` (9 checkpoints).
   - V2X: `voxelrcnn-ros-g1v5/-s2/-s3/d2/d3` and `pvrcnnpp-ros-g1v5/-s2/-s3/d2/d3` (10).
   - The bags `bagvr4`, `bagvr4x`, `bagpv4`, `bagpv4x` (LUMPI) and `bagvr5`, `bagvr5x`, `bagpv5`, `bagpv5x` (V2X) get `_tta12` variants: their seeds' `_tta12` predictions fused exactly as the 8-view bags (same seeds, same IoU, no knob). Every new seed and bag becomes a member.
2. **Ranking.** New members enter `route_table.json` with joint = the mean of their realval-A and realval-B AP, without calibration. The incumbent fusions carry no calibration.
3. **Portfolio: rule 4 in full, from the latest built version.**
   - `fuse --max-members 3 --pooled-rule`: pairs and triples of the top 4 members per class by joint, at IoU 0.3, 0.5 and 0.7, with no checkpoint used twice.
   - LUMPI: Person, Car, Truck and Van only; Person ranked on late-A with the top 3 through the gates; U1's floors and copies (t = 0.274) kept; Bicycle, Motorcycle and Bus frozen.
   - V2X: every class; budget `--pooled`, copies and the sparse stage re-derived, as in `s8v`.
4. **Final check** (`s7_check.py check`, the rule 4 conditions; LUMPI Van by its judge) against the latest built version of the track. LUMPI is checked against `routed-g11b` (`s8b`), V2X against `routed-g13` (`s8v`). A failing class keeps that version's configuration.
5. **Versions and bar.** LUMPI `routed-g11c` / `s8c`, V2X `model-v2x-track/archive/routed-g14` / `s8w`. Each is uploaded only under bar (b), against the version it was checked against, with the kit check under 400 s. A version that changes no class is not built.
6. **Cut-off.** Packaged by 18:00 CDT (23:00 UTC), or not offered: the phase closes at 19:00 CDT and LUMPI scoring takes 6-8 min.
7. **Not in S8.2.** The 20-view set (flip, rotation and scale views together), because the GPU time goes to the bags. Also Bicycle, Motorcycle and Bus, and anything chosen from leaderboard numbers.
8. **Probed and dropped (CPU, before any S8.2 result): the U1 completion on V2X.** `s8v`'s kit check leaves 270 s of headroom, so the probe tested the completion on `s8v`'s validation predictions:

   | Variant | Pedestrian A / B / pooled | Boxes per frame |
   |---|---|---|
   | floors at 0.01 | -0.0029 / -0.0048 / -0.0035 | 400 -> 959 |
   | 8 copies instead of 4 | -0.0030 / -0.0037 / -0.0046 | 599 |
   | both | -0.0043 / -0.0062 / -0.0051 | 1,515 |

   Vehicle and truck are unchanged. The completion loses on V2X because of the S7 sparse stage, which ranks low-point boxes below every other box: new low-score boxes then outrank the demoted true positives. The proof that a box scored below every other box cannot lower AP assumes nothing sits under it. LUMPI has no sparse stage, so U1's argument holds there.

### 9.1 S8.2 results (2026-10-30, 16:35 CDT)

- **12-view bags (realval-A / B).** LUMPI `bagpv4x_tta12` 0.3633 / 0.2010, `bagvr4x_tta12` 0.3606 / 0.2006. V2X `bagvr5x_tta12` 0.7131 / 0.7044, `bagpv5x_tta12` 0.7082 / 0.6988. Every bag seed gained at 12 views on A (LUMPI +0.005 to +0.008 mAP, Person +0.013 to +0.020).
- **LUMPI `routed-g11c` / `s8c`: built.**
  - Fuse (pairs and triples of the top 4 per class):
    - Person, Truck and Van keep their `s8b` fusions; the `s8b` Person fusion still ranks first on late-A.
    - Car moves to `pvros_tta12` + `bagpv4x_tta12` @ 0.7 (pooled +0.0007 at P 0.925).
  - Final check against `s8b`: Car is kept (dA +0.0018, dB -0.0010, train split +0.0018).
  - Local A 0.3911, B 0.2265; **projection against `s8b` +0.00003**, above 0, so `s8c` passes bar (b) by its letter.
  - Kit check valid: 319 s, 31,048 boxes. Only Car differs from `s8b` (12,748 -> 11,758 boxes), and the realism frames are byte-identical.
  - Zip `model-lumpi-track/archive/routed-g11c/submissions/2026-10-30_s8c/lumpi_s8c_submission.zip`, md5 `ead9da5ec4eb683e526efe4b72483dfc`.
  - **Reading:** a near-zero local change in the class whose local gains did not transfer in S7.6 (Car +0.006 on both splits, -0.004 on the leaderboard). The expected leaderboard change is within noise either way.
- **Leaderboard: `s8c` uploaded by the entrant, 1022399 (2026-10-30 21:37 UTC): 0.525439**, rank 1 of 22 (Raj Patil 0.5118).
  - Against `s8b` (1022250): +0.00154. Car 0.6482 -> 0.6608 (+0.0126); every other class and the realism are identical.
  - **The Car change transferred far above its local evidence**: +0.0018 on A, -0.0010 on B, +0.0126 on the test frames. In S7.6 a LUMPI Car change went the other way (+0.006 on both splits, -0.004 on the leaderboard). On LUMPI Car the local splits do not predict the test sign; the pooled rule and the final check bound the downside, not the size.
  - **LUMPI F1 is now `lumpi_s8c_submission.zip`** (rule 6), with `s8b` and then `s7s` as fallbacks. Budget used: LUMPI 10 of 100.
- **V2X `routed-g14`: not built.** Every candidate lost to its incumbent, and the re-derived floors, copies and sparse stage equal `s8v`'s, so every class is frozen at `s8v`.

## 10. S8.3: the completion up to the kit budget (pre-registered 2026-10-30, 17:12 CDT, before any S8.3 result)

The entrant asked at 17:00 CDT for a last rule-aligned increment that fits the remaining 1 h 50 min.

**Why this lever.** On realval-B the largest residual error is localization for the walker classes: LUMPI Person 0.260, V2X pedestrian 0.273. It is also large for LUMPI Truck (0.094) and Bus (0.098). Tail copies target localization, and a copy scored below every box of its class cannot lower AP on any frame set (`apply_tail_copies`). Kit time limits them: LUMPI `s8c` takes 319 s, V2X `s8v` 128 s, against the 400 s rule. No GPU is needed: the merge runs on the members' saved predictions.

1. **LUMPI `routed-g11d` / `s8d`, from `s8c`.**
   - (a) Person copies on more boxes: t from 0.274 (q0.8) down to the lowest realval-A quantile in {0.7, 0.6, 0.5} whose kit check stays at or under 390 s.
   - (b) Copies (4) for Truck and Bus, each with the radius in {0.2, 0.5, 1.0} m that is best on realval-A. A class is kept only if realval-B and the pooled frames gain, as R5's `tail_select`. Bus is frozen, but rule 2 exempts changes that cannot lower AP.
   - Nothing else changes.
2. **V2X `routed-g13x` / `s8x`, from `s8v`.**
   - Copies applied **after** the sparse stage (`final_copies`), scored below every box of the class including the demoted ones, so the argument holds again.
   - Pedestrian: a second ring, radius in {0.3, 0.45} m, for boxes scored at or above the realval-A median of its final pedestrian scores.
   - Vehicle and truck: copies with radius in {0.2, 0.5, 1.0} m.
   - Each class is kept as in 1(b), with the kit check under 390 s.
3. **Bar (b)** against `s8c` / `s8v`: projection above 0. Every change cannot lower AP, so no per-class final check beyond the gains above.
4. **Cut-off.** Packaged by 18:20 CDT (23:20 UTC), or not offered.

### 10.1 S8.3 probe (realval, against `s8c` / `s8v`) and the choice

| Track | Variant | Class | A | B | Pooled (P) | Test boxes | Rule outcome |
|---|---|---|---|---|---|---|---|
| LUMPI | Person t q0.7 (0.1513) | Person | +0.0000 | +0.0011 | +0.0014 (0.99) | 33,116 | candidate |
| LUMPI | Person t q0.6 (0.0841) | Person | +0.0014 | +0.0020 | +0.0014 (1.00) | 35,440 | candidate if the kit check fits |
| LUMPI | Person t q0.5 (0.0508) | Person | +0.0014 | +0.0020 | +0.0024 (1.00) | 37,292 | over the kit budget (U1 measured 437 s) |
| LUMPI | Truck r 0.2 (best on A) | Truck | +0.0009 | +0.0012 | +0.0012 (0.79) | 35,228 | **dropped** (pooled P < 0.9) |
| LUMPI | Bus r 1.0 (best on A) | Bus | +0.0006 | +0.0015 | +0.0010 (1.00) | 33,004 | **kept** |
| V2X | pedestrian ring r 0.3 (best on A) | pedestrian | +0.0009 | +0.0007 | +0.0005 (0.89) | 49,122 | **dropped** (pooled P < 0.9) |
| V2X | vehicle r 0.2 / 0.5 / 1.0 | vehicle | 0 / +0.0005 / 0 | 0 | 0 | 47,542 | dropped |
| V2X | truck r 0.2 / 0.5 / 1.0 | truck | 0 | 0 | 0 | 26,102 | dropped |

- **V2X:** no class passes, so `s8x` is not built and `s8v` stays.
- **LUMPI:** `s8d` = `s8c` + Bus copies (r 1.0) + Person copies at q0.7 or q0.6, whichever is the lowest quantile with a kit check at or under 390 s. Both were timed in parallel (q0.7 + Bus 35,072 boxes, q0.6 + Bus 37,396). The build started with q0.7, the interpolated fit (about 360 s against about 400 s for q0.6).

### 10.2 LUMPI `routed-g11d` / `s8d`: built, passes bar (b)

- **Kit timings** (two in parallel): q0.7 + Bus 351 s (35,072 boxes), q0.6 + Bus 387 s (37,396 boxes). Both fit the 390 s bound, so rule 1(a) takes **q0.6** (t = 0.0841). The q0.7 build, started before the timings were in, was stopped and rebuilt.
- **`s8d` = `s8c` with Person copies at t = 0.0841 and Bus copies (r 1.0 m, 4 copies).** Every other class is identical to `s8c`, every `s8c` box is kept, and the realism frames and declaration are byte-identical. The test predictions are `s8c`'s verified member predictions, merged again (no inference).
- **Local:**
  - realval-A 0.3914 (+0.0003), realval-B 0.2270 (+0.0005);
  - Person +0.0015 / +0.0020, Bus +0.0006 / +0.0015;
  - **projection +0.0002** against `s8c`.
- **Kit check** valid: 361 s, 37,396 boxes.
- **Zip:** `model-lumpi-track/archive/routed-g11d/submissions/2026-10-30_s8d/lumpi_s8d_submission.zip`, md5 `d5bd41769788c902b6e49095236aafd6`.

### 10.3 Leaderboard: `s8d` (the LUMPI entry and F1)

- **Upload.** `s8d` uploaded by the entrant as 1022492 (2026-10-30 23:09 UTC): **0.525688**, rank 1 of 22 (Raj Patil 0.5118).
- **Against `s8c` (1022399): +0.00025, as projected (+0.0002).**
  - Person 0.1865 -> 0.1876 (+0.0011), Bus 0.0028 -> 0.0037 (+0.0010).
  - Every other class and the realism are identical, as the construction says.
- **Against S7.6 (1014495), the whole S8 line on LUMPI: +0.0028.**
  - Person +0.0073, Car +0.0126, Truck +0.0021, Bus +0.0010, Motorcycle +0.0003; nothing lost.
- **The completion transferred in full each time it was uploaded:** the floors in `s8b`, the copies in `s8b` and `s8d`. It is the one lever of the last day whose test-frame gain was never negative and always close to its local size.
- **F1 (rule 6): `lumpi_s8d_submission.zip` and `v2x_s8v_submission.zip`**; LUMPI fallbacks `s8c`, then `s8b`.
- **Budget used:** LUMPI 11 of 100, V2X 12 of 100.
