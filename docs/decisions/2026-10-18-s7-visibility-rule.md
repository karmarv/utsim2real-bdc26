# 2026-10-18 S7 Visibility Rule (V2X): step 1 uploaded and confirmed (V2X 1001919 0.8982, pedestrian +0.015), rank 1; step 2 below the upload gate; 2026-10-26 review: conventions saturated

**Version.** Strategy S7, V2X only, two change sets on top of the S6 entry (`model-v2x-track/routed-g8b`, 995877, 0.8931):
- **Step 1, `routed-g9`:** `routed-g8b` plus a per-class **sparse-box demotion** stage on the final predictions (no training).
- **Step 2, `routed-g10`:** members retrained on the same frames with **visibility-matched labels** (corpus `pcdet/g1-v5m`), as seed bags, through the pooled rule on top of step 1.

Plan and results: [`02-STRATEGY.md` Section 8.11](../02-STRATEGY.md#811-s7-visibility-rule-v2x-2026-10-18). Runs: `$BDC_DATA/logs/s7` (`common/pipeline/`, detached; `STATUS.md`, `events.txt`). The rules basis for the external-data question that started this review is [`2026-10-18-rules-external-datasets.md`](2026-10-18-rules-external-datasets.md).

**Context.** V2X pedestrian (953 test GT, 62% of the test objects) is the largest open class (leaderboard AP 0.413), and static and sparse false positives are its main error (Sections 8.2.1, 8.7.2). The V2X-Real annotators do not label objects that the sensor sees with only a few points. Our synthetic labels keep every object with at least one point (`min_points: 1` in `prepare_g1.py`), so the detector is trained to fire on sparse blobs the test labels never contain.

**Evidence** (legal labels only; points per box counted per box, (0,0,0) nulls excluded, `bdc26.boxes.count_points_per_box`; realval frames have the test format: 50,000 points, 31% nulls):

| Class | Real realval-A: p1 / p2 / p5 points, share < 6 | Real realval-B | Synthetic `g1-v5` (train, every 9th frame): share < 6 (beyond 30 m) |
|---|---|---|---|
| pedestrian | 5 / 6 / 6, 1.7% | 5 / 6 / 6, 1.6% | **16.3% (38.4%)** |
| vehicle | 7 / 8 / 10, 0.3% | 7 / 8 / 10, 0.3% | 2.3% (2.4%) |
| truck | 30 / 32 / 51, 0% | 15 / 18 / 31, 0% | 1.4% (3.6%) |

Exploratory probe of the review (2026-10-18, before this record; final `routed-g8b` predictions, every box of a class with fewer than k points re-scored x 1e-3): pedestrian A 0.3805 -> 0.3825 / 0.3848 / 0.3884 / 0.3942 / **0.3985** / 0.3768 / 0.3533 and B 0.4179 -> 0.4201 / 0.4229 / 0.4283 / 0.4347 / **0.4413** / 0.4205 / 0.3848 for k = 2 ... 8; vehicle +0.002 (A) / +0.004 (B) at k = 5-6; truck unchanged. **Disclosure:** the k grid was therefore seen on both splits before the rules below were fixed, so realval-B is not an independent check of k; the leaderboard confirmation is. On LUMPI (`routed-g8`) the same probe gave Person +0.000 to +0.002 and Car -0.004 to -0.014 (LUMPI keeps boxes with no points: 0.5-1.8% of the Person and Car labels of realval-A and B), so the premise does not hold there.

**Pre-registered rules** (written before step 1's gate ran and before any step 2 checkpoint existed):
1. **Scope:** V2X only. LUMPI keeps the S6 entry; no LUMPI class is changed by S7.
2. **Demotion stage** (`route_predictions.py sparse`, model.yaml `sparse_demotion: {class: k}`), applied last in `merge_card` (after score floors and tail copies): a box of class c with fewer than k_c points inside it is re-scored s x g_c, with g_c = 0.99 x (smallest score of the class in the prediction set) / (largest), so it ranks below every other box of its class; nothing is deleted. The same code runs on validation, test frames and reproduction.
3. **Selection:** grid k in {2, ..., 8}; per class the k with the best realval-A AP (ties: the smaller k). Kept only if, on the final predictions against the incumbent: the pooled A+B gain with paired bootstrap P(gain) >= 0.9; neither split down by more than 0.005 (the 6.0 pooled rule); and **robustness:** k - 1 also gains on the pooled frames, so a lone spike next to a cliff is rejected.
4. **Training labels (step 2):** per class, synthetic labels with fewer points than floor(min over realval-A and B of the 2nd percentile) are removed: pedestrian 6, vehicle 8, truck 17 (`common/tools/filter_labels.py`; removed 26,059 / 2,043 / 1,020 of 157,647 / 57,389 / 24,301). Frames and points identical to `g1-v5`.
5. **Members (step 2):** `voxelrcnn-ros-g1v5m` and `pvrcnnpp-ros-g1v5m`, seeds 666 / 1666 / 2666, the configs of their `g1-v5` parents; post-processing (score blend, plain and TTA tuning) as in S6; bags `bag-voxelrcnn-ros-g1v5m`, `bag-pvrcnnpp-ros-g1v5m`. First read as bags against the `g1-v5` bags of the same seeds (paired, per class); then added as candidates to `routed-g10` (copy of `routed-g9`), `select --rule joint --calibrated --pooled`, `fuse --max-members 3 --pooled`, budget, tail, the rule 3 selection, final pooled check against `routed-g9`.
6. **Upload gate (6.0):** projected gain at least +0.003 combined (0.6 x the mean of the A and B mAP gains x 0.6 / 0.7), kit scorer valid in under 400 s; one change set per upload (step 1 first, step 2 only after step 1 is confirmed or rejected).
7. **Unchanged:** the 50 realism frames (the `g1-v5` frames of the S6 entry); no class or knob chosen from leaderboard numbers; feature freeze Sun Oct 25 (step 2 is dropped if it is not through its gate by then).

**Results, step 1** (2026-10-18, `route_predictions.py sparse model-v2x-track/routed-g9`, 12 min CPU; `validation/results/sparse_table.json`). Final predictions, official 3D AP@0.5 R40, realval-A / realval-B, and the pooled A+B delta against `routed-g8b`:

| k | pedestrian | pooled | vehicle | pooled |
|---|---|---|---|---|
| none (`routed-g8b`) | 0.3805 / 0.4179 | | 0.8654 / 0.8693 | |
| 4 | 0.3884 / 0.4283 | +0.0087 | 0.8675 / 0.8717 | +0.0020 |
| 5 | 0.3942 / 0.4347 | +0.0144 | **0.8678** / 0.8723 | **+0.0022** |
| 6 | **0.3985 / 0.4413** | **+0.0197** | 0.8676 / 0.8733 | +0.0026 |
| 7 | 0.3768 / 0.4205 | -0.0022 | 0.8659 / 0.8727 | +0.0013 |
| 8 | 0.3533 / 0.3848 | -0.0283 | 0.8642 / 0.8698 | -0.0006 |

- Selected by realval-A: **pedestrian k = 6** (P 1.00; k = 5 also gains, +0.0144), **vehicle k = 5** (P 1.00; k = 4 +0.0020). Truck does not move at any k (real trucks have 15 or more points), so it is not kept.
- `routed-g9`: A **0.7272 -> 0.7340**, B **0.7118 -> 0.7206** (paired bootstrap mAP dB +0.0088, P 1.00); 3D@0.7 on B unchanged (0.221).
- Pedestrian on B, the mechanism: unmatched boxes at score >= 0.5 fall from 8.0 to 5.1 per frame (static ones from 4.0 to 2.9). The ranking loss falls from 0.288 to 0.250, and recall at IoU 0.5 is unchanged (0.823), because nothing is deleted.
- The ranking is the same as the probe's x 1e-3: the probe's numbers are reproduced exactly.

**Gate, step 1** (6.0 rules). The pooled check on the final predictions (`pooled_check.py`) passes for vehicle (+0.0022) and pedestrian (+0.0197), both P 1.00. Neither split drops. Projection 0.6 x mean(+0.0068, +0.0088) = +0.0047 mAP, so **+0.0040 combined against the bar +0.003: upload gate passed**. Realism is identical: the 50 frames of the S6 entry, local R 0.937 as packaged, and the kit realism 0.935395 is bit-equal to 995877's. Kit scorer: valid, 141 s, 24,284 boxes.

**Package, step 1.** `model-v2x-track/routed-g9/submissions/2026-10-18_s7/v2x_s7_submission.zip` (md5 `c1483d590242d4fe6b4eefff96c1619c`). It was merged from the saved kit predictions of the six `routed-g8b` members, the exact predictions behind 995877. Against `v2x_s6b_submission.zip`:
- every box and every frame is identical, and only scores change;
- only `predictions.json` and the declaration date differ.

The re-merge check is identical, and `test/reproduce_s7.sh` re-predicts the members from the release-6.0 weights.

**Results, step 2** (2026-10-19, unattended in `$BDC_DATA/logs/s7`, `common/pipeline/s7_portfolio.sh`; six runs, no failure).
- **Bags on the visibility labels against the `g1-v5` bags of the same seeds** (pooled A+B, member level, before the S7 stage):
  - pedestrian +0.0014 to +0.0083 (plain P 0.98-1.00, TTA P 0.69-0.79);
  - vehicle +0.0078 for PV-RCNN++ and -0.0091 to -0.0130 for Voxel R-CNN;
  - truck -0.0197 to +0.0044.
  - Removing the sparse labels in training buys far less than ranking sparse boxes last at inference (+0.0197).
- **`routed-g10`** (`routed-g9` + both bags; select, fuse with `--pooled-rule`, budget, tail, sparse, final pooled check):
  - pedestrian fused with `bagvr5_tta` + `bagvr5m` + `bagpv5_tta` (A +0.0104, B -0.0030, pooled +0.0064, P 0.99);
  - truck `bagpv5m_tta` + `pp5_tta` + `bagvr5m_tta` (A +0.0007, B +0.0081, pooled +0.0042, P 0.91);
  - vehicle frozen at `routed-g9`;
  - A 0.7340 -> 0.7377, B 0.7206 -> 0.7223. Kit check valid (164 s, 29,117 boxes).
- **Projection +0.0014 against the bar +0.003: not met; not uploaded.** On train-split frames only (audit 2026-10-26, rule a): pedestrian +0.0136 (A) / +0.0024 (B), truck -0.0045 / +0.0153. The truck change would fail rule a as well. Package `routed-g10/submissions/2026-10-19_s7m/` kept for the record only.

**Review of 2026-10-26: what else the visibility-and-convention idea can still buy.** Read-only probes on the final validation predictions of the entries, official 3D AP@0.5. Scripts `probe_geom.py`, `probe_height.py`, `probe_envelope.py` (session scratchpad; numbers here).

| Probe | Idea | V2X (`routed-g9`) | LUMPI (`routed-g8`) | Verdict |
|---|---|---|---|---|
| Range-dependent box extents | correct bottom, top, length and width by the realval-A median residual of matched pairs per 10 m (linear in range) | pedestrian z-only pooled +0.0020 (P 0.95); length, width and all-axes variants -0.0014 to -0.0032; vehicle and truck all -0.0004 to -0.0032 | not run (V2X shows no systematic residual) | **saturated**: the BEV-3D gap (pedestrian 0.13 on A, 0.12 on B) is random z error (IQR 0.12 m centre, 0.17 m height), not a bias |
| Heights read off the points | top = 98th percentile of in-box z + A-median offset; bottom = ring-ground 10th percentile + offset | pedestrian pooled -0.021 (top), -0.021 (bottom), -0.040 (both): point extents are noisier (IQR 0.22 / 0.18 m) than the detector's | not run | **rejected** |
| Labels end at a range | predictions beyond the real labels' 99.5th-percentile range | 0.2-1.8% of the top-half boxes | 1-5% (Bicycle 5%, a frozen class) | **negligible** |
| Range-conditional visibility envelope | per class and 5 m bin, rank last boxes below the lower or above the upper percentile of real points per box | every variant loses (pedestrian -0.0002 to -0.0103 pooled; vehicle and truck worse): the flat k already holds the cut | Person lower p5 +0.0048 (P 1.00), Truck lower p2 +0.0027 (P 1.00), Car -0.0011 to -0.0226, Van -0.0012 to +0.0006 | **below the bar**: LUMPI Person + Truck projects about +0.0006 combined |
| Taxonomy | V2X "truck" includes `TrashCan` | `TrashCan` labels are 8.2 x 2.9 x 2.6 m refuse trucks (959 of the truck boxes in realval), not bins, so the unlabeled bins of the G2-lite clutter do not conflict | | **no change** |

**Reading.** On V2X the S7 rule took the one systematic labelling difference left; the other conventions are matched, and what remains is random localization error and ranking, which only better members reduce. On LUMPI the same probes buy at most +0.0006 combined.

**Revisions under S7** (from 2026-10-26; every gate also on train-split frames, audit rule a):

| Revision | What | Cost | Expected | Status |
|---|---|---|---|---|
| S7.1 compliance | close the audit's items 1-3: LOI, the disclosure email, train-split robustness reported with every gate | the entrant's emails; CPU | keeps both entries safe through the verification of top teams | items 1-2 are the entrant's, before Oct 30 20:00 EDT; item 3 done for the live S7 change |
| S7.2 dry run | rebuild both entries from their weights on idle GPUs and compare with the scored zips | 2 GPU-hours | proves F1 | **done 2026-10-26: IDENTICAL on both** (V2X `reproduce_s7.sh`, LUMPI `reproduce_s6.sh`: predictions and all 50 frames equal to the scored zips; kit checks valid, 315 s and 299 s with both jobs running at once; `$BDC_DATA/logs/s7repro`) |
| S7.3 LUMPI envelope | Person lower p5, Truck lower p2 | CPU | +0.0006 projected | **not adopted** (bar +0.003) |
| S7.4 V2X generator-draw bags | the two two-stage configs trained on two fresh draws of the `g1-v5` generator (raw labels), bagged with the existing seeds, fuse with `--pooled-rule` against `routed-g9` | about 12 h on 8 GPUs, CPU portfolio | +0.002 to +0.005 (seed bags gave vehicle and truck +0.014 each through fusion in S6); uncertain | **needs the entrant's go**: it would run after the Oct 25 freeze, so it must be confirmed in the development phase (by Oct 30) or enter the final phase only as an F2-F5 candidate under `Force_Best` |

**Decision, step 1.** `routed-g9` is decision-ready and passes every pre-registered rule. Upload `v2x_s7_submission.zip` unchanged to CodaBench 16685. It is one change set: two classes are re-ranked, and nothing else changes. Projection 0.893 + 0.004 = about **0.897**. LUMPI is unchanged (rule 1).

**Outcome, step 1** (uploaded unchanged by the entrant; scored 2026-10-19 02:52 UTC; public leaderboard API; server record [`codabench_1001919.json`](../../model-v2x-track/routed-g9/submissions/2026-10-18_s7/codabench_1001919.json), manifest via `--record`):

| | V2X 1001919 (S7 step 1) | Previous entry 995877 (S6 variant b) | Change |
|---|---|---|---|
| Combined | **0.8982** | 0.8931 | **+0.0051** |
| 3D mAP@0.5 R40 | 0.6124 | 0.6065 | +0.0059 |
| pedestrian | **0.4288** | 0.4134 | **+0.0154** |
| vehicle | 0.7372 | 0.7349 | +0.0023 |
| truck | 0.6710 | 0.6710 | identical (not changed) |
| Realism R (CD, MMD, EMD, FPD) | 0.9332 (1.986, 0.00063, 1.182, 1.468) | the same | identical (same 50 frames) |
| BEV mAP@0.5 / 3D mAP@0.7 | 0.6662 / 0.1649 | 0.6583 / 0.1645 | +0.008 / +0.000 |
| Rank | **1 of 23** (Raj Patil 0.7555, unchanged since Oct 15) | 1 of 23 | |

**Confirmation passed** (+0.0051).

**Transfer.**
- **Per class.** Pedestrian +0.0154 on the leaderboard against +0.0180 on realval-A (0.85 x) and +0.0233 on realval-B (0.66 x). Vehicle +0.0023 against +0.0024 (0.98 x) and +0.0029 (0.79 x).
- **mAP.** +0.0059 against A +0.0068 and B +0.0088: 0.76 x the mean, near the 0.6 x of the projection rule.
- **Combined.** The leaderboard gain was 1.27 x the projection (+0.0040) and 0.68 x the B-based estimate (+0.0075).
- **Signs.** The pooled condition on the final predictions had both class signs right.
- **The sharp cut transferred.** The k chosen on realval-A at the test format (50,000 points, 31% nulls) is the k the test labels reward. As the disclosure required, the leaderboard was the independent check of k.
- **Comparison.** This is the largest V2X pedestrian gain since S5 (+0.046), above R3 (+0.012) and R5 (+0.011), from a CPU-only stage.

**Consequences.**
1. V2X 1001919 is the entry. `v2x_s7_submission.zip` becomes the V2X candidate for F1 of the final phase. Release 6.0 weights rebuild it; `test/reproduce_s7.sh` reproduced it IDENTICAL on 2026-10-26.
2. Step 2 is judged against `routed-g9` (`common/pipeline/s7_portfolio.sh`).
3. Budget used: V2X 10 of 100.

**Reproduce (step 1).**
- Members: those of `routed-g8b` (record [`2026-10-16-s6-variance-controlled.md`](2026-10-16-s6-variance-controlled.md), weights in release 6.0).
- Model card: `model-v2x-track/routed-g9/model.yaml` (adds `sparse_demotion`).
- Script: `CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g9/test/reproduce_s7.sh` on an idle GPU.
- The stage counts points of the kit test frames themselves, at inference only, as re-centering already does.
