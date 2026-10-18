# 02. Strategy: how this competition is won

> Built on `01-CHALLENGE-FACTS.md`. "est." marks planning estimates to be replaced by real-validation measurements. Strategy codes (S1, S2, ...) name complete submission recipes; the routes after S1 are in [Section 8](#8-strategy-routes-after-s1), and citations [Rn] link to [`07-LITERATURE.md` Section 6](07-LITERATURE.md#6-named-references-r1-r42).

## 0. Measured so far (official metric on legal real validation; updated 2026-10-14, R5)

| Lever | Track | Measured effect | Where |
|---|---|---|---|
| Synthetic walkers (engine G1) | LUMPI | Person 0 -> 0.341; mAP 0.168 -> 0.253 on realval-A | `model-lumpi-track/README.md` 7.2 |
| UT Van -> challenge Van | LUMPI | Van 0.034 -> 0.122 | same |
| Per-class post-processing (size, z, NMS, re-centering, hedges) | LUMPI | 0.210 -> 0.253 for `pointpillars-g1` | same |
| Per-class routing of two runs | LUMPI | 0.253 -> 0.260 (A), 0.156 -> 0.166 (B) | same |
| Background density calibration + frame selection | LUMPI | R 0.59 -> 0.906 | `data-lumpi-track/README.md` 8.7 |
| Walkers (G1 v1 / v2 body) | V2X | pedestrian 0 -> 0.118 / 0.173 | `model-v2x-track/README.md` 7 |
| FOV mask + walkers calibrated per range on legal walkers | V2X | realism R 0.901 -> 0.916 (0.922 selected); detection: `model-v2x-track/README.md` 7 | `data-v2x-track/README.md` 8 |
| Range-dependent z calibration after routing (C1, S1 close-out) | V2X | realval-B 0.520 -> 0.537; leaderboard 0.7665 -> **0.7855** (972563) | `model-v2x-track/README.md` 7.4 |
| CenterPoint members routed per class (S2) | LUMPI | Bicycle 0.102 -> 0.128 (B), mAP B 0.166 -> 0.170: below the upload gate | `model-lumpi-track/README.md` 7.5 |
| CenterPoint members routed per class (S2) | V2X | no class passes; pedestrian BEV-3D gap 0.158 -> 0.112 for the CenterPoint member | `model-v2x-track/README.md` 7.5 |
| Static false positives (S2 diagnosis) | both | 72-77% (V2X), 50-69% (LUMPI) of unmatched walker boxes are static; oracle bound V2X pedestrian B 0.252 -> 0.346 | Section 8.2.1 |
| TTA variants (8 views) as routable members (S3) | V2X | B-mAP 0.537 -> 0.617 (truck +0.114, vehicle +0.081, pedestrian +0.044) | Section 8.3.1 |
| Cross-architecture box fusion of TTA members (S3) | V2X | B-mAP 0.617 -> 0.666; BEV-3D gap on B 0.129 -> 0.063; ranked static false positives 6.2 -> 1.8 per frame | Section 8.3.1 |
| TTA and fusion (S3) | LUMPI | B-mAP 0.170 -> 0.185 (Person, Car, Bicycle, Truck), A 0.272 -> 0.302, late-A 0.271 -> 0.298 | Section 8.3.1 |
| Per-class score floors for the server cost (S3) | both | 66-78% fewer boxes for at most -0.0014 B-mAP | Section 8.3.1 |
| S3 on the leaderboard (2026-10-10) | both | V2X 0.7855 -> **0.8381** (974400, mAP 0.4869 -> 0.5483, rank 1); LUMPI 0.4728 -> **0.5015** by the scorer log (mAP 0.1357 -> 0.1692; Bicycle 0.053 -> 0.224) | Section 8.3.1 |
| Two-stage members (Voxel R-CNN, PV-RCNN++) in the fusion (S4) | V2X | B-mAP 0.664 -> 0.679 (vehicle +0.024, truck +0.022); vehicle localization loss 0.140 -> 0.058; walker localization unchanged | Section 8.4.1 |
| Two-stage members in the fusion (S4) | LUMPI | Bicycle B 0.173 -> 0.202; mAP B 0.184 -> 0.188: below the upload gate | Section 8.4.1 |
| S4 on the leaderboard (2026-10-10/11) | both | V2X 0.8381 -> **0.8485** (975938; vehicle +0.027, truck +0.010); LUMPI 0.5015 -> **0.5040** (975871; Bicycle 0.224 -> 0.244): **rank 1 on both tracks** | Section 8.4.1 |
| Class-wise random object scaling (S5 ROS, real size ranges) | both | V2X Voxel R-CNN TTA B 0.632 -> 0.667 (truck +0.082, pedestrian +0.034); LUMPI 0.170 -> 0.189 (Bicycle, Truck, Bus) | Section 8.5.1 |
| GBlobs inputs (S5 run a) | both | below the parent as a member (LUMPI Person 0.189 -> 0.098 on A); useful only inside fusions | Section 8.5.1 |
| S5 portfolio (`routed-g5`) | both | V2X B 0.679 -> 0.699 (estimate 0.967); LUMPI B 0.188 -> 0.209 (Truck 0.153 -> 0.200, Bus, Bicycle, Car) | Section 8.5.1 |
| S5 on the leaderboard (2026-10-11) | both | V2X 0.8485 -> **0.8730** (978945; pedestrian +0.046, truck +0.029); LUMPI flat 0.5040 -> 0.5039 (978931; Truck +0.038, Bicycle -0.030, Car -0.010), S4 stays the LUMPI entry | Section 8.5.1 |
| Engine G2-lite corpus `g1-v4` (R3): re-cast real-size objects, riders, static clutter | both | position-matched density LUMPI Car 0.44 -> 0.83, two-wheelers 0.25-0.52 -> 0.90-1.04 of real; static walker false positives halved in every LUMPI two-stage member; members gain on V2X (pillars B 0.522 -> 0.567) and on LUMPI Bicycle, Bus, Person | Section 8.7.2 |
| Realism frames from `g1-v4` (R3) | both | LUMPI 0.905 -> 0.934 (held-out), V2X 0.919 -> 0.925 | Section 8.7.2 |
| R3 portfolio (`routed-g6`) with the final pooled gate | both | LUMPI B 0.188 -> 0.221 (Bicycle, Bus, Truck; the S5 Car change reverted), V2X B 0.699 -> 0.703 (pedestrian) | Section 8.7.2 |
| R3 on the leaderboard (2026-10-14) | both | LUMPI 0.5040 -> **0.5169** (986489; realism 0.891 -> 0.932, mAP 0.172 -> 0.168: Bicycle -0.056), V2X 0.8730 -> **0.8789** (986496; pedestrian +0.012, realism +0.0065): **rank 1 on both tracks** | Section 8.7.2 |
| Background density prior fitted to the G2-lite output (R5, corpus `g1-v5`) | V2X | realism of the selected frames 0.925 -> 0.937 as packaged; pillars truck B 0.758 -> 0.827 | Section 8.9.1 |
| Refined density prior (R5) | LUMPI | random frames +0.008 held-out, selected frames +0.0028: under the realism gate, R3 frames kept | Section 8.9.1 |
| Seeds of the two-stage members (R5) | both | seed variance up to 0.17 AP per class on B (V2X truck); LUMPI Person B +0.02-0.03 per seed member | Section 8.9.1 |
| R5 portfolio (`routed-g7`) | both | V2X B 0.703 -> 0.710 (vehicle +0.012, pedestrian +0.010 from tail copies), estimate 0.983; LUMPI Person B 0.145 -> 0.160 (late-A rule), estimate 0.565 | Section 8.9.1 |
| R5 on the leaderboard (2026-10-15) | both | V2X 0.8789 -> **0.8852** (990255; pedestrian +0.011, vehicle +0.002, realism +0.0065), LUMPI 0.5169 -> **0.5198** (990245; Person 0.157 -> 0.180): **rank 1 on both tracks** | Section 8.9.1 |
| Seed bags (S6): weighted box fusion of 3-4 seeds of one configuration | both | every bag at or above its best seed on both splits (V2X PV-RCNN++ B 0.680 -> 0.694, Voxel R-CNN 0.691 -> 0.697; LUMPI 0.196 -> 0.200 and 0.189 -> 0.192); no bag fusion beat R5's fusions by +0.01 on B | Section 8.6.1 |
| LUMPI Van judge (S6): early-A rank, late-A gate | LUMPI | Van A 0.120 -> 0.173, late-A 0.118 -> 0.173 (P 1.00); judged estimate 0.5796 -> 0.5860: upload gate passed | Section 8.6.1 |
| Realism frames from the whole `g1-v4` corpus (S6) | LUMPI | 0.9337 -> 0.9344 / 0.9313 as packaged: R5 frames kept; the scorer's draw varies by sd 0.0012-0.0025 | Section 8.6.1 |

**First leaderboard results (2026-10-06, strategy S1):** LUMPI 965614 combined 0.4728 (mAP 0.1357, R 0.8912), V2X 965633 combined 0.7665 (mAP 0.4648, R 0.9203), both rank 1. Realism transferred (V2X +0.001, LUMPI -0.014 vs held-out proxies); detection transferred at 0.82-0.89 x realval-B but only 0.52 x realval-A on LUMPI (Person 0.117, Bicycle 0.053, Truck 0.028 on the test frames). Per-class tables: `model-<track>/README.md` Section 9. **2026-10-09:** V2X S1+C1 (972563) 0.7855, mAP 0.4869, rank 1; LUMPI S1 is rank 2 since Oct 7 behind an entry with lower mAP (0.1185) but realism R 0.942, so LUMPI realism is now the most valuable LUMPI lever (Section 8.7). **2026-10-10:** S3 uploaded on both tracks: V2X 974400 combined **0.8381** (mAP 0.5483, rank 1 of 19); LUMPI scored **0.5015** by the scorer log (mAP 0.1692), above the LUMPI leader (0.4784), but the submission was still Running at the server after scoring. The S3 gains transferred at 0.8 x the realval-A gain on both tracks, while the realval-B gain over-predicted V2X (0.48 x) and under-predicted LUMPI (1.89 x). **2026-10-10/11:** S4 uploaded on both tracks: V2X 975938 combined **0.8485** (mAP 0.5605), LUMPI 975871 **0.5040** (mAP 0.1721, uploaded below its upload gate by the entrant's call): rank 1 on both tracks. Over the five uploads with a local change, the leaderboard gain had the right sign every time but was 0.25-1.74 x the realval-A gain and 0.48-1.90 x the realval-B gain; projections now use 0.6 x the mean of both (Section 8.4.1). **2026-10-11:** S5 uploaded: V2X 978945 combined **0.8730** (mAP 0.5890, rank 1); LUMPI 978931 0.5039, 0.00007 below the S4 entry (not confirmed; diagnosed in Section 8.5.1: the LUMPI test window answers the size-augmented Bicycle members with false positives no local split shows). **2026-10-14:** R3 uploaded: LUMPI 986489 **0.5169** (realism 0.891 -> 0.932), V2X 986496 **0.8789**, rank 1 on both. **2026-10-15:** R5 uploaded: V2X 990255 **0.8852** (pedestrian +0.011 from the walker tail copies, realism +0.0065), LUMPI 990245 **0.5198** (Person 0.157 -> 0.180 through the late-A rule), rank 1 on both. Register: [`decisions/README.md` Section 2](decisions/README.md#2-submission-register).

The thesis below holds: detection decides, the open points are per class, and the real train split lets us measure the target. The leaderboard adds one correction: **select on realval-A and realval-B jointly**, because realval-A alone over-predicted LUMPI. Planning estimates marked "est." remain for the levers not yet built.

---

## 1. The thesis

1. **The score is `0.857 * mAP + 0.4 * R`.** Realism is capped by a sampling floor (real-vs-real R is about 0.96 on V2X and 0.93-0.95 on LUMPI), and the winners are already at 0.91-0.93. **Detection decides the ranking.**
2. **The open points are per class, not per model.** The ECCV winners reached vehicle/Car AP of 0.59-0.67, but only 0.19 on V2X pedestrian (62% of that test set) and 0.01-0.21 on LUMPI Person, Truck, Bicycle and Van. **Synthesizing the missing and weak classes with the real annotation conventions is the main lever.** Better vehicle detectors are secondary.
3. **The rules let you measure the target.** The real train split (outside the forbidden window) gives a labeled validation set, real sensor calibration, real label conventions and real placement statistics. Every generator parameter becomes a hyperparameter fitted to those measurements.
4. **Match the test-time input distribution exactly.** Real test frames are resampled to 50k points; V2X frames carry about 31% (0,0,0) null returns; LUMPI frames merge 5 heterogeneous sensors in the Measurement4 local frame (ground at about z = -2.1 m). Train at that density and in that frame, and generate realism frames with that structure.
5. **Post-processing is worth real points,** and it is cheap to select on real val: per-class NMS, box re-centering, density-aware re-scoring, and TTA/ensembles. The winner's V2X mAP went from 0.075 to 0.43 on NMS settings alone.

## 2. Score budget and targets

### 2.1 Where the field is, and where we aim

| | Ours (2026-10-15) | Best other IEEE entry (2026-10-15) | ECCV final best (same scorer and data) | Must beat | Target | Stretch |
|---|---|---|---|---|---|---|
| V2X combined | **0.8852** (R5) | 0.662 | 0.746 | 0.76 | 0.80 (met) | 0.87 (met) |
| LUMPI combined | **0.5198** (R5) | 0.491 (R about 0.942) | 0.479 | 0.49 | **0.53** | 0.62 |

An independent estimate from the methods review, counting only levers already proven by the ECCV winners plus moderate VRU gains, is V2X 0.77-0.80 and LUMPI 0.50-0.52. The step from target to stretch is almost entirely VRU synthesis quality (V2X pedestrian, LUMPI Person/Bicycle) and LUMPI Truck.

### 2.2 Per-class plan (est.)

**V2X-Real**

| Class | Test GT | Winner AP | Our target | How |
|---|---|---|---|---|
| vehicle | 470 | 0.59-0.67 | 0.70 | UT + G2 vehicles, real-sized anchors, ensemble |
| pedestrian | 953 | 0.09-0.19 | **0.45** | Walkers **and riders** (bicycle, scooter, motorcycle) synthesized with real box conventions; ray-consistent insertion; per-class NMS; real-val-selected post-processing |
| truck | 124 | 0.53-0.59 | 0.60 | Trucks, vans, buses **and TrashCans** (42% of the class; apparently large static containers, verify) |
| **mAP / R / combined** | | 0.44 / 0.93 / 0.746 | **0.58 / 0.93 / 0.87** (stretch); 0.50 / 0.92 / 0.80 (target) | |

**LUMPI** (7 classes with GT)

| Class | Test GT | Best AP seen | Our target | How |
|---|---|---|---|---|
| Person | 512 | 0.21 | **0.40** | Procedural humans with real sizes; 5-sensor ray-consistent insertion; crowd-aware NMS |
| Car | 1258 | 0.64 | 0.66 | UT cars rescaled from 0.78x to real size; UT Van mapped by real-val evidence ([`data-lumpi-track/README.md`](../data-lumpi-track/README.md) Section 5) |
| Bicycle | 82 | 0.19 | 0.30 | Rider + bicycle as one box (the real convention; verify on real val) |
| Motorcycle | 27 | 0.12 | 0.15 | Rider + motorcycle |
| Bus | 25 | 0.02 | 0.05 | GT is noisy (mostly two-wheeler sized per inspection); low priority, emit hedged duplicates |
| Truck | 192 | 0.07 | **0.30** | Fix the 0.78x UT scale first; then multi-mode truck sizes from real statistics |
| Van | 79 | 0.08 | 0.20 | LUMPI id 6 "unknown" objects, van-sized on legal frames ([`data-lumpi-track/README.md`](../data-lumpi-track/README.md) Section 5); synthesize what they are; hedged duplicates |
| **mAP / R / combined** | | 0.13 / 0.91 / 0.479 | **0.29 / 0.93 / 0.62** (stretch); 0.19 / 0.92 / 0.53 (target) | |

### 2.3 Build-up (est., both tracks; B0-B4 are build steps, not strategy codes)

| Step | V2X combined | LUMPI combined |
|---|---|---|
| B0: UT-trained detector, correct class map, UT frames at 50k points (+ V2X null returns) | 0.62 | 0.40 |
| B1: + scorer-exact eval, real val, per-class NMS and post-processing selected on real val | 0.70 | 0.45 |
| B2: + VRUs synthesized with real conventions (G1 insertion) | 0.75 | 0.48 |
| B3: + real-calibrated sensor model, G2 corpus, class-specific fixes (Truck/Van/Bicycle, trash cans) | 0.78 | 0.51 |
| B4: + ensemble/TTA, realism frame selection | **0.80+** | **0.53+** |

## 3. Levers, ranked by value per effort

| # | Lever | Tracks | Est. gain | Effort | Depends on |
|---|---|---|---|---|---|
| 0 | **Fix UT-LUMPI's 0.78x actor scale** (a 0.78x box cannot reach IoU 0.5) | LUMPI | Likely the single largest LUMPI gain: Truck, Van, Bus and part of Car | 0.5-1 day | M4 |
| 1 | Scorer-exact local AP/realism + real validation set + ForbiddenGuard | Both | Enables every decision below | 2-3 days | Kit, real data |
| 2 | Match the test input distribution: 50k-point resampling, LUMPI local frame, V2X OS1-64 null returns (realism frames) | Both | +0.02-0.05 R; +0.01-0.02 mAP | 1-2 days | M2 |
| 3 | Per-class NMS, re-centering, density re-rank, low score floor, selected on real val | Both | +0.05-0.10 mAP on VRU classes | 1-2 days | Lever 1 |
| 4 | **VRU synthesis** (walkers + riders) with real box conventions, ray-consistent insertion | Both | V2X +0.08-0.12 combined; LUMPI +0.03-0.05 | 4-5 days | M6, M7, M8 |
| 5 | Real box conventions and size modes for every class (UT boxes are about 17% too small; LUMPI Truck is multi-modal) | Both | +0.02-0.05 combined | 1-2 days | M5 |
| 6 | Missing object types inside super-classes: V2X trash cans (truck), scooters/motorcycles with riders (pedestrian) | V2X | +0.01-0.03 | 1-2 days | M7 |
| 7 | Real-calibrated sensor model and fitted ray-drop in G1/G2. **V2X: the real unit is an OS1-64 (+/-16.7 deg); UT-V2X emulates a wide-FOV sensor with twice the points.** LUMPI: UT sensors sit at the wrong positions | Both | +0.01-0.03 mAP; +0.02-0.05 R on V2X | 4-5 days | M5, M6 |
| 8 | Detector choice and DG augmentation selected on real val (PointPillars, CenterPoint, VoxelNeXt, DSVT): **strategies S2, S4, S5, S6** ([Section 8](#8-strategy-routes-after-s1)) | Both | +0.02-0.04 | GPU-bound | Capacity |
| 9 | Ensembles, TTA, 3D WBF: **strategy S3** | Both | +0.01-0.03 | 2 days | 2+ good models |
| 10 | Class-hedged duplicates (Car/Van, Bus/Truck, Bicycle/Motorcycle) with discounted scores | LUMPI | +0.005-0.015 | 0.5 day | Real val |
| 11 | Realism frame selection from the generated pool against our legal real proxy | Both | +0.01-0.03 R | 1 day | M3, M5 |
| 12 | Gated: background-occupancy prior, self-training, real-reconstructed scene | Both | +0.01-0.05 | 3-5 days | Organizer answers |

**Dropped from the Sep-17 plan:** building CARLA twins; per-class score thresholds; 220k-point LUMPI frames; "frame diversity for FPD/MMD"; treating realism as co-equal with detection.

**Deliberately not done:** metric-only warping of the submitted frames, server "realism probes", any use of the 50 test point clouds beyond inference, and downloading any reference bundle.

## 4. Decision gates

Gates A-F below are the original build gates of the plan: A passed with the S1 uploads; B is partly met (real validation is live, but LUMPI realval-A over-predicted the leaderboard, so the strategy gates rank on realval-B); C passed locally; D is replaced by the R track (Section 8.7); E (freeze) and F (dev close) still apply.

**Strategy gates (from 2026-10-09)** are kept with the submissions in [`decisions/README.md`](decisions/README.md):

| What | Where |
|---|---|
| Class gate, upload gate, confirmation rule, freeze and final-submission rules, with their rationale | [Section 3.2](decisions/README.md#32-gates) |
| The scorecard every candidate is measured with | [Section 3.1](decisions/README.md#31-scorecard) |
| Every upload and decision-ready version, with its gate result and leaderboard outcome | [Section 2](decisions/README.md#2-submission-register) |
| Progression of every version against S1 | [Section 4](decisions/README.md#4-progression-tracker) |
| Calendar and compute plan, with status | [Section 5](decisions/README.md#5-calendar-and-compute-plan) |
| One dated record per decision (named `YYYY-MM-DD-<strategy or scope>-<topic>.md`) | [Section 6](decisions/README.md#6-decision-records) |

Original build gates:

| Gate | Date | Pass criterion | If it fails |
|---|---|---|---|
| A: loop closed | Sat Oct 3 | Legal submissions on both tracks; local score equals the server score to 1e-4 on the same zip | Stop feature work until fixed |
| B: real val live | Wed Oct 7 | Real val built for both tracks with the guard; its per-class AP ordering agrees with the leaderboard for our first 2-3 submissions | Re-check class maps and frames |
| C: VRUs work | Mon Oct 12 | V2X pedestrian real-val AP >= 0.30; LUMPI Person >= 0.25 | Fix conventions and sizes before assets |
| D: G2 earns its place | Sun Oct 18 | G1+G2 beats G1 on real-val mAP, or G2 frames beat G1/UT frames on the realism proxy | Keep G2 only where it wins |
| E: feature freeze | Sun Oct 25 | Final configs selected on real val | Only ensembles, frame selection and packaging after this |
| F: dev close | Fri Oct 30, 17:00 PDT | Final dev submissions; all artifacts archived | |
| Final | Nov 1-14 | 1/day; last planned by Thu Nov 12 | 1-2 kept in reserve |

## 5. Using the public leaderboard correctly

- Dev and final phases score **the same test and reference data**. The dev leaderboard is the test set.
- Decide on the real validation set; use the leaderboard only to **confirm**. About 2-3 pre-validated submissions per day per track.
- Never submit to "probe" the realism reference (for example zeroing detection to isolate realism). The winner did this; the IEEE rules forbid it.

## 6. Rule-gated upside branches

| Branch | Organizer question (`01` S10) | Default |
|---|---|---|
| Self-training on unlabeled real | Q1 | Off |
| Real-reconstructed scene, learned ray-drop, background prior | Q2 | Off (sensor-parameter fitting stays on) |
| Post-processing scalars selected on real labels | Q3 | On, but prefer generator-side fixes; switch off if told otherwise |

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Shared GPUs (another user at 100% on all 8) | High | High | Reservation request on D0; 2-GPU recipes; PointPillars/CenterPoint first (fast) |
| Disk (no `/scratch`; free space on `/` swung between 233 GB and 1.4 TB on Sep 30; `/data` 96% full) | Medium | Medium | One data root `$BDC_DATA` on the workspace drive (layout: root `README.md` Section 3); UT data already downloaded (69 GB); float32 corpora regenerated from recipes; check `df -h /` before big jobs |
| Wrong class map (V2X super-classes, LUMPI class IDs) | Medium | Very high | Class-map unit tests; compare real-val per-class counts against the public test GT counts (aggregate sanity only) |
| Wrong frame or density protocol | Medium | High | M2 tests; the first submission is a frame/density sanity check |
| VRU synthesis does not transfer | Medium | High | Gate C; iterate conventions first |
| ECCV teams join late | Medium | Medium | Targets set above their finals |
| Final-phase packaging error (1/day) | Low | Very high | Validator; dry-run the exact final zip in the dev phase |
| Gray-area ruling goes against us | Low | Low | Core plan never depends on a gated branch |

## 8. Strategy routes after S1

A strategy is the complete recipe behind one submission per track: synthetic data, detectors, post-processing, routing or fusion, and the 50 realism frames. S1 is the submitted baseline (code at tag 0.1). The routes S2-S6 come from the detector research in [`07-LITERATURE.md` Section 7](07-LITERATURE.md#7-detector-research-for-the-next-strategies-2026-10-06) and are **ordered by increasing effort and risk; the order is the execution order**. Each one is cumulative: it keeps everything of the previous strategy that passed its gate.

Every strategy below uses the same template: **hypothesis** (what it should fix, in which metric), **prerequisites**, **steps**, **evaluation** (numbers and expected direction), **gate** (keep or drop), **deliverables**, **risks and fallbacks**, **time box**. Progress is measured with one protocol and one tracker table ([`decisions/README.md` Sections 3-4](decisions/README.md#3-evaluation-protocol-and-gates)), so every strategy is compared against the same S1 baseline.

### 8.0 Overview

| Code | Name | Stage | Changes vs the previous strategy | Gap it targets | Effort (est.) | Risk | Research |
|---|---|---|---|---|---|---|---|
| **S1** | Calibrated Twin, Routed Pillars | **submitted** (965614, 965633); S1+C1 submitted on V2X (972563, 0.7855; Section 8.1.3) | engine G1 data, PointPillars x 2-4 runs, per-class post-processing and routing | missing walkers, actor scale, density | done; close-out 1-2 days | done | [R1](07-LITERATURE.md#r1-urbantwin-papers), [R5](07-LITERATURE.md#r5-pointpillars), [R7](07-LITERATURE.md#r7-statistical-normalization), [R9](07-LITERATURE.md#r9-lidar-aug), [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports) |
| **S2** | Center-Routed Small Objects | **done 2026-10-09**: no upload-ready version; LUMPI Bicycle route and CenterPoint members carried to S3 (8.2.1) | CenterPoint specialists for small classes, routed with the S1 pillars; routes chosen on realval-A and B jointly | LUMPI Person, Bicycle, Motorcycle; V2X pedestrian, including its height loss | 4 days; about 32 GPU-hours | low | [R22](07-LITERATURE.md#r22-centerpoint), [R24](07-LITERATURE.md#r24-inscope), [R41](07-LITERATURE.md#r41-pillarnet), [R42](07-LITERATURE.md#r42-mmdetection3d-model-comparison-secondary-source) |
| **S3** | Fused Portfolio with TTA | **submitted 2026-10-10**: V2X 974400 combined 0.8381 (rank 1); LUMPI scored 0.5015 by the scorer log, status Running at the server (8.3.1) | test-time augmentation as routable member variants; per-class box fusion of members; per-class score floors | run-to-run variance; V2X height | 1 day; about 3 GPU-hours | low | [R23](07-LITERATURE.md#r23-weighted-boxes-fusion), [R37](07-LITERATURE.md#r37-ms3d-kde-box-fusion), [R38](07-LITERATURE.md#r38-horizonlidar3d), [R39](07-LITERATURE.md#r39-robosense-2025-report), [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports) |
| **S4** | Two-Stage Refinement | **submitted 2026-10-10/11**: V2X 975938 0.8485, LUMPI 975871 0.5040, rank 1 on both (8.4.1) | Voxel R-CNN and PV-RCNN++ members (plain and TTA, per-class score blend) in fusions of up to three members | walker localization (revised after the S3 review); in effect vehicle, truck and bicycle | 1 day; about 50 GPU-hours (4 runs at once) | medium | [R29](07-LITERATURE.md#r29-pv-rcnn), [R30](07-LITERATURE.md#r30-voxel-r-cnn), [R25](07-LITERATURE.md#r25-robo3d), [R24](07-LITERATURE.md#r24-inscope) |
| **S5** | Geometry-Invariant Inputs | **submitted 2026-10-11**: V2X 978945 0.8730 (rank 1); LUMPI 978931 0.5039, flat, not confirmed (S4 stays the entry) (8.5.1) | GBlobs (cell covariance) and class-wise object scaling (ROS) on Voxel R-CNN; ROS extended to PV-RCNN++ and the pillars; fused | the transfer gap; in effect the twin's size gap (trucks, bicycles, buses) | 1 day; about 100 GPU-hours (8 runs) | medium | [R27](07-LITERATURE.md#r27-gblobs), [R28](07-LITERATURE.md#r28-gblobs-for-sensor-placement), [R26](07-LITERATURE.md#r26-lidar-domain-generalization-study), [R36](07-LITERATURE.md#r36-dts-random-beam-re-sampling), [R40](07-LITERATURE.md#r40-st3d) |
| **R3** | Engine G2-lite (extended step after S5) | **submitted 2026-10-14**, the entry on both tracks until R5: LUMPI 986489 **0.5169** (rank 1; realism 0.891 -> 0.932, mAP -0.004), V2X 986496 **0.8789** (rank 1) (8.7.1-8.7.2) | corpus `g1-v4`: actors re-cast at real size and density with the real rig, real-sized trucks, buses and two-wheelers with riders, unlabeled static clutter; retrained S5 members; pooled A+B class-gate condition | the twin's object geometry: Car and two-wheeler density, size-gap classes, static walker false positives | 2 days; about 60 GPU-hours | medium | [R9](07-LITERATURE.md#r9-lidar-aug), [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports), [R40](07-LITERATURE.md#r40-st3d) |
| **R5** | Realism-led refinement (after R3) | **submitted 2026-10-15, the current entry on both tracks**: V2X 990255 **0.8852**, LUMPI 990245 **0.5198** (rank 1 on both) (8.9-8.9.1) | background density prior for the G2-lite corpus (`g1-v5`; V2X first prior), seeds of the two-stage members, V2X members on `g1-v5`, walker tail copies, pre-registered late-A Person rule and rare-class freeze | background realism (EMD), seed variance, LUMPI Person | 1 day; about 60 GPU-hours | low | [R9](07-LITERATURE.md#r9-lidar-aug), [R40](07-LITERATURE.md#r40-st3d) |
| S6 | Variance-Controlled Final Portfolio (re-planned 2026-10-15; was Sparse Transformer Experts) | **planned** (8.6) | seed bags of the strongest two-stage configurations; LUMPI Van judged on realval-A frames whose labels are vans; final-phase protocol | member noise (seed spread up to 0.17 AP); the frozen LUMPI Van | about 1.5 days; about 120 GPU-hours (16 h on 8 GPUs) | low | [R23](07-LITERATURE.md#r23-weighted-boxes-fusion), [R37](07-LITERATURE.md#r37-ms3d-kde-box-fusion) |

GPU-hours are on the A6000s, from the measured PointPillars runs (LUMPI 40 epochs in 1 h 46 min on 4 GPUs, about 7 GPU-hours; V2X about 4) times the usual cost ratio of each family (center-head voxel models 2-3x, two-stage 4-5x, sparse transformers 5x or more). Each is replaced by the measured smoke-run speed before the full run. Dependencies checked on 2026-10-09: CenterPoint, PV-RCNN++ (its `vector_pool` ops are compiled) and Voxel R-CNN with `MeanVFE` run on the installed stack; DSVT and every dynamic-voxel encoder need `torch_scatter`, which is not installed.

**Evaluation, gates and calendar.** The scorecard, the class gate, the upload gate and the confirmation rule, the progression tracker, the calendar and compute plan, and the register of every submission are in [`decisions/README.md`](decisions/README.md) ([Section 2](decisions/README.md#2-submission-register) register, [3](decisions/README.md#3-evaluation-protocol-and-gates) protocol and gates, [4](decisions/README.md#4-progression-tracker) tracker, [5](decisions/README.md#5-calendar-and-compute-plan) calendar). Each strategy below refers to those gates; a version that passes the upload gate gets a dated record there named for its strategy.

### 8.1 S1 Calibrated Twin, Routed Pillars

**Idea:** keep the organizers' twins [R1](07-LITERATURE.md#r1-urbantwin-papers) as the base, repair what they get wrong for the real sensors and annotators, train PointPillars [R5](07-LITERATURE.md#r5-pointpillars) on synthetic data only, calibrate box conventions per class on legal real validation, and route each class to the best of a few training runs.

| Component | Track 1 LUMPI | Track 2 V2X-Real | Research |
|---|---|---|---|
| Base synthetic data | UT-LUMPI, simulated with the real Measurement4 rig (beam residual 0.03 deg) | UT-V2X-Real-IC | [R1](07-LITERATURE.md#r1-urbantwin-papers) |
| Box and size conventions | actors rescaled by 1/0.78; UT Van trained as the challenge Van | walker boxes from legal label statistics; vehicle and truck sizes calibrated in post-processing | [R7](07-LITERATURE.md#r7-statistical-normalization), [R8](07-LITERATURE.md#r8-pcgen) |
| Missing classes | articulated walkers ray-cast with the five real lidars, ray-consistent occlusion, placement and sizes from legal Person labels; walker v2 body matched to real cluster spread | walkers ray-cast with the measured OS1-64 beam table at legal walker positions; point counts matched per range; UT points outside the real FOV masked | [R9](07-LITERATURE.md#r9-lidar-aug), [R10](07-LITERATURE.md#r10-drcpo), [R11](07-LITERATURE.md#r11-real3d-aug), [R12](07-LITERATURE.md#r12-huch-et-al-sim-to-real-gap) |
| Background and density | real/synthetic density ratio (8 x 8 x 2.5 m cells) from 400 unlabeled legal frames (gray area, disclosed) | 31% (0,0,0) nulls; organizer-style 50k resampling | [R13](07-LITERATURE.md#r13-lidarsim) |
| Detector | PointPillars, 0.15625 m pillars, xyz only, OpenPCDet 233f849, 40 epochs on 4 GPUs; members `pointpillars-g1`, `pointpillars-g1v3` | members `pointpillars-ut`, `pointpillars-g1v2`, `pointpillars-g1v3` | [R5](07-LITERATURE.md#r5-pointpillars), [R6](07-LITERATURE.md#r6-openpcdet) |
| Post-processing | per class: NMS IoU, re-centering, size and z offset, cross-class hedges; tuned on realval-A, behaviour knobs guarded by realval-B | same | [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports) |
| Routing | Person, Motorcycle, Bus, Truck from `g1v3`; Car, Bicycle, Van from `g1` | vehicle `g1v2`, pedestrian `g1v3`, truck `ut` | |
| Realism frames | 50 `g1-v2` val frames by pooled-moment matching to legal proxies 1-3 | 50 `g1-v3` val frames, same selection | [R15](07-LITERATURE.md#r15-chamfer-and-earth-movers-distances)-[R18](07-LITERATURE.md#r18-pot) |

**Result:** LUMPI 0.4728 (rank 1; 0.007 below the ECCV winner, from realism), V2X 0.7665 (rank 1; above the ECCV winner). Baseline rows: [`decisions/README.md` Section 4](decisions/README.md#4-progression-tracker).

#### 8.1.1 Reproduction steps (how S1 was built)

From the repository root after `source common/env/activate.sh`; full commands in the track model READMEs Section 6 and the data READMEs.
1. Data: `fetch_ut.py`, `ingest_kit.py`, `fetch_real.py` (licence accepted), V2X `resolve_test_ids.py`; then `prepare_realval.py` (realval-v1 and realism proxies 1-5) on both tracks.
2. Corpora: LUMPI `prepare_g1.py` `g1-v1`, `fit_density_prior.py`, `g1-v2` (density prior), `g1-v3` (walker v2); V2X `prepare_ut.py ut-v1`, `prepare_g1.py` `g1-v1`, `g1-v2`, `g1-v3` (walker prior, FOV mask, gain 2.5).
3. Training: `train/train.sh 4 run1 --fix_random_seed --workers 6` for every member (40 epochs).
4. Validation: `validation/tune_and_eval.sh <ckpt>` per member (raw predictions on A and B, two-phase tuner, hedges, official scores).
5. Routing: `route_predictions.py select model-<track>/routed-g1` (best on A, ties within 0.005 broken by B).
6. Realism frames: `select_realism_frames.py` (fit proxies 1-3, held-out 4-5) into `routed-g1/test/synthetic_ids.txt`.
7. Packaging and upload: `routed-g1/test/make_submission.sh first`, `check_submission.py --official`, upload unchanged, `package_submission.py --record`. Artifacts: tag 0.1, release 0.1, `submissions/2026-10-02_first/`.

#### 8.1.2 Close-out steps (before S2)

Tools that every later strategy needs:
- **T1 joint routing rule:** `route_predictions.py select --rule joint` ranks members per class by the mean of realval-A and realval-B AP and applies the class gate; `--rule a` keeps the S1 behaviour. Test: on the S1 members it must reproduce the S1 route except where B disagrees (report those classes).
- **T2 scorecard:** `common/tools/scorecard.py <model_dir> [--vs <model_dir>] [--bootstrap 200]` reads the stored validation JSONs (they already hold 3D and BEV AP at 0.5 and 0.7 per class), the realism estimate and any `codabench_<id>.json`, computes the scorecard metrics ([`decisions/README.md` Section 3.1](decisions/README.md#31-scorecard)) and the paired-bootstrap deltas (frame resampling of predictions and GT), writes `scorecard.json` and prints a tracker row. Test: S1 rows equal the progression tracker.
- **T3 strategy tag:** a `strategy` field in `model.yaml` and a `strategy` column in `registry.csv` (`bdc26.registry.FIELDS`), filled by `eval_predictions.py` and `package_submission.py`.
- **T4 evaluation subsets and breakdowns:** `eval_predictions.py --frames-from <ids.txt>` (subsets such as late-A) and `--breakdown` (AP by range 0-20, 20-40, 40+ m and by points in the GT box; height and z-centre error of BEV-matched pairs).

Diagnostics, each a short table appended to the track model README Section 7 (all on legal real data; nothing touches the test frames):
- **D1 test class mix vs realval** (done from the kit's public GT counts): objects per frame, test vs realval-A. LUMPI: Person 10.2 vs 17.4, Car 25.2 vs 27.9, Bicycle 1.6 vs 4.8, Motorcycle 0.54 vs 0.02, Bus 0.50 vs 0.17, Truck 3.8 vs 1.0, Van 1.6 vs 1.4; realval-B is closer for Truck (1.7), Motorcycle (0.30) and Bus (0.31). V2X: vehicle 9.4 vs 8.1, pedestrian 19.1 vs 16.2, truck 2.5 vs 1.7. **Reading:** the LUMPI test window has a different traffic mix (3.7x the trucks, 23x the motorcycles per frame), one more reason to select on B.
- **D2 height and z error (V2X first, then LUMPI):** with T4 on S1 predictions, the distribution of z-centre and height errors of BEV-matched pairs per class, against range and position. Measured so far: V2X pedestrian BEV@0.5 0.426 vs 3D 0.266 on realval-A (0.384 vs 0.226 on B), vehicle 0.752 vs 0.627; LUMPI gaps are small (B 0.191 vs 0.166). **Decision it feeds:** a constant bias means post-processing (already tuned, so unlikely); errors that grow with distance or follow the slope mean a z-resolution problem (S2 voxels, S4 refinement) or a ground-height model (Section 8.7); a wide spread means localization noise (S3 TTA, S4).
- **D3 temporal drift (LUMPI):** S1 AP on realval-A Measurement4 frames 0-3199, 3200-4799 and 4800-6399 (T4 subsets). If AP falls toward 6400 (the start of the excluded window), late-A joins B in the class gate.
- **D4 failure profile:** T4 breakdown by range and points in box for LUMPI Person, Bicycle, Truck and V2X pedestrian on A and B. Tells whether S2 should target far and sparse objects (feature stride, minimum heat-map radius).
- **D5 LUMPI Truck sizes:** length, width and height modes of legal Truck labels (Measurement4 and Measurement5-6) vs the single S1 truck anchor (7.94 x 2.89 x 3.46) and the predicted sizes. Feeds the S2 head groups, the S4 targets and any truck size modes in post-processing (the ECCV winner's 3-mode truck anchors helped [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports)).
- **O1 organizer email** (the entrant's action, pending since day 1): density prior, research-phase exposure, label statistics, self-training ([`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md) Section 10).

**Gate (close-out done):** T1-T4 pass their tests, the S1 tracker rows are reproduced by T2, and D2-D5 are written up. **Passed 2026-10-09** (Section 8.1.3).

#### 8.1.3 Close-out results (2026-10-09)

All on legal real validation with the S1 `routed-g1` predictions; files in `model-<track>/routed-g1/validation/results/` (`scorecard.json`, `diagnostics/`). Tests: `common/tests/test_closeout.py` (6 tests; 44 in the suite).

| Item | Result |
|---|---|
| T1 joint routing | `route_predictions.py select --rule joint`. On the S1 members it reproduces the S1 route on both tracks; the only different candidate (LUMPI Motorcycle from `g1`) fails the class gate (B -0.001). **Joint routing alone gives no new submission.** |
| T2 scorecard | `common/tools/scorecard.py` (library `common/bdc26/scorecard.py`): reproduces the stored official numbers exactly (V2X A 0.5718, B 0.5204); exact realism of the S1 zips 0.905 (LUMPI) and 0.919 (V2X); 8 s (V2X) and 40 s (LUMPI) |
| T3 strategy tag | `strategy: S1` on all 9 model cards; `strategy` column in both registries (`registry.migrate`) |
| T4 subsets and breakdowns | `eval_predictions.py --frames-from` (late-A: 0.2546, equal to the scorecard) and `--breakdown` (`common/bdc26/diagnostics.py`) |
| D1 test class mix | Section 8.1.2 (LUMPI test: 3.7x the trucks, 23x the motorcycles per frame of realval-A) |
| D2 height and z | V2X pedestrian z error +0.16 / +0.08 / +0.03 / -0.11 m at 0-10 / 10-20 / 20-30 / 30+ m (the same on B); pedestrians predicted 0.10 m too tall; trucks 0.35 m too tall. LUMPI: 91% (A) / 84% (B) of BEV-matched Persons already reach 3D IoU 0.5, so LUMPI loses recall and size, not height |
| D3 drift (LUMPI) | realval-A by frame band 0-3199 / 3200-4799 / 4800-6399: mAP 0.272 / 0.237 / 0.255; **Person 0.421 / 0.225 / 0.196**; Truck 0.223 / 0.002 / 0.387 (scene-dependent). The late band has 10.8 Persons per frame, like the test (10.2) |
| D4 failure profile | LUMPI Person recall (score >= 0.3, 3D IoU 0.5) by points in box 1-10 / 10-30 / 30-100 / 100+: 0.24 / 0.51 / 0.65 / 0.64 on A, 0.21 / 0.38 / 0.42 / 0.23 on B (dense Persons missed on B); V2X pedestrian AP by range 0.18 / 0.36 / 0.35 / 0.15 |
| D5 LUMPI Truck sizes | real realval-A trucks are multi-modal: 5-6 m (224), 8-9 m (364), 12-14 m (213), 14-20 m (176); **the synthetic training trucks (`g1-v3`) are at most 8.47 m**, so trucks longer than 12 m are predicted near 9.2 m (median, GT 12.3 m). A generator gap: the twin needs long trucks and trailers |
| O1 organizer email | pending (the entrant's action) |
| **C1 candidate** | range-dependent z calibration after routing (`common/bdc26/detect/zcalib.py`, `route_predictions.py calibrate`), selected on A, class gate on B. V2X: vehicle and pedestrian kept, truck dropped; LUMPI: dropped for every class. Details: [`decisions/2026-10-09-s1-closeout-z-calibration.md`](decisions/2026-10-09-s1-closeout-z-calibration.md) |

**Close-out decision.**
- **Track 2 (V2X): submitted as S1+C1, 972563, combined 0.7855 (confirmed; rank 1).** `model-v2x-track/routed-g1z` (S1 + C1) passes the upload gate: realval-B mAP 0.520 -> 0.537 (bootstrap 90% interval of the gain +0.014 to +0.021), combined estimate (B) 0.814 -> 0.828 (+0.014), identical realism frames, official check valid in 86 s. Zip: `model-v2x-track/routed-g1z/submissions/2026-10-09_zcal/submission.zip`.
- **Track 1 (LUMPI): no new submission.** No close-out change passes the gate; S1 stays.
- **Inputs to S2 and later:** use late-A in the LUMPI gate (D3); V2X far-range pedestrians and LUMPI dense Persons on B are the S2 targets (D4); the V2X BEV-3D gap left after C1 (0.129 on B) is the S2-S4 height target; LUMPI Truck needs long trucks in the generator (D5), which no detector change can supply.

### 8.2 S2 Center-Routed Small Objects

**Hypothesis.** An anchor-free center head [R22](07-LITERATURE.md#r22-centerpoint) on a sparse 3D voxel backbone [R21](07-LITERATURE.md#r21-second) localizes small objects better than pillars, and its z voxels (0.25 m, against one 10 m pillar) reduce the pedestrian height loss. Targets: LUMPI Person, Bicycle and Motorcycle B AP; V2X pedestrian B AP and its BEV-3D gap.

**Prerequisites.** S1 close-out (T1-T4; D2 and D4 shape the config).

**Configuration** (both tracks; built from OpenPCDet's mainline `cfgs/waymo_models/centerpoint.yaml`):

| Part | Setting | Note |
|---|---|---|
| Data processor | voxels 0.1 x 0.1 x 0.25 m, 10 points per voxel, 60,000 voxels (train and test) | 50,000 points per frame; z: LUMPI [-5, 5], V2X [-8, 2], both 40 voxels |
| Encoder and backbone | `MeanVFE` (xyz), `VoxelResBackBone8x`, `HeightCompression` (256 BEV features: 40 z voxels compress to 2 x 128) | as the Waymo config, whose z grid is also 40 |
| BEV backbone | `BaseBEVBackbone`, layers [5, 5], strides [1, 2], filters [128, 256], upsampling to stride 8 | 0.8 m output cells; variant: stride 4 for small classes (step 5) |
| Head | `CenterHead`, head groups LUMPI [Person], [Bicycle, Motorcycle], [Car, Van, Unknown], [Truck, Bus]; V2X [pedestrian], [vehicle], [truck]; heads center, center_z, dim, rot | Gaussian overlap 0.1, minimum radius 2, 500 objects per frame |
| Raw output | score >= 0.01, NMS 0.9 per head, 500 boxes per head | near-raw, as the pillars; real NMS is per class in post-processing |
| Optimization | adam_onecycle, LR 0.003, weight decay 0.01, 40 epochs, batch 4 per GPU on 4 GPUs, `--fix_random_seed`; same augmentation and GT sampling as the pillars | cut to 30 epochs if the smoke run predicts more than 6 h |

**Steps.**
1. Scaffold `centerpoint-g1v3` on both tracks: `python common/tools/new_model.py <track> centerpoint-g1v3 --from pointpillars-g1v3`; write `train/pcdet_model.yaml` and the data-processor block of `train/pcdet_dataset.yaml` per the table; set `strategy: S2` and the architecture in `model.yaml`.
2. Smoke run: `CUDA_VISIBLE_DEVICES=0 bash model-<track>/centerpoint-g1v3/train/train.sh 1 smoke --epochs 2 --workers 6`; check that the loss falls, `pcdet_predict.py --raw --limit 20` on `pcdet/realval-v1` returns boxes of every class inside the range, and record the seconds per iteration (replaces the GPU-hour estimate).
3. Full runs in parallel: LUMPI on GPUs 0-3, V2X on GPUs 4-7, `train.sh 4 run1 --fix_random_seed --workers 6`.
4. Validate: `validation/tune_and_eval.sh <ckpt>` (the unchanged tuner), then `scorecard.py model-<track>/centerpoint-g1v3 --vs model-<track>/pointpillars-g1v3 --bootstrap 200`.
5. Only if the target classes miss the class gate and D4 shows far or sparse misses: one variant run with stride-4 output (upsampling to stride 4 for the small-class heads) or the pillar fallback PillarNet [R41](07-LITERATURE.md#r41-pillarnet); nothing else is tuned.
6. Route: `python common/tools/new_model.py <track> routed-g2 --from routed-g1`; add the member `cp: centerpoint-g1v3` in `model.yaml`; `route_predictions.py select --rule joint model-<track>/routed-g2`; the class gate decides each class (vehicle classes are expected to stay on pillars); then `route_predictions.py calibrate model-<track>/routed-g2` re-selects the C1 z calibration for the new route (Section 8.1.3).
7. Realism frames: S1's `synthetic_ids.txt` unchanged (the R track replaces them only after its own gate, Section 8.7).
8. Scorecard of `routed-g2` vs `routed-g1`; upload gate.
9. Package and upload: `routed-g2/test/make_submission.sh second`, `check_submission.py --official`, upload unchanged, save `codabench_<id>.json`, `--record`, tracker row and register row ([`decisions/README.md`](decisions/README.md) Sections 2 and 4), a dated `s2-...` decision record, root README Section 9 row, zip handed over for the GitHub release.

**Evaluation.** Primary: per-class B AP of LUMPI Person, Bicycle, Motorcycle and V2X pedestrian; V2X pedestrian BEV-3D gap on B (expected to shrink with z voxels). Secondary: 3D@0.7, B/A ratio, late-A. Expected (est., discounted from real-data benchmarks [R24](07-LITERATURE.md#r24-inscope)): +0.02 to +0.05 B AP on the target classes; combined +0.005 to +0.02 per track.

**Gate.** Class gate per class ([`decisions/README.md` Section 3.2](decisions/README.md#32-gates)); success for the strategy means at least one target class per track passes and the upload gate holds.

**Deliverables.** `model-<track>/centerpoint-g1v3/`, `model-<track>/routed-g2/` (with `submissions/<date>_second/`), scorecards, registry rows, tracker row, track README Sections 1, 7 and 9, root README Section 9.

**Risks and fallbacks.** Center heads regress synthetic box sizes directly (the tuner's size calibration still applies); heat-map peaks weaken on sparse distant walkers (step 5); the ECCV winner reported CenterPoint no better than pillars here [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports) (their data, not ours): if no class passes, S2 ends with `routed-g1` unchanged and S3 starts on the S1 members.

**Time box.** Sat Oct 10 - Tue Oct 13; about 32 GPU-hours.

#### 8.2.1 Results (2026-10-09)

**Implementation.** Members `centerpoint-g1v3` (stride 8) and `centerpoint-s4-g1v3` (stride 4, the step-5 variant) on both tracks, trained on `pcdet/g1-v3` with the S1 augmentation; routed models `routed-g2` (LUMPI from `routed-g1`, V2X from `routed-g1z`). New tools: [`pcdet_smoke.py`](../common/tools/pcdet_smoke.py) (measured cost: V2X 0.19 s and LUMPI 0.28 s per iteration, 1.1 h and 1.75 h for 40 epochs on 4 GPUs, about 5 and 7 GPU-hours instead of the planned 32), `route_predictions.py validate` and `select --rule joint --calibrated` (members compared after their own gated z calibration, the rule `calibrate` applies after routing; checked to reproduce the S1+C1 route and calibration exactly).

**OpenPCDet bug found and fixed.** `CenterHead.assign_targets` (233f849) overwrites class labels in place across head groups, so with head groups not in class order a class trains a later head: on V2X every pedestrian became a vehicle target (the vehicle head emitted about 96 pedestrian-sized boxes per frame; vehicle 3D AP 0.019 at epoch 12), on LUMPI Motorcycles trained the Car head. Fixed at runtime in [`pcdet_patches.py`](../common/bdc26/detect/pcdet_patches.py) with a regression test; the affected runs were discarded (`run0_labelbug`) and retrained (V2X vehicle at epoch 12: 0.019 -> 0.546).

**Members on real validation** (official 3D AP@0.5, tuned post-processing; realval-A / realval-B):

| Track / class | Best S1 member (S1+C1 on V2X) | CenterPoint stride 8 | CenterPoint stride 4 |
|---|---|---|---|
| V2X vehicle | 0.641 / 0.685 | 0.650 / 0.675 | **0.685** / 0.681 |
| V2X pedestrian | **0.290** / 0.252 | 0.252 / **0.279** | 0.256 / 0.277 |
| V2X truck | **0.822 / 0.673** | 0.750 / 0.520 | 0.611 / 0.502 |
| LUMPI Person | **0.340 / 0.134** | 0.095 / 0.038 | 0.168 / 0.047 |
| LUMPI Car | **0.874 / 0.770** | 0.848 / 0.756 | 0.844 / 0.749 |
| LUMPI Bicycle | 0.265 / 0.102 | **0.350 / 0.128** | 0.318 / **0.134** |
| LUMPI Motorcycle | 0.008 / 0.015 | 0.069 / 0.022 | 0.057 / 0.023 |
| LUMPI Truck | **0.200 / 0.131** | 0.137 / 0.077 | 0.118 / 0.109 |

**Gates.** Class gate (`route_predictions.py select --rule joint --calibrated`): **LUMPI Bicycle moves to CenterPoint stride 8** (B 0.102 -> 0.128, P(gain) 1.00, A 0.265 -> 0.350); every other class keeps its S1 member (Motorcycle B +0.007, V2X vehicle stride 4 B -0.004, V2X pedestrian: the incumbent keeps the best joint AP). Upload gate: LUMPI `routed-g2` A 0.260 -> 0.272, late-A 0.255 -> 0.271, B 0.1664 -> 0.1700 (bootstrap 90% interval +0.002 to +0.005), combined estimate (B) 0.5047 -> 0.5078, **+0.0031 < +0.005: not upload-ready** (package `lumpi_s2_submission.zip` checked: valid, 156 s, kept for an optional confirmation upload); V2X `routed-g2` equals S1+C1: **no version**. Decision record: [`decisions/2026-10-09-s2-center-routed.md`](decisions/2026-10-09-s2-center-routed.md).

**What S2 taught.**
1. **Height:** z voxels work as intended for V2X pedestrians: the BEV-3D gap on realval-B falls from 0.158 (S1 pedestrian member) to 0.112, at the same BEV AP (0.391 vs 0.384). No range-dependent z calibration passes for the CenterPoint members: their z bias is already small. CenterPoint also localizes better at high IoU (V2X stride 4: 3D mAP@0.7 on B 0.082 vs 0.058).
2. **Static false positives dominate the walker errors on both tracks and both architectures.** Of the unmatched pedestrian boxes scoring >= 0.5, 72-77% (V2X) and 50-69% (LUMPI) sit in the same 1 m cells in at least 20% of a scene's frames: poles, signs, trees and other structures the twin does not contain, so no detector ever saw them as negatives. CenterPoint's finer voxels resolve them and produce 1.8x (V2X) to 2.7x (LUMPI) more of them, which is why its LUMPI Person collapses. Oracle bound (removing those cells with the labels; an upper bound): V2X pedestrian 0.290 -> 0.356 (A) and 0.252 -> 0.346 (B), LUMPI Person 0.340 -> 0.400 (A). **Static hard negatives in the generator are now the largest known lever for walkers**, larger than any detector change (Section 8.7, R3); a static-background prior from legal unlabeled frames would also capture it but is rule-gated (`01` Section 10, question 2).
3. **CenterPoint is a complementary member, not a replacement:** better on realval-B for V2X pedestrians and on realval-A for V2X vehicles, better for LUMPI Bicycle; S3 fusion can use exactly this disagreement.
4. **The protocol held:** the class gate's realval-A guard and the realval-B gain threshold blocked switches that improved only one split (V2X vehicle stride 4: A +0.045, B -0.004).

### 8.3 S3 Fused Portfolio with TTA

**Hypothesis.** Averaging several views and several members reduces localization noise and run-to-run variance: test-time augmentation (TTA) and per-class box fusion add AP without new training [R38](07-LITERATURE.md#r38-horizonlidar3d), and height-shift TTA [R39](07-LITERATURE.md#r39-robosense-2025-report) reduces the V2X height loss. Targets: per-class B AP on every class; V2X BEV-3D gap; 3D@0.7.

**Prerequisites.** S2 decided (its members exist, or S1's if S2 failed); T1-T2.

**Inputs from S2 (2026-10-09).** Start from `routed-g2` on both tracks (members: the S1 pillars plus `centerpoint-g1v3` and `centerpoint-s4-g1v3`). Fusion candidates: V2X pedestrian (pillars `g1v3` best on A, CenterPoint best on B), V2X vehicle (`g1v2` best on B, CenterPoint stride 4 best on A), LUMPI Bicycle (CenterPoint stride 8 and 4). Extra metric: the static false-positive share of walker boxes (Section 8.2.1), since score averaging across members should demote boxes only one member produces. Server cost: the LUMPI S2 package already has 24,639 boxes (156 s), so keep the total under about 30,000.

**Steps.**
1. TTA in `pcdet_predict.py`: `--tta flip,yaw,z` runs each frame as identity, flip-x, flip-y, flip-xy (the models were trained with flips), yaw +/-5 deg (trained rotation +/-10 deg) and z shifts (V2X pedestrians +/-0.3 m, vehicles +/-0.2 m); boxes are mapped back to the original frame and tagged with their view. Unit test: the inverse transform returns synthetic boxes exactly.
2. `common/bdc26/detect/fusion.py`: rotated 3D weighted box fusion [R23](07-LITERATURE.md#r23-weighted-boxes-fusion) (clusters by rotated BEV IoU from `bdc26.evalap`, score-weighted centre and size, yaw of the top box, fused score = sum of scores / number of views) and the runner-up's score fusion `0.6 s_primary + 0.4 s_aux` [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports); KDE box fusion [R37](07-LITERATURE.md#r37-ms3d-kde-box-fusion) only if WBF fails the gate. The axis-aligned WBF prototype kept from earlier research is not reusable for rotated boxes. Unit tests on toy clusters.
3. TTA variants as members: for every kept member, raw predictions with `--tta` on A and B, fused within the member, then `tune_and_eval.sh` on the fused raw output (a `--raw-from` option so the script can start from given raw files); each becomes a routable member `<member>-tta`. The joint routing rule then chooses per class between plain and TTA variants.
4. Cross-member fusion: `route_predictions.py fuse` reads a `fusion:` block in `model.yaml` (per class: up to 2 members, their weights, fusion IoU in {0.3, 0.5, 0.7}), selected on A and B together with at most 2 knobs per class; a class keeps hard routing unless fusion passes its class gate.
5. `routed-g3` (`new_model.py ... --from routed-g2`), kit inference with the same TTA and fusion in `make_submission.sh`.
6. Server cost: total boxes at most about 30,000 and `check_submission.py --official` under 400 s; if not, raise the score floor of fused low-score boxes per class.
7. Scorecard vs S2, upload gate, upload, record.

**Evaluation.** Per-class B AP (all classes), V2X BEV-3D gap and pedestrian AP under z-shift TTA, 3D@0.7, check time and box count. Expected (est.): +0.01 to +0.03 mAP; most on classes with large run-to-run variance (LUMPI Bicycle and Truck, V2X truck).

**Gate.** Class gate per class and per knob; strategy success when at least 2 of 3 V2X classes and 4 of 7 LUMPI classes improve on B, and the upload gate holds.

**Deliverables.** TTA and fusion code with tests, `routed-g3`, scorecards, tracker row, upload.

**Risks and fallbacks.** Fusion knobs tuned on validation can over-fit (the LUMPI lesson): at most 2 knobs per class, chosen on A and B jointly; bad fusion creates duplicates (false positives): per-class NMS still runs after fusion; flips mirror a fixed roadside scene: if flip variants lose on B, keep only yaw and z views.

**Time box.** Wed Oct 14 - Fri Oct 16; about 4 GPU-hours of inference.

#### 8.3.1 Results (2026-10-09)

**Implementation.** Views in [`tta.py`](../common/bdc26/detect/tta.py) (identity, flip-x, flip-y, flip-xy, yaw +/-5 deg, z +/-0.25 m: 8 views inside the training augmentation, OpenPCDet's flip conventions; exact inverse and point-in-box invariance tested), run as one batch per frame by `pcdet_predict.py --tta` and fused per class by rotated 3D weighted box fusion in [`fusion.py`](../common/bdc26/detect/fusion.py) (leader clustering by BEV IoU, 0.3 for walker- and bike-sized classes and 0.5 otherwise; score-weighted centre and size, the leader's yaw; score = the mean over sources of each source's best score in the cluster, so a box only some sources see is demoted in proportion). `tune_and_eval.sh --tta` tunes each TTA variant's own post-processing (`test/postprocess_tta.yaml`) from the neutral start: TTA changes the score scale and the box spread, so the single-view settings do not carry over. In `route_predictions.py`, TTA variants are routable members (`<member>_tta`); `fuse` searches pairs of two different checkpoints among the top-4 members per class (IoU 0.3, 0.5, 0.7; equal weights: 2 knobs) through the class gate; `budget` sets per-class score floors for the server cost. Models `routed-g3` (from `routed-g2`), whose `make_submission.sh` runs the TTA members and the fusion on the kit frames.

**TTA per member** (official 3D AP@0.5 on realval-B, each variant with its own tuned post-processing; plain -> TTA): TTA raises 34 of the 40 member-class pairs on B.

| Track | Member | vehicle / Person | pedestrian / Car | truck / Bicycle | LUMPI Truck |
|---|---|---|---|---|---|
| V2X | `pointpillars-ut` | 0.585 -> 0.647 | 0 -> 0 | 0.673 -> **0.776** | |
| V2X | `pointpillars-g1v2` | 0.662 -> 0.711 | 0.174 -> 0.174 | 0.594 -> 0.684 | |
| V2X | `pointpillars-g1v3` | 0.607 -> 0.604 | 0.226 -> 0.257 | 0.565 -> 0.704 | |
| V2X | `centerpoint-g1v3` | 0.675 -> **0.766** | 0.279 -> 0.324 | 0.520 -> 0.528 | |
| V2X | `centerpoint-s4-g1v3` | 0.681 -> 0.704 | 0.277 -> **0.326** | 0.502 -> 0.582 | |
| LUMPI | `pointpillars-g1` | 0.091 -> **0.141** | 0.770 -> 0.779 | 0.102 -> 0.115 | 0.105 -> 0.119 |
| LUMPI | `pointpillars-g1v3` | 0.134 -> 0.128 | 0.768 -> 0.778 | 0.081 -> 0.100 | 0.131 -> **0.154** |
| LUMPI | `centerpoint-g1v3` | 0.038 -> 0.081 | 0.756 -> 0.780 | 0.128 -> 0.155 | 0.077 -> 0.113 |
| LUMPI | `centerpoint-s4-g1v3` | 0.047 -> 0.079 | 0.749 -> 0.770 | 0.134 -> **0.163** | 0.109 -> 0.107 |

**Portfolio per class** (realval-A / realval-B; each step passed the class gate against the previous one; route and fusion members after their gated z calibration):

| Track / class | S2 route | S3 route (TTA variants) | Fused pair (IoU) | With the budget (score floor) |
|---|---|---|---|---|
| V2X vehicle | `g1v2` + C1: 0.641 / 0.685 | `cp_tta` 0.723 / 0.766 | `cp_tta` + `g1v2_tta` (0.5): 0.758 / 0.821 | **0.757 / 0.819** (0.05) |
| V2X pedestrian | `g1v3` + C1: 0.290 / 0.252 | `g1v3_tta` + C1': 0.316 / 0.296 | `g1v3_tta` + `cp4_tta` (0.5): 0.350 / 0.362 | **0.350 / 0.361** (0.075) |
| V2X truck | `ut`: 0.822 / 0.673 | `ut_tta` + C1': 0.866 / 0.788 | `ut_tta` + `g1v2_tta` (0.5): 0.877 / 0.814 | **0.876 / 0.812** (0.2) |
| LUMPI Person | `g1v3`: 0.340 / 0.134 | kept (TTA: B -0.006) | `g1v3_tta` + `g1_tta` (0.5): 0.396 / 0.146 | **0.396 / 0.145** (0.02) |
| LUMPI Car | `g1`: 0.874 / 0.770 | kept (B +0.008) | `g1v3_tta` + `cp_tta` (0.7): 0.898 / 0.792 | **0.898 / 0.792** (0.02) |
| LUMPI Bicycle | `cp`: 0.350 / 0.128 | `cp4_tta` 0.406 / 0.163 | `cp4_tta` + `cp_tta` (0.5): 0.445 / 0.173 | **0.444 / 0.173** (0.03) |
| LUMPI Truck | `g1v3`: 0.200 / 0.131 | `g1v3_tta` 0.232 / 0.154 | failed (B -0.005) | **0.231 / 0.153** (0.03) |
| LUMPI Motorcycle, Bus, Van | `g1v3`, `g1v3`, `g1`: B 0.015, 0.012, 0.001 | kept | failed (Motorcycle: A 0.008 -> 0.143 but B +0.008, P 0.92) | B 0.013, 0.011, 0.001 (0.3, 0.3, 0.075) |

C1' is the gated range-dependent z calibration of the TTA variant (pedestrian z0 -0.225, 0.0075 per m; truck 0, 0.0075 per m).

**Gates.** Strategy success (8.3): 3 of 3 V2X classes and 4 of 7 LUMPI classes improve on B. Upload gate ([`decisions/README.md` 3.2](decisions/README.md#32-gates)):

| Track | A-mAP | B-mAP (bootstrap 90% interval of the gain vs S2) | late-A | BEV-3D gap (B) | 3D@0.7 (B) | R | Estimate (B) | Server check | Gate |
|---|---|---|---|---|---|---|---|---|---|
| V2X | 0.585 -> **0.661** | 0.537 -> **0.664** (+0.114 to +0.137) | | 0.129 -> **0.062** | 0.055 -> 0.078 | 0.919 | 0.828 -> **0.937** | 74 / 10,671 boxes | **passed** |
| LUMPI | 0.272 -> **0.301** | 0.170 -> **0.184** (+0.012 to +0.016) | 0.271 -> **0.298** | 0.025 -> 0.021 | 0.052 -> 0.062 | 0.905 | 0.508 -> **0.520** | 181 / 17,193 boxes | **passed** (bar 0.510) |

**Selection bias check.** Every choice above is ranked on A and B jointly and gated on B, so B is not fully out of sample. Selecting every route and fusion on realval-A alone gives the same members for all switched classes except LUMPI Bicycle (whose A-only pick still gains on B) and different fusion pairs for V2X vehicle and truck and LUMPI Person: B-mAP 0.653 (V2X) and 0.181 (LUMPI), combined estimates 0.927 and 0.517, both still above the upload bars. The LUMPI Person fusion is the fragile item (its A-only pair loses on B: 0.122 vs 0.134).

**What S3 taught.**
1. **TTA is the largest lever since the G1 walkers on V2X:** routing TTA variants alone lifts B-mAP 0.537 -> 0.617, most on the large classes (truck +0.114, vehicle +0.081): averaging eight views cancels yaw and extent noise of boxes that one roadside sensor sees from one side, and the flips are free because the members were trained with them.
2. **Cross-architecture fusion adds as much again, as S2 predicted** (V2X B 0.617 -> 0.666): pillars and CenterPoint disagree on which static structures look like walkers, and averaging scores demotes the boxes only one member makes. Static false positives ranked above the median true-positive score fall from 6.2 to 1.8 per frame (V2X pedestrian, realval-B) and from 9.7 to 4.1 (LUMPI Person); the share of static boxes among the remaining unmatched ones stays high (0.58 and 0.40), so R3 (static hard negatives in the generator) is still the lever for the rest.
3. **Height:** the V2X BEV-3D gap on B halves (0.129 -> 0.063) with z-shift views and the CenterPoint z voxels in the fused pairs: S4's main V2X target is already met (Section 8.4).
4. **Each variant needs its own post-processing.** A pilot run with the single-view settings, mistakenly reused as raw input, made the tuner post-process boxes twice and collapsed the V2X truck to 0.411 on A; raw files now always come from `pcdet_predict.py --raw` inside `tune_and_eval.sh`, and pilot outputs are never reused.
5. **Server cost:** fusion and TTA triple the boxes (V2X 955 and LUMPI 1,045 per realval-A frame; 48,110 boxes and 224 s in the kit scorer for the unbudgeted V2X package). Per-class score floors costing at most 0.002 AP per class and split cut them to 207 and 359 per frame for -0.0014 and -0.0007 B-mAP.
6. **LUMPI stays transfer-bound:** B/A 0.61; Person on B 0.146. Before the upload, the leaderboard ratios (LUMPI 0.82 x B, V2X 0.91 x B) projected LUMPI combined 0.486 and V2X 0.89; the leaderboard gave 0.5015 and 0.8381 (next paragraph). LUMPI realism (R3) remains the larger LUMPI lever: R 0.891 against the leader's 0.942.

**Leaderboard (2026-10-10).** V2X 974400: combined **0.8381** (mAP 0.5483, R 0.9203), rank 1 of 19, confirmation passed (+0.053). LUMPI: the scorer log reached DONE with combined **0.5015** (mAP 0.1692, R 0.8912), confirmation passed by the log (+0.029), but CodaBench kept the submission in Running after scoring, so the leaderboard still shows 965614. Realism is identical to the previous entries on both tracks (same 50 frames), so every change is detection.

| Track / class | Leaderboard before -> S3 | realval-B before -> S3 | Leaderboard / B (S3) | Leaderboard gain / B gain | Leaderboard gain / A gain |
|---|---|---|---|---|---|
| V2X vehicle | 0.605 -> 0.681 | 0.685 -> 0.819 | 0.83 | 0.56 | 0.65 |
| V2X pedestrian | 0.281 -> 0.346 | 0.252 -> 0.361 | 0.96 | 0.59 | 1.07 |
| V2X truck | 0.574 -> 0.619 | 0.673 -> 0.812 | 0.76 | 0.32 | 0.82 |
| **V2X mAP** | 0.4869 -> **0.5483** | 0.537 -> 0.664 | 0.83 | **0.48** | **0.80** |
| LUMPI Person | 0.117 -> 0.157 | 0.134 -> 0.145 | 1.08 | 3.6 | 0.71 |
| LUMPI Car | 0.633 -> 0.652 | 0.770 -> 0.792 | 0.82 | 0.88 | 0.81 |
| LUMPI Bicycle | 0.053 -> **0.224** | 0.102 -> 0.173 | 1.29 | 2.4 | 0.96 |
| LUMPI Truck | 0.028 -> 0.033 | 0.131 -> 0.153 | 0.22 | 0.23 | 0.16 |
| **LUMPI mAP** | 0.1357 -> **0.1692** | 0.166 -> 0.184 | 0.92 | **1.89** | **0.81** |

7. **Levels follow realval-B, gains follow realval-A.** Leaderboard mAP stays at 0.83-0.92 x B, but the S3 gains transferred at 0.80 and 0.81 x the realval-A gain on both tracks, against 0.48 and 1.89 x the B gain. A likely reason: B is the smaller split (V2X 298 frames, other scenes) and took part in every joint ranking, so its gains carry the selection noise; A is larger and closer to the test window (LUMPI). The leaderboard projection is now previous leaderboard mAP + 0.8 x the A gain ([`decisions/README.md` 3.1](decisions/README.md#31-scorecard)); the gates stay on B, which still predicts the levels and caught the switches that only helped A.
8. **The V2X truck gain transferred least** (0.32 x B, 0.82 x A): the TTA truck member and its fusion pair won mostly on realval-B; LUMPI Truck barely moved on the leaderboard (0.028 -> 0.033), as the S1 close-out predicted (the synthetic trucks stop at 8.47 m). Long trucks in the generator (R3) remain the truck lever on both tracks.
9. **LUMPI Bicycle quadrupled on the leaderboard** (0.053 -> 0.224): CenterPoint (S2) plus TTA and fusion (S3) are the first LUMPI change that moved a weak class by more than its local gain.

Decision record: [`decisions/2026-10-09-s3-fused-portfolio.md`](decisions/2026-10-09-s3-fused-portfolio.md).

### 8.4 S4 Two-Stage Refinement

**Hypothesis (revised 2026-10-10 after the review below).** A second stage that pools the voxel or keypoint features inside each proposal reduces the per-instance localization noise that is now the largest AP loss on walkers [R29](07-LITERATURE.md#r29-pv-rcnn), [R30](07-LITERATURE.md#r30-voxel-r-cnn), and its IoU-quality score ranks well-localized boxes above poorly localized ones. Both members also add a third architecture family to the S3 fusion. PV-RCNN++ is the most corruption-robust family [R25](07-LITERATURE.md#r25-robo3d). Targets: V2X pedestrian and LUMPI Person AP on B, and their localization loss (AP at 3D IoU 0.25 minus AP at 0.5).

**Prerequisites.** S3 decided (`routed-g3` is the starting portfolio); S2's CenterPoint configs (stage 1 of both members is the S2 CenterPoint).

**Review (2026-10-10): where the S3 portfolio loses AP@0.5.** `1 - AP3d@0.5` per class split into localization (AP at 3D IoU 0.25 minus AP at 0.5), ranking (oracle-ranked AP at 0.25 minus AP at 0.25) and misses (1 minus the oracle-ranked AP at 0.25); `routed-g3` on realval-A / realval-B:

| Class | AP3d@0.5 | Recall at 3D IoU 0.5 / 0.25 | Localization | Ranking | Misses |
|---|---|---|---|---|---|
| V2X pedestrian | 0.350 / 0.362 | 0.65 / 0.98 (A) | **0.33 / 0.27** | 0.30 / 0.34 | 0.03 / 0.03 |
| V2X vehicle | 0.757 / 0.819 | 0.88 / 0.98 (A) | 0.11 / 0.09 | 0.10 / 0.07 | 0.03 / 0.03 |
| V2X truck | 0.876 / 0.812 | 0.95 / 0.98 (A) | 0.03 / 0.03 | 0.07 / 0.04 | 0.03 / 0.13 |
| LUMPI Person | 0.396 / 0.146 | 0.70 / 0.91 (A) | **0.18 / 0.29** | 0.33 / 0.42 | 0.10 / 0.15 |
| LUMPI Car | 0.898 / 0.792 | 0.96 / 0.99 (A) | 0.03 / 0.06 | 0.05 / 0.05 | 0.03 / 0.10 |
| LUMPI Bicycle | 0.444 / 0.173 | 0.78 / 0.88 (A) | 0.04 / 0.04 | **0.39 / 0.67** | 0.13 / 0.13 |
| LUMPI Truck | 0.231 / 0.153 | 0.70 / 0.98 (A) | 0.29 / 0.15 | 0.45 / 0.42 | 0.03 / 0.28 |

Near misses (3D IoU 0.25-0.5 with a same-class GT, score >= 0.3) of walkers are **noise, not bias**: for V2X pedestrians and LUMPI Persons the mean errors are about 0 in every component, while the spread doubles against the hits (centre 0.13 vs 0.07 m along and across the ray, length 0.33-0.45 vs 0.14-0.16 m). Replacing one component with the label lifts this share of the near misses over 0.5: centre 0.48-0.50, size 0.51-0.54, centre and z 0.56-0.61, height 0.09-0.10, yaw 0.08-0.15. Vehicles and LUMPI Cars instead show a range-dependent bias along the ray (+0.25 to +0.32 m beyond 20 m for LUMPI Car).

**What changes against the plan of 2026-10-06.**
1. **3D@0.7 is dropped as a target:** the score uses 3D mAP@0.5 only; 3D@0.7 stays a diagnostic.
2. **LUMPI Truck is not an S4 target:** its localization loss is the length gap of the generator (D5, synthetic trucks at most 8.47 m), which a refiner trained on those trucks cannot close; long trucks belong to R3.
3. **The V2X height target is met** by S3 (BEV-3D gap on B 0.062); step 0 (ground-height map) is dropped.
4. **Walker localization noise is the target**, the largest remaining block of AP on V2X (pedestrians are 62% of its test boxes): even a third of the V2X pedestrian localization loss is about +0.03 mAP.
5. **A cheap calibration was tested first and failed:** a range-dependent radial (along the ray) and z calibration of the S3 outputs per class (C2, selected on A) gains A +0.020 (V2X vehicle), +0.006 (LUMPI Car), but B only +0.007, +0.007 and +0.009 (V2X truck): below the class gate, not used. The walker errors have no bias for a calibration to remove.
6. **Two families instead of one**, since the measured cost is a third of the plan (smoke runs below): Voxel R-CNN (voxel RoI pooling) and PV-RCNN++ (keypoint RoI pooling) run at the same time.

**Steps.**
1. `voxelrcnn-g1v3` on both tracks from mainline `voxel_rcnn_with_centerhead_dyn_voxel.yaml`: stage 1 is the S2 CenterPoint (voxels 0.1 x 0.1 x 0.25 m, `VoxelResBackBone8x`, the S2 head groups, `MeanVFE` instead of the dynamic voxel encoder that needs `torch_scatter`); proposals up to 300 per head at score >= 0.03 (dense scenes, and the S3 lesson that low-score boxes still carry AP); `REG_FG_THRESH` 0.45 instead of 0.55 (the boxes to correct are near misses at IoU 0.25-0.5, so regression must train on such proposals); class-agnostic RoI head, IoU-quality score; near-raw final output (score 0.01, NMS 0.9), as for every member. Smoke run: 0.40 s (V2X) and 0.49 s (LUMPI) per iteration at batch 4, 2.5 h and 3.0 h for 40 epochs on 4 GPUs (10 and 12 GPU-hours).
2. `pvrcnnpp-g1v3` on both tracks from mainline `pv_rcnn_plusplus.yaml`: same stage 1 and targets; 2,048 sectorized proposal-centric keypoints (mainline 4,096 for about 150k Waymo points); keypoint features from `bev`, `x_conv1`, `x_conv3`, `x_conv4` (VectorPool), with `x_conv1` (full-resolution voxels) in place of `raw_points`, because xyz-only points give the raw-point branch no input channels; `x_conv4` input 128 channels (residual backbone). Smoke run: 0.56-0.67 s per iteration at batch 2 while sharing the GPUs, 5 GB; trained at batch 4 next to the Voxel R-CNN runs.
3. Score blend (`common/bdc26/detect/pcdet_patches.py`): OpenPCDet's two-stage heads replace the stage-1 heat-map score with the stage-2 IoU score; with `ROI_HEAD.SCORE_BLEND_ALPHA` = a the final score is stage1^a x stage2^(1-a), and padded proposals score 0. a in {0, 0.5, 1} is chosen per member on realval-A (raw predictions with the neutral post-processing), checked on B, and fixed in the config before tuning.
4. `tune_and_eval.sh` (plain) and `tune_and_eval.sh --tta flip4+yaw+z` for both members on both tracks.
5. `routed-g4` from `routed-g3`: members `vr`, `vr_tta`, `pv`, `pv_tta` added; `select --rule joint --calibrated`, then `fuse` with sets of up to 3 members of different checkpoints (pairs and triples among the top 4 per class; still 2 knobs: the set and the IoU), then `budget`.
6. Scorecard vs S3 (with the AP-loss decomposition repeated: the walker localization loss should fall), upload gate, package, kit-scorer check, upload, record; leaderboard projection: previous leaderboard mAP + 0.8 x the A gain.

**Evaluation.** Localization loss of V2X pedestrian and LUMPI Person on B; per-class B AP of the two-stage members against the S2 CenterPoint (the same stage 1, so the difference is the refinement) and against the S3 portfolio; combined estimate (B); box count and check time.

**Gate.** Class gate per member, route and fusion set; strategy success when V2X pedestrian or LUMPI Person passes the class gate through a two-stage member or a fusion containing one, and the upload gate holds (bars after S3: LUMPI 0.520, V2X 0.937).

**Deliverables.** `voxelrcnn-g1v3`, `pvrcnnpp-g1v3` (plain and TTA), `routed-g4`, scorecards, tracker rows, upload.

**Risks and fallbacks.** The refinement learns synthetic box conventions (the near misses are noise in real length, which depends on the gait of real walkers; the synthetic walkers may lack that variation): judge on B, never on synthetic val, and let post-processing re-fit size and z per variant; the IoU score is trained without the static structures of the real scenes, so ranking may not improve on static false positives (R3 remains their lever); if neither member wins a class or a fusion, S4 contributes only diversity, and R3 follows.

**Time box.** Training Sat Oct 10 (both families concurrently, about 3 h and 6-8 h), score blend, tuning and TTA Sun Oct 11, routing, fusion and upload Mon Oct 12.

#### 8.4.1 Results (2026-10-10)

**Implementation.** Members `voxelrcnn-g1v3` and `pvrcnnpp-g1v3` on both tracks (steps 1-2), trained 40 epochs on 4 GPUs each, all four runs at once on the 8 GPUs (wall time 5.4 h V2X, 6.7 h LUMPI; shared GPUs). Score blend (step 3): **per class**, not per member: the class-agnostic IoU head is trained mostly on the frequent classes, so for V2X trucks the stage-1 score is far better (Voxel R-CNN truck A 0.218 at a = 0, 0.570 at a = 1) while walkers and vehicles prefer the blend (pedestrian 0.273 / 0.291 / 0.237 at a = 0 / 0.5 / 1); `ROI_HEAD.SCORE_BLEND_ALPHA` is a list in `CLASS_NAMES` order (V2X [0.5, 0.5, 1]; LUMPI per class). `fuse` gained sets of three and keeps an earlier fusion as the incumbent (regression check: re-running it on a copy of `routed-g3` keeps every S3 fusion). New diagnostics in the scorecard: the AP-loss decomposition per class (`bdc26.diagnostics.ap_loss_decomposition`). Models `routed-g4` on both tracks.

**Members on real validation** (official 3D AP@0.5, tuned; realval-A / realval-B; the S2 CenterPoint is the same stage 1, so the difference is the second stage):

| Track / class | CenterPoint (TTA) | Voxel R-CNN plain / TTA | PV-RCNN++ plain / TTA |
|---|---|---|---|
| V2X vehicle | 0.650 / 0.675 (0.723 / 0.766) | 0.739 / 0.751, 0.796 / 0.820 | 0.748 / 0.791, 0.794 / **0.831** |
| V2X pedestrian | 0.252 / 0.279 (0.282 / 0.324) | 0.300 / 0.331, 0.323 / 0.359 | 0.285 / 0.332, 0.318 / **0.374** |
| V2X truck | 0.750 / 0.520 (0.723 / 0.528) | 0.752 / 0.584, 0.822 / 0.715 | 0.776 / 0.697, 0.810 / 0.727 |
| V2X mAP | 0.551 / 0.492 (0.576 / 0.539) | 0.597 / 0.555, 0.647 / 0.632 | 0.603 / 0.606, 0.641 / **0.644** |
| LUMPI Person | 0.095 / 0.038 (0.211 / 0.081) | 0.189 / 0.041, 0.289 / 0.069 | 0.174 / 0.037, 0.309 / 0.073 |
| LUMPI Car | 0.848 / 0.756 (0.886 / 0.780) | 0.879 / 0.775, 0.895 / 0.775 | 0.878 / 0.779, 0.887 / 0.787 |
| LUMPI Bicycle | 0.350 / 0.128 (0.406 / 0.155) | 0.431 / 0.163, 0.487 / **0.195** | 0.409 / 0.144, 0.493 / 0.182 |
| LUMPI Truck | 0.137 / 0.077 (0.162 / 0.113) | 0.136 / 0.089, 0.217 / 0.118 | 0.219 / 0.079, 0.314 / 0.108 |

**Was the hypothesis right?** Partly (AP-loss decomposition on realval-B, same stage 1 without and with refinement):
- **Vehicles: yes.** The V2X vehicle localization loss falls from 0.140 (CenterPoint) to 0.103 (Voxel R-CNN) and 0.058 (PV-RCNN++); with TTA 0.102 -> 0.069 / 0.056. 3D@0.7 of the portfolio on B rises 0.078 -> 0.146.
- **Walkers: no.** The V2X pedestrian localization loss stays at 0.27-0.30 (CenterPoint 0.272, Voxel R-CNN 0.300, PV-RCNN++ 0.275) and recall at IoU 0.5 does not move (0.67-0.71); the pedestrian gain (+0.05 AP) comes from **ranking** (loss 0.424 -> 0.343 / 0.367): the IoU-quality score orders the found pedestrians better. LUMPI Person is mixed the same way. The walker near-miss noise survives a second stage trained on synthetic walkers: it is likely in the real labels and points themselves (gait-dependent length, a few points per walker), which synthetic training does not teach.

**Portfolio per class** (realval-A / realval-B, each step through the class gate against S3):

| Track / class | S3 (`routed-g3`) | S4 (`routed-g4`, with score floors) | Change | dB (bootstrap P) |
|---|---|---|---|---|
| V2X vehicle | 0.757 / 0.819 | **0.806 / 0.843** | fused `pv_tta` + `vr_tta` (IoU 0.7) | +0.024 (1.00) |
| V2X pedestrian | 0.350 / 0.361 | 0.350 / 0.361 | the S3 fusion stays the best candidate | 0 |
| V2X truck | 0.876 / 0.812 | **0.896 / 0.834** | fused `g1v3_tta` + `g1v2_tta` + `vr_tta` (IoU 0.7), the first triple | +0.022 (0.99) |
| LUMPI Bicycle | 0.444 / 0.173 | **0.525 / 0.202** | fused `vr_tta` + `pv_tta` (IoU 0.7) | +0.029 (1.00) |
| LUMPI Car | 0.898 / 0.792 | 0.898 / 0.792 | `pv_tta` + `g1v3_tta` reaches B +0.0097: just below the gate | 0 |
| LUMPI Truck | 0.231 / 0.153 | 0.231 / 0.153 | `pv_tta` gains A +0.08 but loses B 0.05: gated out | 0 |
| LUMPI Person, Motorcycle, Bus, Van | unchanged | unchanged | no candidate passes | 0 |

Selected on realval-A alone, the same sets win for V2X vehicle and LUMPI Bicycle, and the V2X truck triple swaps `g1v3_tta` for `ut_tta` (B 0.827, still above S3).

**Gates.** Strategy success (8.4): **not met for walkers** (no V2X pedestrian or LUMPI Person change passes); the S4 members win through vehicles, trucks and bicycles instead. Upload gate ([`decisions/README.md` 3.2](decisions/README.md#32-gates)):

| Track | A-mAP | B-mAP (90% interval of the gain vs S3) | late-A | BEV-3D gap (B) | 3D@0.7 (B) | R | Estimate (B) | Bar | Server check | Gate |
|---|---|---|---|---|---|---|---|---|---|---|
| V2X | 0.661 -> **0.684** | 0.664 -> **0.679** (+0.011 to +0.022) | | 0.062 -> 0.051 | 0.078 -> 0.146 | 0.919 | 0.937 -> **0.950** | 0.942 | 80 s, 13,028 boxes | **passed** |
| LUMPI | 0.301 -> 0.313 | 0.184 -> 0.188 (+0.003 to +0.005) | 0.298 -> 0.304 | 0.021 | 0.062 -> 0.064 | 0.905 | 0.520 -> 0.523 | 0.525 | 182 s, 17,004 boxes | **failed** (+0.003) |

Leaderboard projection before the uploads (previous leaderboard mAP + 0.8 x the A gain, Section 8.3.1): V2X combined about 0.854, LUMPI about 0.510; measured 0.8485 and 0.5040 (next paragraph). The LUMPI package was below the upload gate; the entrant uploaded it anyway.

**What S4 taught.**
1. **A second stage is a better scorer than a better localizer on walkers.** Refinement fixes the box geometry where there are enough points (vehicles: localization loss halved), but walker boxes keep their noise; the walker gain comes from IoU-quality ranking. Walker localization needs a different lever: label-convention statistics in the generator (gait, walker size distributions from legal real labels) rather than a detector.
2. **Score blends are per class.** A class-agnostic IoU head under-serves rare large classes (trucks); one blend for all classes would have cost V2X pedestrians 0.05 AP.
3. **Three families make better fusions:** the best V2X vehicle and truck boxes now come from fusions with two-stage members; the first triple wins (truck).
4. **Cumulative portfolios need incumbent-aware selection:** without the fix, a new member could have replaced the S3 pedestrian fusion through a weaker fusion that only beat the single routed member.
5. **LUMPI stays bounded by transfer and Person:** Bicycle keeps improving (A 0.265 in S1 -> 0.525), but Person and Truck do not move with any detector; R3 (static hard negatives, long trucks) remains the LUMPI lever, next to realism.

**Leaderboard (2026-10-10/11).** V2X 975938: combined **0.8485** (mAP 0.5605, R 0.9203), rank 1 of 19, confirmation passed (+0.010). LUMPI 975871 (uploaded below the upload gate by the entrant's call): combined **0.5040** (mAP 0.1721, R 0.8912), **rank 1 of 18** (Raj Patil 0.4784 second), confirmation passed (+0.0025 over the S3 log). Realism identical on both tracks; on the leaderboard only the gated classes changed (V2X pedestrian identical, LUMPI every class but Bicycle identical), as the merge predicts.

| Track / class | Leaderboard S3 -> S4 | realval-A gain | realval-B gain | Leaderboard gain / A gain | / B gain |
|---|---|---|---|---|---|
| V2X vehicle | 0.681 -> 0.707 | +0.049 | +0.024 | 0.54 | 1.11 |
| V2X truck | 0.619 -> 0.628 | +0.020 | +0.022 | 0.50 | 0.45 |
| **V2X mAP** | 0.5483 -> **0.5605** | +0.023 | +0.015 | **0.53** | **0.80** |
| LUMPI Bicycle | 0.224 -> 0.244 | +0.081 | +0.029 | 0.25 | 0.71 |
| **LUMPI mAP** | 0.1692 -> **0.1721** | +0.012 | +0.004 | **0.25** | **0.72** |

Five uploads with a local change (V2X S1+C1, S3, S4; LUMPI S3, S4) now calibrate the projection: the leaderboard mAP gain was 0.25-1.74 x the A gain (median 0.80), 0.48-1.90 x the B gain (median 0.80) and 0.38-1.52 x the mean of both (median 0.63). No split predicts the size of a gain; all five predicted its sign. The projection of 8.3.1 (0.8 x the A gain, fitted on the two S3 uploads) over-predicted S4 (V2X 0.854 vs 0.8485, LUMPI 0.510 vs 0.504) and is replaced by previous leaderboard mAP + 0.6 x the mean of the A and B gains ([`decisions/README.md` 3.1](decisions/README.md#31-scorecard)); the gates stay on B, and the B-based upload gate judged the LUMPI S4 gain correctly (+0.003 estimated, +0.0025 measured).

Decision record: [`decisions/2026-10-10-s4-two-stage.md`](decisions/2026-10-10-s4-two-stage.md).

### 8.5 S5 Geometry-Invariant Inputs

**Hypothesis (revised 2026-10-11 after the review below).** Two source-only changes make the detector read geometry from the points instead of memorizing the twin: (a) GBlobs [R27](07-LITERATURE.md#r27-gblobs) replaces absolute point coordinates with local shape (the covariance of the points around each voxel) and the position inside the voxel, so the network cannot shortcut through absolute position and the twin's point patterns; (b) class-wise random object scaling (ROS, [R40](07-LITERATURE.md#r40-st3d)) stretches each object's points and box independently along length, width and height, so box size must be read from the points, with ranges that cover the real label sizes the twin lacks. Signature of success: B-mAP and the B/A ratio rise together, and the classes with a size gap (LUMPI Bicycle, trucks) move.

**Prerequisites.** S4 decided (`routed-g4` is the starting portfolio); `voxelrcnn-g1v3` is the parent (the S4 voxel two-stage member: best cost per AP, same voxel grid as GBlobs needs).

**Review (2026-10-11): what S1-S4 leave, and what the data says about S5.**
1. **Remaining loss** (S4 portfolio, AP-loss decomposition on B): V2X pedestrian localization 0.274 and ranking 0.339; LUMPI Person localization 0.286, ranking 0.418, misses 0.150; LUMPI Bicycle ranking 0.668; LUMPI Truck ranking 0.421 and misses 0.275. Refinement (S4) did not fix walker localization; static structures still cause most walker false positives (R3).
2. **GBlobs as published degenerates on our data.** The authors' encoder ([malicd/GBlobs](https://github.com/malicd/GBlobs), BSD-3: `GBlobsVFE`, relative distance on, 12 values per voxel: the mean's offset from the voxel centre and the 3 x 3 sample covariance of the voxel's points) computes the covariance inside each voxel. On our frames at the S2-S4 grid (0.1 x 0.1 x 0.25 m), **80-83% of the voxels hold one point and 13-15% two** (synthetic `g1-v3` and real realval-A alike, both tracks), so the covariance is undefined for about 95% of the voxels: the paper's own failure case (nuScenes, 94% of voxels with 1-2 points, small gains). With cells of 0.4 x 0.4 x 0.5 m, 65-74% of the points sit in cells with at least 3 points. **Adaptation:** keep the 0.1 m voxel grid for the backbone and the fine position offset per voxel, but compute the covariance over the aligned 4 x 4 x 2-voxel cell that contains the voxel (`GBlobsCellVFE`); the published voxel-level form stays available as an ablation.
3. **Size statistics (legal real labels vs the synthetic corpus, an allowed use as in the S1 walker calibration).** Walker sizes already match (V2X pedestrian and LUMPI Person length, width and height quantiles within 0.03 m at the median). Gaps: LUMPI Bicycle synthetic 1.66 x 0.58 x 1.62 m with almost no spread (length sd 0.09 m) against real 2.00 x 0.85 x 1.90 m (length 1.79-2.50 m); trucks at most 8.47 m against real V2X 5.7-13.1 m and LUMPI 5.6-17.1 m (5-95%); V2X vehicle height 1.38-1.85 m against 1.42-2.28 m. ROS ranges per class are set to cover these real ranges.
4. **Dropout augmentations dropped from the plan:** the synthetic frames are ray-cast with occlusion and density-calibrated to the real sensors (S1), so there is no measured density gap for frustum or range dropout to close.

**Steps.**
1. `common/bdc26/detect/gblobs_vfe.py`: `GBlobsVFE` (the published voxel form, BSD-3 notice) and `GBlobsCellVFE` (cell covariance, coordinates centred on the cell before the sums so float32 keeps precision), registered into OpenPCDet's VFE registry by `register()`. Unit tests: covariance and offsets of toy voxels and cells against numpy, output width 12.
2. `common/bdc26/detect/augment.py`: `bdc_object_scaling`, class-wise anisotropic scaling of each object's points and box in its own frame, about the box bottom (objects stay on the ground; OpenPCDet's `random_local_scaling` is isotropic and scales about the centre), skipped when the scaled box would overlap another object; after `gt_sampling`. Unit tests: points stay inside the scaled box, the bottom stays in place, overlaps are skipped.
3. Runs on both tracks from `voxelrcnn-g1v3`, 40 epochs, the same seed: **a** `voxelrcnn-gblobs-g1v3` (GBlobsCellVFE); **b** `voxelrcnn-ros-g1v3` (ROS); **c** a + b, if a and b both help on their own. a and b run at the same time (8 GPUs), c afterwards.
4. Score blend per class, `tune_and_eval.sh` plain and TTA, scorecard with the AP-loss decomposition against the parent; compare A, B, late-A, the B/A ratio and the classes with a size gap.
5. Kept runs join `routed-g5` (from `routed-g4`) as plain and TTA members; `select --rule joint --calibrated`, `fuse --max-members 3` (incumbent-aware), `budget`.
6. Scorecard vs S4, upload gate (bars LUMPI 0.523, V2X 0.950), package, kit check, record; leaderboard projection: previous leaderboard mAP + 0.6 x the mean of the A and B gains.

**Evaluation.** Per run: B-mAP, B/A ratio, late-A, per-class B AP (LUMPI Bicycle and Truck, V2X truck for ROS; all classes for GBlobs), localization and ranking loss of each class against the parent.

**Gate.** Class gate per member, route and fusion; strategy success when a run raises B-mAP and the B/A ratio over its parent, or ROS moves a size-gap class through the class gate, and the upload gate holds.

**Deliverables.** GBlobs encoders and ROS with tests, runs a-c on both tracks, `routed-g5`, scorecards, tracker rows, upload.

**Risks and fallbacks.** GBlobs gains were measured real-to-real; here the twin is the same intersection as the test, so absolute position (ground height, where objects stand) is partly legitimate signal, and in-domain AP may drop (run a against its parent shows it); cell covariance smooths over object boundaries; stretched trucks are sparser along their length than real long trucks (ray-cast long trucks remain R3); ROS ranges set from real label statistics are a hyperparameter fitted on the real train split, recorded as such.

**Time box.** Port and smoke Sun Oct 11; runs a and b Sun Oct 11 (about 6 h), c Mon Oct 12; tuning, routing and upload Mon Oct 12 - Tue Oct 13; about 80 GPU-hours.

#### 8.5.1 Results (2026-10-11)

**Implementation.** [`gblobs_vfe.py`](../common/bdc26/detect/gblobs_vfe.py) (`GBlobsVFE` ported from the authors' code with its BSD-3 notice; `GBlobsCellVFE` with the cell covariance) and [`augment.py`](../common/bdc26/detect/augment.py) (`bdc_object_scaling`), both registered by `register()`; unit tests against numpy and for the scaling invariants. ROS checked on the training stream before the runs: LUMPI Bicycle median size 1.66 x 0.58 x 1.62 -> 1.86 x 0.84 x 1.80 m (real 2.00 x 0.85 x 1.90), LUMPI Truck length 95th percentile 8.47 -> 14.1 m (real 17.1), V2X truck 8.47 -> 10.1 m (real 13.1). Runs a and b from `voxelrcnn-g1v3`, four at once (wall time 5.2 h V2X, 7.0 h LUMPI on shared GPUs).

**Runs a and b against the parent** (official 3D AP@0.5, tuned with the per-class score blend; TTA variants; realval-A / realval-B):

| Track / class | `voxelrcnn-g1v3` | a: GBlobs (cell) | b: ROS |
|---|---|---|---|
| V2X vehicle | 0.796 / 0.820 | **0.809 / 0.830** | 0.787 / 0.811 |
| V2X pedestrian | 0.323 / 0.359 | 0.310 / 0.357 | **0.349 / 0.393** |
| V2X truck | 0.822 / 0.715 | 0.788 / 0.674 | **0.856 / 0.797** |
| V2X mAP (B/A) | 0.647 / 0.632 (0.98) | 0.635 / 0.621 (0.98); plain 0.595 / 0.586 (0.99, parent 0.93) | **0.664 / 0.667** (1.00) |
| LUMPI Person | 0.289 / 0.069 | 0.177 / 0.058 | 0.287 / **0.084** |
| LUMPI Bicycle | 0.487 / 0.195 | 0.459 / 0.178 | **0.540 / 0.220** |
| LUMPI Truck | 0.217 / 0.118 | 0.218 / 0.086 | **0.362 / 0.142** |
| LUMPI Bus | 0.010 / 0.010 | 0.010 / 0.010 | **0.018 / 0.077** |
| LUMPI mAP | 0.295 / 0.170 | 0.276 / 0.162 | **0.322 / 0.189** |

- **ROS works on both tracks**, and where the decomposition predicts: V2X truck localization loss on B 0.050 -> 0.009 (real truck extents learned from stretched ones), LUMPI Bus recall at IoU 0.5 0.20 -> 0.42 (Bus shares the head with Truck), and V2X pedestrian ranking loss 0.316 -> 0.289 with only mild walker scaling: randomized sizes make walkers easier to tell from look-alikes. A single `voxelrcnn-ros-g1v3` with TTA (B 0.667) equals the whole S3 portfolio.
- **GBlobs does not**, as a member on its own: LUMPI Person ranking loss 0.529 -> 0.604, V2X truck localization loss 0.050 -> 0.109. The twin is the same intersection as the test, so absolute position (ground height, where objects stand) is legitimate signal, and removing it costs more than the local shape gives. Its plain V2X variant shows the predicted signature (B +0.031, B/A 0.93 -> 0.99) but its TTA variant loses. Run c (a + b) was therefore not run (its precondition, both runs helping on their own, failed).

**Extension: ROS on the portfolio's other families** (not in the plan; motivated by run b): `pvrcnnpp-ros-g1v3` and `pointpillars-ros-g1v3` on both tracks (TTA variants, A / B against their parents):

| Member | V2X | LUMPI |
|---|---|---|
| PV-RCNN++ + ROS | 0.642 / 0.650 (parent 0.641 / 0.644); truck B 0.727 -> 0.786 | 0.312 / **0.186** (0.312 / 0.167); Truck 0.314 / 0.108 -> 0.397 / 0.162 |
| PointPillars g1v3 + ROS | 0.531 / 0.482 (0.568 / 0.522); **truck 0.839 / 0.704 -> 0.672 / 0.546** | 0.287 / **0.187** (0.271 / 0.170); Truck 0.232 / 0.154 -> 0.366 / 0.190 |

The anchor-based PointPillars head has one truck anchor (7.94 x 2.89 x 3.46 m on V2X), and stretched trucks no longer match it; the anchor-free and two-stage heads have no such limit.

**Portfolio** (`routed-g5`, 24 V2X and 20 LUMPI members; each change through the class gate against S4; realval-A / realval-B with the score floors):

| Track / class | S4 (`routed-g4`) | S5 (`routed-g5`) | Source | dB vs S4 (P) |
|---|---|---|---|---|
| V2X vehicle | 0.806 / 0.843 | **0.828 / 0.852** | `vrgb_tta` + `pv_tta` + `pvros_tta` (IoU 0.7) | +0.009 (0.99; +0.011 in `fuse`, before the floors) |
| V2X pedestrian | 0.350 / 0.361 | **0.350 / 0.397** | `vrros_tta` + `pv_tta` (IoU 0.5) | +0.036 (1.00) |
| V2X truck | 0.896 / 0.834 | **0.905 / 0.848** | `ut_tta` + `vrros_tta` + `pvros_tta` (IoU 0.5) | +0.014 (0.98) |
| LUMPI Car | 0.898 / 0.792 | **0.909 / 0.806** | `pvros_tta` + `vrgb_tta` + `ppros_tta` (IoU 0.7) | +0.014 (0.91) |
| LUMPI Bicycle | 0.525 / 0.202 | **0.565 / 0.225** | `vrros_tta` + `pvros_tta` + `pv_tta` (IoU 0.7) | +0.023 (1.00) |
| LUMPI Bus | 0.011 / 0.011 | **0.016 / 0.075** | `vrros_tta` | +0.064 (1.00) |
| LUMPI Truck | 0.231 / 0.153 | **0.433 / 0.200** | `pvros_tta` + `ppros_tta` (IoU 0.3) | +0.047 (1.00) |
| LUMPI Person, Motorcycle, Van | unchanged | unchanged | best Person candidate B +0.006 | 0 |

GBlobs enters through fusions (V2X vehicle, LUMPI Car): as a member it adds the diversity of a different input, which the fusion rewards even though the member alone is weaker. Selected on realval-A alone, every switched class keeps the same set or one that still gains on B.

**Gates.** Strategy success (8.5): met (run b raises B-mAP and the B/A ratio; ROS moves the size-gap classes through the class gate). Upload gate:

| Track | A-mAP | B-mAP (90% interval of the gain vs S4) | late-A | BEV-3D gap (B) | 3D@0.7 (B) | R | Estimate (B) | Bar | Server check | Gate |
|---|---|---|---|---|---|---|---|---|---|---|
| V2X | 0.684 -> **0.694** | 0.679 -> **0.699** (+0.012 to +0.024) | | 0.051 -> 0.048 | 0.146 -> 0.178 | 0.919 | 0.950 -> **0.967** | 0.955 | 58 s, 8,896 boxes | **passed** |
| LUMPI | 0.313 -> **0.350** | 0.188 -> **0.209** (+0.017 to +0.024) | 0.304 -> 0.335 | 0.021 -> 0.018 | 0.064 -> 0.085 | 0.905 | 0.523 -> **0.541** | 0.528 | 146 s, 13,831 boxes | **passed** |

Leaderboard projection (previous leaderboard mAP + 0.6 x the mean of the A and B gains; spread 0.4-1.5 x): V2X combined about 0.856 (0.852-0.868), LUMPI about 0.519 (0.514-0.541).

**What S5 taught.**
1. **Size realism beats input invariance here.** The twin's few asset sizes were a larger gap than its point patterns: scaling objects to the real size range (from legal label statistics) helps every anchor-free and two-stage member, while removing absolute coordinates (GBlobs) hurts in a fixed-intersection domain where position is real signal.
2. **Published input encoders need their density assumptions checked:** GBlobs assumes voxels with several points; at our density 95% of voxels hold one or two, which the cell covariance repairs only partly.
3. **Anchors cap augmentation:** the anchor-based pillars lose trucks under ROS because the single truck anchor no longer matches; class-wise anchors or anchor-free heads are needed to profit from size augmentation.
4. **Weak members can be good fusion members:** the GBlobs runs lose alone but win inside the V2X vehicle and LUMPI Car fusions.
5. **LUMPI Person is still unmoved** (B 0.145 since S3): no detector or augmentation has changed it; R3's static hard negatives (ranking loss 0.418) and realism stay the LUMPI levers.

**Leaderboard (2026-10-11).** V2X 978945: combined **0.8730** (mAP 0.5890, R 0.9203), rank 1 of 19, confirmation passed (+0.024): pedestrian 0.346 -> 0.391, truck 0.628 -> 0.657, vehicle 0.707 -> 0.718, 3D@0.7 0.112 -> 0.196; above the projected range (0.852-0.868). LUMPI 978931: 0.5039 (mAP 0.1720) against the S4 entry's 0.5040: **confirmation failed by 0.00007**, so the leaderboard keeps S4 (975871, rank 1 of 18); Truck 0.033 -> 0.072, but Bicycle 0.244 -> 0.215 and Car 0.652 -> 0.642 (Person, Van, Motorcycle identical).

**LUMPI diagnosis** (stop-and-diagnose rule; no test labels used):

| Check | Bicycle | Car | Truck |
|---|---|---|---|
| Local change S5 - S4, pooled A+B (paired bootstrap P) | +0.031 (1.00) | +0.001 (0.64) | +0.124 (1.00) |
| 90% range at test size (frames resampled to the test window's GT count: 80 / 1,260 / 190) | -0.018 to +0.054 | -0.006 to +0.016 | +0.066 to +0.149 |
| Leaderboard change (probability at test size) | -0.030 (0.02) | -0.010 (0.00) | +0.038 (0.01) |
| Our own predictions on the 50 test frames, confident boxes per frame S4 -> S5 (realval-A) | 3.16 -> 3.72, same size (3.06 -> 3.18) | 13.1 -> 11.3 (15.1 -> 14.1) | 4.46 -> 1.38, 7.8 -> 9.7 m long (2.95 -> 0.97) |

1. **Not sampling noise:** the three leaderboard changes lie outside the 90% range of what the test window's small samples would produce; the test window answers differently from every local split.
2. **Bicycle:** the size-augmented members fire 18% more often on the test frames (realval +4%), against 1.6 real bicycles per test frame; motorcycle confusion (23x more motorcycles in the test window) is present in both portfolios (0.56 vs 0.63 confident Bicycle boxes per realval-B motorcycle) and explains only about 0.04 of the 0.56 extra boxes per frame. The rest are false positives on test-window content the realval frames lack, as for the static walker false positives (S2) and the realism reference (R1-R2).
3. **Car:** the change was weak locally (pooled +0.001, P 0.64), and the B gate passed it at P 0.91 only.
4. **Truck** transferred (+0.038, the largest LUMPI leaderboard gain after S3's Bicycle), at a third of the local gain.
5. **Rule from R3 on:** the class gate also requires a gain on the pooled A+B frames with P(gain) >= 0.9 ([`decisions/README.md` 3.2](decisions/README.md#32-gates)). Checked on all 17 class changes of S3-S5, it agrees in sign with the leaderboard 16 times, rejects only S5 LUMPI Car and blocks no change that transferred (V2X S5 pedestrian P 0.97, leaderboard +0.046). The LUMPI entry stays S4: picking LUMPI classes from these leaderboard numbers would tune on the test set.

Decision record: [`decisions/2026-10-11-s5-object-scaling.md`](decisions/2026-10-11-s5-object-scaling.md).

### 8.6 S6 Variance-Controlled Final Portfolio (re-planned 2026-10-15)

**Why the re-plan.** S6 was planned on 2026-10-06 as *Sparse Transformer Experts* (DSVT, LION or SAFDNet members for capacity and long range). The retrospective after R5 (Section 8.10) ranks capacity last among the drivers: S1's pillars beat the ECCV runner-up's DSVT ensembles, S2 and S4 added little that transferred, and no sim-to-real evidence for sparse transformers has appeared since (the ECCV runner-up's LUMPI write-up with DSVT scored 0.4692). The levers that did transfer are content, variance reduction and the right validation judge per class. S6 is therefore re-scoped as the final strategy around the two untried levers of that kind; the transformer members stay an optional research track (end of this section).

**Review (2026-10-15): what the data says for S6** (legal validation data only; probe scripts in the session scratchpad, numbers here).
1. **Tail hedges are saturated.** Copies below every original box (proven not to lower AP) of every other kind add 0.000-0.003 AP on A, late-A and B: Bus at the automatic-label size, Truck boxes as Bus, Bicycle boxes as Motorcycle, Car boxes as Van, Truck length variants, Bicycle and vehicle jitter, V2X walker and rider size modes, vehicle boxes as truck. Only walker jitter is worth anything (LUMPI Person +0.005-0.008, limited by the server cost; V2X pedestrian already in R5). The remaining errors are ranking errors and misses, which only better members fix.
2. **realval-B cannot judge LUMPI Van.** In Measurements 5-6 the LUMPI class 6 is a different object population: median 1.88 x 0.95 x 1.74 m (M5) and 1.01 x 0.84 x 1.83 m (M6), person- or two-wheeler-sized; in Measurement4 (realval-A and the test window) it is van-sized, 4.77 x 1.99 x 2.00 m (late frames 4.64 x 2.03 x 2.04). Every member scores about 0.001 on B, so the B gate has frozen Van at the S1 member since S1, while realval-A predicted the Van leaderboard level (A 0.122, leaderboard 0.118). Later members and fusions score higher on A and on late-A: `vrros` + `vrros4_tta` + `g1_tta` (IoU 0.5) A 0.122 -> 0.174, late-A 0.120 -> 0.173 (both P 1.00); `vrros` + `g1_tta` A 0.169, late-A 0.193; triples with `pvros4_tta` gain on A but not on late-A.
3. **Member noise is large.** One configuration with another seed moves V2X truck by 0.17 and LUMPI Person by 0.02-0.03 on B (R5); single-seed members make every selection partly a draw, and the R5 V2X vehicle fusion of new members transferred at only 0.2 x B. Averaging seeds of one configuration (a seed bag) reduces exactly this noise and is untried.
4. **LUMPI Truck: annotation gaps, not missing structure.** The confident unmatched trucks of the R5 portfolio are static only in late-A (0.22 per frame, static share 0.70; 0.00 on A as a whole and on B): one 17.1 x 3.2 x 4.3 m object at about (19, 25), detected in 80 consecutive frames 5960-6395 (the last 45 s before the test window), with no label of any class; static unmatched cars are unlabeled stationary vehicles in the same period. A hard negative of that shape would teach the detector to miss real long trucks (real LUMPI trucks reach 16 m and more), and suppressing it by persistence across test frames or by a background map from real frames is outside the rules reading (`decisions/2026-10-14-rules-compliance-review.md`). The planned long-structure negatives are dropped; the finding explains part of the Truck transfer (0.3-0.5 x B) for the report.
5. **Final phase.** The competition has one leaderboard (`Results`) with the rule `Force_Best`, and the final phase hides scores and allows one submission per day (5 in total per the pages). If `Force_Best` applies to the final phase, as the shared leaderboard suggests, the best final submission counts: the confirmed R5 zips on the first day fix the current scores, and later gated candidates can only add (to be confirmed in the organizer email).

**Hypothesis.** (a) Seed bags of the strongest two-stage configurations lift the classes with the largest seed spread (LUMPI Person; V2X truck and pedestrian) and transfer better than fusions of single new members, because they remove member noise instead of selecting it. (b) Judging LUMPI Van on the frames whose labels are vans unlocks a class frozen since S1: about +0.05 Van AP on A and late-A, worth about +0.006 combined if the A-to-leaderboard relation of S1 holds.

**Pre-registered rules** (written before any S6 run):
1. **Seed bag:** a member made by fusing k seeds of one configuration (the R3/R5 weighted box fusion, equal weights, IoU 0.5 for walkers and two-wheelers, 0.7 otherwise), in a plain and a TTA variant; it is routed, fused and gated like any member (class gate, pooled condition, final gate). Seeds: 1666 exists; 2666 and 3666 are new.
2. **LUMPI Van judge:** candidates are ranked on early realval-A (Measurement4 frames 0-4799) and the change must gain at least 0.01 on late-A (4800-6399) with paired-bootstrap P(gain) >= 0.9; realval-B and the pooled condition are not used for Van (its B labels are not vans); the final gate applies the same judge to Van.
3. **Upload estimate for LUMPI:** the unclipped estimate uses Van's realval-A AP in place of its realval-B AP, for every version compared (otherwise no Van change can show); the bar stays +0.005 over the R5 estimate computed the same way.
4. **Frozen as in R5:** LUMPI Bicycle, Motorcycle and Bus; realism frames change only through the +0.003 held-out rule; walker tail copies stay (V2X), LUMPI Person copies only if the kit scorer stays under 400 s.
5. No class or knob is chosen from leaderboard numbers (rules review).

**Refinements fixed on 2026-10-15 before the first S6 run** (review of optimizations and research; part of the pre-registration):
6. **Bag composition:** LUMPI `bag-voxelrcnn-ros-g1v4` = seeds 1666, 2666, 3666 (the size-capped configuration; the R3 seed-666 run predates the cap and is a different configuration, so it stays out); LUMPI `bag-pvrcnnpp-ros-g1v4` = seeds 666, 1666, 2666, 3666; V2X `bag-voxelrcnn-ros-g1v5` and `bag-pvrcnnpp-ros-g1v5` = seeds 666, 1666, 2666. Each bag fuses the seeds' own tuned, post-processed predictions (no new knob besides the IoU) in a plain and a TTA variant; fusion IoU 0.7 for Car, Van and vehicle, 0.5 for every other class; the existing fusion averages scores over all seeds, so a box only one seed finds keeps a third or a quarter of its score (a soft vote).
   *Amendment (2026-10-15, before any S6 portfolio step):* the functional test of the bag tool on the two existing V2X `voxelrcnn-ros-g1v4` seeds gave a bag at least as good as the better seed on every class (TTA, B: vehicle 0.844 against 0.832 / 0.846, pedestrian 0.382 against 0.376 / 0.376, truck 0.803 against 0.803 / 0.636); the two-seed V2X bags `bag-voxelrcnn-ros-g1v4` and `bag-pvrcnnpp-ros-g1v4` (seeds 666 and 1666, no training) are therefore added as candidates, gated like the others.
   *Clarification (2026-10-15, before any S6 portfolio step):* the S3 rule that a fusion set uses different checkpoints counts a bag as all of its seeds, so a bag is never fused with one of its own seeds (that would count the seed twice; `route_predictions.member_weights`).
7. **Van candidates:** for the Van judge the fusion search draws on the six members with the best early-A Van AP (four for the other classes), because the best Van fusion of the review needs a fifth-ranked member.
8. **Monitoring is not selection:** every new member gets realval learning curves in TensorBoard (official AP on a fixed subset of realval-A and B every five epochs, `common/tools/tb_realval.py`) next to OpenPCDet's training losses; the epoch-40 checkpoint is always the one used, as in S1-R5.
9. **Realism extension (optional, CPU):** the LUMPI frames may also be chosen from the whole `g1-v4` corpus (train and validation splits, 10,000 frames, the generator of the LUMPI members) with the S1 selector and the EMD refinement; the +0.003 held-out rule decides, as in R5.
10. **Left out after the review:** weight averaging of the last checkpoints (stochastic weight averaging needs a cyclic extra schedule and a batch-norm refit, and the reported LiDAR gain is about 0.2 points [R44](07-LITERATURE.md#r44-afdetv2-swa)); more tail hedges (saturated, review item 1); long-structure negatives (review item 4); per-member fusion weights (more knobs on the same splits).

**Steps.**
1. **Seeds** (GPU, about 16 h on 8 GPUs): LUMPI `voxelrcnn-ros-g1v4` (capped) and `pvrcnnpp-ros-g1v4` with seeds 2666 and 3666 (bags of three with the R5 seed 1666 and, for PV-RCNN++, the R3 seed 666); V2X `voxelrcnn-ros-g1v5` and `pvrcnnpp-ros-g1v5` with seeds 1666 and 2666 (bags of three with 666), on the corpus of the submitted V2X frames. Score blend, plain and TTA tuning as in R5; TTA tunes are queued after training to avoid running out of GPU memory.
2. **Bag members** (code): `route_predictions.py` member type `bag` (members listed, fused per class before routing, validation and kit predictions cached), unit tests (a bag of identical members equals the member; boxes of one seed alone pass through).
3. **Van judge** (code): `--judge Van=early-A:late-A` in `fuse` and `gate`, and the LUMPI estimate of rule 3 in `scorecard.py`.
4. **Portfolio `routed-g8`** from `routed-g7`: bags and the new seeds as members; select, fuse (late-A Person rule, Van judge), budget, freeze, tail, final gate against `routed-g7`; package, kit check, scorecard.
5. Upload gate, upload, record.
6. **Final phase** (Section 8.8): the best confirmed zips on the first day, then only gated candidates.

**Evaluation.** Per bag against its best single seed and against the R5 configuration of each target class (B, pooled, late-A for LUMPI Person); Van on early-A and late-A; the scorecard against `routed-g7`.

**Expected** (planning numbers): LUMPI Van +0.03-0.05 and Person +0.005-0.015 on the leaderboard: combined about +0.004 to +0.008 (0.524-0.528); V2X truck and pedestrian +0.005-0.01: combined about +0.002 to +0.004 (0.887-0.889).

**Risks and fallbacks.** The Van judge uses the selection split (its post-processing is tuned on all of realval-A), so the late-A check is only partly independent and the leaderboard is the real test; if Van does not transfer, the next upload reverts it. Bags may not beat the best single seed on B (then the gate keeps R5). GPU time competes with nothing else now. If the seeds run late, the Van change alone is an upload candidate (CPU only, about half a day).

**Time box.** Oct 15-16 seeds and code; Oct 17 portfolio and upload; buffer to Oct 25; report from Oct 26.

**Implementation (2026-10-15).** Every step runs detached under `common/pipeline/` ([README](../common/pipeline/README.md); root README Section 6.10) in `$BDC_DATA/logs/s6`: two training workers (one per 4-GPU half) pop the eight seed runs from a queue; two post-processing workers run the score blend, plain and TTA tuning and the realval curves of each finished seed on whichever GPU has 24 GB free (3 retries, the R5 out-of-memory failures); one orchestrator per track (`s6_portfolio.sh`) waits for its seeds, fuses the bags, builds `routed-g8` and runs select, fuse (Van judge, late-A Person rule), budget, freeze or tail copies, the final gate against `routed-g7`, packaging, the official kit check, the scorecard and the reproduction script, then stops: uploads stay manual. Progress: `bash common/pipeline/status.sh $BDC_DATA/logs/s6` and `events.txt`; training losses and realval curves in TensorBoard (localhost, SSH port forwarding). Tools added: `bag_predictions.py`, `score_blend.py`, `tb_realval.py`, `freeze_classes.py`, `reproduce_submission.py` (every scored version since S1 re-merges identically; S1 LUMPI re-run from its checkpoints gave identical boxes and frames), `route_predictions.py --judge`, `scorecard.py --judge`; tests `common/tests/test_s6.py`. Checks before the first portfolio step: every bag's seeds share one training configuration (only the per-member score blend differs, an inference knob); the bag kit cache is redone when a seed's checkpoint or post-processing is newer, and reproduction scripts always predict again. Upload bars fixed before any result: LUMPI judged estimate 0.5846 (R5 0.5796 + 0.005), V2X 0.988; realism item 9 bar 0.9367 (the R5 frames score 0.9337 as packaged: the scorer's subsample depends on frame order by about 0.0005, so candidates are scored in the packaged order).

**Research track (optional, not in the final portfolio unless it passes every gate):** one new-family member for the report, VoxelNeXt first (no new dependency) or DSVT-pillar (`torch_scatter` 2.1.2 wheel for torch 2.1 + cu121 exists; it would be pinned in `.venv_ut`). Original S6 plan of 2026-10-06: install `torch_scatter`, `dsvt-g1v3` from `dsvt_pillar.yaml` with xyz input and our ranges, smoke run, full run only if under 12 h, then a portfolio member through the gates.


#### 8.6.1 S6 results (2026-10-15 to 2026-10-16)

**Run.** 16 h of training on the 8 GPUs (12:22 to 04:32, eight seed runs, no failure), post-processing next to training on whichever GPU had 24 GB free (no out-of-memory retry needed), then the two portfolios unattended (V2X 05:48-07:57, LUMPI 05:39-10:07); every step in `$BDC_DATA/logs/s6/events.txt`. Record: [`decisions/2026-10-16-s6-variance-controlled.md`](decisions/2026-10-16-s6-variance-controlled.md).

**Seed bags** (TTA, realval-A / realval-B; best single seed in brackets):

| Track | Bag | Seeds | Bag | Best seed | Per class (B) |
|---|---|---|---|---|---|
| V2X | `bag-pvrcnnpp-ros-g1v5` | 666, 1666, 2666 | **0.702 / 0.694** | 0.689 / 0.680 | vehicle 0.846, pedestrian 0.394, truck 0.842: above every seed |
| V2X | `bag-voxelrcnn-ros-g1v5` | 666, 1666, 2666 | **0.708 / 0.697** | 0.690 / 0.691 | vehicle 0.861, pedestrian 0.407 above every seed; truck 0.822 (seeds 0.697-0.832) |
| LUMPI | `bag-pvrcnnpp-ros-g1v4` | 666-3666 | **0.356 / 0.200** | 0.343 / 0.196 | Car, Bicycle, Truck and late-A Person (0.334 against 0.316-0.328) above every seed; Person B 0.123 (best seed 0.124) |
| LUMPI | `bag-voxelrcnn-ros-g1v4` | 1666-3666 | **0.348 / 0.192** | 0.336 / 0.189 | Bicycle 0.241, A Van 0.125 above every seed; Person B 0.128 (seeds 0.093-0.137) |

Hypothesis (a) held for the members: every bag is at or above its best seed on both split means, and the seed spread it removes is large (V2X Voxel R-CNN truck 0.697-0.832 on B, LUMPI Voxel R-CNN Person 0.093-0.137). It did not carry into the portfolios: no bag fusion beat R5's three-architecture fusions by +0.01 on B, most likely because those fusions already average much of the same member noise.

**Portfolios** (`routed-g8`, every change through the class gate with the pooled condition, then the final gate against `routed-g7`):

| Track / class | R5 | S6 | Source | Gate |
|---|---|---|---|---|
| LUMPI Van | 0.120 / 0.001 (late-A 0.118) | **0.173 / 0.002 (late-A 0.173)** | `vrros` + `vrros4_tta` + `g1_tta` (IoU 0.5, floor 0.05), the first candidate by early-A | judge: late-A +0.055 (P 1.00) on the final predictions |
| LUMPI Person | 0.465 / 0.160 | R5 kept | late-A candidates (bag fusions, late-A 0.370-0.372) lost 0.009-0.015 on B | failed |
| LUMPI Car | 0.898 / 0.792 | R5 kept | `pvros_tta` + `vrros_tta` + `pvros4s2_tta`: +0.007 (P 1.00) | under the bar |
| LUMPI Motorcycle | 0.008 / 0.015 | R5 (frozen, rule 4) | `cp_tta` + `bagvr4` + `vr` passed (+0.023, A +0.171) | frozen |
| LUMPI Truck, Bicycle, Bus | R5 | R5 | Truck -0.004; Bicycle and Bus frozen | |
| V2X vehicle | 0.857 / 0.864 | R5 kept | `bagvr5_tta` + `pvros4s2_tta`: +0.005 (P 0.94), A +0.008, pooled +0.007 | under the bar |
| V2X pedestrian | 0.381 / 0.418 | R5 kept | `bagvr5_tta` + `bagpv5_tta`: -0.006 | failed |
| V2X truck | 0.905 / 0.848 | R5 kept | `pp5_tta` + `bagvr5_tta` + `bagpv5`: -0.001, **A +0.030, pooled +0.022** | failed on B |

**Gate.** LUMPI judged estimate 0.5796 -> **0.5860** (bar 0.5846), late-A 0.351 -> 0.358, kit scorer 160 s: **upload gate passed**; the package differs from the R5 entry only in Van. V2X: predictions and frames identical to the R5 entry (estimate 0.983, bar 0.988): no upload.

**V2X variant b (2026-10-16, for the leaderboard comparison).** `routed-g8b` takes, per class, the fuse step's best joint-ranked candidate wherever the pooled condition holds (P >= 0.9) without the +0.01 B requirement: vehicle and truck change, pedestrian stays at R5. A 0.714 -> 0.727, B 0.7101 -> 0.7118 (P 0.82), B 3D mAP@0.7 0.170 -> 0.221 (truck 0.114 -> 0.264), estimate 0.9847 (bar 0.988), kit 137 s. Its upload tests whether the B requirement is too strict for complete systems; the answer changes the final-phase rule only if fixed before the next run.

**Realism (item 9).** The whole `g1-v4` corpus as the pool did not help: as packaged 0.9344 (FPD) and 0.9313 (FPD + EMD) against 0.9337 for the R5 frames; R5 frames kept. Noise study (exact R, 10 subsample seeds): 0.9335 / 0.9340 / 0.9344, sd 0.0012-0.0025. The FPD + EMD set scored 0.9372 in the selector's frame order and 0.9313 in the packaged order: the scorer's 10,000-point subsample depends on the frame order, so held-out scores are now computed in the packaged order (the server's draw), and the +0.003 gate is about 1.5-2 sd of one draw. The R5 realism-gate numbers (selector order) carry the same noise.

**Monitoring.** Realval learning curves for all eight seeds and 28 earlier members are in TensorBoard. They are not monotonic on B (V2X PV-RCNN++ seed 1666: 0.584, 0.494, 0.617, 0.634, 0.580, 0.622 at epochs 15-40), which supports keeping epoch 40 rather than picking an epoch on real data.

**Lessons.** (1) Bags are the right member when a class has no cross-architecture fusion; against fusions they are a near miss, not a gain. (2) A class whose labels differ between the splits needs its own judging split, fixed before the run (Van). (3) Realism changes below about 0.004 cannot be told apart from the scorer's draw. (4) The V2X near misses (truck A +0.030, pooled +0.022) are documented for the report, not adopted: changing the gate after seeing the result would be choosing on the same splits.


#### 8.6.2 S6 close-out (2026-10-17): leaderboard transfer, the pooled rule and the plan to the final phase

**Leaderboard (2026-10-17 UTC; record [`decisions/2026-10-16-s6-variance-controlled.md`](decisions/2026-10-16-s6-variance-controlled.md)).** LUMPI 995869 (`routed-g8`) **0.5228** (mAP 0.1748, R 0.9323), rank 1 of 21; V2X 995877 (`routed-g8b`, variant b) **0.8931** (mAP 0.6065, R 0.9332), rank 1 of 23. Both confirmed; realism identical to R5 on both (same frames).

| Change | realval-A | realval-B | Pooled on the final predictions | Leaderboard | Leaderboard / local |
|---|---|---|---|---|---|
| LUMPI Van (judge: early-A rank, late-A gate) | +0.053 (late-A +0.055) | +0.001 | judge: late-A +0.055, P 1.00 | **+0.024** | 0.45 x A |
| V2X vehicle (Voxel R-CNN bag + PV-RCNN++ seed 1666) | +0.008 | +0.005 | +0.007, P 1.00 | **+0.014** | 1.7 x A, 2.7 x B |
| V2X truck (pillars + both bags) | +0.030 | -0.000 | +0.024, P 1.00 | **+0.014** | 0.45 x A |
| Combined | | | | LUMPI +0.0029, V2X +0.0079 | projections: LUMPI +0.003 to +0.006 (low end), V2X +0.000 to +0.004 (above) |

**Findings.**
1. **The +0.01-on-B requirement was too strict for complete systems.** It rejected the two V2X changes that gained +0.014 each; the pooled A+B condition on the final predictions had both V2X signs right (and had caught the false LUMPI Car gains of S5 and R5; it does not cover the rare LUMPI classes, which stay frozen after Bicycle passed it in R3 and fell on the leaderboard). From 6.0 on the pooled rule replaces it, with an upload bar on the projection rule ([`decisions/README.md` Section 3.2](decisions/README.md#32-gates), pre-registered 2026-10-17).
2. **Bags transfer through fusions with other architectures**, not as routed members alone: both V2X gains are bag fusions.
3. **A judged class transfers at about half its judging-split gain** (Van 0.45 x A; the leaderboard / A level ratio fell from 0.97 to 0.81).
4. **The B-based estimate under-predicts V2X fusions** (+0.0014 against +0.0079); the projection rule (0.6 x the mean of the A and B gains) was closer (+0.0037) but still low.
5. **Box tightness at IoU 0.7 on the V2X test window is not represented locally**: 3D mAP@0.7 fell 0.187 -> 0.165 while it rose on B (0.170 -> 0.221). Not scored, but worth a note in the report.

**Close-out.**
- **LUMPI variant b (the pooled rule on LUMPI):** only Car qualified in `fuse` (pooled +0.0055, P 1.00); on the final predictions it gains on A (+0.0074) and on B (+0.0074) separately but loses on the pooled frames (-0.0022, P 0.24): the third LUMPI Car fuse-level gain that does not survive (S5, R5, S6). **Not adopted**; LUMPI stays at S6. (`common/pipeline/s6b_lumpi.sh`, `model-lumpi-track/routed-g8b`.)
- **Reproduction from the weights** (`$BDC_DATA/logs/s6close`, one job per GPU): both entries' test-frame scripts give IDENTICAL predictions (maximum difference 0.0) and identical frames, from the corpus and, as in a fresh clone, from the scored zip; the validation scripts recompute realval-A/B and late-A with split mAP identical to four decimals and every class within 4e-4 AP (EQUIVALENT: 41 of 48 member files bit-identical; 7 TTA files of two-stage members, recorded on GPUs shared with training, differ in the last digits).
- **Release 6.0** carries the 21 checkpoints and both zips as assets (`releases/6.0/weights.json`; `common/tools/release_weights.py fetch --tag 6.0`).

**Plan to the final phase (reassessed 2026-10-17).** Time left: development phase to Fri Oct 30, 17:00 PDT (13 days, 5 uploads a day; 93 LUMPI and 91 V2X uploads unused); final phase Nov 1-14 (5 uploads, hidden scores, the best counts); report due Nov 15. Every new class change follows the pooled rule; every upload the 6.0 upload bar; one change set per upload.

| # | Task | When | Cost | Expected | Decision rule |
|---|---|---|---|---|---|
| 1 | Record S6, close-out, release 6.0 with the weights | Oct 17 | done | traceable, reproducible entries | |
| 2 | **V2X bag extension (optional):** seeds 3666 and 4666 of `voxelrcnn-ros-g1v5` and `pvrcnnpp-ros-g1v5`, bags of five, the vehicle and truck fusions re-searched | Oct 18-19 | 4 runs, about 12 GPU-hours; pipeline as S6 | +0.002 to +0.005 on vehicle or truck (three seeds gave +0.006 to +0.013 over the best seed on B) | pooled rule; upload bar |
| 3 | **Bags for the unmoved classes (optional):** seeds of the members in the incumbent V2X pedestrian fusion (`voxelrcnn-ros-g1v3`, `voxelrcnn-ros-g1v4`) and the LUMPI Person fusion (`pointpillars-g1v4`, `voxelrcnn-ros-g1v4-s2` family) | Oct 18-21 | about 6 runs, 18 GPU-hours | uncertain: the S6 bag fusions did not beat these incumbents | pooled rule (LUMPI Person also the late-A rule); upload bar |
| 4 | Final-phase dry run: rebuild the F1 zips from the release weights in a fresh clone (`reproduce_<tag>.sh`), byte and kit check | Oct 24 | 1 GPU-hour | proves F1 | IDENTICAL |
| 5 | Gate E: feature freeze; at most two confirmation uploads per track; report draft from 8.10 and the records | Oct 25-30 | | | |
| 6 | F1 = the 6.0 zips (995869, 995877); F2-F5 only confirmed versions | Nov 1-14 | 5 uploads | | `Force_Best` |
| 7 | Report (4-8 pages) | to Nov 15 | | | |

Tasks 2 and 3 run with the S6 pipeline (`common/pipeline/`: training queue, post workers, `s6_portfolio.sh` adapted to the pooled rule) after the entrant's go; nothing in them touches the 6.0 entries.

### 8.7 Parallel and gated work

**R track: LUMPI realism** (CPU, Sat Oct 10 - Mon Oct 19; joins the current strategy when it passes). **Status 2026-10-14: done through R3** (leaderboard R 0.891 -> 0.932, rank 1 regained by 0.026; Section 8.7.2). **Priority raised 2026-10-09:** LUMPI is rank 2 behind an entry with realism R 0.942 (CD 0.877, EMD 1.108, FPD 0.498) and a lower mAP (0.1185); at our mAP, about +0.015 leaderboard R regains rank 1. Hypothesis: the LUMPI frames lack the static structure of the test window (35% of the reference mass lies where the twin has no geometry [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports)); +0.022 R is worth +0.009 combined, enough to pass the ECCV LUMPI winner.
1. **R1 diagnosis:** per-term realism on proxies 1-5; a BEV mass-difference map (pooled selected frames vs fit proxies 1-3), range and height histograms; where the EMD comes from. Written into [`data-lumpi-track/README.md`](../data-lumpi-track/README.md).
2. **R2 selection objective:** `select_realism_frames.py --objective r`: the current FPD greedy search, then a refinement pass that scores candidate swaps with the full official R against the fit proxies (a few hundred evaluations). Gate: held-out R (proxies 4-5) up by at least 0.003.
3. **R3 engine G2-lite static clutter and long trucks (M9; promoted after S2 as the largest walker lever, Section 8.2.1):** trucks and trailers of 12-20 m (29% of real realval-A trucks; the synthetic trucks stop at 8.47 m, close-out D5), which also serve Truck detection after retraining; parked-vehicle rows at positions where legal Measurement4 Car labels stay stationary (label statistics, an allowed use), plus poles and vegetation primitives; ray-cast with the five G1 sensors and inserted ray-consistently; corpus `g1-v4`. Gate: held-out R >= 0.915 with FPD below 4, and no drop in detection when evaluated as realism frames only.
   **Planned in detail 2026-10-11 (after S5): Section 8.7.1** (review, engine G2-lite, steps, gates, trade-offs); results in 8.7.2.
   **Refined 2026-10-11 by S4-S5:** walker sizes already match the real labels, so the walker part of R3 is static hard negatives only (S4: walker localization is not a detector problem; the static share of unmatched walker boxes is still 0.41-0.59); long trucks stay in R3 even if S5's object scaling helps, because stretched trucks are sparser than ray-cast ones; R3 is the next strategy after S5 and its corpus `g1-v4` retrains the kept members, two-stage included.
4. **R4 adoption (decided 2026-10-12, R3):** the kept members were retrained on `g1-v4` and the frames come from `g1-v4` too, so frames and training share one generator. The original options were: if `g1-v4` passes, either retrain the kept LUMPI members on `g1-v4` (about one day of GPUs 0-3, scheduled into the S5 slot) so frames and training share one generator (the S1 rule, `decisions/2026-09-30-s1-g1-generator.md`), or submit `g1-v4` frames with the current detectors and record the deviation in a decision record.
- **V2X realism:** background density calibration as on LUMPI (E8 in the V2X model README); low priority (R 0.920 against the ECCV winner's 0.925).

**R1-R2 results (2026-10-09).** New legal proxies `pcdet/realism-proxy-late-{1,2,3}`: 50 realval-A frames each from Measurement4 4800-6399 (closest to the excluded test window), disjoint from proxies 1-5 and from the density-prior frames. The S1 LUMPI frames score R 0.908 / 0.901 / 0.906 against them (0.906 against proxy 4), so the late frames do **not** reproduce the leaderboard's 0.891 (EMD 1.65, FPD 5.1): the hidden reference differs in content from every legal frame, not by time alone. R2 (re-selecting the 50 frames on proxies 1-3 plus late-1/2) scores R 0.901-0.902 on the held-out proxies 4, 5 and late-3, below the S1 frames: **failed, S1 frames kept**. Frame selection is near its limit on legal proxies; the gap needs generator content (R3), which S2 showed is also the main walker lever (static hard negatives, Section 8.2.1).

**Gated: self-training on unlabeled legal real frames** [R40](07-LITERATURE.md#r40-st3d) (only after a written organizer yes to question 1): pseudo-label legal unlabeled train-split frames with the frozen portfolio, keep per-class high-confidence boxes, mix 1:1 with synthetic frames, retrain the best member, evaluate on B (never on frames that were pseudo-labeled), and disclose it in the report.

#### 8.7.1 R3 Engine G2-lite: review and plan (2026-10-11)

**Position.** R3 runs as an extended step after S5 and before S6, with the full S5 machinery (members with plain and TTA variants, per-class score blend, joint routing, fusion of up to three members, score floors). It changes the training data (corpus `g1-v4`) and keeps every detector; the 50 realism frames change only through the realism gate below.

**Hypothesis (revised by the review).** After S5 the largest remaining gap is the twin's object geometry, not the detectors: UT Cars and two-wheelers are far sparser than real ones in the same place, trucks and buses have the twin's few asset sizes, and the scene has none of the static structures behind most walker false positives. Re-rendering the objects with the real rig at real size and density, and adding unlabeled static clutter as hard negatives, should (a) give the size-gap classes ray-cast real-size examples instead of ROS-stretched ones, (b) let Car and two-wheeler members learn from real-like density, and (c) lower the static share of walker false positives (LUMPI Person ranking loss 0.418, V2X pedestrian 0.289 on B). Signature: a member trained on `g1-v4` beats its `g1-v3` parent on B and on the pooled A+B frames for these classes, with the same detector.

**Review (2026-10-11): what the data says.**
1. **Point density must be compared in the same place.** A range-binned comparison (median points per box by distance to the frame origin) first suggested that every UT actor class on LUMPI has 0.33-0.6x the real density. It misleads: the five LUMPI lidars stand around the intersection, so the frame-origin range is not the sensing range, and synthetic and real objects stand in different places. Position-matched (points per box inside the same 8 m BEV cell for LUMPI, 4 m for V2X, so the sensor coverage is the same; count-weighted geometric mean of the per-cell synthetic/real ratios over realval-A+B), `g1-v3` against real: LUMPI **Car 0.44**, Van 0.99, Truck 0.83, Bus 2.2, **Bicycle 0.25**, **Motorcycle 0.52**, Person 0.86; V2X vehicle 0.96, **truck 0.42**, pedestrian 0.98. The scale fix (UT renders actors at 0.78x and the points are stretched by 1/0.78) explains the Cars; UT two-wheelers have 8-11 points without a rider.
2. **Sizes** (legal realval label statistics, as in S5): LUMPI Truck real length median 8.35 m, 90th percentile 16.3 m, synthetic at most 8.47 m; LUMPI Bus real 12.0 x 3.3 x 3.3 m, synthetic one asset of 10.27 x 3.94 x 4.25 m; LUMPI Bicycle and Motorcycle real 2.0 x 0.85 x 1.9 m and 2.0 x 0.85 x 1.8 m (riders included); V2X truck real 8.2 x 2.89 m, synthetic 5.2 x 2.07 m.
3. **Walker false positives** stay 41-59% static (S2-S5); the twin has no poles, signs, trees, bins or boxes. LUMPI S5 added Bicycle false positives on test-window content (S5 record).

**Engine G2-lite** ([`render/g2.py`](../common/bdc26/render/g2.py), the `post_inserter` of `convert_ut_frame` after the scale fix; Open3D (Embree) ray casting with the real rig; Open3D is part of `.venv_ut`):
1. **Re-cast actors** (LUMPI Car, Van, Truck, Bus; V2X truck) from the convex hull of their own points, mirrored about the long axis (single-view actors otherwise become wedges). Sparse actors (under 400 points, 79% of the LUMPI actors) get a hull exemplar of a well-sampled UT actor of the class joined, from a bank built once from training frames (`gen/hull_bank_g2.npz`): hulls of 40-100 points covered 0.44 of their box against 0.65 for well-sampled UT cars.
2. **Real sizes** (Truck, Bus, Bicycle, Motorcycle on LUMPI; truck on V2X) from the legal size prior (`gen/size_prior_g2.npz`): one sample per actor, placed centred, front-kept or rear-kept, shortened in 0.5 m steps (never below the UT length) when the traffic leaves no room. A first version lengthened half of the trucks only (8% grew), a second resampled until one fit (buses came out 8.9 m long against the real 12.0 m).
3. **Two-wheelers with riders**: wheels, frame or motorcycle body, a seated rider (lean, arms to the bar, helmet on motorcycles) filling the real box.
4. **Static clutter**: Poisson(30) unlabeled poles (with a sign plate or a street-light arm), trees, bollards, utility boxes, bins and barriers per frame, 60% of them 1-4 m from real walker positions (legal label statistics), on the ground and clear of labeled boxes: hard negatives in the walker height band.
5. **Ray-consistent insertion** per sensor: new returns behind existing geometry are dropped (range image), and a frame point that a new object hides is removed only if it is hidden from every sensor whose beam table fits it. A merged frame does not record its sensor: 45% of the UT-LUMPI points fit two sensors within 0.08 deg (mostly the Pandar64, whose beams are 0.17 deg apart), and the best-fit rule removed 49% of one frame from wrong origins. Physical shadows are still larger than UT's: two LUMPI lidars stand only 1.5-2.4 m above the ground, so a full-size car near the Pandar64 hides the ground to the horizon where UT's 0.78x cars left it visible (42,800 points removed per LUMPI frame on average, 3,400 per V2X frame).
6. **Sampling rate**: objects keep the G1 sampling rate (the in-range point count before the pass, `resample_calibrated(n_ref=...)`). Otherwise the added clutter returns and the larger shadows move it (V2X vehicles 0.96 -> 0.79 with clutter, LUMPI up to 1.18x), and the dropout calibration would depend on the amount of clutter.
7. **Per-class ray dropout**, calibrated position-matched against real (glass and dark paint return less than a closed hull): LUMPI Car 0.14 up to 15 m falling to 0.02 at 25 m, Van 0.43, Truck 0.20, Bus 0.70 (thin evidence: 9 matched boxes), clutter 0.10; other classes 0.02.

**Steps.**
1. G2-lite with unit tests (mesh insertion and occlusion, candidate-sensor occlusion, hull bank, dropout ramp, rider and hull fit, shrink-to-fit sizes, the pass, the reference sampling rate) and the pooled class-gate condition in `route_predictions.py --pooled` (`scorecard.pooled_gate`).
2. Corpora `g1-v4` on both tracks: the `g1-v3` recipes plus `--g2` (7 min LUMPI, 1-2 min V2X on 96 CPU workers); dataset card with the G2 statistics; position-matched density and size checks against the real labels (Section 8.7.2).
3. **Wave 0, the data-only ablation** (about 2 h): `pointpillars-g1v4` on both tracks against `pointpillars-g1v3`, the same detector; anchors follow the new label sizes (class-wise: LUMPI Truck short and long, V2X truck by length terciles; the S5 lesson that one anchor caps size realism). Continue only if the targeted classes gain on B and pooled; otherwise diagnose before 60 GPU-hours.
4. **Waves 1-2**: `voxelrcnn-ros-g1v4` and `pvrcnnpp-ros-g1v4` on both tracks, `pointpillars-ros-g1v4` on LUMPI; 40 epochs, the S5 seeds and schedules. ROS keeps the generic jitter, the Car and vehicle ranges, and a truck length tail (l up to 1.5x LUMPI, 1.4x V2X), now capped per class at the real 99th-percentile sizes (`CLASS_MAX`, legal realval label statistics; added after the first V2X run, see 8.7.2); the S5 Bicycle and full truck ranges go, because they would scale real-sized objects a second time.
5. Plain and TTA tuning with the per-class score blend; scorecards against the `g1-v3` parents with the AP-loss decomposition and the static share of walker false positives.
6. Portfolio `routed-g6`: V2X from `routed-g5` (the confirmed entry), LUMPI from `routed-g4` (the confirmed entry) with every S5 and R3 member, so each S5 LUMPI class change is decided again under the pooled condition; `select --rule joint --calibrated --pooled`, `fuse --max-members 3 --pooled`, `budget`, then the **final gate** `gate --vs <confirmed entry>`: the class gate and the pooled condition on the final predictions (score floors applied), where the pooled rule was validated; a failing class reverts to the entry's configuration (added after the first LUMPI portfolio: the S5 Car fusion passed the pooled check inside `fuse`, +0.010 at P 1.00, but not on the final predictions, +0.0006 at P 0.64, the S5 diagnosis value).
7. Realism: 50 `g1-v4` validation frames chosen as in S1 (FPD greedy on proxies 1-3), scored on the held-out proxies against the current frames (LUMPI `g1-v2` frames 0.905, V2X `g1-v3` 0.919).
8. Upload gate, package, kit check, record.

**Gates.** Class gate with the pooled A+B condition (from R3 on) for every member, route, fusion and calibration. Realism gate: held-out R up by at least 0.003 against the current frames (R2's rule; the earlier R3 target of 0.915 stays the goal), otherwise the frames stay. Upload gate: estimate (B) at least 0.005 above the best upload (LUMPI 0.541, V2X 0.967), and on LUMPI a projection above the 0.5040 entry. Strategy success: a `g1-v4` member passes the class gate against its `g1-v3` parent for a targeted class (LUMPI Car, Bicycle, Motorcycle, Truck, Bus, Person; V2X truck, pedestrian), and `routed-g6` passes the upload gate.

**Trade-offs and risks.**
- **Real data in the generator:** sizes, walker positions and five dropout values come from legal realval-A+B labels and points per box (allowed, as the S1 density prior and walker calibration); B is therefore not fully untouched for these few scalars, and the leaderboard confirmation stays the check.
- **Convex hulls** fill concavities (wheel arches, the gap between cab and trailer); exemplars give sparse actors another UT car's shape.
- **Hard negatives trade recall for precision:** walker-like clutter next to walkers may suppress real walkers near poles; Person recall at IoU 0.25 is watched in the scorecard.
- **Procedural riders** are a new synthetic signature for Bicycle and Motorcycle.
- **Remaining density gaps:** LUMPI Cars 25 m or more from the nearest sensor stay at about 0.6x; walkers drop from 0.86 to 0.80 (clutter and full-size cars occlude them, as in reality).
- **Long trucks:** queues leave room for 12-16 m in 36-42% of the LUMPI trucks, so the tail keeps coming partly from ROS.
- **Realism:** clutter at walker-anchored positions may raise CD and EMD of the realism frames (the hidden reference has its structures elsewhere); the frames change only through the realism gate.

**Time box.** Oct 11-12: engine, corpora, wave 0; Oct 12-13: waves 1-2 (about 60 GPU-hours on 8 GPUs); Oct 13-14: portfolio, gates, upload; inside the calendar's R3 slot (Oct 12-18).

#### 8.7.2 R3 results (2026-10-11 to 2026-10-13)

**Corpora `g1-v4`** (10,000 frames per track; LUMPI 5.2 min, V2X 1.2 min on 96 CPU workers; cards in `pcdet/g1-v4/dataset.yaml`). Per LUMPI frame: 43.9 actors re-cast (34.7 completed from the hull bank), 13.4 at a real size, 9.9 two-wheelers with riders, 30.0 clutter objects, 43,000 frame points removed as occluded; per V2X frame: 3.3 trucks re-cast at a real size, 30.0 clutter objects, 4,200 points removed. Boxes per frame 55.6 -> 55.1 (LUMPI) and 25.2 -> 23.9 (V2X): more boxes end empty behind full-size actors and clutter.

Position-matched point density, synthetic / real (realval-A+B, same BEV cell; Section 8.7.1 review item 1):

| Track | Class | `g1-v3` | `g1-v4` | Change |
|---|---|---|---|---|
| LUMPI | Car | 0.44 | **0.83** (0-15 m 1.03, 15-25 m 0.94, 25+ m 0.57) | re-cast at full size, glass dropout |
| LUMPI | Bicycle | 0.25 | **0.90** | riders |
| LUMPI | Motorcycle | 0.52 | **1.04** | riders |
| LUMPI | Truck | 0.83 | 0.91 | re-cast, real sizes |
| LUMPI | Bus | 2.2 | **1.06** (9 matched boxes) | real size, glass dropout |
| LUMPI | Van | 0.99 | 1.07 | re-cast (the stretched UT points were sparse, but UT's small cars occluded too little) |
| LUMPI | Person | 0.86 | 0.80 | unchanged walkers, now occluded by clutter and full-size cars |
| V2X | truck | 0.42 | **0.77** | real sizes, completed hulls |
| V2X | vehicle | 0.96 | 0.93 | unchanged |
| V2X | pedestrian | 0.98 | 0.95 | unchanged |

Sizes (medians, l x w x h in m; real from the legal size prior):

| Track / class | `g1-v3` | `g1-v4` | Real |
|---|---|---|---|
| LUMPI Truck | 7.94 x 2.89 x 3.46 (length 90th percentile 8.47) | 6.47 x 2.63 x 2.82 (10.2) | 8.35 x 2.93 x 3.15 (16.3) |
| LUMPI Bus | 10.27 x 3.94 x 4.25 (one asset) | 10.48 x 3.25 x 3.26 (12.1) | 12.04 x 3.29 x 3.25 (12.5) |
| LUMPI Bicycle | 1.66 x 0.58 x 1.62 | 2.00 x 0.85 x 1.92 | 2.00 x 0.84 x 1.90 |
| LUMPI Motorcycle | 2.19 x 0.87 x 1.53 | 1.96 x 0.85 x 1.77 | 1.96 x 0.85 x 1.77 |
| V2X truck | 5.20 x 2.07 x 2.10 (8.47) | **7.97 x 2.88 x 2.59** (11.3) | 8.20 x 2.89 x 2.59 (13.0) |

Real sizes need free road: UT trucks stand in queues, so a sample longer than the gap is shortened (never below the UT length). V2X trucks now match the real sizes; LUMPI Trucks keep a short-biased length (63% take a real size, 36-42% have room for 12-16 m), which the members' ROS length tail covers.

**Realism** (step 7; 50 frames of the `g1-v4` validation split chosen by the S1 selector on proxies 1-3; exact official R against every held-out legal proxy, both sets scored the same way):

| Track | Frames | Proxy 4 | Proxy 5 | Late 1 | Late 2 | Late 3 | EMD | FPD |
|---|---|---|---|---|---|---|---|---|
| LUMPI | current (`g1-v2`, S1) | 0.906 | 0.905 | 0.908 | 0.901 | 0.906 | 1.53-1.58 | 2.9-3.9 |
| LUMPI | **`g1-v4`** | **0.934** | **0.933** | **0.932** | **0.932** | **0.934** | 1.28-1.34 | 0.1-0.4 |
| V2X | current (`g1-v3`) | 0.916 | 0.916 | | | | 1.45-1.47 | 1.5-1.7 |
| V2X | **`g1-v4`** | **0.921** | **0.922** | | | | 1.38-1.39 | 1.3-1.4 |

On LUMPI the selector now reaches a pooled FPD of 0.02 against the fit proxies (random `g1-v4` frames 3.41; the S1 frames keep 2.9-3.9 against the held-out ones): the clutter supplies the above-ground static structure that R1 found missing, and the gain holds on the three late proxies closest to the test window (+0.024 to +0.031), so it is not a property of the selection proxies. The realism gate (+0.003) passes on both tracks, and LUMPI also meets the original R3 target (R >= 0.915 with FPD below 4). Caveat from R1-R2: the hidden reference differs from every legal frame (the S1 frames scored 0.905 locally and 0.891 on the leaderboard), so the leaderboard gain may be smaller; V2X R moves by about 0.003 with the draw of the (0,0,0) nulls, so the gate is re-checked as packaged (the packager's null draw, held-out proxies 4-5): **V2X 0.919 (S5 zip) -> 0.925, LUMPI 0.905 (S4 zip) -> 0.934: passed on both tracks**; `routed-g6` takes the `g1-v4` frames (`realism_frames: pcdet/g1-v4`, `test/synthetic_ids.txt`). Swapping the 50 frames changes only R: detection is scored on the kit's test frames.

**Wave 0: the data-only ablation** (`pointpillars-g1v4` against `pointpillars-g1v3`: same detector, anchors moved to the new label sizes; 40 epochs; official 3D AP@0.5 R40, realval-A / realval-B; gate = class gate on B with the pooled A+B condition):

| Track / class | plain `g1-v3` | plain `g1-v4` | TTA `g1-v3` | TTA `g1-v4` | gate (plain, TTA) |
|---|---|---|---|---|---|
| V2X vehicle | 0.563 / 0.607 | **0.646 / 0.627** | 0.598 / 0.604 | **0.690 / 0.667** | pass, pass |
| V2X pedestrian | 0.266 / 0.226 | **0.285 / 0.262** | 0.267 / 0.257 | **0.288 / 0.278** | pass, pass |
| V2X truck | 0.703 / 0.565 | **0.803 / 0.697** | 0.839 / 0.704 | **0.859 / 0.758** | pass, pass |
| V2X mAP | 0.511 / 0.466 | **0.578 / 0.529** | 0.568 / 0.522 | **0.612 / 0.567** | |

| LUMPI Person | 0.340 / 0.134 | 0.351 / 0.130 | 0.381 / 0.128 | **0.410 / 0.137** | fail, fail (TTA: dB +0.0098 at P 1.00, pooled +0.025 at P 1.00) |
| LUMPI Car | 0.873 / 0.768 | 0.859 / 0.755 | 0.890 / 0.778 | 0.883 / 0.775 | fail, fail |
| LUMPI Bicycle | 0.186 / 0.081 | **0.458 / 0.196** | 0.228 / 0.100 | **0.506 / 0.222** | pass, pass |
| LUMPI Motorcycle | 0.008 / 0.015 | 0.008 / 0.013 | 0.015 / 0.020 | 0.015 / 0.021 | fail, fail |
| LUMPI Bus | 0.011 / 0.012 | **0.023 / 0.079** | 0.011 / 0.009 | **0.047 / 0.096** | pass, pass |
| LUMPI Truck | 0.200 / 0.131 | 0.231 / 0.105 | 0.232 / 0.154 | 0.260 / 0.113 | fail, fail (B -0.041) |
| LUMPI mAP (late-A) | 0.248 / 0.163 (0.244) | **0.289 / 0.183** (0.269) | 0.271 / 0.170 (0.267) | **0.317 / 0.195** (0.296) | |

On V2X every class passes, plain and TTA (pooled P(gain) 1.00 throughout). The static hard negatives work as intended: confident static pedestrian false positives on B fall from 6.2 to 3.6 per frame (plain; TTA 1.67 -> 1.04), their share of the unmatched pedestrian boxes from 0.65 to 0.50, and the pedestrian ranking loss from 0.445 to 0.408. Truck localization loss falls from 0.204 to 0.004 (real sizes and class-wise anchors), with more truck ranking loss (0.181 -> 0.274) as the real-size trucks now compete with vehicles.

On LUMPI the member gains 0.025-0.029 mAP on A, B and late-A, through two classes: **Bicycle** (B 0.100 -> 0.222; recall at IoU 0.25 0.88 -> 0.96: the riders) and **Bus** (0.009 -> 0.096: real sizes); Person rises on A, B and pooled but stays 0.0002 under the 0.01 B threshold; static Person false positives fall in the plain variant (9.7 -> 7.0 per frame on B). **Truck regresses on B** (0.154 -> 0.113): confident unmatched trucks of 11 m or more appear (1.7-1.9 per real frame, none before), 70% of them static and most at two places of the real intersection (around (18, -28) and (-12, 36), in Measurements 4, 5 and 6), 4.9 m tall with about 470 points. There the real frames have about twice the synthetic returns between 1.5 and 5 m: a tall static structure the twin under-represents, which the real-size long trucks and the new long anchor (12.1 m) now call a truck. The portfolio takes LUMPI Truck from whichever member passes the gate; long tall static hard negatives (walls, hedges, tree rows) are a follow-up corpus (`g1-v5`) if the two-stage members show the same failure. Motorcycle stays near zero (ranking loss 0.84: found but outranked, mostly by Bicycle boxes of the same size now).

**Wave 1, first V2X run: a size tail beyond reality.** `voxelrcnn-ros-g1v4` (TTA) gained on vehicle (B 0.811 -> 0.830, gate passed) but lost trucks (0.797 -> 0.418) with recall at IoU 0.25 still 0.998: about one confident truck of 19.4-20.0 m per real frame overlapping no labeled object, at a long static structure. The truck length range of ROS (up to 1.4x) on top of real sizes produced training trucks up to 19 m (real V2X trucks: 99th percentile 13.4 m), and the anchor-free head fitted the longest of them onto the structure; the anchor-based pillars (longest anchor 12.2 m) do not. Fix: `bdc_object_scaling` caps every scaled size at the real 99th percentile of its class (`CLASS_MAX`, unit test), in all five R3 two-stage and ROS configs; the run is kept as the ablation `run0_rostail` (registry rows annotated) and both V2X two-stage members are retrained (the PV-RCNN++ run was stopped after one hour). LUMPI `voxelrcnn-ros-g1v4` was already at epoch 30 with the uncapped config and is evaluated as is.

**Wave 1, V2X `voxelrcnn-ros-g1v4` with the cap** (TTA, A / B against `voxelrcnn-ros-g1v3`): vehicle **0.787 / 0.811 -> 0.831 / 0.832** (gate passed, pooled +0.037), truck 0.856 / 0.797 -> 0.849 / 0.803 (the collapse is gone: confident unmatched trucks 1.02 -> 0.04 per B frame, lengths 5.4-6.3 m; plain truck B +0.063), pedestrian 0.349 / 0.393 -> 0.340 / 0.376 (-0.017).

**Wave 2, `pvrcnnpp-ros-g1v4`** (with the cap; A / B against `pvrcnnpp-ros-g1v3`): LUMPI (TTA) **Person 0.243 / 0.070 -> 0.402 / 0.101** (pooled +0.104; static Person false positives on B 12.3 -> 5.0 per frame), **Bicycle 0.499 / 0.201 -> 0.524 / 0.230**, **Motorcycle 0.013 / 0.010 -> 0.046 / 0.029** (all three pass), Car -0.014, Truck -0.021 and Bus -0.010 on B; V2X (plain) **vehicle 0.770 -> 0.790, pedestrian 0.308 -> 0.336, truck 0.710 -> 0.773 on B**, all three passing (its TTA tuning ran out of GPU memory next to a training job and was rerun).

**Wave 1, LUMPI `voxelrcnn-ros-g1v4`** (uncapped ROS config; TTA, A / B against `voxelrcnn-ros-g1v3`): **Person 0.287 / 0.084 -> 0.435 / 0.104** (gate passed, pooled +0.088), with confident static Person false positives on B down from 14.5 to 6.1 per frame and the ranking loss from 0.516 to 0.436: the clutter hard negatives work on the two-stage member too, the first detector-level change to move LUMPI Person since S3. Motorcycle 0.015 / 0.013 -> 0.042 / 0.025 (passed; still small). Losses: **Bus 0.077 -> 0.008 on B** (recall at IoU 0.25 0.62 -> 0.23) and **Truck 0.142 -> 0.104**, Car -0.010. Unlike V2X there are no long false trucks; with real sizes, buses (10-12 x 3.3 m) and short trucks (5-6 m) resemble trucks and cars (confident false trucks on real cars on B: 678 -> 1,208), while the UT bus asset (3.94 m wide, 4.25 m tall) had been easy to tell apart. The per-class portfolio keeps those classes with the members that pass.

**Engine findings on the way** (each fixed before the full build): the merged multi-lidar frame needs the all-candidate-sensor occlusion rule; the object sampling rate has to stay the G1 one; sparse hulls need exemplar completion; lengthening by a coin flip grew only 8% of the trucks, and resampling until a size fits biased buses to 8.9 m.

**Wave 2, LUMPI `pointpillars-ros-g1v4`** (TTA, against `pointpillars-ros-g1v3`): Bicycle B 0.118 -> 0.225 (passed), Person A 0.332 -> 0.402 and B +0.004, Truck B 0.190 -> 0.127 (the long-anchor failure of wave 0); V2X `pvrcnnpp-ros-g1v4` TTA: pedestrian B 0.354 -> 0.369 and truck 0.786 -> 0.813 (both passed), vehicle +0.005.

**Portfolio `routed-g6`** (LUMPI from the confirmed `routed-g4` with the S5 and R3 members, 28 members; V2X from the confirmed `routed-g5` with the R3 members, 30; `select --calibrated --pooled`, `fuse --max-members 3 --pooled`, `budget`, then the final gate against the entry; realval-A / realval-B):

| Track / class | Entry | `routed-g6` | Source | dB (P), pooled (P) |
|---|---|---|---|---|
| LUMPI Bicycle | 0.525 / 0.202 | **0.600 / 0.264** | `vrros_tta` + `pvros4_tta` + `pp4_tta` (IoU 0.7) | +0.062 (1.00), +0.069 (1.00) |
| LUMPI Bus | 0.011 / 0.011 | **0.079 / 0.134** | `ppros4_tta` + `vrros_tta` (IoU 0.3) | +0.123 (1.00), +0.094 (1.00) |
| LUMPI Truck | 0.231 / 0.153 | **0.466 / 0.200** | `pvros_tta` + `ppros_tta` + `pvros4_tta` (IoU 0.3) | +0.047 (1.00), +0.138 (1.00) |
| LUMPI Car | 0.898 / 0.792 | S4 kept | the S5 fusion passed `fuse` but **not the final gate** (pooled +0.0006, P 0.64) | reverted |
| LUMPI Person | 0.396 / 0.146 | S4 kept | best joint fusion (A 0.473, B 0.150) under the B bar (+0.004) | 0 |
| LUMPI mAP (late-A) | 0.313 / 0.188 (0.304) | **0.367 / 0.221 (0.341)** | | +0.033 (+0.028 to +0.039) |
| V2X pedestrian | 0.350 / 0.397 | **0.370 / 0.408** | `vrros_tta` + `vrros4_tta` (IoU 0.5) | +0.011 (0.99), +0.022 (1.00) |
| V2X vehicle, truck | S5 | S5 kept | best candidates +0.009 on B (P 0.995) | 0 |
| V2X mAP | 0.694 / 0.699 | **0.701 / 0.703** | | +0.004 (+0.001 to +0.007) |

Two classes that passed in the early portfolios (LUMPI Person B +0.015 with the wave-0 member, V2X vehicle +0.012 with the first two-stage member) did not pass in the final ones: `fuse` tests only the best joint candidate, and with more members a set with a higher A and a smaller B gain won the ranking. Picking the earlier winners now would select on B across runs, so the final result stands.

**Gates.** Upload gate (unclipped estimate from R3 on, [`decisions/README.md` 3.2](decisions/README.md#32-gates)):

| Track | A-mAP | B-mAP (90% interval of the gain) | late-A | BEV-3D gap (B) | 3D@0.7 (B) | R (as packaged) | Estimate (B) | Bar | Server check | Gate |
|---|---|---|---|---|---|---|---|---|---|---|
| LUMPI | 0.313 -> **0.367** | 0.188 -> **0.221** (+0.028 to +0.039) | 0.304 -> 0.341 | 0.021 -> 0.021 | 0.064 -> 0.086 | 0.905 -> **0.934** | 0.523 (S4) / 0.541 (S5) -> **0.563** | 0.546 | 180 s, 16,262 boxes | **passed** |
| V2X | 0.694 -> **0.701** | 0.699 -> **0.703** (+0.001 to +0.007) | | 0.048 -> 0.049 | 0.178 -> 0.180 | 0.919 -> **0.925** | 0.967 -> **0.9726** (0.970 clipped) | 0.972 | 56 s, 8,682 boxes | **passed** (by 0.0006) |

Leaderboard projection (previous leaderboard mAP + 0.6 x the mean of the A and B gains; R without and with the S1 local-to-leaderboard realism offset): LUMPI **0.526-0.538** against 0.5040 (two thirds of the gain is realism if it transfers), V2X **0.876-0.878** against 0.8730. Decision record: [`decisions/2026-10-12-r3-g2-lite.md`](decisions/2026-10-12-r3-g2-lite.md).

**Leaderboard (2026-10-14 UTC).** V2X 986496: combined **0.8789** (mAP 0.5929, R 0.9268), rank 1 of 19, confirmation passed (+0.0059, projected 0.876-0.878): pedestrian 0.391 -> 0.403, vehicle and truck identical. LUMPI 986489: combined **0.5169** (mAP 0.1680, R 0.9323), rank 1 of 21 (Raj Patil 0.4914 second), confirmation passed (+0.0129, projected 0.526-0.538) **through realism**: R 0.891 -> 0.932 (EMD 1.647 -> 1.302, FPD 5.10 -> 0.52), while the mAP fell by 0.004 (Truck +0.025, Bus +0.003, **Bicycle 0.244 -> 0.188**; Person, Car, Motorcycle, Van identical).

| Transfer | Local gain | Leaderboard gain | Ratio |
|---|---|---|---|
| V2X pedestrian (B) | +0.011 | +0.012 | 1.1 |
| V2X realism (as packaged) | +0.0064 | +0.0065 | 1.0 |
| LUMPI realism (as packaged) | +0.028 | +0.041 | 1.5 |
| LUMPI Truck (B) | +0.047 | +0.025 | 0.5 |
| LUMPI Bus (B) | +0.123 | +0.003 | 0.02 |
| LUMPI Bicycle (B) | +0.062 | -0.056 | sign wrong (S5: +0.023 -> -0.030) |

**LUMPI diagnosis** (no test labels used). At test size (realval frames resampled to the test window's 80 bicycles, 190 trucks, 25 buses) the R3 - S4 changes would lie in Bicycle -0.011 to +0.102, Truck +0.084 to +0.165, Bus +0.029 to +0.252 (90%): the leaderboard values are not sampling noise. On the 50 test frames the R3 portfolio emits 3.68 confident Bicycle boxes per frame (S4 3.16) against about 1.6 real bicycles per test frame (realval-A 4.84); every Bicycle member fires 1-19% more on the test frames than on realval-A, and Bicycle boxes on real motorcycles are unchanged (0.47 -> 0.49 per motorcycle). As in S5, a more sensitive Bicycle detector meets a test window with a third of the bicycle density and false positives on content the realval frames lack. Reverting LUMPI Bicycle because of these numbers would tune on the test set and is not done.

**What R3 taught.**
1. **Compare synthetic and real data in the same place.** Range bins from the frame origin called every LUMPI actor class too sparse; matched by BEV cell only Cars and two-wheelers were, and Vans were already right.
2. **Ray-consistent insertion into merged multi-lidar frames needs the candidate-sensor rule**, and the object sampling rate must stay fixed when the background changes, or every calibration depends on the amount of clutter.
3. **Static hard negatives halve the static walker false positives** in every LUMPI two-stage member (14.5 -> 6.1, 12.3 -> 5.0 per frame) and lift LUMPI Person by 0.02-0.03 on B per member; ranking among the new members is the next walker step.
4. **Real sizes need a ceiling and context:** augmentation beyond the real size range produced 19.7 m false trucks (V2X), a long anchor fired on a tall static structure (LUMPI), and real-size buses and short trucks blur into trucks and cars; per-class routing keeps each class with the members that handle it.
5. **Generator content moves realism where frame selection could not** (R2 failed at the selection limit): LUMPI 0.905 -> 0.934 on every held-out proxy including the late ones, and **0.891 -> 0.932 on the leaderboard**: the gap between the legal proxies and the hidden reference (0.015 with the S1 frames) shrank to 0.002.
6. **Gate on what is submitted:** the pooled condition on the final predictions (score floors applied) reverts the S5 Car change that the per-step check passed; the upload estimate is unclipped once B-mAP passes 0.7.
7. **LUMPI Bicycle does not follow any local split** (S5 and R3, both pooled P 1.00 locally, both lost on the leaderboard): a further LUMPI Bicycle change needs a test-window-like proxy (realval frames re-weighted to the test window's class counts) before it is trusted.

### 8.8 Final phase plan (Nov 1-14)

The final phase scores the same test data with **1 submission per day, 5 in total, a hidden leaderboard, and no carry-over** of development submissions ([`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md)). The competition has a single leaderboard (`Results`, rule `Force_Best`), and the final phase hides the scores (`hide_score_output`), so the best final submission most likely counts (checked through the public API on 2026-10-15; to be confirmed in the organizer email).
1. Before Nov 1: re-package every candidate from its saved predictions and check it byte for byte against its scored upload copy (done for R3 on 2026-10-14), run `check_submission.py --official`, and store the zips.
2. F1 (Nov 1): the best confirmed version per track, as the exact zip scored in the development phase (since 2026-10-17 S6: `lumpi_s6_submission.zip` (995869) and `v2x_s6b_submission.zip` (995877), release 6.0, with their weights as release assets and verified reproduction scripts).
3. F2-F5: only versions that passed every local gate, preferably confirmed in the development phase before it closes (Oct 30); with `Force_Best` an unconfirmed gated candidate cannot lower the result, but each try costs one of the five slots and an invalid zip may too, so every zip passes the kit check first.
4. Record every final submission like a development one (`codabench_<id>.json`, the register in `decisions/README.md` Section 2, track model README Section 9, root README Section 9) and write the 4-8 page report (due Nov 15) from the retrospective (Section 8.10), the progression tracker, the submission register and the decision records.

### 8.9 R5 Realism-led refinement (after R3; review and plan 2026-10-14)

**Position.** R5 starts from the confirmed R3 entries (`routed-g6` on both tracks) and builds `routed-g7`. It is a new strategy code, not an R3 variant, because it changes the generator again (corpus `g1-v5`), adds members, and adds pre-registered selection rules. The rules review that precedes it is [`decisions/2026-10-14-rules-compliance-review.md`](decisions/2026-10-14-rules-compliance-review.md).

**Review (2026-10-14): what the data says after R3** (legal validation data only; probe scripts in `$BDC_DATA/logs/r5/`).
1. **Competition.** Top 3 is secure on both tracks (third place LUMPI 0.277, V2X 0.538). LUMPI rank 1 is contested: Raj Patil is 0.0255 behind and gained 0.013 in five days, all from detection; the LOI window is open until Oct 30.
2. **A test-window-like proxy does not predict LUMPI Bicycle.** realval-A re-weighted to the test window's public per-frame class counts (and late-A) predicts Bicycle gains of +0.025 (S4 -> S5) and +0.070 (S4 -> R3) where the leaderboard lost 0.029 and 0.056; the planned proxy gate is dropped. Truck cannot be re-weighted at all (3.8 trucks per test frame, effective sample 6 frames).
3. **LUMPI label provenance drifts over Measurement4.** The share of manually corrected Person labels is 0.99, 0.97, 0.83 and 0.69 in frames 0-1599, -3199, -4799 and -6399; automatic Person boxes are 1.20-1.25 m long against 0.75-0.80 m. On late-A the R3 portfolio's recall at IoU 0.5 is 0.72 on corrected labels and 0.49 on automatic ones. Bus and Motorcycle labels after frame 3200 are all automatic. This explains why leaderboard Person (0.157) follows realval-B (0.145, mostly automatic labels) and not realval-A (0.396). No post-processing exploits it safely (every resize or convention copy that helps B loses on late-A); the consequence is the Person selection rule below.
4. **Walker localization** (AP@0.25 - AP@0.5: LUMPI Person 0.29, V2X pedestrian 0.28) is a random centre error of 0.16-0.22 m on near misses, not a convention offset. Copies of each walker box shifted by 0.15 m and scored below every original box gain +0.010 AP on V2X pedestrian and +0.005-0.007 on LUMPI Person; copies scored among the originals are unstable.
5. **Residual realism is in the background.** Attributing the exact EMD transport of the R3 frames point by point (real-vs-real baseline: one legal proxy against another): LUMPI EMD 1.32 against 1.01, of the excess 44% serves real ground points, 26% points 0.5-1.5 m up, 18% 1.5-3 m and 11% above 3 m; V2X 1.36 against 0.76, 43% ground (the synthetic frames lack ground near the sensor). Tall static structure is a minor share, so the planned walls and hedges are not built. The LUMPI background density prior was fitted on the G1 output (`g1-v1`) and is miscalibrated for G2-lite; V2X never had one (item E8).
6. **Realism ceiling.** Legal LUMPI proxies scored against each other reach R 0.947-0.953 (EMD 0.93-1.03); our leaderboard R is 0.932 and the LUMPI leader's 0.942 (EMD 1.11): all of the remaining LUMPI realism gap is EMD.
7. **Sparse transformers (S6)** stay post-freeze research: no sim-to-real evidence, the ECCV runner-up's DSVT LUMPI write-up scored 0.4692, and five strategies showed transfer, not capacity, is the limit (`torch_scatter` 2.1.2 has a cu121 wheel; VoxelNeXt needs no new dependency).

**Hypothesis.** A background density prior fitted to the G2-lite output closes part of the EMD gap on both tracks (realism transfers at 1.0-1.5x, the most reliable lever); seeds and a member set trained on the new corpus add fusion diversity; walker tail copies add a small, risk-free walker gain; ranking LUMPI Person on late-A picks fusions that match the test window's label provenance.

**Pre-registered rules** (written before the R5 portfolio runs; they cannot be tuned to its results):
1. **Density prior:** candidates are compared on random 50-frame draws against the fit proxies 1-3 only; the held-out proxies (4, 5, late-1-3) judge the final corpus once.
2. **Realism frames** change only if the held-out R of the packaged frames gains at least 0.003 over the R3 frames (R2 rule), on every held-out proxy on average.
3. **LUMPI Person:** fusion candidates are ranked by late-A AP; the top 3 go through the class gate and the pooled condition in that order; the first that passes is kept (`fuse --late-rank Person --gate-top 3`).
4. **LUMPI Bicycle, Motorcycle and Bus are frozen** at their R3 configuration: no local split has predicted them (Bicycle lost twice after pooled P 1.00 gains; Bus +0.123 on B gave +0.003; Motorcycle has 30 realval-A labels). Truck stays gated as usual (both Truck changes transferred with the right sign, at 0.5-0.8x B).
5. **Walker tail copies** (`route_predictions.py tail`, after `budget`): the copy radius is chosen on realval-A; a copy-only change needs a gain on B and on the pooled frames with P >= 0.9, but not the 0.01 bar of the class gate, because copies cannot lower AP on any frame set (the waiver was decided after the first V2X run measured dB +0.0098; it is recorded here for that reason).
6. **Final gate** against the R3 entry (`gate --vs routed-g6`), then the upload gate: unclipped estimate (B) at least 0.005 above the R3 uploads (LUMPI 0.568, V2X 0.978), kit scorer valid in under 400 s.

**Steps.**
1. Seeds: `voxelrcnn-ros-g1v4-s2` and `pvrcnnpp-ros-g1v4-s2` on both tracks (`pcdet_train.py --seed 1666`; OpenPCDet hard-codes 666).
2. Density prior: LUMPI by iterative proportional fitting (`fit_density_prior.py --base`, one step from the v1 prior on the `g1-v4` output: `gen/density_prior_v2.npz`); V2X first prior, 8 m cells (`gen/density_prior_v1.npz`). Corpus `g1-v5` = the `g1-v4` recipe with that prior.
3. Realism frames from the `g1-v5` validation split: FPD selection (S1) and the EMD-targeted refinement (`select_realism_frames.py --objective fpd+emd`); rule 2 decides.
4. Retrain the R3 member set on `g1-v5` (`pointpillars-g1v5`, `voxelrcnn-ros-g1v5`, `pvrcnnpp-ros-g1v5`, LUMPI `pointpillars-ros-g1v5`); plain and TTA tuning, score blend.
5. `routed-g7`: every new member plain and TTA; `select --rule joint --calibrated --pooled`, `fuse --max-members 3 --pooled` (LUMPI with rule 3), rule 4, `budget`, `tail`, final gate; package, kit check, scorecard against `routed-g6`.
6. Fallback: the R3 zips re-verified from their saved predictions for the first final-phase submission.

#### 8.9.1 R5 results (2026-10-14)

**Run.** One day of wall time on the 8 GPUs (detached chains and a shared queue; logs and `status.sh` in `$BDC_DATA/logs/r5/`). Seed runs of the two strongest two-stage members per track; on V2X the R3 member set retrained on `g1-v5`; the LUMPI `g1-v5` retrain was skipped by the realism gate. Two TTA tunings ran out of GPU memory next to a training job and were rerun; the after-training evaluation of OpenPCDet fails on the checkpoint being written (exit code 1, as in R3), so every checkpoint was loaded once to confirm it.

**Density prior and realism** (exact official R; random 50-frame draws of the validation split, then the selected frames):

| Track | Prior | Random draws, fit proxies 1-3 | Random draws, held-out | Selected frames, held-out | Gate (+0.003 over the R3 frames) |
|---|---|---|---|---|---|
| V2X | none (`g1-v4`) | 0.912 | | 0.9254 (R3 frames) | |
| V2X | **v1, 8 m cells** (4 m: 0.9335; a second step: 0.932) | **0.934** | 0.935 | FPD 0.9318, **FPD + EMD 0.9336**; as packaged 0.9366 | **passed** |
| LUMPI | v1 (fitted on G1, `g1-v4`) | 0.918 | 0.912 | 0.9332 (R3 frames) | |
| LUMPI | one-step refit on the G2-lite output | 0.892 | | | |
| LUMPI | **v2 = v1 refined once (iterative fitting)** (more steps 0.927, 0.925) | **0.929** | 0.920 | FPD 0.9326, FPD + EMD 0.9360 | **failed (+0.0028)** |

The one-step refit fails because the uniform G2-lite output lies far from real in y (mean -4.2 m against 0.0) and cells that need more mass saturate once all their points are kept; one step of iterative proportional fitting from the old prior corrects it. The EMD-targeted refinement of the selection helped on both `g1-v5` pools (+0.002 to +0.003 held-out) and lost on `g1-v4` (-0.002), so it is no general improvement. On LUMPI the prior lifts random frames (+0.008 held-out) but selection from `g1-v4` already reached the same level, so the R3 frames stay.

**Members** (TTA, realval-A / realval-B; seed 1666 against the R3 member trained with seed 666):

| Track | Member | R3 member | R5 | Notes |
|---|---|---|---|---|
| V2X | Voxel R-CNN seed 2 | 0.673 / 0.670 | 0.650 / 0.619 | vehicle 0.846 (0.832), pedestrian 0.376 (0.376), **truck 0.636 (0.803)** |
| V2X | PV-RCNN++ seed 2 | 0.663 / 0.666 | 0.671 / 0.671 | |
| V2X | pillars `g1-v5` | 0.612 / 0.567 | 0.641 / 0.589 | truck 0.758 -> 0.827: the prior also helps detection |
| V2X | Voxel R-CNN `g1-v5` | 0.673 / 0.670 | 0.651 / 0.639 | pedestrian 0.384, the best Voxel R-CNN variant |
| V2X | PV-RCNN++ `g1-v5` | 0.663 / 0.666 | **0.684** / 0.669 | pedestrian 0.380 |
| LUMPI | Voxel R-CNN seed 2 (with the size cap the R3 run lacked) | 0.343 / 0.178 | 0.336 / 0.188 | **Person 0.104 -> 0.137**, Truck 0.104 -> 0.137 |
| LUMPI | PV-RCNN++ seed 2 | 0.342 / 0.191 | 0.343 / 0.196 | **Person 0.101 -> 0.124** |

**Portfolio** (`routed-g7`: LUMPI 32 members, V2X 40; select, fuse with the late-A Person rule, budget, freeze, tail, final gate; realval-A / realval-B):

| Track / class | R3 | R5 | Source | dB (P), pooled (P) |
|---|---|---|---|---|
| LUMPI Person | 0.396 / 0.145 | **0.465 / 0.160** | `pp4_tta` + `vrros4s2_tta` (IoU 0.5): late-A rank 3 of the tested candidates; ranks 1 and 2 (triples, late-A 0.366 and 0.365) failed on B (dB -0.002, -0.0004) | +0.015 (1.00), +0.053 (1.00) |
| LUMPI Car | 0.898 / 0.792 | R3 | passed `fuse` (+0.011 at P 1.00), reverted by the final gate (pooled -0.0003, P 0.39) | 0 |
| LUMPI Person tail copies | | not used | +0.008 on B with r 0.2 m, but 34,793 boxes and 443 s in the kit scorer | |
| V2X vehicle | 0.828 / 0.852 | **0.857 / 0.864** | `pvros4s2_tta` + `vrros4s2_tta` + `vrros5_tta` (IoU 0.7) | +0.012 (0.99), +0.024 (1.00) |
| V2X pedestrian | 0.370 / 0.408 | **0.381 / 0.418** | R3 fusion + tail copies (r 0.15 m, 4 copies) | +0.010 (1.00), +0.010 (1.00) |
| V2X truck | 0.905 / 0.848 | R3 | best fusion +0.008 on B; a floor change reverted by the final gate | 0 |

**Gates.** V2X: estimate (B) 0.9726 -> **0.9833** against the bar 0.978, kit scorer 132 s with 24,759 boxes: **upload gate passed**. LUMPI: 0.5631 -> **0.5649** against 0.568, late-A 0.341 -> 0.351, kit scorer 157 s with 15,009 boxes: **upload gate not met** (a Person-only change; the entrant's call, as S4). Projection (previous leaderboard mAP + 0.6 x the mean of the A and B gains; realism at 1.0-1.5 x the packaged gain): V2X **0.889-0.891** against 0.8789, LUMPI **0.519-0.520** against 0.5169. Decision record: [`decisions/2026-10-14-r5-realism-led.md`](decisions/2026-10-14-r5-realism-led.md).

**Leaderboard (2026-10-15 UTC).** V2X 990255: combined **0.8852** (mAP 0.5972, R 0.9332), rank 1 of 20, confirmation passed (+0.0063, projected 0.889-0.891): pedestrian 0.403 -> 0.413, vehicle 0.719 -> 0.721, truck identical; realism CD 2.181 -> 1.986, MMD 0.0015 -> 0.0006, EMD 1.345 -> **1.182**, FPD 0.733 -> 1.468. LUMPI 990245 (uploaded below the upload gate by the entrant's call): combined **0.5198** (mAP 0.1714, R 0.9323), rank 1 of 21 (Raj Patil 0.4914), confirmation passed (+0.0029, projected 0.519-0.520): **Person 0.157 -> 0.180**, every other class and the realism identical.

| Transfer | Local gain | Leaderboard gain | Ratio |
|---|---|---|---|
| V2X pedestrian, tail copies (B) | +0.0098 | +0.0105 | 1.07 |
| V2X vehicle, fusion of new members (B) | +0.0119 | +0.0023 | 0.19 |
| V2X realism (as packaged) | +0.0112 | +0.0065 | 0.58 (EMD about 0.9 x; FPD rose on the server) |
| LUMPI Person, late-A rule (B) | +0.0149 | +0.0236 | 1.58 |
| mAP against the projection rule | V2X +0.0062, LUMPI +0.0036 | +0.0043, +0.0034 | 0.69, 0.94 |

**What R5 taught.**
1. **Seed variance is as large as many strategy steps** (V2X truck 0.64-0.80 on B for one config); member comparisons on one run each carry it, and seed fusions average it out.
2. **A density prior must be fitted to the generator it corrects**, iteratively when cells saturate; on V2X it is the realism lever (+0.011 R) and helps the detector too.
3. **The final gate on the final predictions is necessary:** it caught the second LUMPI Car gain that existed only before the score floors.
4. **Pre-registered rules held** where it was tempting to bend them: the LUMPI realism gate failed by 0.0002 and the frames stayed; the only waiver (the 0.01 bar for tail copies) has a proof behind it and is recorded with the number that prompted it.
5. **LUMPI Person moved for the first time since S3,** through the members that see the static clutter (seeds of the `g1-v4` two-stage members) and a selection rule matched to the test window's label provenance.
6. **What transferred:** the walker tail copies (1.07 x, as their construction predicts) and the late-A Person rule (1.6 x B); the V2X vehicle fusion of new members did not (0.2 x), and its 3D mAP@0.7 fell on the server as it did locally.
7. **V2X realism proxies do not hold the reference's moments:** the EMD gain transferred, the FPD doubled on the server while it fell locally; the next V2X frame change should be judged on EMD and FPD separately.

### 8.10 Retrospective after R5 (2026-10-15): what each step bought, why, and what is left

**Benefits per step on the leaderboard** (official scores of every scored upload; the combined change is split into its detection part, 0.6 x dmAP / 0.7, and its realism part, 0.4 x dR):

| Step | What it changed | V2X combined (detection, realism) | LUMPI combined (detection, realism) |
|---|---|---|---|
| S1 | engine G1 (walkers ray-cast with the real sensors, actor scale fix, density and FOV calibration), PointPillars, per-class post-processing, routing | **0.7665** (first upload) | **0.4728** (first upload) |
| S1+C1 | range-dependent z calibration (V2X) | +0.0190 (+0.0190, 0) | no version |
| S2 | CenterPoint members | no version | no upload (below the gate) |
| S3 | 8-view TTA as routable members, cross-architecture box fusion, score floors | **+0.0526** (+0.0526, 0) | **+0.0287** (+0.0287, 0) |
| S4 | two-stage members (Voxel R-CNN, PV-RCNN++) in fusions | +0.0104 (+0.0104, 0) | +0.0025 (+0.0025, 0) |
| S5 | class-wise object scaling to the real size ranges, GBlobs in fusions | **+0.0245** (+0.0245, 0) | -0.0001 (not listed) |
| R3 | engine G2-lite (real-size re-cast actors, riders, static clutter) | +0.0059 (+0.0033, +0.0026) | **+0.0129** (-0.0035, **+0.0164**) |
| R5 | density prior for G2-lite, seeds, tail copies, late-A Person rule | +0.0063 (+0.0037, +0.0026) | +0.0029 (+0.0029, 0) |
| S6 (added 2026-10-17) | seed bags; LUMPI Van judged on early/late realval-A; V2X variant b (bag fusions by the pooled condition) | **+0.0079** (+0.0079, 0) | +0.0029 (+0.0029, 0) |
| **Total since S1** | | **0.7665 -> 0.8931 (+0.1266: detection +0.1214, realism +0.0052)** | **0.4728 -> 0.5228 (+0.0500: detection +0.0335, realism +0.0164)** |

Per class on the leaderboard since S1 (to S6): V2X vehicle 0.585 -> 0.735, **pedestrian 0.235 -> 0.413**, truck 0.574 -> 0.671; LUMPI **Person 0.117 -> 0.180**, Car 0.633 -> 0.652, **Bicycle 0.053 -> 0.188** (peak 0.244 in S4), Truck 0.028 -> 0.058, Bus 0.000 -> 0.003, Motorcycle 0.001 (unchanged), Van 0.118 -> 0.141 (unchanged until the S6 judge). S1 itself is measured only locally (no baseline upload): walkers took V2X pedestrian from 0 to 0.266 and LUMPI Person from 0 to 0.341 on realval-A, and the density calibration took LUMPI realism from 0.59 to 0.906; it was rank 1 on both tracks at its first upload, above the ECCV winners on V2X (0.746).

**The main drivers, in order of leaderboard value.**
1. **Fill what the twin is missing, with the real sensor and annotation conventions** (S1 walkers and calibration; R3 riders, real sizes and static clutter): the foundation of both tracks, and on LUMPI the largest realism gain (R3 +0.041 R).
2. **Average out member noise at inference** (S3 TTA and fusion: 44% of the V2X and 61% of the LUMPI leaderboard gain; R5 seeds and tail copies): the largest single detection lever on both tracks.
3. **Give the box head the real size distribution** (S5 object scaling, then R3 real sizes): V2X pedestrian +0.045 and truck +0.029 in one step; capped at the real sizes after the 19.7 m false trucks.
4. **Correct conventions the detector cannot learn from the twin** (S1 post-processing per class, S1+C1 z calibration, R5 late-A Person rule): cheap and transferable.
5. **Refinement and capacity mattered least** (S2 CenterPoint: no transferable gain except LUMPI Bicycle through S3; S4 two-stage: vehicle and truck localization only).

**Lessons by theme.**

| Theme | Lesson | Evidence |
|---|---|---|
| Synthetic data | The decisive gaps were content and conventions (missing walkers, 0.78x actors, no static structure, few asset sizes), not detector capacity | S1, R3; S1 pillars beat the ECCV runner-up's DSVT ensembles |
| Synthetic data | Compare synthetic and real data in the same place (BEV cell), not by frame-origin range | R3 density review |
| Synthetic data | A density prior must be fitted to the generator it corrects, iteratively when cells saturate | R5 (one-step refit on G2-lite was worse) |
| Synthetic data | Size augmentation needs a ceiling at the real sizes, and anchors cap it | S5 pillars truck, R3 19.7 m trucks |
| Detectors | Weak members can be good fusion members; architecture diversity helps fusions more than single-model rank | S3-S5 fusions (GBlobs, CenterPoint) |
| Detectors | Seed variance is as large as many strategy steps (up to 0.17 AP per class on B for one config) | R5 seeds |
| Inference | TTA and box fusion transfer; so do copies scored below every original (provably non-negative) | S3; R5 tail copies 1.07 x |
| Inference | The remaining errors are ranking errors and misses, not near-misses: tail hedges of every other kind add 0.000-0.003 AP | S6 review probe (Section 8.6) |
| Validation | realval-A over-predicts LUMPI levels; realval-B predicts levels; gains transfer at about 0.6 x the mean of the A and B gains (0.25-1.9 x, sign right 9 of 11) | decisions README 3.1 |
| Validation | Gate on the final predictions, pooled over A and B: it caught two false LUMPI Car gains (S5, R5) | R3, R5 final gates |
| Validation | Each class needs a judge whose labels share the test window's semantics: realval-B's LUMPI class 6 is not vans; late Measurement4 Person and Bus labels are automatic | S6 review (Section 8.6); R5 Person rule |
| Validation | Rare LUMPI classes (Bicycle, Motorcycle, Bus) follow no local split; a class-count proxy fails its backtest | S5, R3, R5 |
| Realism | Frame selection saturates (R2); generator content moves realism (R3); the local proxies represent the reference's EMD but not always its moments (V2X R5 FPD) | R2, R3, R5 |
| Integrity | Pre-register the rules a run will be judged by; waive only with a proof, and record it | R5 |
| Operations | Long runs need detached chains, event logs and a status script; TTA tuning next to training can run out of memory; OpenPCDet's after-training evaluation races the last checkpoint | R3, R5 |

**Gaps going into S6** (each a reason for the S6 plan in Section 8.6):
1. **Gate blind spots:** a class whose second split does not share the test labels' semantics can never pass the B gate. LUMPI Van has used the S1 member since S1 although later members score higher on realval-A, the split that has predicted its leaderboard level (A 0.122, leaderboard 0.118).
2. **Member noise:** single-seed members make every selection partly a draw; seed bags (fusions of several seeds of one configuration) are untried.
3. **LUMPI Truck** transfers at 0.3-0.5 x B; long false trucks stand at the same tall static structures in Measurements 4-6.
4. **LUMPI realism:** EMD 1.30 against the leader's 1.11 and about 1.0 real-vs-real; frame selection is near its limit.
5. **Detector capacity** (the original S6) has no supporting evidence in this challenge.
