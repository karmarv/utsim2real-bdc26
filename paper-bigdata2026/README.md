# paper-bigdata2026: the challenge report and the BigData Cup paper

> Scope: the system that produced the challenge entries, strategies S1-S8 (the S8 entries of both tracks) and the final-phase submissions, as recorded in [`docs/01`](../docs/01-CHALLENGE-FACTS.md) to [`docs/07`](../docs/07-LITERATURE.md), the [decision records](../docs/decisions/README.md) and the track READMEs. Every number in the paper comes from a record in this repository; nothing is re-run for the paper. Sections 3-4 hold the report material on the final development-phase entries: the approach in the challenge's four steps, and the score breakdown of both tracks.

## 1. Deliverables and dates

| Deliverable | Due | Length and format | Who | Channel |
|---|---|---|---|---|
| Challenge report | **Nov 15, 2026** | 4-8 pages, IEEE two-column | every team | ASK ([`docs/01` Section 10](../docs/01-CHALLENGE-FACTS.md#10-questions-for-the-organizers-email-muhammadshahbazucfedu-on-day-1), question 5) |
| Cup paper (paper track, CyberChair subarea SC04) | camera-ready **Nov 20, 2026** | up to 10 pages including references, IEEE two-column | top 3 per track (invited) | CyberChair |
| Code release for verification | with the paper | a public repository with the detector code and the weights of the final entries | top 3 per track | GitHub (Section 8) |

The final phase closes Sat Nov 14, 16:00 PST, so the report's final-phase numbers arrive less than a day before it is due: draft everything else by **Nov 1**, when the system is frozen at the S7 entries (F1 = the S7.6 zips; their weights are the assets of release 7.0). Winners are announced Nov 25; IEEE BigData 2026 is Dec 14-17 in Phoenix.

**Questions for the organizers** (send them with question 5 of `docs/01` Section 10): the submission channel and template for the Nov 15 report; whether the report is archival (published in the proceedings) or only a requirement for the prize; whether the Nov 20 camera-ready replaces it or is a separate paper.

## 2. Contributions (what the paper claims)

1. **A rule-compliant synthetic-only pipeline** that ranks first on both tracks (development phase: LUMPI 0.5239, S8, rank 1 of 22; V2X 0.9022, S8, rank 1 of 25; final phase: to add on Nov 15). The real data enters only as statistics for the generator and as labelled validation; no detector sees a real frame in training.
2. **Generator side:** completing the organizers' twins with what they miss (walkers and riders ray-cast with the real sensors, real-size actors, static clutter, calibrated background density and field of view), and realism-frame selection against a legal real proxy. Leaderboard realism from the first upload to S7 (unchanged since R5 on V2X and R3 on LUMPI): LUMPI 0.891 -> 0.932, V2X 0.920 -> 0.933 (the organizers' raw LUMPI frames score about 0.60 on our held-out proxy; `data-lumpi-track/README.md` Section 8).
3. **Detector side:** a routed per-class portfolio built from four trained architectures (PointPillars, CenterPoint, Voxel R-CNN, PV-RCNN++; the final entries route three, and CenterPoint's head remains the first stage of the two-stage members) with test-time augmentation, cross-architecture box fusion, class-wise object scaling, seed and generator-draw bags, a ranking rule matched to the real annotators' visibility cut (V2X) and per-class post-processing. Measured on the leaderboard: detection +0.126 (V2X) and +0.034 (LUMPI) of combined score since S1.
4. **Validation practice under a 100-frame hidden test:** two disjoint real validation splits (realval-A and realval-B), pre-registered gates and the pooled rule, and bit-exact reproduction of both entries from the released weights.

## 3. The approach in the challenge's four steps

The challenge website describes the protocol in four steps: get the data, synthesize, train sim-only, submit. This section maps the system behind the final development-phase entries onto those steps (material for paper Sections 3-6). Both entries are S8 (2026-10-30): the S7.6 system plus 12-view TTA fusions of the walker class and, on LUMPI, the non-negative completion; rank 1 on both, and F1 of the final phase:
- Track 1, LUMPI: [`routed-g11b`](../model-lumpi-track/routed-g11b/model.yaml), CodaBench 1022250, combined 0.5239, 15 checkpoints (the S7.6 ones; S7.6 was [`routed-g10`](../model-lumpi-track/routed-g10/model.yaml), 1014495, 0.5228).
- Track 2, V2X-Real: [`routed-g13`](../model-v2x-track/routed-g13/model.yaml), CodaBench 1022246, combined 0.9022, 10 checkpoints (the S7.6 ones; S7.6 was [`routed-g12`](../model-v2x-track/routed-g12/model.yaml), 1014682, 0.8982, identical to 1001919).

The checkpoints of both are the assets of release 8.0 ([`releases/8.0/weights.json`](../releases/8.0/weights.json)), byte-identical to release 7.0: S8 adds test-time views and post-processing only.

### 3.1 Get the data

| Source | Content | Use |
|---|---|---|
| UT twins (the organizers' CARLA twins, CC0) | UT-LUMPI and UT-V2X-Real-IC, 10,000 frames each | the raw material of every training frame and every submitted frame |
| Starting kit | 50 real test frames per track (point clouds, no labels), the scorer `local_eval.py`, `config.json` | inference and format checks only; no statistics |
| Real datasets (licensed) | LUMPI (CC BY-NC 3.0); V2X-Real infrastructure lidar (UCLA Academic) | validation, sensor measurement, label statistics for the generator; never a training input or label |

- **Guard.** Every reader of real data goes through `bdc26.guard.ForbiddenGuard`, which logs each read with its purpose in `access_log.csv`.
  - LUMPI: the forbidden frames are Measurement4 006497-008109. The guard blocks the window 6400-8199, and labels are filtered while they download (75,761 blocked rows never reached the disk).
  - V2X: the challenge IDs (`<scenario index>_<frame>`) do not name scenes. `resolve_test_ids.py` recovered 26 indices by exact point matching and bounded the other 6 by the sorted order of the indices; the organizers confirmed the mapping on 2026-10-14. The guard blocks every candidate scene and 20 frames on either side of each forbidden frame.
- **Splits** built from the legal frames, never trained on:
  - realval-A chooses: LUMPI 1,280 Measurement4 frames (0-6399, every 5th), the recording of the test frames; V2X 688 frames.
  - realval-B checks: LUMPI 867 frames of Measurements 5-6 (another session); V2X 298 frames of other scenes (split by scene name).
  - five realism proxies of 50 frames each: 1-3 to fit, 4-5 held out for honest estimates.

Sources: [`data-lumpi-track/README.md`](../data-lumpi-track/README.md) Sections 7-8, [`data-v2x-track/README.md`](../data-v2x-track/README.md) Sections 6-7, [`docs/01`](../docs/01-CHALLENGE-FACTS.md#3-rules) Section 3.

### 3.2 Synthesize

Defects of the twins, measured on synthetic data and legal real statistics:

| Defect | Consequence |
|---|---|
| UT-LUMPI actors are 0.78x real size | a perfectly placed box reaches at most 0.78^3 = 0.47 IoU, below the 0.5 threshold |
| no Person in UT-LUMPI; no walking pedestrian in UT-V2X | Person is 1/7 of the LUMPI metric; pedestrians are 62% of the V2X test objects |
| UT-V2X emulates a denser, wider sensor (69k against 35k valid points; elevations -56..+25 against +16.1..-16.8 deg) | wrong density and field of view |
| raw UT-LUMPI frames score R 0.59 on a held-out proxy (FPD 61) | realism is 40% of the score |
| UT trucks are too short (V2X 5.2 m against 8.2 m real); UT cars and two-wheelers are 0.25-0.52x as dense as real ones in the same place | sizes and densities that the real boxes do not have |

The generator (`prepare_g1.py`) adds, in this order:
1. **Base fixes:** actors scaled by 1/0.78 (LUMPI); resampling to the real density (50,000 points LUMPI, 35,000 valid points V2X); the measured OS1-64 field-of-view mask (V2X).
2. **Engine G1 walkers:** articulated bodies of 16-18 ellipsoids (gait, clothing, bags), ray-cast analytically with each real sensor's measured beam table (the five Measurement4 lidars; the OS1-64), with ray-consistent occlusion, 2% ray drop and range noise. Each walker copies the position, heading, box size and ground height of a legal real label row, jittered (LUMPI: 0.4 m, 0.2 rad, +/-3% size). V2X walker points by range: 52 / 40 / 18 / 7 against 46 / 36 / 19 / 7 real (0-10 / 10-20 / 20-30 / 30-45 m).
3. **Engine G2-lite (R3):** Car, Van, Truck and Bus re-cast with Open3D at real size and density (LUMPI cars 0.44x -> 0.83x the real density, two-wheelers 0.90-1.04x); real-size trucks and buses; two-wheelers with riders; Poisson(30) unlabeled static objects per frame (poles, trees, bollards, bins) as hard negatives; per-class ray dropout.
4. **Background density prior:** the real / synthetic density ratio on 8 x 8 x 2.5 m cells, fitted on legal frames, sets the keep probability of background points; object points keep their rate.
5. **V2X null returns:** the submitted frames carry 31% (0,0,0) points, like the test frames.
6. **Fresh draws** of the same recipe (generator seeds 2234 and 3234) for the S7 seed-and-draw bags.

Corpora in the final entries:
- LUMPI: members trained on `g1-v2`, `g1-v3`, `g1-v4` and the draws `g1-v4d2` and `g1-v4d3`; realism frames from `g1-v4`. Realism on held-out proxies: raw UT 0.59 -> calibrated density 0.88 -> frame selection 0.90 -> G2-lite 0.934.
- V2X: members trained on `g1-v3`, `g1-v4` and `g1-v5` (G2-lite with the density prior); realism frames from `g1-v5`.

Sources: data READMEs Sections 8-10 (LUMPI 8.4-8.7b).

### 3.3 Train sim-only

**Training.**
- OpenPCDet (233f849), from scratch (no pretraining): 40 epochs, adam one-cycle, 4 GPUs.
- Augmentation: ground-truth sampling, flips, rotation, global scaling, and class-wise random object scaling (ROS) capped at the real size ranges.
- Four architectures were trained (PointPillars, CenterPoint, Voxel R-CNN, PV-RCNN++). The final entries route three; CenterPoint's head remains the first stage of the two-stage members.
- Strong configurations were trained with several seeds (666-3666) and on the fresh draws, then merged into bags by weighted box fusion: seeds of one configuration differ by up to 0.17 AP per class.
- Never used: real frames as input, real labels, BN statistics of real frames, pseudo-labels, fine-tuning.

**Inference-time layer, chosen on real validation** (hyperparameter selection under the Rules):
- 8-view test-time augmentation (four flips, yaw, height).
- Per-class post-processing: score floor, rotated NMS IoU, re-centering on in-box points, size scale, z offset; tuned on realval-A, guarded by realval-B.
- Per-class routing and fusion of up to three members, then per-class score floors that bound the server's scoring time.
- V2X only: walker tail copies (4 copies 0.15 m away, scored below every original box, so they can only add matches) and the S7 visibility rule (a box with fewer points than the real annotators' cut, pedestrian 6 and vehicle 5, ranks last).
- Gates:
  - the class gate: +0.01 on B, paired-bootstrap P(gain) >= 0.9, and a gain on the pooled A+B frames;
  - the upload gate: a projected leaderboard gain of at least +0.003. Both S7.6 packages projected +0.0014 and were uploaded by the entrant's decision.

LUMPI portfolio (`routed-g10`; TTA unless marked plain):

| Class | Members | Fusion BEV IoU |
|---|---|---|
| Person | `pointpillars-g1v4` + `voxelrcnn-ros-g1v4-s2` | 0.5 |
| Car | `pvrcnnpp-ros-g1v3` + `bag-pvrcnnpp-ros-g1v4x` (6 members: 4 seeds, 2 draws) | 0.7 |
| Bicycle | `voxelrcnn-ros-g1v3` + `pvrcnnpp-ros-g1v4` + `pointpillars-g1v4` | 0.7 |
| Motorcycle | `pointpillars-g1v3` (plain, single member) | |
| Bus | `pointpillars-ros-g1v4` + `voxelrcnn-ros-g1v3` | 0.3 |
| Truck | `pvrcnnpp-ros-g1v4d2` (draw run) + `pointpillars-ros-g1v3` | 0.3 |
| Van | `voxelrcnn-ros-g1v3` (plain) + `voxelrcnn-ros-g1v4` + `pointpillars-g1`, chosen by the pre-registered Van judge | 0.5 |

V2X portfolio (`routed-g12`; TTA unless marked plain):

| Class | Members | Fusion BEV IoU |
|---|---|---|
| vehicle | `bag-voxelrcnn-ros-g1v5` (3 seeds) + `pvrcnnpp-ros-g1v4-s2` (range-dependent z calibration) | 0.7 |
| pedestrian | `voxelrcnn-ros-g1v3` + `voxelrcnn-ros-g1v4`, then tail copies and the visibility rule | 0.5 |
| truck | `pointpillars-g1v5` + `bag-voxelrcnn-ros-g1v5` + `bag-pvrcnnpp-ros-g1v5` (plain) | 0.5 |

**Where real labels enter.** The site's "No real labels, ever" holds for the detector weights. Real labels still enter in two places, and the report states both:
- validation and selection: V2X settled by the organizers' FAQ; LUMPI Measurements 5-6 still open;
- generator statistics: walker placement copies real label rows, a moderate risk in the [compliance audit](../docs/decisions/2026-10-26-rules-compliance-audit.md), disclosed to the organizers.

Sources: track model READMEs Sections 2-3 and 7; the two `model.yaml` files; [`docs/decisions/README.md`](../docs/decisions/README.md#32-gates) Section 3.2; [`docs/01`](../docs/01-CHALLENGE-FACTS.md#31-our-operating-interpretation) Section 3.1.

### 3.4 Submit

Each zip holds three members:
- `synthetic/0001.bin ... 0050.bin` (float32 N x 3, 50,000 points): chosen from the generator output, never modified. `select_realism_frames.py` swaps frames greedily to minimize FPD (from R5 on, EMD + FPD) against proxies 1-3, then scores the choice on the held-out proxies 4-5. Local held-out R: LUMPI 0.934, V2X 0.935-0.937 (V2X frames with the 31% nulls).
- `predictions.json`: 32,038 boxes (LUMPI) and 21,354 boxes (V2X) on the 50 kit frames (S7.6: 23,270 and 24,284).
- `declaration.txt`: the required declaration word for word, team KarmaRV.

Before each upload, `check_submission.py --official` validates the zip, runs the kit scorer under the server's 1,200 s limit (S8: LUMPI 328 s, V2X 128 s) and records the zip's md5. The entrant uploads the zip unchanged, and the server record is kept as `codabench_<id>.json`. `reproduce_s8b.sh` and `reproduce_s8v.sh` (S7.6: `reproduce_s7s.sh`) rebuild each zip from the release 7.0 weights (IDENTICAL).

## 4. Score breakdown of the final entries (development phase)

The final development entries are S8 (2026-10-30, release 8.0). Server records: [`codabench_1022250.json`](../model-lumpi-track/routed-g11b/submissions/2026-10-30_s8b/codabench_1022250.json) and [`codabench_1022246.json`](../model-v2x-track/routed-g13/submissions/2026-10-30_s8v/codabench_1022246.json); the S7.6 entries before them were [`codabench_1014495.json`](../model-lumpi-track/routed-g10/submissions/2026-10-27_s7s/codabench_1014495.json) and [`codabench_1014682.json`](../model-v2x-track/routed-g12/submissions/2026-10-27_s7s/codabench_1014682.json). Recomputing the combined score from the per-class AP and the four realism distances, with the kit's formula and normalization (`config.json`), reproduces both to six decimals:

```
combined = 0.6 * clip(mAP / 0.7)  +  0.4 * R
R = 1 - mean( clip((CD-2)/28), clip(MMD/0.5), clip(EMD/5), clip(FPD/50) )
```

The site's "norm" of a realism term is 1 minus its normalized distance, and a CD below 2.0 counts as perfect.

| | LUMPI 1022250 (S8) | V2X 1022246 (S8) |
|---|---|---|
| 3D mAP@0.5 (R40) | 0.1762 | 0.6170 |
| Detection = clip(mAP / 0.7) | 0.2516 | 0.8814 |
| Realism R | 0.9323 | 0.9332 |
| 0.6 x detection | 0.1510 | 0.5289 |
| 0.4 x realism | 0.3729 | 0.3733 |
| **Combined** | **0.5239** | **0.9022** |
| Still available: detection / realism | 0.449 / 0.027 | 0.071 / 0.027 |
| Change since S1: detection / realism | +0.035 / +0.016 | +0.130 / +0.005 |
| Change since S7.6 (1014495, 1014682) | +0.0011 (detection only) | +0.0040 (detection only) |
| Next team (2026-10-30) | 0.5118 | 0.8112 |
| ECCV 2026 winner (same scorer and test data) | 0.479 | 0.746 |

### 4.1 Realism: near its ceiling on both tracks

| Term | LUMPI raw -> normalized | V2X raw -> normalized | Reading |
|---|---|---|---|
| CD | 1.594 -> 0 | 1.986 -> 0 | under the 2.0 floor: no cost |
| MMD | 0.00003 -> 0.0001 | 0.00063 -> 0.0013 | the kernel test does not separate the two sets |
| EMD | 1.302 -> 0.260 | 1.182 -> 0.236 | the only term that costs: 96% (LUMPI) and 89% (V2X) of the realism loss |
| FPD | 0.519 -> 0.010 | 1.468 -> 0.029 | the pooled point mean and covariance match closely |

- R 0.932-0.933 is close to what real frames score against other real frames locally (about 0.93-0.95 on LUMPI). The kit's dummy frames score 0.473.
- The remaining loss is EMD: each point would have to move about 1.2-1.3 m on average to match the reference. The largest share of the excess (about 44%) sits in the ground-level background, not on objects.
- Each 0.1 m of EMD is worth +0.002 combined, and perfect realism would add at most +0.027 on either track. Realism is equal across the two tracks, so the ranking is decided on detection.

### 4.2 Detection, LUMPI (mean over 7 classes; Unknown has no test boxes)

| | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van |
|---|---|---|---|---|---|---|---|
| AP | 0.187 | 0.648 | 0.188 | 0.001 | 0.003 | 0.065 | 0.141 |
| Test boxes | 512 | 1,258 | 82 | 27 | 25 | 192 | 79 |

- Car supplies 53% of the mAP (0.093 of 0.176); Motorcycle and Bus are near zero, yet they are 2/7 of the metric.
- Detection is at 25% of its cap, so realism supplies 71% of the combined score. Each +0.01 mAP is worth +0.0086 combined: the remaining LUMPI points are in detection.
- Local splits overstate the test level: mAP 0.391 on realval-A and 0.227 on realval-B against 0.176. Person falls 0.482 -> 0.187, Bicycle 0.600 -> 0.188, Truck 0.487 -> 0.063. The test frames come from the last 20% of Measurement4, which is excluded, and its labels have another provenance.
- BEV mAP 0.189 against 0.176 in 3D: height costs only 0.013. The losses are in finding and classifying objects; 3D mAP@0.7 is 0.085.
- Against S7.6 (1014495): +0.0011 (Person +0.006 from the 12-view fusion and the tail copies, Truck +0.002 and Motorcycle +0.0003 from the lowered floors). S7.6 against S6 (995869) was +0.00009, a tie.

### 4.3 Detection, V2X (mean over 3 classes)

| | vehicle | pedestrian | truck |
|---|---|---|---|
| AP | 0.737 | 0.443 | 0.671 |
| Test boxes | 470 | 953 | 124 |

- mAP 0.617 is 88.1% of the 0.7 cap, so detection can add at most +0.071.
- Pedestrian is the weakest class: 62% of the test objects, one third of the metric. Its gains drove S5, R5, S7 and S8 (0.235 at S1 -> 0.443; S8's 12-view fusion added +0.014).
- BEV 0.667 against 0.617 in 3D: height on the sloped campus costs 0.050 mAP (0.105 at S1).
- 3D mAP@0.7 is 0.165: boxes are found but placed loosely; localization is the residual error.
- Local splits overstate the test level by about 0.11 (realval-A 0.736, realval-B 0.724).

### 4.4 Reading for the paper

- Since S1, LUMPI rose 0.4728 -> 0.5239 (detection +0.035, realism +0.016) and V2X 0.7665 -> 0.9022 (detection +0.130, realism +0.005).
- The V2X lead over the next team (+0.091) is detection; the LUMPI lead (+0.012) is smaller, and the LUMPI challengers' realism is higher (EMD 1.10 against our 1.30), and the open LUMPI points are almost all in detection of the rare classes (Bus, Motorcycle, Truck; paper Section 8, limitations).
- Paper use: the first table is T1, the per-class tables are T2, the realism table feeds T4 ([Section 6](#6-tables-and-figures)).

## 5. Outline and page budget

The 8-page report; the 10-page paper adds Sections 7.3-7.4 and a longer related-work section.

| # | Section | Pages | Content | Sources |
|---|---|---|---|---|
| 1 | Introduction | 0.75 | the task, the two tracks, the combined metric (0.6 detection + 0.4 realism), the four contributions, the headline results | `docs/01` Sections 1-4 |
| 2 | Related work | 0.5 | sim-to-real LiDAR detection, roadside 3D detection, digital twins (UrbanTwin), LiDAR simulation and ray drop, test-time augmentation and box fusion | `docs/07` Sections 6-7 (R1-R44) |
| 3 | Data, splits and rule compliance | 0.75 | the declaration; the forbidden-frame guard and exclusion windows; realval-A/B; the log of real-data use; the rules review | Sections 3.1 and 3.3 here; `docs/01` Sections 3 and 9; `docs/decisions/2026-10-14-rules-compliance-review.md`; data READMEs |
| 4 | Synthetic data | 1.5 | engine G1 (walkers, actor scale, density, FOV), engine G2-lite (re-cast real-size actors, riders, clutter), the density prior, realism-frame selection | Sections 3.2 and 3.4 here; `docs/03` Section 3; `data-<track>-track/README.md` Section 8; `docs/02` Sections 8.7, 8.9 |
| 5 | Detection | 1.25 | the four architectures and their training; object scaling; TTA; cross-architecture fusion; per-class routing, floors and post-processing; seed bags | Section 3.3 here; `docs/03` Section 4; `model-<track>-track/README.md` Section 7; `docs/02` Sections 8.3-8.6, 8.11-8.12 |
| 6 | Validation and selection | 0.75 | the A/B protocol, the upload gate, the pooled rule (one paragraph), the Van judge; reproduction from the released weights | `docs/decisions/README.md` Section 3; root README Section 6.11 |
| 7 | Results | 1.5 | 7.1 leaderboard progression per step (T1); 7.2 per-class results (T2); 7.3 ablations on realval-B (T3); 7.4 realism by component (T4) | Section 4 here; `docs/02` Sections 0 and 8.10; submission register; registries |
| 8 | Limitations and lessons | 0.5 | what did not transfer (LUMPI Bicycle after R3, S5 on LUMPI, LUMPI Car in S7.6, GBlobs alone); classes left near zero (Bus, Motorcycle); the cost of a 100-frame test | `docs/02` Section 8.10 |
| | References | 0.5 | | `docs/07` |

## 6. Tables and figures

| ID | What | Source (exists) | To make |
|---|---|---|---|
| T1 | leaderboard progression per step, combined split into detection and realism, both tracks | `docs/02` Section 8.10 (benefits table) | LaTeX table |
| T2 | per-class AP, S1 and S7 (the S7.6 entries), both tracks | `docs/02` Section 8.10; `codabench_<id>.json` per submission | LaTeX table |
| T3 | ablations on realval-B, one row per lever, both tracks | `docs/02` Section 0; `model-<track>-track/registry.csv` | LaTeX table |
| T4 | realism R per generator component, held-out proxies | `data-<track>-track/README.md` Section 8 | LaTeX table |
| F1 | pipeline diagram: generator, training, portfolio, gates | `docs/03` Section 2 | drawing |
| F2 | real against synthetic frames, bird's-eye view, one per track | the prepared corpora | a plot script in this folder |
| F3 | per-class gains per step (stacked bars) | T1, T2 | a plot script in this folder |
| F4 | fusion and TTA: static false positives per frame and BEV-3D gap | `docs/02` Section 8.3.1 | a plot script in this folder |

## 7. Layout and build

```
paper-bigdata2026/
├── README.md        this file
├── main.tex         IEEE conference template (IEEEtran), one file per section under sections/
├── sections/        01-intro.tex ... 08-limitations.tex
├── tables/          T1-T4 (.tex), written by make_tables.py from the records
├── figures/         F1-F4, written by make_figures.py (F1 drawn by hand)
├── refs.bib         from docs/07
├── make_tables.py   reads the registries, codabench_<id>.json and the submission register
└── make_figures.py  same sources; matplotlib from .venv_ut
```

The server has no TeX installation: build on Overleaf (IEEE conference template) and keep the sources in this folder, so the tables and figures stay generated from the records. Commit the PDF of each submitted version next to the sources (`report-2026-11-15.pdf`, `camera-ready-2026-11-20.pdf`).

## 8. Checklist

- [ ] Final-phase scores recorded (`codabench_<id>.json`, the register in `docs/decisions/README.md` Section 2) before Section 7 is final.
- [ ] Section 3 matches the declaration and the rules review word for word where it quotes them.
- [ ] Organizers cited as Shahbaz and Agarwal; the UrbanTwin papers and datasets cited with their DOIs; licences acknowledged (LUMPI CC BY-NC 3.0, V2X-Real academic use, UT sets CC0).
- [ ] Every number traceable to a record; development and final-phase numbers labelled as such.
- [ ] Code release (top 3): a new public repository with the detector code and the weights of the final entries (the release 7.0 assets), prepared by the maintainer; the paper links to it, never to this repository (which is private).
- [ ] No em dashes; IEEE reference style; figures readable in grayscale.
