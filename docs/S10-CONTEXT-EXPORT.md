# S10 context export: BDC26 UrbanTwin Sim2Real, final week (2026-11-08)

**What this file is.** A single, self-contained file for an outside reviewer (another AI or a person) to verify the S10 strategy and propose a plan.
- **Part 1** is a briefing written for a reader new to the project: the competition, the rules, the history, a glossary, the live state and the questions we want answered.
- **Part 2** is the full S10 decision record (`docs/decisions/2026-11-08-s10-clean-final-plan.md`), verbatim, with its headings moved down one level.

**State as of 2026-11-09, about 14:45 UTC.** Times are UTC unless marked. The run logs use server time (UTC-8). Nothing here is committed to git yet.

**Who is who.** "The entrant" is the team (KarmaRV, one researcher), who makes every upload and every decision. "We" is the entrant with the coding assistant that ran the experiments and wrote the records.

---

# Part 1. Briefing

## 1.1 What we ask the reviewer to do

1. **Verify** the plan against the rules: each technique against the organizers' clarification of 2026-11-07 (codes T, L, V, C, D in 1.3).
2. **Check the statistics**: the member check, the pooled gate, the projection rule and the expected values (1.6 and Part 2 Sections 8, 14.7 and 15.9).
3. **Find blind spots**: anything that could disqualify us, leak test information, or overfit our validation sets.
4. **Propose** the best use of the remaining time: about 5 days of GPU work and 3 uploads per track, ranked by expected combined-score gain per GPU hour, inside the constraints of 1.4.

Specific questions are in 1.11.

## 1.2 The competition

IEEE BigData Cup 2026, UrbanTwin Sim2Real challenge. CodaBench instances 16684 (LUMPI) and 16685 (V2X-Real); both are entered.

**Task.** Detect 3D objects in real roadside LiDAR with a detector trained only on synthetic data. Each submission also contains 50 synthetic frames, which are scored for realism against hidden real reference frames.

| | Track A: LUMPI | Track B: V2X-Real |
|---|---|---|
| Real data | LUMPI, Hannover; 5 merged LiDARs; Measurement 4 local frame | V2X-Real infrastructure subset; one Ouster OS1-64 |
| Classes scored (mean over those with test labels) | 7: Person, Car, Bicycle, Motorcycle, Bus, Truck, Van | 3: vehicle, pedestrian, truck |
| Range (m) | [-40, 40]² x [-5, 5] | [-40, 40]² x [-8, 2] |
| Test set | 100 frames, LUMPI Measurement 4 IDs 006497-008109 (the "forbidden frames") | 100 frames over 32 scenarios |
| Organizer synthetic data | UT-LUMPI, 10,000 CARLA twin frames, CC0 | UT-V2X-Real-IC, 10,000 frames, CC0 |

**Score.** combined = 0.6 x clip(mAP / 0.7) + 0.4 x R.
- **mAP:** 3D AP at IoU 0.5.
- **R** = 1 - mean of four terms, each clipped to [0, 1]:
  - Chamfer distance: (CD - 2) / 28, so 0 below CD 2;
  - MMD / 0.5;
  - EMD / 5;
  - FPD / 50.
- **The realism scorer**, replicated bit-for-bit in `common/bdc26/realism.py`:
  - the 50 frames are concatenated and masked to the track range, and 10,000 points are drawn per side (seed 1234);
  - EMD is the square root of W1 with a Euclidean cost;
  - FPD is the Frechet distance between 3-D Gaussians of xyz.

**Final phase.**
- Upload limits: 1 upload per day and 5 in total per track. Two are used on each track, so **3 remain**.
- The leaderboard shows each team's newest upload. Until the organizers answer, we assume **the last upload counts** (rule 13).
- **Close:** the phase pages show 2026-11-16 04:59 UTC for both tracks. The entrant may confirm this on the Phases tab, because an older note had V2X closing on Nov 15.
- **Deadlines after the close:** the report is due Nov 15; the camera-ready on Nov 20; winners are announced Nov 25.
- **Kit:** a runtime check with a 1,200 s execution limit.
- **Paper track:** the top 3 per track are invited and must be able to release code for verification.

## 1.3 Rules

**From the organizers (the CodaBench rules tab, summarized).**
- **Allowed:**
  - any simulator or generative model;
  - any detector trained on our synthetic data only;
  - training augmentations;
  - real non-forbidden data for hyperparameter selection.
- **Forbidden:**
  - any use of the 100 test frames;
  - predictions from a model trained on real labels of any roadside-LiDAR dataset;
  - probing the realism reference through the leaderboard;
  - multiple accounts.
- **Disqualification:** the organizers may inspect submissions for synthetic frames that "suspiciously resemble held-out real frames", and for predictions that imply access to the hidden ground truth.

**The clarification of 2026-11-07 (both tracks).** It decided S10:

| Code | Meaning |
|---|---|
| **T** | The detector is trained on synthetic data only. |
| **L** | Real labels, and object points cut out with real boxes, never enter the training set. |
| **V** | Non-forbidden real frames may be used for validation, model selection and box-size statistics (labels allowed). |
| **C** | Unlabelled real clouds may be used to calibrate the realism of the synthetic data. |
| **D** | Every use of real data is described in the report. |

**Consequence.** Our corpora before `g1-v6` placed each synthetic walker at a jittered real label row, so that walker's training box was a real label plus noise. Under L this counts as real labels in training. Every system uploaded before S10 contains such members. **S10 Plan A: every remaining upload is "clean"**: each member trains on a `g1-v6`-family corpus or on UrbanTwin data alone (rule 1, checked by `common/tools/clean_check.py`).

**Our own audit rules (stricter than the text).**
- **(a)** Every gate also reports the train-split-only result.
- **(b)** Never turn the positions of real objects into boxes, rules or placements.
- **(d)** Choose between complete systems by the combined score only. Never change a class because of the leaderboard's per-class numbers, including final-phase ones.
- Never probe the leaderboard. Test frames are used only for inference and kit checks. No real label row and no test frame enters the generator.

**Grey areas, waiting for the organizers** (email draft in Part 2, Appendix A; **not yet sent**):
- (a) Does the best or the last final upload count?
- (b) Is a 10-bin histogram of walker distance from the sensor acceptable as a statistic?
- (c) May unlabelled real frames be used to locate static structures the twin lacks, so that synthetic objects can be placed there ("twin completion")?

## 1.4 Constraints on any proposal

**Compute.**
- 8 x A6000 (48 GB), run as two 4-GPU training workers: trainA on GPUs 1, 3, 5, 7 and trainB on GPUs 0, 2, 4, 6.
- Three tuning workers share GPUs 0, 2, 4 and 6.
- A 12-view TTA tuning job uses up to 45 GB, so it never shares a GPU with training.
- Training stops **Nov 13, 18:00 UTC**. That leaves about 220 worker-hours.

**Time per member.**

| Architecture | Training time |
|---|---|
| PointPillars | 1.1-2.1 h |
| Voxel R-CNN | 2.9-5.9 h |
| PV-RCNN++ | 2.9-4.1 h |
| VoxelNeXt | 1.7-3.8 h |
| DSVT | 5.5-7.5 h |

- Tuning (validation inference with TTA variants and curves) takes about 3 h per LUMPI member and about 1.2 h per V2X member. **Tuning is the binding constraint.**
- A new 10,000-frame corpus draw takes about 20 min of CPU.
- A portfolio build takes 2-3.5 h of CPU.
- Disk is 95% used, with room for about 20 new corpora. Nothing is deleted without the entrant's approval.

**Software.** One pinned environment, OpenPCDet with spconv. **New packages, new architecture code and any download need the entrant's permission.** That covers the organizers' Google Drive mapping tables and extra real validation frames ("realval-C").

**Process.**
- The entrant uploads; the assistant never does.
- Leaderboard scores come from the entrant's screenshots or logs.
- Commits, tags and pushes are the entrant's.

## 1.5 History, S1 to S10

| Strategy | Main idea | LUMPI combined | V2X combined | Lesson |
|---|---|---|---|---|
| S1 (Oct 6) | twin data with ray-cast walkers; PointPillars; per-class routing | 0.4728 | 0.7665 (0.7855 with z calibration) | transfer and small objects limit the score, not detector capacity |
| S3-S4 (Oct 10) | fused portfolio; two-stage detectors (Voxel R-CNN, PV-RCNN++) | 0.5015, then 0.5040 | 0.8381, then 0.8485 | the leaderboard gain had the right sign but was 0.25-1.9x the local gain, so projections use 0.6x |
| S5 (Oct 11) | random object scaling (ROS) to the real size ranges | 0.5039 (flat) | 0.8730 | the pooled A+B gate agrees with the leaderboard on 16 of 17 class changes |
| R3 (Oct 12-14) | engine G2-lite: re-cast actors at real size and density; 30 static negatives per frame (`g1-v4`) | 0.5169 | 0.8789 | realism from a better corpus transfers |
| R5 (Oct 14) | realism-led frames | 0.5198 | 0.8852 | |
| S6 (Oct 16-17) | seed bags; the pooled rule | 0.5228 | 0.8931 | ensemble depth transfers (+0.008 on V2X) |
| S7 (Oct 18-26) | visibility (sparse) demotion; draw bags | | 0.8982 | draw bags +0.002 to +0.011 |
| S8 (Oct 29-30) | last development-phase versions | 0.5257 | 0.9022 | |
| S9 (Nov 2-6) | label-free walkers on the twin's own map (`g1-v6`); anchored box-size calibration | 0.5425 (development), 0.5428 (final, `s9j`) | 0.9030 (development), 0.9038 (final, `s9f`) | label-free placement raised LUMPI Person by +0.07 on the server. **`s9j` and `s9f` are not clean**: they include pre-v6 members |
| **S10 C0 (Nov 8)** | the first clean systems | **0.5408** | **0.8885** | clean costs 0.002 on LUMPI and 0.015 on V2X; all of the V2X loss is pedestrian |

We have been rank 1 on both tracks since S4. Rare-class changes chosen on validation did not transfer (`s9iu`: +0.010 projected, -0.0025 scored), because the test window holds classes that our late-window validation barely covers (Part 2, Section 3.3).

## 1.6 Glossary

| Term | Meaning |
|---|---|
| realval A / B | Our real validation splits, with labels and no forbidden frame. LUMPI A: Measurement 4 frames 0-6395, every 5th frame. LUMPI late-A: M4 frames 4800-6399, the most test-like subset. LUMPI B: Measurement 5/6 samples. V2X A/B: non-forbidden infrastructure frames. |
| proxies 1-5 | Unlabelled real frame sets that stand in for the hidden realism reference. Fit on 1-3, score held out on 4-5. |
| `g1-vN` | Our corpus versions: 10,000 synthetic frames each, built from the UrbanTwin data plus inserted walkers and re-cast actors. `g1-v6` is the first label-free recipe. |
| `g1-v6d2`, `d3`, `d4` | New random draws (seeds) of the `g1-v6` recipe. |
| `g1-v6j` | The union of `g1-v6` and `g1-v6d2` (18,000 frames). |
| `g1-v7` (V2X) | `g1-v6` plus map-placed static structures (`--structure 30`), used for training only. |
| Architectures | voxelrcnn = Voxel R-CNN; pvrcnnpp = PV-RCNN++; voxelnext; dsvt; pointpillars (all OpenPCDet). |
| Config suffixes | `ros`: random object scaling. `rosf`: ros plus a world tilt of ±1.5° and a GT-sampling fade. `rosn`: rosf with GT sampling off in every epoch. `sn`: statistical normalization of each synthetic object to real size statistics (lever C1). `rj`: 2 cm range jitter along each ray (lever C2). `snrj`: both. `swa`: the mean of the epoch 31-40 weights. `bag-...-x`: a fusion bag over draws. |
| Short names in routes | e.g. `vrrosn6_tta12` = voxelrcnn-rosn-g1v6 with 12-view TTA; `bvrrosf6x` = bag of voxelrcnn-rosf over the `g1-v6` draws. Prefixes: pv = PV-RCNN++, pp = PointPillars, vn = VoxelNeXt, ds = DSVT. Suffixes: `_tta` = 8-view TTA; `j`/`d2` = the joint corpus or draw 2. |
| Member check (rule 4) | A new member against its family's incumbent, per class and variant (plain, 8-view TTA). It passes a class if the pooled A+B paired bootstrap P(gain) >= 0.9 and neither split drops by more than 0.005 AP. |
| Portfolio / routed system | Per class, either route to one member or fuse up to 3 members (weighted box fusion at a set IoU). Then the post-processing stages: z calibration, score floors, box budget, tail copies (low-score duplicate boxes), sparse demotion (S7), overhead demotion (V5, new in S10), anchored size calibration, the clean check, packaging and the kit check. The "card" is the YAML file that describes a portfolio. |
| Projection (rules 6 and 10) | The expected server change: 0.6 x the mean A/B validation gain, converted to combined, plus 0.4 x the local R change. A loss from a systematic change is not shrunk. |
| `C0`, `C1`, `C2` | The S10 clean system versions. `C0` is scored; `C1` is planned for Nov 11 and `C2` for Nov 14. |

## 1.7 S10 at a glance

**Pre-registered rules** (full text in Part 2, Sections 8, 14.7 and 15.9):
1. Clean members only.
2. Class gate: pooled P(gain) >= 0.9, neither split down more than 0.005. LUMPI Person is ranked on late-A, and LUMPI Van is judged on early-A and late-A.
3. Rare LUMPI classes (Bicycle, Motorcycle, Bus) follow one rule: each takes the clean candidate with the best pooled AP.
4. Members first: the member check before any portfolio.
5. Generator parameters are never chosen by detection results.
6. Realism frames must gain held-out R >= 0.003, with CD, MMD and FPD not worse and V2X CD < 2.
7. Kit limits: at most 38,466 LUMPI boxes, and the kit check under 400 s.
8. At most one upload per day per track; the projection is recorded first; the choice between scored systems uses the combined score only.
9. Weight averaging and statistical normalization count as new members.
10. A new version needs a projection > 0 against `C0` and the final pooled gate.
11. A new post-processing stage has one parameter per class, chosen on A, and passes the pooled gate.
12. `g1-v7` is a training corpus only.
13. The last upload of each track must be our best scored clean zip; the reserve upload re-submits it if needed.
14. Grouped final gate (adopted 2026-11-09 with margins calibrated on 13 past uploads; Part 2 Section 15.12): GO at grouped P(gain) >= 0.75, leave-one-group-out >= -0.002 mAP and rare classes under half of the gain; JUDGEMENT between; NO-GO at delta <= 0 or grouped P < 0.5. Every gate comes with a history-based assessment.

**`C0` scored (upload 2):**

| Track | Submission | Combined | mAP | R | CD / EMD / FPD | vs kept zip |
|---|---|---|---|---|---|---|
| LUMPI | 1042287 | 0.5408 | 0.1950 | 0.9342 | 1.510 / 1.272 / 0.430 | -0.0020 vs `s9j` |
| V2X | 1042294 | 0.8885 | 0.5976 | 0.9406 | 1.844 / 1.110 / 0.748 | -0.0153 vs `s9f` (mAP -0.021; R +0.0074) |

