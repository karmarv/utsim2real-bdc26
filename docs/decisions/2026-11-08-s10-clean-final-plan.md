# 2026-11-08 S10 plan: Clean Final, label-free entries for the final week

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

## 1. The clarifications, line by line

| Sentence (both tracks unless marked) | What we do | Verdict |
|---|---|---|
| LUMPI: "All 100 IDs in forbidden_frames.txt are frames from Measurement 4 ... 006497 is Measurement4/lidar/006497.ply" | The kit list holds 100 IDs, 006497 to 008109, all inside the organizers' M4 test window (6496-8119). The guard blocks the window, and label rows are filtered while streaming. Realval-A is M4 0-6395 (every 5th frame), and every other M4 use stops at frame 6399. | **Confirmed.** The nearest legal use is 98 frames before the first forbidden ID. |
| V2X: "`<s>_<f>` ... infrastructure LiDAR (agent folder -1) ... `<s>` is a 0-based index over the ... scenario folders that contain a -1 agent, sorted by name (33 in total)" | This is the FAQ rule we checked on 2026-10-27 (audit addendum). Our point-matched mapping agrees at every index. The guard blocks a superset of candidate folders. No realval frame and none of 14,381 logged reads lies within 20 frames of a forbidden frame. | **Confirmed.** The organizers' mapping tables are Google Drive files. A direct comparison would replace our inference, but downloading them is the entrant's call. |
| "you may use the remaining real training frames for validation, model selection and box-size statistics (labels allowed)" | Covers: realval A/B and every grid, route, fusion, threshold and copy choice; the S9 anchored size calibration; the 19 size quantiles of the rare classes; the size thresholds of the vehicle class rule; the walker box-size mixture. | **Allowed, now explicitly.** This closes the size part of audit item 4 and disclosure item (i). |
| "and for calibrating the realism of your synthetic data (unlabelled clouds)" | Covers: the background density priors, the OS1-64 beam table, and the realism proxies that select the 50 frames. | **Allowed, now explicitly.** This closes audit item 19. One residual point: the V2X statistics use val and test split frames, so we read "remaining real training frames" as every non-forbidden frame, as the Oct 14 FAQ did for validation. Disclose it. |
| "The detector itself must be trained only on synthetic data, so **real labels and object points cut out with real boxes must not enter the training set**" | **Corpora before `g1-v6`** (LUMPI from `g1-v1`, V2X from `g1-v3`): every inserted walker copies one real label row, with its position jittered by 0.4 m, heading by 0.2 rad, size by 0.97-1.03, and with the real ground height. The rendered walker's box is its training label. The G2 clutter is also anchored at real walker positions. **`g1-v6` corpora:** walkers and clutter are placed on the twin's own scene map, and only scalars reach the generator: the box-size mixture, size quantiles, and a 10-bin range histogram. **No corpus** contains object points cut out with real boxes; the GT-sampling databases are built from each synthetic corpus. | **Pre-v6 corpora: not compatible** on a plain reading, since each walker's training box is a real label plus small noise. **`g1-v6`: compatible.** The range histogram is a position statistic, not a label; disclose it. |
| "Please describe any use of real data in your report." | The report draft (`paper-bigdata2026/README.md` Sections 3.1-3.3) lists the uses. It also says the walker rows were "disclosed to the organizers", which has not happened: the email is unsent. | **Rewrite** the report's real-data section (Section 9) and correct that sentence. |

## 2. What this means for the kept zips

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

## 3. New measurements (2026-11-08; legal frames, corpus cards and validation outputs only)

### 3.1 Clean members against the kept zips

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

### 3.2 Corpus effect, same architecture: `g1-v4`/`g1-v5` to `g1-v6`

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

### 3.3 LUMPI label conventions: the test window is late Measurement 4

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

### 3.4 Size gap between `g1-v6` and real labels

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

### 3.5 Compute and storage

- **GPUs.** 8 A6000s run as two 4-GPU workers.
- **Training time per member.** PointPillars 1.1-2.1 h; Voxel R-CNN 2.9-5.2 h; PV-RCNN++ 2.9-4.1 h; VoxelNeXt 1.7-3.8 h; DSVT 5.5-7.5 h.
- **Validation tuning.** About 3 h per LUMPI member and about 1.2 h per V2X member. A 12-view job adds 80 min on LUMPI and 27 min on V2X.
- **Builds.** A new 10,000-frame draw takes about 20 min of CPU. A portfolio build takes 2-3.5 h.
- **Budget.** About 300 worker-hours remain until Nov 14, enough for 50-60 member trainings with tuning across both tracks. Tuning, not training, is the binding constraint, as in S9.
- **Weight averaging needs no retraining.** Epoch 11-40 checkpoints are kept for every member.
- **Disk.** 386 GB free (95% used). That is enough for about 20 new corpora; old corpora are not deleted.

## 4. Hypotheses

- **H1 (compliance at small cost).** A clean portfolio from the existing `g1-v6` members ties the kept zip on LUMPI within ±0.005 combined. On V2X it loses about 0.02-0.03 combined.
- **H2 (V2X depth).** The V2X gap is ensemble depth, not the corpus. Two more clean draws, with PV-RCNN++ and Voxel R-CNN bags over three or four draws and 12-view TTA, recover half or more of it. Evidence: seed bags +0.0079 on the V2X server (S6), draw bags +0.002 to +0.011 each (S7.4).
- **H3 (sizes in training).** Real box-size statistics are now explicitly allowed. Applied in training as statistical normalization, they raise AP@0.5 through better centres where the sizes differ most (Section 3.4): LUMPI Car, Person, Van and Bus, and V2X vehicle height. The S9 test-time calibration (3D@0.7 +0.034 on V2X) shows the size bias is real.
- **H4 (weight averaging).** Averaging the last checkpoints of a member is a small, free robustness gain under domain shift.

## 5. Levers, ranked by value per effort

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

## 6. Three plans

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

## 7. Work packages and schedule (Plan A; UTC)

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

## 8. Pre-registered rules (written 2026-11-08, before any S10 run)

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

## 9. Compliance, the email and the report

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

## 10. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Clean V2X stays 0.02-0.03 below 0.904 | Still about 0.06 above the best V2X competitor seen (Nov 2). Spend B1 first. |
| Clean LUMPI lands below 0.5428 | The margin to the next team was 0.031 on Nov 2. E2 and C1 are the LUMPI levers. |
| The best submission counts and a pre-v6 zip stays best | The email asks the organizers to rank the clean uploads. The entrant may also check whether CodaBench lets a participant remove a final-phase submission; that is the entrant's decision. |
| Tuning throughput | Tune the 8-view set first, and run 12-view only for members that pass. |
| Disk at 95% | New corpora only; delete nothing without the entrant's say. |

## 11. Literature behind the levers

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

## 12. Decisions for the entrant

