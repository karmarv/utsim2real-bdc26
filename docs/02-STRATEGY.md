# 02. Strategy: how this competition is won

> Built on `01-CHALLENGE-FACTS.md`. "est." marks planning estimates to be replaced by real-validation measurements.

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

The thesis below holds: detection decides, the open points are per class, and the real train split lets us measure the target. Planning estimates marked "est." remain for the levers not yet built.

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

### 2.3 Build-up (est., both tracks)

| Step | V2X combined | LUMPI combined |
|---|---|---|
| S0: UT-trained detector, correct class map, UT frames at 50k points (+ V2X null returns) | 0.62 | 0.40 |
| S1: + scorer-exact eval, real val, per-class NMS and post-processing selected on real val | 0.70 | 0.45 |
| S2: + VRUs synthesized with real conventions (G1 insertion) | 0.75 | 0.48 |
| S3: + real-calibrated sensor model, G2 corpus, class-specific fixes (Truck/Van/Bicycle, trash cans) | 0.78 | 0.51 |
| S4: + ensemble/TTA, realism frame selection | **0.80+** | **0.53+** |

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
| 8 | Detector choice and DG augmentation selected on real val (PointPillars, CenterPoint, VoxelNeXt, DSVT) | Both | +0.02-0.04 | GPU-bound | Capacity |
| 9 | Ensembles, TTA, 3D WBF | Both | +0.01-0.03 | 2 days | 2+ good models |
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
