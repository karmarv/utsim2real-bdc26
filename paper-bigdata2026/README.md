# paper-bigdata2026: the challenge report and the BigData Cup paper

> **Status 2026-11-14: two track reports, one per track, as the organizers asked (CodaBench message of 2026-11-13). Same structure; titles "Exploring UrbanTwin Sim2Real for Synthetic-Only Roadside LiDAR Detection: LUMPI Track, Team KarmaRV" and "...: V2X-Real Track, Team KarmaRV" (the entrant, 2026-11-14); affiliation Hitachi America, Ltd. R&D.**
> - **Text:** [`report_lumpi.md`](report_lumpi.md) and [`report_v2x.md`](report_v2x.md), the single sources.
> - **Word versions** (IEEE conference template, 10 US-letter pages each including references), named after the organizers' title convention "Final Report - IEEE Big Data Cup 2026 - Track Name - Team Name": [`Final_Report_IEEE_Big_Data_Cup_2026_LUMPI_Track_KarmaRV.docx`](Final_Report_IEEE_Big_Data_Cup_2026_LUMPI_Track_KarmaRV.docx) and [`Final_Report_IEEE_Big_Data_Cup_2026_V2X-Real_Track_KarmaRV.docx`](Final_Report_IEEE_Big_Data_Cup_2026_V2X-Real_Track_KarmaRV.docx).
> - **PDF previews:** the `.pdf` next to each `.docx`, rendered by LibreOffice. Export the submission PDFs from Word.
> - **Figures:** [`figures/`](figures)`fig_lumpi_*.png` and `fig_v2x_*.png`, seven per track, made by [`make_figures.py`](make_figures.py) from the `codabench_<id>.json` records, the routed validation outputs and legal frames.
>
> The entries are LUMPI L8 1051832 (0.54233) and V2X V4 1051825 (0.894399), both release 10.4. L9 (release 10.5, LUMPI) passed every gate and was held back by the entrant (not uploaded); the TransFusion-L member of L10 (10.5 record Section 10) was in training when the reports were last built, and the LUMPI report says so. LUMPI board of Nov 14, 19:48 UTC: L8 fourth (liella722 0.5786, dipper13579 0.5541, lukefinigan 0.5440). Release 10.5 has no V2X upload (the calibrated-corpus retraining lost 0.0586 mAP; the view-set swap passed no class). The combined report of 2026-11-13/14 (`report.md` and its .docx/.pdf) is superseded by the two track reports. Sections 3-4 below are working notes on the S8 development entries; their walkers were placed from real label rows, which the organizers later ruled out, and the reports supersede them. Every number comes from a record in this repository or is measured by `make_figures.py` on legal frames; no model is re-run for the reports.

## 1. Deliverables and dates

