# 02. Strategy: how this competition is won

> Built on `01-CHALLENGE-FACTS.md`. "est." marks planning estimates to be replaced by real-validation measurements. Strategy codes (S1, S2, ...) name complete submission recipes; the routes after S1 are in [Section 8](#8-strategy-routes-after-s1), and citations [Rn] link to [`07-LITERATURE.md` Section 6](07-LITERATURE.md#6-named-references-r1-r42).

## 0. Measured so far (official metric on legal real validation; updated 2026-10-09)

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

**First leaderboard results (2026-10-06, strategy S1):** LUMPI 965614 combined 0.4728 (mAP 0.1357, R 0.8912), V2X 965633 combined 0.7665 (mAP 0.4648, R 0.9203), both rank 1. Realism transferred (V2X +0.001, LUMPI -0.014 vs held-out proxies); detection transferred at 0.82-0.89 x realval-B but only 0.52 x realval-A on LUMPI (Person 0.117, Bicycle 0.053, Truck 0.028 on the test frames). Per-class tables: `model-<track>/README.md` Section 9. **2026-10-09:** V2X S1+C1 (972563) 0.7855, mAP 0.4869, rank 1; LUMPI S1 is rank 2 since Oct 7 behind an entry with lower mAP (0.1185) but realism R 0.942, so LUMPI realism is now the most valuable LUMPI lever (Section 8.7). **2026-10-10:** S3 uploaded on both tracks: V2X 974400 combined **0.8381** (mAP 0.5483, rank 1 of 19); LUMPI scored **0.5015** by the scorer log (mAP 0.1692), above the LUMPI leader (0.4784), but the submission was still Running at the server after scoring. The S3 gains transferred at 0.8 x the realval-A gain on both tracks, while the realval-B gain over-predicted V2X (0.48 x) and under-predicted LUMPI (1.89 x). **2026-10-10/11:** S4 uploaded on both tracks: V2X 975938 combined **0.8485** (mAP 0.5605), LUMPI 975871 **0.5040** (mAP 0.1721, uploaded below its upload gate by the entrant's call): rank 1 on both tracks. Over the five uploads with a local change, the leaderboard gain had the right sign every time but was 0.25-1.74 x the realval-A gain and 0.48-1.90 x the realval-B gain; projections now use 0.6 x the mean of both (Section 8.4.1). **2026-10-11:** S5 uploaded: V2X 978945 combined **0.8730** (mAP 0.5890, rank 1); LUMPI 978931 0.5039, 0.00007 below the S4 entry (not confirmed; diagnosed in Section 8.5.1: the LUMPI test window answers the size-augmented Bicycle members with false positives no local split shows). Register: [`decisions/README.md` Section 2](decisions/README.md#2-submission-register).

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

| | Ours (2026-10-09) | Best other IEEE entry (2026-10-09) | ECCV final best (same scorer and data) | Must beat | Target | Stretch |
|---|---|---|---|---|---|---|
| V2X combined | **0.7855** (S1+C1) | 0.662 | 0.746 | 0.76 | **0.80** | 0.87 |
| LUMPI combined | 0.4728 (S1) | **0.478** (R 0.942) | 0.479 | 0.49 | **0.53** | 0.62 |

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
| S6 | Sparse Transformer Experts | after the freeze, unless a route is dropped | DSVT (or LION, SAFDNet) members | capacity and long range | 7-10 days; 100+ GPU-hours | high | [R31](07-LITERATURE.md#r31-dsvt), [R32](07-LITERATURE.md#r32-lion), [R33](07-LITERATURE.md#r33-hednet-and-safdnet), [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports) |

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

### 8.6 S6 Sparse Transformer Experts

**Hypothesis.** A sparse transformer backbone (DSVT [R31](07-LITERATURE.md#r31-dsvt); LION [R32](07-LITERATURE.md#r32-lion) or SAFDNet [R33](07-LITERATURE.md#r33-hednet-and-safdnet) as forks) adds capacity and long-range context that the CNN members lack. The only evidence on this challenge is negative (the runner-up's DSVT ensembles scored below S1 [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports)), so S6 runs only if an earlier route is dropped, or after the freeze as research.

**Steps.**
1. Install `torch_scatter` for torch 2.1.2 + CUDA 12.1 into `.venv_ut` (`pip install torch-scatter -f https://data.pyg.org/whl/torch-2.1.0+cu121.html`), add it to `requirements.txt`, check `import torch_scatter`.
2. Model `dsvt-g1v3` from mainline `cfgs/waymo_models/dsvt_pillar.yaml` (faster than `dsvt_voxel.yaml`): xyz only (the Waymo config uses 5 point features), our ranges, S2's head groups.
3. Smoke run; full run only if the smoke run predicts 12 h or less per track.
4. `tune_and_eval.sh`, scorecard, then a member of the current portfolio; joint routing and fusion decide per class.
5. Upload only before Oct 30 and only through the upload gate.

**Evaluation and gate.** As S2; the bar is the current portfolio, not S1.

**Risks.** Cost, tuning sensitivity, extra dependency; a dropped S6 costs nothing but GPU time.

**Time box.** Post-freeze research, or the slot of a dropped route.

### 8.7 Parallel and gated work

**R track: LUMPI realism** (CPU, Sat Oct 10 - Mon Oct 19; joins the current strategy when it passes). **Priority raised 2026-10-09:** LUMPI is rank 2 behind an entry with realism R 0.942 (CD 0.877, EMD 1.108, FPD 0.498) and a lower mAP (0.1185); at our mAP, about +0.015 leaderboard R regains rank 1. Hypothesis: the LUMPI frames lack the static structure of the test window (35% of the reference mass lies where the twin has no geometry [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports)); +0.022 R is worth +0.009 combined, enough to pass the ECCV LUMPI winner.
1. **R1 diagnosis:** per-term realism on proxies 1-5; a BEV mass-difference map (pooled selected frames vs fit proxies 1-3), range and height histograms; where the EMD comes from. Written into [`data-lumpi-track/README.md`](../data-lumpi-track/README.md).
2. **R2 selection objective:** `select_realism_frames.py --objective r`: the current FPD greedy search, then a refinement pass that scores candidate swaps with the full official R against the fit proxies (a few hundred evaluations). Gate: held-out R (proxies 4-5) up by at least 0.003.
3. **R3 engine G2-lite static clutter and long trucks (M9; promoted after S2 as the largest walker lever, Section 8.2.1):** trucks and trailers of 12-20 m (29% of real realval-A trucks; the synthetic trucks stop at 8.47 m, close-out D5), which also serve Truck detection after retraining; parked-vehicle rows at positions where legal Measurement4 Car labels stay stationary (label statistics, an allowed use), plus poles and vegetation primitives; ray-cast with the five G1 sensors and inserted ray-consistently; corpus `g1-v4`. Gate: held-out R >= 0.915 with FPD below 4, and no drop in detection when evaluated as realism frames only.
   **Refined 2026-10-11 by S4-S5:** walker sizes already match the real labels, so the walker part of R3 is static hard negatives only (S4: walker localization is not a detector problem; the static share of unmatched walker boxes is still 0.41-0.59); long trucks stay in R3 even if S5's object scaling helps, because stretched trucks are sparser than ray-cast ones; R3 is the next strategy after S5 and its corpus `g1-v4` retrains the kept members, two-stage included.
4. **R4 adoption (decide Mon Oct 19):** if `g1-v4` passes, either retrain the kept LUMPI members on `g1-v4` (about one day of GPUs 0-3, scheduled into the S5 slot) so frames and training share one generator (the S1 rule, `decisions/2026-09-30-s1-g1-generator.md`), or submit `g1-v4` frames with the current detectors and record the deviation in a decision record.
- **V2X realism:** background density calibration as on LUMPI (E8 in the V2X model README); low priority (R 0.920 against the ECCV winner's 0.925).

**R1-R2 results (2026-10-09).** New legal proxies `pcdet/realism-proxy-late-{1,2,3}`: 50 realval-A frames each from Measurement4 4800-6399 (closest to the excluded test window), disjoint from proxies 1-5 and from the density-prior frames. The S1 LUMPI frames score R 0.908 / 0.901 / 0.906 against them (0.906 against proxy 4), so the late frames do **not** reproduce the leaderboard's 0.891 (EMD 1.65, FPD 5.1): the hidden reference differs in content from every legal frame, not by time alone. R2 (re-selecting the 50 frames on proxies 1-3 plus late-1/2) scores R 0.901-0.902 on the held-out proxies 4, 5 and late-3, below the S1 frames: **failed, S1 frames kept**. Frame selection is near its limit on legal proxies; the gap needs generator content (R3), which S2 showed is also the main walker lever (static hard negatives, Section 8.2.1).

**Gated: self-training on unlabeled legal real frames** [R40](07-LITERATURE.md#r40-st3d) (only after a written organizer yes to question 1): pseudo-label legal unlabeled train-split frames with the frozen portfolio, keep per-class high-confidence boxes, mix 1:1 with synthetic frames, retrain the best member, evaluate on B (never on frames that were pseudo-labeled), and disclose it in the report.

### 8.8 Final phase plan (Nov 1-14)

The final phase scores the same test data with **1 submission per day, 5 in total, a hidden leaderboard, and no carry-over** of development submissions ([`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md)).
1. Before Nov 1: re-package every frozen candidate from its tag, run `check_submission.py --official`, and store the zips; confirm in [`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md) whether the last or the best final submission counts (ask the organizers if it is not stated).
2. F1 (Nov 1): the frozen best strategy per track, the exact zip confirmed on the development leaderboard.
3. F2 (Nov 3): the runner-up candidate that differs in one decision (for example routed vs fused, or with and without the R-track frames), only if its development confirmation was within 0.005 of F1.
4. F3-F5: reserve for platform failures; no new features after Gate E.
5. Record every final submission like a development one (`codabench_<id>.json`, the register in `decisions/README.md` Section 2, track model README Section 9, root README Section 9) and write the 4-8 page report (due Nov 15) from the progression tracker, the submission register and the decision records ([`decisions/README.md`](decisions/README.md)).