1. Adopt Plan A: every remaining upload is clean.
2. Send the email of Section 9 (I can draft it).
3. Optional downloads: the organizers' two mapping tables (a cross-check), and realval-C frames (lever H1).
4. Optional new code for lever G1 (new packages need the entrant's permission).

## 13. Results

### 13.1 Day 0: Plan A started (2026-11-08, 03:40-04:00 UTC; before any S10 result)

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

### 13.2 `C0` built on both tracks (2026-11-08, 05:20-07:00 UTC)

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

### 13.3 `C0` scored (final phase, upload 2; the entrant's scoring output, 2026-11-08)

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

### 13.4 The final-phase leaderboard (the entrant's screenshots, server time 2026-11-08 06:45 and 06:52 CST)

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

## 14. The plan after `C0` (2026-11-08, 13:00-14:30 UTC; written before any W2 result)

### 14.1 Where the points are

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

### 14.2 What the research adds (2026-11-08; two read-only scans, numbers as reported, "unverified" where not checked)

- **The other entrant's reports** (Luo et al., arXiv 2609.07590 LUMPI and 2609.07608 V2X): LUMPI combined 0.4692 (mAP 0.126, R 0.9035, EMD 1.857, CD 2.18), V2X 0.742 (mAP 0.452). Their largest LUMPI step was a box-size calibration (+0.0135 mAP), which we have. Class routing helped them (+0.0093); uniform ensembles added false positives. Their scorer description: both sides masked to [-40, 40]² x [-5, 5] m, 10,000 points sampled per side.
- **Hard negatives for pedestrians.** False-positive sampling (arXiv 2403.02639) raised KITTI pedestrian moderate AP by 4.8-9.1 (PV-RCNN, SECOND, CenterPoint). This supports B2a (structures in V2X `g1-v7`). Mining false positives on real frames, or pasting real points, is not allowed.
- **Pedestrian box conventions.** PCGen (arXiv 2210.08738): CAD pedestrians with pose filtering and box loosening went from 6.56 to 54.31 3D AP@0.5 on real Waymo (real data 61.62). Our walker box-to-body margins are already scalars chosen on realval-A (S9); the size part is in C1.
- **Visibility cues.** Free-space and visibility features raised nuScenes pedestrian AP from 38.2 to 45.7 (Hu et al., CVPR 2020). The cheap form is a demotion stage on validation (lever V5); a learned rescorer trained on synthetic true and false boxes is the full form (lever X1).
- **Weight averaging.** Model soups gave about +1 AP on COCO detectors (arXiv 2012.12645). No domain-shift evidence was found, but our first checks pass (Section 14.3).
- **Realism.** EMD at the scorer's sample size cannot go below about 0.95 (empirical W1 converges as n^(-1/3)). Global transforms and per-point moves are not allowed or did not transfer for the other entrant. Our density prior is already the thinning model the literature recommends.
- **Grey, not used without the organizers' answer:** locating real static structure (poles, trees) in unlabelled real clouds to place synthetic negatives there ("twin completion"); any new test-time hedge such as low-score cross-class duplicates. Both go into the email as questions.

### 14.3 Experiments in progress (state at 14:30 UTC)

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

### 14.4 Levers for C1 and C2, ranked by value per GPU hour

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

### 14.5 Incremental plans on top of Plan A

Each increment can be adopted alone. The cost is in GPU worker-hours (two 4-GPU workers, about 250 worker-hours until training stops on Nov 13, 18:00 UTC).

1. **Increment 1, V2X pedestrian (B2a, V5, the snrj member).** If the `g1-v7` probe passes pedestrian, train PV-RCNN++, VoxelNeXt and a second Voxel R-CNN draw on `g1-v7` (about 10 worker-hours) for a `g1-v7` bag. V5 enters as a pre-registered stage (k from {3, 5, 10, 20} on A, rule 11). Expected +0.005 to +0.015 on V2X.
2. **Increment 2, weight averaging everywhere (D1+).** Average every draw member and bag the averages; no training. Expected +0.002 to +0.006 on V2X; LUMPI if its checks pass.
3. **Increment 3, LUMPI depth (L1).** About 13 worker-hours. Expected +0.001 to +0.004. (V5 does not apply to LUMPI, 14.3.)
4. **Increment 4, stretch (X1, F2).** Only once 1-3 are built, by Nov 11.

**Recommended:** all of 1-3 (about 25 worker-hours of training plus tuning, inside the budget), and 4 only if there is time.

### 14.6 Schedule (UTC)

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

### 14.7 Rules added before any W2 result

10. **Projection against `C0`.** Rule 6 as before, against `C0`'s local scores. A new version needs projection > 0 and the final pooled gate. A loss from a systematic change is not shrunk (13.3).
11. **New post-processing stages** (V5, X1) follow the S7 sparse rule: one parameter per class, chosen on realval-A, kept only with pooled P(gain) >= 0.9 and neither split down by more than 0.005.
12. **`g1-v7` is a training corpus.** V2X realism frames stay `g1-v6`-family frames (rule 6), unless a re-selection passes S9 rule 4 with CD below 1.9.

## 15. S10 wave 1: increments 1-4 adopted (2026-11-08)

**Decision.** On 2026-11-08 the entrant adopted increments 1-4 of Section 14 as the first wave of S10 work ("proceed by adopting the 1-4 proposal under the first wave of work in S10"). This section is the readable brief behind that decision, with the leaderboard reading of Section 13.4 folded in. Increment 5 (realism, 15.6) was added the same day.

### 15.1 The rules, in brief (the organizers' clarification of 2026-11-07, both tracks)

| Code | What the clarification says |
|---|---|
| **T** | The detector is trained on synthetic data only. |
| **L** | Real labels, and object points cut out with real boxes, never enter training. |
| **V** | Non-forbidden real frames may be used for validation, model selection and box-size statistics (labels allowed). |
| **C** | Unlabelled real clouds may be used to calibrate the realism of the synthetic data. |
| **D** | Every use of real data is described in the report. |

### 15.2 What S1-S10 taught us, and how it shapes the wave

1. **Ensemble depth transfers.** Seed bags gave +0.008 on the V2X server (S6), draw bags +0.002 to +0.011 (S7.4).
2. **Corpus fixes transfer.** Label-free walkers gave LUMPI Person +0.07 on the server (S9).
3. **Fine post-processing transfers at 0.3-0.6x.** Gains picked on validation shrink on the server.
4. **Rare-class picks did not transfer** (`s9iu`: +0.010 projected, -0.0025 scored).
5. **Today's evidence.** Weight averaging passes on 3 of 4 members. 65% of confident false V2X pedestrians sit on static structures. The board shows LUMPI as the close race (lead 0.0066) and realism as our weakest term on both tracks (13.4).

### 15.3 The four increments

| # | Technique | Evidence (ours; literature) | Expected combined | Cost | Rules |
|---|---|---|---|---|---|
| **1. V2X pedestrian** | (a) **`g1-v7`**: map-placed static structures (hedges, fences, walls, shelters, facades) in V2X training scenes as unlabelled negatives; realism frames stay `g1-v6`. (b) The SN + range-jitter member enters for pedestrian only. (c) **V5 overhead-points demotion** (rule 11). | Ours: 65% of confident false pedestrians are static structures; LUMPI's corpus with structures gained Person +0.07 to +0.17; (b) +0.004 to +0.006 pooled; (c) +0.002 to +0.003 AP on both splits. Literature: false-positive sampling, +4.8 to +9.1 AP on KITTI pedestrians (arXiv 2403.02639) | V2X **+0.003 to +0.012** | probe: one 3 h training; 3 more members (about 10 worker-hours) if it passes | **T, L:** synthetic scenes, positions from the twin's own map. **V:** the demotion threshold and size targets come from validation and size statistics. **D** |
| **2. Weight averaging everywhere** | The mean of the epoch 31-40 checkpoints of each member (SWA); bags of the averaged draws | Ours: V2X Voxel R-CNN vehicle +0.005, truck +0.008; V2X PV-RCNN++ vehicle +0.005, pedestrian +0.004; LUMPI Voxel R-CNN Car +0.016, Bicycle +0.012, Person +0.007; LUMPI PV-RCNN++ mixed. Literature: SWAD (arXiv 2102.08604); model soups about +1 AP on COCO (arXiv 2012.12645) | **+0.002 to +0.006 per track** | no training; about 40 h on the tuning workers | **T:** synthetic-trained weights only. **V:** the member check |
| **3. Ensemble depth** | V2X: draws 3 and 4 (Voxel R-CNN, PV-RCNN++, VoxelNeXt), 4-draw bags with 12-view TTA. LUMPI: draw 3 for the Person and Car members (Voxel R-CNN rosn and rosf, PV-RCNN++), 3-draw bags | Ours: the S6 and S7.4 transfers; V2X draw-3 Voxel R-CNN vehicle +0.021 pooled; `C0` V2X lost mostly through shallower fusion | V2X **+0.005 to +0.012**; LUMPI +0.001 to +0.003 | V2X about 9 worker-hours; LUMPI about 13 | **T:** new synthetic draws of the same clean recipe |
| **4. Stretch** | (a) **X1**, a small rescorer for walker boxes, trained only on synthetic detections, with visibility features (points above, free space through the box, height above ground, points against the count expected at that range). (b) **F2**, V2X realism frames re-selected from the 40,000-frame pool of draws 1-4 | Literature: visibility features +7.5 AP on nuScenes pedestrians (Hu et al., CVPR 2020). Ours: the overhead feature alone gives +0.002; realism re-selection transferred at 0.35x on LUMPI (1.2x on V2X for `g1-v6`) | +0.000 to +0.005 (uncertain); +0.000 to +0.002 | 8-12 h of code on CPU | **T:** trained on synthetic only. **C:** frames chosen against unlabelled real proxies |

### 15.4 Pros and cons

| # | Pros | Cons and risks |
|---|---|---|
| 1 | Targets the one measured V2X gap with a synthetic-only fix. The probe answers in about 6 h. | Structures may also hide real pedestrians standing by walls. The probe may fail (S9 left structures out of V2X for realism; the frames stay `g1-v6`). V5 only helps the low-score tail. |
| 2 | Free: every member keeps the checkpoints. Strong on 3 of 4 checks. | Gains can shrink inside fusion, which already averages. 12-view TTA needs a GPU without training (45 GB), so averaged members use 8 views until training stops. |
| 3 | The best-transferring lever on V2X. New draws cost minutes of CPU. | Most GPU hours. Returns fall off past 3-4 draws. Single draws swing per class (draw-3 truck -0.05), so only bags are used. |
| 4 | No detector retraining. Aims at the ranking loss (0.29 of pedestrian AP). | The rescorer learns synthetic false positives, which differ from real ones. Small measured signal so far. Competes with 1-3 for time. |

### 15.5 Not pursued

| Idea | Reason | Rule |
|---|---|---|
| Self-training, pseudo-labels, test-time adaptation | the detector would learn from real clouds | not allowed (T) |
| Placing negatives where real unlabelled clouds show poles and trees ("twin completion") | the strongest false-positive fix in the literature, but its positions come from real clouds | grey: email question (c) |
| New test-time hedges (low-score duplicates across classes) | a metric hedge | disclosure needed; not without the entrant's approval |
| LUMPI rare-class relabelling by size at inference | cannot be validated in the test window | the `s9iu` lesson; rule 3 |
| Generative LiDAR models fitted to real clouds | real clouds would reach training through the generator | not allowed (T) |
| New backbones | no cross-domain evidence; new code and packages | allowed, low value |

### 15.6 Increment 5, realism (adopted by the entrant on 2026-11-08: "Add increment 5")

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

### 15.7 Wave 1 actions (launched 2026-11-08, 13:00-15:30 UTC)

| Increment | Action | State |
|---|---|---|
| 1a | `g1-v7` built and clean (structures 30, seed 7234); `voxelrcnn-ros-g1v7` first in the train queue | **Decision point:** its member check against `voxelrcnn-ros-g1v6`. If it passes pedestrian without failing another class: PV-RCNN++, VoxelNeXt and a second Voxel R-CNN draw on `g1-v7` |
| 1b | `voxelrcnn-ros-snrj-g1v6` passed pedestrian; it enters `C1`'s route search as a pedestrian candidate | done |
| 1c | V5 stage in `route_predictions.py` (`overhead` mode, `overhead_demotion` card key, part of the final gate's class configuration), two unit tests; V2X step in `s10_portfolio_tail.sh` after the sparse stage | built. **Dry run on a scratch copy of V2X `C0`:** pedestrian k 5 kept (A +0.0029, B +0.0017, pooled +0.0027 at P(gain) 1.00; the next k, 10, gains +0.0022, so no lone spike). It enters `C1` through the V2X tail script |
| 2 | 15 averaged members of every `C0` leaf member, queued for tuning; a third tuning worker | tuning; member checks as each finishes |
| 3 | V2X draw 4 members queued. LUMPI `g1-v6d3` (S9 G5 flags, seed 3234) building, with `voxelrcnn-rosn-g1v6d3`, `voxelrcnn-rosf-g1v6d3` and `pvrcnnpp-ros-g1v6d3`. **Order:** the `g1-v7` probe, then the two LUMPI Voxel R-CNN draws (LUMPI is the close race), then the probes, then LUMPI PV-RCNN++, then V2X draw 4 | building |
| 4 | X1 and F2 code after `C1` is built | Nov 10 |

### 15.8 Schedule (UTC; both tracks close 2026-11-16 04:59 per the phase pages)

| When | Work | Uploads |
|---|---|---|
| Sun Nov 8 | wave 1 launched (15.7) | (`C0` scored) |
| Mon Nov 9 | member checks; the `g1-v7` decision; SWA of new draw members; V2X `C1` build once the draw-3 bags and averaged members are tuned | |
| Tue Nov 10 | LUMPI `C1` build; X1 and F2 code; increment 5 if adopted | |
| **Wed Nov 11** | | **Upload 3: `C1`, both tracks** (rules 10 and 13) |
| Thu Nov 12 to Fri Nov 13 | wave 2: partners of whatever passed; training stops **Nov 13, 18:00** | |
| **Sat Nov 14** | `C2` builds, kit checks, reproduction dry runs | **Upload 4: `C2`, both tracks** |
| **Sun Nov 15 to Mon Nov 16 04:59** | report | **Upload 5 (reserve):** re-upload the best scored clean version if `C2` scored lower (rule 13) |

### 15.9 Rule added with the leaderboard reading

13. **The last upload counts until the organizers say otherwise.** A version is uploaded only if its projection beats the best scored clean version (rule 10). If an upload scores below that version, the reserve upload re-submits the best scored clean zip unchanged before the close. The last upload of each track must be our best scored clean zip.

### 15.10 Wave 1 results so far (2026-11-08, to 23:40 UTC)

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
| V2X | `voxelrcnn-ros-g1v6d5` (`voxelrcnn-ros-g1v6`) | draw 5 | vehicle +0.013 / +0.0092 8v | truck plain -0.047 (B -0.095, P 0.00); pedestrian B -0.009 / -0.010 8v | bag partner |
| V2X | `voxelrcnn-ros-swa-g1v6d5` (`voxelrcnn-ros-g1v6d5`) | SWA | vehicle +0.0053 / +0.0046 8v, truck +0.010 plain | truck 8v -0.0039 (P 0.02) | bag partner |
| V2X | `bag-voxelrcnn-ros-g1v6x5` (`bag-voxelrcnn-ros-g1v6x4`) | 5-draw bag | **truck +0.0155 / +0.0088 8v**, vehicle +0.0037 / +0.0016 8v | pedestrian flat (P 0.30-0.81) | truck and vehicle candidate; the 5th draw adds truck, not pedestrian |
| V2X | **`bag-voxelrcnn-ros-swa-g1v6x5`** (`bag-voxelrcnn-ros-g1v6x5`; `bag-voxelrcnn-ros-swa-g1v6x4`) | bag of averaged draws 1-5 | vs plain x5: vehicle +0.0040 / +0.0017 8v, truck +0.0034 plain; vs averaged x4: vehicle +0.0048 plain, **truck +0.012 / +0.0068 8v**, pedestrian 8v +0.0018 | none (truck 8v flat vs plain x5) | the best Voxel R-CNN bag (A/B mean 0.682 plain, 0.694 8v; truck 8v A 0.884, B 0.833); `C1` candidate (12-view queued) |
| V2X | `pvrcnnpp-ros-g1v6d4` (`pvrcnnpp-ros-g1v6`) | draw 4 | vehicle +0.025 / +0.024 8v | pedestrian -0.005 / -0.004 8v (P 0.05), truck 8v -0.014 | bag partner |
| V2X | `bag-pvrcnnpp-ros-g1v6x4` (`bag-pvrcnnpp-ros-g1v6x3`) | 4-draw bag | vehicle +0.010 / +0.0046 8v, pedestrian +0.0032 plain | pedestrian 8v flat, truck 8v -0.0039 (P 0.09) | vehicle; **returns falling** (draw 3 added +0.020 vehicle) |
| V2X | `pvrcnnpp-ros-swa-g1v6d4` (`pvrcnnpp-ros-g1v6d4`) | SWA | vehicle +0.0044, truck 8v +0.0068 | truck plain -0.041 (B -0.052) | bag partner |
| V2X | **`bag-pvrcnnpp-ros-swa-g1v6x4`** (`bag-pvrcnnpp-ros-g1v6x4`, the plain 4-draw bag) | bag of averaged draws 1-4 | **pedestrian +0.0026 / +0.0057 8v** (P 1.00), truck +0.0028 plain | none | **lead V2X PV-RCNN++ pedestrian candidate** for `C1` |
| V2X | `pvrcnnpp-ros-g1v6d5` (`pvrcnnpp-ros-g1v6`) | draw 5 | vehicle +0.015 / +0.015 8v | truck -0.038 / -0.011 8v, pedestrian flat | bag partner |
| V2X | `pvrcnnpp-ros-swa-g1v6d5` (`pvrcnnpp-ros-g1v6d5`) | SWA | vehicle 8v +0.0027 | truck -0.020 plain | bag partner |
| V2X | `bag-pvrcnnpp-ros-g1v6x5` (`bag-pvrcnnpp-ros-g1v6x4`) | 5-draw bag | pedestrian +0.0028 / +0.0035 8v, vehicle 8v +0.0019 | truck plain -0.0036 (n.s.) | small gains: **PV-RCNN++ saturates at 5 draws** (no draw 6) |
| V2X | `bag-pvrcnnpp-ros-swa-g1v6x5` (`bag-pvrcnnpp-ros-g1v6x5`; `bag-pvrcnnpp-ros-swa-g1v6x4`) | bag of averaged draws 1-5 | vs plain x5: pedestrian 8v +0.0026; vs averaged x4: vehicle +0.0034 / +0.0023 8v, pedestrian +0.0021 plain | vs averaged x4: truck plain -0.011 | `C1` pedestrian and vehicle candidate (12-view queued) |
| V2X | `voxelnext-ros-g1v6d4` (`voxelnext-ros-g1v6`) | draw 4 | pedestrian +0.063 / +0.022 8v, truck +0.080 / +0.050 8v | vehicle -0.0036 / -0.0029 8v (n.s.) | bag partner (VoxelNeXt draw 1 is the weak draw) |
| V2X | **`bag-voxelnext-ros-g1v6x4`** (`bag-voxelnext-ros-g1v6x3`) | 4-draw bag | **all six**: vehicle +0.0037 / +0.0020 8v, pedestrian +0.0073 / +0.0073 8v, truck +0.022 / +0.015 8v | none | `C1` candidate; **VoxelNeXt still gains from a 4th draw** (draw 5 is queued) |
| V2X | `voxelnext-ros-swa-g1v6` (`voxelnext-ros-g1v6`) | SWA | pedestrian 8v +0.0034, truck 8v +0.0038 | vehicle plain -0.0062 (B -0.020) | bag partner |
| V2X | `voxelnext-ros-swa-g1v6d2` (`voxelnext-ros-g1v6d2`) | SWA | vehicle +0.0071 / +0.0069 8v, pedestrian +0.0050 / +0.0041 8v | truck plain -0.0082 (P 0.04) | bag partner |
| V2X | `voxelnext-ros-swa-g1v6d3` (`voxelnext-ros-g1v6d3`) | SWA | vehicle plain, truck 8v +0.0093 | pedestrian -0.0056 / -0.0045 8v (P 0.00) | bag partner; the bag of averaged draws 1-4 follows draw 4's averaging |
| V2X | `voxelnext-ros-swa-g1v6d4` (`voxelnext-ros-g1v6d4`) | SWA | vehicle +0.014 / +0.012 8v, truck +0.014 plain | pedestrian 8v -0.0024 (P 0.01, B -0.006) | bag partner |
| V2X | `bag-voxelnext-ros-swa-g1v6x4` (`bag-voxelnext-ros-g1v6x4`, the plain 4-draw bag) | bag of averaged draws 1-4 | vehicle +0.0028 plain, pedestrian +0.0024 plain, truck +0.0097 / +0.0038 8v | vehicle and pedestrian 8v flat (P 0.81-0.83) | truck candidate (A/B mean 0.635 plain, 0.648 8v) |
| V2X | `voxelnext-ros-g1v6d5` (`voxelnext-ros-g1v6`) | draw 5 | vehicle +0.011 / +0.015 8v, pedestrian +0.0055 plain | truck plain -0.143 (P 0.00), pedestrian 8v -0.032 | bag partner |
| V2X | `voxelnext-ros-swa-g1v6d5` (`voxelnext-ros-g1v6d5`) | SWA | truck +0.076 / +0.032 8v | none | bag partner (averaging repairs draw 5's truck) |
| V2X | `bag-voxelnext-ros-g1v6x5` (`bag-voxelnext-ros-g1v6x4`) | 5-draw bag | vehicle +0.0074 / +0.0045 8v | pedestrian -0.0027 / -0.0028 8v (P 0.01), truck plain B -0.005 | vehicle still gains; pedestrian has saturated |
| V2X | **`bag-voxelnext-ros-swa-g1v6x5`** (`bag-voxelnext-ros-g1v6x5`; `bag-voxelnext-ros-swa-g1v6x4`) | bag of averaged draws 1-5 | vs plain x5: **all six** (vehicle +0.0022 / +0.0028 8v, pedestrian +0.0052 / +0.0019 8v, truck +0.015 / +0.0058 8v); vs averaged x4: vehicle +0.0068 / +0.0060 8v, truck 8v +0.0064 | vs averaged x4: pedestrian 8v -0.0018 (P 0.04) | the best VoxelNeXt bag (A/B mean 0.637 plain, 0.651 8v; averaged x4 0.635 / 0.648); `C1` candidate (12-view queued) |
| V2X | `voxelrcnn-ros-gblobs-g1v6` (`voxelrcnn-ros-g1v6`) | D3: GBlobs cell covariance (S5 run c on `g1-v6`) | vehicle plain +0.021 (A +0.032, **B -0.005**, at the rule's limit) | pedestrian -0.049 / -0.054 8v, truck -0.035 / -0.010 8v, vehicle 8v B -0.008 (all fail) | as in S5: weak alone, a vehicle fusion-diversity candidate; a pass by the letter of rule 4 |
| V2X | `voxelrcnn-ros-gblobs-swa-g1v6` (`voxelrcnn-ros-gblobs-g1v6`) | D3 SWA | vehicle +0.0046 / +0.0035 8v, pedestrian +0.0022 plain | truck -0.0069 / -0.0054 8v | vehicle fusion candidate (12-view queued) |
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
| LUMPI | `voxelrcnn-rosf-g1v6d4` (`voxelrcnn-rosf-g1v6`) | draw 4 | 8 of 14: Person +0.014 / +0.011 8v, Bicycle +0.015 / +0.011 8v, Car 8v +0.0145, Bus 8v, Van | Truck -0.013 / -0.0045 8v, Car plain -0.0052, Bus plain -0.006 (all P <= 0.03) | bag partner (a strong Person draw, unlike `rosn` draw 4) |
| LUMPI | `voxelrcnn-rosf-swa-g1v6d4` (`voxelrcnn-rosf-g1v6d4`) | SWA | Person +0.0058 / +0.0066 8v, Car plain, Bicycle +0.010 / +0.0085 8v | Van 8v -0.0019 (P 0.00) | bag partner |
| LUMPI | `bag-voxelrcnn-rosf-g1v6x4` (`bag-voxelrcnn-rosf-g1v6x3`) | 4-draw bag | 9 of 14: Person +0.0020 / +0.0072 8v, Car +0.0017 plain, Bicycle +0.0050 / +0.0038 8v, Bus, Truck +0.0030 plain, Van | none (Car 8v flat) | Car and Bicycle candidate; the 4th `rosf` draw still gains |
| LUMPI | **`bag-voxelrcnn-rosf-swa-g1v6x4`** (`bag-voxelrcnn-rosf-g1v6x4`; `bag-voxelrcnn-rosf-swa-g1v6x3`) | bag of averaged draws 1-4 | vs averaged x3: Person +0.0036 / **+0.0052 8v**, Car +0.0050 plain, Bicycle +0.0084 / +0.0023 8v, Car 8v, Van 8v; vs plain x4: Bicycle +0.012 / +0.0094 8v, Person 8v +0.0052, Bus 8v, Truck plain | vs plain x4: Car plain -0.0010, Van 8v -0.0013 (P <= 0.01) | **lead LUMPI Person candidate: B Person 8v 0.240** (`C0` fused 0.232; averaged x3 0.236); 12-view queued |
| LUMPI | `voxelrcnn-rosn-g1v6d5` (`voxelrcnn-rosn-g1v6`) | draw 5 | Bicycle +0.062 / +0.048 8v, Bus, Van +0.010 / +0.0072 8v | **Person -0.022 / -0.016 8v**, Truck -0.020 / -0.023 8v, Car -0.0044 / -0.0030 8v (all P 0.00) | bag partner (a weak Person draw, as draw 4) |
| LUMPI | `voxelrcnn-rosn-swa-g1v6d5` (`voxelrcnn-rosn-g1v6d5`) | SWA | Person +0.0052 plain, Car +0.0015 / +0.0042 8v | Van -0.0056 / -0.0040 8v (P 0.00) | bag partner |
| LUMPI | `bag-voxelrcnn-rosn-g1v6x5` (`bag-voxelrcnn-rosn-g1v6x4`) | 5-draw bag | Bicycle +0.012 / +0.0059 8v, Motorcycle +0.0043 plain, Van | **Truck -0.0057 / -0.0047 8v (P 0.00)**; Person and Car flat | **`rosn` saturates at 5 draws** (Bicycle and Van only) |
| LUMPI | `bag-voxelrcnn-rosn-swa-g1v6x5` (`bag-voxelrcnn-rosn-g1v6x5`; `bag-voxelrcnn-rosn-swa-g1v6x4`) | bag of averaged draws 1-5 | vs plain x5: Person +0.0018 / +0.0016 8v, Car, Bicycle; vs averaged x4: Car +0.0012 / +0.0007 8v, Bicycle +0.0105 / +0.0067 8v, Van | vs averaged x4: Truck -0.0039 / -0.0045 8v, Person 8v -0.0013 (P <= 0.01) | Bicycle and Car fusion candidate; Person B 8v 0.226 (`rosf` averaged x4: 0.240) |
| LUMPI | `voxelrcnn-rosf-g1v6d5` (`voxelrcnn-rosf-g1v6`) | draw 5 | Person +0.017 / +0.0069 8v, Bicycle +0.030 / +0.022 8v, Car 8v +0.013 | Truck -0.024 / -0.016 8v, Bus plain -0.0078, Car plain -0.0066, Van (all P 0.00-0.01) | bag partner |
| LUMPI | `voxelrcnn-rosf-swa-g1v6d5` (`voxelrcnn-rosf-g1v6d5`) | SWA | Bicycle +0.016 / +0.013 8v, Car, Van | Person 8v -0.0091, Truck 8v -0.0085 (P 0.00) | bag partner |
| LUMPI | `bag-voxelrcnn-rosf-g1v6x5` (`bag-voxelrcnn-rosf-g1v6x4`) | 5-draw bag | Person +0.0035 plain, Bicycle +0.0092 / +0.0043 8v | Person 8v -0.0016, Bus and Van (all under 0.002, P <= 0.03) | **`rosf` saturates at 5 draws** |
| LUMPI | `bag-voxelrcnn-rosf-swa-g1v6x5` (`bag-voxelrcnn-rosf-g1v6x5`; `bag-voxelrcnn-rosf-swa-g1v6x4`) | bag of averaged draws 1-5 | vs plain x5: Person +0.0033 / +0.0045 8v, Bicycle +0.011 / +0.012 8v, Bus 8v; vs averaged x4: Person +0.0047 plain, Car, Bicycle +0.0079 / +0.0070 8v, Motorcycle plain | vs averaged x4: **Person 8v -0.0023 (P 0.03)**, Truck -0.0018 / -0.0024 8v | Person B 8v 0.238 against the averaged x4's 0.240: **the averaged 4-draw bag stays the lead Person candidate** |
| LUMPI | **`voxelrcnn-rosf-gblobs-g1v6`** (`voxelrcnn-rosf-g1v6`) | D3: GBlobs cell covariance (S5 run c on `g1-v6`) | **7 of 14**: Bicycle +0.049 / +0.033 8v, **Car 8v +0.0133** (B +0.012), Person 8v +0.0058 (P 0.97), Bus 8v, Van | Car plain -0.009, Truck 8v -0.0145, Motorcycle | much stronger than S5's run a (object scaling and the clean corpus); D3 rule met: draws 2-3 train next |
| LUMPI | `voxelrcnn-rosf-gblobs-swa-g1v6` (`voxelrcnn-rosf-gblobs-g1v6`; `voxelrcnn-rosf-swa-g1v6`) | D3 SWA | vs plain GBlobs, 6 of 14: Person +0.0098 / +0.0035 8v, Car +0.0013, Bicycle +0.012 / +0.0054 8v, Truck 8v +0.0056; vs averaged xyz: Bicycle +0.049 / +0.026 8v, Van +0.0033 / +0.0033 8v | vs averaged xyz: Car -0.005 / -0.003 8v, Motorcycle 8v -0.016, Truck 8v -0.0085; Person 8v +0.0028 (P 0.81) | Bicycle and Van candidate; Person fusion partner (12-view queued) |

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

### 15.11 An outside review, checked (2026-11-08, 21:00-22:00 UTC)

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

### 15.12 Rule 14 adopted: the grouped final gate, with a margin (2026-11-09, about 00:30 UTC)

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

### 15.13 Final-week research review (2026-11-09, 13:40-14:15 UTC; the entrant's board screenshots of 07:39-07:40 CST, server time UTC-6)

The entrant asked for a deep review of the scores and the competitors' gains, a research scan of the community's synthesis and detection stacks beyond OpenPCDet and CARLA frames, a few plans that can be added to S10 one increment at a time within the rules, and a nuanced assessment. Two read-only literature scans ran in parallel (nothing was downloaded or installed), and six local measurements were made on legal frames and validation outputs only.

#### 15.13.1 The board, decomposed with our scorer

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

#### 15.13.2 New measurements (2026-11-09; legal frames and validation only)

| Probe | Result | Verdict |
|---|---|---|
| **Ground height** (`scratchpad/s10/research/terrain_bound.py`): the synthetic ground moved to the real per-cell ground (1 m cells, lowest 5%, fitted on unlabelled proxies 1-3, scored on held-out 4-5, exact scorer) | Our LUMPI ground is flat at z -2.15 m (5th, 25th and 50th percentiles); the real ground spans -2.37 / -2.08 / -1.95 m (5th / 50th / 75th). The correction moves LUMPI EMD by -0.005 and R by +0.0002-0.0003; V2X EMD by -0.003 to -0.006, R +0.0000, CD +0.02-0.05 | **Dropped.** The ground error is real, but it is not what EMD sees (as S9's ground bowl showed). A ray-consistent version would move ring radii too, but the vertical bound leaves little room |
| **Ring audit** (`ring_audit.py`): each Measurement4 lidar's points in its metadata frame, residual to the beam table | The merged frames mix five lidars, so nearest-sensor assignment contaminates every sensor. The cleanest one (Pandar64, 0.171 deg spacing) has a real residual of 0.035 deg, consistent with the metadata pose | **Inconclusive; not pursued.** No gross pose error is visible. A re-cast of the UrbanTwin background is not possible without the twin assets |
| **Van hedge** (`van_probe.py`): low-score Van copies of large Car boxes on the `C0` predictions | Van AP A 0.108 -> 0.070-0.112, B 0.0012 -> 0.0009-0.0010 | **Dropped.** The real vans on B are not found as Car boxes either. Van has no inference lever, and the email needs no hedge question |
| **Person centroid shift** (`person_probe.py`, lever 1 of the detection scan): xy moved toward the interior-point centroid, blend 0.25 / 0.5 / 1.0 | LUMPI Person A -0.006 / -0.014 / -0.037, B -0.003 / -0.005 / -0.020; V2X pedestrian A -0.006 / -0.022 / -0.081, B -0.003 / -0.016 / -0.059 | **Dropped.** Our fused, calibrated boxes are already better centred than the visible-surface centroid, which is biased toward the sensor |
| **Point-count rescoring** (score x (n+1)^beta) | beta 0.1: LUMPI Person A +0.0011, B +0.0055; V2X pedestrian A +0.0034, B -0.0021. beta 0.25 and 0.5 lose | **A small candidate (LUMPI Person only)** under the class gate in `C1`; a post-processing change, so transfer 0.2-0.6x: about +0.0002 combined |
| **Static gap** (`static_gap.py`, R1 diagnostic): persistent above-ground occupancy (0.5 m cells, occupied in at least 60% of 300 unlabelled legal frames; no label read) against the same in 300 UrbanTwin frames (occupied in at least 30%) | LUMPI: **34.9% of the real above-ground static mass, 9.5% of all points**, lies in 868 static cells (211 clusters) where the twin has no geometry. V2X: 38.1%, 9.2% (579 cells, 171 clusters). Vehicle-sized static clusters (parked cars, excluded from any use) are 1.2% (LUMPI) and 0.5% (V2X) of the points | **R1 has the headroom to explain most of our EMD excess** (moving 9% of the mass 3-5 m is 0.27-0.45 m of W1, against our 0.43-0.48 excess). It also bears on detection: 65% of the confident V2X pedestrian false positives sit on static structures (14.1). The email's question (c) gates both |
| **`C1` rehearsal** (`routed-c1a`, LUMPI): `C0`'s 33 member folders plus the 27 tuned wave 1-3 candidates, the `C0` pipeline | running since 14:02 UTC | gives the measured projection of increment D1 below |

#### 15.13.3 The research scan, in brief (two read-only scans; links in the scan reports, numbers as reported, "unverified" where not checked)

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

#### 15.13.4 The plans (increments that can be added one at a time)

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

#### 15.13.5 Assessment and alignment

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

#### 15.13.6 Adopted (the entrant, 2026-11-09, about 14:20 UTC: "Adopt, allow GBlobs")

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

#### 15.13.7 The C1 dry runs (2026-11-09, 14:00-18:40 UTC)

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

#### 15.13.8 Wave 5 options (proposed 2026-11-09, 23:30 UTC; the entrant chooses; B runs by default at 18:00 UTC Nov 10)

**Capacity.** The train queue drains at about 06:30 (trainA) and 07:50 UTC (trainB) on Nov 10. The 12-view queue (39 jobs) then runs until about 10:30-11:00, and the staged GBlobs draws 2-3 (both tracks) until about 19:00. From then until the Nov 13 18:00 stop, two trainers have about 71 hours each, room for 35-40 members at 3-4.3 h each. Ideas with positive expected value, not GPU time, are the limit.

| Option | Members (each with its SWA average and 12-view tuning) | Expected value | Rule alignment | Risk |
|---|---|---|---|---|
| **A. Balanced depth** | LUMPI GBlobs draws 4-5; LUMPI PV-RCNN++ draws 4-5 (its averaged draw 3 gained Person +0.017); V2X VoxelNeXt draw 6 (new corpus `g1-v6d6`, seed 6234) | LUMPI +0.0005 to +0.0015 combined (fusion members); V2X +0.0005 to +0.0015 (VoxelNeXt truck and pedestrian) | D1 depth; D3; the wave 3 draw-6 rule (VoxelNeXt still gains on all six) | low; about 6 members, the rest of the capacity idle |
| **B. A plus a LUMPI push (recommended)** | A, plus GBlobs probes on the LUMPI Voxel R-CNN `rosn` and PV-RCNN++ configs (rule 4 against their xyz siblings), then draws 2-3 of each probe that passes | LUMPI +0.001 to +0.003 if a probe passes as `rosf` did; LUMPI needs +0.0032 combined (about +0.0037 mean mAP) to pass the board leader without R1 | within the GBlobs permission (D3); new member types enter only through rule 4 | a probe can fail (S5 GBlobs alone was weak); PV-RCNN++ with GBlobs is untested (30-iteration smoke test first) |
| **C. Only what is already authorized** | the staged GBlobs draws 2-3 and VoxelNeXt draw 6 | V2X +0.0005 to +0.0015 | wave 3 rule only | GPUs idle for most of Nov 11-13 |

**In plain terms** (added 2026-11-10 at the entrant's request). The choice is what the two trainers train from about 19:00 UTC Nov 10, when the staged GBlobs draws 2-3 finish, to the Nov 13 18:00 stop. It feeds `C2` (upload 4) only; `C1` (upload 3) uses members trained before then. A trains more draws of members that already gain. B adds to A one GBlobs test on each of two more LUMPI detectors, with draws 2-3 only for a test that passes. C trains nothing new. In every option a new member passes rule 4 before it is used, and `C2` passes R3 and rule 14, so a member that does not help on validation is filtered out; the options differ in how much the `C2` pool can gain, and in GPU hours left idle (A uses about 25 of about 142 trainer hours, B about 45, C about 4).

#### 15.13.9 Wave 5: option B adopted (the entrant, 2026-11-10, about 00:40 UTC: "Option B")

- **Members** (`w5_option_b.sh`; each passes rule 1 before it is queued; training seed 666):
  - **probes, draw 1:** LUMPI `voxelrcnn-rosn-gblobs-g1v6` (rule 4 against `voxelrcnn-rosn-g1v6`) and `pvrcnnpp-ros-gblobs-g1v6` (rule 4 against `pvrcnnpp-ros-g1v6`, after a 30-iteration smoke test, since PV-RCNN++ has not run with GBlobs). Both take the parent configs with `GBlobsCellVFE`, as `voxelrcnn-rosf-gblobs-g1v6`;
  - **part A:** LUMPI `voxelrcnn-rosf-gblobs-g1v6` draws 4-5, LUMPI `pvrcnnpp-ros-g1v6` draws 4-5, V2X `voxelnext-ros-g1v6` draw 6 (new corpus `g1-v6d6`, seed 6234, the wave 3 V2X flags, no R1 anchors).
- **Order.** The probes go first in the staged wave, so their checks arrive about 4 hours sooner and leave time for their draws. Then the staged GBlobs draws 2-3 (both tracks), then part A.
- **The probe rule (as D3).** A probe that passes a class in rule 4 gets draws 2-3 (`g1-v6d2`, `g1-v6d3`) before the Nov 13 stop, for a bag in `C2`. A probe that passes nothing stops there.
- **After training.** Each member gets its SWA average (epochs 31-40) and the usual 8-view tuning. Members finishing after the 12-view window get their 12-view tuning after the Nov 13 18:00 stop.
- **Expected timeline (UTC).** The wave starts when the 12-view queue finishes (about 10:30-11:00 Nov 10). Probes trained by about 15:30 and checked by about 18:30. Staged draws by about 23:30. Part A by about 09:30 Nov 11. Probe draws, if any, by about 18:00 Nov 11. That uses about 45 of about 142 trainer hours; the rest stays free for whatever the checks show.
- **Check-in (2026-11-10, 04:40 UTC): the queued draws still earn their place.**
  - **V2X VoxelNeXt draw 6 stays queued.** The 5-draw bag still gains vehicle over the 4-draw bag: +0.0074 plain, +0.0045 8v. The averaged 5-draw bag gains +0.0068 / +0.0060 8v over the averaged 4-draw bag. Pedestrian has saturated (-0.0027 plain, -0.0028 8v). Draw 6 therefore serves vehicle and truck only. The expected gain is about +0.003 vehicle AP, so about +0.001 combined if VoxelNeXt carries vehicle in a route.
  - **LUMPI `rosf` draw 5 stays queued.** The 4th `rosf` draw still gains 9 of 14 checks (none lost). The averaged 4-draw bag reaches B Person 8v 0.240, the best clean LUMPI Person so far (`C0` fused 0.232). Draw 5 was the last member of the wave 3 queue. It trained on trainB from 05:22 to 09:57 UTC Nov 10. Its 8-view tuning ends after the 12-view window, so its 12-view tuning follows the Nov 13 stop: `C1` uses the averaged 4-draw bag at 12 views, and the 5-draw bags at 8 views.


### 15.14 The organizers' answers (2026-11-09, 22:24 CST; the entrant's copy, 2026-11-10) and what they change

**The answers** (Muhammad Shahbaz, for the organizers):
- **Disclosure.** Placing inserted objects at the position, heading and size of real labels used real annotations, which the sim-only rule does not allow; the organizers note that we reported and stopped it ourselves. **KarmaRV is ranked only by LUMPI 1042287 and V2X 1042294 onward.** The earlier final-phase submissions are removed from the boards but still count toward the submission limit. The report must describe the change.
- **Every other listed use of real data is allowed**, as long as none of the 100 forbidden frames is involved; the report must list them all:
  - validation and model selection on non-forbidden frames, including frames of the public V2X val and test splits;
  - label statistics (box-size distributions, the distance histogram), in the generator and in the test-time size calibration;
  - realism calibration from unlabelled real clouds, including choosing the 50 submitted frames;
  - test-time post-processing of the detector's own outputs: augmentation, box fusion, score adjustment, low-score duplicate boxes.
- **(a) Each team's best submission counts**; the board shows it automatically (for us, only from 1042287 / 1042294).
- **(b) Yes:** the walker-distance histogram is a label statistic.
- **(c) Yes:** static structures may be located in unlabelled, non-forbidden real frames and our own synthetic geometry added there, as long as no real points are copied; describe it in the report.
- **(d)** The board shows the highest-scoring entry and cannot be chosen; the earlier entries will be removed, so it shows our best clean entry per track.

**What changes.**
1. **Uploads left: three per track** (five, less `s9j`/`s9f` and `C0`), at most one a day per track. The close is **V2X 2026-11-15 04:59 UTC and LUMPI 2026-11-16 04:59 UTC** (the header of this record). `docs/01` gives 2026-11-15 00:00 UTC for both, so the plan keeps every V2X upload on Nov 14 UTC or earlier.
2. **Rule 13 is retired.** A lower score no longer replaces a better one, nothing has to be re-uploaded, and slot 5 carries a new candidate.
3. **Rule 14 becomes a slot rule** (proposed, 15.14.2). Each upload still needs rule 1, projection > 0 against the best scored clean version, and the audit rules. The grouped gate and the history margin now decide which candidate gets each of the three slots, instead of protecting the ranking.
4. **R1 (twin completion) is allowed.** The organizers' answer supersedes, for this use, the `docs/01` row "Generator fitted to real scans ... structure positions read off real points". The anchors meet the answer's terms:
   - no label is read;
   - the 300 anchor frames per track come from the guarded realval build (0 forbidden frames, checked again on 2026-11-10);
   - the generator ray-casts its own synthetic blocks there;
   - no real point is copied.

   **One fix, made first.** 30-38% of the held-out proxy frames (proxies 4-5) were among the v1 anchor frames. The v2 anchors (`gen/static_anchors_r1_v2.json`: LUMPI 215, V2X 175) exclude all 250 proxy frames, as the density prior already does, so held-out R stays honest. `clean_check.py` keeps the interlock: an R1 corpus needs `BDC_ALLOW_R1=1`, now set deliberately for R1 corpora only.
5. **(b) closes the moderate-risk walker row of the compliance audit.** The generator does not change.
6. **Every test-time stage in use is confirmed:** TTA, fusion, the size calibration, low-score duplicate copies, D2 point-count rescoring and V5 overhead demotion. D2 and V5 also read the input frame's points; the report lists them as test-time post-processing of our detector's outputs.
7. **The report gains three items:**
   - the change (label-placed walkers until Nov 2; ranked from 1042287 / 1042294);
   - the full list of real-data uses;
   - R1, if it is used.

#### 15.14.1 R1.0, started at once (no-regret, CPU only, 2026-11-10 13:41 UTC)

The pre-registered decision was "prepare, use only on a yes (in `C2` if the answer arrives by Nov 12)". The answer arrived on Nov 10, so the measurement started without changing the train queue (`r1_probe.sh`):
- **Corpora `g1-v6r1`** per track: the draw 1 recipe and seed (1234) plus the v2 anchors, so R1 is the only change against `pcdet/g1-v6`. Then infos and GT databases, ready for training.
- **The realism gate (S9 rule 4):** the same 50-frame selection on both pools (val split, fit proxies 1-3, held-out 4-5, `fpd+emd`, seed 1234). R1 passes if held-out R gains at least 0.003 with CD, MMD and FPD not worse, and V2X CD stays below 2.0. The `C0` scored frames are scored on proxies 4-5 as the reference.
- **History for the reading:** LUMPI realism-frame gains transferred to the server at 0.35x (S9); V2X frames at about 1x.

#### 15.14.2 Options (for the entrant)

**Training from about 22:30 UTC Nov 10** (when the GBlobs probes and the staged GBlobs draws 2-3 finish) **to the Nov 13 18:00 stop**, about 2 x 43 trainer hours:

| Option | What | Pros | Cons | Expected server gain (combined) | Rules |
|---|---|---|---|---|---|
| **1. R1 now (recommended)** | R1.1: one member per track on `g1-v6r1` ahead of part A (LUMPI `voxelrcnn-rosf`, the Person lead; V2X `voxelrcnn-ros`), each with its SWA average; rule 4 against draw 1, and the bag with draws 1-5 against the 5-draw bag. R1.2: if R1.1 passes a class, R1 draws 2-3 (new seeds) for `C2` bags. Part A (GBlobs d4-d5, PV d4-d5, VoxelNeXt d6) follows | the largest lever left on both tracks; it touches realism (our weakest term) and detection (65% of confident V2X pedestrian false positives sit on static structures, 14.1); anchors and code are ready | displaces part A by about 9 hours (part A adds about +0.001: the `rosf`, `rosn` and PV-RCNN++ bags have saturated); LUMPI realism transfer has been 0.35x | LUMPI +0.001 to +0.004; V2X +0.002 to +0.006 (realism and detection together; R1.0 replaces the realism part with a measurement) | allowed by (c); in the report |
| 2. R1 after part A | the same members, from about 12:30 UTC Nov 11 | no change to the running order | R1.2 draws may not fit before the stop; `C2` gets one R1 member per track at most | about half of option 1 | same |
| 3. No R1 | wave 5 option B as queued | nothing new to report | leaves the largest LUMPI lever unused while LUMPI is 0.0032 behind | 0 | none |

**If R1.0 fails the realism gate,** option 1 still trains the two R1.1 members once, for the detection effect; R1 stops there if they also fail rule 4. **If R1.1 members are used** (a bag or a route class), the R1 frames may be submitted (rule 6: the realism frames come from a corpus that trains a used member).

**Uploads (three slots per track; best counts):**

| Slot | V2X (closes Nov 15 04:59 UTC; plan to Nov 14 UTC) | LUMPI (closes Nov 16 04:59 UTC) |
|---|---|---|
| 3 | **Nov 11: `C1`** (12-view bags, V5, R2; fallback `c1av5`) | **Nov 11: `C1`** if its projection against `C0` is at least +0.001 (the board noise is about ±0.0015); otherwise held for a later candidate |
| 4 | **Nov 12-13: `C1r`**: `C1` plus the R1.1 members and R1 frames, if R1 passes (else held) | **Nov 13-14: `C2a`** (R1.1 members and frames if they pass, wave 5 members tuned by then) |
| 5 | **Nov 14: `C2`** (everything trained by the stop) | **Nov 15: `C2`** |

- **Slot rule (proposed rule 14b):** each slot goes to the candidate with the highest projection that passes rule 1 and the grouped gate's direction (grouped P >= 0.8), with no fixed margin, because a lower score now costs only the slot. Two consecutive uploads should differ in more than tuning noise; a best-of on correlated candidates adds little.
- **History.** Small detection changes scored within ±0.0015 of their projection (`s9c` -0.0004 at grouped P 0.98). Ensemble changes transferred at about 1x, post-processing at 0.2-0.6x, and LUMPI realism frames at 0.35x.

**Default.** If the entrant has not chosen by 22:00 UTC Nov 10, when the first R1.1 member would start, option 1 runs. It changes only the order of the queued members.

#### 15.14.3 Option 1 adopted (the entrant, 2026-11-10, about 14:35 UTC: "Adopt option 1")

- **R1.1 members** (both CLEAN with `BDC_ALLOW_R1=1`; the interlock still fails them without it):
  - LUMPI `voxelrcnn-rosf-g1v6r1`: the `voxelrcnn-rosf-g1v6` configs on `pcdet/g1-v6r1`;
  - V2X `voxelrcnn-ros-g1v6r1`: the `voxelrcnn-ros-g1v6` configs on `pcdet/g1-v6r1`;
  - training seed 666.
- **Queue.** Both follow the GBlobs draws 2-3 and come ahead of part A. They start at about 22:30 UTC Nov 10 and finish at about 03:00 UTC Nov 11. Part A follows, ending at about 21:00 UTC Nov 11.
- **After training.** Each member gets its SWA average and the 8-view tuning, then two checks: rule 4 against draw 1, and the bag of draws 1-5 plus R1 against the 5-draw bag. R1.2 (R1 draws 2-3, new generator seeds) is queued only if R1.1 passes a class.
- **Builds.** A portfolio build that includes an R1 member (`C1r`, `C2a`, `C2`) runs with `BDC_ALLOW_R1=1`. Its card and the report name R1.
- **Tool text updated.** "Grey zone" was replaced by the ruling in `clean_check.py`, `prepare_g1.py` (both tracks) and `g2.py`. The S10 tests pass (14).

#### 15.14.4 The R1.0 gate result and the mass calibration (2026-11-10, 15:42-16:01 UTC)

**R1.0 result.** 50 frames from the val pool, fit on proxies 1-3, held out on 4-5 (`$BDC_DATA/logs/s10/r1/`):

| Track | Frames | Fit objective (EMD/5 + FPD/50) | R proxy 4 / 5 | Mean R | CD | MMD | EMD | FPD |
|---|---|---|---|---|---|---|---|---|
| V2X | `g1-v6` | 0.2128 | 0.9315 / 0.9325 | 0.9320 | 1.85 / 1.85 | 0.0009 / 0.0009 | 1.215 / 1.209 | 1.46 / 1.32 |
| V2X | `g1-v6r1` | 0.2297 | 0.9327 / 0.9358 | 0.9343 (+0.0022) | 1.93 / 1.96 | 0.0006 / 0.0005 | 1.222 / 1.180 | 1.17 / 0.99 |
| V2X | `C0` frames (`g1-v6`, train+val pool) | | 0.9415 / 0.9437 | 0.9426 | 1.83 / 1.80 | 0.0004 / 0.0004 | 1.114 / 1.082 | 0.52 / 0.40 |
| LUMPI | `g1-v6` | 0.1910 | 0.9376 / 0.9361 | 0.9369 | 1.49 / 1.47 | 0.0000 / 0.0001 | 1.212 / 1.234 | 0.35 / 0.43 |
| LUMPI | `g1-v6r1` | 0.5574 | 0.8725 / 0.8706 | 0.8716 (-0.0653) | 1.94 / 1.91 | 0.0033 / 0.0033 | 1.902 / 1.906 | 6.16 / 6.50 |
| LUMPI | `C0` frames (`g1-v6`, train+val pool) | | 0.9404 / 0.9394 | 0.9399 | 1.48 / 1.47 | 0.0000 / 0.0000 | 1.180 / 1.201 | 0.12 / 0.12 |

- **Verdict (S9 rule 4): both tracks fail.** V2X gains +0.0022, below the 0.003 gate, and its CD worsens from 1.85 to 1.95 (still below 2.0). LUMPI loses 0.065 R.
- **The `C0` frames** score above both selections because S9 chose them from the larger train+val pool. Only the like-for-like pair measures R1.
- **Diagnosis.**
  - On LUMPI, the share of points more than about 2 m above the ground (z > 0) is 8.1% in the real proxies, 7.5% in `g1-v6` and 18.5% in `g1-v6r1`.
  - The solid blocks return far more than the real structures. LUMPI blocks return 4.35x the real missing mass (18,900 against 4,390 points per stored frame); V2X blocks return 1.44x (5,600 against 3,920).
  - The anchors are in the right places. But a box or pole returns every ray, while the real structures (trees, fences, signs) are porous.
  - LUMPI: 132 blocks over-return (18,475 points against their 2,146) and 83 return almost nothing.
  - V2X: 39 of the 94 dead anchors have no point in their footprint in `g1-v6`. The synthetic scenes see nothing there, so a block cannot show.
- **The mass calibration** (`s10_static_anchors.py --calibrate`, `g2.thinned_drop`, test `test_calibrated_static_blocks_keep_their_share_of_returns`; 15 tests pass):
  - **Method.** For each anchor, count the points more than 0.3 m above the local ground in its footprint, in the anchored corpus minus the unanchored one: 200 frames, same recipe and seed, the same count the real mass uses. That count estimates the block's returns. An over-returning block keeps the share mass/returns of its rays (floor 0.02); the other blocks are unchanged.
  - **Data used.** Only the anchors' real missing mass, already part of R1, and synthetic frames. No proxy frame is read.
  - **Expected stored returns after:** LUMPI 2,170 (mass 4,390); V2X 1,140 (mass 3,920). The dead anchors cannot be raised.
- **R1.0m** (`r1m_probe.sh`, running since 16:01 UTC, about 1.5 h):
  - corpora `g1-v6r1m`: the R1.0 recipe and seed with the calibrated anchors (`static_anchors_r1_v2m.json`), so the calibration is the only change against `g1-v6r1`;
  - the clean check and a returns check;
  - the realism selection on the val pool (like for like with R1.0) and on the train+val pool (like for like with the `C0` frames);
  - then infos.

**Pre-registered before the R1.0m result:**
1. **The R1.1 corpus per track.** The member trains on `g1-v6r1m` if its fit-proxy objective (val pool) is below `g1-v6r1`'s; otherwise on `g1-v6r1` as queued.
   - This is S9 rule 5: generator choices use proxies 1-3 only, so the held-out proxies 4-5 stay a single judge.
   - The new members `voxelrcnn-rosf-g1v6r1m` and `voxelrcnn-ros-g1v6r1m` take the queued places, with the same configs and training seed. The queue order is unchanged.
2. **R1 frames in a submission.** Only if the R1 member is used (rule 6), and only if the train+val selection on its corpus beats the `C0` frames on proxies 4-5 by at least 0.003 R. CD, MMD and FPD must not be worse, and V2X CD must stay below 2.0. LUMPI frame gains have transferred at 0.35x.
3. **Detection** (15.14.2 stands). The R1.1 members train once for the detection effect, whatever the realism result. R1 stops if they also fail rule 4.
4. **Report.** R1 is described with the calibration: the real data enters only as the per-anchor missing mass from unlabelled, non-forbidden frames.

#### 15.14.5 The R1.0m result (2026-11-10, 17:06 UTC)

After the calibration, stored block returns are 0.73x the real mass on LUMPI (3,209 against 4,391 points per frame) and 0.48x on V2X (1,889 against 3,920), down from 4.35x and 1.44x.

| Track | Frames | Pool | Fit objective | R proxy 4 / 5 | Mean R | CD | FPD |
|---|---|---|---|---|---|---|---|
| LUMPI | `g1-v6` | val | 0.1910 | 0.9376 / 0.9361 | 0.9369 | 1.49 / 1.47 | 0.35 / 0.43 |
| LUMPI | `g1-v6r1` | val | 0.5574 | 0.8725 / 0.8706 | 0.8716 | 1.94 / 1.91 | 6.16 / 6.50 |
| LUMPI | **`g1-v6r1m`** | val | **0.2346** | 0.9306 / 0.9308 | 0.9307 | 1.62 / 1.63 | 0.54 / 0.52 |
| LUMPI | `g1-v6r1m` | train+val | 0.1959 | 0.9365 / 0.9351 | 0.9358 | 1.45 / 1.48 | 0.26 / 0.32 |
| LUMPI | `C0` frames | train+val | | 0.9404 / 0.9394 | 0.9399 | 1.48 / 1.47 | 0.12 / 0.12 |
| V2X | `g1-v6` | val | 0.2128 | 0.9315 / 0.9325 | 0.9320 | 1.85 / 1.85 | 1.46 / 1.32 |
| V2X | `g1-v6r1` | val | 0.2297 | 0.9327 / 0.9358 | 0.9343 | 1.93 / 1.96 | 1.17 / 0.99 |
| V2X | **`g1-v6r1m`** | val | **0.2150** | 0.9308 / 0.9331 | 0.9320 | 2.06 / 2.12 | 1.48 / 1.31 |
| V2X | `g1-v6r1m` | train+val | 0.2043 | 0.9399 / 0.9427 | 0.9413 | 1.92 / 1.94 | 0.81 / 0.69 |
| V2X | `C0` frames | train+val | | 0.9415 / 0.9437 | 0.9426 | 1.83 / 1.80 | 0.52 / 0.40 |

**Applying the rules set in 15.14.4:**
1. **R1.1 corpus: `g1-v6r1m` on both tracks.** Its fit-proxy objective is below `g1-v6r1`'s (LUMPI 0.2346 against 0.5574; V2X 0.2150 against 0.2297).
   - On V2X the held-out proxies disagree: `g1-v6r1` reads 0.9343 against 0.9320. The rule uses the fit proxies, so this does not change the choice, and the two corpora differ there by 0.002 R, within the noise of a 50-frame selection.
   - Queue: `voxelrcnn-rosf-g1v6r1m` and `voxelrcnn-ros-g1v6r1m` took the R1 places under the queue lock (17:08 UTC). The `g1-v6r1` members are marked superseded and are not trained.
2. **R1 frames: none in any submission.** Neither track beats the `C0` frames on the train+val pool: LUMPI 0.9358 against 0.9399 (-0.0041); V2X 0.9413 against 0.9426 (-0.0013), with CD worse.
3. **Detection:** the R1.1 members train once, from about 22:30 UTC, and face rule 4 against draw 1 and the bag check.

**Reading.**
- The calibration removes most of the harm: LUMPI goes from -0.065 to -0.006 against `g1-v6` on the val pool. But no version of R1 improves realism. The anchors fill places the synthetic scenes do not see, and about a third of the anchors cannot show at all.
- The LUMPI realism gap to the board leader (15.13.1) stays open for this phase. R1 is now a detection lever only: static structures as unlabelled negatives, the mechanism that gained Person on LUMPI's structure corpus.
- **Slot plan change (15.14.2):** V2X `C1r` becomes `C1` plus the R1.1 member, and only if that member passes rule 4. Otherwise slot 4 goes to the best candidate by rule 14b.

#### 15.14.6 The `C1` builds and the disk-full stop (2026-11-10)

**Disk full, 17:15-17:40 UTC.** The root volume (7.0 TB; data, repository and temporary files) reached 0 bytes free.
- **Effects:**
  - both `C1` selects failed;
  - both GBlobs probes hung: the TensorBoard writer thread died on the full disk, its queue filled, and rank 0 blocked while the other ranks spun.
- **Recovery, all without deleting anything:**
  - the superseded `g1-v6r1` corpora (12.9 GB, never trained) and the pre-v6 corpora `g1-v1` to `g1-v5*` (89 GB, no S10 member) moved to `/data/workspace/bdc26-overflow` with symlinks; frame counts and clean checks were verified through the links;
  - the probes resumed from their checkpoints (OpenPCDet auto-resume; epochs 38 and 36), and all 10 SWA checkpoints load;
  - both `C1` builds relaunched;
  - `disk_watch.sh` logs an event below 40 GB free.
- **Space left:** `/` had about 92 GB free, enough until about Nov 12.
- **Epoch 1-30 checkpoints deleted** (the entrant, 2026-11-10, about 19:30 UTC: "Yes, delete epochs 1-30"):
  - 2,460 files, 0.437 TB (list: `$BDC_DATA/logs/s10/ckpt_delete_list.txt`); `/` now has 497 GB free;
  - kept: the two members in training (their newest checkpoint is the resume point), three short runs whose last epoch is 30 or lower, and every epoch 31-40 and epoch-40 file;
  - no card, script, release manifest or doc in the repository or data folder named one of the deleted files;
  - checked after: all 165 runs that reached epoch 40 still have it, and the SWA windows (31-40) are intact.

**V2X `routed-c1`** (65 clean folders, 185 members, with the 12-view bags). Against `C0` before the class gate (`gate --vs routed-c0`):

| Class | Route from scratch | Pooled AP | A | B | P(gain) | Gate |
|---|---|---|---|---|---|---|
| vehicle | `bvrrosswa6x4_tta12` | -0.0157 | -0.0139 | -0.0176 | 0.00 | reverted |
| pedestrian | `bvrrosswa6x5_tta12` plus V5 | +0.0024 | +0.0024 | +0.0046 | 0.935 | reverted: route change, below R3's +0.01 bar on B |
| truck | `bvrrosswa6x5_tta12` | +0.0033 | +0.0036 | +0.0045 | 0.99 | reverted: route change, below the bar |

- **Result.** After the gate, `routed-c1` equals `C0`, so rule 14 says NO-GO with a delta of 0. The session stopped the build at packaging, since a copy of `C0` would only spend GPU time.
- **Reading.**
  - The 12-view averaged bags do not beat `C0`'s vehicle fusion (the 12-view 2-draw bag with DSVT). The search from scratch does not reach it, as in the dry run.
  - The new pedestrian route with V5 (+0.0024) gains no more than V5 alone on `C0`'s route (`c1av5`: +0.0027).
  - Truck's +0.0033 (about +0.0009 combined) is the one real candidate, and R3 blocks it, as pre-registered.
- **V2X upload 3 = `c1av5`, the pre-registered fallback** (`model-v2x-track/routed-c1a/submissions/2026-11-09_c1av5/v2x_s10_submission.zip`, md5 `2f3d80cbfed8c0f4064a8ba77aa5ecb5`).
  - Kit check valid; realism frames equal `C0`'s; rule 1 clean; local A 0.7290 and B 0.7062 (`C0` 0.7281 and 0.7056); rule 14 GO: pooled +0.0009, grouped P 1.00 over 57 scenarios.
  - **History:** all three V2X GO cases in the back-test scored positive on the server (+0.0008 to +0.0040). Expect about +0.0008 combined, which may fall inside the board's noise (about ±0.0015).

**LUMPI `routed-c1`** (80 clean folders, 211 members).
- **Fuse failed after the disk recovery,** on a code defect. Person's fusion pool was its four best members, all averaged rosf bags (draws 1-3, 1-4 and 1-5). They share checkpoints, so no pair was allowed, and the worker pool got zero workers.
- **Fix** (`route_predictions.py disjoint_pool`):
  - when a pool holds no checkpoint-disjoint pair, the best-ranked member that can pair joins it;
  - a class with no candidate keeps its routed member;
  - a pool that already has a valid pair is unchanged, so the earlier builds would not change.
  - Test `test_disjoint_pool_adds_one_member_only_when_no_pair_is_possible`; 180 tests pass. `s10_portfolio_tail.sh` accepts `fuse` as a start step.
- **Status:** resumed from fuse at 18:44 UTC.

#### 15.14.7 V2X upload 3 scored, LUMPI `C1` gated (2026-11-10, 21:00-21:20 UTC)

**V2X upload 3 (`c1av5`, the entrant's scoring output):**

| Submission | Combined | mAP 3D@0.5 | vehicle | pedestrian | truck | R | CD / EMD / FPD |
|---|---|---|---|---|---|---|---|
| `C0` 1042294 | 0.888471 | 0.597600 | 0.743130 | 0.397532 | 0.652140 | 0.940605 | 1.844 / 1.110 / 0.748 |
| **`c1av5` 1046758** | **0.888864** | 0.598059 | 0.743126 | 0.398913 | 0.652140 | 0.940605 | equal (same frames) |
| Delta | **+0.000393** | +0.000459 | -0.000004 | +0.001381 | 0 | 0 | 0 |

- **Projection:** +0.0008 combined (local pooled +0.0009 mAP). **Transfer: 0.5x**, inside the 0.2-0.6x band measured for post-processing stages (15.13.2). Positive, as all three V2X GO cases of the rule 14 back-test, but at the low end (they scored +0.0008 to +0.0040), and inside the board noise (about ±0.0015).
- **Per-class server numbers** are recorded only (audit rule d). The V5 stage acts on pedestrian alone, so a pedestrian-only change is what the stage predicts, not a selection.
- Records: `model-v2x-track/routed-c1a/submissions/2026-11-09_c1av5/codabench_1046758.json` and the registry row. **V2X has 2 uploads left.** The best clean V2X entry is now 0.888864.

**LUMPI `routed-c1`** (resumed from fuse; 12 member models, rule 1 clean):
- **Fused sets:** Car `bvrrosnswa6x5_tta12` + `bvrrosf6x4_tta12` @0.7; Bicycle `pprosswa6d2_tta` + `dsrosfswa6_tta` @0.5; Motorcycle `vnrosn6_tta12` + `vnrosf6d2_tta` @0.7.
- **D2 point rescoring:** not kept on Person (best beta 0.05: pooled -0.0035), as in the dry run.
- **Size calibration:** Car (-0.2, 0, 0) kept (pooled +0.0019).
- **Class gate against `C0`:**
  - Person kept: A +0.0048, B +0.0121, pooled +0.0096, P 1.00;
  - Car (pooled -0.0010), Bicycle (-0.0077), Bus (+0.0012, P 0.65) and Truck (-0.0070) reverted;
  - Motorcycle and Van are unchanged.
- **Rule 14: GO.** Pooled mAP +0.0014 (A +0.0007, B +0.0017), grouped P 1.00 over 28 groups, 90% CI [+0.0005, +0.0017]. Combined before transfer: +0.0012. At the 0.5-0.6x V2X transfer: about **+0.0006 to +0.0007**.
- **Packaged** (22:04 UTC): `model-lumpi-track/routed-c1/submissions/2026-11-10_c1/lumpi_s10_submission.zip`, md5 `4e5f82fccbd5bec9a30d991ff4d402c7`. Kit valid (24,481 boxes); realism frames are `C0`'s `g1-v6` frames. The scorecard projection is +0.0005 combined. The zip is held for the entrant's choice on L1 (Section 15.15.5).

**Rule 4, GBlobs probe on `rosn`** (the wave 5 probe rule, 15.13.9):
- `voxelrcnn-rosn-gblobs-g1v6` against `voxelrcnn-rosn-g1v6`: **PASS 7 of 14**, Person +0.0198 (8-view +0.0121), Bicycle +0.0701 (+0.0568), Bus, Van 8-view.
- Its averaged member passes only Bus 8-view over the plain probe. Against the averaged plain-VFE draw 1 it passes 7 of 14 (Person +0.0150, Bicycle +0.0561).
- **Draws 2-3** (`voxelrcnn-rosn-gblobs-g1v6d2`, `d3`; rule 1 clean) are queued after the R1.1 members.

**The entrant asked (2026-11-10)** for this score to be recorded, a review of the plan, and an assessment of why the multi-day effort did not bring the expected gain, with the research done early. The research runs in parallel (Section 15.15).

### 15.15 Why S10 has not delivered, and what is left (2026-11-10, 21:10-23:30 UTC)

Three studies ran in parallel: a detection forensics study and a LUMPI realism forensics study (CPU only; legal frames, validation labels and cached validation predictions; no test frame, no kit `realism_reference`, no real label row), plus a read-only external scan. Scripts and logs: `scratchpad/s10/research2/{detection,realism}`, with a `REPORT.md` for detection. Server per-class numbers are records only.

#### 15.15.1 The shortfall

| | Planned for `C1` (15.13.4, D1 plus stages) | Delivered |
|---|---|---|
| V2X | +0.003 to +0.006 combined | **+0.0004** (1046758). It came from V5 alone; no new member reached the V2X route |
| LUMPI | +0.002 to +0.005 | `C1` keeps Person only: +0.0014 mAP locally, about +0.0006 to +0.0007 expected; not yet scored |
| GPU work since `C0` | | 29 trained members (17 plain draws, 6 SN and range-jitter arms, 1 `g1-v7` probe, 5 GBlobs), about 30 SWA averages and 40 bags |

#### 15.15.2 Root causes, ranked by share of the V2X shortfall

| # | Cause | Evidence | Share |
|---|---|---|---|
| 1 | **The variance gain was already used up.** `C0`'s fusion and the new bags both average correlated models, so they substitute for each other | `C0`'s fused system beats its best member by +0.024 to +0.037 AP on A (LUMPI Bicycle +0.079). The best S10 member beats the best `C0` member by +0.002 to +0.016 and stays below `C0`'s system on every class but LUMPI Person. New members find 84-100% of what `C0` finds, but only 2-7% of its V2X pedestrian misses and 8-14% of its LUMPI Person misses | about 75% |
| 2 | **What is left is bias that every member shares.** More draws cannot remove it | Confident confusion false positives are made by 73-100% of the other members. LUMPI late-A loses AP to ranking (Person 0.337, Bicycle 0.45, Truck 0.415, Van 0.743), not to misses (0.025-0.05). Oracle pools: LUMPI Van boxes on real Cars +0.35, Bicycle on real Persons +0.26 to +0.38, Truck on Cars and Vans +0.12 to +0.17; V2X pedestrians on static structures +0.082 | why cause 1 cannot be bought with draws |
| 3 | **The expectation was set at member level and not revised.** Rule 4 compares a bag with the previous bag, not with `C0`'s fused output | The `C1a` rehearsal (15.13.7, Nov 9) already showed LUMPI -0.0015 from scratch and `C1a` = `C0` after the gate. Waves 3-5 kept training plain depth after that warning | the process cause behind 1 |
| 4 | **R3's +0.01 bar on route changes** | blocked V2X truck +0.0033 (P 0.99) and pedestrian +0.0024 (P 0.935) | about 25% (about +0.001 combined after the shrink) |
| 5 | Transfer | `c1av5` 0.51x; the V2X GO pairs since S8 0.80x pooled (median 0.60x); LUMPI Person and Car changes median 1.24x; rare-class gains negative (s9iu -0.28x); size calibrations 0.24-0.37x | under 10%; **the 0.6 shrink stands** |
| 6 | Operations | the disk-full stop, two hung probes and the fuse defect cost about 5 hours on `C1` | changed no outcome |

**LUMPI is a realism race,** and S10 put its GPU hours into detection depth. The 15.13 scan had bounded every legal realism lever we could then measure under +0.001. The forensics below found one more.

#### 15.15.3 LUMPI realism forensics

1. **Nulls and padding are not the cause.** LUMPI test frames carry no nulls (kit format report), and neither do legal real frames or `C0`'s frames.
2. **The test window explains why the server is worse than our local numbers. It does not explain why other teams are better.**
   - `C0` scores EMD 1.18-1.20 against proxies 4-5 and 1.234-1.256 against five late sets (frames 4800-6395, the legal frames nearest the test window). The server's 1.272 matches the late level plus noise.
   - **Scene drift:** real against real within one time window gives 0.958-0.964; across windows, 1.00-1.16.
   - **Noise:** the scorer seed moves EMD by 0.01-0.02, and the frame selector's seed moves held-out R by about ±0.0013.
   - Together these explain LUMPI's 0.31x transfer for fine changes. Selecting frames against the late sets does not help reliably (-0.0001 to +0.0021), so **the late sets become the baseline for estimates** (expect the server about 0.02-0.03 EMD above them).
3. **A larger selection pool does not help:** `g1-v6` plus draws 2-3 (30,000 frames) scores -0.0005 R.
4. **Why R1 failed.**
   - In total the blocks match the real mass in the 215 anchor footprints (7,579 against 8,277 points per frame). Per anchor they are far off: 31% exceed 1.5x and 27% fall below 0.5x, so about 5,400 points per frame sit in the wrong places. The keep calibration can only lower a block.
   - Our frames already have too much mass above the ground (45.6% against 33.7% real), and R1 raises that.
   - The opposite edit, deleting twin-only static geometry (6.0% of a frame), also loses (-0.0018 R).
5. **The one fault worth fixing: the twin renders the PandarQT (sensor 36) without its steep beams.**
   - **The real sensor:** 64 beams from -52.1 to +52.1 deg, 1.81 m above the twin ground (`meta.json`).
   - **In the twin:** its lowest return is about -27 deg.
   - **In real frames:** 3.6% of all points come from the -52 to -30 deg beams, a ground ring 1.4-3.4 m from the sensor. This holds in Measurement4, 5 and 6 and in every time window.
   - **In our frames:** 0.13% fall in that ring, and a ring 3.5-7 m out carries 5.0% extra. This single spot is 16% of `C0`'s transport cost against `late-3`.
   - **The fix:** within 7 m of the sensor, flat-ground points (within 0.12 m of the twin ground) move radially onto the ground rings of the real beam table. The count and azimuth stay the same; sensor metadata only.
   - **Result:** held-out R +0.0019 (mean of 5 sets; at least +0.0014 on every set; EMD -0.033 to -0.040; CD -0.04 to -0.05; FPD equal). After re-selecting frames: +0.0019 to +0.0025. Over 3 other scorer seeds: +0.0014 to +0.0018. The gain is flat for radii of 6-8 m.
   - **Checked by the main session** with `bdc26.realism.score` on proxies 4, 5 and `late-3` at seeds 1234 and 77: R +0.0016 to +0.0020 on all six, EMD -0.033 to -0.040 (`research2/realism/verify_main`).
6. **Measured and dropped:**
   - the same re-cast for the other four lidars (-0.0001 to -0.0003);
   - a Pandar64 housing return (sign depends on the point count);
   - 30% fewer clutter objects (+0.0009 over the fix locally, a fine change, so about +0.0001);
   - ground height (at most -0.005 EMD).
7. **The gap to the leaders.** Retaking LUMPI by realism alone needs about -0.16 EMD; the fix gives -0.035. dipper13579's CD (0.755) is at the real-against-real level (0.62-0.72), and lukefinigan's (1.186) is below ours (1.40-1.51). Their frames match the real local geometry more closely than a CARLA twin can. How they built them is not known, and we draw no conclusion.

**Organizer rule on the frames** (docs/01): the 50 frames "must be synthetic", with no real frames and nothing derived from the forbidden frames, and the report must say where they came from. A sensor-model correction from metadata keeps them synthetic. S10 rule 1's clause that the frames come from a corpus that trains a used member is our own, stricter rule. V2X already ships nulls added at packaging.

#### 15.15.4 External scan (read-only)

- No new report from lukefinigan, dipper13579, sadbodh or linyongchun.
- AMAN_UPG (arXiv 2611.03940) confirms V2X null injection (we ship 0.31 already). The UCF LUMPI report (arXiv 2609.07590) found that global affine and radial-density fixes do not move EMD materially. It scored EMD 1.857.
- UrbanTwin (arXiv 2509.06781) matches LUMPI points per frame (220k against 219k), so our gap is spatial, not density.
- Learned ray drop and diffusion translation (DRUM, LiDARsim) train on real scans and are excluded.

#### 15.15.5 Levers left (expected server gain in combined score)

| # | Lever | Measured | Expected | Cost and landing | Rule fit | Risks |
|---|---|---|---|---|---|---|
| **L1** | PandarQT re-cast on the LUMPI realism frames at packaging | held-out R +0.0019 (main-session check +0.0016 to +0.0020) | **+0.0005 to +0.0011** (a geometric change, 0.6-1.45x) | code and test about 2 h; in LUMPI upload 3 (Nov 11) | organizer rule met (synthetic, metadata only, disclosed); needs a waiver of S10 rule 1's frame clause until L2 lands | LUMPI transfer ranged 0.31-1.45x; one fixed server seed |
| **L2** | The same fix as a corpus (`g1-v6pq`: points inside labelled boxes untouched) plus one member on it | as L1 | as L1; restores rule 1 as written for `C2` | corpus about 1 h CPU; member about 6 h training and 3 h tuning | rule 1 as written | the member must be used in `C2` (a bag partner or a class route); it takes one trainer slot (capacity is not binding) |
| **L3** | Rule 14b for the `C2` gate on route changes (projection > 0, grouped P >= 0.8) instead of R3's +0.01 bar | V2X truck +0.0033, pedestrian +0.0024 pooled | V2X +0.0010 to +0.0016 | none | the entrant's gate choice | gains this small transferred at 0.24-1.86x |
| **L4** | R1.1 members first (done: moved to the queue front at 22:10 UTC); R1.2 draws only if R1.1 passes a class | V2X pedestrian oracle +0.032 inside anchors; capture rate unknown | V2X +0.001 to +0.002 if it passes; LUMPI +0.0002 to +0.0005 | R1.1 checks about Nov 11 10:00 UTC | adopted (option 1) | 12-16% of true pedestrians stand inside anchors |
| **L5** | GBlobs probe draws (done: `rosn` d2-d3 and PV-RCNN++ d2-d3 queued) | `rosn` probe Person +0.020, Bicycle +0.070 at member level | LUMPI +0.0005 to +0.0015 if a bag carries Person or Bicycle in `C2` | queued | adopted (option B) | member-level gains have shrunk at portfolio level (cause 1) |
| L6 | One LUMPI draw with late-M4 Van size quantiles and a real-size Truck mixture | not measurable before training | 0 to +0.002, very uncertain | code 2 h, corpus 3 h, training 6 h, tuning 3 h; about Nov 12 12:00 UTC | real-size statistics (rule 5) | the SN arm failed Truck at P 0.00; Truck validation does not predict the test window |
| L7 | Van height gate stage (Van boxes under 1.9 m tall, score x0.5) | A +0.0085, late-A +0.0062, B -0.0002 | about +0.0003 | 2 h CPU | new inference stage, disclosed | the grid was seen before any rule |
| - | Dropped: more plain depth beyond the queue, R1 frames for realism, other sensors' re-casts, clutter cuts, larger pools, late-proxy selection, cross-class demotion, duplicate removal, a static mask from real clouds | | | | | |

**Assessment.**
- **LUMPI.** `C1` with L1 is about +0.0011 to +0.0018 over `C0` (0.5419-0.5426), against lukefinigan's 0.5440 on Nov 9. With L2-L6 in `C2`, the high side is about +0.003, roughly level with 0.5440, and only if that board has not moved. Rank 1 on LUMPI is possible, but not likely. L1 is the largest single lever left on LUMPI.
- **V2X.** The clean lead was 0.033 over sadbodh on Nov 9. L3 and L4 can add +0.001 to +0.003. Plain depth adds nothing more. Nobody has read the current board since Nov 9.
- **The plan changes.** Plain depth stays queued only because trainer capacity is free (13 queued members end about Nov 12 13:00 UTC, against the Nov 13 18:00 stop). Bias levers (L2, L4, L5, L6) go ahead of plain draws. Expected gains are now judged against `C0`'s fused output, not against the previous bag.

#### 15.15.6 The GBlobs 3-draw bags (2026-11-11, 02:40-03:00 UTC)

GBlobs draws 2-3 on `rosf` (`voxelrcnn-rosf-gblobs-g1v6d2`, `d3`) and their averaged members are tuned. Two bag cards were built from draws 1-3 (CLEAN, rule 1; the iou of the xyz bags): `bag-voxelrcnn-rosf-gblobs-g1v6x3` and `bag-voxelrcnn-rosf-gblobs-swa-g1v6x3`. Rule 4 (check log w1_batch2.log, from line 1273):

| Bag (reference) | Passes | Person pooled (8-view) | Bicycle pooled (8-view) | Losses |
|---|---|---|---|---|
| GBlobs x3 (xyz x3) | Person, Bicycle, Van 8v | +0.0165 (+0.0106) | +0.0362 (+0.0365) | Car -0.006, Truck 8v -0.015 |
| GBlobs averaged x3 (xyz averaged x3) | Person, Bicycle, Van 8v | +0.0203 (+0.0100) | +0.0386 (+0.0313) | Truck 8v -0.015, Bus |
| GBlobs averaged x3 (GBlobs x3) | 7 of 14 | +0.0043 (+0.0066) | +0.0113 (+0.0057) | none significant |
| GBlobs averaged x3 (**xyz averaged x5**, the Person lead's family) | Person, Bicycle, Van 8v | **+0.0120 (+0.0071)** | **+0.0222 (+0.0219)** | Car -0.007 / -0.005, Truck -0.009, Motorcycle |

- **Against `C0`'s fused system** (A / B, 8-view; 15.15 detection table): Person 0.607 / 0.236 against 0.601 / 0.232, the first bag above `C0` on both splits for Person; Bicycle 0.590 / 0.255 against 0.648 / 0.286, below.
- **Reading.** GBlobs is the first S10 lever whose gain holds at bag level against the best xyz bag (3 draws beat 5). It is a different input encoding, so its errors are less shared than another xyz draw's (cause 2). Its portfolio value is still to be measured: the bag's Person gain over the averaged xyz x5 bag (+0.007 to +0.012 pooled) shrinks inside the Person fusion (cause 1), so about +0.002 to +0.006 Person AP, or +0.0003 to +0.0008 combined at the LUMPI rate. Bicycle (below `C0`) can enter only as a fusion partner.
- **What follows.** Part A's GBlobs draws 4-5 (`voxelrcnn-rosf-gblobs-g1v6d4`, `d5`) stay queued; the 5-draw GBlobs bags go to `C2`. The 12-view runs of draws 2-3 wait for the Nov 13 stop (12-view jobs do not share a GPU with training). `C1` (packaged 22:04 UTC Nov 10) does not contain these bags.

#### 15.15.7 Adopted: package A (the entrant, 2026-11-11, about 03:50 UTC: "Adopt package A")

Package A = L1 in LUMPI upload 3, plus L2 and L3 for `C2` (15.15.5). B (L6, L7) and C (rule 1 as written) are not adopted.

**L1 and L2 share one corpus.** `common/tools/s10_beamfix.py` (test `test_beamfix_moves_near_ground_points_onto_the_real_rings_and_spares_boxes`) writes `pcdet/g1-v6pq` from `pcdet/g1-v6`:
- the PandarQT (session 36) flat-ground points within 7 m are re-cast onto the sensor's 22 Measurement4 ground rings (1.41-6.58 m), azimuth kept, 1% jitter;
- points in a labelled box's footprint column stay, and no point moves into one, so every box keeps its points;
- draws are seeded per frame ([0, frame id]);
- metadata only: no real point, label or frame enters;
- 10,000 frames, labels and splits copied; about 3,750 points moved per frame (7.5%), the same as in the research version (about 4,000).

The card's `real_data_use` names the re-cast, and `clean_check.py` passes it.

**Held-out check of the frames as packaged.** C1's 50 frame ids (`g1-v6` val, as in `C0`), taken from `g1-v6pq`, against `C0`'s frames, scorer settings, 3 proxies x 2 seeds:

| Proxy | Seed | `C0` frames R | Research fix R | `g1-v6pq` frames R | dR | dEMD | dCD |
|---|---|---|---|---|---|---|---|
| 4 | 1234 | 0.9404 | 0.9422 | 0.9421 | +0.0017 | -0.033 | -0.042 |
| 4 | 77 | 0.9393 | 0.9410 | 0.9412 | +0.0019 | -0.036 | -0.032 |
| 5 | 1234 | 0.9394 | 0.9410 | 0.9410 | +0.0016 | -0.032 | -0.042 |
| 5 | 77 | 0.9397 | 0.9417 | 0.9418 | +0.0021 | -0.043 | -0.032 |
| late-3 | 1234 | 0.9372 | 0.9391 | 0.9390 | +0.0018 | -0.035 | -0.051 |
| late-3 | 77 | 0.9387 | 0.9407 | 0.9408 | +0.0021 | -0.042 | -0.032 |

Mean dR +0.0019 (range +0.0016 to +0.0021). The box guard costs nothing.

**L1: LUMPI upload 3 = `C1` with the `g1-v6pq` frames** (tag `c1pq`).
- The detections are byte-identical to `C1`'s (predictions md5 `e18947d7...`, 24,481 boxes).
- The 50 frame ids are the same; only the frames' near-field ground points differ.
- `routed-c1/model.yaml` now names `realism_frames: pcdet/g1-v6pq`, and `clean_check.py` passes (12 members, frames CLEAN).
- The `C1` zip without the fix (`2026-11-10_c1`) is kept and is not uploaded.
- **Package:**
  - The file to upload is `model-lumpi-track/routed-c1/submissions/2026-11-10_c1pq/lumpi_s10_submission.zip`, md5 `6c2da31f4146a174caba4923709f87c4`.
  - The official kit check passes: valid, 24,481 boxes, 271.5 s (limit 400 s).
  - Kit realism against proxy 4: R 0.942147 against `C1`'s 0.940414 (CD 1.443 against 1.485, EMD 1.147 against 1.180).
  - Proxy 5: R 0.94103.
  - Registry row: "packaged, not yet uploaded".
- **Expectation against `C0` 0.5408:**
  - Detection: projection +0.0005 (rule 14 GO +0.0014 pooled mAP).
  - Realism: 0.4 x +0.0019 R at a transfer of 0.6-1.45x gives +0.0005 to +0.0011.
  - Total: about +0.0010 to +0.0016, so 0.5418 to 0.5424. That is below lukefinigan's 0.5440 of Nov 9.
  - LUMPI realism transfer has been as low as 0.31x; then the total is about +0.0007.
  - Under rule 14b's slot rule (highest projection, rule 1 and grouped P >= 0.8), this is the best candidate available for upload 3.
- Until L2's member is used, S10 rule 1's frame clause (the frames come from a corpus that trains a used member) is waived for this upload. The organizers' rule (synthetic frames, nothing from real frames, their origin stated in the report) is met.

**L2: the `g1-v6pq` member.**
- `voxelrcnn-rosf-gblobs-g1v6pq`: the GBlobs `rosf` configs, training seed 666, CLEAN.
- It goes to the front of the train queue (about 6 h training, 3 h tuning).
- **Pre-registered use:** it replaces draw 1 (`voxelrcnn-rosf-gblobs-g1v6`) in `C2`'s GBlobs bags (plain and averaged), so `C2`'s frames come from a corpus that trains a used member.
- Rule 4 against draw 1 is a sanity check: no class is expected to differ, since only near-field ground points changed.
- If the bag is not used in `C2`, the waiver above stays, and the report says so.

**L3: rule 14b for `C2`.**
- `route_predictions.py gate --route-bar 0` drops R3's +0.01 B bar on route changes, so a changed class needs a B gain at P >= 0.9 and the pooled condition, as a stage change does. Function `b_bar`, test `test_rule_14b_drops_the_route_bar_only_when_asked`.
- The version as a whole then needs rule 14 at grouped P >= 0.8 (`s10_grouped_gate.py --go-p 0.8`, raised from 0.75) and a projection above 0.
- The tail takes `S10_ROUTE_BAR=0 S10_GO_P=0.8` for `C2`; the defaults keep R3 and rule 14 as in `C1`.

**Report items.** The PandarQT re-cast (sensor metadata only; the realism frames and `g1-v6pq`); rule 14b as a gate change.

#### 15.15.8 LUMPI upload 3 scored, and the release split 10.0 / 10.1 (2026-11-11)

**Score.** 1047204 (`c1pq`) scored **0.539575**, -0.001225 against `C0` 1042287 (0.5408). `C0` stays the best clean LUMPI entry, and LUMPI has 2 uploads left (close 2026-11-16 04:59 UTC). Server record `routed-c1/submissions/2026-11-10_c1pq/codabench_1047204.json`; one read of the public API returned the bot check, which is not bypassed.

| Term | `C0` 1042287 | `c1pq` 1047204 | Delta | Local expectation |
|---|---|---|---|---|
| Combined | 0.540800 | 0.539575 | **-0.001225** | +0.0010 to +0.0016 |
| Realism R | 0.934200 | 0.935524 | **+0.001324** | +0.0019 held-out (so 0.70x) |
| CD / EMD / FPD | 1.5103 / 1.2720 / 0.4298 | 1.4672 / 1.2464 / 0.4221 | -0.043 / -0.026 / -0.008 | -0.04 / -0.035 / small |
| 3D mAP@0.5 | 0.194973 | 0.192926 | **-0.002047** | +0.0007 |
| Person AP (record only) | 0.3058 | 0.2911 | -0.0146 | pooled +0.0096 |
| Other classes (record only) | | | Bicycle +0.0003, Car +0.00004, the rest equal | 0 |

- **L1 (the PandarQT re-cast) worked.** Realism transferred at 0.70x, inside the 0.6-1.45x range expected for a geometric change.
- **The one detection change, the Person route, lost.** That is the whole shortfall.

**Why the Person route lost: late-A.** Final routed validation predictions of `C1` against `C0`, Person AP:

| Split | `C0` | `C1` | Delta | P(gain) |
|---|---|---|---|---|
| realval-A (1,280 frames) | 0.6011 | 0.6059 | +0.0048 | 1.00 |
| early-A (Measurement4 frames before 4800, 960 frames) | 0.6400 | 0.6500 | +0.0101 | 1.00 |
| **late-A (Measurement4 4800-6399, 320 frames)** | 0.4589 | 0.4534 | **-0.0055** | **0.02** |
| realval-B (867 frames) | 0.2322 | 0.2422 | +0.0100 | 1.00 |

The test window is Measurement4 frames 6497-8109, right after late-A. R3's class gate reads B and A+B pooled, and the fuse step ranks Person by late-A (R5's `--late-rank`) but does not gate on it. So the late-A loss went through.

**History check (diagnostic; server per-class numbers are records only).** Every consecutive pair of LUMPI uploads with final routed validation predictions, for each class whose local AP changed (`common/tools/s10_split_history.py`). Sign agreement with the server:

| Class set | Changed pairs | early-A agrees | late-A agrees | B agrees | late-A > 0 and B > 0 agrees |
|---|---|---|---|---|---|
| Person | 9 | 6 | **8** | 7 | **9 of 9** |
| Car, Bicycle, Truck | 9 | 3 | 1 | 3 | no split predicts the server |

- **Person.** The two Person changes with late-A < 0 both lost on the server: `C0` against `s9j` (late-A -0.0114, server -0.0034) and `C1` against `C0` (late-A -0.0055, server -0.0146). All 6 changes with late-A > 0 and B > 0 gained on the server.
- **The one late-A miss** is `s9c` against `s9b` (late-A +0.0094, server -0.0039); its B was negative (-0.0013).
- **Other classes.** Car, Bicycle and Truck changes do not transfer by any split, the rare-class lesson again (s9iu, 15.15.2).
- **The sample is small (9 Person pairs).** But the mechanism is direct: late-A is the same measurement and the same season, and it ends 100 frames before the test window. This history only reads past uploads; nothing was fitted to it.

**Proposed rule 15 (for `C2`; the entrant's decision):**
- A LUMPI Person route, fusion or calibration change needs a late-A gain (delta > 0 at P(gain) >= 0.5) in addition to the class gate. Stage-only changes are included.
- Classes other than Person keep the current gate; no split predicts them.
- `C1`'s Person route would have been reverted. `C1` would then have equalled `C0` plus L1.

**The release split (the entrant, 2026-11-11).** The organizers rank KarmaRV only by LUMPI 1042287 and V2X 1042294 onward (15.14), and the report must describe the change, so the tags separate the two sets:

| Tag | Commit | Uploads | Rule 1 (`clean_check.py`, 2026-11-11) |
|---|---|---|---|
| **10.0** | `e6c34d9` (the 9.2 commit) | LUMPI 1038963 (`s9j`, 0.5428), V2X 1038966 (`s9f`, 0.9038): the first final-phase uploads, **removed from the boards** | FAIL: LUMPI 10 of 12 members, V2X 6 of 6 members and its frames trained on real label rows |
| **10.1** | the S10 commit of 2026-11-11 | LUMPI 1042287 (`C0`, 0.5408, **best**), 1047204 (`c1pq`, 0.5396); V2X 1042294 (`C0`, 0.8885), 1046758 (`c1av5`, 0.8889, **best**) | PASS: every member of all four uploads clean |

- `RELEASES.md`, `docs/decisions/README.md` (register, ranked entries, reproduction table), the root README (Sections 8 and 9) and both track READMEs (Section 9) carry the split.
- The reproduction scripts of all four 10.1 uploads re-merge to identical boxes. The GPU dry runs and `releases/10.1/weights.json` follow the Nov 13 training stop. The entrant pushes and publishes.
- `C2` uploads need a tag that the entrant names.

#### 15.15.9 Adopted: option 1 (the entrant, 2026-11-11: "Adopt option 1")

LUMPI's last two uploads:

| Upload | System | Expected | Status |
|---|---|---|---|
| 4 | **`c0pq`**: `C0`'s detections (byte-identical to 1042287's) with the `g1-v6pq` frames (byte-identical to 1047204's) | **0.541329** = 0.6 x 0.278533 + 0.4 x 0.935524: both terms are already measured on the server, and each term depends only on its own part of the zip | packaged: `model-lumpi-track/routed-c0/submissions/2026-11-10_c0pq/lumpi_s10_submission.zip`, md5 `aa167c395f3d8c4549b063d9e269a863`; kit valid (24,088 boxes, 244 s, kit R 0.942147 as `c1pq`); `test/reproduce_c0pq.sh` re-merges identical; the entrant uploads |
| 5 | `C2` under rule 14b and **rule 15** | 0.541-0.544 (15.15.5) | after the Nov 13 18:00 UTC training stop |

**Rule fit.**
- Detection is the better-scored complete system (`C0`), so no per-class server number is used (audit rule d).
- The frames are the adopted L1 frames.
- S10 rule 1's frame clause is waived as for `c1pq` until the `g1-v6pq` member is used in `C2`.

**Rule 15 (adopted for `C2`, LUMPI Person).**
- `route_predictions.py gate --late-gate Person`: a changed Person configuration that passes the class gate must also gain on late-A (delta > 0 at P(gain) >= 0.5), or it reverts to the incumbent. Function `late_gate_ok`, test `test_rule_15_needs_a_late_a_gain`.
- The tail takes `S10_LATE_GATE=Person`.
- **Checked on a scratch copy of `C1` against `C0`:**
  - Under rule 14b alone (route bar 0), Person is kept (B +0.0100 at P 1.00).
  - With rule 15 it reverts: late-A -0.0055 at P 0.02.
  - So rule 15 is needed exactly because rule 14b lowers the B bar.
  - (Under R3's +0.01 bar, the final `C1` predictions now fail on B by 0.00002, since the copy fit after the gate moved B; C1's gate itself saw +0.0121.)

**The `C2` settings, fixed now:**
- LUMPI: `S10_INCUMBENT=model-lumpi-track/routed-c0 S10_ROUTE_BAR=0 S10_GO_P=0.8 S10_LATE_GATE=Person`, frames `pcdet/g1-v6pq`.
- V2X: `S10_INCUMBENT=model-v2x-track/routed-c1a S10_ROUTE_BAR=0 S10_GO_P=0.8`, frames `g1-v6`.
- The GBlobs bags carry `voxelrcnn-rosf-gblobs-g1v6pq` in place of draw 1 (15.15.7).

#### 15.15.10 LUMPI upload 4 scored as expected; the 10.0 / 10.1 releases (2026-11-11, 04:35-05:10 UTC)

**Score.** **1047231 = `c0pq`: 0.541329**, exactly the expected value (+0.000529 against 1042287). It is the best clean LUMPI entry. LUMPI has **1 upload left** (close 2026-11-16 04:59 UTC); V2X has 2 (close 2026-11-15 04:59 UTC).
- **Which file was uploaded.** The entrant's message named the `c1pq` path. The scores identify the `c0pq` zip (`model-lumpi-track/routed-c0/submissions/2026-11-10_c0pq/lumpi_s10_submission.zip`, md5 `aa167c395f3d...`):
  - mAP 0.194973 and every per-class AP equal `C0`'s (the `c1pq` zip scored 0.192926 as 1047204);
  - every realism term equals 1047204's (the `g1-v6pq` frames; `C0`'s zip scored R 0.9342).
  - Only the `c0pq` zip pairs the two. It is recorded there (`codabench_1047231.json` with a `file_identification` note; manifest; registry).
- **Determinism, confirmed.** Detection and realism are scored separately and exactly reproducibly: the same predictions give the same AP, and the same frames give the same R. So a combination of two scored parts is known before upload.

**Releases (the entrant: weights and scripts on GitHub, each set reported separately).**
- `releases/10.0/weights.json`: 23 checkpoints and 2 zips, all byte-identical to 9.2's assets. The tag stays on `e6c34d9`; the manifest lives on `main`.
- `releases/10.1/weights.json`: 23 checkpoints and 5 zips (3.47 GB) for `lumpi:c0`, `lumpi:c0pq`, `lumpi:c1pq`, `v2x:c0` and `v2x:c1av5`.
- **Bug fixed in `release_weights.py collect`.**
  - Zips that share a file name (every S10 upload is `<track>_s10_submission.zip`) overwrote each other, so 2 of the 5 zips would have been published.
  - They are now named `<track>.<model>.<tag>.<file>` (test `test_release_zip_assets_get_unique_names_when_versions_share_a_file_name`).
  - `v2x:c1av5`'s manifest now carries its CodaBench id (it was recorded by hand on Nov 10).
- `RELEASES.md` has detailed 10.0 and 10.1 sections for the report: the rule 1 table; one row per version with its change, members, corpora, test-time stages and frames; the score decomposition; the real-data uses; the assets; and the fetch and reproduce commands.
- The tag 10.1 moves to the commit that holds all five 10.1 uploads and the manifest. The GPU dry runs follow the Nov 13 training stop.

**Late-A check of the Person candidates for `C2`** (against `C0`'s Person member `voxelrcnn-rosn-g1v6` 12-view):

| Candidate | A | late-A (P) | B (P) | Rule 15 |
|---|---|---|---|---|
| `bag-voxelrcnn-rosf-gblobs-swa-g1v6x3` 8-view | +0.0109 | **+0.0081 (0.98)** | +0.0185 (1.00) | passes |
| `bag-voxelrcnn-rosf-gblobs-swa-g1v6x3` plain | -0.0010 | +0.0002 (0.62) | +0.0131 (1.00) | passes (barely) |
| `bag-voxelrcnn-rosf-gblobs-g1v6x3` 8-view | -0.0037 | -0.0216 (0.00) | +0.0162 (1.00) | fails |
| `bag-voxelrcnn-rosf-swa-g1v6x4` 12-view (`c1pq`'s route) | +0.0094 | -0.0099 (0.01) | +0.0225 (1.00) | fails (as on the server) |
| `voxelrcnn-rosn-gblobs-swa-g1v6` 8-view | -0.0014 | -0.0012 (0.54) | +0.0133 (1.00) | fails |
| `voxelrcnn-rosn-gblobs-g1v6` 8-view | +0.0004 | -0.0032 (0.43) | +0.0138 (1.00) | fails |

- The averaged GBlobs `rosf` bag is the one Person candidate with late-A evidence.
- So the queue moved `voxelrcnn-rosf-gblobs-g1v6d4` and `d5` behind the `g1-v6pq` member. Nothing is dropped, and everything queued still trains before the stop.

**C2 rehearsals (`routed-c2r`, both tracks) launched at 04:41 UTC** with the adopted settings: LUMPI rules 14b and 15 against `routed-c0`, frames `g1-v6pq`; V2X rule 14b against `routed-c1a`.
- Members: every clean member tuned so far. LUMPI adds 10 folders to C1's 80: the GBlobs draws, their averaged versions and bags, and the probes. V2X has C1's 65.
- They forecast `C2` and test the new gates end to end. A V2X rehearsal that passes could take V2X upload 4.

### 15.16 Research 3: realism-frame calibration, the rule question, and the plan to the close (2026-11-11, 05:00-06:00 UTC)

**Standing.**
- **LUMPI:** best 1047231 (0.541329); 1 upload left, close 2026-11-16 04:59 UTC.
- **V2X:** best 1046758 (0.888864); 2 uploads left, close 2026-11-15 04:59 UTC.
- **Last board read (Nov 9):** LUMPI lukefinigan 0.5440 (mAP 0.1953, R 0.9414); V2X sadbodh 0.8550 and lukefinigan 0.8334.
- On LUMPI the gap is realism, about 0.0027. The board is behind a bot check, so the entrant's screenshot is the only source.

**Two research agents (CPU, fit-and-judge protocol, `scratchpad s10/research3/`)** found one large lever per track:
- **LUMPI N1, nearest-support density re-weighting.**
  - Every point of the legal fit frames (proxies 1-3; Measurement4 frames 40-6390) goes to its nearest synthetic point, pooled over the 50 frames.
  - On a 2 x 2 x 0.5 m grid of the synthetic support, weight = real share / synthetic share.
  - Each frame is re-drawn to 50,000 points from its own points in proportion to the weight. Repeated points get N(0, 2 cm) jitter.
  - It is the same statistic as our disclosed density prior (8 x 8 x 2.5 m, background only, applied in the generator), but much finer (12,601 cells), applied to all points of the 50 frames only. About 34% of the points are jittered copies.
- **V2X A + W (`aw_mid`).**
  - W: in each (azimuth, elevation) bin of 10 x 2.125 deg, the ranges of our points are quantile-mapped onto the real ones (21 quantiles); points move along their own rays.
  - A: the share of points per bin is rebalanced (gamma 0.5) with background points taken from 150 other `g1-v6` frames.
  - Fitted on V2X proxies 1-3 and `g1-v6` frames outside the 50. Nulls and points in boxes are untouched.
  - It mends a misplaced twin scene: points that must move more than 3 m are 15% of the mass and carry 50% of W1.

**Main-session verification** (independent scorer runs, including a new scorer seed and judge sets that no agent used):

| Set | Judge | Mean dR | Lowest | Wins | Mean dEMD | Max CD |
|---|---|---|---|---|---|---|
| LUMPI N1 `safe_frames` (fit: proxies 1-3 only; pre-registered) | proxies 4, 5, late-3, b-m5, b-m6 x seeds 1234, 99 | **+0.0076** | +0.0063 | 10/10 | -0.152 | 0.98 |
| LUMPI N1 `best_frames` (fit also on late-1/2) | same | +0.0062 | +0.0032 | 10/10 | -0.134 | 0.96 |
| LUMPI N1 on the approved 8 x 8 x 2.5 m grid (fit: proxies 1-3) | same | +0.0015 | -0.0007 | 9/10 | -0.027 | |
| V2X `aw_mid` | proxies 4, 5 x seeds 1234, 2024 | **+0.0100** | +0.0077 | 4/4 | -0.159 | 0.86 |
| V2X `w_coarse` (W only, 30 x 4.25 deg) | same | +0.0041 | +0.0012 | 4/4 | -0.056 | 1.28 |

**Provenance and copy audit.**
- **LUMPI:**
  - every fit frame is Measurement4 below 6400 (maximum 6395);
  - every output point is a point of its own synthetic frame (65.7% exact, the rest within 0.11 m);
  - the share of points within 1 mm of a real point is unchanged (0.002%).
- **V2X `aw_mid`:**
  - 50 x 50,000 points, nulls 0.3100;
  - its median distance to the nearest real fit point falls from 0.283 to 0.124 m;
  - within 1 cm: 0.16% to 1.30%; within 1 mm: 0.001% to 0.015%.
  - No real point is copied, but the warped frames sit on the real surfaces.

**Server expectation, at transfers seen before** (combined score; detections unchanged):

| Track | Set | Low | Central | High |
|---|---|---|---|---|
| LUMPI | N1 `safe_frames` (+0.0076 R) | 0.31x: 0.5423 | 0.70x: 0.5435 | 1.0x: 0.5444 |
| V2X | `aw_mid` (+0.0100 R) | 0.5x: 0.8909 | 0.86x: 0.8923 | 1.0x: 0.8929 |

**The rule question (it is the entrant's decision).**
- **The organizers' own frame rule** (docs/01): the 50 frames "must be synthetic", with no real frames and nothing from the 100 forbidden frames, and the report must say where they came from. Both levers meet it as written.
- **The organizers' answer of 2026-11-09** allowed the uses we listed: a background density prior, the V2X beam table, and choosing the frames with proxies. Neither lever is on that list.
- **Our own rules table (docs/01 Section 3)** is stricter:
  - "Affine or quantile warping applied **only** to the 50 submitted frames to match real moments: **Avoid**". W is exactly this, and N1 and A are fine density matches applied only to the frames.
  - "Generator fitted to real scans (... structure positions read off real points ...): **not with the track's own real frames**". W moves the twin's structure onto the real range profile; N1 at 2 m is far finer than the "density on 8 m cells" that the row names as distribution analysis.
- **The same table:** "Uploads designed to isolate realism (only the frames changed, or detection zeroed): not done".
  - **1047231 (`c0pq`) changed only the frames against 1042287.** It was not designed as a probe: both of its terms were already measured (1042287 and 1047204), so it told us nothing new about the realism reference.
  - The report states it plainly.
  - Future uploads keep the rule: frames ship together with a detection change, and no frame choice is taken from another upload's server realism.
- **Risk.** If the organizers judge a frame method outside the rules, they can remove that upload, as they removed 10.0.
  - Because the best entry counts, the board would fall back to the previous best. But the report and the ranking would carry the issue.
  - Their last answer took about 3 hours.

**Options for the remaining uploads:**

| Option | What | LUMPI last upload | V2X uploads 4-5 | Expected | Risks |
|---|---|---|---|---|---|
| **1 (recommended)** | Ask the organizers first (Appendix B, short); use only on a yes; prepare everything now | best detections (`C2` if it passes rules 14b and 15 against `c0pq`, else `C0`'s) + N1 `safe_frames` | upload 4: V2X `C2r` detections (if they pass) + `aw_mid`; upload 5: final V2X `C2` + `aw_mid` | LUMPI 0.5435 central (0.5444 at 1.0x), plus any `C2` gain; V2X about 0.892 plus `C2` | the answer may come late. The cutoff is Nov 13 12:00 UTC for V2X and Nov 14 12:00 UTC for LUMPI; past it, Option 3 plus the 8 m variant |
| 2 | Use them without asking | same | same | same | a removal, and a reporting problem; against our own rules table |
| 3 | Do not use them | best detections + `g1-v6pq` frames (or the 8 m N1 variant, +0.0015 R, inside the approved granularity) | `C2` + `g1-v6` frames | LUMPI about 0.5413-0.5419 plus `C2`; V2X about 0.889 plus `C2` | LUMPI likely stays 2nd |

**Detection side (unchanged plan, new evidence).**
- The averaged GBlobs `rosf` bag is the one LUMPI Person candidate that passes rule 15 (late-A +0.0081 at P 0.98). GBlobs draws 4-5 train next after the `g1-v6pq` member.
- The `C2` rehearsals give the first full forecast.
- The V2X rehearsal's select step was killed by the kernel's out-of-memory killer at 05:05 UTC (each select holds about 78 GB). It reruns after the LUMPI select.

**Pre-registered now (before any of these frames is scored):**
- LUMPI ships N1 `safe_frames` (fit on proxies 1-3 only; seed 0) if the organizers allow it. Otherwise it ships the 8 m variant, only if its gain holds on the held-out sets (it does: +0.0015, 9/10); otherwise `g1-v6pq`. (Corrected in Appendix B: the 8 m variant also changes only the 50 frames, so it ships only if the organizers' answer covers it.)
- V2X ships `aw_mid` if allowed; else `w_coarse` if W alone is allowed; else `g1-v6`.
- No frame choice depends on a server number.

#### 15.16.1 R1.1 on V2X passes rule 4; R1.2 starts (2026-11-11, 05:35-05:50 UTC)

Rule 4 against draw 1 (check log `w1_batch2.log`; `BDC_ALLOW_R1=1`):

| Member (reference) | Passes | Vehicle pooled (8-view) | Pedestrian pooled (8-view) | Truck pooled (8-view) |
|---|---|---|---|---|
| `voxelrcnn-ros-g1v6r1m` (`voxelrcnn-ros-g1v6`) | vehicle, pedestrian, vehicle 8v, truck 8v | +0.0253 (+0.0165) | +0.0166 (+0.0051; B -0.017) | -0.0215 (+0.0236) |
| `voxelrcnn-ros-swa-g1v6r1m` (`voxelrcnn-ros-swa-g1v6`) | vehicle, pedestrian, vehicle 8v | +0.0250 (+0.0073) | +0.0222 (+0.0101; B -0.010) | -0.0323 (-0.0008) |

- **The pre-registered rule (15.14.3):** R1.2, R1 draws 2-3, train for `C2` bags.
- `r12_v2x.sh` builds `pcdet/g1-v6d2r1m` and `g1-v6d3r1m`: the draw recipes with seeds 2234 and 3234, plus the anchors `static_anchors_r1_v2m`. It then makes the members `voxelrcnn-ros-g1v6d2r1m` and `d3r1m` (CLEAN with `BDC_ALLOW_R1=1`) and queues them after the GBlobs `rosf` d4-d5, ahead of the plain draws.
- **The R1 bag check (05:55 UTC).** The 5 draws plus the R1 member, against the 5-draw bags (rule 4):

  | Bag (reference) | Vehicle pooled (8-view) | Pedestrian pooled (8-view) | Truck pooled (8-view) | Passes |
  |---|---|---|---|---|
  | `bag-voxelrcnn-ros-g1v6r1x6` (`bag-voxelrcnn-ros-g1v6x5`) | +0.0048 (+0.0040) | +0.0035 (+0.0038) | +0.0019 (+0.0047, P 0.98) | 5 of 6 |
  | `bag-voxelrcnn-ros-swa-g1v6r1x6` (`bag-voxelrcnn-ros-swa-g1v6x5`) | +0.0042 (+0.0039) | +0.0047 (+0.0025) | +0.0013 (+0.0030, P 0.97) | 5 of 6 |

  - The R1 member adds diversity where the plain draws had saturated (pedestrian flat from the 5th draw, 15.10).
  - So the V2X `C2` pool takes the R1 bags (with `BDC_ALLOW_R1=1`), and a second V2X rehearsal with them (`c2r1`) follows the first.
- **R1.2 draw 2 (2026-11-11, 19:40 UTC).** `voxelrcnn-ros-g1v6d2r1m` against plain draw 2 (`voxelrcnn-ros-g1v6d2`, rule 4) passes only truck 8-view (+0.0073, P 0.93). Vehicle (-0.0026; 8-view -0.0016) and pedestrian (-0.0009; -0.0013) are level, with B up on vehicle (+0.013; 8-view +0.026). So R1.1's single-member gain over draw 1 (vehicle +0.025) was partly draw noise. R1 still earns its place only at bag level. The bag check of the R1 draws follows once `d3r1m` and the averaged `d2r1m` are tuned.
  - The averaged `voxelrcnn-ros-swa-g1v6d2r1m` against averaged plain draw 2: the same pattern; only truck 8-view passes (+0.0126, P 0.99), and vehicle and pedestrian are level (8-view +0.0021, +0.0012).
- **R1.2 draw 3 (2026-11-11, 21:55 UTC).** Against plain draw 3 (rule 4, `BDC_ALLOW_R1=1`):

  | Member (reference) | Passes | Vehicle pooled (8-view) | Pedestrian pooled (8-view) | Truck pooled (8-view) |
  |---|---|---|---|---|
  | `voxelrcnn-ros-g1v6d3r1m` (`voxelrcnn-ros-g1v6d3`) | pedestrian, truck | -0.0211 (-0.0201), both splits down | +0.0066 (+0.0030) | +0.0645 (+0.0004) |
  | `voxelrcnn-ros-swa-g1v6d3r1m` (`voxelrcnn-ros-swa-g1v6d3`) | pedestrian, truck, pedestrian 8v | -0.0222 (-0.0189), both splits down | +0.0064 (+0.0053) | +0.0709 (-0.0052) |

  - Across the three R1 draws the single-member vehicle effect is +0.025, level and -0.021. It is draw noise, not an R1 effect. R1 is judged at bag level only.
  - The bag check builds two shapes (`BDC_ALLOW_R1=1`), each against the 5-draw bag of its kind:
    - `r1x8`: the 5 draws plus the 3 R1 draws (8 members). This is the deployable candidate, but it mixes the R1 effect with bag depth (V2X depth still paid from 4 to 5 draws: vehicle +0.0037, truck +0.0155).
    - `r1s5`: draws 1-3 replaced by their R1 versions (5 members). This holds the size fixed and isolates R1.
- **The R1.2 bag check (22:50-23:12 UTC; rule 4, `BDC_ALLOW_R1=1`):**

  | Bag (reference) | Vehicle pooled (8-view) | Pedestrian pooled (8-view) | Truck pooled (8-view) | Passes |
  |---|---|---|---|---|
  | `bag-voxelrcnn-ros-g1v6r1x8` (`bag-voxelrcnn-ros-g1v6x5`) | +0.0076 (+0.0046) | +0.0067 (+0.0052) | +0.0194 (+0.0101) | 6 of 6 |
  | `bag-voxelrcnn-ros-swa-g1v6r1x8` (`bag-voxelrcnn-ros-swa-g1v6x5`) | +0.0087 (+0.0042) | +0.0049 (+0.0041) | +0.0161 (+0.0086) | 6 of 6 |
  | `bag-voxelrcnn-ros-g1v6r1s5` (`bag-voxelrcnn-ros-g1v6x5`) | -0.0001 (+0.0010) | +0.0070 (+0.0052) | +0.0059 (+0.0090) | 4 of 6 |
  | `bag-voxelrcnn-ros-swa-g1v6r1s5` (`bag-voxelrcnn-ros-swa-g1v6x5`) | -0.0003 (+0.0006) | +0.0053 (+0.0049) | +0.0015 (+0.0058) | 3 of 6 |
  | `bag-voxelrcnn-ros-g1v6r1x8` (`bag-voxelrcnn-ros-g1v6r1x6`) | +0.0028 (+0.0005) | +0.0031 (+0.0014) | +0.0175 (+0.0054) | 4 of 6 |
  | `bag-voxelrcnn-ros-swa-g1v6r1x8` (`bag-voxelrcnn-ros-g1v6r1x8`) | +0.0050 (+0.0014) | -0.0005 (-0.0003) | +0.0001 (-0.0020) | 2 of 6 |

  - **At a fixed size (`r1s5`), R1 helps pedestrian and truck, not vehicle.** The vehicle gain of `r1x8` is bag depth.
  - **So `r1x8` is the V2X R1 candidate for the final `C2`**, both kinds, with `BDC_ALLOW_R1=1`. As in `c2r1` (15.16.3), it competes at 8 views only until its R1 members have 12-view runs, so they lead the final 12-view wave (15.16.7).

#### 15.16.7 The final 12-view wave (planned 2026-11-11, 23:08 UTC)

- **Why.** In `c2r1` the R1 bags lost every class because only their 8-view outputs existed, while `C0`'s members had 12-view runs. 46 members of the candidate bags still have no 12-view runs.
- **Queue** `jobs_tta12_w5.txt` (46 jobs, `tune_and_eval.sh --tta flip4+yaw+z+scale --tta-tag tta12 --reuse-raw`, as in 15.13.7), in this order:
  1. V2X: the six R1 members of `r1x8` (averaged first), then the four GBlobs draws 2-3 (vehicle fusion candidates, 15.16.3). V2X goes first because its last upload closes first (Nov 15 04:59 UTC).
  2. LUMPI: the ten members of the GBlobs `pqx5` bags (averaged first), then `rosf` draw 5 (plain and averaged).
  3. LUMPI: the six R1 members, the six `rosn-gblobs`, the six `pvrcnnpp-ros-gblobs`, PV draws 4-5; then V2X VoxelNeXt draw 6.
- **Mechanics.** `t12_at_drain2.sh` hands each trainer's four GPUs (trainA2: 1, 3, 5, 7; trainB2: 0, 2, 4, 6) to the queue at that trainer's end of queue, one fixed-GPU worker each (`t12x<gpu>`).
  - Each job (`t12f_job.sh`) waits for its member's 8-view tuning step, then for 46 GB free on its GPU. So training never shares a GPU with a 12-view job, and a member still in training waits its turn.
  - Eight averaged members of the late draws are made at their plain member's `TRAIN_DONE`, as usual.
- **Timing.** Past 12-view jobs took 30-45 min (V2X) and 55-75 min (LUMPI). That is about 45 GPU-hours over 8 GPUs, so the wave ends about 6 h after the train queue drains (about Nov 13 04:00 UTC). The final `C2` builds follow, V2X first.

#### 15.16.2 R1.1 on LUMPI passes rule 4; R1.2 starts (2026-11-11, 06:35 UTC)

- **`voxelrcnn-rosf-swa-g1v6r1m` against `voxelrcnn-rosf-swa-g1v6`: passes 6 of 14.**
  - Bicycle +0.0273 (8-view +0.0125), Van +0.0121 (+0.0091), Person 8-view +0.0068 (P 0.99), Car 8-view +0.0015.
  - Loses Truck (-0.016 / -0.020), Motorcycle and Bus.
- **R1.2 on LUMPI (`r12_lumpi.sh`).** Corpora `pcdet/g1-v6d2r1m` and `g1-v6d3r1m`: draw recipes with seeds 2234 and 3234, plus `static_anchors_r1_v2m`. Members `voxelrcnn-rosf-g1v6d2r1m` and `d3r1m` are queued after the V2X R1 draws.
- **Train queue:** 14 members, ending about Nov 13 03:30 UTC, before the 18:00 stop.
- **`voxelrcnn-rosf-g1v6r1m` against `voxelrcnn-rosf-g1v6` (06:50 UTC): passes 6 of 14.** Person +0.0174 (8-view +0.0114), Bicycle +0.0300 (+0.0162), Car 8-view +0.0182, Van 8-view +0.0065. Loses Truck, Motorcycle and Bus.
- **Against `C0`'s Person member on late-A (rule 15),** both R1 members are far behind:
  - plain -0.065 and averaged -0.067 (8-view -0.051 / -0.052), all at P 0.00;
  - on B: -0.019 / -0.016 plain, +0.001 / +0.004 8-view.
  - So R1 will not carry LUMPI Person. Its LUMPI value is Bicycle, Van and Car, which `C2`'s gates judge.
- **R1.2 draw 2 (2026-11-12, 02:00 UTC).** Against plain draw 2 (rule 4, `BDC_ALLOW_R1=1`):

  | Member (reference) | Passes | Person pooled (8-view) | Car | Bicycle | Van | Truck |
  |---|---|---|---|---|---|---|
  | `voxelrcnn-rosf-g1v6d2r1m` (`voxelrcnn-rosf-g1v6d2`) | 6 of 14 | -0.0086 (-0.0037) | +0.0060 (+0.0055) | +0.0074 (-0.0006) | -0.0060 (-0.0029) | +0.0109 (+0.0044) |
  | `voxelrcnn-rosf-swa-g1v6d2r1m` (`voxelrcnn-rosf-swa-g1v6d2`) | 4 of 14 | -0.0121 (-0.0056) | +0.0053 (+0.0029) | +0.0109 (-0.0007) | -0.0047 (-0.0018) | +0.0063 (+0.0032) |

  - Car holds for both kinds, and Bicycle at plain only. Person, Van and Motorcycle drop.
  - So R1.1's Person and Van gains over draw 1 were partly draw noise, as on V2X (15.16.1). LUMPI R1 is judged at bag level (`bag-voxelrcnn-rosf-[swa-]g1v6r1x8` and `r1s5`, built as on V2X) once draw 3 is tuned.
- **R1.2 draw 3 (2026-11-12, 04:40-06:50 UTC).** Against plain draw 3 (rule 4):
  - `voxelrcnn-rosf-g1v6d3r1m` passes 5 of 14: Bicycle +0.0162, Car +0.0009 (8-view +0.0020), Bus, Van 8-view. Person -0.0072 (8-view -0.0053) and Truck 8-view -0.0129 drop.
  - `voxelrcnn-rosf-swa-g1v6d3r1m` passes 4 of 14: Bicycle +0.0109, Bus, Car 8-view, Van 8-view. Person is level (-0.0002; 8-view -0.0022), and Truck 8-view drops (-0.0164).
  - The plain member's 8-view step failed once and passed on the post worker's retry (the retry overwrote the step log, so the cause is not recorded).
- **The LUMPI R1 bag check (06:50 UTC; rule 4, `BDC_ALLOW_R1=1`).** Each bag against the 5-draw bag of its kind:

  | Bag | Passes | Person pooled (8-view) | Car | Bicycle | Van | Truck | Motorcycle |
  |---|---|---|---|---|---|---|---|
  | `bag-voxelrcnn-rosf-g1v6r1x8` | 11 of 14 | +0.0095 (+0.0066) | +0.0043 (+0.0074) | +0.0106 (+0.0099) | +0.0009 (+0.0011) | +0.0044 (-0.0010) | -0.0008 (-0.0045) |
  | `bag-voxelrcnn-rosf-swa-g1v6r1x8` | 11 of 14 | +0.0053 (+0.0010) | +0.0041 (+0.0037) | +0.0092 (+0.0088) | +0.0030 (+0.0028) | +0.0017 (-0.0012) | -0.0022 (-0.0031) |
  | `bag-voxelrcnn-rosf-g1v6r1s5` (swap) | 7 of 14 | +0.0102 (+0.0049) | +0.0024 (+0.0059) | +0.0092 (+0.0108) | -0.0009 (+0.0009) | +0.0000 (-0.0066) | -0.0045 (-0.0087) |
  | `bag-voxelrcnn-rosf-swa-g1v6r1s5` (swap) | 7 of 14 | +0.0034 (-0.0002) | +0.0028 (+0.0030) | +0.0092 (+0.0098) | +0.0021 (+0.0031) | -0.0042 (-0.0075) | -0.0033 (-0.0077) |

  - **At a fixed size (`r1s5`), R1 helps Car and Bicycle on LUMPI, and plain Person.** The `r1x8` bags add Bus, Van and part of Truck through depth.
  - **Late-A Person (rule 15 view):**
    - `r1x8` against `x5`: plain +0.0053 (P 0.97; 8-view +0.0020, P 0.83); averaged +0.0012 (8-view -0.0022, P 0.24).
    - The 8-view `r1x8` bags against `C0`'s Person member (`voxelrcnn-rosn-g1v6`, 12-view): late-A -0.0227 / -0.0222 (P 0.00), B +0.0128 / +0.0189.
    - The averaged 8-view `r1x8` against the averaged GBlobs `pqx5` bag: late-A -0.0360, B -0.0068 (both P 0.00).
  - **So the LUMPI R1 bags are not a Person route.** Person stays with the GBlobs `pqx5` bags (15.16.6). The `r1x8` bags enter the final `C2` pool (with `BDC_ALLOW_R1=1`) as Car, Bicycle, Van and Bus candidates. As on V2X, they compete at 8 views until their R1 members' 12-view runs (15.16.7) are done; rule 14b's class gate decides.
  - The six LUMPI R1 members are already in the 12-view queue (`jobs_tta12_w5.txt`, group 3).

#### 15.16.3 The V2X `C2` rehearsal (`routed-c2r`, 2026-11-11, 04:42-07:25 UTC)

- **Pool and settings:** C1's 65 clean folders (no R1 member), rule 14b against `routed-c1a` (`c1av5`), frames `g1-v6`.
- **Class gate:**
  - truck **kept**: pooled +0.0033 at P 0.99, B +0.0045 at P 0.93 (R3's +0.01 bar would have reverted it);
  - vehicle reverted (-0.016);
  - pedestrian reverted (pooled -0.0003, P 0.47; `c1av5` already has V5).
- **Rule 14 at grouped P 0.8:** GO. Pooled mAP +0.0011 (A +0.0012, B +0.0015), grouped P 0.97 over 57 scenarios; none of the 57 leave-one-scenario-out deltas is negative (worst +0.0007).
- **Package.** `model-v2x-track/routed-c2r/submissions/2026-11-10_c2r/v2x_s10_submission.zip`, md5 `9f836506b943141b4cdce78648e143c7`, `g1-v6` frames with nulls 0.31. Kit check valid (41,252 boxes, 253 s).
- **Projection against `c1av5`: +0.0007.** V2X GO changes have transferred at a median of 0.60x (0.24-1.86x), so expect about +0.0004 (0.0002-0.0013).
- **This is the V2X upload 4 candidate under the slot rule** (projection > 0, rule 1, grouped P >= 0.8). It is decided against `c2r1` below by the same rule.
- **`c2r1` (with the R1 member and the two R1 bags, `BDC_ALLOW_R1=1`; 07:25-09:20 UTC): every class reverted to `routed-c1a`.**
  - Select routed vehicle and truck to the averaged R1 bag (8-view only).
  - Fuse kept vehicle `bvrrosswa6x4_tta12` + `bvrros6r1x6_tta` at 0.7 and truck `bvrrosswa6r1x6_tta` + `bvrros6r1x6_tta` at 0.3.
  - Against `c1av5`'s final predictions: vehicle -0.013 and truck -0.016 pooled (both P 0.00), pedestrian flat.
  - The R1 bags have no 12-view runs yet (they follow the Nov 13 stop), and the 12-view C0 members still win.
  - The build was stopped by PID group after the gate; a re-package of `c1av5` was not needed.
  - **V2X upload 4 candidate: `c2r`.** The R1 bags come back in the final `C2` with their 12-view runs.
- **The frames follow the entrant's choice on 15.16:** `aw_mid` only after the organizers allow it. Otherwise `g1-v6`.
- **The V2X GBlobs 3-draw bags (10:30 UTC)** against the xyz 3-draw bags (rule 4):
  - `bag-voxelrcnn-ros-gblobs-g1v6x3` passes vehicle: +0.0128, 8-view +0.0149;
  - `bag-voxelrcnn-ros-gblobs-swa-g1v6x3` passes vehicle: +0.0114, 8-view +0.0097;
  - both lose pedestrian (-0.046 to -0.051, P 0.00) and slightly truck.
  - As in S5, GBlobs on V2X is a vehicle fusion candidate for the final `C2`, not a pedestrian lever.

#### 15.16.4 The LUMPI `C2` rehearsal (`routed-c2r`, 2026-11-11, 04:44-08:10 UTC)

- **Pool and settings:** C1's 80 clean folders plus the 10 GBlobs folders; rules 14b and 15 against `routed-c0`; frames `g1-v6pq`.
- **Fuse.** Person = `bvrrosfswa6x4_tta12` + `bvrrosfgblobsswa6x3_tta` at IoU 0.7 (`C1`'s averaged xyz bag fused with the averaged GBlobs 3-draw bag).
- **Class gate:**

  | Class | A | B (P) | Pooled (P) | Late-A (P) | Decision |
  |---|---|---|---|---|---|
  | Person | +0.0150 | +0.0142 (1.00) | +0.0160 (1.00) | **+0.0133 (1.00)** | kept (rule 15 passed) |
  | Car | -0.0002 | -0.0050 (0.00) | -0.0010 | | reverted |
  | Bicycle | -0.0164 | -0.0056 (0.05) | -0.0104 | | reverted |
  | Bus | +0.0012 | -0.0006 (0.61) | +0.0012 (0.65) | | reverted |
  | Truck | -0.0143 | -0.0057 (0.15) | -0.0070 | | reverted |

  - `C1`'s Person route alone lost on late-A (-0.0055 at P 0.02). Fused with the GBlobs bag it gains +0.0133 at P 1.00.
  - The GBlobs encoding fixes the late-window weakness, as the member check of 15.15.10 suggested.
- **Rule 14 (grouped P 0.8):** GO. Pooled mAP +0.0023 (A +0.0021, B +0.0020), grouped P 1.00 over 28 groups, 90% CI [+0.0015, +0.0027]. None of the 28 leave-one-group-out deltas is negative (worst +0.0017). The rare-class share of the gain is 0.
- **Rule 1:** PASS (13 members).
- **Projection: about +0.0011 combined** against `C0`'s detections. History: Person changes with late-A > 0 and B > 0 gained on the server 6 of 6 times; LUMPI Person transfer has a median of 1.24x.
- **With N1 frames** (if the organizers allow them; 15.16), the LUMPI last upload would be about 0.5413 + 0.0011 + 0.0021 = 0.5445 central, and 0.5431-0.5458 over the past transfer range. **Without them:** about 0.5424.
- **The pre-registered choice for the LUMPI last upload:**
  - the final `C2`, built after the Nov 13 18:00 UTC stop with GBlobs draws 4-5, the `g1-v6pq` member and the R1 draws, if it passes rules 1, 14b, 15 and 14 and its projection is at least `c2r`'s;
  - otherwise `c2r` as packaged.
  - Upload by Nov 15 18:00 UTC, which leaves margin before the 2026-11-16 04:59 UTC close.
- **`c2r` package (09:00 UTC).**
  - `model-lumpi-track/routed-c2r/submissions/2026-11-11_c2r/lumpi_s10_submission.zip`, md5 `9fe2ec6102f06a0fd2160e9016b6cf13`.
  - The Person copy threshold was re-fitted (t 0.7472, 24,654 kit boxes), and the zip re-packaged.
  - Kit check valid (24,654 boxes, 244 s).
  - The frames are byte-identical to 1047231's, so the realism term is known exactly (R 0.935524). The expected score is 0.541329 + the detection gain (+0.0011 projected), about 0.5424.
  - This is the fallback for the LUMPI last upload.
- **Queue end:** about Nov 12 22:00 UTC, before the Nov 13 18:00 stop.
- **The LUMPI R1.1 members** are still tuning; one 8-view step failed once and was retried.

#### 15.16.5 The L2 member: the `g1-v6pq` GBlobs member against draw 1 (2026-11-11, 12:25 UTC)

- **Rule 4** (`w1_batch2.log`): `voxelrcnn-rosf-gblobs-g1v6pq` against `voxelrcnn-rosf-gblobs-g1v6` passes Person (+0.0370 pooled, 8-view +0.0309, P 1.00) and Bus (+0.0092, 8-view +0.0057). No class passes the other way; Truck plain is down (-0.0122, P 0.00) and level at 8-view (+0.0005).
- **Late-A Person** (the rule 15 split): +0.0262 plain and +0.0263 8-view against draw 1, both at P 1.00; B +0.0152 and +0.0247.
- **Against `C0`'s Person member** (`voxelrcnn-rosn-g1v6`, 12-view): the 8-view pq member is level on late-A (-0.0027, P 0.40) and ahead on B (+0.0214, P 1.00). The plain pq member is behind on both (late-A -0.0245).
- **Reading.** The pre-registered expectation of 15.15.7 ("no class expected to differ") does not hold: the near-field re-cast helps Person, on the late window too. It is one draw, so part of the gain can be draw noise (GBlobs draws 1-3 differ on Person by up to 0.02).
- **No change to the plan.** As pre-registered, the pq member replaces GBlobs draw 1 in the GBlobs bags of the final `C2`. Once its averaged member (`voxelrcnn-rosf-gblobs-swa-g1v6pq`) is tuned, the 3-draw replacement bags (pq, d2, d3; plain and averaged) are checked against the `x3` bags by rule 4 as a diagnostic.
- **The averaged pq member (12:30 UTC)** against averaged draw 1 passes Person (+0.0267, 8-view +0.0255), Bus, and at 8-view Car, Bicycle and Van; Truck is down (-0.0164 plain, -0.0066 8-view). Late-A Person 8-view +0.0143 (P 1.00).
- **The replacement bags (diagnostic; both CLEAN):**

  | Bag (reference) | Passes | Person pooled (8-view) | Person late-A 8-view (P) | Against `C0`'s Person member, 8-view: late-A (P) / B |
  |---|---|---|---|---|
  | `bag-voxelrcnn-rosf-gblobs-g1v6pqx3` (`...-g1v6x3`) | Person, Bus | +0.0103 (+0.0091) | +0.0137 (1.00) | -0.0079 (0.12) / +0.0241 |
  | `bag-voxelrcnn-rosf-gblobs-swa-g1v6pqx3` (`...-swa-g1v6x3`) | Person, Bus, Car 8v | +0.0082 (+0.0092) | +0.0008 (0.72) | **+0.0089 (0.98)** / +0.0261 |

  - Bicycle is slightly down in the plain bag (-0.0052, P 0.01) and Truck in both (about -0.003).
  - The averaged replacement bag is the best Person fusion partner so far against `C0`'s member: its late-A edge is +0.0089, against +0.0081 for the averaged `x3` bag that `c2r` fuses.
  - The swap is kept for the final `C2` as pre-registered. The rehearsal `c2r` stays as packaged; the final `C2` gate decides.

#### 15.16.6 The 5-draw GBlobs bags (pq for draw 1): the strongest LUMPI Person and Bicycle candidates (2026-11-11, 20:00 UTC)

Bags `bag-voxelrcnn-rosf-gblobs-g1v6pqx5` and `bag-voxelrcnn-rosf-gblobs-swa-g1v6pqx5` (members: the `g1-v6pq` member and GBlobs draws 2-5; both CLEAN). Rule 4, pooled A+B (8-view in brackets):

| Bag | Reference | Passes | Person | Bicycle | Car | Truck |
|---|---|---|---|---|---|---|
| plain x5 | GBlobs pq x3 | 11 of 14 (every class but Motorcycle; Bus 8v) | +0.0045 (+0.0073) | +0.0135 (+0.0058) | +0.0059 (+0.0043) | +0.0135 (+0.0096) |
| averaged x5 | averaged GBlobs pq x3 | 9 of 14 | +0.0059 (+0.0028) | +0.0125 (+0.0054) | +0.0054 (+0.0008) | +0.0117 (+0.0106) |
| plain x5 | xyz x5 (`bag-voxelrcnn-rosf-g1v6x5`) | Person, Bicycle, Bus, Van; Truck plain | +0.0257 (+0.0214) | +0.0303 (+0.0285) | -0.0021 (+0.0036) | +0.0043 (-0.0046) |
| averaged x5 | averaged xyz x5 | Person, Bicycle, Van | +0.0261 (+0.0190) | +0.0311 (+0.0274) | -0.0024 (+0.0011) | -0.0004 (-0.0018) |

- **Depth still pays for GBlobs.** Unlike the xyz bags, which saturated at 5 draws (15.10), 3 to 5 GBlobs draws gain on five classes, Truck included.
- **Person against `C0`'s Person member** (`voxelrcnn-rosn-g1v6`, 12-view), late-A / B:
  - averaged x5, 8-view: **+0.0138 (P 0.99) / +0.0257**;
  - averaged x5, plain: +0.0136 (P 1.00) / +0.0176;
  - plain x5, 8-view: +0.0038 (P 0.91) / +0.0270.
  - The averaged 5-draw GBlobs bag alone now beats `C0`'s Person route on both splits, late-A included. Until now it was only a fusion partner (`c2r` fuses the averaged x3 bag: +0.0133 late-A after fusion).
- **Motorcycle** stays weak against the xyz bags (-0.012 to -0.018, P <= 0.09). The class gate keeps `C0`'s Motorcycle route unless a candidate passes.
- **For the final `C2`:** the x5 GBlobs bags enter the LUMPI pool, with 12-view tuning of their members. Rules 14b and 15 decide as pre-registered; this check changes no rule.
- **Timing.** The train queue drains about Nov 12 22:00 UTC, before the Nov 13 18:00 UTC stop. The 12-view tuning starts on each GPU as its trainer frees up, and the final `C2` builds start once it is done. That leaves more margin before the last uploads (V2X close Nov 15 04:59 UTC; LUMPI upload by Nov 15 18:00 UTC). No new draw is added: the remaining value of more GBlobs depth (5 to 7 draws) is likely below +0.001 combined, less than the cost of a late or failed final build.

#### 15.16.8 The 3-draw `rosn` GBlobs bags (2026-11-12, 10:15-10:55 UTC)

Wave 5's probe rule (15.13.9) trained GBlobs draws 2 and 3 of `voxelrcnn-rosn-gblobs-g1v6` because draw 1 passed rule 4 over `voxelrcnn-rosn-g1v6` (Person, Bicycle, Bus). Draw 3 and its averaged member were tuned by 10:15 UTC (the averaged member's 8-view step failed once and passed on retry). Bags `bag-voxelrcnn-rosn-gblobs-g1v6x3` and `bag-voxelrcnn-rosn-gblobs-swa-g1v6x3` (draws 1-3, the iou of the `rosn` bags; both CLEAN).

**Rule 4, pooled A+B** (8-view in brackets):

| Bag | Reference | Passes | Person | Bicycle | Bus | Truck |
|---|---|---|---|---|---|---|
| plain x3 | `rosn` x3 | 8 of 14 (Person, Bicycle, Bus, Van plain; Car 8v) | +0.0170 (+0.0145) | +0.0436 (+0.0416) | +0.0149 (+0.0163) | -0.0100 (-0.0087) |
| averaged x3 | averaged `rosn` x3 | 6 of 14 (Person, Bicycle, Bus) | +0.0180 (+0.0128) | +0.0356 (+0.0353) | +0.0188 (+0.0203) | -0.0076 (-0.0089) |
| averaged x3 | plain GBlobs x3 | 3 of 14 (Person plain, Bus) | +0.0022 (+0.0009) | -0.0039 (-0.0015) | +0.0049 (+0.0040) | +0.0000 (+0.0005) |

- **GBlobs gains hold at bag level for `rosn`**, as they did for `rosf` (15.16.6): Person, Bicycle and Bus, on both splits. Truck loses about 0.01 at P <= 0.01, and Motorcycle stays weak (P <= 0.31).
- **Averaging the weights adds little here**: level with the plain bag apart from Bus.

**Person on late-A (rule 15) and on B**, delta (P):

| Bag | vs `C0`'s Person member (12-view) | vs `rosn` x3, same views | vs GBlobs pq x5, same views | vs averaged GBlobs pq x5, same views |
|---|---|---|---|---|
| plain x3, 8-view | +0.0009 (0.74) / +0.0211 | +0.0172 (1.00) / +0.0089 | -0.0029 (0.22) / -0.0059 | -0.0128 (0.00) / -0.0047 |
| averaged x3, 8-view | +0.0009 (0.78) / +0.0215 | +0.0171 (1.00) / +0.0093 | -0.0029 (0.23) / -0.0054 | -0.0129 (0.01) / -0.0042 |
| plain x3, plain | -0.0021 (0.38) / +0.0132 | +0.0363 (1.00) / +0.0102 | -0.0078 (0.04) / -0.0031 | -0.0157 (0.00) / -0.0043 |
| averaged x3, plain | -0.0027 (0.36) / +0.0153 | +0.0357 (1.00) / +0.0122 | -0.0084 (0.04) / -0.0011 | -0.0163 (0.00) / -0.0023 |

- **Rule 15: the 8-view bags pass, barely** (+0.0009 at P 0.74 to 0.78 against `C0`'s 12-view Person member; B +0.021). The plain-view bags fail.
- **The averaged 5-draw GBlobs pq bag stays the LUMPI Person lead**: on late-A it is +0.0138 over `C0`'s member (15.16.6), and the `rosn` GBlobs bags trail it by about 0.013 on late-A and 0.004 on B.

**Against the GBlobs pq 5-draw bags** (rule 4 across families, for the record; 11:10 UTC):

| Bag | Reference | Passes | Person | Bicycle | Bus | Van |
|---|---|---|---|---|---|---|
| plain x3 | GBlobs pq x5 | Bus only | -0.0101 (-0.0075) | -0.0279 (-0.0169) | +0.0085 (+0.0127) | -0.0029 (-0.0038) |
| averaged x3 | averaged GBlobs pq x5 | Bus only | -0.0116 (-0.0088) | -0.0437 (-0.0294) | +0.0178 (+0.0173) | -0.0039 (-0.0039) |

- **Bus is the one class where the `rosn` GBlobs bags add to the pool** (P 1.00 on both kinds and views, both splits up). Bus AP is small (A 0.01, B 0.04), so a route gain of +0.018 is worth at most about +0.0026 mAP, or +0.0022 combined.
- **Person and Bicycle stay with the GBlobs pq x5 bags**, which beat these bags on both splits.
- **For the final `C2`:** the two bags join the LUMPI pool as Bus candidates and possible Person fusion partners, with 12-view tuning of their six members (already in the wave, 15.16.7). The `C2` select and rules 14b and 15 decide as pre-registered; this check changes no rule. No further `rosn` GBlobs draw is added (the 15.16.6 reasoning).

#### 15.16.9 The last depth draws: VoxelNeXt draw 6 (V2X) and PV-RCNN++ draws 4-5 (LUMPI) (2026-11-12)

Option A (15.13) queued these as depth for the bags. Bags `bag-voxelnext-ros-g1v6x6` and `bag-voxelnext-ros-swa-g1v6x6` (draws 1-6), and `bag-pvrcnnpp-ros-g1v6x5` and `bag-pvrcnnpp-ros-swa-g1v6x5` (draws 1-5); each pair is built when its last member is tuned.

**V2X VoxelNeXt, 6 draws against 5** (13:00-14:20 UTC; both CLEAN). Rule 4, pooled A+B (8-view in brackets):

| Bag | Reference | Passes | vehicle | pedestrian | truck |
|---|---|---|---|---|---|
| plain x6 | plain x5 | 3 of 6 (pedestrian plain, truck both) | -0.0007 (-0.0006) | +0.0044 (+0.0005) | +0.0149 (+0.0073) |
| averaged x6 | averaged x5 | 3 of 6 (vehicle and pedestrian plain, truck 8v) | +0.0012 (**-0.0022, P 0.01**) | +0.0048 (-0.0003) | +0.0040 (+0.0039) |
| averaged x6 | plain x6 | 3 of 6 (all three plain) | +0.0040 (+0.0013) | +0.0056 (+0.0011) | +0.0043 (+0.0024) |

- **Vehicle has saturated for VoxelNeXt at 5 draws**, against the 15.13 forecast that draw 6 would serve vehicle and truck: plain x6 is level (P 0.25 to 0.41), and the averaged x6 bag loses 0.0022 at 8 views.
- **Truck still gains with depth** (+0.004 to +0.015, mostly on B). Pedestrian gains only without test-time views.
- **Value:** the 8-view A/B mean is 0.6509 (averaged x6) against 0.651 (averaged x5, 15.10), so level overall. If VoxelNeXt carries truck in a route, +0.004 truck AP is about +0.0013 mAP, or +0.0011 combined; otherwise about zero.
- **For the final `C2`:** both bags join the V2X pool, with 12-view tuning of the two draw 6 members (last in the wave, 15.16.7). The `C2` select and rule 14b decide; this check changes no rule.

**LUMPI PV-RCNN++, 5 draws against 3** (14:25-15:05 UTC; both CLEAN). Alone, draws 4 and 5 are weaker than draw 1, as draw 3 was (draw 4 plain passes only Car and Motorcycle at 8 views; Person -0.011 and Truck -0.029 at 8 views; STATUS 11:05 UTC). Rule 4, pooled A+B (8-view in brackets):

| Bag | Reference | Passes | Person | Car | Bicycle | Truck |
|---|---|---|---|---|---|---|
| plain x5 | plain x3 | 9 of 14 (Person, Car, Bicycle, Van both; Motorcycle 8v) | +0.0083 (+0.0036) | +0.0020 (+0.0019) | +0.0041 (+0.0030) | -0.0059 (**-0.0101, P 0.00**) |
| averaged x5 | averaged x3 | 8 of 14 (Car, Bicycle, Van both; Person, Motorcycle plain) | +0.0047 (+0.0001) | +0.0023 (+0.0033) | +0.0051 (+0.0044) | **-0.0093 (-0.0104), P 0.00** |
| averaged x5 | plain x5 | 4 of 14 (Person plain, Van both, Car 8v) | +0.0019 (-0.0003) | +0.0012 (+0.0007) | +0.0003 (+0.0004) | +0.0032 (-0.0018) |

- **Depth still pays a little for PV on five classes**, but Truck loses about 0.01, all of it on A (-0.012 to -0.024; B is level).
- **Person, late-A** (8-view bags against `C0`'s 12-view Person member): plain x5 -0.0063 (P 0.18), averaged x5 -0.0069 (P 0.15); B +0.004 and +0.003. Against the averaged GBlobs pq x5 bag both trail by about 0.020 on late-A and 0.022 on B. **So no PV bag is a Person route**, and rule 15 would reject one.
- **For the final `C2`:** both bags join the LUMPI pool as Car, Bicycle and Van candidates and fusion partners, with 12-view tuning of the four draw 4-5 members (in the wave, 15.16.7). Truck stays with whichever route the class gate keeps. The `C2` select and rules 14b and 15 decide; this check changes no rule.

### 15.17 The organizers' answer on frame calibration, what it changes, and the plan to the close (2026-11-12, 15:00-16:30 UTC)

**The answer** (Appendix B.4; received 2026-11-12 08:33 CST = 14:33 UTC; the entrant's copy):
- "The 50 submitted frames are meant to represent the synthetic data your detector was trained on, so that the realism score and the detection score describe the same data."
- So a calibration applied **only to the 50 frames, with the training data unchanged, is not allowed** on either track.
- Both methods (the LUMPI 2 m density prior and the V2X range mapping) **are acceptable as part of the data generator**: apply the calibration to the training data, retrain the detector on it, and submit 50 frames from that calibrated data.
- The report must describe the calibration, the real frames it was fitted on, and how the 50 frames were chosen.

**What it means for every upload and package** (frames against the corpora the detector was trained on):

| Upload or package | Realism frames | Detector trained on that data? | Under the answer |
|---|---|---|---|
| LUMPI 1042287 (`C0`, 0.5408) | 50 `g1-v6` frames as generated | yes: every member trained on the `g1-v6` family (`g1-v6`, `d2`, `j`) | **meets it** |
| LUMPI 1047204 (`c1pq`, 0.5396) | the same ids from `g1-v6pq` (PandarQT near-field re-cast) | **no**: no member trained on `g1-v6pq` | **does not meet it** |
| LUMPI 1047231 (`c0pq`, 0.5413, the board entry) | as `c1pq` | **no**: `C0`'s members, none trained on `g1-v6pq` | **does not meet it** |
| V2X 1042294 (`C0`) and 1046758 (`c1av5`, 0.8889, the board entry) | 50 `g1-v6` frames; 31% (0,0,0) no-return points added at packaging | yes for every real point. The loader removes (0,0,0) points in training and inference (`BDCDataset.get_lidar`, `strip_nulls`), so the detector sees the same valid points either way | meets it in substance: the nulls are the real sensor's no-return encoding (about 29-31% in the legal real frames and in the organizers' reference), not a fit to the data (about 31% in the legal real frames as resampled to the organizers' format). Low risk; the report says so |
| Held `c2r_n1_pending` (LUMPI N1) and `c2r_aw_pending` (V2X `aw_mid`) | frames-only calibrations | no | **not allowed; withdrawn** (never uploaded) |
| LUMPI `c2r` package (2026-11-11, `g1-v6pq` frames) | as `c0pq` | no | not allowed; **re-packaged as `c2rv6`** with `C0`'s frames |
| Pre-registered `C2` frames `g1-v6pq` (L2: one `g1-v6pq` member in the GBlobs bags) | `g1-v6pq` | one member of about 20 checkpoints | **dropped**: the answer speaks of "the data your detector was trained on", and the other members never saw `g1-v6pq`. LUMPI `C2` ships `g1-v6` frames |

- **The waiver was the mistake.** Our own rule (docs/01 Section 9, "submitted synthetic frames come from the same generator configuration as the training corpus"; S10 rule 1's frame clause) said the same as the answer. Package A waived it for `c1pq` and `c0pq` (15.15.7). The organizers' principle restores it, now as their rule.
- **Cost of compliance on LUMPI:** 1047231's frames gained +0.001324 R (+0.000529 combined) over 1042287. Without them the best compliant LUMPI entry is 1042287 (0.5408). The rank does not change (2nd; 3rd is 0.5354).
- **The entrant's decision:** a short disclosure asking the organizers to drop 1047204 and 1047231 from our ranking (draft in Appendix C). The 10.1 release notes state the same facts either way.

**Standing** (the entrant's screenshots, Results and My Submissions, 2026-11-12 07:59-09:04 CST):

| Track | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| LUMPI | lukefinigan **0.5440** (1042827, Nov 8; mAP 0.1953, R 0.9415, CD 1.186, EMD 1.124) | **KarmaRV 0.5413** (1047231; mAP 0.1950, R 0.9355, CD 1.467, EMD 1.246) | sadbodh 0.5354 (Nov 10; mAP 0.1859, R 0.9401) | dipper13579 0.5278 |
| V2X | **KarmaRV 0.8889** (1046758; mAP 0.5981, R 0.9405, CD 1.844, EMD 1.110) | sadbodh 0.8616 (1048897, Nov 11; mAP 0.5625, R 0.9486, CD 1.170, EMD 0.976) | arnav007 0.8475 (Nov 11; mAP 0.5491, R 0.9421) | lukefinigan 0.8334 |

(R derived from combined = 0.6 x mAP / 0.7 + 0.4 x R.)
- **LUMPI gap** from the compliant 1042287: 0.0032. lukefinigan's mAP term is level with ours (0.1953 against 0.1950); the gap is realism, 0.0073 R (0.0029 combined). To pass 0.5440 a compliant entry needs about +0.0037 mAP with our frames, or +0.008 R with our detections, or a mix.
- **V2X lead** 0.0273 over sadbodh, who gained +0.0066 since Nov 9. sadbodh's realism is higher (0.9486); our mAP is higher by 0.036.
- **Uploads.** The final phase page now shows **8 in total and 4 a day** (docs/01 had 5 and 1). The page counts 3 LUMPI and 2 V2X uploads; the organizers said the removed 1038963 and 1038966 still count. So **LUMPI has 4 left and V2X 5** (one more each if the page's count is the one enforced).
- **Close.** Both phase pages end "November 15, 2026 at 10:59 PM CST" = **2026-11-16 04:59 UTC on both tracks** (V2X was planned to Nov 15 04:59 UTC). The plan keeps every last upload before Nov 15 18:00 UTC.

**Levers left** (expected server gain in combined score; compliant ones only):

| # | Lever | Track | What it takes | Expected | Rule fit | Risks |
|---|---|---|---|---|---|---|
| A1 | `c2r` as packaged (`g1-v6` frames, nulls 0.31; rule 14 GO) | V2X | ready (md5 `9f836506...`) | +0.0004 (0.0002-0.0013) | meets the answer (frames as `C0`'s) | small |
| A2 | `c2rv6`: `c2r`'s detections with `C0`'s frames (byte-identical to 1042287's) | LUMPI | ready (below) | 0.5408 + 0.0011 projected = **about 0.5419** (Person transfer history: 6 of 6 gained, median 1.24x) | meets it | the Person route is the whole gain |
| A3 | final `C2` (12-view wave, GBlobs x5, R1 x8, `rosn` GBlobs, PV x5, VoxelNeXt x6) with training-corpus frames | both | 12-view wave (about 16:00-22:00 UTC), then the two selects in turn (78 GB each) | LUMPI +0.001 to +0.003 over `C0`; V2X +0.0005 to +0.002 | meets it | late or failed build: A1 and A2 stay |
| **B** | **The calibrated LUMPI generator, as the organizers allow it:** the PandarQT re-cast and the N1 density re-draw (2 x 2 x 0.5 m, fitted on proxies 1-3) applied to `C0`'s three corpora; all 14 `C0` checkpoints retrained from scratch on them; `C0`'s route, fusion and calibration recipe unchanged; the same 50 ids taken from the calibrated `g1-v6` | LUMPI | code and test about 3 h (CPU), corpora about 2 h (CPU) during the 12-view wave; training about 24-30 h on both trainers (Nov 12 22:00 to about Nov 14 02:00-04:00 UTC; the GPUs are otherwise idle); tuning and 12-view about 4 h; package about Nov 14 12:00 UTC | realism vs `C0`: pq +0.0013 R (server-measured) plus N1 +0.0076 local at 0.31-1.0x = **0.5423 / 0.5434 / 0.5444** (low / central / high), plus an unknown detection change from the calibrated training | **meets the answer exactly** ("apply the same calibration to your training data, retrain your detector on it, and submit 50 frames from that calibrated data"); report lists the fit frames | the detection change is unmeasured (N1 makes 34% of points jittered copies); disk (/ at 97%, about 50 GB needed); no select is needed (the recipe is reused), only a merge and the gate; it does not carry `C2`'s detection gains |
| C | The calibrated V2X generator (W range map) and the 4 `c1a` checkpoints retrained | V2X | about 8 h of both trainers after B | +0.002 to +0.004 (`aw_mid` +0.0100 R local at 0.5-1.0x; `w_coarse` +0.0041) | meets it | not needed for rank 1; would delay B |
| - | Dropped: frames-only calibrations (not allowed); fine-tuning old checkpoints on calibrated data (grey: the detector would also be trained on uncalibrated data); a larger frame pool (S6: the 10x pool gave nothing, within 0.001) | | | | | |

**Why B is worth running even though its central value (0.5434) is below 0.5440.**
- The best upload counts, and LUMPI has 4 uploads left. So what matters is the chance that **some** upload passes 0.5440, not the central value of each.
- A2/A3 and B are close to independent: A3 adds detection to `C0`'s frames, B adds realism to `C0`'s detections. A3 passes 0.5440 only at its high end (about 15-20%); B passes it at a transfer of about 0.9x or more with neutral detection (about 20-30%). Together, about 35%.
- The GPUs are otherwise idle after the 12-view wave (the `C2` builds are CPU and RAM).
- It is exactly the path the organizers named, so it carries no rule risk; the report describes it.

**Pre-registered for B (if adopted, before any B result exists):**
1. **Realism gate on CPU first:** the calibrated generator's 50 frames (same ids) on the held-out judge sets (proxies 4, 5, late-3, b-m5, b-m6 x seeds 1234, 99) must beat `C0`'s frames by at least +0.006 R mean, 9 of 10 wins. Points inside labelled boxes are left as generated (the box guard of `g1-v6pq`); if the guarded re-draw loses more than 0.0015 R against the unguarded one, the unguarded one is used. Else B stops.
2. **Detection gate:** `routed-c0n1` (the `C0` recipe on the retrained members) against `C0` on realval A/B: rule 14 at grouped P 0.8 decides only whether the detection change is reported as a gain; the upload decision uses the combined projection.
3. **Upload rule:** B is uploaded if its projection (detection projection + 0.70 x the held-out realism gain) is above the best compliant entry's expected score at that time. It is uploaded after A2 (so A2's server score is known), never instead of the last V2X or LUMPI slot needed by A3.
4. **No server number chooses a frame set or a knob** (docs/01 Section 9); B's frames are the same 50 ids as `C0`'s.

**Recommended order (times UTC):** A1 (V2X) and A2 (LUMPI) uploaded now; the disclosure sent; the 12-view wave and B's CPU work in parallel until about 22:00; B trains; V2X `C2` select about Nov 13 00:00-06:00, LUMPI `C2` select about 06:00-12:00; V2X `C2` upload Nov 13-14; LUMPI `C2` upload Nov 14; B's upload about Nov 14 12:00-18:00; last margin Nov 15 18:00.

### 15.18 Release 10.2 and every organizer ruling: what is resolved, what is open (2026-11-12, 20:00-21:30 UTC; for the entrant's review)

The entrant set the split on 2026-11-12: release 10.1 holds the uploads already made (LUMPI 1042287, 1047204, 1047231; V2X 1042294, 1046758) and becomes a full release; all later work is release 10.2. They asked that every organizer ruling on the feasibility of our final-phase systems be applied and resolved in 10.2. This section re-reads the whole email thread (the entrant's PDF copy, 2026-11-12; not in git, it holds contact details).

**The rulings, in the organizers' words where it matters.**

| Date | Ruling | What it requires of us |
|---|---|---|
| 2026-10-31 | the emailed declaration is received; "You could also include the declaration in your submission zip if not already" | every zip carries `declaration.txt` (checked on `c2rv6`: present) |
| 2026-11-07 (both tracks) | real labels, and object points cut out with real boxes, must not enter the training set | rule 1 (`clean_check.py`); 10.0 removed |
| 2026-11-09 | "We will rank KarmaRV only by submissions from LUMPI 1042287 and V2X 1042294 onward"; earlier final-phase uploads removed but "still count toward your submission limit"; describe the change in the report | the ranked window; the upload count |
| 2026-11-09 | every listed real-data use is allowed (validation and model selection, label statistics, realism calibration from unlabelled clouds "including choosing your 50 submitted frames", test-time post-processing); "Please list all of these in your report" | the report list |
| 2026-11-09 (a), (d) | "Each team's best submission counts"; "The leaderboard automatically shows each team's highest-scoring submission, so participants cannot choose which one is shown" | **the board shows LUMPI 1047231**, and we cannot change that ourselves |
| 2026-11-09 (b), (c) | the walker-distance histogram is allowed; twin completion (R1) is allowed if no real point is copied; describe it in the report | R1 members need `BDC_ALLOW_R1=1` and a report paragraph |
| 2026-11-12 | "a calibration may change the submitted frames only if it also changed the data your detector was trained on"; describe the calibration, its real fit frames and how the 50 frames were chosen | **rule 1b** below |

**Every final-phase upload and 10.2 candidate against them.**

| System | No real label (Nov 7) | Ranked window (Nov 9) | Frames rule (Nov 12) | Status |
|---|---|---|---|---|
| LUMPI 1038963, V2X 1038966 (10.0) | **no** | before it | (n/a) | removed by the organizers; count toward the limit |
| LUMPI 1042287 (`C0`) | yes | yes | **passes** (`g1-v6`, a training corpus of 11 of 16 shipped checkpoints) | the best qualifying LUMPI entry, 0.5408 |
| LUMPI 1047204 (`c1pq`), 1047231 (`c0pq`) | yes | yes | **fails**: `g1-v6pq` (the PandarQT near-field re-cast) is the training corpus of no shipped checkpoint | 1047231 (0.5413) is what the board shows |
| V2X 1042294 (`C0`), 1046758 (`c1av5`) | yes | yes | passes on the corpus (`g1-v6`, 4 of 6 checkpoints); **one open point**: packaging adds 31% (0,0,0) no-returns that the training frames do not store (the loader strips them in training and at inference) | 1046758 (0.8889) leads the board |
| 10.2 LUMPI `c2rv6` | yes | yes | passes (`g1-v6`, 11 of 20) | ready, about 0.5419 |
| 10.2 V2X `c2r` | yes | yes | passes on the corpus (5 of 11); the same no-return point | ready, about 0.8893 |
| 10.2 final `C2`, lever B | rule 1 in their gates | yes | rule 1b in code (below); B retrains every member, so its calibrated frames pass | not built |

**The point the email changes for 10.1.** The organizers' reply opens "Thank you for asking before uploading". That is true of the two calibrations we asked about (N1, `aw_mid`: never uploaded), but not of the PandarQT re-cast, which reached the frames of 1047204 and 1047231 on Nov 10 before we asked. Under ruling (d), the LUMPI board shows 1047231 automatically and we cannot choose another entry. Two things fix it, and they do not exclude each other:
1. **The disclosure** (Appendix C, revised below): we ask the organizers to leave 1047204 and 1047231 out, as they did with 10.0.
2. **A qualifying upload above 0.5413** replaces 1047231 on the board by itself. `c2rv6` projects 0.5419, only 0.0006 above it, which is within the Person route's transfer spread. A3 (`C2`) and B are the uploads with real margin.

10.1's release notes say this, and keep both uploads as the record of what was uploaded.

**Resolved in 10.2 (done, 2026-11-12).**
- **Rule 1b in code.** `clean_check.py` checks a routed model's realism frames against its shipped checkpoints. The frames' corpus must be a training corpus of a shipped checkpoint, and every real-data item (calibration) on its card must be in the training data of every shipped checkpoint. `package_submission.py` refuses to package frames that fail it (a reproduction of an earlier upload only warns). Test: `test_frames_rule_needs_frames_from_the_detectors_training_data`. Run on every final-phase system: LUMPI `routed-c0`, `routed-c2r` and V2X `routed-c0`, `routed-c1a`, `routed-c2r` pass; LUMPI `routed-c1` (the `c1pq` frames) fails; packaging `routed-c0` with `g1-v6pq` (the `c0pq` build) is refused. One stricter case is intended: frames from a calibrated corpus fail while any shipped checkpoint lacks that calibration (one re-cast member among 20 is not enough), so lever B must retrain every member.
- **The packages.** Both 10.2 packages pass. The withdrawn ones (LUMPI `c2r` with `g1-v6pq` frames; the held N1 and `aw_mid` packages) are out of git and never uploaded.
- **docs/01 Section 3.1** has the rule row (release 10.1).

**Open, and the next steps of the 10.2 plan** (nothing below is started; the entrant reviews and chooses):

| # | Step | Who | Resolves | Note |
|---|---|---|---|---|
| N1 | Send the revised disclosure (Appendix C): leave 1047204 and 1047231 out; **ask the V2X no-return question** (now recommended, no longer optional) | the entrant | the board entry (d); the last literal doubt on the V2X entries | short, with yes/no questions |
| N2 | Upload LUMPI `c2rv6` (A2), then V2X `c2r` (A1) | the entrant | a qualifying LUMPI entry that may top 1047231 | LUMPI 4 uploads left, V2X 5 |
| N3 | Final `C2` on both tracks, `g1-v6` frames, rule 1b in the gate | here, after the 12-view wave | more detection | the GBlobs `g1-v6pq` member may stay in a bag with `g1-v6` frames (rule 1b passes: its training data carries every item of `g1-v6`); dropping it is the stricter option |
| N4 | Lever B: the PandarQT re-cast and the N1 re-draw in the generator, all 14 `C0` checkpoints retrained (15.17) | here, on the entrant's go | the realism gap, the way the organizers allow it | report: the calibration, its fit frames (proxies 1-3), the frame choice |
| N5 | If the organizers rule the V2X no-returns frames-only: write them into the V2X corpora and retrain the V2X members, or ship frames without them | here, only on that ruling | V2X | the detector's input would not change (the loader strips them); the realism cost of dropping them is not measured yet |
| N6 | The report checklist (below) | here | every "describe it in your report" | |
| N7 | 10.1 GPU dry runs after the 12-view wave | here | 10.1 reproduction | |

**The report checklist** (every item the organizers asked for):
1. The change: label-placed walkers until 2026-11-02; ranked from 1042287 / 1042294; 10.0 removed.
2. Every real-data use (the list of the 2026-11-09 answer, with the frames each used).
3. The walker-distance histogram and the box-size statistics.
4. R1 twin completion, if a shipped member uses it.
5. The PandarQT re-cast in 1047204 and 1047231 (frames only), and that they are out under the 2026-11-12 rule.
6. The V2X (0,0,0) no-returns, and the organizers' answer to N1.
7. Any generator calibration that ships (lever B): the calibration, its real fit frames, and how the 50 frames were chosen.

## Appendix A. Email to the organizers (the entrant sends it)

### A.1 The short version to send (2026-11-10, at the entrant's request: "concise and pointed"; sent 2026-11-09 19:44 CST, answered 22:24 CST: Section 15.14)

Drop question (d) if the V2X board already shows 1042294 when you send it.

> **Subject:** KarmaRV (LUMPI, V2X): one disclosure and four short questions
>
> Dear organizers,
>
> After your November 7 clarification we checked our pipeline. We have one disclosure and four questions. A short answer to each would help us before the final phase closes on November 16.
>
> **Disclosure.** Until November 2, our synthetic training scenes placed each inserted pedestrian at the position, heading and size of a real label from a non-forbidden frame. Detectors trained on those scenes are in our development entries and in our first final-phase submissions (LUMPI 1038963, V2X 1038966). Our submissions from LUMPI 1042287 and V2X 1042294 (November 8) onward use no real label in training, only the label statistics listed below. **Please rank us only by these clean submissions.**
>
> We used none of the 100 forbidden frames on either track. We read these other uses of real data as allowed (on V2X they include some frames of the public val and test splits):
> - validation and model selection (LUMPI Measurements 4-6; V2X infrastructure frames);
> - real label statistics: box-size distributions (in the generator and in a test-time size calibration) and the histogram of question (b);
> - realism calibration from unlabelled real point clouds (beam pattern, background density, and choosing the 50 submitted synthetic frames);
> - test-time post-processing: augmentation, box fusion, score adjustments and low-score duplicate boxes.
>
> **Questions**
> - **(a)** In the final phase, does each team's best or last submission count?
> - **(b)** Our generator places walkers on the twin's map using a 10-bin histogram of real walker distance from the sensor. Is this allowed? If not, we will remove it.
> - **(c)** The digital twins lack some static structures of the real sites (poles, trees, sign posts, walls, vegetation). May we locate them in unlabelled real frames and add unlabelled synthetic geometry there in our training scenes? No real points would be copied. We have not used this and will not without your yes.
> - **(d)** The V2X leaderboard still shows our 1038966, not 1042294 (scored November 8), while the LUMPI board shows our newest. Which entry is ranked, and can we choose it?
>
> Best regards,
> KarmaRV

### A.2 The longer draft (superseded by A.1 on 2026-11-10; kept for the report, not to send)


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

## Appendix B. Question to the organizers on two realism-frame calibrations (revised 2026-11-11; the entrant sends it)

**Sent** by the entrant on 2026-11-11 (logged 16:27 UTC): the revised text below, **without** the optional 8 m sentence. So the LUMPI fallback is `g1-v6pq` (the frames of 1047231) unless the answer itself covers the 8 x 8 x 2.5 m re-draw. The answer is recorded here when the entrant shares it.

**Why we ask.** Neither calibration breaks a written rule: both fit only guard-allowed real frames ("hyperparameter selection or domain adaptation, provided no forbidden frame is touched"), and the 50 frames stay synthetic (FAQ, Oct 14). They are grey on three counts, so we ask before using them:
- **The disqualification check** for "synthetic frames that suspiciously resemble held-out real frames". The V2X warp moves points onto real surfaces (median distance to the nearest real fit point 0.283 m to 0.124 m). The LUMPI re-weighting leaves the share within 1 mm of a real point at 0.002%.
- **The FAQ's learned-synthesis line** ("real frames from the V2X-Real must not be used"): both fit tables to the track's own real frames.
- **Our own rules** (docs/01 Sections 3.1 and 9): "affine or quantile warping applied only to the 50 submitted frames: Avoid"; "density on 8 m cells" as the coarse limit; "submitted synthetic frames come from the same generator configuration as the training corpus; no metric-only warping". Both levers change only the 50 frames, so the report would have to state an exception.
- **Their 2026-11-10 approval** lists the 8 m density prior and the V2X beam table, not these.

**The revision** (the entrant chose it on 2026-11-11 over the first draft) adds the two facts the organizers need: only the 50 frames change, and the V2X points end close to real surfaces. It also names the fit frames and says no leaderboard number is used.

> Subject: KarmaRV: two realism-frame calibrations, allowed?
>
> Dear organizers,
>
> Before our last uploads, may we apply either of these calibrations to our 50 submitted synthetic frames? They change only the 50 frames; the detector and its training data stay as they are.
>
> Both are fitted only on unlabelled, non-forbidden real frames (LUMPI Measurement4 frames below 6400; V2X-Real frames at least 20 frames from any forbidden frame). No label, test or kit frame, and no leaderboard number is used; no real point is copied; the settings are fixed in advance on our own held-out real frames.
>
> 1. LUMPI: a finer version of our disclosed density prior (2 x 2 x 0.5 m cells instead of 8 x 8 x 2.5 m). Each frame is re-drawn from its own points in proportion to the real-to-synthetic share of its cell (still 50,000 points; repeated points get 2 cm jitter).
> 2. V2X: in each (azimuth, elevation) bin, the ranges of our points are mapped onto the real range quantiles (points move only along their own ray), and the share of points per bin is rebalanced with points from our other synthetic frames. The moved points end up close to real surfaces (median distance to the nearest real point 0.12 m instead of 0.28 m).
>
> We would describe both in the report. If only one is acceptable, please say which.
>
> Best regards,
> KarmaRV

**On the answer** (pre-registered in 15.16):
- **Both allowed:** LUMPI ships N1 `safe_frames`, V2X ships `aw_mid`.
- **Only one allowed:** that one ships; the other track keeps its fallback.
- **W alone allowed:** V2X ships `w_coarse`.
- **No, or no answer** by Nov 13 12:00 UTC (V2X) or Nov 14 12:00 UTC (LUMPI): V2X ships `g1-v6`. LUMPI ships `g1-v6pq` (the frames of 1047231).
- **Correction to the 15.16 fallback (2026-11-11, before any of these frames is scored).** The 8 m N1 variant is inside the approved granularity, but it too changes only the 50 frames. It has the same docs/01 Section 9 issue ("no metric-only warping"), so it ships only if the organizers' answer covers it. The optional last sentence below asks for exactly that.
- **Optional last sentence** (replaces "If only one is acceptable, please say which."): "If only one is acceptable, or item 1 only on the 8 x 8 x 2.5 m cells of our disclosed prior, please say which."
- **The held packages** (the rehearsal detections, frames swapped) are reproduction packages, git-ignored and with no registry row: `model-lumpi-track/routed-c2r/test/output/c2r_n1_pending/submission.zip` and `model-v2x-track/routed-c2r/test/output/c2r_aw_pending/submission.zip`. None is uploaded before a yes. On a yes, the chosen system is packaged for upload in the usual way (registry row, tracked copy).
- **Kit checks (2026-11-11):** both valid. LUMPI `c2r_n1_pending`: 24,654 boxes, 225 s, md5 `2008e3ad0c877f3e55c7b8dfac17756e`. V2X `c2r_aw_pending`: 41,252 boxes, 242 s, md5 `dbe29e0f09fd2515341c42080649f717`. The detections are byte-identical to the rehearsal zips, and the frames to the calibrated sets. The kit run scores realism against our legal proxy 4 (not the kit's reference), which was already one of the judge sets: LUMPI R 0.9421 to 0.9484 (EMD 1.147 to 1.011), V2X R 0.9415 to 0.9527 (EMD 1.114 to 0.938). This is a consistency check, not new evidence.

### B.4 The answer (2026-11-12, 08:33 CST = 14:33 UTC; the entrant's copy, not in git)

- **Frames-only calibrations are not allowed on either track:** the 50 frames must represent the synthetic data the detector was trained on, so that realism and detection describe the same data.
- **Both methods are allowed as part of the generator:** apply the calibration to the training data, retrain the detector on it, and submit 50 frames from that calibrated data. The report must describe the calibration, the real frames it was fitted on, and how the 50 frames were chosen.
- **So, by the pre-registered table above:** neither held package ships (`c2r_n1_pending`, `c2r_aw_pending`; both withdrawn). V2X ships `g1-v6`. LUMPI ships `g1-v6`, **not** `g1-v6pq`: the answer also covers the PandarQT re-cast, which reached the frames of 1047204 and 1047231 without reaching their detectors' training data (Section 15.17).
- The generator path the answer opens is lever B of Section 15.17.

## Appendix C. Disclosure to the organizers on the LUMPI frames (revised 2026-11-12, 21:30 UTC; the entrant sends it)

Revised after re-reading the thread (Section 15.18). The organizers' reply thanks us "for asking before uploading", and their ruling (d) says the board shows our highest score and we cannot choose it. So the email says plainly that the re-cast was uploaded before we asked, and the V2X question is now part of it.

> Subject: KarmaRV: two LUMPI uploads under your frame rule, and one V2X question
>
> Dear organizers,
>
> Thank you for the answer. Under it, two of our LUMPI uploads do not qualify, and we should have asked before making them. In 1047204 and 1047231 (November 10), the 50 frames carried a sensor-model fix that our detectors were not trained on: the PandarQT's near-field ground returns, re-cast from its beam table in the dataset metadata. Please leave both out of our ranking, as the board would otherwise show 1047231; our best qualifying LUMPI entry is 1042287. From now on our frames come only from the data our detectors were trained on.
>
> One V2X question. Our 50 frames store 31% of points as (0,0,0), the real sensor's no-return encoding (the rate measured on unlabelled, non-forbidden frames). Our training frames hold only the valid points, and our detector removes (0,0,0) points in training and at inference, so they do not change what it sees. Is this acceptable? If not, we will change it.
>
> Best regards,
> Rahul (KarmaRV)

- The first draft (same day) had the V2X paragraph as optional. It is now recommended: the 2026-11-12 rule read literally covers anything that changes the frames without changing the training data, and our V2X entries lead the board.
