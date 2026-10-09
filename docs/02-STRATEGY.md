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

**First leaderboard results (2026-10-06, strategy S1):** LUMPI 965614 combined 0.4728 (mAP 0.1357, R 0.8912), V2X 965633 combined 0.7665 (mAP 0.4648, R 0.9203), both rank 1. Realism transferred (V2X +0.001, LUMPI -0.014 vs held-out proxies); detection transferred at 0.82-0.89 x realval-B but only 0.52 x realval-A on LUMPI (Person 0.117, Bicycle 0.053, Truck 0.028 on the test frames). Per-class tables: `model-<track>/README.md` Section 9. **2026-10-09:** V2X S1+C1 (972563) 0.7855, mAP 0.4869, rank 1; LUMPI S1 is rank 2 since Oct 7 behind an entry with lower mAP (0.1185) but realism R 0.942, so LUMPI realism is now the most valuable LUMPI lever (Section 8.7). Register: [`decisions/README.md` Section 2](decisions/README.md#2-submission-register).

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
| **S2** | Center-Routed Small Objects | **next** | CenterPoint specialists for small classes, routed with the S1 pillars; routes chosen on realval-A and B jointly | LUMPI Person, Bicycle, Motorcycle; V2X pedestrian, including its height loss | 4 days; about 32 GPU-hours | low | [R22](07-LITERATURE.md#r22-centerpoint), [R24](07-LITERATURE.md#r24-inscope), [R41](07-LITERATURE.md#r41-pillarnet), [R42](07-LITERATURE.md#r42-mmdetection3d-model-comparison-secondary-source) |
| S3 | Fused Portfolio with TTA | planned | test-time augmentation as routable member variants; per-class box fusion of members | run-to-run variance; V2X height | 3 days; about 4 GPU-hours | low | [R23](07-LITERATURE.md#r23-weighted-boxes-fusion), [R37](07-LITERATURE.md#r37-ms3d-kde-box-fusion), [R38](07-LITERATURE.md#r38-horizonlidar3d), [R39](07-LITERATURE.md#r39-robosense-2025-report), [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports) |
| S4 | Two-Stage Refinement | planned | a PV-RCNN++ (or Voxel R-CNN) member that re-fits boxes on raw points | V2X height (BEV-3D gap 0.146 on realval-B); IoU 0.7; LUMPI Truck and Car | 5 days; about 64 GPU-hours | medium | [R29](07-LITERATURE.md#r29-pv-rcnn), [R30](07-LITERATURE.md#r30-voxel-r-cnn), [R25](07-LITERATURE.md#r25-robo3d), [R24](07-LITERATURE.md#r24-inscope) |
| S5 | Geometry-Invariant Inputs | planned | GBlobs voxel features plus dropout and object-scale augmentation on the best voxel member | the realval-to-test transfer gap itself | 5 days; about 96 GPU-hours (3 runs per track) | medium | [R27](07-LITERATURE.md#r27-gblobs), [R28](07-LITERATURE.md#r28-gblobs-for-sensor-placement), [R26](07-LITERATURE.md#r26-lidar-domain-generalization-study), [R36](07-LITERATURE.md#r36-dts-random-beam-re-sampling), [R40](07-LITERATURE.md#r40-st3d) |
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

### 8.3 S3 Fused Portfolio with TTA

**Hypothesis.** Averaging several views and several members reduces localization noise and run-to-run variance: test-time augmentation (TTA) and per-class box fusion add AP without new training [R38](07-LITERATURE.md#r38-horizonlidar3d), and height-shift TTA [R39](07-LITERATURE.md#r39-robosense-2025-report) reduces the V2X height loss. Targets: per-class B AP on every class; V2X BEV-3D gap; 3D@0.7.

**Prerequisites.** S2 decided (its members exist, or S1's if S2 failed); T1-T2.

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

### 8.4 S4 Two-Stage Refinement

**Hypothesis.** A second stage that pools the raw points inside each proposal corrects box height, z and size [R29](07-LITERATURE.md#r29-pv-rcnn), [R30](07-LITERATURE.md#r30-voxel-r-cnn), the remaining V2X height loss after S2-S3, and improves 3D@0.7. PV-RCNN++ is also the most corruption-robust family [R25](07-LITERATURE.md#r25-robo3d). Targets: V2X BEV-3D gap on B (halve it), 3D@0.7, LUMPI Truck and Car B AP.

**Prerequisites.** D2 (decides between refinement and a ground-height model); S2's CenterPoint config (the PV-RCNN++ proposal head is a `CenterHead`).

**Steps.**
0. Read D2. If V2X z errors follow the slope or position, first test a fixed ground-height map of the static sensor fitted on legal unlabeled frames (sensor calibration, an allowed use; it is not fitted on test frames) as a z-offset input to post-processing, one cheap experiment on the S3 portfolio; then continue with steps 1-6 for the residual.
1. Model `pvrcnnpp-g1v3` on both tracks from mainline `cfgs/waymo_models/pv_rcnn_plusplus.yaml`: S2's voxel grid and head groups, xyz only, 2,048 keypoints (50,000-point frames), `VectorPoolAggregation` modules as in the config, `PVRCNNHead` refinement, batch 2 per GPU.
2. Alternative if PV-RCNN++ is too slow (smoke run over 3 s per iteration): `voxelrcnn-g1v3` from `voxel_rcnn_with_centerhead_dyn_voxel.yaml` with `MeanVFE` and `VoxelBackBone8x` in place of the dynamic voxel encoder (avoids `torch_scatter`).
3. Smoke run (2 epochs), then 40 epochs on 4 GPUs per track (est. 10 h LUMPI, 6 h V2X).
4. `tune_and_eval.sh`, scorecard vs the S3 portfolio's best member per class.
5. Add as a member (plain and TTA variant) to `routed-g4` (from `routed-g3`); joint routing and fusion decide per class.
6. Scorecard vs S3, upload gate, upload, record.

**Evaluation.** V2X BEV-3D gap on B (target: from 0.146 to 0.07 or less, measured after S2-S3), 3D@0.7 on B, LUMPI Truck and Car B AP, check time (two-stage outputs are fewer, cleaner boxes, so the box count should fall).

**Gate.** Class gate; strategy success when the V2X BEV-3D gap shrinks by half or LUMPI Truck passes the class gate, and the upload gate holds.

**Deliverables.** `pvrcnnpp-g1v3` (or `voxelrcnn-g1v3`), `routed-g4`, scorecards, tracker row, upload.

**Risks and fallbacks.** Refinement may relearn synthetic box conventions that the post-processing corrects (judge on B, not on synthetic val); training cost; if the member never wins a class, S4 contributes only the D2 ground-height experiment.

**Time box.** Smoke Mon Oct 12, training Tue Oct 13 - Thu Oct 15 (in parallel with S3 coding), tuning and upload Sat Oct 17 - Mon Oct 19; about 64 GPU-hours.

### 8.5 S5 Geometry-Invariant Inputs

**Hypothesis.** Part of the realval-to-test gap comes from the detector relying on absolute point positions and the twin's exact point patterns. GBlobs [R27](07-LITERATURE.md#r27-gblobs) replaces the per-voxel mean xyz with the voxel's point covariance (9 values) and the mean's offset from the voxel centre (3 values), a parameter-free drop-in for `MeanVFE` (the authors' `GBlobsVFE`, BSD-3, also used with CenterPoint in their code [R28](07-LITERATURE.md#r28-gblobs-for-sensor-placement)); source-only dropout and object scaling [R36](07-LITERATURE.md#r36-dts-random-beam-re-sampling), [R40](07-LITERATURE.md#r40-st3d) widen the training distribution. Signature of success: B-mAP and the B/A ratio rise together.

**Prerequisites.** The best voxel member from S2 or S4. The authors also provide a PointPillars config, but the covariance carries most information in small voxels, so the voxel member is the first target.

**Steps.**
1. `common/bdc26/detect/gblobs_vfe.py`: the GBlobs encoder with its BSD-3 notice, registered into OpenPCDet's VFE registry by `pcdet_train.py` and `pcdet_predict.py` at start-up (as `BDCDataset` is), so `third_party/OpenPCDet` stays unmodified. Unit test: covariance and offsets of a toy voxel; output width 12.
2. Model `centerpoint-gblobs-g1v3` (from the S2 winner): VFE `GBlobsVFE` with relative distance on, 10 points per voxel, same grid (0.25 m z keeps the 256-feature BEV; the authors use 0.2 m).
3. Run a: GBlobs only. Run b: a + `random_world_frustum_dropout` and `random_local_frustum_dropout` (OpenPCDet augmentors) plus a range-dependent point dropout (frames carry xyz only, so per-sensor beam dropout would need a generator change). Run c: b + `random_local_scaling` (random object scaling). One change per run, both tracks, the same seed.
4. `tune_and_eval.sh` and scorecard for each run against the parent member; compare A, B, late-A and the B/A ratio.
5. The best run joins `routed-g5` (from the S4 portfolio) as a member, plain and TTA variant; joint routing and fusion decide per class.
6. Scorecard vs S4, upload gate, upload, record.

**Evaluation.** B-mAP, B/A ratio and late-A for each run; per-class B AP; V2X pedestrian and LUMPI Person (the most convention-sensitive classes).

**Gate.** Class gate; strategy success when the best run raises B-mAP and the B/A ratio over its parent and the upload gate holds.

**Deliverables.** GBlobs encoder with tests, 3 runs per track, `routed-g5`, scorecards, tracker row, upload.

**Risks and fallbacks.** Gains were measured real-to-real; in-domain AP may drop because the twin is the same intersection as the test (absolute position is partly legitimate signal): run a vs its parent shows this directly; sparse voxels with 1-2 points give degenerate covariances (expected to hurt far objects: check with the T4 breakdown); if no run passes, S5 ends without a member and the S4 portfolio stays.

**Time box.** Port Sat Oct 17 - Mon Oct 19, runs Tue Oct 20 - Wed Oct 21, tuning and upload Thu Oct 22 - Fri Oct 23; about 96 GPU-hours.

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
3. **R3 engine G2-lite static clutter and long trucks (M9):** trucks and trailers of 12-20 m (29% of real realval-A trucks; the synthetic trucks stop at 8.47 m, close-out D5), which also serve Truck detection after retraining; parked-vehicle rows at positions where legal Measurement4 Car labels stay stationary (label statistics, an allowed use), plus poles and vegetation primitives; ray-cast with the five G1 sensors and inserted ray-consistently; corpus `g1-v4`. Gate: held-out R >= 0.915 with FPD below 4, and no drop in detection when evaluated as realism frames only.
4. **R4 adoption (decide Mon Oct 19):** if `g1-v4` passes, either retrain the kept LUMPI members on `g1-v4` (about one day of GPUs 0-3, scheduled into the S5 slot) so frames and training share one generator (the S1 rule, `decisions/2026-09-30-s1-g1-generator.md`), or submit `g1-v4` frames with the current detectors and record the deviation in a decision record.
- **V2X realism:** background density calibration as on LUMPI (E8 in the V2X model README); low priority (R 0.920 against the ECCV winner's 0.925).

**Gated: self-training on unlabeled legal real frames** [R40](07-LITERATURE.md#r40-st3d) (only after a written organizer yes to question 1): pseudo-label legal unlabeled train-split frames with the frozen portfolio, keep per-class high-confidence boxes, mix 1:1 with synthetic frames, retrain the best member, evaluate on B (never on frames that were pseudo-labeled), and disclose it in the report.

### 8.8 Final phase plan (Nov 1-14)

The final phase scores the same test data with **1 submission per day, 5 in total, a hidden leaderboard, and no carry-over** of development submissions ([`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md)).
1. Before Nov 1: re-package every frozen candidate from its tag, run `check_submission.py --official`, and store the zips; confirm in [`01-CHALLENGE-FACTS.md`](01-CHALLENGE-FACTS.md) whether the last or the best final submission counts (ask the organizers if it is not stated).
2. F1 (Nov 1): the frozen best strategy per track, the exact zip confirmed on the development leaderboard.
3. F2 (Nov 3): the runner-up candidate that differs in one decision (for example routed vs fused, or with and without the R-track frames), only if its development confirmation was within 0.005 of F1.
4. F3-F5: reserve for platform failures; no new features after Gate E.
5. Record every final submission like a development one (`codabench_<id>.json`, the register in `decisions/README.md` Section 2, track model README Section 9, root README Section 9) and write the 4-8 page report (due Nov 15) from the progression tracker, the submission register and the decision records ([`decisions/README.md`](decisions/README.md)).