| Deliverable | Due | Length and format | Who | Channel |
|---|---|---|---|---|
| Challenge report | **Nov 15, 2026** | 4-8 pages, IEEE two-column | every team | ASK ([`docs/01` Section 10](../docs/01-CHALLENGE-FACTS.md#10-questions-for-the-organizers-email-muhammadshahbazucfedu-on-day-1), question 5) |
| Cup paper (paper track, CyberChair subarea SC04) | camera-ready **Nov 20, 2026** | up to 10 pages including references, IEEE two-column | top 3 per track (invited) | CyberChair |
| Code release for verification | with the paper | a public repository with the detector code and the weights of the final entries | top 3 per track | GitHub (Section 8) |

The final phase closes Sat Nov 14, 16:00 PST, so the report's final-phase numbers arrive less than a day before it is due: draft everything else by **Nov 1**, when the system is frozen at the S7 entries (F1 = the S7.6 zips; their weights are the assets of release 7.0). Winners are announced Nov 25; IEEE BigData 2026 is Dec 14-17 in Phoenix.

**Report channel (organizers' CodaBench message, 2026-11-13, both tracks).** Reports are valid if they reach the organizers by **Nov 15, 2026, 11:59 PM EST**. Recommended: upload to arXiv and email the link; or email the report source and PDF directly (to the first organizer, with the two Cc addresses of that message), stating the team, the participants and the submission IDs; including the report in a submission zip is possible but not recommended. Suggested title: "Final Report - IEEE Big Data Cup 2026 - Track Name - Team Name". One report per track.

## 2. Contributions (what the paper claims)

1. **A rule-compliant synthetic-only pipeline** that ranks first on both tracks (development phase: LUMPI 0.5257, S8.3, rank 1 of 22; V2X 0.9022, S8, rank 1 of 25; final phase: to add on Nov 15). The real data enters only as statistics for the generator and as labelled validation; no detector sees a real frame in training.
2. **Generator side:** completing the organizers' twins with what they miss (walkers and riders ray-cast with the real sensors, real-size actors, static clutter, calibrated background density and field of view), and realism-frame selection against a legal real proxy. Leaderboard realism from the first upload to S7 (unchanged since R5 on V2X and R3 on LUMPI): LUMPI 0.891 -> 0.932, V2X 0.920 -> 0.933 (the organizers' raw LUMPI frames score about 0.60 on our held-out proxy; `data-lumpi-track/README.md` Section 8).
3. **Detector side:** a routed per-class portfolio built from four trained architectures (PointPillars, CenterPoint, Voxel R-CNN, PV-RCNN++; the final entries route three, and CenterPoint's head remains the first stage of the two-stage members) with test-time augmentation, cross-architecture box fusion, class-wise object scaling, seed and generator-draw bags, a ranking rule matched to the real annotators' visibility cut (V2X) and per-class post-processing. Measured on the leaderboard: detection +0.126 (V2X) and +0.034 (LUMPI) of combined score since S1.
4. **Validation practice under a 100-frame hidden test:** two disjoint real validation splits (realval-A and realval-B), pre-registered gates and the pooled rule, and bit-exact reproduction of both entries from the released weights.

## 3. The approach in the challenge's four steps

The challenge website describes the protocol in four steps: get the data, synthesize, train sim-only, submit. This section maps the system behind the final development-phase entries onto those steps (material for paper Sections 3-6). Both entries are S8 (2026-10-30): the S7.6 system plus 12-view TTA fusions of the walker class and, on LUMPI, the non-negative completion; rank 1 on both, and F1 of the final phase:
- Track 1, LUMPI: [`routed-g11d`](../model-lumpi-track/routed-g11d/model.yaml), CodaBench 1022492, combined 0.5257, 15 checkpoints (the S7.6 ones; before it S8.2 [`routed-g11c`](../model-lumpi-track/routed-g11c/model.yaml), 1022399, 0.5254, and S8 U2 [`routed-g11b`](../model-lumpi-track/routed-g11b/model.yaml), 1022250, 0.5239; S7.6 was [`routed-g10`](../model-lumpi-track/routed-g10/model.yaml), 1014495, 0.5228).
- Track 2, V2X-Real: [`routed-g13`](../model-v2x-track/routed-g13/model.yaml), CodaBench 1022246, combined 0.9022, 10 checkpoints (the S7.6 ones; S7.6 was [`routed-g12`](../model-v2x-track/routed-g12/model.yaml), 1014682, 0.8982, identical to 1001919).

The checkpoints of both are the assets of releases 8.0 and 8.1 ([`releases/8.0/weights.json`](../releases/8.0/weights.json)), byte-identical to release 7.0: S8 adds test-time views and post-processing only.

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
- `predictions.json`: 37,396 boxes (LUMPI) and 21,354 boxes (V2X) on the 50 kit frames (S7.6: 23,270 and 24,284).
- `declaration.txt`: the required declaration word for word, team KarmaRV.

Before each upload, `check_submission.py --official` validates the zip, runs the kit scorer under the server's 1,200 s limit (S8: LUMPI 361 s, V2X 128 s) and records the zip's md5. The entrant uploads the zip unchanged, and the server record is kept as `codabench_<id>.json`. `reproduce_s8d.sh` and `reproduce_s8v.sh` (S7.6: `reproduce_s7s.sh`) rebuild each zip from the release 7.0 weights (IDENTICAL).

## 4. Score breakdown of the final entries (development phase)

The final development entries are S8 (2026-10-30): LUMPI S8.3 (release 8.1) and V2X S8 (release 8.0). Server records: [`codabench_1022492.json`](../model-lumpi-track/routed-g11d/submissions/2026-10-30_s8d/codabench_1022492.json) and [`codabench_1022246.json`](../model-v2x-track/routed-g13/submissions/2026-10-30_s8v/codabench_1022246.json); the S7.6 entries before them were [`codabench_1014495.json`](../model-lumpi-track/routed-g10/submissions/2026-10-27_s7s/codabench_1014495.json) and [`codabench_1014682.json`](../model-v2x-track/routed-g12/submissions/2026-10-27_s7s/codabench_1014682.json). Recomputing the combined score from the per-class AP and the four realism distances, with the kit's formula and normalization (`config.json`), reproduces both to six decimals:

```
combined = 0.6 * clip(mAP / 0.7)  +  0.4 * R
R = 1 - mean( clip((CD-2)/28), clip(MMD/0.5), clip(EMD/5), clip(FPD/50) )
```

The site's "norm" of a realism term is 1 minus its normalized distance, and a CD below 2.0 counts as perfect.

| | LUMPI 1022492 (S8.3) | V2X 1022246 (S8) |
|---|---|---|
| 3D mAP@0.5 (R40) | 0.1782 | 0.6170 |
| Detection = clip(mAP / 0.7) | 0.2546 | 0.8814 |
| Realism R | 0.9323 | 0.9332 |
| 0.6 x detection | 0.1528 | 0.5289 |
| 0.4 x realism | 0.3729 | 0.3733 |
| **Combined** | **0.5257** | **0.9022** |
| Still available: detection / realism | 0.447 / 0.027 | 0.071 / 0.027 |
| Change since S1: detection / realism | +0.036 / +0.016 | +0.130 / +0.005 |
| Change since S7.6 (1014495, 1014682) | +0.0028 (detection only) | +0.0040 (detection only) |
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
| AP | 0.188 | 0.661 | 0.188 | 0.001 | 0.004 | 0.065 | 0.141 |
| Test boxes | 512 | 1,258 | 82 | 27 | 25 | 192 | 79 |

- Car supplies 53% of the mAP (0.094 of 0.178); Motorcycle and Bus are near zero, yet they are 2/7 of the metric.
- Detection is at 25% of its cap, so realism supplies 71% of the combined score. Each +0.01 mAP is worth +0.0086 combined: the remaining LUMPI points are in detection.
- Local splits overstate the test level: mAP 0.391 on realval-A and 0.227 on realval-B against 0.178. Person falls 0.484 -> 0.188, Bicycle 0.600 -> 0.188, Truck 0.487 -> 0.063. The test frames come from the last 20% of Measurement4, which is excluded, and its labels have another provenance.
- BEV mAP 0.191 against 0.178 in 3D: height costs only 0.013. The losses are in finding and classifying objects; 3D mAP@0.7 is 0.085.
- Against S7.6 (1014495): +0.0028 (Person +0.007 from the 12-view fusion and the tail copies; Car +0.013 from the 12-view PV-RCNN++ bag, although its local gain was +0.0018 / -0.0010; Truck +0.002, Bus +0.001 and Motorcycle +0.0003 from the lowered floors and the copies). S7.6 against S6 (995869) was +0.00009, a tie.

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

- Since S1, LUMPI rose 0.4728 -> 0.5257 (detection +0.036, realism +0.016) and V2X 0.7665 -> 0.9022 (detection +0.130, realism +0.005).
- The V2X lead over the next team (+0.091) is detection; the LUMPI lead (+0.014) is smaller, and the LUMPI challengers' realism is higher (EMD 1.10 against our 1.30), and the open LUMPI points are almost all in detection of the rare classes (Bus, Motorcycle, Truck; paper Section 8, limitations).
- Paper use: the first table is T1, the per-class tables are T2, the realism table feeds T4 ([Section 6](#6-tables-and-figures)).

## 5. The track reports as written (report_lumpi.md, report_v2x.md)

Both reports follow one structure; only the track's data, members, iterations and results differ.

| Section | Content | Main sources |
|---|---|---|
| I Introduction | the task, the track's three difficulties, team and submission IDs, contributions; Fig. 1 the two stacks and their checks | `docs/01`; the dataset paper [2]; the ECCV 2026 reports [7], [8] |
| II Related work | simulators and twins, transfer, detectors and ensembles, realism metrics | `docs/07` |
| III Track, data and protocol | Table I the track, the metric (1)-(2), the real-data boundary and the three rulings, validation splits, environment | `docs/01`; `data-*-track/README.md`; the S10 records |
| IV Data observations | sensor and frame; class mix, size and density (Table II gaps and fixes, Fig. 2 frames, Fig. 3 data statistics); static structure; label provenance (LUMPI) or label coverage (V2X); realism (Table III) | `data-*-track/README.md`; `docs/02` Section 8; S9 and S10 records; `make_figures.py` on legal frames |
| V The final system | CompleteTwin generator, training, inference, Table IV composition (and V2X Table V members), post-processing stages, the decision protocol and how its gates grew | model cards `routed-s10-4-l8`, `routed-s10-4-v4` and parents; scorecards; S9, S10 records |
| VI Model observations | architectures per class, views, fusion, bags and seeds, localization, the clean rebuild, the error profile (LUMPI Tables V-VI) | registry and member score files; S2-S10 records |
| VII Strategy evolution and trade-offs | the ten iterations; the iterations table (evidence, gate, trade-off, server change); Phases I-III; the upload codes; 10.5 (L9; V2X calibrated-corpus retraining); Fig. 4 what each iteration bought; Fig. 5 every scored upload | `codabench_<id>.json`; the S10, 10.2-10.5 records |
| VIII Results | final-phase uploads table, Fig. 6 qualitative cases (three rule-chosen realval-B frames), Fig. 7 per-class AP, leaderboard, transfer | score files; 10.2 record Section 11; 10.4 and 10.5 records |
| IX What did not work | the negative-results table; the required list of real-data uses | S7-S10 records; 10.2 record Section 9 |
| X-XI Discussion, conclusion | lessons, limitations, reproducibility | releases 10.2-10.5 |

New measurements made for the reports (by `make_figures.py`, legal frames only): objects per frame, box sizes and points per box by range for the released twin (`ut-v1`), CompleteTwin draw 1 (`g1-v6`) and realval-A+B (Fig. 3, numbers printed by the script); the realval-B qualitative frames (Fig. 6). Two findings came from them: on LUMPI, real Truck and Bus share one median size and real Vans are car-length, while CompleteTwin's trucks are shorter and its buses and vans longer; some person-sized objects in Measurement 6 carry Car or Van labels. On V2X, one realval-B scene part (`2023-04-04-15-58-18_30_0`, 11 frames) has no pedestrian label while the system finds 31.7 pedestrians per frame there; within 10 m CompleteTwin walkers carry about three times the real points.

### 5.1 Names used in the paper and their repository codes

The paper uses names, not repository codes. The corpora of the `g1-v6` family (`g1-v6`, draws `g1v6d2`-`d5`, unions) are **CompleteTwin**. Iterations are numbered by release tag:

| Iteration (paper) | Repository code | Name in the paper | Release |
|---|---|---|---|
| 1 | S1, S1+C1 | Calibrated Twin | 0.1, 1.0 |
| 2 | S2 | Center-Routed Small Objects (not adopted) | 2.0 |
| 3 | S3 | Fused Portfolio | 3.0 |
| 4 | S4 | Two-Stage Refinement | 4.0 |
| 5 | S5 | Size-Aware Augmentation | 5.0 |
| 5.1 | R3 (G2-lite) | Re-cast Twin | 5.1 |
| 5.2 | R5 | Realism-Led Refinement | 5.2 |
| 6 | S6 | Seed Bags | 6.0 |
| 7 | S7, S7.6 | Visibility Rule | 7.0 |
| 8 | S8, S8.2, S8.3 | Twelve-View Completion | 8.0, 8.1 |
| 9 | S9 (`s9a`-`s9j`) | Label-Free Twin | 9.1, 9.2 |
| 10.1-10.5 | S10 (`C0`, `c1av5` = OD, `s10-2-l1` = L1, `s10-2-v1` = V1, `s10-2-l5` = L5, `s10-4-v4` = V4, `s10-4-l8` = L8, `s10-5-l9` = L9; V3x/V3xp = "the calibrated corpus", V5 = "the view-set swap", not uploaded) | Clean Final | 10.1-10.5 |

The final size adjustment is the repository's P (LUMPI) and PV (V2X); static-mass completion is R1; the calibrated corpus is `g1-v6aw` (range mapping `aw_mid`). On LUMPI, iteration 7 is named "generator-draw bags" (S7.6) because the Visibility Rule is V2X-only. Release 10.0 (the S9 close-out re-tag, removed) is not named in the reports.

## 6. Figures and tables

Every figure exists per track: `figures/fig_lumpi_<name>.png` and `figures/fig_v2x_<name>.png` (`make_figures.py --track lumpi v2x --only <name>`).

| Item | `<name>` | What | Made from |
|---|---|---|---|
| Fig. 1 | `pipeline` | the generator stack, the detector stack and the evaluation and rule checks, with iteration tags and the timeline | drawn by `make_figures.py` (`PIPE` holds the track's layers, `ITERATIONS` the names) |
| Fig. 2 | `frames` | a released twin frame, the same frame in CompleteTwin (one of the 50 submitted) and a real realval-A frame | `ut-v1`, `g1-v6`, `realval-v1` |
| Fig. 3 | `data` | class mix, box length, points per box by range: released twin, CompleteTwin, real | the same three sources (`SOURCES`) |
| Fig. 4 | `levers` | combined change per iteration, detection and realism parts | the entry path in `PATHS` and the score files |
| Fig. 5 | `trajectory` | every scored upload by status, phases I-III shaded | the track's `codabench_<id>.json` files (`PHASES`) |
| Fig. 6 | `qualitative` | three realval-B frames chosen by fixed rules (`QUAL_RULES`), matched at the official 3D IoU | the routed validation outputs of the entries (`routed-s10-4-l8`, `routed-s10-4-v4`) |
| Fig. 7 | `perclass` | per-class AP: first upload, best development upload, best before the ruling, C0, entry | the score files (`PERCLASS`) |
| Tables | | LUMPI I-IX, V2X I-VIII: track; twin gaps; realism by frame version; composition (V2X: and members); LUMPI: sampling by architecture, loss decomposition; iterations; final-phase uploads; negative results | `docs/01`, `data-*-track/README.md`, model cards, scorecards, score files, decision records |

## 7. Layout and build

```
paper-bigdata2026/
├── README.md                     this file
├── report_lumpi.md, report_v2x.md    the two track reports (single sources)
├── Final_Report_IEEE_Big_Data_Cup_2026_LUMPI_Track_KarmaRV.docx / .pdf      built from report_lumpi.md
├── Final_Report_IEEE_Big_Data_Cup_2026_V2X-Real_Track_KarmaRV.docx / .pdf   built from report_v2x.md
├── template/ieee-conference-template-letter.docx   the IEEE conference template (US letter, Strict OOXML)
├── figures/                      fig_lumpi_*.png, fig_v2x_*.png, 300 dpi
├── make_figures.py               figures from the records and legal frames (matplotlib, scipy; .venv_ut)
└── build_docx.py                 report_<track>.md -> .docx (standard library only); --pdf renders with soffice
```

```bash
source common/env/activate.sh && python paper-bigdata2026/make_figures.py && python paper-bigdata2026/build_docx.py --pdf
```

- **Styles.** The builder keeps every style of the template: title, author, abstract, keywords, numbered headings, body text, bullets, table head, figure caption, references.
- **Floats.** Full-width figures and the wide tables are floats anchored at the top or the bottom of a page (`<!-- wide top -->`, `<!-- wide bottom -->`), so the two-column text needs no section breaks. In LibreOffice:
  - Place a top float's directive where its anchor falls in the **left column** of the page that should hold it; an anchor in the right column lets text laid out before it run under the float.
  - Place a bottom float's directive high enough on its target page that the table fits below it; otherwise its height is reserved on that page and the table jumps to the next one.
  - Keep one top float per page; two on one page are drawn over each other.
  - A column table or figure that does not fit where it falls moves to the next column and leaves a gap; put it after a paragraph that can fill the column.
  - Current pages: Fig. 1 on 2, Fig. 2 on 3, Fig. 3 on 4, the iterations table on 7, Fig. 6 on 8, the negative-results table at the bottom of 9 (both reports). After any edit, list each page's lines and captions (for example `pdftotext -f N -l N -layout` on each column) and look at the pages.
- **Table widths.** Each column first gets the width of its longest cell (up to the table width), in proportion to what it needs; any spare width is shared by text length. Keep column tables to six or seven short columns.
- **Numbering.** Figure and table numbers are written as text, and the builder checks them against the document order; references are numbered in order of first citation (each report cites only its own UT dataset, so its reference list has 37 entries).
- **Final PDF.** Open each .docx in Word, check the floats, and export the PDF there.

## 8. Checklist

- [x] Every number traceable to a record; development and final-phase numbers labelled as such.
- [x] The required report items of the 2026-11-12 record (Section 9): the change and the removed uploads; every real-data use; label statistics; R1 (not shipped); the PandarQT re-cast (frames only, not qualifying); the V2X no-returns; the calibrations; the test-time stages; P.
- [x] Organizers cited as Shahbaz and Agarwal; the dataset paper (IEEE OJ-ITS 2026, arXiv:2509.06781) and the UT dataset DOIs cited; licences named (LUMPI CC BY-NC 3.0, V2X-Real academic use).
- [x] No em dashes; IEEE reference style; figures readable in grayscale (marker shapes carry the status).
- [x] Affiliation: Hitachi America, Ltd. R&D (the entrant, 2026-11-14); team KarmaRV named in the Introduction.
- [x] Release 10.4 (2026-11-14): V4 1051825 and L8 1051832 are the entries; abstract, Sections V-D, VI, VII, VIII, IX-X, Tables IV-VI and Figs. 1, 3-6 updated.
- [x] Restructure (2026-11-14): new title and affiliation; CompleteTwin for `g1-v6`; iterations by name, every code defined where used; Fig. 1 redrawn as the two stacks with checks and the iteration timeline; Table IV (what worked) replaces the transfer table; 10 pages.
- [x] Split into two track reports (2026-11-14, the entrant): same structure, track and team in the title, per-track figures, data, model, strategy and experiment observations; 10 pages each.
- [x] Titles shortened (2026-11-14, the entrant); L9 marked held; the Nov 14 LUMPI board; the rare-class evidence of the 10.5 record (118 detectors; corpus counts); TransFusion-L cited as [38] (LUMPI).
- [ ] If L10 or L11 (or L9) is uploaded and scored: add its row to the LUMPI Table VIII and its result to Sections I, VII-C and Table VII; if it beats L8, also the abstract, Section VIII and `ENTRY`, `PERCLASS`, `FINAL_CARD`, `PATHS` in `make_figures.py`.
- [ ] Code release (top 3): a new public repository with the detector code and the weights of the final entries (release 10.4), prepared by the maintainer; the paper links to it, never to this repository (which is private).
- [ ] Challenge reports due Nov 15, 11:59 PM EST, by email (one per track; team, participant and submission IDs stated in each); Cup camera-ready Nov 20 (up to 10 pages including references, IEEE two-column, single-blind).
