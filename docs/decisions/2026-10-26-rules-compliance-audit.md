# 2026-10-26 rules: deep compliance audit before the final phase (entries S7 V2X and S6 LUMPI; every method S1-S7)

**Version.** Entries V2X 1001919 (S7 step 1, `model-v2x-track/routed-g9`) and LUMPI 995869 (S6, `model-lumpi-track/routed-g8`); every method and real-data use of S1-S7.

**Sources re-read on 2026-10-26.**
- CodaBench 16684 and 16685: Terms, Rules, Overview, Evaluation, Data, Submission, and the phases through the public API.
- The challenge site: unchanged since 2026-07-27, commit `72aa87f` of `urbanity-lab/bdc2026-urbantwin-sim2real`.
- The kit declaration, and the organizers' papers for the split definitions.

**Changes since the 2026-10-14 review.** Only the Letter of Intent notice. CodaBench now says "accepted through October 30, 2026, 8:00 PM EDT ... Teams that have already submitted an LOI by email need take no further action", while the site still shows Aug 15 (stale). The texts are otherwise identical.

**Checks run for this audit.**
- **No pretraining.** Every member training log that records the setting shows `pretrained_model None` and `ckpt None`.
- **Entry members.** Every member of both entries is trained on our G1/G2 corpora (`g1-v2` to `g1-v5`).
- **Test frames.** The kit test frames are read only by detector inference (`pcdet_predict.py`), the S7 point count at inference (`route_predictions.frame_points`) and the one-time guard resolution (`resolve_test_ids.py`).
- **Git contents.** No kit or real-data file is tracked in git.
- **Kit check.** The kit check scores realism against the legal proxy 4, not the kit's `realism_reference` (which duplicates the test frames).
- **Splits.** The organizers' papers split LUMPI Measurement4 80/20: frames 0-6495 train, 6496-8119 test, which holds the whole forbidden window.
- **Dry run.** Both entries rebuild from their checkpoints IDENTICAL (predictions and frames equal to the scored zips; `$BDC_DATA/logs/s7repro`), so the code a verification would ask for reproduces what was scored.
- **Train-split frames in our validation.** V2X realval-A (688 frames) has 424 from V2X-Real's train split, 119 from val and 145 from test. realval-B (298) has 162 / 27 / 109.

