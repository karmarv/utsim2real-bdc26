# 2026-10-26 S7 final revisions (S7.4 V2X, S7.5 LUMPI): generator-draw bags, pre-registration, results and submission-ready versions

**Decision to extend the freeze** (the entrant, 2026-10-26). Gate E (Oct 25) is extended for these two revisions only, so that each track gets an optimized, submission-ready version before the development phase closes (Fri Oct 30, 17:00 PDT).
- Nothing else is added.
- A revision that does not pass every rule below leaves its track's current entry as the submission-ready version. That entry is the exact scored zip: V2X 1001919 `v2x_s7_submission.zip`, LUMPI 995869 `lumpi_s6_submission.zip`.

**Why this lever.** The 2026-10-26 review ([`2026-10-18-s7-visibility-rule.md`](2026-10-18-s7-visibility-rule.md)) found post-processing conventions saturated on both tracks. The one lever with leaderboard evidence left is variance reduction through fusion:
- S6 seed bags fused with other architectures gave V2X vehicle and truck +0.014 each on the leaderboard;
- every bag was at or above its best seed.

Seeds vary only the initialization. A member trained on a fresh draw of the same generator also sees different walkers, clutter, insertions and resampling. This is the same recipe and the same frames, so it is decorrelated noise, not new content.

**Pre-registered rules** (written before any new corpus or run existed):
1. **Draws.** Two fresh draws per track with the corpus recipe of the current members and only the generator seed changed (`prepare_g1.py --seed`; the default 1234 reproduces the existing corpora):
   - V2X `pcdet/g1-v5d2` and `g1-v5d3` (seeds 2234 and 3234), recipe of `g1-v5`;
   - LUMPI `pcdet/g1-v4d2` and `g1-v4d3` (seeds 2234 and 3234), recipe of `g1-v4`.
   - Labels are raw (`min_points: 1`), as in the parent corpora.
2. **Runs.** The two-stage configs of the current bags, copied unchanged from their seed runs, with training seed 4666 on draw 2 and 5666 on draw 3:
   - V2X `voxelrcnn-ros-g1v5d2/-d3` and `pvrcnnpp-ros-g1v5d2/-d3` (from `*-g1v5-s2`);
   - LUMPI `voxelrcnn-ros-g1v4d2/-d3` (from the size-capped `voxelrcnn-ros-g1v4-s2`) and `pvrcnnpp-ros-g1v4d2/-d3` (from `pvrcnnpp-ros-g1v4-s2`).
   - Eight runs, 40 epochs, epoch-40 checkpoints. Post-processing as in S6 (score blend, plain and TTA tuning).
3. **Bags.** One extended bag per family: the existing seeds plus both draws.
   - V2X `bag-voxelrcnn-ros-g1v5x` and `bag-pvrcnnpp-ros-g1v5x`: 5 members each.
   - LUMPI `bag-voxelrcnn-ros-g1v4x` (5) and `bag-pvrcnnpp-ros-g1v4x` (6).
   - The fusion IoU of the existing bags. A bag is never fused with one of its own members.
4. **Portfolios.**
   - V2X `routed-g11` = `routed-g9` + the four draw runs and the two extended bags (plain and TTA).
   - LUMPI `routed-g9` = `routed-g8` + the same.
   - Tail copies and the sparse stage are removed and re-derived. Then select (joint, calibrated, pooled), fuse (up to 3 members, the 6.0 pooled rule), budget, and tail and sparse for V2X.
   - LUMPI as in S6: the late-A Person rule, the Van judge, and Bicycle, Motorcycle and Bus frozen at the entry.
5. **Final check against the entry, per class**, on the final predictions:
   - the pooled A+B gain with paired bootstrap P(gain) >= 0.9, and neither split down by more than 0.005;
   - **audit rule a:** no loss on train-split frames alone. For V2X that is the V2X-Real train split of A and B, pooled. For LUMPI it is realval-A (Measurement4 0-6399).
   - LUMPI Van by its judge (late-A gain at least 0.01, P >= 0.9).
   - A failing class is frozen at the entry.
