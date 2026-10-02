# 2026-09-30 Review of the Sep-17 plan set (decision record)

> Scope: the Sep-17 plan set `reference/RESEARCH-OVERVIEW.md`, `reference/PLAN-V2X-Real.md`, `reference/PLAN-LUMPI.md`, `reference/SETUP-AND-STACK.md` and `reference/BDC26-OVERVIEW.html`. After this review they were consolidated into `docs/` and removed from the tree; read them with `git show 2a0bc24:reference/<file>`.
> Method: every claim was checked against the live challenge pages, the CodaBench API (rules, phases, datasets, leaderboards of the IEEE and ECCV instances), the four organizer papers, the organizers' public generation script (`m-shahbaz-kharal/HiFi-DT-Utils`), and the server itself.

---

## 1. Verdict

The Sep-17 set is a good **literature orientation**. It correctly identifies several real levers: the missing pedestrian class, the UrbanTwin recipe, sensor and pose matching, geometry-only training, OpenPCDet, TTA plus ensembles, and ablation discipline.

It is **not implementable as written** and **would lose points**. It misreads the rules on real-data use, sets an impossible LUMPI point-count target, spends effort on levers that cannot move AP, puts a multi-week CARLA twin build on the critical path, and was never checked against the server (storage, GPUs, CUDA). It also has no module boundaries, data contracts or acceptance tests, so it cannot be executed step by step.

| Dimension | Grade | Summary |
|---|---|---|
| Literature coverage | B+ | Broad and mostly accurate; some 2025-2026 entries need verification (Section 5) |
| Rule interpretation | D | Misses the explicit permission to use the real train split for hyperparameter selection and domain adaptation |
| Scoring model | C- | Right formula; wrong mechanics (pooled subsampling, file cap, AP thresholds); realism over-weighted |
| Competitive picture | D | "8 participants, few submissions" versus 31/33 participants and ECCV finals at 0.746 / 0.479 |
| Engineering feasibility | D | `/scratch` does not exist; `/` is 97% full; GPUs are shared; the CARLA twin needs an Unreal source build plus a RoadRunner licence |
| Implementability | D | No modules, interfaces, tests, class-map tables, beam tables or guard code |
| Schedule | C | Direction right (ship early), but no dated gates and wrong final-phase mechanics |

## 2. Critical errors (fix or lose points)

