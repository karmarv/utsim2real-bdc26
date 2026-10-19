# 2026-10-18 S7 Visibility Rule (V2X): pre-registration, results and decision

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

**Results, step 2.** To be filled after the six runs (`$BDC_DATA/logs/s7`, `common/pipeline/s7_portfolio.sh`: bags, comparison with the `g1-v5` bags, `routed-g10`, gates, package).

**Decision, step 1.** `routed-g9` is decision-ready and passes every pre-registered rule. Upload `v2x_s7_submission.zip` unchanged to CodaBench 16685. It is one change set: two classes are re-ranked, and nothing else changes. Projection 0.893 + 0.004 = about **0.897**. LUMPI is unchanged (rule 1).

**Outcome.** Pending upload (the entrant's step). Record afterwards with `python common/tools/package_submission.py model-v2x-track/routed-g9 --tag s7 --record <id> <leaderboard.json>`.

**Reproduce (step 1).**
- Members: those of `routed-g8b` (record [`2026-10-16-s6-variance-controlled.md`](2026-10-16-s6-variance-controlled.md), weights in release 6.0).
- Model card: `model-v2x-track/routed-g9/model.yaml` (adds `sparse_demotion`).
- Script: `CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g9/test/reproduce_s7.sh` on an idle GPU.
- The stage counts points of the kit test frames themselves, at inference only, as re-centering already does.