**Final-phase leaderboard (entrant's screenshots, 2026-11-08 ~12:50 UTC):**

| Track | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| LUMPI | KarmaRV 0.5408 (`C0`) | lukefinigan 0.5342 (mAP 0.188) | dipper13579 0.5217 (R 0.9423) |
| V2X | KarmaRV 0.9038 (`s9f`; `C0` 0.8885 was still scoring) | sadbodh 0.855 | dipper13579 0.7816 |

- **LUMPI is the close race:** the lead is 0.0066.
- **Our realism is the weakest of the top teams on both tracks.** V2X linyongchun has EMD 0.80 and CD 0.49, which sits at the real-against-real floor (1.7, increment 5).

**Wave 1, adopted by the entrant on 2026-11-08** (increments 1-4, then 5). Details are in Part 2, Section 15.

| # | Increment | Technique | Expected combined | Status at export |
|---|---|---|---|---|
| 1 | V2X pedestrian | (a) `g1-v7` with map-placed structures as unlabelled negatives; (b) the `snrj` member as a pedestrian candidate; (c) V5 overhead-points demotion | V2X +0.003 to +0.012 | (a) **closed**: the probe's pedestrian gain is inside draw-to-draw variation (Part 2, 15.11), so no more `g1-v7` members; (b) passed pedestrian; (c) built, with a dry run on `C0` of pedestrian +0.0027 pooled, P 1.00 |
| 2 | Weight averaging (SWA) of every leaf member | mean of the epoch 31-40 checkpoints; bags of the averages | +0.002 to +0.006 per track | 4 Day 0 probes checked; of the 15 leaf members, 7 tuned and checked, 2 tuning, 6 queued (1.8) |
| 3 | Ensemble depth | V2X draws 3 and 4 (VR, PV, VN), 4-draw bags; LUMPI draw 3 (VR rosn, VR rosf, PV) | V2X +0.005 to +0.012; LUMPI +0.001 to +0.003 | V2X d3: VR, PV, VN trained, tuned and checked; d4 queued. LUMPI d3: rosn tuned; its 3-draw bag passes Person 8v +0.0102 against the 2-draw bag; rosf training, PV queued |
| 4 | Stretch | X1, a visibility rescorer trained on synthetic detections; F2, V2X realism frames re-selected from the draws 1-4 pool | +0.000 to +0.005 | code after `C1` (Nov 10) |
| 5 | Realism | frame selection on the exact scorer, merged with F2; twin completion only if the organizers allow it | V2X +0.0004 to +0.0012 | thinning / density refit dropped (no gain); twin completion waits for question (c) |

**Why the realism headroom is small for us** (Part 2, Section 15.6). A fixed sensor returns nearly the same points from the same static scene in every frame. So two real frame sets coincide to the centimetre:
- median nearest-neighbour distance between real frame sets: 0.000-0.002 m on V2X;
- ours: 0.22-0.33 m.

As a result:
- **real against real:** EMD 0.751 on V2X and 0.980 on LUMPI;
- **our `C0` frames:** 1.08-1.20;
- **thinning toward the real density at any resolution:** no gain.

## 1.8 Live status at export (2026-11-09, about 18:45 UTC)

**Training** (wave 3, refined option A; Part 2 Section 15.10).

| Worker | Member | State |
|---|---|---|
| trainA (GPUs 1, 3, 5, 7) | LUMPI `voxelrcnn-rosf-gblobs-g1v6` (D3) | started 16:01 UTC |
| trainB (GPUs 0, 2, 4, 6) | V2X `voxelrcnn-ros-gblobs-g1v6` (D3) | started 16:20 UTC |

**Train queue (in order):** V2X `pvrcnnpp-ros-g1v6d5`; LUMPI `voxelrcnn-rosf-g1v6d4`; V2X `voxelnext-ros-g1v6d5`; V2X `voxelrcnn-ros-g1v6d5`; LUMPI `voxelrcnn-rosn-g1v6d5`; LUMPI `voxelrcnn-rosf-g1v6d5`. Every member passed the clean check (rule 1). The queue drains on about Nov 10, afternoon UTC; the next wave is planned before then.

**Tuning:** V2X `voxelnext-ros-swa-g1v6d4` (then the VoxelNeXt bag of averaged draws 1-4); LUMPI `voxelrcnn-rosn-g1v6d4` and `voxelrcnn-rosn-swa-g1v6d4` (then the rosn 4-draw bags). V2X `bag-voxelnext-ros-g1v6x4` passes all six checks against the 3-draw bag: VoxelNeXt still gains from a 4th draw.

**C1 dry runs (Part 2 Section 15.13.7):** LUMPI `routed-c1a` from scratch is -0.0015 against `C0`; the R3 class gate reverts every class (Person +0.0037 on B is below the +0.01 bar), and after a gate fix (the revert now restores the size entry) it reproduces `C0` exactly. LUMPI `C1` today would be `C0`. The V2X dry run (gated against `routed-c0` by the new tail step `S10_INCUMBENT`) started 18:19 UTC.

**Member checks:** the full table (about 45 rows) is in Part 2 Section 15.10. In short:
- **Draw bags work on both tracks.** Each 3-draw bag beats its 2-draw bag on at least the classes listed: V2X PV-RCNN++ and VoxelNeXt on all six class variants, V2X Voxel R-CNN on vehicle, LUMPI Voxel R-CNN on Person, Car and Bicycle, and LUMPI PV-RCNN++ on Car, Bicycle and Van (Truck, its `C0` route class, is flat).
- **Weight averaging (SWA) passes at least one class on every averaged member.** It is strong for Voxel R-CNN and V2X DSVT, and weak for LUMPI PV-RCNN++ and VoxelNeXt.
- **Bags of averaged draws** add LUMPI Person (8v +0.0026 and +0.0072, B 0.231 and 0.236 against `C0`'s fused 0.232) and V2X PV-RCNN++ pedestrian (+0.0023).
- **All four pre-registered levers are dropped by the rule** (a lever is kept only if its single arm passes a class without failing another): V2X statistical normalization, V2X range jitter, LUMPI statistical normalization and LUMPI range jitter (decided 12:40 UTC Nov 9: it passes Person, Bicycle, Car 8v and Van, and fails Truck, Motorcycle and Car plain at P 0.00). The SN, jitter and SN + jitter members stay per-class route candidates.
- **`g1-v7` structures:** no pedestrian effect beyond draw variance, so no more `g1-v7` members (branch C, Part 2 Section 15.11).

- **Board of 2026-11-09 07:40 CST and the final-week research review (Part 2 Section 15.13):** LUMPI is lost by 0.0032 to lukefinigan (equal detection; EMD 1.124 against our 1.272). The V2X board still shows `s9f` (not clean); clean `C0` leads by 0.055. Plans D1 (depth, running), D2 (Person point-count rescoring), D3 (GBlobs member, conditional), R1 (twin completion, waits on the email), R2 and V5.

**Next decision points:**
- **Nov 9-10:** V2X draw-4 bags and bags of averaged draws; V2X draw 6 only if the 3 to 4 draw gains still grow.
- **Nov 10:** `C1` builds on both tracks: the route and fusion search over the new candidates, the V5 overhead stage (V2X), realism frame selection (V2X), then the rule 14 gate against `routed-c0` with the history-based assessment (Part 2 Section 15.12).
- **Nov 11:** upload 3 (`C1`, both tracks), by the entrant.

## 1.9 Schedule ahead (UTC)

| When | Work | Uploads |
|---|---|---|
| Mon Nov 9 | member checks (the `g1-v7` decision is made: branch C); the LUMPI `rj` lever; V2X draw-4 bags | |
| Tue Nov 10 | LUMPI `C1` build; X1 and F2 code | |
| **Wed Nov 11** | | **Upload 3: `C1`, both tracks** |
| Thu Nov 12 to Fri Nov 13 | bag partners of whatever passed; training stops Nov 13, 18:00 | |
| **Sat Nov 14** | `C2` builds, kit checks, reproduction dry runs | **Upload 4: `C2`, both tracks** |
| Sun Nov 15 to Mon Nov 16 04:59 | the report | **Upload 5 (reserve):** re-upload the best scored clean zip if `C2` scored lower (rule 13) |

## 1.10 Open items for the entrant

1. **Send the email** (Part 2, Appendix A): disclosure, Q3 (best or last), the histogram question, and question (c) on twin completion. Twin completion is the only larger realism lever left, and it waits on (c).
2. Confirm on the V2X board that 1042294 (`C0`) replaced 1038966 (`s9f`).
3. Push release 9.2 and publish its weights, if not done.
4. Confirm the close time on the Phases tab.

## 1.11 Questions for the reviewer

1. **Multiple comparisons** (partly answered by rule 14, Part 2 Section 15.12). We run dozens of member checks, each at P(gain) >= 0.9 per class and variant, so some passes are false. Is the final pooled gate on the complete system, with the 0.6 shrink, enough protection? Would a stricter gate, or a holdout we have not used for selection, be better?
2. **Projection.** Is 0.6 x the mean A/B gain right for `C1` against `C0`, given these transfers: V2X realism at 0.86x, LUMPI fine realism changes at 0.31x, and a systematic V2X loss at 1.2x?
3. **LUMPI.** The lead is 0.0066, and the largest `C0` loss against `s9j` is Bus (-0.073 AP on B). The rare classes cannot be validated in the test window (late Measurement 4 holds 11 Bus and 4 Motorcycle boxes). What is the best legal LUMPI lever for the next 5 days?
4. **V2X pedestrian.** Is `g1-v7` (structures as unlabelled negatives) the right first lever? 65% of confident false pedestrians sit on static structures. Alternatives: walker mesh and pose variety, pedestrian-strong draw bags, the X1 rescorer.
5. **Realism.** Is there any legal synthetic route that brings EMD toward the real-against-real floor, short of twin completion? For example, a better reconstruction of the twin's own static geometry, without real points.
6. **V5 overhead demotion** uses only each test cloud's own points at inference, like the S7 sparse stage. Should it be named in the email as a test-time step, or is the report enough?
7. **Upload policy.** Is the "last counts" reading and the reserve re-upload (rule 13) the safest policy if the organizers do not answer?
8. Anything in Part 2 that conflicts with T, L, V, C or D.

## 1.12 Key files

| Path | What |
|---|---|
| `docs/decisions/2026-11-08-s10-clean-final-plan.md` | the S10 record (Part 2) |
| `docs/decisions/2026-11-02-s9-clean-twin-plan.md` | the S9 record (the `g1-v6` label-free recipe) |
| `docs/01-CHALLENGE-FACTS.md` | verified challenge facts, timeline, rules |
| `common/tools/clean_check.py` | rule 1 check |
| `common/tools/s9_member_check.py` | member check (rule 4) |
| `common/tools/route_predictions.py` | route, fusion, calibration and the post-processing stages, including V5 `overhead` |
| `common/pipeline/s10_clean_portfolio.sh`, `s10_portfolio_tail.sh` | clean portfolio build |
| `common/tools/swa_ckpt.py` | weight averaging |
| `common/bdc26/detect/augment.py` | statistical normalization (`CLASS_CENTER`) and range jitter |
| `common/bdc26/realism.py` | exact realism scorer |
| `common/tools/s10_emd_attribution.py`, `s10_thinning_bound.py` | increment 5 analysis |
| `common/tests/test_s10.py` | S10 unit tests (all pass) |
| `$BDC_DATA/logs/s10/STATUS.md`, `events.txt`, `member_checks/` | run state |

---

# Part 2. The S10 decision record (verbatim, headings moved down one level)
## 2026-11-08 S10 plan: Clean Final, label-free entries for the final week

**Version.** S10 starts from the kept final-phase zips:
- LUMPI `s9j` (1038963, 0.542809, `routed-g22`);
- V2X `s9f` (1038966, 0.903777, `routed-g19`).

Both are release 9.2. One of five final uploads is used per track, so four are left. The final phase closes on **2026-11-15 04:59 UTC (V2X)** and **2026-11-16 04:59 UTC (LUMPI)**. This record is the plan, written before any S10 run. Results go in Section 13.

**Status: Plan A adopted by the entrant on 2026-11-08 ("Adopt Plan A").** Every remaining upload is a clean system.

**Why now.** On 2026-11-07 the organizers sent the same clarification on both tracks about forbidden frames and real-data use (Section 1). One sentence of it decides what the remaining uploads must be.

**Sources.**
- The two organizer emails of 2026-11-07, which the entrant forwarded.
- The S1-S9 records, summarized for this plan.
- New checks on 2026-11-08 (Section 3), run on legal frames, corpus cards and validation outputs only.
- A literature review (Section 11).

### 1. The clarifications, line by line

| Sentence (both tracks unless marked) | What we do | Verdict |
|---|---|---|
| LUMPI: "All 100 IDs in forbidden_frames.txt are frames from Measurement 4 ... 006497 is Measurement4/lidar/006497.ply" | The kit list holds 100 IDs, 006497 to 008109, all inside the organizers' M4 test window (6496-8119). The guard blocks the window, and label rows are filtered while streaming. Realval-A is M4 0-6395 (every 5th frame), and every other M4 use stops at frame 6399. | **Confirmed.** The nearest legal use is 98 frames before the first forbidden ID. |
| V2X: "`<s>_<f>` ... infrastructure LiDAR (agent folder -1) ... `<s>` is a 0-based index over the ... scenario folders that contain a -1 agent, sorted by name (33 in total)" | This is the FAQ rule we checked on 2026-10-27 (audit addendum). Our point-matched mapping agrees at every index. The guard blocks a superset of candidate folders. No realval frame and none of 14,381 logged reads lies within 20 frames of a forbidden frame. | **Confirmed.** The organizers' mapping tables are Google Drive files. A direct comparison would replace our inference, but downloading them is the entrant's call. |
| "you may use the remaining real training frames for validation, model selection and box-size statistics (labels allowed)" | Covers: realval A/B and every grid, route, fusion, threshold and copy choice; the S9 anchored size calibration; the 19 size quantiles of the rare classes; the size thresholds of the vehicle class rule; the walker box-size mixture. | **Allowed, now explicitly.** This closes the size part of audit item 4 and disclosure item (i). |
| "and for calibrating the realism of your synthetic data (unlabelled clouds)" | Covers: the background density priors, the OS1-64 beam table, and the realism proxies that select the 50 frames. | **Allowed, now explicitly.** This closes audit item 19. One residual point: the V2X statistics use val and test split frames, so we read "remaining real training frames" as every non-forbidden frame, as the Oct 14 FAQ did for validation. Disclose it. |
| "The detector itself must be trained only on synthetic data, so **real labels and object points cut out with real boxes must not enter the training set**" | **Corpora before `g1-v6`** (LUMPI from `g1-v1`, V2X from `g1-v3`): every inserted walker copies one real label row, with its position jittered by 0.4 m, heading by 0.2 rad, size by 0.97-1.03, and with the real ground height. The rendered walker's box is its training label. The G2 clutter is also anchored at real walker positions. **`g1-v6` corpora:** walkers and clutter are placed on the twin's own scene map, and only scalars reach the generator: the box-size mixture, size quantiles, and a 10-bin range histogram. **No corpus** contains object points cut out with real boxes; the GT-sampling databases are built from each synthetic corpus. | **Pre-v6 corpora: not compatible** on a plain reading, since each walker's training box is a real label plus small noise. **`g1-v6`: compatible.** The range histogram is a position statistic, not a label; disclose it. |
| "Please describe any use of real data in your report." | The report draft (`paper-bigdata2026/README.md` Sections 3.1-3.3) lists the uses. It also says the walker rows were "disclosed to the organizers", which has not happened: the email is unsent. | **Rewrite** the report's real-data section (Section 9) and correct that sentence. |

### 2. What this means for the kept zips

| Zip | Members | Trained on a pre-v6 corpus | Realism frames |
|---|---|---|---|
| LUMPI `s9j` | 14 | 12. Only `pvros6_tta12` and `vrrosf6_tta12` train on `g1-v6`. The Person fusion is clean and the Car fusion half clean. Bicycle, Motorcycle, Bus, Truck and Van route to `g1-v1`, `g1-v3` and `g1-v4` members. | `g1-v6` |
| V2X `s9f` | 6 | All 6 (`g1-v3`, `g1-v4` and `g1-v5` bags and seeds) | `g1-v5` |

**Reading.** Under the clarification's fifth sentence, both kept zips depend on members whose training set holds jittered real labels. The Oct 27 audit rated this moderate, because the FAQ was the only text then. The clarification restates it in plain words for both tracks, so the risk is now **high**. The same holds for every development entry and every earlier release.

**What S10 does about it (recommended, Plan A).** Every remaining upload is a **clean system**: each member trains on a `g1-v6`-family corpus or on the UrbanTwin data alone, and the realism frames come from such a corpus. The entrant emails the organizers, and the email should do three things:
- state that the F2 uploads (1038963, 1038966) and the development entries include members trained with label-placed walkers;
- name the clean uploads as the ones to rank;
- ask Q3 (does the best or the last final submission count).

Earlier releases stay published as history. The READMEs record their status.

### 3. New measurements (2026-11-08; legal frames, corpus cards and validation outputs only)

#### 3.1 Clean members against the kept zips

Best single clean member per class: realval 3D AP@0.5, A / B. There is no fusion yet. For each class the member is picked by its mean of A and B, so A and B come from the same member.

| Class | Kept zip A / B | Best clean A / B | Member (views) |
|---|---|---|---|
| LUMPI Person | 0.595 / 0.231 | 0.596 / 0.217 | `voxelrcnn-rosn-g1v6` (12) |
| LUMPI Car | 0.910 / 0.808 | 0.901 / 0.789 | `voxelrcnn-rosf-g1v6` (12) |
| LUMPI Bicycle | 0.601 / 0.264 | 0.569 / 0.257 | `bag-pointpillars-ros-g1v6x` (8) |
| LUMPI Motorcycle | 0.008 / 0.015 | 0.235 / 0.033 | `voxelnext-rosn-g1v6` (12) |
| LUMPI Bus | 0.080 / 0.136 | 0.010 / 0.062 | `pointpillars-ros-g1v6` (8) |
| LUMPI Truck | 0.487 / 0.205 | 0.375 / 0.232 | `bag-pvrcnnpp-ros-g1v6x` (8) |
| LUMPI Van | 0.174 / 0.002 | 0.109 / 0.001 | `dsvt-rosf-g1v6` (12) |
| **LUMPI mAP** | **0.408 / 0.237** | **0.399 / 0.227** | single members, before fusion |
| V2X vehicle | 0.875 / 0.879 | 0.831 / 0.842 | `bag-voxelrcnn-ros-g1v6x` (8) |
| V2X pedestrian | 0.418 / 0.451 | 0.374 / 0.365 | `bag-voxelrcnn-ros-g1v6x` (8) |
| V2X truck | 0.936 / 0.848 | 0.878 / 0.821 | `bag-voxelrcnn-ros-g1v6x` (8) |
| **V2X mAP** | **0.743 / 0.726** | **0.694 / 0.676** | single members, before fusion |

In the kept zips, fusion adds 0.017 (B) to 0.031 (A) mAP over the best single member per class on V2X, and 0.013 on LUMPI B. On LUMPI A it adds nothing, because of the frozen classes and the late-A Person ranking.
- **LUMPI:** a clean portfolio is expected near the kept zip, from -0.005 to +0.003 combined. The Person and Motorcycle gains offset Bus, Truck and Van.
- **V2X:** a clean portfolio is expected 0.025 to 0.035 mAP below the kept zip, so combined about 0.875 to 0.885 against 0.904. That would still be well above the next V2X team (0.8112 on Nov 2; the final-phase board is hidden).

#### 3.2 Corpus effect, same architecture: `g1-v4`/`g1-v5` to `g1-v6`

Each cell is the AP change on realval A / B, 8 views.

| Track, member | Change |
|---|---|
| LUMPI Voxel R-CNN | Person **+0.132 / +0.102**; Car -0.022 / -0.037; Truck -0.037 / +0.104; Van -0.088 / 0.000 |
| LUMPI PV-RCNN++ | Person **+0.149 / +0.109**; Car -0.024 / -0.037; Van -0.085 / 0.000 |
| LUMPI VoxelNeXt | Person **+0.171 / +0.078**; Bicycle +0.080 / +0.027; Motorcycle -0.083 / -0.007 |
| LUMPI bags (Voxel R-CNN, PV-RCNN++) | Person +0.121 to +0.127 / +0.073 to +0.091; Car -0.027 to -0.031 / -0.025 to -0.042 |
| V2X Voxel R-CNN | vehicle -0.033 / -0.004; pedestrian +0.020 / -0.018; truck +0.059 / +0.104 |
| V2X PV-RCNN++ | vehicle -0.018 / +0.007; pedestrian +0.006 / -0.026; truck -0.015 / -0.018 |
| V2X VoxelNeXt | vehicle +0.022 / +0.044; pedestrian -0.017 / -0.061; truck +0.055 / +0.064 |
| V2X Voxel R-CNN bag | vehicle -0.026 / -0.022; pedestrian +0.002 / -0.038; truck -0.023 / -0.011 |

**Reading.**
- Label-free placement **helps LUMPI Person by a large margin** on every architecture. It costs LUMPI Car 0.01-0.04 and Van 0.05-0.09; the Van loss comes from the size-based class rule.
- On V2X the corpus effect is mixed and small per architecture. So most of the V2X gap in Section 3.1 is ensemble depth: the kept zip fuses three bags of `g1-v4`/`g1-v5` draws, and the clean pool has one Voxel R-CNN bag and one VoxelNeXt bag.
- V2X pedestrian is the one class where the clean corpus is weaker on B for most architectures.

#### 3.3 LUMPI label conventions: the test window is late Measurement 4

The 100 test frames are M4 6497-8109. Legal M4 label rows (frames 0-6399), by class:

| Class | Frames < 3200 (objects; median l x w x h; labels) | Frames >= 3200 (objects; median; labels) |
|---|---|---|
| Bicycle | 44; 2.26 x 0.93 x 2.00 m; manual | 34; 1.94 x 0.82 x 1.86 m; manual |
| Motorcycle | 2; 2.36 x 0.95 x 1.73 m | 5; 1.84 x 0.77 x 1.73 m; **all automatic** |
| Bus | 5; 12.15 x 2.86 x 3.32 m | 23; median 7.12 m long; **all automatic**. 296 rows are a 5.5 x 0.39 x 2.13 m object, which is not a bus |
| Truck | 33; 10.80 x 2.89 x 3.80 m | 33; 8.35 x 2.93 x 3.09 m |
| Van (SDK "unknown") | 112; **0.84 x 0.70 x 1.93 m (person-sized)** | 114; **4.84 x 2.03 x 2.04 m (van-sized)** |

The test set has Person 512, Car 1,258, Bicycle 82, Motorcycle 27, Bus 25, Truck 192 and Van 79 boxes.

**Reading.**
- The test-window conventions follow late M4: the class labeled Van holds vans, Bicycle boxes are shorter, and Bus and Motorcycle labels are automatic and partly not real buses.
- Late-A (M4 4800-6399, our most test-like subset) holds only **11 Bus and 4 Motorcycle boxes**. These classes cannot be validated where it matters. This is why local rare-class gains did not transfer (`s9iu`: projection +0.0101, server -0.0025).
- Real labels may serve only as size statistics and validation. **Never** turn the positions of real objects (static or not) into boxes or rules; that would be fitting to real labels, against audit rule b and the clarification.

#### 3.4 Size gap between `g1-v6` and real labels

Median l x w x h of `g1-v6` training boxes (800 sampled frames) against realval A+B labels; the ratio is synthetic over real.

| Class | Synthetic (m) | Real (m) | Ratio l / w / h |
|---|---|---|---|
| LUMPI Person | 0.71 x 0.71 x 1.90 | 0.80 x 0.77 x 1.89 | **0.89** / 0.92 / 1.00 |
| LUMPI Car | 4.61 x 1.93 x 1.55 | 4.51 x 1.98 x 1.68 | 1.02 / 0.97 / **0.92** |
| LUMPI Bicycle, Motorcycle | | | 0.99-1.01 (sizes already come from real quantiles) |
| LUMPI Bus | 10.50 x 3.27 x 3.26 | 8.31 x 2.75 x 3.12 | **1.26** / 1.19 / 1.05 |
| LUMPI Truck | 5.96 x 2.35 x 2.56 | 8.23 x 2.68 x 3.09 | **0.72** / 0.88 / 0.83 (the size class rule turns UT transporters into Truck) |
| LUMPI Van | 5.57 x 2.15 x 2.05 | 4.25 x 1.94 x 1.83 | **1.31** / 1.11 / 1.12 |
| V2X vehicle | 4.67 x 2.03 x 1.52 | 4.68 x 2.07 x 1.67 | 1.00 / 0.98 / **0.91** |
| V2X pedestrian, truck | | | 0.99-1.04 |

**Reading.**
- At IoU 0.5, these gaps alone still leave an IoU of about 0.75 or more for a box with the right centre.
- Their cost comes through the centre: a detector trained on boxes of the wrong size places the centre of a partly seen object wrongly, which is what the anchored calibration corrects after detection.
- Statistical normalization in training (lever C1) targets the same bias where it is learned. Its candidates are LUMPI Car height, Person length and width, Van and Bus length, and V2X vehicle height.
- LUMPI Truck is a convention question (Section 3.3), not a scale question.

#### 3.5 Compute and storage

- **GPUs.** 8 A6000s run as two 4-GPU workers.
- **Training time per member.** PointPillars 1.1-2.1 h; Voxel R-CNN 2.9-5.2 h; PV-RCNN++ 2.9-4.1 h; VoxelNeXt 1.7-3.8 h; DSVT 5.5-7.5 h.
- **Validation tuning.** About 3 h per LUMPI member and about 1.2 h per V2X member. A 12-view job adds 80 min on LUMPI and 27 min on V2X.
- **Builds.** A new 10,000-frame draw takes about 20 min of CPU. A portfolio build takes 2-3.5 h.
- **Budget.** About 300 worker-hours remain until Nov 14, enough for 50-60 member trainings with tuning across both tracks. Tuning, not training, is the binding constraint, as in S9.
- **Weight averaging needs no retraining.** Epoch 11-40 checkpoints are kept for every member.
- **Disk.** 386 GB free (95% used). That is enough for about 20 new corpora; old corpora are not deleted.

### 4. Hypotheses

- **H1 (compliance at small cost).** A clean portfolio from the existing `g1-v6` members ties the kept zip on LUMPI within ±0.005 combined. On V2X it loses about 0.02-0.03 combined.
- **H2 (V2X depth).** The V2X gap is ensemble depth, not the corpus. Two more clean draws, with PV-RCNN++ and Voxel R-CNN bags over three or four draws and 12-view TTA, recover half or more of it. Evidence: seed bags +0.0079 on the V2X server (S6), draw bags +0.002 to +0.011 each (S7.4).
- **H3 (sizes in training).** Real box-size statistics are now explicitly allowed. Applied in training as statistical normalization, they raise AP@0.5 through better centres where the sizes differ most (Section 3.4): LUMPI Car, Person, Van and Bus, and V2X vehicle height. The S9 test-time calibration (3D@0.7 +0.034 on V2X) shows the size bias is real.
- **H4 (weight averaging).** Averaging the last checkpoints of a member is a small, free robustness gain under domain shift.

### 5. Levers, ranked by value per effort

The literature column refers to Section 11. Expected gains are combined-score estimates, discounted by the transfer ratios seen so far.

| # | Lever | Mechanism | Our evidence | Expected gain | Cost | Rules |
|---|---|---|---|---|---|---|
| A1 | **Clean portfolio `C0`** from the existing members | route, fusion of up to 3 members, z and size calibration, budget, copies and sparse stage, all rebuilt from scratch on clean members only | Section 3.1 | LUMPI -0.005 to +0.003; V2X -0.02 to -0.03 | about 0.5 day of CPU; no GPU | required by the clarification |
| A2 | **V2X realism frames from `g1-v6`** | held-out R +0.0035 (S9 rule 4 passed) | LUMPI `g1-v6` frames transferred at 0.35x | about +0.0005 | none | allowed (realism calibration) |
| B1 | **V2X clean draws and bags** | 2 more draws (`g1-v6d3`, `g1-v6d4`); PV-RCNN++, Voxel R-CNN and VoxelNeXt bags over 3-4 draws; 12-view TTA on bag members | S6 and S7.4 bags transferred | +0.01 to +0.02 | about 12 trainings plus tuning | allowed |
| B2 | **V2X pedestrian, label-free** | re-weight the twin-map area shares towards crossings (road-line cells) and curb bands; pedestrian sizes from real statistics; more walkers per frame; standing share and group sizes (already scalars in `WalkerConfig`) chosen on proxies | S9 Person gain on LUMPI | +0.005 to +0.015 (pedestrian is about 1/3 of V2X mAP) | one corpus recipe, `g1-v7`, plus 4-6 trainings | allowed if every placement input is a scalar statistic or the twin map |
| C1 | **Statistical normalization in training** | per class, scale each synthetic object (box and points, also in the GT-sampling database) to the real size statistics during training, instead of only after detection. ROS narrows to a small range around the target | S9 calibration: 3D@0.7 +0.007 / +0.034. Section 3.4 gives the targets. Literature: SN is the strongest single cross-domain fix, and resizing boxes after detection recovers much less of it (Section 11, [1], [2]) | +0.003 to +0.01 per track | one augmentor in `bdc26` (3-5 h), 4-8 trainings | allowed: box-size statistics |
| C2 | **Sensor noise on twin points** | range jitter along each ray (about 2 cm, from the nearest sensor) on every UT point during training. Our inserted walkers and G2 actors already carry 1.5-3 cm noise; the UrbanTwin clouds carry none | not tried | +0.002 to +0.006 | one augmentor (2 h), trained together with C1 as a 2 x 2 probe | allowed: synthetic data only |
| C3 | **Box-corner regression (EdgeHead)** | regress the sensor-facing corner instead of the centre: the training-time form of the anchored calibration | the S9 calibration shows the bias | +0.002 to +0.008 | about 1 day on the two-stage heads | allowed. Optional: only if C1 passes and time remains |
| D1 | **Weight averaging** (SWA of epochs 31-40, BN statistics re-estimated on synthetic frames) | flatter optimum, more robust under shift | not tried (S6 left it out for lack of an extra schedule; the checkpoints exist now) | +0.000 to +0.005 | about 1 h per member, no training | allowed: synthetic data only |
| E1 | **LUMPI rare classes rebuilt clean** | Bicycle, Motorcycle and Bus cannot keep their frozen S8 routes, because those routes are pre-v6 members. One rule for all three, from clean candidates | Section 3.3: these classes cannot be validated in the test window | ±0.005; high variance | inside A1 | allowed; the rule treats the three classes alike, so no leaderboard per-class reading enters (audit rule d) |
| E2 | **Late-M4 size conventions** | the size calibration and statistical normalization for Bicycle, Truck and Van use late-M4 label sizes (frames 3200-6399), the window nearest the test | Section 3.3 | +0.002 to +0.008 | small | allowed: box-size statistics |
| F1 | **LUMPI EMD** | the 0.3-0.5 m height band (real 18.5% against our 7.4%), ground offset beyond 20 m, sparse cells | Proxy-to-server transfer of fine levers is 0.35x. Real-against-real EMD is 0.93-1.03 here and about 0.9-1.0 in [3], and global transforms do not lower it [3]. Our server EMD is 1.272, so at most about 0.3 EMD (+0.006 combined) is left even in theory | +0.001 to +0.002 | a corpus recipe | allowed (realism calibration) |
| G1 | **New architecture** (HEDNet, SAFDNet, LION) | stronger backbones | detector capacity ranked last in the S1-S9 retrospective; not in our checkout. No cross-domain evidence found for any of them (Section 11, [10]) | uncertain | HEDNet and SAFDNet need new code only (spconv is installed); LION may need new packages. Either way, the entrant's permission | allowed |
| (done) | GBlobs features; no GT sampling | | GBlobs lost as a member in S5 (LUMPI Person 0.189 to 0.098). The no-GT-sampling `rosn` members won Person pooled +0.016 to +0.0275 in S9, in line with the literature [6], and they are in the clean pool | inside A1 | | |
| H1 | **Realval-C** (more M5/M6 frames for validation) | more rare-class objects for selection | M5/M6 conventions differ from late M4 | low | needs a download (the entrant's permission); about 25 GB | allowed: validation |

**Not allowed, or out of bounds:**
- self-training or pseudo-labels on real or test clouds;
- TENT, AdaBN or any batch-norm statistics from real frames;
- real backgrounds or background maps;
- object points cut with real boxes;
- boxes or rules placed from real object positions;
- any per-class choice read off leaderboard numbers.

### 6. Three plans

**Plan A: Clean Final (recommended).**
- **Day 0:** A1 and A2.
- **Training waves:** worker 1 on B1 (V2X depth) from Day 0. Worker 2 on D1 (inference only), then the C1 x C2 probe from Day 0 evening. B2 from Day 1. E2 inside the next portfolio build.
- **Uploads:** C0 on Nov 8-9, then C1 and C2.
- Every upload is clean. It keeps both tracks competitive and removes the main disqualification risk.

**Plan B: Clean minimum.**
- **Work:** A1, A2 and B1 only. Training stops on Nov 11; the rest of the time goes to the report and the email.
- **Trade-off:** lower V2X recovery, the most time for the report.

**Plan C: Keep and ask (not recommended).**
- **Work:** keep `s9j`/`s9f`, send the disclosure, and wait for a ruling.
- **Risk:** the clarification already reads as the ruling. If the best submission counts, the tainted zips remain the ranked ones.

### 7. Work packages and schedule (Plan A; UTC)

| When | Work |
|---|---|
| **Sun Nov 8** | **WP0, clean check:** a tool that reads each used member's corpus card and refuses any card that lists label rows; run it on `s9j` and `s9f` (expected: refuse), then on the clean pool. **WP1, `C0` on both tracks:** a from-scratch clean build (route table, fusion of up to 3 members by the 6.0 pooled rule, LUMPI late-A Person ranking and Van judge, z calibration, budget, copies, V2X sparse stage, size calibration re-selected, copy fit, kit check, scorecard, reproduction scripts, projection). **WP2:** V2X `C0` takes the `g1-v6` frames. **GPU W1, worker 1:** V2X draws `g1-v6d3` and `g1-v6d4`, with PV-RCNN++ and Voxel R-CNN on each. **Worker 2:** D1 weight-averaging probes on 4 members per track (inference only). **WP6:** the C1 statistical-normalization and C2 range-jitter augmentors, with unit tests; then the 2 x 2 probe (Voxel R-CNN, V2X first because it trains fastest). **The entrant** sends the email (Section 9). |
| **Mon Nov 9** | **Upload 2 (both tracks): `C0`.** It is the first scored clean system and calibrates H1. **GPU W2:** the C1 x C2 probe on LUMPI Voxel R-CNN and on PV-RCNN++ (both tracks); V2X 12-view tuning of the new bag members. **WP3:** the `g1-v7` V2X walker recipe, chosen on synthetic checks and realism proxies only (S9 rule 5). |
| **Tue Nov 10 to Wed Nov 11** | **GPU W3:** `g1-v7` V2X members (Voxel R-CNN, PV-RCNN++, VoxelNeXt) and a bag partner; LUMPI C1 members; D1 on the strongest new members. **WP4:** `C1` portfolios with every member that passes the member check. |
| **Wed Nov 11 to Thu Nov 12** | **Upload 3: `C1`**, if its projection against `C0` is positive and it passes the final pooled gate. |
| **Thu Nov 12 to Fri Nov 13** | **GPU W4,** the last wave: bag partners of whatever passed. Training stops on **Nov 13, 18:00 UTC**. **WP5:** `C2` portfolios, kit check, reproduction dry runs on idle GPUs. |
| **Sat Nov 14** | **Upload 4, V2X: `C2`** (or the best clean version again if Q3 says last counts). Release (tag named by the entrant). |
| **Sun Nov 15** | **Upload 4, LUMPI: `C2`**, before Nov 16 04:59 UTC. The report is due Nov 15. |
| reserve | **Upload 5:** held for a re-upload if Q3 says the last submission counts. |

### 8. Pre-registered rules (written 2026-11-08, before any S10 run)

1. **Clean members only.** Every member of an S10 system trains on a corpus whose card lists no real label rows (the `g1-v6` family and any `g1-v7`), or on UrbanTwin data alone. The realism frames come from such a corpus, and from one that trains a used member. WP0's tool checks this before packaging, and a failing system is not uploaded.
2. **Class gate.** The 6.0 pooled rule applies: pooled A+B P(gain) >= 0.9, and neither split down by more than 0.005. The train-split result is reported (audit rule a). LUMPI Person is ranked by late-A (R5), and LUMPI Van is judged on early-A and late-A (S6). A new version needs projection > 0 against the previous clean version, then the final pooled gate.
3. **Rare classes (LUMPI Bicycle, Motorcycle, Bus).** One rule for all three: each takes the clean candidate (single member or fusion) with the best pooled A+B AP. No class is treated differently because of a leaderboard result.
4. **Members first.** A new member enters only after the S6 member check against the best clean member of its family. A failed member is recorded and not retried with other settings.
5. **Generator choices** (the `g1-v7` walker shares, statistical-normalization targets) are made on synthetic checks, realism proxies and real-size statistics only. Detection results never choose a generator parameter after its members are trained.
6. **Realism frames.** S9 rule 4 applies: held-out R must gain at least 0.003, with CD, MMD and FPD not worse, and V2X CD below 2.0.
7. **Kit.** The LUMPI kit prediction holds at most 38,466 boxes (S9 rule 1(b)), and the kit check takes under 400 s.
8. **Uploads.**
   - At most one per day per track (the platform limit), and never a system that fails rule 1.
   - The projection is recorded before each upload.
   - The choice between scored clean systems uses the combined score only (audit rule d).
9. **Weight averaging and statistical normalization** count as new members under rule 4: they must pass the member check on their own.

### 9. Compliance, the email and the report

**Real-data uses of a clean entry.** Each fits a category the organizers named on 2026-11-07:

| Use | Data | Category |
|---|---|---|
| Realval A/B, every selection and calibration grid | LUMPI M4 0-6395 and M5/M6 samples; V2X non-forbidden infrastructure frames of all splits | validation and model selection |
| Size quantiles, class-rule thresholds, walker box mixture, anchored size calibration | legal real labels | box-size statistics |
| Walker range histogram (10 bins) | legal real labels | a position statistic; disclose |
| Density priors, OS1-64 beam table, realism proxies | unlabelled legal frames | realism calibration |
| Sensor metadata (LUMPI M4 extrinsics) | `meta.json` | sensor description |

**Email (the entrant sends; draft to follow on request).**
- The disclosure items (a)-(i) shrink to one past-tense item: the label-placed walkers of pre-v6 corpora, used by the development entries and the F2 uploads.
- Every other use maps to the table above.
- **Requests:** rank the clean final uploads (named by submission ID once scored); answer Q3; confirm that a 10-bin walker range histogram counts as a statistic.

**Report.**
- Rewrite paper Sections 3.1-3.3 around the table above.
- Remove "disclosed to the organizers" until the email is sent.
- Describe the switch to label-free placement as a result: on LUMPI it raises Person by 0.07-0.17 AP across architectures (Section 3.2).

### 10. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Clean V2X stays 0.02-0.03 below 0.904 | Still about 0.06 above the best V2X competitor seen (Nov 2). Spend B1 first. |
| Clean LUMPI lands below 0.5428 | The margin to the next team was 0.031 on Nov 2. E2 and C1 are the LUMPI levers. |
| The best submission counts and a pre-v6 zip stays best | The email asks the organizers to rank the clean uploads. The entrant may also check whether CodaBench lets a participant remove a final-phase submission; that is the entrant's decision. |
| Tuning throughput | Tune the 8-view set first, and run 12-view only for members that pass. |
| Disk at 95% | New corpora only; delete nothing without the entrant's say. |

### 11. Literature behind the levers

A read-only scan on 2026-11-08. Numbers are as the papers report them. Items marked "unverified" were not checked against the paper.

1. **Statistical normalization (SN).** Wang et al., "Train in Germany, Test in the USA", CVPR 2020 (arXiv 2005.08139).
   - Waymo to KITTI, Car AP3D@0.7: 13.2 direct, **47.1 with SN**.
   - Resizing the predicted boxes after detection gave far less, because the learned centres stay biased.
   - Also ST3D, CVPR 2021 (arXiv 2103.05346): SECOND-IoU source-only 27.48, SN 59.20.
   - This supports lever C1, and explains why our test-time calibration moved 3D@0.7 more than 3D@0.5.
2. **Random object scaling can hurt.** Eskandar et al. 2024 (arXiv 2402.17562): ROS lowered Waymo to nuScenes. This matches our S5 result (V2X gain, LUMPI flat). C1 therefore narrows ROS around the SN target instead of stacking both.
3. **The same challenge, ECCV 2026 DriveX instance (LUMPI track).** Luo et al., arXiv 2609.07590 (verified 2026-11-08).
   - Results: combined 0.4692, mAP 0.126, R 0.9035.
   - Methods: DSVT plus PointPillars specialists, density matching to the 50k-point test frames, rare-class copy-paste, class-aware routing and fusion, selective box-size calibration, radial-density matching for realism.
   - EMD carried most of their realism penalty. Two real-against-real subsamples give EMD of about 0.9-1.0 (the agent's reading; unverified).
   - Our pipeline already covers each of these levers. Their test set and scores are not comparable with ours.
4. **UrbanTwin dataset paper.** Shahbaz and Agarwal, IEEE OJ-ITS 2026 (arXiv 2509.06781).
   - CARLA twins with the real sensors' channels, FOV and pose.
   - No ray drop, range noise or intensity model is described.
   - Pedestrians are left out because CARLA's human meshes are poor for LiDAR.
   - Real mean box volume is above the synthetic one (unverified figure).
   - This supports C2 (noise on twin points) and our walker engine.
5. **Sensor noise.** Huch et al., IEEE T-IV 2023 (arXiv 2303.01899): 2 cm range jitter in simulation raised AP3D@0.7 on real data, PointRCNN 38.2 to 41.6 and PointPillars 13.4 to 18.8. Random 20% point dropout did not help. This supports C2.
6. **GT sampling across domains.** Eskandar et al. 2024: GT sampling lowered PV-RCNN cross-domain AP (20.36 to 15.86). Our no-GT-sampling `rosn` members agree.
7. **Density and beam augmentation.**
   - LiDAR Distillation, ECCV 2022 (arXiv 2203.14956).
   - The augmentation part of PDDA, ECCV 2024 (arXiv 2311.10845); its test-time adaptation is not allowed here.
   - Low priority for us: our walkers use the real sensors' beam tables, and the density priors match the real point density.
8. **EdgeHead.** Zhang et al. 2024 (arXiv 2407.04061; venue unverified): regressing the sensor-facing corner improved cross-domain AP3D@0.7, most of all with SN. This is lever C3.
9. **Weight averaging.** SWAD, NeurIPS 2021 (arXiv 2102.08604), for 2D domain generalization. No 3D-detection study was found, so lever D1 is a cheap probe, not an expected gain.
10. **Newer backbones.** HEDNet and SAFDNet (one OpenPCDet codebase), LION, Voxel Mamba and PTv3. No cross-domain evidence was found for any of them. Robustness tracks clean accuracy (Dong et al., CVPR 2023, arXiv 2303.11040). This supports G1's low rank.
11. **Asset fidelity.** ReSimAD, ICLR 2024 (arXiv 2309.05527): sensor-matched, higher-fidelity simulation gave large cross-domain gains (figures from a secondary summary; unverified). It is the direction of B2, at a cost beyond this week for full assets.
12. **Rolling-shutter motion of actors during the sweep.** Manivasagam et al., ICCV 2023. It matters for matching detector outputs, but no AP figure was found. Not planned.
13. **Generative LiDAR models** (RangeLDM, LiDM, DUSty v2). These are fitted to real clouds, so they are conditional under the rules, and they need new packages. Not planned.

### 12. Decisions for the entrant

1. Adopt Plan A: every remaining upload is clean.
2. Send the email of Section 9 (I can draft it).
3. Optional downloads: the organizers' two mapping tables (a cross-check), and realval-C frames (lever H1).
4. Optional new code for lever G1 (new packages need the entrant's permission).

### 13. Results

#### 13.1 Day 0: Plan A started (2026-11-08, 03:40-04:00 UTC; before any S10 result)

Run directory: `$BDC_DATA/logs/s10` (`STATUS.md`, `events.txt`; event times are server time, UTC-8).

**WP0, the clean check.** `common/tools/clean_check.py` reads each member's corpus card and implements rule 1. A corpus fails if its `real_data_use` names label rows, its walkers come from the label prior, or its G2 clutter is anchored at real walker positions. A union corpus is checked part by part.
- **Kept zips:** both fail. `routed-g22` has 10 of 12 member models not clean; `routed-g19` has 6 of 6, plus its `g1-v5` frames.
- **Clean pool:** LUMPI 35 folders and V2X 17 (V2X `pointpillars-g1` and `g1v2` use free placement and no real data).

**WP1, the `C0` builds** (`common/pipeline/s10_clean_portfolio.sh`, tag `c0`, folder `routed-c0` on both tracks).
- **LUMPI:** started 03:45 UTC, with 33 folders (79 members) and the S9 `g1-v6` frames (the same 50 ids as `s9j`).
- **V2X:** waits for 12-view tuning of 7 clean members. Only 2 of 17 had 12-view outputs. It then builds three clean draw bags: `bag-pvrcnnpp-ros-g1v6x` (new: the two PV-RCNN++ draws, which S9 never bagged) and the existing Voxel R-CNN and VoxelNeXt bags with 12 views. It uses the S9 `g1-v6` frames (S9 rule 4 passed, Section 14.3 of the S9 record).

**W1 (lever B1).**
- V2X draws `g1-v6d3` (seed 3234) and `g1-v6d4` (seed 4234) use the S9 flags unchanged, 10,000 frames each. They took 3 minutes.
- Six draw members follow: Voxel R-CNN, PV-RCNN++ and VoxelNeXt on each new draw, training seed 666.
- The first PV-RCNN++ run ran out of GPU memory next to a 12-view job (45 GB). Training now uses GPUs 1, 3, 5 and 7 until the 12-view jobs end; the second worker then takes GPUs 0, 2, 4 and 6.

**C1 and C2, pre-registered here before any probe result.**
- **Statistical normalization targets** (`CLASS_CENTER`, real median over `g1-v6` median, l / w / h). Every object of a listed class is normalized, with narrow jitter (0.95-1.05 for l and w, 0.97-1.03 for h).
  - **LUMPI**, from late-M4 legal labels (frames 3200-6399; lever E2): Person 1.127 / 1.070 / 0.968; Car 0.941 / 1.005 / 1.058; Bicycle 0.975 / 0.976 / 0.974; Van 0.869 / 0.944 / 0.995.
  - **V2X**, from realval A+B labels: vehicle 1.002 / 1.020 / 1.099; pedestrian 0.959 / 1.000 / 1.006.
  - **Not normalized:** Bus (the late-M4 rows hold the junk object), Motorcycle (39 late rows) and Truck (a convention question, Section 3.3).
- **Range jitter:** sigma 0.02 m along each ray from the nearest sensor (LUMPI: the five M4 sensor origins; V2X: the frame origin). It runs before any world transform.
- **Probe:** a 2 x 2 per track. The base is the parent member: V2X `voxelrcnn-ros-g1v6`, LUMPI `voxelrcnn-rosf-g1v6`. The arms are `-sn-`, `-rj-` and `-snrj-`, all on `g1-v6` with seed 666.
- **Decision rule:** each arm is a new member under rule 4, so it must pass the S6 member check against its parent. A lever is kept for the C1 waves only if its single arm passes on at least one class without failing another.
- **Checks so far:** unit tests in `common/tests/test_s10.py` (5 passed). A 20-iteration smoke run of both `-snrj-` configs on GPU passed.

**D1, weight averaging (no training).**
- `common/tools/swa_ckpt.py` writes the mean of epochs 31-40 as a new member (`-swa-`). Batch-norm statistics are averaged too and not re-estimated.
- Members: V2X `voxelrcnn-ros-swa-g1v6` and `pvrcnnpp-ros-swa-g1v6`; LUMPI `voxelrcnn-rosf-swa-g1v6` and `pvrcnnpp-ros-swa-g1v6`.
- Weights move a median of 1.5% from epoch 40, as expected at the end of a one-cycle schedule.
- The same rule 4 member check as the probes applies.

**A build change made before any `C0` result.**
- `select --calibrated` runs a z-calibration search for every member and class, about a minute each: roughly 10 h for 79 LUMPI members.
- `C0` therefore ranks members uncalibrated, as the S8.2 `extend` step already did for every S9 member. It then runs `calibrate --pooled` once per class on the routed and fused predictions.
- The LUMPI build restarted at about 03:57 UTC.

#### 13.2 `C0` built on both tracks (2026-11-08, 05:20-07:00 UTC)

**Three build faults, fixed before any `C0` number was read.**
1. **Calibration after fusion (LUMPI, 05:26).** `calibrate` reads the route-only merge. merge_card applies the class-level `calibration` to routed classes only; a fused class takes its members' own calibrations, and these are empty after an uncalibrated select. Bicycle's routed member is not in its fused set, so the merge had no Bicycle boxes and the step crashed. Fix: `common/pipeline/s10_portfolio_tail.sh` (new; every step after the card) calibrates only the classes that are not fused. Fused classes therefore carry no z calibration in `C0`. Earlier route-level gains were small (Person +0.0001, Car +0.002 on A), and the anchored size calibration still moves heights.
2. **The V2X card lost its route (05:47).** The card kept `routed-g19`'s `budget:` above `route:`. The budget writer cuts the card at `budget:`, so route, fusion and calibration were dropped. The card was reset to its 44 members, and the build ran again from `select`. The result was identical, because select and fuse are deterministic. `s10_clean_portfolio.sh` now drops the reference budget on V2X and hands steps 3-8 to a snapshot of the tail script.
3. **Scorecard realism.** `--realism-from` the reference failed, because the S9 references' scorecards hold no realism. Both scorecards were re-run with `--realism` (exact, on the zip), and the tail script now does that.

**LUMPI `routed-c0`** (13 member models, all clean; the same 50 `g1-v6` realism frames as `s9j`).

| Class | Source |
|---|---|
| Person | fusion `vrrosn6_tta12` + `bvrrosf6x_tta` @0.7 (late-A ranking) |
| Car | fusion `vrrosf6_tta12` + `bvrrosn6x_tta` + `vrrosf6j_tta12` @0.7 |
| Bicycle | fusion `ppros6d2_tta` + `dsrosf6_tta12` + `pvros6j_tta12` @0.5 |
| Motorcycle | fusion `vnrosn6_tta12` + `vnrosf6d2_tta` @0.7 |
| Bus | `ppros6_tta` |
| Truck | fusion `bpvros6x_tta` + `pvros6j_tta` @0.7 |
| Van | `dsrosf6_tta12` (Van judge) |

- **Post-processing:**
  - z calibration: none (Bus and Van were tried; neither passed).
  - Score floors and copies: `routed-g22`'s S8.3 values.
  - Person copy threshold: re-fitted to 0.7531 under rule 7.
  - Size calibration kept for Car (dl -0.2, dw +0.08, dh +0.07; A +0.0029, B +0.0052) and Person (dh +0.03; A +0.0045, B +0.0046).
- **Validation:**
  - mAP: A 0.4147, B 0.2388, late-A 0.3537.
  - Exact R on the zip 0.9399, the same frames as `s9j`.
  - Kit check: 24,088 boxes, 213 s.
- **Against `routed-g22` (`s9j`), set B paired bootstrap:**
  - mAP +0.0018 (P(gain) 0.65).
  - Gains: Bicycle +0.022, Motorcycle +0.035, Truck +0.033.
  - Losses: Bus -0.073, Car -0.005.
  - Person +0.001 and Van -0.0004.
  - Rule 6 projection: -0.0002 combined, so about level with 0.5428.
- **Zip:** `model-lumpi-track/routed-c0/submissions/2026-11-07_c0/lumpi_s10_submission.zip`, md5 `1de9f12c1f18d045e5b0c05e08a2f793`.

**V2X `routed-c0`** (5 member models, all clean; the `g1-v6` frames, which S9 rule 4 passed).
- **Every class is fused:**
  - vehicle: `bvrros6x_tta12` + `dsros6_tta` @0.5;
  - pedestrian: `vrros6d2_tta12` + `vrros6_tta12` + `vrrosf6_tta12` @0.5;
  - truck: `vrrosf6_tta12` + `bvrros6x_tta` @0.7.
- The new PV-RCNN++ bag and the VoxelNeXt bag were not chosen.
- **Post-processing:**
  - Score floors: vehicle 0.01, pedestrian 0.05, truck 0.05.
  - Pedestrian tail copies: r 0.15, n 4.
  - Sparse demotion: 6, 6 and 8.
  - Size calibration for vehicle (dl -0.3, dh +0.03; A +0.0035, B +0.0012).
- **Validation:**
  - mAP: A 0.728, B 0.706.
  - Exact R on the zip 0.9426, against 0.9366 for `routed-g19` (+0.0060).
  - Kit check: 41,225 boxes, 250 s.
- **Against `routed-g19` (`s9f`), set B:**
  - mAP -0.0205 (P(gain) 0.00).
  - Pedestrian -0.060, vehicle -0.002, truck +0.000.
  - Rule 6 projection: -0.0090 from mAP, +0.0024 from R (0.4 x 0.0060), so about **0.897** against 0.9038.
- **Zip:** `model-v2x-track/routed-c0/submissions/2026-11-07_c0/v2x_s10_submission.zip`, md5 `c70e8a341b7647d8ae7712a09ba1baf6`.

**What `C0` says about H1.**
- **LUMPI:** the clean system is level with the kept zip. The `g1-v6` Person and rare-class members make up for the label-placed walkers; Bus is the one large loss.
- **V2X:** the whole clean gap is pedestrian (-0.06 B). The label-placed walkers of `g1-v3` to `g1-v5` mattered most there. This makes B2 (the `g1-v7` walker recipe) and B1 (pedestrian-strong draw bags) the V2X levers for `C1`.
- **Uploads:** `C0` is upload 2 on both tracks (Section 7), the first scored clean systems.

#### 13.3 `C0` scored (final phase, upload 2; the entrant's scoring output, 2026-11-08)

| Track | Submission | Combined | mAP 3D@0.5 | R | CD / EMD / FPD | vs the kept zip |
|---|---|---|---|---|---|---|
| LUMPI | **1042287** | **0.5408** | 0.194973 | 0.9342 | 1.510 / 1.272 / 0.430 | -0.0020 against `s9j` 0.542809 (mAP -0.0023; R equal, same frames) |
| V2X | **1042294** | **0.888471** | 0.5976 | 0.940605 | **1.844** / 1.110 / 0.748 | -0.0153 against `s9f` 0.903777 (mAP -0.0213, detection -0.0183; R **+0.0074**) |

Records: `model-<track>-track/routed-c0/submissions/2026-11-07_c0/codabench_<id>.json`, the manifests and the `leaderboard` rows of both registries. The public board shows a bot check and was not read.

**What the scores say.**
- **H1 holds.** The clean LUMPI system is within 0.002 of the kept zip. The clean V2X system loses 0.015, inside the predicted 0.02-0.03 once the realism gain is counted.
- **Projection error.**
  - LUMPI: projected -0.0002, scored -0.0020.
  - V2X: the mAP part was projected -0.0090 (rule 6 shrinks validation gains by 0.6) and scored -0.0183. The V2X loss transferred at about 1.2x the mean A/B validation loss.
  - **Reading:** the 0.6 shrink fits gains chosen on validation (selection bias), not a systematic loss such as removing the label-placed walkers. The S10 projections compare clean versions with each other, where the shrink still applies.
- **V2X realism.** The `g1-v6` frames lower CD from 1.986 to 1.844, which moves the CD < 2 condition from a 0.014 margin to 0.156. They also lower EMD (1.182 to 1.110) and FPD (1.468 to 0.748). The local held-out gain (+0.0060) understated the server gain (+0.0074).
- **Per-class server numbers** are in the records and select nothing (audit rule d). The V2X diagnosis (pedestrian) was made on validation before the score (Section 13.2).
- **The clean baseline** for every later S10 version: **LUMPI 0.5408, V2X 0.8885.** Three uploads are left per track.

#### 13.4 The final-phase leaderboard (the entrant's screenshots, server time 2026-11-08 06:45 and 06:52 CST)

Read from the entrant's screenshots of the Results tab (Final phase); the public API was not read. R is derived from the shown EMD and FPD as 1 - (EMD/5 + FPD/50)/4.

**LUMPI (43 participants; 06:45 CST)**

| # | Team | ID (date, CST) | Combined | mAP 3D@0.5 | 3D@0.7 | CD | EMD | FPD | R |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **KarmaRV** | **1042287** (11-08 06:42, `C0`) | **0.5408** | 0.195 | 0.0992 | 1.510 | 1.272 | 0.430 | 0.9342 |
| 2 | lukefinigan | 1041567 (11-07 23:25) | 0.5342 | 0.1877 | 0.0321 | 1.486 | 1.266 | 0.674 | 0.9333 |
| 3 | dipper13579 | 1040958 (11-07 13:45) | 0.5217 | 0.1689 | 0.0592 | 0.755 | 1.100 | 0.531 | 0.9423 |
| 4 | sadbodh | 1038056 (11-06 10:55) | 0.5198 | 0.1676 | 0.0675 | 1.564 | 1.177 | 0.177 | 0.9403 |
| 5 | StagAI | 1037920 (11-06 09:43) | 0.4697 | 0.1098 | 0.0218 | 1.412 | 1.198 | 0.225 | 0.9390 |

**V2X (45 participants; 06:52 CST)**

| # | Team | ID (date, CST) | Combined | mAP 3D@0.5 | 3D@0.7 | CD | EMD | FPD | R |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **KarmaRV** | **1038966** (11-06 21:21, `s9f`) | **0.9038** | 0.6189 | 0.1983 | 1.986 | 1.182 | 1.468 | 0.9332 |
| 2 | sadbodh | 1039213 (11-06 23:24) | 0.855 | 0.5573 | 0.1534 | 1.827 | 1.092 | 0.402 | 0.9434 |
| 3 | dipper13579 | 1041736 (11-08 00:55) | 0.7816 | 0.4679 | 0.0994 | 0.698 | 0.946 | 0.268 | 0.9514 |
| 4 | linyongchun | 1040931 (11-07 13:12) | 0.7271 | 0.4005 | 0.1122 | 0.487 | 0.804 | 0.051 | 0.9596 |
| 5 | lukefinigan | 1042183 (11-08 05:47) | 0.6919 | 0.379 | 0.018 | 1.709 | 1.335 | 2.826 | 0.9191 |
| 6 | tokyovo | 1036509 (11-06 01:07) | 0.6685 | 0.3515 | 0.0652 | 2.540 | 1.372 | 1.466 | 0.918 (from the combined score; the formula gives 0.924) |

**Readings.**
1. **Which upload the board shows.** LUMPI lists `C0` (1042287, 0.5408), uploaded three minutes earlier, not `s9j` (1038963, 0.5428). So the board shows a team's newest upload, not its best. At 06:52 CST V2X still listed `s9f`. `C0` V2X (1042294) has a higher ID than the LUMPI upload, so it was likely still being scored. Until the organizers answer Q3, **S10 reads the final ranking as "the last upload counts"** (rule 13). The entrant can confirm on the V2X board that 1042294 replaced 1038966.
2. **LUMPI is the close race.** Our clean lead is **0.0066** over lukefinigan, whose mAP (0.1877) is near ours (0.195). LUMPI work therefore moves up in the GPU order (Section 15).
3. **V2X lead.** Clean `C0` (0.8885) leads sadbodh (0.855) by 0.034.
4. **Realism is our weakest term.**
   - LUMPI: our R (0.9342) is the lowest of the top four. dipper13579 reaches 0.9423 at EMD 1.100.
   - V2X: our `C0` R (0.9406) is below sadbodh's (0.9434), dipper13579's (0.9514) and linyongchun's (0.9596 at EMD 0.804).
   - These EMDs show that 1.10 on LUMPI and about 0.80 on V2X can be reached. The Section 14 cap (+0.006 on LUMPI) understated the V2X headroom.
   - Value at the competitors' levels: LUMPI +0.008 R = **+0.003 combined**; V2X +0.019 R = **+0.008**.
   - How those teams build their frames is unknown. Very low CD (0.49-0.76) suggests frames very close to real clouds. Increment 5 (Section 15.6) is the legal route for us.
5. **CD above 2 is penalized, not zeroed.** The scorer adds (CD - 2)/28 to the mean of the four terms (Section 15.6). That reproduces tokyovo's R of 0.918 at CD 2.54.
6. **Both phase pages show the end as November 15, 10:59 PM CST = 2026-11-16 04:59 UTC.** Section 7 had V2X closing at 2026-11-15 04:59 UTC. The schedule in Section 15 uses the pages; the entrant may confirm on the Phases tab.

### 14. The plan after `C0` (2026-11-08, 13:00-14:30 UTC; written before any W2 result)

#### 14.1 Where the points are

| | LUMPI | V2X |
|---|---|---|
| Clean baseline (`C0`) | 0.5408: detection term 0.2785 (mAP 0.195), realism 0.9342 | 0.8885: detection term 0.8537 (mAP 0.598), realism 0.9406 |
| To pass the kept zip | +0.0020 | +0.0153 (about +0.018 mAP) |
| Value of +0.01 AP on one class | +0.0012 combined (7 classes) | +0.0029 combined (3 classes) |
| Largest validation loss | Bus and the rare classes (not validatable in the test window, Section 3.3) | pedestrian on B: ranking 0.287, localization 0.272, misses 0.050 |
| Realism headroom | EMD 1.272 against a real-against-real floor of about 0.95 at the scorer's 10,000 points: at most +0.006 even in theory | CD 1.844 (margin 0.156); EMD 1.110 |

**V2X pedestrian false positives** (validation, `routed-c0`; validation and box-geometry checks only):
- At score >= 0.5, 65% of unmatched pedestrian boxes are static structures, repeating at the same cells across a scene. The S2 oracle put the cost at 0.09 AP on B.
- **Points above the box top** (0.2-2.0 m above it, inside 90% of its footprint) separate the low-score false positives: at score >= 0.1, 36% of false boxes and 3.4% of true ones have any; at >= 0.3, 13.9% against 1.9%. Above 0.5 the share is about 1-2% on both sides. So the confident false positives are not tall poles or trunks: they are objects of walker height or lower (what they are is not measured).
- **`g1-v6` V2X has no map-placed structures** (S9 left them out because they raised FPD, a realism reason only). Its Poisson(30) clutter of poles, trees, bollards, boxes, bins and barriers is map-anchored. LUMPI `g1-v6` has both, and its Person gain over the pre-v6 corpora was +0.07 to +0.17.

#### 14.2 What the research adds (2026-11-08; two read-only scans, numbers as reported, "unverified" where not checked)

- **The other entrant's reports** (Luo et al., arXiv 2609.07590 LUMPI and 2609.07608 V2X): LUMPI combined 0.4692 (mAP 0.126, R 0.9035, EMD 1.857, CD 2.18), V2X 0.742 (mAP 0.452). Their largest LUMPI step was a box-size calibration (+0.0135 mAP), which we have. Class routing helped them (+0.0093); uniform ensembles added false positives. Their scorer description: both sides masked to [-40, 40]² x [-5, 5] m, 10,000 points sampled per side.
- **Hard negatives for pedestrians.** False-positive sampling (arXiv 2403.02639) raised KITTI pedestrian moderate AP by 4.8-9.1 (PV-RCNN, SECOND, CenterPoint). This supports B2a (structures in V2X `g1-v7`). Mining false positives on real frames, or pasting real points, is not allowed.
- **Pedestrian box conventions.** PCGen (arXiv 2210.08738): CAD pedestrians with pose filtering and box loosening went from 6.56 to 54.31 3D AP@0.5 on real Waymo (real data 61.62). Our walker box-to-body margins are already scalars chosen on realval-A (S9); the size part is in C1.
- **Visibility cues.** Free-space and visibility features raised nuScenes pedestrian AP from 38.2 to 45.7 (Hu et al., CVPR 2020). The cheap form is a demotion stage on validation (lever V5); a learned rescorer trained on synthetic true and false boxes is the full form (lever X1).
- **Weight averaging.** Model soups gave about +1 AP on COCO detectors (arXiv 2012.12645). No domain-shift evidence was found, but our first checks pass (Section 14.3).
- **Realism.** EMD at the scorer's sample size cannot go below about 0.95 (empirical W1 converges as n^(-1/3)). Global transforms and per-point moves are not allowed or did not transfer for the other entrant. Our density prior is already the thinning model the literature recommends.
- **Grey, not used without the organizers' answer:** locating real static structure (poles, trees) in unlabelled real clouds to place synthetic negatives there ("twin completion"); any new test-time hedge such as low-score cross-class duplicates. Both go into the email as questions.

#### 14.3 Experiments in progress (state at 14:30 UTC)

| Item | Lever | State | Result |
|---|---|---|---|
| V2X `voxelrcnn-ros-swa-g1v6` | D1 | tuned | **passes** vehicle (8-view, +0.005 pooled) and truck (8-view, +0.008), P(gain) 1.00 |
| V2X `pvrcnnpp-ros-swa-g1v6` | D1 | tuned | **passes** vehicle (plain +0.005, 8-view +0.003) and pedestrian (plain +0.004) |
| LUMPI `voxelrcnn-rosf-swa-g1v6` | D1 | tuned | **passes** Person, Bicycle, Bus, Truck (plain) and Person, Car (+0.016 pooled), Bicycle, Bus (8-view) |
| LUMPI `pvrcnnpp-ros-swa-g1v6` | D1 | tuned | passes Person (plain) and Van; 8-view Truck -0.010 and Bus -0.008 pooled: mixed |
| 15 more averaged members (every leaf member `C0` uses: 12 LUMPI, 3 V2X) | D1+ | created 14:40 UTC, queued for tuning; a third tuning worker added | member checks follow |
| V2X `voxelrcnn-ros-snrj-g1v6` | C1 + C2 | tuned | **passes pedestrian only** (+0.004 to +0.006 pooled); truck -0.016 to -0.046, vehicle -0.026 on B. Usable as a pedestrian member |
| V2X `voxelrcnn-ros-sn-g1v6`, `-rj-` | C1, C2 alone | sn training (worker A), rj queued | decide the levers (Section 13.1 rule) |
| LUMPI `voxelrcnn-rosf-snrj-g1v6` | C1 + C2 | trained, tuning | |
| LUMPI `-sn-`, `-rj-` | C1, C2 alone | queued | |
| V2X draw 3: Voxel R-CNN, PV-RCNN++, VoxelNeXt | B1 | VR tuned, PV tuning, VN training (worker B) | VR **passes** vehicle (8-view, +0.021 pooled); truck swings from -0.050 (plain) to +0.008 (8-view): a bag partner, as planned |
| V2X draw 4: the same three | B1 | queued | |
| V2X `g1-v7` (structures 30, seed 7234) and `voxelrcnn-ros-g1v7` | B2a | corpus built and clean (05:07 server time); the member is first in the train queue | |
| Overhead-points demotion on validation (`C0` final predictions; a box with >= k points 0.2-2.0 m above its top ranks last) | V5 | measured | **V2X pedestrian:** k 5 gives A +0.0029, B +0.0017; k 10 gives +0.0023, +0.0020 (about +0.0006 combined); enters `C1` through rule 11. **LUMPI Person:** A -0.058 (k 1) to -0.013 (k 5), B within +0.001: real LUMPI pedestrians often stand under trees or roofs; **dropped** for LUMPI |

#### 14.4 Levers for C1 and C2, ranked by value per GPU hour

| # | Lever | Track | Mechanism | Evidence | Expected | Cost | Rule |
|---|---|---|---|---|---|---|---|
| D1+ | **Weight averaging everywhere** | both | average epochs 31-40 of every clean member that enters a portfolio, then bag the averaged draws | three passes (V2X Voxel R-CNN and PV-RCNN++, LUMPI Voxel R-CNN) and one mixed (LUMPI PV-RCNN++), 14.3 | +0.002 to +0.006 per track | about 1.2 h (V2X) or 3 h (LUMPI) of tuning per member, no training | member check, rule 4 |
| B1 | V2X draw bags over 4 draws (Voxel R-CNN, PV-RCNN++, VoxelNeXt), 12-view | V2X | ensemble depth | S6, S7.4 bags transferred | +0.005 to +0.015 | running | rule 4 |
| B2a | **V2X `g1-v7`: map-placed structures as negatives** | V2X | the twin lacks the structures where confident pedestrians fire; LUMPI has them | 14.1, 14.2 | +0.003 to +0.010 | probe 3 h; 3 members if it passes | rule 4 on the probe; frames stay `g1-v6` |
| V5 | **Overhead-points demotion** | V2X pedestrian (LUMPI dropped, 14.3) | a box with points above its top ranks last, as the S7 sparse stage does | 14.1, 14.3: +0.002 to +0.003 AP on both splits | about +0.0006 | a stage in `route_predictions.py` (3 h) | rule 11 |
| C1/C2 | statistical normalization and range jitter | both | per the Day 0 probe | snrj: pedestrian only | per arm | running | Section 13.1 rule |
| L1 | LUMPI draw 3 for the Person and Car members (Voxel R-CNN rosn and rosf, PV-RCNN++) | LUMPI | depth for the two classes that validate | S9 bags | +0.001 to +0.003 | 3 trainings (13 h) | rule 4 |
| X1 | Synthetic-trained visibility rescorer (gradient-boosted, few monotone features) | both | false positives that look like walkers but leave the wrong shadow | Hu et al. 2020 | +0.002 to +0.008, uncertain | 8-12 h of code | stretch; rule 11 |
| F2 | V2X realism frames from the union of draws 1-4 | V2X | a larger pool for the S9 selection | local held-out R | +0.000 to +0.001 | CPU | S9 rule 4, CD < 1.9 |

**Dropped or held:** rare-class relabelling by size at inference (the `s9iu` lesson: +0.010 projected, -0.0025 scored; rule 3 stays); EMD work beyond F2 (capped and transfers at 0.35x); new architectures (no evidence, new code); SPG and new walker meshes (days of work, aimed at misses, which are rare).

#### 14.5 Incremental plans on top of Plan A

Each increment can be adopted alone. The cost is in GPU worker-hours (two 4-GPU workers, about 250 worker-hours until training stops on Nov 13, 18:00 UTC).

1. **Increment 1, V2X pedestrian (B2a, V5, the snrj member).** If the `g1-v7` probe passes pedestrian, train PV-RCNN++, VoxelNeXt and a second Voxel R-CNN draw on `g1-v7` (about 10 worker-hours) for a `g1-v7` bag. V5 enters as a pre-registered stage (k from {3, 5, 10, 20} on A, rule 11). Expected +0.005 to +0.015 on V2X.
2. **Increment 2, weight averaging everywhere (D1+).** Average every draw member and bag the averages; no training. Expected +0.002 to +0.006 on V2X; LUMPI if its checks pass.
3. **Increment 3, LUMPI depth (L1).** About 13 worker-hours. Expected +0.001 to +0.004. (V5 does not apply to LUMPI, 14.3.)
4. **Increment 4, stretch (X1, F2).** Only once 1-3 are built, by Nov 11.

**Recommended:** all of 1-3 (about 25 worker-hours of training plus tuning, inside the budget), and 4 only if there is time.

#### 14.6 Schedule (UTC)

| When | GPU | Builds and uploads |
|---|---|---|
| Sun Nov 8 | W1 finishes: sn, rj, d3, the `g1-v7` probe | member checks; V5 on `C0` |
| Mon Nov 9 | d4 draws; LUMPI sn, rj; the `g1-v7` members if the probe passes; SWA of every new member | `C1` build (V2X) starts once d3 and d4 are tuned |
| Tue Nov 10 | LUMPI draw 3; `g1-v7` bag partners | `C1` V2X; `C1` LUMPI build |
| **Wed Nov 11** | W3 | **Upload 3: `C1` on both tracks** (V2X first), if the projection against `C0` is positive and the final pooled gate passes |
| Thu Nov 12 to Fri Nov 13 | W4: partners of whatever passed; training stops **Nov 13, 18:00** | `C2` builds; kit checks; reproduction dry runs |
| **Sat Nov 14** | none | **Upload 4, V2X: `C2`** |
| **Sun Nov 15** | none | **Upload 4, LUMPI: `C2`**; the report |
| reserve | | **Upload 5** per Q3 (re-upload the best clean version if the last counts) |

#### 14.7 Rules added before any W2 result

10. **Projection against `C0`.** Rule 6 as before, against `C0`'s local scores. A new version needs projection > 0 and the final pooled gate. A loss from a systematic change is not shrunk (13.3).
11. **New post-processing stages** (V5, X1) follow the S7 sparse rule: one parameter per class, chosen on realval-A, kept only with pooled P(gain) >= 0.9 and neither split down by more than 0.005.
12. **`g1-v7` is a training corpus.** V2X realism frames stay `g1-v6`-family frames (rule 6), unless a re-selection passes S9 rule 4 with CD below 1.9.

### 15. S10 wave 1: increments 1-4 adopted (2026-11-08)

**Decision.** On 2026-11-08 the entrant adopted increments 1-4 of Section 14 as the first wave of S10 work ("proceed by adopting the 1-4 proposal under the first wave of work in S10"). This section is the readable brief behind that decision, with the leaderboard reading of Section 13.4 folded in. Increment 5 (realism, 15.6) was added the same day.

#### 15.1 The rules, in brief (the organizers' clarification of 2026-11-07, both tracks)

| Code | What the clarification says |
|---|---|
| **T** | The detector is trained on synthetic data only. |
| **L** | Real labels, and object points cut out with real boxes, never enter training. |
| **V** | Non-forbidden real frames may be used for validation, model selection and box-size statistics (labels allowed). |
| **C** | Unlabelled real clouds may be used to calibrate the realism of the synthetic data. |
| **D** | Every use of real data is described in the report. |

#### 15.2 What S1-S10 taught us, and how it shapes the wave

1. **Ensemble depth transfers.** Seed bags gave +0.008 on the V2X server (S6), draw bags +0.002 to +0.011 (S7.4).
2. **Corpus fixes transfer.** Label-free walkers gave LUMPI Person +0.07 on the server (S9).
3. **Fine post-processing transfers at 0.3-0.6x.** Gains picked on validation shrink on the server.
4. **Rare-class picks did not transfer** (`s9iu`: +0.010 projected, -0.0025 scored).
5. **Today's evidence.** Weight averaging passes on 3 of 4 members. 65% of confident false V2X pedestrians sit on static structures. The board shows LUMPI as the close race (lead 0.0066) and realism as our weakest term on both tracks (13.4).

#### 15.3 The four increments

| # | Technique | Evidence (ours; literature) | Expected combined | Cost | Rules |
|---|---|---|---|---|---|
| **1. V2X pedestrian** | (a) **`g1-v7`**: map-placed static structures (hedges, fences, walls, shelters, facades) in V2X training scenes as unlabelled negatives; realism frames stay `g1-v6`. (b) The SN + range-jitter member enters for pedestrian only. (c) **V5 overhead-points demotion** (rule 11). | Ours: 65% of confident false pedestrians are static structures; LUMPI's corpus with structures gained Person +0.07 to +0.17; (b) +0.004 to +0.006 pooled; (c) +0.002 to +0.003 AP on both splits. Literature: false-positive sampling, +4.8 to +9.1 AP on KITTI pedestrians (arXiv 2403.02639) | V2X **+0.003 to +0.012** | probe: one 3 h training; 3 more members (about 10 worker-hours) if it passes | **T, L:** synthetic scenes, positions from the twin's own map. **V:** the demotion threshold and size targets come from validation and size statistics. **D** |
| **2. Weight averaging everywhere** | The mean of the epoch 31-40 checkpoints of each member (SWA); bags of the averaged draws | Ours: V2X Voxel R-CNN vehicle +0.005, truck +0.008; V2X PV-RCNN++ vehicle +0.005, pedestrian +0.004; LUMPI Voxel R-CNN Car +0.016, Bicycle +0.012, Person +0.007; LUMPI PV-RCNN++ mixed. Literature: SWAD (arXiv 2102.08604); model soups about +1 AP on COCO (arXiv 2012.12645) | **+0.002 to +0.006 per track** | no training; about 40 h on the tuning workers | **T:** synthetic-trained weights only. **V:** the member check |
| **3. Ensemble depth** | V2X: draws 3 and 4 (Voxel R-CNN, PV-RCNN++, VoxelNeXt), 4-draw bags with 12-view TTA. LUMPI: draw 3 for the Person and Car members (Voxel R-CNN rosn and rosf, PV-RCNN++), 3-draw bags | Ours: the S6 and S7.4 transfers; V2X draw-3 Voxel R-CNN vehicle +0.021 pooled; `C0` V2X lost mostly through shallower fusion | V2X **+0.005 to +0.012**; LUMPI +0.001 to +0.003 | V2X about 9 worker-hours; LUMPI about 13 | **T:** new synthetic draws of the same clean recipe |
| **4. Stretch** | (a) **X1**, a small rescorer for walker boxes, trained only on synthetic detections, with visibility features (points above, free space through the box, height above ground, points against the count expected at that range). (b) **F2**, V2X realism frames re-selected from the 40,000-frame pool of draws 1-4 | Literature: visibility features +7.5 AP on nuScenes pedestrians (Hu et al., CVPR 2020). Ours: the overhead feature alone gives +0.002; realism re-selection transferred at 0.35x on LUMPI (1.2x on V2X for `g1-v6`) | +0.000 to +0.005 (uncertain); +0.000 to +0.002 | 8-12 h of code on CPU | **T:** trained on synthetic only. **C:** frames chosen against unlabelled real proxies |

#### 15.4 Pros and cons

| # | Pros | Cons and risks |
|---|---|---|
| 1 | Targets the one measured V2X gap with a synthetic-only fix. The probe answers in about 6 h. | Structures may also hide real pedestrians standing by walls. The probe may fail (S9 left structures out of V2X for realism; the frames stay `g1-v6`). V5 only helps the low-score tail. |
| 2 | Free: every member keeps the checkpoints. Strong on 3 of 4 checks. | Gains can shrink inside fusion, which already averages. 12-view TTA needs a GPU without training (45 GB), so averaged members use 8 views until training stops. |
| 3 | The best-transferring lever on V2X. New draws cost minutes of CPU. | Most GPU hours. Returns fall off past 3-4 draws. Single draws swing per class (draw-3 truck -0.05), so only bags are used. |
| 4 | No detector retraining. Aims at the ranking loss (0.29 of pedestrian AP). | The rescorer learns synthetic false positives, which differ from real ones. Small measured signal so far. Competes with 1-3 for time. |

#### 15.5 Not pursued

| Idea | Reason | Rule |
|---|---|---|
| Self-training, pseudo-labels, test-time adaptation | the detector would learn from real clouds | not allowed (T) |
| Placing negatives where real unlabelled clouds show poles and trees ("twin completion") | the strongest false-positive fix in the literature, but its positions come from real clouds | grey: email question (c) |
| New test-time hedges (low-score duplicates across classes) | a metric hedge | disclosure needed; not without the entrant's approval |
| LUMPI rare-class relabelling by size at inference | cannot be validated in the test window | the `s9iu` lesson; rule 3 |
| Generative LiDAR models fitted to real clouds | real clouds would reach training through the generator | not allowed (T) |
| New backbones | no cross-domain evidence; new code and packages | allowed, low value |

#### 15.6 Increment 5, realism (adopted by the entrant on 2026-11-08: "Add increment 5")

**The scorer, exactly** (`common/bdc26/realism.py`, bit-for-bit against the kit, `test_official_parity.py`): both clouds are concatenated over the 50 frames and masked (V2X [-40, 40]² x [-8, 2] m, LUMPI [-40, 40]² x [-5, 5] m). One seeded generator (1234) draws 10,000 points per side. **EMD is the square root of W1 with a Euclidean cost**, so our LUMPI 1.272 means points must move 1.62 m on average (dipper13579: 1.21 m) and V2X 1.110 means 1.23 m (linyongchun: 0.65 m). **FPD is the Frechet distance of 3-D Gaussians of xyz**: means and covariances only. R = 1 - mean of four clipped terms: CD in [2, 30], MMD in [0, 0.5], EMD in [0, 5], FPD in [0, 50]. So **CD above 2 adds (CD - 2)/28**, which reproduces tokyovo's 0.918 exactly (13.4 reading 5).


| Item | Content |
|---|---|
| **Why now** | The leaderboard (13.4) shows realism as our weakest term on both tracks. At the levels other teams reach, it is worth about +0.003 combined (LUMPI) and +0.008 (V2X). That matches the detection increments, with no GPU training. |
| **5a. Scorer replica** | Mask [-40, 40]² x [-5, 5] m and sample 10,000 points per side, as the other entrant's report describes, averaged over seeds. Check it against our 7 server realism scores (each with known frames) before using it. CPU, about 4 h. |
| **5b. Attribution** | Where our frames' mass differs from the held-out proxies after the mask: range bins, height bands, BEV cells, ground share. This tells 5c what to fix. CPU, about 3 h. |
| **5c. Levers** | (i) Frame selection on the replica's EMD over a larger pool (draws 1-4, `g1-v7`). (ii) A return-probability (thinning) model by range, ring and ground flag, fitted to unlabelled proxies, applied in a new generator draw that also trains a used member (rules 1 and 6). (iii) Twin completion for realism only after the organizers answer question (c). |
| **Expected** | V2X +0.002 to +0.006; LUMPI +0.001 to +0.003. |
| **Risks** | LUMPI proxy-to-server transfer has been 0.35x. V2X CD must stay below 2 (now 1.844). Structures raised FPD on V2X in S9. |
| **Rules** | **C** allows unlabelled real clouds for realism calibration. The frames must come from a corpus that trains a used member (rules 1 and 6). No test frame is used for calibration, and no real point is copied. |

**5a result: do the local proxies predict the server?** Every frame set with both a server R and a local R (the mean over held-out proxies 4 and 5, exact EMD):

| Track | Frames | Local R | Server R | Local - server |
|---|---|---|---|---|
| V2X | `g1-v3` | 0.9190 | 0.9203 | -0.0013 |
| V2X | `g1-v4` | 0.9254 | 0.9268 | -0.0014 |
| V2X | `g1-v5` | 0.9366 | 0.9332 | +0.0034 |
| V2X | `g1-v6` | 0.9426 | 0.9406 | +0.0020 |
| LUMPI | `g1-v2` | 0.9053 | 0.8912 | +0.0141 |
| LUMPI | `g1-v4` | 0.9337 | 0.9323 | +0.0014 |
| LUMPI | `g1-v6` | 0.9399 | 0.9342 | +0.0057 |

- **V2X:** steps transfer at 0.6x to 1.2x, and `g1-v3` to `g1-v6` overall at **0.86x** (local +0.0236, server +0.0203). V2X realism can be developed on the proxies.
- **LUMPI:** the coarse step (`g1-v2` to `g1-v4`: ground, density, real-size actors) transferred at 1.45x. The fine step (`g1-v4` to `g1-v6`) transferred at 0.31x. LUMPI realism needs coarse changes, and a local gain is discounted to 0.3x unless the change is coarse.

**5b result: where our EMD comes from** (`common/tools/s10_emd_attribution.py`, exact transport on the scorer's subsamples; logs in `$BDC_DATA/logs/s10/realism`).
- **V2X:** shares by range band and height band match the real proxies within 0.015. The cost is in the BEV layout: the cell x -10..0, y 0..10 holds 14.7% of our points against 11.1-11.7% real and causes 22% of W1, and the neighbouring cells are short. Half our points move under 0.52 m, the furthest 10% over 3.3 m.
- **LUMPI:** the typical point moves 1.0 m. The ground band carries 42% of W1: about 4% too few points below z -2 m and 2-3% too many at -2 to -1 m. S9's smooth ground surface changed realism by 0.0000, so this is not a smooth height offset.

**The floor, real against real** (proxy 4 against proxy 5, the same tool):

| | EMD | CD | R | Median move |
|---|---|---|---|---|
| V2X real vs real | **0.751** | 0.33 | 0.9617 | 0.17 m |
| V2X `C0` vs real | 1.08-1.11 | 1.80-1.83 | 0.942-0.944 | 0.52 m |
| LUMPI real vs real | **0.980** | 0.64 | 0.9498 | 0.54 m |
| LUMPI `C0` vs real | 1.18-1.20 | 1.47-1.49 | 0.939-0.940 | 1.0 m |

**Why the floor is so low.** The median distance from a point to the nearest point of the other real proxy is **0.000-0.002 m on V2X** and 0.004-0.03 m on LUMPI. Ours is 0.22-0.33 m on V2X and 0.13-0.73 m on LUMPI. A fixed sensor returns nearly the same points from the same static scene in every frame, so two real frame sets coincide to the centimetre. A twin rendered in CARLA cannot do that, whatever its density. The V2X competitor at EMD 0.80 and CD 0.49 (13.4) sits at this real-against-real floor. How they built their frames is not known, and we draw no conclusion about it.

**5c bound: thinning does not help** (`common/tools/s10_thinning_bound.py`: keep probabilities fitted on proxies 1-3, scored on 4-5).

| Cells | V2X R (held-out) | LUMPI R (held-out) |
|---|---|---|
| BEV 10 m | +0.0018 to +0.0024, but CD rises to 2.02-2.07 (penalized) | -0.0006 to -0.0009 |
| BEV 5 m | -0.005 to -0.006 | |
| BEV and height bands | -0.014 to -0.015 | -0.013 to -0.024 |

Reweighting density, at any resolution, does not move EMD toward the floor, and it raises FPD. This confirms S9.

**Revised increment 5 (2026-11-08, after 5a-5c).**

| Lever | Status | Expected |
|---|---|---|
| Thinning or density-prior refit | **dropped** (bound above) | none |
| Frame selection on the exact scorer over the V2X pool of draws 1-4 (fit proxies 1-3, held-out 4-5, S9 rule 4), merged with F2 | **kept**; with the `C1` V2X build | V2X +0.0004 to +0.0012 combined |
| Twin completion: synthetic structures where unlabelled real clouds show static surfaces the twin lacks (the 0.6-0.7 m distances above 0.5 m on LUMPI) | **waits for the organizers' answer to question (c)** | LUMPI and V2X, perhaps +0.001 to +0.003 each |
| Real background points in frames or training | **not allowed** (T; frames must be synthetic and train a used member) | |

The realism gap to the leaderboard's best R is mostly not reachable with synthetic frames. Increment 5 shrinks to the frame selection, plus twin completion if the organizers allow it.

#### 15.7 Wave 1 actions (launched 2026-11-08, 13:00-15:30 UTC)

| Increment | Action | State |
|---|---|---|
| 1a | `g1-v7` built and clean (structures 30, seed 7234); `voxelrcnn-ros-g1v7` first in the train queue | **Decision point:** its member check against `voxelrcnn-ros-g1v6`. If it passes pedestrian without failing another class: PV-RCNN++, VoxelNeXt and a second Voxel R-CNN draw on `g1-v7` |
| 1b | `voxelrcnn-ros-snrj-g1v6` passed pedestrian; it enters `C1`'s route search as a pedestrian candidate | done |
| 1c | V5 stage in `route_predictions.py` (`overhead` mode, `overhead_demotion` card key, part of the final gate's class configuration), two unit tests; V2X step in `s10_portfolio_tail.sh` after the sparse stage | built. **Dry run on a scratch copy of V2X `C0`:** pedestrian k 5 kept (A +0.0029, B +0.0017, pooled +0.0027 at P(gain) 1.00; the next k, 10, gains +0.0022, so no lone spike). It enters `C1` through the V2X tail script |
| 2 | 15 averaged members of every `C0` leaf member, queued for tuning; a third tuning worker | tuning; member checks as each finishes |
| 3 | V2X draw 4 members queued. LUMPI `g1-v6d3` (S9 G5 flags, seed 3234) building, with `voxelrcnn-rosn-g1v6d3`, `voxelrcnn-rosf-g1v6d3` and `pvrcnnpp-ros-g1v6d3`. **Order:** the `g1-v7` probe, then the two LUMPI Voxel R-CNN draws (LUMPI is the close race), then the probes, then LUMPI PV-RCNN++, then V2X draw 4 | building |
| 4 | X1 and F2 code after `C1` is built | Nov 10 |

#### 15.8 Schedule (UTC; both tracks close 2026-11-16 04:59 per the phase pages)

| When | Work | Uploads |
|---|---|---|
| Sun Nov 8 | wave 1 launched (15.7) | (`C0` scored) |
| Mon Nov 9 | member checks; the `g1-v7` decision; SWA of new draw members; V2X `C1` build once the draw-3 bags and averaged members are tuned | |
| Tue Nov 10 | LUMPI `C1` build; X1 and F2 code; increment 5 if adopted | |
| **Wed Nov 11** | | **Upload 3: `C1`, both tracks** (rules 10 and 13) |
| Thu Nov 12 to Fri Nov 13 | wave 2: partners of whatever passed; training stops **Nov 13, 18:00** | |
| **Sat Nov 14** | `C2` builds, kit checks, reproduction dry runs | **Upload 4: `C2`, both tracks** |
| **Sun Nov 15 to Mon Nov 16 04:59** | report | **Upload 5 (reserve):** re-upload the best scored clean version if `C2` scored lower (rule 13) |

#### 15.9 Rule added with the leaderboard reading

13. **The last upload counts until the organizers say otherwise.** A version is uploaded only if its projection beats the best scored clean version (rule 10). If an upload scores below that version, the reserve upload re-submits the best scored clean zip unchanged before the close. The last upload of each track must be our best scored clean zip.

#### 15.10 Wave 1 results so far (2026-11-08, to 23:40 UTC)

**Member checks** (rule 4: pooled A+B P(gain) >= 0.9 and neither split down more than 0.005; "8v" is 8-view TTA). Logs: `$BDC_DATA/logs/s10/member_checks/w1_batch1.log` and `w1_batch2.log`.

| Track | Member (against) | Lever | Passes (pooled AP gain) | Notable losses |
|---|---|---|---|---|
| V2X | `voxelrcnn-ros-swa-g1v6` (`voxelrcnn-ros-g1v6`) | SWA | vehicle 8v +0.005, truck 8v +0.008 | none |
| V2X | `pvrcnnpp-ros-swa-g1v6` (`pvrcnnpp-ros-g1v6`) | SWA | vehicle +0.005, pedestrian +0.004, vehicle 8v +0.003 | none |
| V2X | `voxelrcnn-rosf-swa-g1v6` (`voxelrcnn-rosf-g1v6`) | SWA | vehicle +0.026, pedestrian +0.002, truck +0.019; vehicle 8v +0.020, pedestrian 8v +0.0025 | none |
| V2X | `dsvt-ros-swa-g1v6` (`dsvt-ros-g1v6`) | SWA | all six; truck 8v +0.022 | none |
| V2X | `voxelrcnn-ros-swa-g1v6d2` (`voxelrcnn-ros-g1v6d2`) | SWA | vehicle +0.003 | truck 8v -0.006 |
| V2X | `voxelrcnn-ros-g1v6d3` (`voxelrcnn-ros-g1v6`) | draw 3 | vehicle 8v +0.021 | truck plain -0.050 |
| V2X | `pvrcnnpp-ros-g1v6d3` (`pvrcnnpp-ros-g1v6`) | draw 3 | vehicle +0.024, vehicle 8v +0.0185, pedestrian 8v +0.0070 | truck -0.025 plain, -0.010 8v |
| V2X | `voxelnext-ros-g1v6d3` (`voxelnext-ros-g1v6`) | draw 3 | all six; truck +0.092 plain, +0.058 8v | none |
| V2X | `voxelrcnn-ros-g1v7` (`voxelrcnn-ros-g1v6`) | `g1-v7` structures (B2a probe) | pedestrian +0.0127 (A +0.019, B +0.001) | pedestrian 8v B -0.007; truck -0.025 plain; vehicle 8v -0.007 (B -0.030) |
| V2X | `voxelrcnn-ros-g1v6d2` (`voxelrcnn-ros-g1v6`) | draw 2 (draw-variance reference) | pedestrian +0.0121, truck 8v +0.026 | vehicle 8v B -0.026 |
| V2X | `voxelrcnn-ros-snrj-g1v6` (`voxelrcnn-ros-g1v6`) | SN + jitter | pedestrian +0.0058, pedestrian 8v +0.0042 | truck -0.046 / -0.016; vehicle -0.026 on B |
| V2X | `voxelrcnn-ros-sn-g1v6` (`voxelrcnn-ros-g1v6`) | SN | pedestrian +0.0049 (P 0.93) | truck -0.093 plain, -0.038 8v; vehicle -0.011, -0.007 (all P 0.00) |
| V2X | **`bag-pvrcnnpp-ros-g1v6x3`** (`bag-pvrcnnpp-ros-g1v6x`) | 3-draw bag | **all six**: vehicle +0.020 / +0.013 8v, pedestrian +0.009 / +0.0053 8v, truck +0.018 / +0.014 8v | none | `C1` candidate, every class |
| V2X | **`bag-voxelnext-ros-g1v6x3`** (`bag-voxelnext-ros-g1v6x`) | 3-draw bag | **all six**: vehicle +0.022 / +0.013, pedestrian +0.014 / +0.006, truck +0.051 / +0.035 | none | `C1` candidate |
| V2X | `bag-voxelrcnn-ros-g1v6x3` (`bag-voxelrcnn-ros-g1v6x`) | 3-draw bag | vehicle +0.019 / +0.0096 8v | pedestrian 8v B -0.009 (pooled +0.0009, n.s.) | vehicle candidate |
| V2X | `voxelrcnn-ros-rj-g1v6` (`voxelrcnn-ros-g1v6`) | range jitter | **none** (vehicle pooled +0.012 but B -0.028 / -0.008 8v) | truck -0.049 plain (B -0.070); every class down on B | **lever not kept** (Section 13.1 rule) |
| V2X | `voxelrcnn-ros-swa-g1v6d3` (`voxelrcnn-ros-g1v6d3`) | SWA | vehicle +0.0065 / +0.0037 8v | truck plain -0.014 | vehicle |
| V2X | `bag-voxelrcnn-ros-swa-g1v6x3` (`bag-voxelrcnn-ros-g1v6x3`) | bag of averaged draws 1-3 | vehicle +0.0043 / +0.0024 8v | none | vehicle candidate; pedestrian and truck flat |
| V2X | `pvrcnnpp-ros-swa-g1v6d3` (`pvrcnnpp-ros-g1v6d3`) | SWA | pedestrian +0.0050 / +0.0029 8v, truck +0.015 / +0.004 8v, vehicle 8v +0.002 | none | strong; a bag of averaged PV-RCNN++ draws follows |
| V2X | `pvrcnnpp-ros-swa-g1v6d2` (`pvrcnnpp-ros-g1v6d2`) | SWA | vehicle +0.009 / +0.0047 8v | none | vehicle |
| V2X | **`bag-pvrcnnpp-ros-swa-g1v6x3`** (`bag-pvrcnnpp-ros-g1v6x3`, the plain 3-draw bag) | bag of averaged draws 1-3 | pedestrian +0.0023 / **+0.0023 8v**, truck +0.0023 / +0.0025 8v, vehicle 8v +0.0014 | none | lead V2X PV-RCNN++ candidate, every class |
| V2X | `voxelrcnn-ros-g1v6d4` (`voxelrcnn-ros-g1v6`) | draw 4 | pedestrian +0.0087 plain (+0.0060 8v, P 1.00 but B -0.007) | truck plain -0.031 (P 0.00); vehicle B -0.019 / -0.029 8v | bag partner |
| V2X | `voxelrcnn-ros-swa-g1v6d4` (`voxelrcnn-ros-g1v6d4`) | SWA | vehicle +0.0072 / +0.0018 8v, pedestrian +0.0020 / +0.0020 8v | truck plain B -0.056 | vehicle and pedestrian |
| V2X | `bag-voxelrcnn-ros-g1v6x4` (`bag-voxelrcnn-ros-g1v6x3`) | 4-draw bag | vehicle +0.0046 plain, **pedestrian +0.0054 / +0.0016 8v** | truck plain -0.0034 (P 0.01, A -0.007) | pedestrian candidate; **the vehicle gain fell from +0.019 (draw 3) to +0.005** |
| V2X | `bag-voxelrcnn-ros-swa-g1v6x4` (`bag-voxelrcnn-ros-g1v6x4`) | bag of averaged draws 1-4 | vehicle +0.0029 / +0.0030 8v, truck +0.0066 plain | pedestrian flat | vehicle and truck candidate |
| V2X | `pvrcnnpp-ros-g1v6d4` (`pvrcnnpp-ros-g1v6`) | draw 4 | vehicle +0.025 / +0.024 8v | pedestrian -0.005 / -0.004 8v (P 0.05), truck 8v -0.014 | bag partner |
| V2X | `bag-pvrcnnpp-ros-g1v6x4` (`bag-pvrcnnpp-ros-g1v6x3`) | 4-draw bag | vehicle +0.010 / +0.0046 8v, pedestrian +0.0032 plain | pedestrian 8v flat, truck 8v -0.0039 (P 0.09) | vehicle; **returns falling** (draw 3 added +0.020 vehicle) |
| V2X | `pvrcnnpp-ros-swa-g1v6d4` (`pvrcnnpp-ros-g1v6d4`) | SWA | vehicle +0.0044, truck 8v +0.0068 | truck plain -0.041 (B -0.052) | bag partner |
| V2X | **`bag-pvrcnnpp-ros-swa-g1v6x4`** (`bag-pvrcnnpp-ros-g1v6x4`, the plain 4-draw bag) | bag of averaged draws 1-4 | **pedestrian +0.0026 / +0.0057 8v** (P 1.00), truck +0.0028 plain | none | **lead V2X PV-RCNN++ pedestrian candidate** for `C1` |
| V2X | `voxelnext-ros-g1v6d4` (`voxelnext-ros-g1v6`) | draw 4 | pedestrian +0.063 / +0.022 8v, truck +0.080 / +0.050 8v | vehicle -0.0036 / -0.0029 8v (n.s.) | bag partner (VoxelNeXt draw 1 is the weak draw) |
| V2X | **`bag-voxelnext-ros-g1v6x4`** (`bag-voxelnext-ros-g1v6x3`) | 4-draw bag | **all six**: vehicle +0.0037 / +0.0020 8v, pedestrian +0.0073 / +0.0073 8v, truck +0.022 / +0.015 8v | none | `C1` candidate; **VoxelNeXt still gains from a 4th draw** (draw 5 is queued) |
| V2X | `voxelnext-ros-swa-g1v6` (`voxelnext-ros-g1v6`) | SWA | pedestrian 8v +0.0034, truck 8v +0.0038 | vehicle plain -0.0062 (B -0.020) | bag partner |
| V2X | `voxelnext-ros-swa-g1v6d2` (`voxelnext-ros-g1v6d2`) | SWA | vehicle +0.0071 / +0.0069 8v, pedestrian +0.0050 / +0.0041 8v | truck plain -0.0082 (P 0.04) | bag partner |
| V2X | `voxelnext-ros-swa-g1v6d3` (`voxelnext-ros-g1v6d3`) | SWA | vehicle plain, truck 8v +0.0093 | pedestrian -0.0056 / -0.0045 8v (P 0.00) | bag partner; the bag of averaged draws 1-4 follows draw 4's averaging |
| V2X | `voxelnext-ros-swa-g1v6d4` (`voxelnext-ros-g1v6d4`) | SWA | vehicle +0.014 / +0.012 8v, truck +0.014 plain | pedestrian 8v -0.0024 (P 0.01, B -0.006) | bag partner |
| V2X | `bag-voxelnext-ros-swa-g1v6x4` (`bag-voxelnext-ros-g1v6x4`, the plain 4-draw bag) | bag of averaged draws 1-4 | vehicle +0.0028 plain, pedestrian +0.0024 plain, truck +0.0097 / +0.0038 8v | vehicle and pedestrian 8v flat (P 0.81-0.83) | truck candidate (A/B mean 0.635 plain, 0.648 8v) |
| V2X | `voxelrcnn-ros-gblobs-g1v6` (`voxelrcnn-ros-g1v6`) | D3: GBlobs cell covariance (S5 run c on `g1-v6`) | vehicle plain +0.021 (A +0.032, **B -0.005**, at the rule's limit) | pedestrian -0.049 / -0.054 8v, truck -0.035 / -0.010 8v, vehicle 8v B -0.008 (all fail) | as in S5: weak alone, a vehicle fusion-diversity candidate; a pass by the letter of rule 4 |
| LUMPI | `voxelrcnn-rosf-swa-g1v6` (`voxelrcnn-rosf-g1v6`) | SWA | Person, Bicycle, Bus, Truck plain; Person 8v +0.0065, Car 8v +0.0157, Bicycle 8v +0.0121, Bus 8v +0.0049 | Van -0.003 |
| LUMPI | `pvrcnnpp-ros-swa-g1v6` (`pvrcnnpp-ros-g1v6`) | SWA | Person plain, Van, Van 8v | Truck 8v -0.010, Bus 8v -0.008 |
| LUMPI | `voxelrcnn-rosf-swa-g1v6d2` (`voxelrcnn-rosf-g1v6d2`) | SWA | Person, Car, Bicycle, Truck plain; Car 8v +0.0028, Bicycle 8v +0.0118, Truck 8v +0.0050 | Van -0.001 |
| LUMPI | `voxelrcnn-rosn-swa-g1v6d2` (`voxelrcnn-rosn-g1v6d2`) | SWA | Car, Bicycle, Truck plain; Person 8v +0.0011, Bicycle 8v, Bus 8v, Truck 8v (each < +0.003) | none |
| LUMPI | `voxelrcnn-rosn-swa-g1v6` (`voxelrcnn-rosn-g1v6`) | SWA | Person +0.0047, Car, Bicycle +0.012 plain; Person 8v +0.0073, Car 8v, Bicycle 8v +0.0100, Bus 8v | Truck 8v -0.0055 |
| LUMPI | `voxelrcnn-rosf-swa-g1v6j` (`voxelrcnn-rosf-g1v6j`) | SWA | Person +0.026, Car, Bicycle +0.012, Motorcycle +0.004, Van plain; Person 8v +0.0139, Bicycle 8v +0.0086, Van 8v | Truck -0.002 (not significant) |
| LUMPI | `voxelrcnn-rosn-g1v6d3` (`voxelrcnn-rosn-g1v6`; `-g1v6d2`) | draw 3 | vs draw 1: Bicycle +0.042 / +0.031 8v, Van; vs draw 2: Person 8v +0.0067, Van | vs draw 1: Person -0.014 plain, -0.005 8v; Truck -0.011 | a bag partner (its Person lies between draws 1 and 2) |
| LUMPI | **`bag-voxelrcnn-rosn-g1v6x3`** (`bag-voxelrcnn-rosn-g1v6x`, the 2-draw bag) | 3-draw bag | **Person 8v +0.0102** (A +0.008, B +0.009), Bicycle +0.022 / +0.009 8v, Car plain, Van | none | `C1` Person candidate (B Person 8v 0.229; `C0`'s fused Person B 0.232) |
| LUMPI | `pvrcnnpp-ros-swa-g1v6d2` (`pvrcnnpp-ros-g1v6d2`) | SWA | Person, Car, Bicycle plain (+0.001 to +0.003) | none | weak |
| LUMPI | `pvrcnnpp-ros-swa-g1v6j` (`pvrcnnpp-ros-g1v6j`) | SWA | Car, Bicycle, Van plain; Car 8v +0.0007 | Person 8v -0.013, Truck 8v -0.0145 | mixed: averaging PV-RCNN++ hurts LUMPI 8-view, as on draw 1 |
| LUMPI | `voxelnext-rosn-swa-g1v6` (`voxelnext-rosn-g1v6`) | SWA | Car, Bus, Truck, Van, plain and 8v (each +0.001 to +0.004) | Motorcycle 8v -0.008 (P 0.40; Motorcycle is this family's `C0` route) | small; no Motorcycle gain |
| LUMPI | `dsvt-rosf-swa-g1v6` (`dsvt-rosf-g1v6`) | SWA | Person +0.0033 / +0.0057 8v, Bicycle +0.0079 / +0.0075 8v, Truck +0.009 / +0.003 8v, Bus 8v | Car -0.008 plain; Van 8v -0.0009 (Van is this member's `C0` route, by the Van judge) | Bicycle fusion candidate; Van stays on the parent |
| LUMPI | `pointpillars-ros-swa-g1v6` (`pointpillars-ros-g1v6`) | SWA | Person +0.023 plain, Bicycle +0.006 / +0.006 8v, Bus +0.0018 plain, Van, Truck 8v | Bus 8v +0.0014 not significant (Bus is this member's `C0` route, 8v) | Bicycle candidate |
| LUMPI | `voxelnext-rosf-swa-g1v6d2` (`voxelnext-rosf-g1v6d2`) | SWA | Person +0.0069 plain, Bicycle +0.0086 / +0.0092 8v | Person 8v B -0.035; Motorcycle 8v -0.0006 (this member is in the `C0` Motorcycle fusion) | weak |
| LUMPI | **`bag-voxelrcnn-rosf-g1v6x3`** (`bag-voxelrcnn-rosf-g1v6x`, the 2-draw bag) | 3-draw bag | **11 of 14**: Person +0.0096 / +0.0037 8v, Car +0.0049 / +0.0007 8v, Bicycle +0.012 / +0.005, Motorcycle plain, Bus, Truck +0.008 / +0.008 | none | `C1` Person and Car candidate |
| LUMPI | `pointpillars-ros-swa-g1v6d2` (`pointpillars-ros-g1v6d2`) | SWA | Person, Car, Bicycle, Bus plain; Person 8v +0.0034, Bicycle 8v +0.0031, Truck 8v +0.011 | Motorcycle 8v -0.0028, Van 8v -0.0007 | Bicycle and Truck candidate |
| LUMPI | `pointpillars-rosf-swa-g1v6` (`pointpillars-rosf-g1v6`) | SWA | Person, Car, Bicycle, Truck plain; Car 8v +0.0022, **Bicycle 8v +0.019**, Bus 8v +0.0025, Van 8v | Motorcycle 8v -0.0028, Truck 8v -0.0035 | Bicycle candidate |
| LUMPI | `voxelrcnn-rosn-swa-g1v6d3` (`voxelrcnn-rosn-g1v6d3`) | SWA | Motorcycle plain, Van, Car 8v | Person -0.005 (both variants), Bicycle 8v -0.003 | weak alone |
| LUMPI | **`bag-voxelrcnn-rosn-swa-g1v6x3`** (`bag-voxelrcnn-rosn-g1v6x3`, the plain 3-draw bag) | bag of averaged draws 1-3 | Person +0.0012 / **+0.0026 8v**, Bicycle +0.004 / +0.005 8v, Van | none | lead LUMPI Person candidate: B Person 8v 0.231 (`C0` fused 0.232) |
| LUMPI | `voxelrcnn-rosf-swa-g1v6d3` (`voxelrcnn-rosf-g1v6d3`) | SWA | Car, Bicycle, Truck plain; Car 8v, Bicycle 8v | Person plain -0.006 | weak alone |
| LUMPI | **`bag-voxelrcnn-rosf-swa-g1v6x3`** (`bag-voxelrcnn-rosf-g1v6x3`, the plain 3-draw bag) | bag of averaged draws 1-3 | **Person 8v +0.0072** (B 8v 0.236, above `C0`'s fused 0.232), Bicycle +0.009 / +0.011 8v, Bus, Truck | Car plain -0.0043 (B -0.006); Car 8v -0.0008 n.s. | Person, Bicycle, Bus and Truck candidate; Car stays on the plain bag |
| LUMPI | `pvrcnnpp-ros-swa-g1v6d3` (`pvrcnnpp-ros-g1v6d3`) | SWA | **9 of 14**: Person +0.017 plain (B +0.027), Truck +0.016 / +0.006 8v, Car, Van, Person 8v, Bus 8v | none | strong (unlike the draw-1 and `j` averages) |
| LUMPI | `bag-pvrcnnpp-ros-swa-g1v6x3` (`bag-pvrcnnpp-ros-g1v6x3`, the plain 3-draw bag) | bag of averaged draws 1-3 | Person +0.0055 / +0.0032 8v, Truck +0.0067 plain, Car plain, Van | Car 8v -0.0006 (P 0.04), Truck 8v -0.0015 n.s. | fusion candidate (Person B 8v 0.218, below `C0`'s fused 0.232); Truck stays on the 2-draw bag |
| LUMPI | `voxelrcnn-rosf-sn-g1v6` (`voxelrcnn-rosf-g1v6`) | SN | Person +0.0116 / +0.0116 8v, **Car 8v +0.0105**, Bicycle +0.043 / +0.020 8v, Bus 8v +0.009, Van | **Truck -0.016 / -0.014 8v and Car plain -0.013 (all P 0.00)** | lever not kept (rule); member is a Person, Car (8v), Bicycle candidate |
| LUMPI | `voxelrcnn-rosf-snrj-g1v6` (`voxelrcnn-rosf-g1v6`) | SN + jitter | Person +0.0074, Truck, Van; Person 8v +0.0077, Car 8v +0.0137, Truck 8v +0.0103, Van 8v +0.0079 | Bicycle -0.014 plain, -0.021 8v; Car plain -0.007 |
| LUMPI | `voxelrcnn-rosf-rj-g1v6` (`voxelrcnn-rosf-g1v6`) | range jitter | Person +0.0094 plain, Bicycle +0.0124 plain, **Car 8v +0.0142** (B 0.782), Van +0.006 / +0.006 8v | **Truck -0.016 / -0.0075 8v, Motorcycle -0.020 plain, Car plain -0.0045 (all P 0.00)**, Bus 8v -0.0027 (P 0.01) | **lever not kept** (Section 13.1 rule); member is a Person, Bicycle, Car (8v) and Van candidate |
| LUMPI | `pvrcnnpp-ros-g1v6d3` (`pvrcnnpp-ros-g1v6`) | draw 3 | Car +0.0027 / +0.0134 8v, Bicycle +0.0045 / +0.0118 8v, Van | Person -0.0086 (B -0.014), Truck -0.018 / -0.019 8v, Motorcycle -0.023 plain, Bus 8v -0.008 (all P <= 0.12) | a bag partner only |
| LUMPI | `bag-pvrcnnpp-ros-g1v6x3` (`bag-pvrcnnpp-ros-g1v6x`, the 2-draw bag) | 3-draw bag | Car +0.0040 / +0.0154 8v, Bicycle +0.014 / +0.0098 8v, Van | Truck 8v -0.0023 (P 0.19; Truck is the 2-draw bag's `C0` route), Bus 8v -0.0014 (P 0.03); Person flat (+0.0004) | Bicycle and Car fusion candidate; Truck stays on the 2-draw bag |
| LUMPI | `voxelrcnn-rosn-g1v6d4` (`voxelrcnn-rosn-g1v6`) | draw 4 | Car +0.0034 / +0.0020 8v, Bicycle +0.043 / +0.032 8v, Bus +0.015 / +0.018 8v, Truck +0.017 / +0.010 8v | **Person -0.019 / -0.018 8v (P 0.00)**, Motorcycle plain -0.0098 | bag partner (a weak Person draw) |
| LUMPI | `voxelrcnn-rosn-swa-g1v6d4` (`voxelrcnn-rosn-g1v6d4`) | SWA | Person +0.0024 / +0.0013 8v, Bicycle 8v +0.0016 | Truck -0.0034 / -0.0027 8v (P <= 0.04) | bag partner |
| LUMPI | `bag-voxelrcnn-rosn-g1v6x4` (`bag-voxelrcnn-rosn-g1v6x3`) | 4-draw bag | Car +0.0049 / +0.0054 8v, Bicycle +0.0087 / +0.0061 8v, Bus, Truck +0.0079 / +0.0023 8v | **Person 8v -0.0032 (P 0.00)**: draw 4 dilutes Person | Car, Bicycle and Truck candidate; not Person |
| LUMPI | `bag-voxelrcnn-rosn-swa-g1v6x4` (`bag-voxelrcnn-rosn-g1v6x4`, the plain 4-draw bag) | bag of averaged draws 1-4 | Person 8v +0.0026, Bicycle +0.0060 / +0.0025 8v | Bus and Truck plain -0.003 (P 0.01) | Person B 8v 0.229, below `C0`'s fused 0.232 |
| LUMPI | **`voxelrcnn-rosf-gblobs-g1v6`** (`voxelrcnn-rosf-g1v6`) | D3: GBlobs cell covariance (S5 run c on `g1-v6`) | **7 of 14**: Bicycle +0.049 / +0.033 8v, **Car 8v +0.0133** (B +0.012), Person 8v +0.0058 (P 0.97), Bus 8v, Van | Car plain -0.009, Truck 8v -0.0145, Motorcycle | much stronger than S5's run a (object scaling and the clean corpus); D3 rule met: draws 2-3 train next |

**Decision under the Section 13.1 rule: V2X statistical normalization is not kept.** The single `sn` arm passes pedestrian (plain only), but it fails truck and vehicle on both variants at P(gain) 0.00. So no new V2X `sn` members are trained. The `rj` arm, next in the train queue, decides range jitter on its own. `voxelrcnn-ros-snrj-g1v6` stays a pedestrian-only route candidate under rule 4. The LUMPI `sn` and `rj` arms are queued; LUMPI `snrj` passes four classes and fails Bicycle, so its single arms decide the LUMPI levers.

**Decision under the Section 13.1 rule: V2X range jitter is not kept either** (2026-11-09, 05:30 UTC). The single `rj` arm passes no class: every class is down on B, and truck by 0.070. Both single V2X arms fail, while the combined `snrj` member passes pedestrian (+0.0058 / +0.0042 8v). So `snrj` stays a pedestrian-only route candidate, and no V2X `sn`, `rj` or `snrj` members are added. The LUMPI arms (`sn` tuning, `rj` training) decide the LUMPI levers.

**Decision under the Section 13.1 rule: LUMPI statistical normalization is not kept as a lever** (2026-11-09, 08:00 UTC). The single `sn` arm passes Person, Car (8v), Bicycle, Bus (8v) and Van, but it fails Truck on both variants and Car without TTA, all at P(gain) 0.00. The rule keeps a lever only if its arm passes a class *without failing another*, so no SN members are trained on new draws. The member itself enters the `C1` route search for the classes it passes (rule 4), like `snrj`. Reading: Truck is not normalized, and normalizing Car and Van sizes probably moves some vehicles across the size-based Truck boundary (not measured). The rule is conservative here; a per-class use is still possible through the route.

**V2X draw 6: not added** (2026-11-09, 14:30 UTC; the wave 3 rule: "V2X draw 6 only if the draw-4 bags still gain"). The Voxel R-CNN 4-draw bag still gains pedestrian (+0.0054 plain, +0.0016 8v), but its vehicle gain shrank from +0.019 (3 against 2 draws) to +0.0046, and truck lost 0.0034 on plain predictions. The returns are falling, so the queued draw-5 members finish the V2X bags. The PV-RCNN++ and VoxelNeXt 4-draw bags (tuning) complete the reading. This also bears on increment D3 (Section 15.13.4): vehicle is saturating and pedestrian is not.

**Decision under the Section 13.1 rule: LUMPI range jitter is not kept as a lever either** (2026-11-09, 12:40 UTC). The single `rj` arm passes Person and Bicycle (plain), Car (8v, +0.0142) and Van, but it fails Truck on both variants, Motorcycle and Car without TTA (all at P(gain) 0.00), and Bus 8v (P 0.01). So no `rj` members are trained on new draws, and the member enters the `C1` route search for the classes it passes (rule 4).

**All four pre-registered lever arms are now decided, and none is kept:** V2X SN, V2X range jitter, LUMPI SN and LUMPI range jitter. Each single LUMPI arm gains Person, Bicycle and Car (8v) and loses Truck at P 0.00. The combined `snrj` arm does the reverse on two classes: it gains Truck and loses Bicycle. **Reading:** both augmentations change the size and range statistics that the size-based class rule uses to separate Car, Van and Truck, so one class pays for what the others gain. This is not measured. The gains are still usable class by class: `sn`, `rj` and `snrj` each enter the `C1` route search under rule 4 and the class gate, and the route keeps Truck on its current member. Training time goes to draws and bags (wave 3), which gained without a class loss.

**Readings.**
- **Weight averaging passes at least one class on all 11 averaged members checked.** It costs a class by more than 0.005 on three of them: LUMPI PV-RCNN++, Truck 8v of LUMPI `voxelrcnn-rosn-swa-g1v6`, and truck 8v of V2X `voxelrcnn-ros-swa-g1v6d2`. Increment 2 holds: the averaged members enter the `C1` search, per class.
- **Draw-to-draw spread is up to 0.09 AP for a class.** For example, VoxelNeXt truck: draw 3 against draw 1 gains +0.092 on plain predictions. Single draws are therefore used only inside bags (increment 3), as planned.
- **V2X SN hurts truck most.** The SN targets move vehicle heights up by about 10% and leave truck unchanged. A taller synthetic vehicle may be read as a truck more often; this is not measured.

**Wave 3 started: refined option A, by default** (2026-11-09, 09:00 UTC). On Nov 9 at about 03:00 UTC the entrant was given three options for the training time after the wave 1 queue (A balanced depth, B LUMPI-heavy, C V2X-heavy), with A as the default at 09:00 UTC if no other choice came. No other choice came, so A started. The evidence behind it: every 3-draw bag beat its 2-draw bag on both tracks; averaging the draws inside a bag added Person (LUMPI) and pedestrian (V2X); and the V2X SN, V2X range jitter and LUMPI SN levers were dropped by the Section 13.1 rule.
- **Corpora** (`w3_corpora.sh`, the clean `g1-v6` recipe, new seeds): LUMPI `g1-v6d4` (seed 4234) and `g1-v6d5` (seed 5234); V2X `g1-v6d5` (seed 5234).
- **Members** (`w3_option_a.sh`; each passes rule 1 before it is queued, training seed 666): LUMPI `voxelrcnn-rosn` and `-rosf` on draws 4 and 5; V2X `pvrcnnpp-ros`, `voxelnext-ros` and `voxelrcnn-ros` on draw 5. They train after V2X PV-RCNN++ and VoxelNeXt draw 4.
- **Then:** averaged versions of the Voxel R-CNN and PV-RCNN++ members, bags of 4-5 draws, and V2X draw 6 only if the draw-4 bags still gain.

#### 15.11 An outside review, checked (2026-11-08, 21:00-22:00 UTC)

The entrant shared an outside memo (ChatGPT, "Beyond S10, phased strategy for finals week"). It was written from release 9.2 (`e6c34d9`) and the S10 export. Each claim was checked in the code and, where cheap, measured on `C0` validation predictions or on the training corpora. Scripts: `fusion_dup_audit.py` and `label_owner_proxy.py` (session scratch, read-only).

| Memo item | Checked | Result | Verdict |
|---|---|---|---|
| Walker groups carry over between frames of one generator worker (`scene_map.py`, `_queue`) | **true**: the queue persists across frames within a worker | a frame's walkers depend on the worker's previous frame. The distribution is unchanged, so detection and the rules are unaffected; exact per-frame reproduction needs the same worker count and order | fix behind a new flag after the competition; never mid-wave (bags need one recipe). Record corpus hashes for the release |
| A finals preset, a histogram-free mode, a provenance manifest | partly covered: the `g1-v6` flags, `clean_check.py`, corpus cards | a histogram-free retrain of the portfolio cannot finish before Nov 13 | the manifest goes with the release. If the organizers reject the histogram (question (b)), the fallback is disclosure, not a retrain |
| LUMPI fusion: repeated boxes from one source move the fused centre | **true** in `fusion.py` (geometry uses every member, the score only the best per source) | repeated-source clusters: LUMPI 4.0-4.2%, V2X 6.8%. Median centre shift: LUMPI 0.02 m, V2X 0.14 m. Full `C0` system with one box per source: mAP LUMPI A -0.00004, B -0.0005; V2X A -0.0004, B +0.0004 | **closed** (no gain; the memo's own exit) |
| V2X pedestrian labels kept by ground or prop points after the walker's returns are gone (`prep.py`, min_points 1) | **true** in the code | proxy (in-box points only in the bottom 0.3 m): V2X `g1-v6` 0.75% of 14,852 labels, `g1-v7` 0.68%, LUMPI `g1-v6` 0.06%. Structures do not raise it | **closed** (rare); a body-return condition can enter a later recipe |
| Walker / prop / empty counterfactual scenes and hard synthetic asset families | not built | matches the 14.1 finding that confident false positives are objects of walker height or lower | branch B of the `g1-v7` decision (below) |
| GT sampling may undo the `g1-v7` contrast (the loader pastes up to 12 pedestrians per frame; OpenPCDet checks collisions with labelled boxes only, so pastes can land on unlabelled structures) | **true** for the probe's config | not measured. LUMPI evidence: the no-GT-sampling `rosn` members are the best Person family | **adopted as a decision input** |
| Ouster per-ring azimuth offsets in walker insertion | `pedsim.py` uses one azimuth grid; `lidar_sim.py` supports offsets, but we hold no unit metadata | estimating offsets from unlabelled clouds would take more than a day; value unknown | not pursued |
| Grouped validation: scenario blocks (V2X), contiguous blocks (LUMPI), leave-one-group-out | **true gap**: `scorecard.paired_bootstrap` resamples single frames, and neighbouring frames are correlated, so P(gain) is optimistic | | proposed as rule 14 (below), before any `C1` result |
| +0.010 AP on one class is worth +0.00122 combined (LUMPI) or +0.00286 (V2X) | agrees with 14.1 | | |
| Hold one 4-GPU run until the audits finish | | both audits closed the same day | not adopted: the GPUs stay on measured levers |

**The memo does not cover** the levers with the most measured value: weight averaging (11 of 11 members pass a class), draw bags (the best server transfer), the V2X pedestrian gap, the LUMPI Person and Car candidates (15.10), V5, realism frame selection, and the upload policy (rule 13). It is an audit memo, not a scoring plan.

**The `g1-v7` decision, with the memo's input** (decided on the probe's member check against `voxelrcnn-ros-g1v6`):
- **A, passes pedestrian without failing another class:** PV-RCNN++, VoxelNeXt and a second Voxel R-CNN draw on `g1-v7`, as 15.7 says.
- **B, borderline, or passes with the pedestrian false positives still near structures:** one no-GT-sampling arm (`voxelrcnn-rosn` config on `g1-v7`) before any more `g1-v7` members.
- **C, fails pedestrian:** `g1-v7` stops. The slot goes to V2X draw depth.

**The `g1-v7` decision (2026-11-08, 22:25 UTC).** Branch A is not met: the probe passes pedestrian without TTA (+0.0127 pooled, P(gain) 1.00), but not with TTA (B -0.007), and it fails truck (plain) and vehicle (8v). Against the parent, two plain `g1-v6` redraws move pedestrian by +0.0121 (`d2`) and +0.0037 (`d3`) without TTA, and by +0.0084 and +0.0012 with TTA. **So the structures show no pedestrian effect beyond draw-to-draw variation.** Branch B (the no-GT-sampling arm) has a weak prior: S9's V2X `voxelrcnn-rosn-g1v6` lost pedestrian (-0.0051) against its GT-sampling parent. **Outcome, branch C:** no further `g1-v7` members, and the three planned `g1-v7` trainings go to V2X draw depth. The probe stays a clean Voxel R-CNN draw, usable as a bag partner (rule 4 through the bag); its frames are not used (rule 12). Reading: label-free structures were the strongest LUMPI Person lever (S9) but do not move V2X pedestrian. The V2X pedestrian gap to the label-placed corpora stays open, and depth and averaging are the measured levers left for it.

**Rule 14 (grouped final gate), as first proposed; adopted with calibrated margins in 15.12.** `C1` and later versions also report a block bootstrap: V2X frames grouped by scenario, LUMPI by 200-frame contiguous blocks per measurement. They also report leave-one-group-out signs. A version is uploaded only if the block-bootstrap P(gain) of the mAP is at least 0.8 and no single group's removal flips the sign of the pooled gain. Status: waiting for the entrant's adoption.

**Operations note.** The probe's TTA tuning failed three times with out-of-memory errors. Each time, two tuning jobs had started on GPU 0 within seconds of each other; the step picks the GPU with the most free memory before either job has allocated. The fourth tuning worker, added at 20:47 UTC, makes such collisions more likely. The step was re-run by hand on GPU 1. New tuning workers should claim a GPU with a lock for the first minutes of a step.

#### 15.12 Rule 14 adopted: the grouped final gate, with a margin (2026-11-09, about 00:30 UTC)

**Decision.** The entrant adopted rule 14 as a gate, "but have a margin as the submission leaderboard have provided minor gains upon upload ... Do make a nuanced assessment during the decision gate as per the leaderboard submissions history." The margins below were set from the upload history, before any `C1` result.

**Tool.** `common/tools/s10_grouped_gate.py <new> <ref>` runs on the final validation predictions (`*_routed.json`), with A and B pooled. `scorecard.grouped_bootstrap` and `leave_one_group_out` were added, with two unit tests. It reports:
- the frame-level bootstrap;
- the grouped bootstrap: 1,000 resamples of whole groups. Groups are V2X scenario folders (57) and LUMPI 100 s recording windows (28);
- leave-one-group-out deltas;
- per-class deltas on A, B and pooled;
- the share of the gain carried by LUMPI Bicycle, Motorcycle and Bus, which the test window cannot validate.

**Back-test on 13 past uploads with known leaderboard outcomes** (each against the upload it replaced; the server delta is combined):

| Track | New vs ref | Server | Pooled mAP delta (A / B) | P frame / grouped | Worst leave-one-out | Rare share | Level |
|---|---|---|---|---|---|---|---|
| LUMPI | `g11c` vs `g11b` (S8) | +0.0015 | +0.0001 (+0.0003 / -0.0001) | 0.93 / 0.60 | -0.0001 | 0.00 | JUDGEMENT |
| LUMPI | `g11d` vs `g11c` (S8.3) | +0.0002 | +0.0003 (+0.0003 / +0.0005) | 1.00 / 1.00 | +0.0003 | 0.41 | GO |
| LUMPI | `g12` vs `g11d` (`s9a`) | +0.0100 | +0.0087 (+0.0127 / +0.0062) | 1.00 / 1.00 | +0.0078 | 0.00 | GO |
| LUMPI | `g13` vs `g12` (`s9b`) | +0.0059 | +0.0017 (+0.0009 / +0.0021) | 1.00 / 0.93 | +0.0013 | 0.00 | GO |
| LUMPI | `g14` vs `g13` (`s9c`) | -0.0004 | +0.0007 (+0.0018 / -0.0002) | 1.00 / 0.98 | +0.0003 | 0.00 | GO |
| LUMPI | `g15` vs `g14` (`s9d`) | +0.0013 | +0.0003 (+0.0003 / +0.0010) | 1.00 / 0.93 | +0.0002 | 0.00 | GO |
| LUMPI | `g21` vs `g15` (`s9iu`) | **-0.0025** | +0.0103 (+0.0307 / +0.0087) | 1.00 / 1.00 | +0.0046 | **1.00** | JUDGEMENT |
| LUMPI | `g22` vs `g15` (`s9j`) | +0.0003 | +0.0010 (+0.0007 / +0.0009) | 1.00 / 1.00 | +0.0008 | 0.00 | GO |
| LUMPI | `c0` vs `g22` | -0.0020 | -0.0070 (+0.0068 / +0.0018) | 0.02 / 0.24 | -0.0107 | 1.00 | NO-GO |
| V2X | `g13` vs `g12` (S8) | +0.0040 | +0.0025 (+0.0023 / +0.0034) | 1.00 / 1.00 | +0.0022 | | GO |
| V2X | `g15` vs `g13` (`s9a`) | +0.0008 | +0.0014 (+0.0020 / +0.0006) | 0.96 / **0.79** | +0.0005 | | GO |
| V2X | `g19` vs `g15` (`s9f`) | +0.0008 | +0.0040 (+0.0044 / +0.0015) | 1.00 / 1.00 | +0.0032 | | GO |
| V2X | `c0` vs `g19` | -0.0153 | -0.0155 (-0.0147 / -0.0205) | 0.00 / 0.00 | -0.0173 | | NO-GO |

**The margins (calibrated on the table, so that no past positive upload is blocked):**

| Level | Conditions | Back-test |
|---|---|---|
| **GO** | pooled mAP delta > 0; grouped P(gain) >= **0.75** (0.8 was proposed; V2X `s9a` at 0.79 scored +0.0008); every leave-one-group-out delta >= **-0.002 mAP**; rare classes carry less than half of the gain | 9 cases: 8 scored positive, 1 scored -0.0004 (inside leaderboard noise) |
| **JUDGEMENT** | delta > 0 and grouped P(gain) >= **0.5**, but a GO condition fails | 2 cases: `s9iu` (rare-class gain, scored -0.0025) and LUMPI `g11c` (tiny gain, scored +0.0015) |
| **NO-GO** | delta <= 0, or grouped P(gain) < 0.5 | 2 cases, both scored negative (both `C0`s) |

**What the history says about magnitude.**
- **Pooled validation gains understate server gains when the change is a Person or ensemble improvement.**
  - `s9a` +0.0087 validation scored +0.0100 on the server; `s9b` +0.0017 scored +0.0059.
  - V2X S8 +0.0025 scored +0.0040.
- **The opposite holds for rare classes and box-size calibrations.**
  - `s9iu` +0.0103 validation scored -0.0025.
  - `s9j` +0.0010 scored +0.0003.
  - V2X `s9f` +0.0040 scored +0.0008.
- **Small changes are inside the leaderboard noise.** The 100 test frames give about ±0.001-0.002 combined, so `s9c` scored -0.0004 despite grouped P 0.98. Rule 13's reserve upload is the protection against such a loss, so a GO with a small gain is still worth an upload slot.

**The nuanced assessment at each gate** (given to the entrant with the level, before any upload):
1. The level and its conditions, from the tool.
2. The change broken down by type, with each type's server transfer from the table:
   - Person, route and ensemble changes: about 1x or better;
   - box-size and post-processing changes: 0.2-0.6x;
   - rare classes: unreliable, sign included.
3. An expected server range: the rule 10 projection times the transfer band of the change's dominant type, set against the leaderboard noise (±0.0015) and against the race (LUMPI lead 0.0066 on 2026-11-08).
4. The upload-slot situation (rule 13): which slot it would use, and whether the reserve remains.

`C0` itself is level NO-GO against the kept zips, as expected: it was uploaded under Plan A (compliance), not as a gain. From `C1` on, every version is gated against the best scored clean version.

#### 15.13 Final-week research review (2026-11-09, 13:40-14:15 UTC; the entrant's board screenshots of 07:39-07:40 CST, server time UTC-6)

The entrant asked for a deep review of the scores and the competitors' gains, a research scan of the community's synthesis and detection stacks beyond OpenPCDet and CARLA frames, a few plans that can be added to S10 one increment at a time within the rules, and a nuanced assessment. Two read-only literature scans ran in parallel (nothing was downloaded or installed), and six local measurements were made on legal frames and validation outputs only.

##### 15.13.1 The board, decomposed with our scorer

Every value is reproduced to within 0.0006 by `bdc26.realism.normalize` and `combined`. The detection term is 0.6 clip(mAP/0.7); R = 1 - mean of the four clipped terms.

**LUMPI (07:40 CST)**

| # | Team (ID, date CST) | Combined | mAP 3D@0.5 | Detection term | CD | EMD | FPD | R | 0.4 R |
|---|---|---|---|---|---|---|---|---|---|
| 1 | lukefinigan (1042827, 11-08 12:17) | **0.5440** | 0.1953 | 0.1674 | 1.186 | **1.124** | 0.457 | 0.9414 | 0.3766 |
| 2 | **KarmaRV** (1042287, `C0`) | 0.5408 | 0.1950 | 0.1671 | 1.510 | 1.272 | 0.430 | 0.9342 | 0.3737 |
| 3 | dipper13579 (1044443, 11-09 07:13) | 0.5278 | 0.1760 | 0.1509 | 0.755 | 1.100 | 0.531 | 0.9423 | 0.3769 |
| 4 | sadbodh (1038056) | 0.5198 | 0.1676 | 0.1437 | 1.564 | 1.177 | 0.177 | 0.9402 | 0.3761 |

**V2X (07:39 CST)**

| # | Team (ID, date CST) | Combined | mAP 3D@0.5 | Detection term | CD | EMD | FPD | R | 0.4 R |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **KarmaRV** (1038966, `s9f`, **not clean**) | 0.9038 | 0.6189 | 0.5305 | 1.986 | 1.182 | 1.468 | 0.9332 | 0.3733 |
| (1) | **KarmaRV clean `C0`** (1042294, not shown) | 0.8885 | 0.5976 | 0.5122 | 1.844 | 1.110 | 0.748 | 0.9406 | 0.3762 |
| 2 | sadbodh (1039213) | 0.8550 | 0.5573 | 0.4777 | 1.827 | 1.092 | 0.402 | 0.9433 | 0.3773 |
| 3 | lukefinigan (1043708, 11-08 23:49) | 0.8334 | 0.5264 | 0.4512 | 1.420 | **0.876** | 0.167 | 0.9554 | 0.3821 |
| 4 | dipper13579 (1043882, 11-09 01:37) | 0.7855 | 0.4724 | 0.4049 | 0.698 | 0.946 | 0.268 | 0.9513 | 0.3805 |
| 5 | linyongchun (1040931) | 0.7271 | 0.4005 | 0.3433 | 0.487 | 0.804 | 0.051 | 0.9596 | 0.3838 |

**Readings.**
1. **LUMPI is lost by 0.0032, and all of it is realism.** The detection terms are equal (0.1674 against 0.1671). The realism term differs by 0.0029, from EMD alone (1.124 against 1.272). lukefinigan's last upload gained +0.0098 (mAP +0.0076, EMD -0.142, FPD -0.22).
2. **V2X: the board still shows `s9f`, a submission that is not clean,** a day after `C0` was scored. So the board does not simply list the newest upload. Reading 1 of Section 13.4 held for LUMPI, but not for V2X. The likely cause is that the phase lets each team choose its board entry: LUMPI shows the lower, newer `C0`, and V2X shows the higher, older `s9f`. This is not verified. **The entrant should open My Submissions on V2X and put 1042294 on the board.**
3. **V2X lead, clean: 0.055 over lukefinigan.** The lead is detection (+0.061) minus realism (-0.006). lukefinigan gained +0.141 in one upload (mAP +0.147, EMD -0.459, FPD -2.66). At their R (0.955), they pass `C0` at mAP 0.591, which is +0.065 from where they are. This is a real threat by Nov 16.
4. **What is not scored:**
   - CD below 2 (every top entry is below 2);
   - BEV mAP;
   - 3D mAP@0.7, where we lead LUMPI by 0.037.

   The CD and BEV gains visible on the board move nothing. EMD (and a little FPD) moves R.
5. **Exchange rates** (both tracks):

   | Change | Combined |
   |---|---|
   | -0.1 EMD | +0.0020 |
   | +0.01 mean mAP | +0.0086 |
   | +0.01 AP on one LUMPI class | +0.0012 |
   | +0.01 AP on one V2X class | +0.0029 |

   To retake LUMPI with a margin for lukefinigan's next step, we need about +0.005 on the server.

##### 15.13.2 New measurements (2026-11-09; legal frames and validation only)

| Probe | Result | Verdict |
|---|---|---|
| **Ground height** (`scratchpad/s10/research/terrain_bound.py`): the synthetic ground moved to the real per-cell ground (1 m cells, lowest 5%, fitted on unlabelled proxies 1-3, scored on held-out 4-5, exact scorer) | Our LUMPI ground is flat at z -2.15 m (5th, 25th and 50th percentiles); the real ground spans -2.37 / -2.08 / -1.95 m (5th / 50th / 75th). The correction moves LUMPI EMD by -0.005 and R by +0.0002-0.0003; V2X EMD by -0.003 to -0.006, R +0.0000, CD +0.02-0.05 | **Dropped.** The ground error is real, but it is not what EMD sees (as S9's ground bowl showed). A ray-consistent version would move ring radii too, but the vertical bound leaves little room |
| **Ring audit** (`ring_audit.py`): each Measurement4 lidar's points in its metadata frame, residual to the beam table | The merged frames mix five lidars, so nearest-sensor assignment contaminates every sensor. The cleanest one (Pandar64, 0.171 deg spacing) has a real residual of 0.035 deg, consistent with the metadata pose | **Inconclusive; not pursued.** No gross pose error is visible. A re-cast of the UrbanTwin background is not possible without the twin assets |
| **Van hedge** (`van_probe.py`): low-score Van copies of large Car boxes on the `C0` predictions | Van AP A 0.108 -> 0.070-0.112, B 0.0012 -> 0.0009-0.0010 | **Dropped.** The real vans on B are not found as Car boxes either. Van has no inference lever, and the email needs no hedge question |
| **Person centroid shift** (`person_probe.py`, lever 1 of the detection scan): xy moved toward the interior-point centroid, blend 0.25 / 0.5 / 1.0 | LUMPI Person A -0.006 / -0.014 / -0.037, B -0.003 / -0.005 / -0.020; V2X pedestrian A -0.006 / -0.022 / -0.081, B -0.003 / -0.016 / -0.059 | **Dropped.** Our fused, calibrated boxes are already better centred than the visible-surface centroid, which is biased toward the sensor |
| **Point-count rescoring** (score x (n+1)^beta) | beta 0.1: LUMPI Person A +0.0011, B +0.0055; V2X pedestrian A +0.0034, B -0.0021. beta 0.25 and 0.5 lose | **A small candidate (LUMPI Person only)** under the class gate in `C1`; a post-processing change, so transfer 0.2-0.6x: about +0.0002 combined |
| **Static gap** (`static_gap.py`, R1 diagnostic): persistent above-ground occupancy (0.5 m cells, occupied in at least 60% of 300 unlabelled legal frames; no label read) against the same in 300 UrbanTwin frames (occupied in at least 30%) | LUMPI: **34.9% of the real above-ground static mass, 9.5% of all points**, lies in 868 static cells (211 clusters) where the twin has no geometry. V2X: 38.1%, 9.2% (579 cells, 171 clusters). Vehicle-sized static clusters (parked cars, excluded from any use) are 1.2% (LUMPI) and 0.5% (V2X) of the points | **R1 has the headroom to explain most of our EMD excess** (moving 9% of the mass 3-5 m is 0.27-0.45 m of W1, against our 0.43-0.48 excess). It also bears on detection: 65% of the confident V2X pedestrian false positives sit on static structures (14.1). The email's question (c) gates both |
| **`C1` rehearsal** (`routed-c1a`, LUMPI): `C0`'s 33 member folders plus the 27 tuned wave 1-3 candidates, the `C0` pipeline | running since 14:02 UTC | gives the measured projection of increment D1 below |

##### 15.13.3 The research scan, in brief (two read-only scans; links in the scan reports, numbers as reported, "unverified" where not checked)

**Detection stacks.** Every 2023-2026 detector with usable code that the scan checked is an OpenPCDet fork:
- HEDNet and SAFDNet (CVPR 2024, Apache-2.0);
- LION and Voxel Mamba (NeurIPS 2024; need Mamba or RWKV CUDA builds);
- ScatterFormer (ECCV 2024; a custom kernel);
- FSHNet (CVPR 2025; needs torch_scatter);
- GBlobs (CVPR 2025, BSD-3).

MMDetection3D's last release is v1.4.0 (January 2024) and lacks these. Pointcept has no box detection. **Switching stacks buys nothing.** The only route is porting a model file into our pinned fork.

**Detection levers that fit the rules:**
- **GBlobs** (Malic et al., CVPR 2025): voxel mean and covariance as input features. 1st in RoboSense 2025 Track 3 (CARLA synthetic). Voxel R-CNN Waymo to KITTI 3D mAP 46.8 -> 67.8. Much of that gain is a box-height bias that our size calibration already fixes, and the covariance is degenerate for voxels with 1-2 points (far pedestrians).
- Per-member score calibration before fusion (MoCaE, ProbEn): up to +2.5 AP on 2D COCO; little where routing picks one member.
- Point-count rescoring and the Person centroid shift (AMAN_UPG, arXiv 2611.03936 and 2611.03940): measured above.
- Scale and rotation TTA (RoboSense 2025): our 12-view set already includes scale.
- Box-convention alignment was the largest single sim-to-real factor in "Synth It Like KITTI" (arXiv 2502.15076: Moderate AP 37.3 -> 62.8), which supports our anchored calibration. Naive ray drop and Gaussian jitter did little there and in Huch et al. (arXiv 2303.01899).

**Detection levers that fail the rules or the window:**
- ST3D, DTS, SPG, HUNTER and MOS adapt or self-train on target frames (rule T, our test-frame rule).
- Uni3D and ReSimAD need real labelled source data (L).
- 3D-VField and PA-AUG are about zero in GBlobs' table.
- LiDAR Distillation fixes a beam-count gap the twin does not have.
- Model soups across our bags are a trap: they are trained from scratch, not fine-tuned from a shared start.

**Synthesis and realism.** The order of effects for pooled-xyz metrics:
1. Static geometry, and the sensor pose and beam pattern.
2. The ray-drop pattern, only once the geometry is good (Waabi, ICCV 2023).
3. Second returns, only for dual-return long-range sensors.

Noise, rolling shutter and motion blur do not move pooled distributions.

Other simulators (AWSIM, Isaac Sim RTX LiDAR, HELIOS++, BlenSor) do not fit the window: they need a new simulator and the twin assets. They would buy beam divergence and multi-echo, not geometry.

Learned ray drop or translation (DUSty, SynLiDAR PCT, CycleGAN, DRUM) and generative refinement (R2DM, R2Flow, LiDM, La La LiDAR, SPIRAL) are a poor fit, for four reasons:
- they are trained on real scans, and the challenge page forbids "using real data for training, including fine-tuning", which may cover a generator;
- on a fixed site they memorize the background, which is twin completion by another route;
- they can erase or shift small labelled objects;
- they take 2-3 days.

Neural reconstruction (NFL, LiDAR4D, NeuRAD, UniSim, GS-LiDAR) rebuilds the real background from real sweeps. That is the twin-completion grey zone.

**Competitor reports** (new; none for lukefinigan, dipper13579 or sadbodh):
- **AMAN_UPG** (arXiv 2611.03936 and 2611.03940; DriveX phase; LUMPI 0.4793, V2X 0.7457):
  - PointPillars;
  - pedestrian insertion from point-count curves;
  - post-hoc steps, measured above;
  - for realism: V2X null returns (31% of the real reference; we already ship 0.31), moment alignment and EMD-targeted frame selection.
- **urban-finals** (DriveX LUMPI 3rd, 0.4637): fitted its realism transform on the 50 released detection-test frames, which the organizers forbid.
- **linyongchun** may be the contact of a RoboSense 2025 team that used GBlobs with ST3D self-training (unverified).
- **lukefinigan's V2X jump** (EMD 1.335 -> 0.876) matches adding null returns (hypothesis H1 of the scan; AMAN reported EMD 1.38 at a 0.23 null rate). Since we already ship nulls, it also means their non-null geometry is closer to the real one than ours. How is not known, and we draw no conclusion.
- **One trap named by the scan:** the scorer's subsample seed (1234) is public, so the 10,000 drawn points could be predicted and gamed. That is metric gaming, and it breaks our frame-provenance rule. Not considered.

##### 15.13.4 The plans (increments that can be added one at a time)

| Increment | Technique | Pros | Cons | Expected server gain (combined) | Rules | Cost and window | Decision |
|---|---|---|---|---|---|---|---|
| **D1** (in flight) | Depth of the clean portfolio: draws 4-5, 3- to 5-draw bags, bags of averaged draws, SWA members, the `C1`/`C2` route and fusion search | Measured: every 3-draw bag beat its 2-draw bag; averaged bags add Person / pedestrian; ensemble changes transfer at about 1x | LUMPI gains are spread over classes; the rehearsal gives the number | LUMPI +0.002 to +0.005; V2X +0.003 to +0.006 (to be replaced by the rehearsal projection) | clean (rule 1); rules 4, 10, 14 | running; trains to Nov 13 18:00 UTC | **keep** |
| **D2** | Point-count rescoring of LUMPI Person (beta 0.05-0.15) as a `C1` stage under the class gate | CPU, hours; +0.0055 B, +0.0011 A at beta 0.1 | post-processing transfer 0.2-0.6x; V2X mixed | about +0.0002 | inference on test frames only; disclosed (D) | Nov 10, with `C1` | **add** (gate decides) |
| **D3** | One GBlobs Voxel R-CNN member per track (our `GBlobsCellVFE` from S5; see the correction in 15.13.6), routed per class | a challenge-winning sim-to-real precedent; no new dependencies; a new kind of diversity for fusion | needs the entrant's permission (new architecture code); one member without bag or SWA rarely beats a routed ensemble on a class; displaces two draw members | +0.000 to +0.003, uncertain | T (synthetic only) | port about 4 h, then 2 x 4 h training and 2 x 3 h tuning; must start by Nov 10 | **conditional:** only if the 4-draw bags saturate (checks running at 14:15 UTC) and the entrant allows the code |
| **R1** | Twin completion: synthetic structures (and surfaces) where unlabelled legal real clouds show persistent static geometry the twin lacks | the only realism lever left with headroom: the real-against-real floor is R 0.9498 against our 0.9399 (LUMPI, local) | grey zone; needs the organizers' answer to question (c); a new draw must also train a used member (rule 6) | LUMPI +0.001 to +0.003; V2X +0.002 to +0.005 | C if the organizers agree | code about 1 day (prepared, unused, while the email waits); corpus 3 h, training 4 h, tuning 3 h | **prepare, use only on a yes** (in `C2` if the answer arrives by Nov 12) |
| **R2** (kept from 15.6) | EMD-targeted frame selection over the V2X pool of draws 1-5, fit on proxies 1-3, held-out 4-5 | measured +0.0004 to +0.0012 | can overfit the proxy; CD must stay below 2 | V2X +0.0004 to +0.0012 | C; frames train a used member | CPU, with the `C1` V2X build | **keep** |
| **X1/V5** (kept from 14) | V2X pedestrian overhead demotion; synthetic-trained rescorer | V5 measured +0.002-0.003 pedestrian AP on both splits | X1 code not written | V2X +0.001 to +0.002 | inference only; disclosed | Nov 10 | **keep** (V5); X1 if time |

**Dropped today, with the reason:**
- the Person centroid shift (hurts);
- the Van hedge (no gain);
- ground calibration (bound about 0);
- a pose or beam re-cast (no error found, no twin assets);
- a per-pixel ray-drop mask (it can only remove mass, and the thinning bound of 15.6 says removal does not reach the floor);
- moment alignment (our FPD term is already 0.009 or less);
- learned or generative translation (rules, window, label damage);
- new backbones that need new builds (LION, Voxel Mamba, FSHNet, ScatterFormer) and stack switches;
- model soups across bags, any test-time adaptation or self-training, and seed-aware subsampling.

##### 15.13.5 Assessment and alignment

- **The winning plan on V2X is the one in place,** provided the board shows a clean entry: clean depth (D1), the V5 stage, and frame selection (R2). The lead is 0.055 against a competitor who gained 0.141 in a day. So `C1` and `C2` should keep adding detection, and the gate should not hold back a real V2X gain for want of margin.
- **LUMPI cannot be retaken by realism alone under our current reading of the rules.** Every legal realism lever we can still measure is worth below +0.001. The gap (0.0032) is realism, so retaking LUMPI needs one of the following:
  - D1 on its high side (+0.004 to +0.005);
  - D1 plus R1, if the organizers allow twin completion;
  - a fall by lukefinigan, who has moved up twice in two days.

  An honest reading: rank 1 on LUMPI is possible but not likely without R1, and the 0.0032 deficit is close to the board noise (±0.0015) only once D1 lands.
- **The email is now on the critical path.** Question (c) gates R1 (the largest lever left on LUMPI), and question (a) decides whether the reserve slot must re-upload or can carry a new candidate. Both answers are worth more than any single experiment we can run before them.
- **The order of work:**
  1. today, the 4-draw bag checks and the rehearsal projection (D1);
  2. Nov 10, the `C1` builds with D2, V5 and R2, and the rule 14 gate with the history-based assessment;
  3. Nov 11, upload 3;
  4. R1 code written but unused until the answer;
  5. D3 only on the two conditions above.

**For the entrant:**
1. On V2X, put 1042294 (clean `C0`) on the board through My Submissions, if the page allows it, and tell us what the page offers. This also answers whether rule 13's reserve re-upload is needed.
2. Send the email (Appendix A) today. Question (c) now names static surfaces as well as poles and trees, and a new question (d) asks how the board entry is chosen.
3. Decide D3: allow one GBlobs member per track (new architecture code), or not.

##### 15.13.6 Adopted (the entrant, 2026-11-09, about 14:20 UTC: "Adopt, allow GBlobs")

- **Adopted increments:**
  - D1 continues;
  - D2 becomes a `C1` stage under the class gate;
  - R2 and V5 as planned;
  - R1 code is prepared and stays unused until the organizers answer question (c).
- **D3 is allowed** (new architecture code: the GBlobs input encoder in our OpenPCDet fork, ported from the paper and the BSD-3 reference code).
- **Correction (14:30 UTC): GBlobs is not new here.** S5 (2026-10-11, docs/02 Section 8.5.1) ran it as `voxelrcnn-gblobs-g1v3` on both tracks, with our cell-covariance adaptation `GBlobsCellVFE` (`common/bdc26/detect/gblobs_vfe.py`). The published per-voxel form degenerates here: 80-83% of our 0.1 m voxels hold one point. Alone it lost to its parent (LUMPI A/B 0.276 / 0.162 against 0.295 / 0.170; Person ranking loss 0.529 -> 0.604), because the twin is the test intersection and absolute position is real signal. Inside fusions it won (V2X vehicle, LUMPI Car). GBlobs with object scaling (S5 run c) was never run. The research review missed this history. So D3 is S5's run c on the clean corpus: a fusion-diversity member, not a stronger single member. No port is needed; the encoder and its unit tests exist. Members: LUMPI `voxelrcnn-rosf-gblobs-g1v6` (the `voxelrcnn-rosf-g1v6` configs) and V2X `voxelrcnn-ros-gblobs-g1v6` (`voxelrcnn-ros-g1v6`), both clean (rule 1), seed 666, `pcdet/g1-v6`.
- **When D3 trains.** The saturation condition is read on the evidence available at adoption. The Voxel R-CNN 4-draw bag's vehicle gain fell from +0.019 to +0.005, and V2X draw 6 was not added. So the GBlobs members take the training slots that draw 6 would have used. They go to the front of the train queue once the port passes a smoke test, LUMPI first (the close race), then V2X. The queued draw-5 members move back by one slot each and still finish by Nov 11.
- **R1 prepared, unused** (14:45 UTC): `common/tools/s10_static_anchors.py` wrote `gen/static_anchors_r1_v1.json` on both tracks (LUMPI 210 block anchors from 211 clusters, V2X 172 from 171; vehicle-sized clusters dropped). `prepare_g1.py --static-anchors` (both tracks) ray-casts one unlabeled block per anchor through G2 (`G2Config.static_anchors`, skipped where it would cover a labeled box). **Interlock:** `clean_check.py` fails any corpus built with anchors unless `BDC_ALLOW_R1=1`, which is set only after the organizers' yes. No frame has been generated with the anchors. The email's question (c) now says that we measured where structures are missing and used it nowhere.
- **What decides D3's use.** Each GBlobs member is checked against its xyz sibling (`voxelrcnn-rosf-g1v6` on LUMPI, `voxelrcnn-ros-g1v6` on V2X) by rule 4. It enters the route search for the classes it passes. If it passes a class, GBlobs draws 2 and 3 train before the Nov 13 stop, for a bag in `C2`.

##### 15.13.7 The C1 dry runs (2026-11-09, 14:00-18:40 UTC)

**LUMPI `routed-c1a`** (`C0`'s 33 member folders and 27 tuned wave 1-3 candidates, built from scratch by `s10_clean_portfolio.sh`; clean, kit check valid, 23,873 boxes, Person copy threshold 0.7533). Not an upload.

| Step | Pooled mAP against `routed-c0` | Reading |
|---|---|---|
| Built from scratch (select, fuse, size calibration) | **-0.0015** (A -0.0028, B -0.0011); rule 14 NO-GO, 28 of 28 leave-one-group-out deltas negative | Person +0.0044 (P 0.97, the fusion `bvrrosfswa6x3_tta+vrrosn6_tta12`); Bicycle -0.0077, Truck -0.0070, Car -0.0018: the search from scratch did not find `C0`'s Bicycle and Truck fusions |
| D2 point rescore on that Person fusion | not kept (A -0.0011, pooled -0.012, P 0.00) | the gain measured on `C0`'s Person (15.13.2) does not carry over to another fusion |
| R3 class gate (`gate --vs routed-c0`) | every changed class reverted | Person's B gain +0.0037 is below the +0.01 bar of R3 |
| After the revert, before the fix | -0.0007; Person -0.0048 | **defect:** a reverted class got `C0`'s route but not `C0`'s size entry (Person `dh` +0.03; Car kept the new, smaller entry) |
| After the fix, gate run again | **+0.0000 on every scored class** (A 0.4147, B 0.2388, the `C0` values) | the revert now reproduces `C0` exactly; only the unscored Unknown route differs |

- **Fix (route_predictions.py):** `_class_config` now includes the class's size entry with its anchors (`_size_entry`), so a size change alone sends a class through the gate, and the revert restores the incumbent's entry (`_restore_size_entry`; it refuses to mix two anchor sets). Test `test_gate_revert_restores_the_incumbents_size_entry`; 165 tests pass.
- **Procedure for `C1` and `C2`, both tracks:** `S10_INCUMBENT=model-<track>-track/routed-c0 bash common/pipeline/launch.sh ... s10_clean_portfolio.sh ...`. After the size calibration, the tail runs `gate --vs` (LUMPI with the Van judge), validates again and runs the rule 14 grouped gate. Then the clean check, package, copy fit and kit check run as before.
- **Reading for LUMPI.** No candidate tuned so far clears R3 against `C0` on any class. So a LUMPI `C1` built today would be `C0`, and its upload would be spent for nothing. Even if Person's +0.0044 pooled gain had been kept, it is worth about +0.0005 combined at the LUMPI rate (one class, +0.01 AP = +0.0012), far below the 0.0032 gap to the board leader. That gap is realism (EMD 1.124 against our 1.272, 15.13.1), and the realism lever R1 waits for question (c). **LUMPI upload 3 is spent only if the Nov 10 build passes rule 14;** the candidates still to come are the GBlobs member and the Voxel R-CNN draws 4-5 and their bags.

**V2X `routed-c1a`** (`C0`'s 16 member folders and 33 tuned candidates: the 3- and 4-draw bags of all three families, their averaged bags, single draws 3-4, the averaged draws; gated against `routed-c0` by the new tail step). Launched 18:19 UTC. R2 (frame selection over the draw pool) is added on Nov 10: it needs the packager to take frames from several corpora, and it changes frames only.

| Class | From scratch (before the gate) | Pooled against `C0` | Gate |
|---|---|---|---|
| vehicle | `bvrrosswa6x4_tta+bpvrosswa6x4_tta@0.7` (8-view bags of averaged draws 1-4) | **-0.0118** (A -0.012, B -0.009) | reverted |
| pedestrian | `C0`'s fusion (`vrros6d2_tta12+vrros6_tta12+vrrosf6_tta12@0.5`) plus V5 (k 5) | **+0.0027** (A +0.0029, B +0.0017, P 1.00) | reverted by R3's +0.01 bar |
| truck | `vrrosf6_tta12+bvrros6x3_tta@0.7` | -0.0002 (P 0.64) | reverted |

After the gate the dry run equals `C0` (A 0.7281, B 0.7056): the revert procedure holds on V2X too.

- **12-view outputs decide V2X vehicle and pedestrian.** `C0`'s vehicle is the 12-view 2-draw bag fused with DSVT, and its pedestrian fusion has three 12-view single members. None of the new draws (3-4) and none of the averaged draws has 12-view outputs, so no bag of 3-4 draws can be compared at 12 views. The 8-view 4-draw bags lose vehicle to the 12-view 2-draw bag by 0.012. **Plan:** `jobs_tta12_w4.txt` holds 12-view tuning (`tune_and_eval.sh --tta flip4+yaw+z+scale --tta-tag tta12 --reuse-raw`, as on Nov 7) for the 35 members of the candidate bags that lack it (V2X Voxel R-CNN and PV-RCNN++ draws 3-4 first, then the averaged draws and VoxelNeXt; then LUMPI rosn, rosf and PV-RCNN++). A waiter (`t12_at_drain`) gives each trainer's four GPUs to that queue when the trainer's queue is empty (about 08:00-09:00 UTC Nov 10), so training never shares a GPU with a 45 GB job; about 25 GPU-hours, done by about 12:30 UTC. Then the bags get 12-view outputs (`bag_predictions.py --tags _tta12`), and the `C1` builds run in the afternoon of Nov 10. The next training wave starts after the 12-view queue.
- **Gate correction (route_predictions.py `_only_stage_change`, 20:30 UTC).** R3's +0.01 bar on B protects an incumbent route from noisy switches; R5 already waived it when copies are the only change. Rule 11 keeps a new stage (V5, X1) on its own test: pooled P(gain) >= 0.9, neither split down by more than 0.005. V5 passed that and was then reverted by the +0.01 bar, so the two rules disagreed. Now a class whose route, calibration, fusion, budget and size entry equal the incumbent's, and whose only change is a stage (tail copies, sparse, overhead, point rescore), needs a gain on B at P >= 0.9 and the pooled condition, without the +0.01 bar. A route or size change keeps the bar. Test `test_final_gate_waives_the_route_bar_only_for_stage_changes`. The entrant can overrule this correction; without it V5 never enters a version.
- **V5 re-test with the corrected gate (20:45 UTC).** `overhead` on the gated dry run (k 5 again; the next k gains +0.0022, so the choice is not on a knife edge), then `gate --vs routed-c0`: pedestrian kept (B +0.0017 at P 0.975, pooled +0.0027 at P 1.00); vehicle and truck equal `C0`. Validation A 0.7290, B 0.7062. **Rule 14: GO** (pooled +0.0009, A +0.0010, B +0.0006; grouped P(gain) 1.00 over 57 scenarios; 0 of 57 leave-one-scenario-out deltas negative; no rare-class share). About +0.0008 combined. History check (15.12): all three V2X GO cases in the back-test scored positive on the server (+0.0008 to +0.0040, from validation gains of +0.0014 to +0.0040), and this one has a smaller gain but a cleaner grouped test (P 1.00 against `s9a`'s 0.79). Expect a small positive, possibly inside the leaderboard's noise. Packaged as `c1av5` (kit check in the events), **the V2X fallback for upload 3** if the Nov 10 build with 12-view bags does not pass rule 14.

##### 15.13.8 Wave 5 options (proposed 2026-11-09, 23:30 UTC; the entrant chooses; B runs by default at 18:00 UTC Nov 10)

**Capacity.** The train queue drains at about 06:30 (trainA) and 07:50 UTC (trainB) on Nov 10. The 12-view queue (39 jobs) then runs until about 10:30-11:00, and the staged GBlobs draws 2-3 (both tracks) until about 19:00. From then until the Nov 13 18:00 stop, two trainers have about 71 hours each, room for 35-40 members at 3-4.3 h each. Ideas with positive expected value, not GPU time, are the limit.

| Option | Members (each with its SWA average and 12-view tuning) | Expected value | Rule alignment | Risk |
|---|---|---|---|---|
| **A. Balanced depth** | LUMPI GBlobs draws 4-5; LUMPI PV-RCNN++ draws 4-5 (its averaged draw 3 gained Person +0.017); V2X VoxelNeXt draw 6 (new corpus `g1-v6d6`, seed 6234) | LUMPI +0.0005 to +0.0015 combined (fusion members); V2X +0.0005 to +0.0015 (VoxelNeXt truck and pedestrian) | D1 depth; D3; the wave 3 draw-6 rule (VoxelNeXt still gains on all six) | low; about 6 members, the rest of the capacity idle |
| **B. A plus a LUMPI push (recommended)** | A, plus GBlobs probes on the LUMPI Voxel R-CNN `rosn` and PV-RCNN++ configs (rule 4 against their xyz siblings), then draws 2-3 of each probe that passes | LUMPI +0.001 to +0.003 if a probe passes as `rosf` did; LUMPI needs +0.0032 combined (about +0.0037 mean mAP) to pass the board leader without R1 | within the GBlobs permission (D3); new member types enter only through rule 4 | a probe can fail (S5 GBlobs alone was weak); PV-RCNN++ with GBlobs is untested (30-iteration smoke test first) |
| **C. Only what is already authorized** | the staged GBlobs draws 2-3 and VoxelNeXt draw 6 | V2X +0.0005 to +0.0015 | wave 3 rule only | GPUs idle for most of Nov 11-13 |

### Appendix A. Email to the organizers (draft; the entrant sends it)

> **Subject:** KarmaRV (LUMPI and V2X): real-data use after your clarification, and our final-phase submissions
>
> Dear organizers,
>
> Thank you for the clarification of November 7 on forbidden frames and real-data use. We checked our pipeline against it. We want to disclose one point and ask four questions while the final phase is open.
>
> 1. **Forbidden frames.** We used none of the 100 frames on either track for any purpose. On LUMPI, every use of real data stops at Measurement 4 frame 6399 (the first forbidden ID is 006497). On V2X, our mapping of the IDs agrees with your rule, and we also blocked every frame within 20 frames of a forbidden one.
>
> 2. **Real labels in earlier training sets (disclosure).**
>    - Our synthetic corpora built before November 2 placed each inserted synthetic pedestrian at the position, heading, size and ground height of a real label row from non-forbidden frames, with small random jitter. The rendered pedestrian's box was its training label. Under your clarification, we count this as real labels entering the training set.
>    - Detectors trained on those corpora are part of our development-phase entries and of our first final-phase submissions (LUMPI 1038963, V2X 1038966).
>    - Since November 2, our corpora place walkers on the digital twin's own map. Only scalar statistics of real labels reach the generator: box-size distributions, and a 10-bin histogram of walker distance from the sensor.
>    - For the rest of the final phase, we submit only systems whose detectors were trained on these map-placed corpora or on the UrbanTwin data alone. The first are **LUMPI 1042287 and V2X 1042294** (November 8). **Please rank our team by these clean submissions and the clean ones that follow;** we will list their IDs at the close.
>
> 3. **Other uses of real data** (all after removing the 100 frames), which we read as allowed by your clarification:
>    - validation and model selection on real frames (LUMPI Measurement 4 frames 0-6395 and samples of Measurements 5 and 6; V2X infrastructure frames);
>    - box-size statistics of real labels (size distributions in the generator and a test-time box-size calibration);
>    - realism calibration from unlabelled real clouds (a background density prior, the V2X sensor's beam elevation table, and proxies used to select the 50 synthetic frames). For V2X, these unlabelled frames include frames of the public val and test splits, none of them forbidden.
>
>    Our report also describes our test-time post-processing (test-time augmentation, box fusion, score floors and low-score duplicate boxes).
>
> 4. **Questions.**
>    - (a) In the final phase, does each team's best or last submission count?
>    - (b) Is the 10-bin walker distance histogram acceptable as a statistic? If not, we will remove it.
>    - (c) The digital twins lack some static structures and surfaces of the real sites (poles, trees, sign posts, walls, vegetation). May we use unlabelled, non-forbidden real frames to locate such structures and place synthetic objects there in our training scenes (no real points are copied)? We read this as realism calibration. We have only measured where such structures are missing (a diagnostic on unlabelled frames); no synthetic object has been placed there, and no training set or submission uses it. We will not use it without your answer.
>    - (d) On the V2X board our entry is still 1038966, although 1042294 was scored on November 8; on LUMPI the board shows our newest submission. How is the board entry chosen in the final phase, and which entry will be ranked?
>
> Best regards,
> KarmaRV