| # | Sep-17 claim | Fact | Impact | Fixed in |
|---|---|---|---|---|
| 1 | "Detector trains on synthetic only; **no real data even unlabeled**"; "You cannot validate on real" | The CodaBench Rules tab (binding per Terms item 1) allows "using the **train split** of the public real dataset for **hyperparameter selection or domain adaptation**, provided no forbidden frame is touched." | Throws away a real labeled validation set, real sensor calibration and real label conventions: the biggest process advantage available | `01` S3.1, `03` S1 |
| 2 | LUMPI: "match ~220k points/frame so EMD and MMD see the right mass" | Each submitted frame is capped at **1.5 MB (about 125k xyz points)**. Realism pools the 50 frames, masks to range and **uniformly subsamples 10k points**, so per-frame count is irrelevant. | The target is impossible; UT-LUMPI frames must be subsampled to be submitted at all | `01` S4.4 |
| 3 | "Per-class threshold tuning" as a key inference lever | KITTI-style interpolated AP **cannot decrease** when lower-scored detections are added; thresholds do not raise AP | Wasted effort; risk of cutting recall | `01` S4.4 |
| 4 | "Do not collapse frame diversity: hurts FPD covariance and MMD" | Metrics are computed once on the pooled 10k-point sets; per-frame diversity enters only through the pooled distribution | Wrong mental model for frame selection | `01` S4.4 |
| 5 | Realism (40%) treated as a co-equal battleground | Published endpoints: AP [0, 0.7], CD [2, 30], MMD [0, 0.5], EMD [0, 5], FPD [0, 50], so `combined = 0.857 * mAP + 0.4 * R`. Real-vs-real R is about 0.93-0.96; winners already reach 0.91-0.93 | Mis-allocated effort; detection is where ranks are decided | `01` S4, `02` S1 |
| 6 | LUMPI class handling treated generically ("8 classes, correct Van handling") | The mean is over **7** classes (Unknown has 0 test GT). Test GT: Person 512, Car 1258, Bicycle 82, Motorcycle 27, Bus 25, Truck 192, Van 79. The organizers' own histogram shows 0 Van in real Measurement4, yet the test set has 79 Vans, and a competitor found person-sized "Van" GT in his harness: **the LUMPI class-ID mapping must be verified from the raw labels.** Best Truck AP is 0.07 and best Van 0.08 | Plan did not target the classes where the points are | `TRACK1` S3 |
| 7 | Build CARLA twins (Cesium, Blender, RoadRunner, CARLA) in 2 weeks for 2 sites | Needs an Unreal/CARLA source build, a RoadRunner (MathWorks) licence, and mesh cleanup. The organizers' twins already exist in the UT frames. CARLA's `ray_cast` spaces beams **uniformly**, so it cannot reproduce HDL-64E / Pandar64 / PandarQT beam tables. | Weeks off the critical path for a result the UT data already provides | `03` S3 (engines G1/G2) |
| 8 | `make_lidar(... dropoff_general_rate=0.10 ...)` | The organizers used `dropoff_general_rate=0.68`, `noise_stddev=0.002`, datasheet rate x 2.26, 10 Hz, and **zero sensor tilt** (`carla.Rotation()`) | Arbitrary parameters; misses the tilt and beam-table gaps that are real improvement opportunities | `TRACK1`/`TRACK2` sensor sections |
| 9 | LUMPI z-range is a detector ablation ([-5,5] vs [-8,2]) | It is a **coordinate-frame** question. The frames are in the LUMPI Measurement4 local frame (`meta.json` frame minus (364, 85, 100)) with ground at about z = -2.1 m; the real sensors are tripod-mounted about 1.2-2.6 m above ground. UT-LUMPI shares the frame (flat ground at -2.152) | A wrong frame silently ruins realism and 3D IoU at once | M2 in `04` |
| 9c | "Ouster OS1-128 at the roadside unit"; LUMPI "exact models to confirm" | **V2X: the challenge unit is agent -1, an OS1-64** (64 x 1024, about +/-16.7 deg). UT-V2X emulates a wide-FOV sensor (about +25/-30 deg) with twice the points. **LUMPI: UT's five CARLA sensors are not at the real positions** | Both sensor models in the plan were wrong | `TRACK2` S2, `TRACK1` S2 |
| 9d | UT labels usable after class mapping | **UT-LUMPI actors are 0.78x real size** (a 0.78x box peaks at 0.47 3D IoU, below 0.5); UT labels list every vehicle on the whole map | LUMPI detection capped for anyone who trains on UT-LUMPI as-is | `TRACK1` S4 |
| 9e | Real datasets assumed free to use | **LUMPI is CC BY-NC 3.0; V2X-Real is academic-only ("All Rights Reserved")** | Needs legal sign-off for an industrial researcher | `07` S4 |
| 9b | (absent) | Real test and reference frames are **resampled to 50,000 points per frame**, and about **31% of V2X real points are (0,0,0) null returns** that the realism metric keeps | Training at native density overstates real-val mAP; synthetic frames without nulls lose realism | `01` S4.2 |
| 10 | "Competitive landscape: 8 participants, few or no submissions" | 31 (LUMPI) / 33 (V2X) participants, about 165 submissions each; ECCV finals on the **same scorer and the same test data**: V2X 0.7457, LUMPI 0.4793; the winners published their methods | Targets set too low; free intelligence unused | `01` S7, `02` S2 |
| 10b | V2X classes: "car/van/bus/box-truck/scooter/motorcycle/bicycle into vehicle vs truck vs pedestrian" (mapping left open) | Per the official V2X-Real super-class map: **truck includes TrashCan (42% of truck instances), Van and Bus**; **pedestrian includes cyclists, scooter riders and motorcyclists**. Pedestrian is 62% of the test GT, and the best AP is 0.19 | The biggest lever in the track was unidentified | `TRACK2` S3 |
| 11 | Final phase "5 total submissions", no daily cap | CodaBench final phase: **1 per day**, 5 total, closes **Nov 15 00:00 UTC = Sat Nov 14, 16:00 PST / 18:00 CST** | Cannot burst submissions at the end | `01` S2 |
| 12 | Storage under `/scratch/bdc26` (300-500 GB) | `/scratch` does not exist. `/` had 233 GB free (97% used) in the morning and 1.4 TB later the same day (other users); `/data` has 607 GB (96% used) | Downloads could fail or fill the shared root disk; free space must be checked, not assumed | `03` S6 |
| 13 | "8x A6000; give DDP all free GPUs" | Another user is running jobs on all 8 GPUs at 100% utilization (about 6 GB each) | Training time estimates are optimistic by an unknown factor | `02` S7, `05` |
| 14 | "OpenPCDet's built-in KITTI evaluator mirrors the leaderboard precisely" | KITTI eval applies difficulty filters (height/occlusion/truncation) and camera-frame conventions; the challenge applies **none** and scores classes absent from GT as excluded | Local AP would not match the server | M3 in `04` |
| 15 | UT labels used directly | UT labels **include empty boxes** outside LiDAR range ([TUT] Fig. 6); synthetic boxes are **about 17% smaller** in volume than human labels (LUMPI 10.13 vs 12.17 m^3) | Training on invisible targets; systematic IoU loss (consistent with near-zero mAP@0.7 across the field) | M7 in `04` |
| 16 | Realism proxy code in `SETUP-AND-STACK.md` S7 | Biased MMD with a full-set median bandwidth; the official scorer uses the **unbiased** estimator and a median over a **1,000-point** joint subsample; EMD `numItermax` behaviour unverified | Proxy would not match the server | M3 in `04` |