| # | Item | Clause | Our use | Risk | Action |
|---|---|---|---|---|---|
| 1 | Letter of Intent | Overview: LOIs "accepted through October 30, 2026, 8:00 PM EDT"; "Teams that have already submitted an LOI by email need take no further action" | ~~no LOI or confirmation on record since Oct 2~~ **2026-10-28:** LOI by email on 2026-08-26 (team KarmaRV, both tracks, institution and bio), acknowledged by the organizers the same day; the repository had no record of it until 2026-10-28 | ~~moderate~~ **none (closed 2026-10-28)** | none: no form and no confirmation request ([Addendum 2026-10-28](#addendum-2026-10-28-the-letter-of-intent-is-on-record)) |
| 2 | Disclosure to the organizers | Terms 6 (integrity verification of top teams); Rules, Disqualification | the Section 10 questions and the gray-area disclosures were never sent | **low-moderate**: an undisclosed gray use found in a verification reads worse than a declared one | send Appendix A, recommended before the final phase opens on Nov 1 (the audit's date, not a rule's); record the reply verbatim |
| 3 | Scope of "train split" | Rules, Allowed: "the train split of the public real dataset for hyperparameter selection or domain adaptation" | V2X validation includes V2X-Real val and test split frames (38% of A, 46% of B); LUMPI realval-B is Measurements 5-6, outside the organizers' M4 split; LUMPI realval-A (M4 0-6399) is inside it | **low**: not forbidden (the Forbidden list and Terms 1 name only the 100 frames), but outside the Allowed wording. **2026-10-27:** V2X validation allowed by the forum FAQ; LUMPI M5-6 open (Addendum) | disclose and ask (Appendix A, Q1). The live S7 V2X decision holds on train-split frames alone (pedestrian k = 6 best on A-train +0.018 and B-train +0.019; vehicle gains on both). From now on every gate also reports the train-split-only result |
| 4 | Real label statistics in the generator | Rules: detector "trained on your synthetic data only"; "model trained on real labels" forbidden; declaration "synthetic data I generated" | walker placement drawn from legal real label rows plus jitter (a kernel density sample); real size priors and ROS ranges; clutter near real walker positions; S7 label thresholds | ~~remote~~ **moderate (2026-10-27, Addendum)**: each inserted walker's training box is a jittered real label row, against the FAQ's "real labels (or derivatives) as ground truth" | disclose (Appendix A; report); no new label-derived generator content before the final |
| 5 | Post-processing selected on real labels | Rules, Allowed: hyperparameter selection; Terms 1 | per-class sizes, C1 z, NMS, score blend, fusion sets, score floors, tail copies, S7 point thresholds | **none-remote** | **boundary kept and now a rule:** a few scalars per class are chosen on validation; no model is ever fitted to real labels (no learned re-scorer, regressor or calibration network), because that would be "a model trained on real labels" |
| 6 | Leaderboard-informed meta rules | Forbidden: "hyperparameter-tuning ... from any of the 100 frames"; allowed: "Use this to iterate", "resubmit your best system" | the 6.0 pooled rule adopted after the S6 variant b upload; R5 froze LUMPI Bicycle, Motorcycle and Bus after leaderboard Bicycle drops; the S6 Van judge was supported by realval-A matching the leaderboard Van level; the projection rule calibrated on leaderboard transfers | **remote**: each is a gate or judge applied to whole classes, never a per-class configuration copied from the leaderboard; Van rests on label sizes (class 6 differs between M4 and M5-6) | disclose as iteration on complete systems; no further leaderboard-informed rule change before the final |
| 7 | Public statistics of the test GT | Forbidden: "otherwise observing ground truth from any of the 100 frames" | the public per-class test GT counts used in planning (`01` 7.2); the R5 test-window-like proxy (realval-A re-weighted to the public per-frame class counts; dropped after a failed backtest); the S5 and R3 diagnoses comparing our test-frame box counts with those counts | **low-remote**: organizer-published aggregates, never used to select | disclose; S7 revisions never use them |
| 8 | The 50 test point clouds | Terms 3: "strictly for generating challenge submissions ... not re-distributed, re-hosted, or used outside this challenge" | inference, S7 point counts at inference, format checks, guard resolution by exact point matching (V2X) | **remote** (guard resolution is integrity work for this challenge) | `common/kit/` stays git-ignored and out of every release; no work outside this challenge uses the kit frames or leaderboard numbers |
| 9 | Set-level scaling of scores | none (inference) | tail copies and the S7 demotion scale by min/max of the class's scores over all 50 test frames, so one frame's scores depend on the others | **remote**: only the order changes, and a fixed factor gives the same ranking (S7 probe: x 1e-3 gave identical AP) | none for the entries; new versions may use fixed constants |
| 10 | Realism frames | Forbidden: inferring the realism reference via leaderboard signal | frames chosen on legal proxies; nulls injected at 31% (legal realval 0.309; the kit's 31.1% only confirms the format); server realism compared with proxies descriptively | **remote** | no frames-only upload; frames fixed through the final |
| 11 | Frames next to the test window | Rules; Disqualification ("frames that suspiciously resemble held-out real frames") | LUMPI late-A (M4 4800-6399) judges Person and Van because it is closest to the window; self-exclusion 6400-8200 (the organizers' test split starts at 6496) | **remote** (validation frames, never training data or submitted frames) | disclose |
| 12 | Research-phase exposure (`2026-09-30-rules-research-exposure.md`) | Forbidden: observing forbidden GT | aggregates over Measurement4 computed before the guard existed (at most 1.2% of the rows in the forbidden window), nothing derived used | **low** | disclose in the email |
| 13 | UT twins inside our corpora | declaration: "synthetic data I generated" | UT frames re-rendered and extended by our engines; no member is trained on raw UT alone in either entry | **remote** (the organizers state UT "may serve as training data"); **closed 2026-10-27** by the forum FAQ | state it in the report |
| 14 | Declaration file | Terms: "a signed declaration.txt"; Submission: `declaration.txt` accepted | verbatim statement, team, date | **remote** | keep the scored zips byte-identical for F1; the final-phase zips may add a signature line (the entrant's name) only if repackaged |
| 15 | Final-phase mechanics | phase pages: 5 in total, 1 per day, hidden, no carry-over; Terms 7: terms may change before Nov 1 | the API shows `max_submissions: None` for the final phase | **low** (operational) | self-enforce 5; re-read the Terms on Nov 1 before F1; F1 = the exact scored zips |
| 16 | Report, verification and code release | Rules: a 4-8 page report from every team by Nov 15; top-3 verification (Terms 6) | `paper-bigdata2026/`; repository private | **low** (organizational) | the release excludes real data, kit files and real-derived priors (V2X-Real is "All Rights Reserved"; ship the scripts that rebuild them instead); licence sign-off for a corporate entrant (LUMPI CC BY-NC 3.0, V2X-Real academic) stays the entrant's |
| 17 | Accounts and coordination | Rules, Forbidden | one account (KarmaRV) | none | |
| 18 | Pretraining on real data | site: "Using real data for training, including fine-tuning" | none: all members from scratch on synthetic corpora | none | |

**Decision.**
1. **The entries stand.** Both are compliant under the 2026-10-14 reading. Items 1 to 3 are actions to close, not reasons to withdraw.
2. **Pre-registered for every later version** (S7 revisions and the final phase):
   - (a) each gate also reports the result on train-split frames only (V2X train split; LUMPI M4 0-6495), and a change that loses there is not kept;
   - (b) no model is fitted on real labels; only scalars are selected;
   - (c) no statistic of the test frames or of the public test GT is used;
   - (d) no leaderboard-informed rule change before the final;
   - (e) frame-independent constants are preferred for new score scaling.
3. **The entrant's action:** the email (Appendix A), recommended before the final phase opens on Nov 1 so that a ruling can arrive in time (no rule sets a date for it). ~~The LOI (item 1), before Oct 30, 20:00 EDT~~: closed on 2026-10-28, the LOI is on record since 2026-08-26 ([Addendum 2026-10-28](#addendum-2026-10-28-the-letter-of-intent-is-on-record)).

**Outcome.** Pending: the organizers' reply to the email. The LOI needs no action (Addendum 2026-10-28). **2026-10-31:** the S8 entries were reviewed against every item ([S8 review](2026-10-31-s8-compliance-review-and-final-phase.md)); the email gains item (h), the test-time processing, and Q5.

## Addendum 2026-10-27: the organizers' forum FAQ

**Sources.**
- The CodaBench forum of the V2X-Real track (16685): two FAQ posts by the organizers (mshahbazkharal), Sept 30 and Oct 14, 2026. The entrant forwarded them; this audit had not read the forum.
- The LUMPI forum (16684) has no posts.
- The live pages of both competitions, re-read through the public API on 2026-10-27. Rules, Overview, Data, Submission and Evaluation are unchanged from the quotes in [`01-CHALLENGE-FACTS.md`](../01-CHALLENGE-FACTS.md) Section 3, and the two Rules pages are identical. The development phase ends 2026-10-31T00:00Z (Oct 30, 17:00 PDT). The final phase runs Nov 1 to Nov 15 00:00Z at 1 per day.
- The FAQ answers are written for the V2X track, but most interpret the shared Rules text. Where an answer names V2X-Real, LUMPI is treated by analogy and marked open.

**Checks run** (all on 2026-10-27):
- **Forbidden IDs.** The FAQ rule sorts the infrastructure scenarios and counts 33. It agrees with our point-matched `kit/id_mapping.json` at every resolved index, including its anchors 0, 1 and 32. It also places the 6 indices we had only bounded inside our candidate lists: 17-19 are `..._19_1`, `..._23_0` and `..._30_0` (2023-04-04-15-47-17 / 15-51-17 / 15-58-18); 25-26 are `2023-04-05-15-11-13_2_0` and `2023-04-05-16-10-26_7_0`; 31 is `2023-04-05-16-25-26_22_1`.
  - Our guard blocked every candidate folder, a superset of the exact mapping.
  - Under the exact mapping, none of the 986 realval frames, and none of the 14,381 logged real-data accesses for any purpose, lies within ±20 frames of a forbidden frame.
  - Our copy has 43 train scenes with an agent `-1` folder. The organizers' 33 skip the 10 between their indices 1 and 2; no forbidden frame is in them.
  - The forum's attached 100-ID table was not available here. A direct comparison would replace this inference.
- **Class grouping.** `data-v2x-track/track.yaml` `super_class_map` equals the FAQ list, including the dataset's spelling `MotorcyleRider`. Types outside the map are dropped.
  - In realval, riders are single boxes: ScooterRider 3.0%, BicycleRider 1.3% and MotorcyleRider 0.6% of pedestrian GT.
  - There are 6 lone Scooter boxes, no Motorcycle and no Bicycle; the 8 ConstructionCart boxes are dropped.
- **The scored zips** (V2X 1001919, LUMPI 995869; also the S7.5 package `s7x`):
  - Every synthetic frame is N x 3 float32 with N = 50,000. 150,000 floats divide by 3 and by 4; the scorer tests 3 first (FAQ; kit `score.py` lines 50-54), so they load as XYZ.
  - V2X frames are 31.0% (0,0,0), set from realval's 0.309; LUMPI frames have none, as in the kit frames.
  - The declaration's first line is the required statement word for word; the template wraps the same words over three lines. Then team and date.
- **Real-data uses by purpose** (V2X access log, every guard-allowed read). The walker rows, density prior and beam table also draw on V2X-Real val and test split frames, not only train:

| Purpose | Train | Val | Test |
|---|---|---|---|
| Realval | 586 | 146 | 254 |
| Generator walker rows | 2,883 | 717 | 1,253 |
| Density prior | 254 | 58 | 88 |
| OS1-64 beam table | 0 | 12 | 11 |

  - Real truck sizes: realval A+B labels.
- **Corpus provenance.** Each corpus card's `real_data_use` was read. V2X cards from `g1-v3` on list only the walker rows. They omit the beam table (from `g1-v3`), the real truck sizes (from `g1-v4`) and the density prior (from `g1-v5`). `data-v2x-track/prepare_g1.py` now writes all four for new corpora. The existing cards are left as written; this table is the complete record.

| FAQ answer | Our practice | Status |
|---|---|---|
| One account per team; no extra accounts to raise the limits | one account (KarmaRV); LUMPI 7 and V2X 10 of 100, never above 5 a day | aligned |
| The CodaBench page, config and scorer are authoritative; the kit is a guide | local gates use the kit scorer (parity tests) as a proxy; only CodaBench scores are reported as results | aligned |
| "never use real frames (or derivatives) as input and real labels (or derivatives) as ground truth for training and/or fine-tuning the model"; real data may be used "outside model training pipeline to judge and select models"; the conservative reading (only distribution analysis, model selection, confidence calibration) is confirmed | detectors: from scratch on synthetic corpora, no real frame as input, no real box as a direct label; every post-processing knob is a grid choice on validation (the z calibration too, `bdc26/detect/zcalib.py`). Generator: see items 4 and 19 below | detectors aligned; generator open (items 4, 19) |
| Learned synthesis components (refiner, discriminator): "real frames from the V2X-Real must not be used"; "any data from any other real datasets can be used in any form"; the restriction applies to prize-seeking submissions | no learned synthesis component on main; the density prior and beam table are fitted statistics of V2X-Real frames (item 19) | open (item 19); other real datasets are not used on main (2026-10-18 decision stands) |
| XYZ is recommended; intensity is not scored | N x 3 float32 | aligned |
| Held-out frames come from the same release; the fixed point count and zero padding are the official preprocessing to reproduce | 50,000 points, V2X 31% (0,0,0) | aligned |
| Redistributing the scorer is up to the participants | the kit stays out of the repository and any release (item 16) | aligned |
| ID rule over the 33 infrastructure scenarios; remove all 100 frames before using any other real frame; "Using the remaining real frames for validation or parameter selection is allowed" | exact mapping verified (above); V2X validation uses non-forbidden frames of all splits | aligned; closes item 3 for V2X validation |
| Class grouping (SUPER_CLASS_MAP); unlisted types left out | identical | aligned |
| UT-V2X-Real-IC counts as synthetic, as released, modified or combined; "synthetic data I generated" includes the published UrbanTwin data | UT frames re-rendered and extended by our engines | aligned; closes item 13 (LUMPI by the organizers' general statement) |
| Keep the required statement exactly; a line naming sources may follow; describe the sources in the report | statement verbatim, then team and date | aligned; a sources line only in repackaged final-phase zips (item 14: F1 stays byte-identical) |
| The 50 frames must be synthetic, nothing from V2X-Real or the 100 frames; the report says where they came from | generator outputs chosen on legal proxies | aligned; they inherit the generator's priors (items 4, 19) |

**Items revised.**
- **Item 3 (scope of "train split").** Validation and parameter selection on non-forbidden V2X-Real frames of any split are allowed by the Oct 14 answer. LUMPI Measurements 5-6 stay open, because the LUMPI forum is empty. The generator statistics taken from V2X-Real val and test split frames move to item 19.
- **Item 4 (real labels in the generator): raised from remote to moderate.** The Oct 26 wording "no real point or box enters a frame" is too strong:
  - In `data-v2x-track/prepare_g1.py` (`build_prior`, `PriorPose`), every inserted synthetic walker takes one real label row: its position (jitter σ 0.4 m), heading (σ 0.2 rad), l/w/h (x 0.97-1.03) and ground height.
  - V2X draws on 70,818 Pedestrian/Child/RoadWorker rows from every guard-allowed agent `-1` frame (`gen/walker_prior_v1.npz`).
  - LUMPI draws on 115,633 Person rows of Measurement4 0-6399 (`gen/person_prior_m4.npz`).
  - The rendered walker's box is its training label, so that label is close to a real box.
  - The G2 pass also gives re-cast actors real label sizes: V2X truck (1,584 rows), and LUMPI Bus, Truck, Bicycle and Motorcycle (`gen/size_prior_g2.npz`, realval A+B).
  - Against the FAQ's "real labels (or derivatives) as ground truth for training", the walker rows are the closest use we have. For it: the Rules allow the train split for "domain adaptation", the FAQ allows "distribution analysis", and the ECCV winners calibrated sizes to real labels.
  - Corpora: every V2X corpus from `g1-v3` on and every LUMPI corpus, so all members of both entries except the UT-only `pointpillars-ut`.
- **Item 13 (UT twins).** Closed by the FAQ.
- **Item 19 (new): real frames in the generator.** **Low-moderate.**
  - The background density prior applies 400 cell ratios (8 x 8 x 2.5 m cells) to synthetic frames:
    - V2X `g1-v5` on: fitted on 400 realval-A frames (254 train, 58 val, 88 test).
    - LUMPI `g1-v2` on: fitted on 400 realval-A frames (M4).
  - The V2X OS1-64 beam table (64 elevation angles and tilt) was measured on 23 unlabeled val and test frames.
  - None of these is a learned network. The FAQ bars V2X-Real frames only from learned synthesis components, and the organizers estimated their own sensor pose from a real frame.
  - The V2X sources lie partly or wholly outside the train split that the Rules name for domain adaptation.

**Decision (2026-10-27).**
1. **The entries stand.** Nothing found touches a forbidden frame; the class grouping, format, padding and declaration match the FAQ.
2. **Disclose items 4 and 19 precisely and ask for a ruling before the final phase** (Appendix A, revised). The Oct 26 draft understated item 4.
3. **Contingency** (not started; the entrant's decision once the ruling arrives). The final phase opens Nov 1, so a negative reply after about Nov 5 leaves little room.
   - **C1, if the statistics must come from the train split.** Rebuild the V2X priors from train-split frames only (walker rows, density prior, beam table, truck sizes) and the LUMPI sizes from realval-A. Regenerate the corpora with the same recipes and seeds, then retrain the core members. Cost: about 1-2 days of 8 GPUs.
   - **C2, if label-derived placement is not allowed.** Place walkers from a non-label source (UT's own actors, or public map data for sidewalks and crossings) with sizes from published anthropometrics. Expected loss on pedestrian and Person: unknown; a one-member probe per track (about 8 h) measures it.
4. **The S7.4-S7.6 versions** use the same corpus recipes (only the generator seed differs), so they share the entries' status. This now covers the entries themselves: the entrant uploaded both S7.6 packages on 2026-10-27 (LUMPI 1014495, V2X 1014682, identical to 1001919), and they are F1.

## Addendum 2026-10-28: the Letter of Intent is on record

**Source.** The entrant's email thread with the organizers (Muhammad Shahbaz and Shaurya Agarwal, UCF) of 2026-08-26, which the entrant provided. It stays out of the repository because it holds personal contact details.
- The entrant asked the organizers to take the email as the team's participation intent.
- The organizers noted the intent and asked for a short bio with the team name, the institution and the tracks.
- The entrant replied the same day: team KarmaRV (the CodaBench profile), both tracks (16684 and 16685), Hitachi America Ltd. R&D, and a bio.
- The organizers acknowledged the reply ("Noted") the same afternoon.

**Rule.** The Overview of both tracks, re-read through the public API on 2026-10-28, is unchanged:
- LOIs are "accepted through October 30, 2026, 8:00 PM EDT";
- teams that already sent an LOI by email "need take no further action";
- the form is for teams joining now.

The Rules tab sets no LOI condition: eligibility is open to anyone, with one account per team. The deadline in force on Aug 26 (Aug 15) had passed, but the organizers noted the LOI, and the extension to Oct 30 covers it in any case.

**Decision.** Item 1 is closed: no form and no confirmation request. Appendix A no longer asks about the LOI. Item 1 was opened on 2026-10-26 because the repository held no record of the LOI, not because a rule asks a team to file twice.

## Appendix A. Email to the organizers (draft, revised 2026-10-27 after the forum FAQ; LOI item removed 2026-10-28; the entrant sends it, best as a reply in the 2026-08-26 LOI thread)

To: Muhammad.Shahbaz@ucf.edu; Cc: Shaurya.Agarwal@ucf.edu
Subject: UrbanTwin Sim2Real Challenge, team KarmaRV (both tracks): disclosure of real-data use, rule questions

> Dear Dr. Shahbaz and Dr. Agarwal,
>
> I compete as team KarmaRV (one account; Rahul Vishwakarma, Hitachi) on both tracks (CodaBench 16684 and 16685), as in my Letter of Intent of Aug 26.
>
> **1. Disclosure.** Our detectors are trained from scratch on our own synthetic data: the UrbanTwin frames, re-rendered and extended with our own LiDAR simulation. No real point is ever a training input, and no network sees a real frame. Your forum FAQ (Sept 30 and Oct 14) asks that real labels and their derivatives are never used as ground truth for training. One part of our generator comes close to that line, so I describe every use of the public real data exactly. None touches a forbidden frame:
>
> (a) **Walker placement from real label rows.** Each synthetic walker we insert takes one real label row: its position (jittered by 0.4 m), heading (jittered by 0.2 rad), box size (scaled by 0.97-1.03) and ground height. Our engine renders the walker into a synthetic frame, and that box becomes its training label.
> - V2X-Real: 70,818 Pedestrian/Child/RoadWorker rows from non-forbidden infrastructure frames of the train, val and test splits.
> - LUMPI: 115,633 Person rows from Measurement4 frames 0-6399.
>
> (b) **Real label sizes for re-cast vehicles.** The re-cast trucks (V2X) and the re-cast buses, trucks, bicycles and motorcycles (LUMPI) take their box sizes from real labels of our validation frames.
>
> (c) **Statistics of unlabeled real frames.**
> - A background point-density prior: 400 ratios on 8 m x 8 m x 2.5 m cells, from 400 validation frames. It resamples our synthetic background points.
> - The OS1-64 beam table (64 elevation angles and the tilt), measured on 23 V2X-Real val and test frames.
> - The share of (0,0,0) returns.
>
> (d) **Validation.** Labeled real frames serve as a validation set: checkpoint, architecture, fusion and post-processing choices, and a few per-class scalars chosen by grid search (z offset, score floors, a minimum number of points per predicted box).
> - V2X-Real: non-forbidden frames of all splits, with a ±20-frame buffer around every forbidden frame.
> - LUMPI: Measurement4 0-6399 and Measurements 5-6. Frames 6400-8200 are excluded entirely.
>
> (e) **Early aggregates.** Before our forbidden-frame filter existed, some aggregate label statistics were computed over all of LUMPI Measurement4. At most 1.2% of those rows fell in the forbidden window, and nothing derived from them was used.
>
> (f) **Building the filter.** We matched the 50 released V2X test clouds against V2X-Real frames point for point to exclude those scenes; we never loaded their labels. Your index rule (33 infrastructure scenarios) agrees with our mapping.
>
> (g) **The 50 synthetic frames.** They are generator outputs chosen on our own real validation frames, never by leaderboard probing.
>
> **2. Questions.**
>
> Q1. Are (a), (b) and (c) acceptable for prize-eligible submissions as distribution analysis or domain adaptation? If (a) is not, may walker positions come from a coarse statistic of the labels, or must they come from non-label sources? If any of them must use the train split only, please say so. We would rebuild those parts before the final phase.
>
> Q2. Your Oct 14 answer allows validation on the remaining V2X-Real frames. Does the same apply to LUMPI Measurements 5-6?
>
> Q3. In the Final phase, does the best of the five submissions count (the leaderboard rule Force_Best), or the last one?
>
> Q4. What is the submission channel and template for the Nov 15 report, and is the report published?
>
> Thank you,
> Rahul Vishwakarma (team KarmaRV)