6. **Upload gate (6.0).** Projected gain at least +0.003 combined (0.6 x the mean of the A and B mAP gains x 0.6 / 0.7; LUMPI Van from realval-A), and a valid kit check in under 400 s. Realism frames are unchanged (the entries' frames).
7. **Audit rules a-e** ([`2026-10-26-rules-compliance-audit.md`](2026-10-26-rules-compliance-audit.md)): no model fitted on real labels, no statistic of the test frames or the public test GT, no leaderboard-informed change.

**Schedule.**
- Oct 26 evening: generation and launch.
- Oct 27 about 06:00: training done. Morning: post-processing.
- Oct 27 afternoon: both portfolios, gates and packages (unattended, `common/pipeline/s7f_portfolio.sh`).
- Upload and confirmation: the entrant's, by Oct 30.

**Launch** (2026-10-26).
- 15:27-15:45: corpora `g1-v5d2/d3` and `g1-v4d2/d3` (`prepare_g1.py --seed`; V2X frame 100 has 29 boxes against 24 in `g1-v5`, 6 shared).
- 15:34: eight runs queued on two 4-GPU workers, two post workers, `portfolio_v2x` and `portfolio_lumpi` waiting (`$BDC_DATA/logs/s7f`).
- Before launch, the script's final check and projection were dry-run on existing models: V2X step 2 gives +0.0014 as recorded, and LUMPI S6 against R5 gives the Van judge pass and +0.0039.

**Results of S7.4 and S7.5** (2026-10-27, `$BDC_DATA/logs/s7f`).
- **Runs.** All eight trained to epoch 40 (done 03:16-07:08) and were post-processed by 09:42. Each draw member falls inside the spread of its family's seeds. Each extended bag gains on both splits over the bag it extends. Realval mAP A / B with TTA:

| Family | Seeds | Draw 2 | Draw 3 | Bag it extends | Extended bag | Gain A / B |
|---|---|---|---|---|---|---|
| V2X Voxel R-CNN | 0.651-0.690 / 0.639-0.691 | 0.6759 / 0.6829 | 0.6685 / 0.6706 | 0.7083 / 0.6968 (3) | 0.7100 / 0.6998 (5) | +0.0017 / +0.0030 |
| V2X PV-RCNN++ | 0.667-0.689 / 0.660-0.680 | 0.6822 / 0.6780 | 0.6730 / 0.6572 | 0.7018 / 0.6937 (3) | 0.7055 / 0.6968 (5) | +0.0037 / +0.0031 |
| LUMPI Voxel R-CNN | 0.327-0.336 / 0.180-0.189 | 0.3504 / 0.1932 | 0.3450 / 0.1916 | 0.3483 / 0.1922 (3) | 0.3593 / 0.1992 (5) | +0.0110 / +0.0070 |
| LUMPI PV-RCNN++ | 0.337-0.343 / 0.188-0.196 | 0.3485 / 0.1920 | 0.3360 / 0.1883 | 0.3563 / 0.1996 (4) | 0.3613 / 0.2009 (6) | +0.0050 / +0.0013 |

  More members and fresh draws cannot be told apart here: the extended bags have 5-6 members, the bags they extend 3-4.
- **V2X (`routed-g11`).** Select moved vehicle to `bagvr5x_tta`. The fuse step then kept the incumbent fusions:
  - vehicle: the best extended-bag candidate, `bagvr5x_tta+bagpv5x_tta@0.7`, scored A 0.8640 / B 0.8690. The incumbent scores 0.8654 / 0.8693.
  - truck: the best candidate scored 0.9108 / 0.8420, against the incumbent triple's 0.9356 / 0.8481.
  - pedestrian: `bagvr5_tta+bagpv5x_tta@0.7` failed the pooled rule (pooled +0.0017 at P 0.79, dB -0.0041).
  - **Outcome:** every class equals the entry, so the entry stays.
- **LUMPI (`routed-g9`).** The fuse step passed three classes, each at pooled P 1.0:
  - Car: `pvros_tta+bagpv4x_tta@0.7`, pooled +0.0059.
  - Truck: `pvros4d2_tta+ppros_tta@0.3`, pooled +0.0173.
  - Motorcycle: frozen by rule 4.

  On the final predictions, Truck was kept: dA +0.0210, dB +0.0049, pooled +0.0169 at P 1.0, train split +0.0210. Car was frozen: dA +0.0063 and dB +0.0063, but pooled -0.0026 at P 0.54. Person and Van kept their incumbents.

  Package `s7x`: kit check valid, 15,159 boxes, 173 s. Projection: dA +0.0030, dB +0.0007, combined **+0.0010, below the +0.003 bar**. **Outcome:** not submission-ready under rule 6.
- **Why LUMPI Car failed on the final predictions.** The budget's score floor of 0.01 caused it:
  - The floor leaves the A and B APs exactly unchanged and cuts Car boxes from 259 to 73 per frame (realval-A).
  - It does remove the last few true positives under an R40 recall level of the pooled A+B frames.
  - Losing that one level costs 0.0085 pooled AP, which turns +0.0059 into -0.0026.
  - Recomputing from the member predictions (the fusion, then the floor) reproduces both numbers exactly.
  - The budget bounds the floor's loss per split only. The final check reads the pooled frames.
  - The same mechanism probably explains R3 LUMPI Car (fuse +0.010 at P 1.00, final +0.0006 at P 0.64; `route_predictions.final_gate`).
- **What the pre-registered fuse step did not test.** Its candidates are the sets of top-ranked members plus the incumbent. Several incumbent fusions contain a 3-seed bag or a seed of a bag family: V2X vehicle and truck, LUMPI Person, and the new LUMPI Truck. The candidates never included the same fusion with the extended bag in that member's place. That swap is the direct test of the S7 hypothesis: the same fusion with less variance.

**Amendment S7.6** (2026-10-27). Written after the results above and before any S7.6 number existed. It is post hoc, so it gets one candidate per class and no search. The rules of S7.4 and S7.5 otherwise stand.
1. **Bag swap.**
   - **Starting point:** the S7.4/S7.5 portfolio as it stood before its final-check freeze. V2X `routed-g12` starts from `routed-g11`. LUMPI `routed-g10` starts from `routed-g9`, with Car and Truck as fused.
   - **Swap rule:** in each fusion (not of a rare-frozen class), replace every member that is a seed of an extended bag, or the 3-seed bag that bag extends, with the extended bag at the same TTA setting. The IoU stays the same. A candidate that would use a checkpoint twice is not tested.
   - **Candidates** (computed by `route_predictions.swap_candidates` before evaluation):
     - V2X vehicle: `bagvr5x_tta+pvros4s2_tta@0.7` (was `bagvr5_tta+pvros4s2_tta`).
     - V2X truck: `pp5_tta+bagvr5x_tta+bagpv5x@0.5` (was `pp5_tta+bagvr5_tta+bagpv5`).
     - LUMPI Person: `pp4_tta+bagvr4x_tta@0.5` (was `pp4_tta+vrros4s2_tta`).
     - LUMPI Truck: `bagpv4x_tta+ppros_tta@0.3` (was the S7.5 pick `pvros4d2_tta+ppros_tta`).
     - V2X pedestrian, LUMPI Car and LUMPI Van have no bag member, so no candidate.
   - **Gate:** the same as the fuse step: the 6.0 pooled rule, with LUMPI Person ranked on late-A.
2. **Pooled budget.** For every class, the score floor's AP loss must be at most 0.002 on realval-A, on realval-B and now also on the pooled A+B frames (`budget --pooled`). Floors can only fall, so box counts and kit time can grow; the kit check must still finish in under 400 s.
3. **Unchanged steps.** V2X tail copies and the sparse stage are re-derived, and the LUMPI rare classes are frozen. The final check against the entry (rule 5) runs, now as the shared tool `common/tools/s7_check.py`; failing classes are frozen. Then the upload gate (rule 6, +0.003) and audit rules a-e apply.
4. **One run** (`common/pipeline/s7g_amend.sh`, package tag `s7s`). No further amendment before the development phase closes.

**Results of S7.6** (2026-10-27, 15:39-16:58, `$BDC_DATA/logs/s7f`, events `AMEND`, logs `am_<track>_*.log`). Realval AP, A / B:

| Track, class | Swap candidate | Incumbent | Gate | Decision |
|---|---|---|---|---|
| V2X vehicle | `bagvr5x_tta+pvros4s2_tta@0.7`: 0.8649 / 0.8662 | 0.8654 / 0.8693 | not tested (below the incumbent on the mean) | incumbent kept |
| V2X truck | `pp5_tta+bagvr5x_tta+bagpv5x@0.5`: 0.9375 / 0.8502 | 0.9356 / 0.8481 | pooled +0.0010 at P 0.70 (dB +0.0021 at P 0.60) | **failed** the pooled rule |
| LUMPI Person | `pp4_tta+bagvr4x_tta@0.5`: 0.4878 / 0.1480 | 0.4654 / 0.1605 | the incumbent ranks first on late-A | incumbent kept |
| LUMPI Truck | `bagpv4x_tta+ppros_tta@0.3`: 0.4759 / 0.2018 | the S7.5 pick, 0.4873 / 0.2056 | not tested | S7.5 pick kept |

- **Pooled budget.** It changed one floor only: LUMPI Car fell from 0.01 to 0.0 (259 boxes per frame instead of 73). Every other floor on both tracks is unchanged.
- **V2X (`routed-g12`).** No class changed, so the result equals the entry.
- **LUMPI (`routed-g10`).** The final check keeps two classes, each at pooled P 1.0, with train-split deltas equal to dA:
  - Car: dA +0.0063, dB +0.0063, pooled **+0.0059**. Under the S7.5 floor it was -0.0026, which confirms the floor artifact.
  - Truck: as in S7.5.

  Package `s7s`: kit check valid, 23,270 boxes, 271 s (S7.5: 15,159 boxes, 173 s). Projection: dA +0.0039, dB +0.0016, combined **+0.0014, below the +0.003 bar**.
- **What the three runs show.** The extended bags gain on their own (+0.002 to +0.011 per bag). Inside the portfolio, though, the fusions with other architectures have already taken most of that variance reduction. The per-class gains that remain are small, and they pass the gates only on LUMPI Car and Truck, which together are worth +0.0014 combined.

**Submission-ready versions** (rule 6; nothing passed the upload gate):

| Track | Submission-ready version | Why |
|---|---|---|
| V2X | **the entry: 1001919, `model-v2x-track/routed-g9/submissions/2026-10-18_s7/v2x_s7_submission.zip`** (md5 `c1483d590242`) | S7.4 and S7.6 change no class |
| LUMPI | **the entry: 995869, `model-lumpi-track/routed-g8/submissions/2026-10-16_s6/lumpi_s6_submission.zip`** | S7.6 `s7s` passes every class rule but projects +0.0014, under the +0.003 bar |

- The LUMPI `s7s` package (`model-lumpi-track/routed-g10/submissions/2026-10-27_s7s/submission.zip`) stays on disk, checked and reproducible. It is not an upload candidate under these rules.
- No upload is planned before the development phase closes. Final-phase F1 is the exact scored zip of each track.
- The forum-FAQ review of 2026-10-27 ([audit addendum](2026-10-26-rules-compliance-audit.md#addendum-2026-10-27-the-organizers-forum-faq)) applies to these versions as it does to the entries. They use the same corpus recipes; only the generator seed differs.