## 3. Important omissions

- **No real validation protocol:** no buffer around forbidden frames, no scorer-exact local AP, no bootstrap confidence intervals on a 50-frame test set.
- **No coordinate-frame work** for aligning UT, real train-split and test frames.
- **No concrete pedestrian method.** "Spawn CARLA walkers, upgrade with MetaHuman + AMASS" is not a plan: MetaHuman requires Unreal, AMASS/SMPL licences are non-commercial (a problem for an industrial lab), and the organizers dropped CARLA walkers as unrealistic.
- **No class-mapping tables** (V2X-Real's raw categories to vehicle/pedestrian/truck; UT's six classes to either track).
- **No beam tables** for the Ouster unit (OS1-64 or OS1-128, unverified), Pandar64, HDL-64E, PandarQT or VLP-16.
- **No ForbiddenGuard implementation**, no experiment registry, no submission validator.
- **No asset-licence review** for an industrial participant.
- **No use of the leaderboard as intelligence** (normalization endpoints, field strength, what the stock frames score).

## 4. What is right and carried forward

- The pedestrian/VRU gap is the biggest detection lever (now quantified in `02` S2).
- Sensor spec and mounting-pose matching improves both detection and realism (now done by measurement from real frames, M5/M6).
- OpenPCDet as the framework; geometry-only inputs as the default; CenterPoint/VoxelNeXt-class detectors.
- TTA plus multi-model ensembling with 3D weighted box fusion.
- Ablation discipline and writing for the paper track from day 1.
- "Get a legal submission in week 1, then improve."

## 5. Citation audit

All 40 arXiv IDs resolve to the claimed papers; none are fabricated. There are seven corrections (one wrong venue, one mislabeled metric, one missing ID that is a segmentation paper, one misattributed gain, one segmentation-only method listed for detection, one unsupported claim, one venue mix-up), plus the rules misreading and the V2X sensor question (the challenge unit may be the OS1-64, not the OS1-128). Details: `07-LITERATURE.md` Section 1.

## 6. What replaced the Sep-17 set

| Now | Replaces |
|---|---|
| `docs/01-CHALLENGE-FACTS.md` | `RESEARCH-OVERVIEW.md` S1-3, S11; `SETUP-AND-STACK.md` S1 |
| `docs/02-STRATEGY.md` | `RESEARCH-OVERVIEW.md` S0, S7; the "three recommendations" in both PLAN files |
| `docs/03-ARCHITECTURE.md` (incl. the repository layout and code map) | `RESEARCH-OVERVIEW.md` S8; `SETUP-AND-STACK.md` S5-6 |
| `docs/04-IMPLEMENTATION-GUIDE.md` | the Phase 0-5 sections of both PLAN files; `SETUP-AND-STACK.md` S3-4, S6.3, S7-9 |
| `docs/TRACK1-lumpi-track.md`, `docs/TRACK2-v2x-track.md` (incl. models and experiment tables) | track-specific parts of both PLAN files, including their ablation grids |
| `docs/05-SCHEDULE-AND-RUNBOOK.md` | both PLAN calendars and `RESEARCH-OVERVIEW.md` S3.1 |
| `docs/06-LEARNING-PATH.md` | `RESEARCH-OVERVIEW.md` S5 (primer) |
| `docs/07-LITERATURE.md` | `RESEARCH-OVERVIEW.md` S6, S9, S12 (verified) |
| `DATASET.md`, `data-<track>/`, `common/env/` | `SETUP-AND-STACK.md` S3, S5, S6.3 (environment and data layout, now as working scripts) |
| (dropped) | `BDC26-OVERVIEW.html` (a visual summary of the old plan with outdated facts) |

**Layout update (2026-10-02).** On the entrant's request, `DATASET.md` and the two TRACK documents were split into per-track guides inside the track folders: `data-<track>/README.md` (data, generator, dataset versions) and `model-<track>/README.md` (approaches, selected model, lifecycle, results), plus a README in every model folder; the root `README.md` became the developer guide. The rows above that name `DATASET.md` or `docs/TRACK*.md` describe the 2026-09-30 layout.
