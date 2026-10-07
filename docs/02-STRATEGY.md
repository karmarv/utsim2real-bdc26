# 02. Strategy: how this competition is won

> Built on `01-CHALLENGE-FACTS.md`. "est." marks planning estimates to be replaced by real-validation measurements. Strategy codes (S1, S2, ...) name complete submission recipes; the routes after S1 are in [Section 8](#8-strategy-routes-after-s1), and citations [Rn] link to [`07-LITERATURE.md` Section 6](07-LITERATURE.md#6-named-references-r1-r42).

## 0. Measured so far (2026-10-02, official metric on legal real validation)

| Lever | Track | Measured effect | Where |
|---|---|---|---|
| Synthetic walkers (engine G1) | LUMPI | Person 0 -> 0.341; mAP 0.168 -> 0.253 on realval-A | `model-lumpi-track/README.md` 7.2 |
| UT Van -> challenge Van | LUMPI | Van 0.034 -> 0.122 | same |
| Per-class post-processing (size, z, NMS, re-centering, hedges) | LUMPI | 0.210 -> 0.253 for `pointpillars-g1` | same |
| Per-class routing of two runs | LUMPI | 0.253 -> 0.260 (A), 0.156 -> 0.166 (B) | same |
| Background density calibration + frame selection | LUMPI | R 0.59 -> 0.906 | `data-lumpi-track/README.md` 8.7 |
| Walkers (G1 v1 / v2 body) | V2X | pedestrian 0 -> 0.118 / 0.173 | `model-v2x-track/README.md` 7 |
| FOV mask + walkers calibrated per range on legal walkers | V2X | realism R 0.901 -> 0.916 (0.922 selected); detection: `model-v2x-track/README.md` 7 | `data-v2x-track/README.md` 8 |

**First leaderboard results (2026-10-06, strategy S1):** LUMPI 965614 combined 0.4728 (mAP 0.1357, R 0.8912), V2X 965633 combined 0.7665 (mAP 0.4648, R 0.9203), both rank 1. Realism transferred (V2X +0.001, LUMPI -0.014 vs held-out proxies); detection transferred at 0.82-0.89 x realval-B but only 0.52 x realval-A on LUMPI (Person 0.117, Bicycle 0.053, Truck 0.028 on the test frames). Per-class tables: `model-<track>/README.md` Section 9.

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

| | IEEE live best | ECCV final best (same scorer and data) | Must beat | Target | Stretch |
|---|---|---|---|---|---|
| V2X combined | 0.611 | 0.746 | 0.76 | **0.80** | 0.87 |
| LUMPI combined | 0.277 | 0.479 | 0.49 | **0.53** | 0.62 |

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

### 8.0 Overview

| Code | Name | Stage | Changes vs the previous strategy | Gap it targets | Effort (est.) | Risk | Research |
|---|---|---|---|---|---|---|---|
| **S1** | Calibrated Twin, Routed Pillars | **submitted** (tag 0.1; 965614, 965633) | engine G1 data, PointPillars x 2-4 runs, per-class post-processing and routing | missing walkers, actor scale, density | done | done | [R1](07-LITERATURE.md#r1-urbantwin-papers), [R5](07-LITERATURE.md#r5-pointpillars), [R7](07-LITERATURE.md#r7-statistical-normalization), [R9](07-LITERATURE.md#r9-lidar-aug), [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports) |
| **S2** | Center-Routed Small Objects | **next** | CenterPoint specialists for small classes, routed with the S1 pillars; routes chosen on realval-A and B jointly | LUMPI Person, Bicycle, Motorcycle; V2X pedestrian; near-threshold localization | 5-7 days; about 30 GPU-hours | low | [R22](07-LITERATURE.md#r22-centerpoint), [R24](07-LITERATURE.md#r24-inscope), [R41](07-LITERATURE.md#r41-pillarnet), [R42](07-LITERATURE.md#r42-mmdetection3d-model-comparison-secondary-source) |
| S3 | Fused Portfolio with TTA | planned | per-class box fusion of the S2 members instead of hard routing; flip, yaw and height TTA | duplicates and variance across runs; V2X height | 3-4 days; few GPU-hours | low | [R23](07-LITERATURE.md#r23-weighted-boxes-fusion), [R37](07-LITERATURE.md#r37-ms3d-kde-box-fusion), [R38](07-LITERATURE.md#r38-horizonlidar3d), [R39](07-LITERATURE.md#r39-robosense-2025-report), [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports) |
| S4 | Two-Stage Refinement | planned | a PV-RCNN++ or Voxel R-CNN member that re-fits boxes on raw points | V2X height (BEV 0.570 vs 3D 0.465); LUMPI Truck and Car; IoU 0.7 | 5-7 days; about 50 GPU-hours | medium | [R29](07-LITERATURE.md#r29-pv-rcnn), [R30](07-LITERATURE.md#r30-voxel-r-cnn), [R25](07-LITERATURE.md#r25-robo3d), [R24](07-LITERATURE.md#r24-inscope) |
| S5 | Geometry-Invariant Inputs | planned | GBlobs local-geometry features plus beam and object-scale augmentation on the best member | the realval-to-test transfer gap itself | 5-7 days; about 30 GPU-hours | medium | [R27](07-LITERATURE.md#r27-gblobs), [R28](07-LITERATURE.md#r28-gblobs-for-sensor-placement), [R26](07-LITERATURE.md#r26-lidar-domain-generalization-study), [R36](07-LITERATURE.md#r36-dts-random-beam-re-sampling), [R40](07-LITERATURE.md#r40-st3d) |
| S6 | Sparse Transformer Experts | only if time remains | DSVT (or LION, SAFDNet) members | capacity and long range | 7-10 days; 80+ GPU-hours | high | [R31](07-LITERATURE.md#r31-dsvt), [R32](07-LITERATURE.md#r32-lion), [R33](07-LITERATURE.md#r33-hednet-and-safdnet), [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports) |

GPU-hours are on the A6000s, from the measured PointPillars runs (LUMPI about 8 GPU-hours, V2X about 4 per 40-epoch run) times the usual cost ratio of each family; they are estimates until the first smoke run of each route.

**Common acceptance gate (all routes).** A change to a class is kept only if its realval-B AP rises by at least 0.01 and its realval-A AP does not drop; a strategy is uploaded only if its combined estimate with the realval-B mAP beats the previous strategy's (S1: LUMPI 0.505, V2X 0.814). One development submission per strategy and track, recorded in the track's model README Section 9 and the root README Section 9. Rationale: the S1 leaderboard showed realval-B predicting the test mAP (0.82-0.89 x) far better than realval-A (0.52 x on LUMPI).

**Calendar.** S2 by Tue Oct 13; S3 by Fri Oct 16; S4 by Wed Oct 21; S5 by Sat Oct 24; feature freeze Sun Oct 25 (Gate E, Section 4). S6 cannot finish before the freeze on top of S2-S5, so it is a post-freeze research item unless an earlier route is dropped. Final phase (Nov 1-14): only frozen strategies.

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

**Result:** LUMPI 0.4728 (rank 1; 0.007 below the ECCV winner, from realism), V2X 0.7665 (rank 1; above the ECCV winner). **Lessons for S2+:** realism transfers; LUMPI small classes and Truck, and V2X truck, do not; V2X loses 0.105 mAP to height; realval-A alone is an unreliable selector.

### 8.2 S2 Center-Routed Small Objects

**Idea.** Add CenterPoint [R22](07-LITERATURE.md#r22-centerpoint) members (sparse 3D voxel backbone [R21](07-LITERATURE.md#r21-second), anchor-free center heat-map heads) and route small classes to them, keeping PointPillars for vehicles. Center heads regress the box from the object center instead of matching preset anchors, which suits pedestrian-sized boxes where a 10 cm offset costs most of the IoU.

| | Track 1 LUMPI | Track 2 V2X-Real |
|---|---|---|
| Members to add | `centerpoint-g1v3` on `pcdet/g1-v3` (and `centerpoint-g1` on `g1-v2` if the first one helps) | `centerpoint-g1v3` on `pcdet/g1-v3` |
| Voxels | 0.1 x 0.1 x 0.25 m over `[-40, -40, -5, 40, 40, 5]` (800 x 800 x 40) | 0.1 x 0.1 x 0.25 m over `[-40, -40, -8, 40, 40, 2]` (the slope needs the full z range) |
| Head groups | [Person], [Bicycle, Motorcycle], [Car, Van, Unknown], [Truck, Bus] | [pedestrian], [vehicle], [truck] |
| Classes it competes for | Person, Bicycle, Motorcycle (and any class where it wins on A and B) | pedestrian (and any class where it wins) |
| Fallback | PillarNet or CenterPoint-pillar [R41](07-LITERATURE.md#r41-pillarnet): center head on the pillar encoding, if voxel features prove too density-sensitive | same |

**Pros.** Best published evidence for small roadside objects: InScope cyclist AP 58.46 to 74.74 and pedestrian 23.8 to 49.6 vs pillars [R24](07-LITERATURE.md#r24-inscope); nuScenes pedestrian 71.8 to 84.7 [R42](07-LITERATURE.md#r42-mmdetection3d-model-comparison-secondary-source). In mainline OpenPCDet with the installed spconv [R6](07-LITERATURE.md#r6-openpcdet); no anchors, so a size-convention mismatch cannot block matching; fits the existing tuner and router unchanged.

**Cons.** It regresses synthetic box sizes directly, so size calibration in post-processing is still needed; heat-map peaks weaken on sparse distant walkers; about 2-3x slower to train than pillars; the ECCV winner reported CenterPoint no better than pillars on this data [R19](07-LITERATURE.md#r19-eccv-2026-winner-reports) (with their data, not ours); it does not address LUMPI Truck.

**Steps.**
1. `python common/tools/new_model.py <track> centerpoint-g1v3 --from pointpillars-g1v3`; write `train/pcdet_model.yaml` from OpenPCDet's `cfgs/waymo_models/centerpoint.yaml` pattern (VoxelBackBone8x, HeightCompression, BaseBEVBackbone, CenterHead with the head groups above); keep the dataset config (same augmentation, 50k points).
2. Smoke run: 2 epochs on 1 GPU; check that `BDCDataset` labels, the center head targets and `pcdet_predict.py --raw` work.
3. Full run: 40 epochs on 4 GPUs (LUMPI on GPUs 0-3, V2X on 4-7 in parallel).
4. `tune_and_eval.sh` (unchanged tuner) for realval-A/B; registry rows.
5. Extend `route_predictions.py select` with a joint rule (rank members by the mean of realval-A and realval-B AP, require the common gate) and build `routed-g2` with the S1 members plus the CenterPoint member(s).
6. `make_submission.sh`, `check_submission.py --official`, one upload per track, `--record`; list under S2 in the root README Section 9.

**Gate.** Per-class gate as in 8.0; success means LUMPI Person or Bicycle and V2X pedestrian rise on realval-B by 0.02 or more.

### 8.3 S3 Fused Portfolio with TTA

**Idea.** Replace hard per-class routing by per-class box fusion of the S2 members (WBF [R23](07-LITERATURE.md#r23-weighted-boxes-fusion) or KDE box fusion [R37](07-LITERATURE.md#r37-ms3d-kde-box-fusion); or the runner-up's primary/auxiliary score fusion `0.6 s_p + 0.4 s_a` [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports)), with test-time augmentation per member: x/y flips, small yaw, and per-class height offsets [R39](07-LITERATURE.md#r39-robosense-2025-report).

**Pros.** Proven, cheap gains (WBF +2.2 and TTA +2.6 in a Waymo winner [R38](07-LITERATURE.md#r38-horizonlidar3d)); reuses trained models, no new training; height TTA targets the V2X z loss directly; reduces the run-to-run variance that routing exploits only partly.

**Cons.** Needs members of different architectures to pay (hence after S2); bad fusion creates duplicates, which are false positives; adds knobs tuned on validation, the over-fitting path seen on LUMPI.

**Steps.** `pcdet_predict.py --tta` (flip and yaw variants, boxes mapped back); a `common/bdc26/detect/fusion.py` (rotated 3D WBF, KDE fusion, score fusion); `route_predictions.py fuse`; tune at most 2 knobs per class (fusion IoU, member weights) on A and B together; then the usual packaging and one upload.

**Gate.** As 8.0; additionally the realval-B gain must hold for at least 2 of 3 V2X classes and 4 of 7 LUMPI classes.

### 8.4 S4 Two-Stage Refinement

**Idea.** Add a two-stage member, PV-RCNN++ [R29](07-LITERATURE.md#r29-pv-rcnn) (center-based proposals plus point-level RoI refinement) or the lighter Voxel R-CNN [R30](07-LITERATURE.md#r30-voxel-r-cnn), which re-fits each box on the raw points inside it.

**Pros.** Directly targets the V2X height gap and the low IoU-0.7 mAP; PV-RCNN++ is the most robust family under corruptions (mCE 91.6 vs 127.5 for PointPillars [R25](07-LITERATURE.md#r25-robo3d)) and tops InScope mAP40 [R24](07-LITERATURE.md#r24-inscope); builds on the S2 center proposals.

**Cons.** 3-4x training cost; many hyperparameters; the refinement may re-impose synthetic box conventions that the post-processing corrects, so it must be judged on realval-B; some configs (dynamic voxels) need `torch_scatter`.

**Steps.** 0: diagnose first: compute BEV@0.5 vs 3D@0.5 on realval-A/B for S1; if realval also shows the V2X height gap, the model is at fault (S4 helps), otherwise the test convention differs (z calibration on B, or the V2X ground-plane experiment [R39](07-LITERATURE.md#r39-robosense-2025-report)). Then new model `pvrcnnpp-g1v3` from `cfgs/waymo_models/pv_rcnn_plusplus.yaml`, smoke, 40 epochs, tune, add to the S3 fusion.

**Gate.** As 8.0; success means the BEV-3D gap on V2X realval-B shrinks by half.

### 8.5 S5 Geometry-Invariant Inputs

**Idea.** Feed the best member GBlobs features [R27](07-LITERATURE.md#r27-gblobs) (local covariance of each point's neighbourhood, parameter-free) in place of absolute xyz, plus source-only augmentation: random beam re-sampling [R36](07-LITERATURE.md#r36-dts-random-beam-re-sampling) (per sensor on LUMPI) and random object scaling [R40](07-LITERATURE.md#r40-st3d).

**Pros.** The only route aimed at the transfer gap itself; +21 mAP Waymo to KITTI over the previous DG state of the art and the RoboSense 2025 sensor-placement winner [R28](07-LITERATURE.md#r28-gblobs-for-sensor-placement); local point features generalize better than absolute coordinates [R26](07-LITERATURE.md#r26-lidar-domain-generalization-study); BSD-3 code on OpenPCDet.

**Cons.** Gains were measured real-to-real, not synthetic-to-real; the twin is the same intersection as the test, so absolute position is partly legitimate signal and in-domain AP may drop; adds a k-nearest-neighbour step on 50k points per frame.

**Steps.** Port the GBlobs feature encoder into a VFE option (keep the licence notice); retrain the S2 winner with it and with the augmentations, one change at a time (3 runs per track); tune and gate.

**Gate.** As 8.0, judged mostly on realval-B and on the realval-A to realval-B ratio (a smaller drop from A to B is the expected signature).

### 8.6 S6 Sparse Transformer Experts

**Idea.** DSVT [R31](07-LITERATURE.md#r31-dsvt) members (mainline OpenPCDet), or LION [R32](07-LITERATURE.md#r32-lion) or SAFDNet [R33](07-LITERATURE.md#r33-hednet-and-safdnet) forks, as additional fused members.

**Pros.** State of the art on Waymo and nuScenes; the runner-up's choice on this challenge.

**Cons.** The only evidence on this challenge is negative: the runner-up's DSVT ensembles scored below S1 on both tracks [R20](07-LITERATURE.md#r20-eccv-2026-runner-up-reports); needs `torch_scatter` (DSVT) or a Mamba build (LION); 4-6x slower and sensitive to tuning; cannot finish before the Oct 25 freeze on top of S2-S5.

**Steps.** Only if an earlier route is dropped: install `torch_scatter` for torch 2.1.2+cu121, DSVT-voxel config, smoke, train, tune, fuse.

### 8.7 Outside the detector routes

- **LUMPI realism (engine G2, M9):** static clutter and parked-car rows the twin lacks; the cheapest combined-score gain (+0.022 R = +0.009 combined, enough to pass the ECCV LUMPI winner); CPU-bound, so it runs in parallel with S2-S5 and joins whichever strategy is current.
- **V2X ground-plane canonicalization:** part of the S4 diagnosis (step 0).
- **Self-training on unlabeled legal real frames** [R40](07-LITERATURE.md#r40-st3d): probably the strongest sim-to-real lever; off until the organizers answer question 1 (`01` Section 10).
