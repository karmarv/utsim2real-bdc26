# 04. Implementation guide (modules M0-M12)

> Each module is a self-contained work package: **goal, where it lives, steps, acceptance tests, pitfalls**. Build in order; M0-M4 produce the first legal submission (Gate A). Track-specific values live in `data-<track>/track.yaml` and are explained in the track guides `data-<track>/README.md` and `model-<track>/README.md`; data steps are catalogued in the track data guides (`data-<track>/README.md`); architecture and the code map with build status are in `03-ARCHITECTURE.md` Section 6.
> Conventions: shared code in `common/bdc26/` (tests in `common/tests/`), shared CLIs in `common/tools/`, track data scripts in `data-<track>/`, one folder per model in `model-<track>/<model>/`, large data under `$BDC_DATA/<track>/`. Run `source common/env/bdc26.env` in every shell.

---

## Module map

| ID | Module | Needs | Unlocks | Days | Gate | Status (2026-09-30) |
|---|---|---|---|---|---|---|
| M0 | Environment, storage, GPU plan | - | everything | 0.5 | | Done (GPU reservation still to arrange) |
| M1 | Data ingestion + ForbiddenGuard | M0 | M2-M5 | 1 | | Done; kit and real data are external steps |
| M2 | Frame and density conventions | M1 | M3-M9 | 0.5-1 | | Partial |
| M3 | Scorers, validator, packager, registry | M1 | every submission | 1 | A | Done; kit parity pending |
| M4 | Baseline detector + first submissions | M2, M3 | leaderboard loop | 1-2 | A | Configured and smoke-tested |
| M5 | Measurement: real val, label stats, sensor calibration, realism proxy | M1, M2 | M6-M12 | 2-3 | B | Partial (real-val builders written) |
| M6 | Sensor model + raycaster | M5 | M8, M9 | 2 | | Prototype |
| M7 | Actors, placement sampler, label conventions | M5 | M8, M9 | 2-3 | C | To build |
| M8 | Engine G1: UT+ insertion | M6, M7 | M10 | 2 | C | To build |
| M9 | Engine G2: Twin-Raycast | M6, M7 | M10, M12 | 3 | D | To build |
| M10 | Detector v2 (data mix, DG aug, architectures) | M4, M8, M9 | M11 | 3-5 (GPU) | D, E | To build |
| M11 | Inference stack (post-processing, TTA, ensemble) | M10 | final | 2 | E | Partial |
| M12 | Frame selection, final packaging, report | M3, M9, M11 | final | ongoing | F | Partial |

---

## M0. Environment, storage, GPU plan

**Goal.** Reproducible environments, a data root with enough space, and an agreed share of the GPUs.
**Where.** `common/env/bdc26.env`, `common/env/setup_bdc_train.sh`, `common/env/setup_bdc_sim.sh`, `common/pyproject.toml`.

**Steps.**
1. **Data root.** `common/env/bdc26.env` sets `BDC_DATA=$BDC_REPO/../bdc26-data` (the workspace drive, `/`, 1.3 TB free on Sep 30) and `PCDET_ROOT=$BDC_DATA/third_party/OpenPCDet`. `/data` (607 GB, 96% full) is only for archives. Free space on `/` is shared and has swung by more than 1 TB in a day: check `df -h /` before large jobs.
2. **Training env** `bash common/env/setup_bdc_train.sh` (idempotent). Recipe, verified on this server: Python 3.10, `setuptools<70` (torch 2.1's extension builder imports `pkg_resources`), torch 2.1.2 (cu121 wheel), spconv-cu121 2.3.8, numpy 1.23.5, OpenPCDet at commit 233f849 with the optional-Argo2 import patch, built with `CUDA_HOME=/usr/local/cuda-12.8` and `TORCH_CUDA_ARCH_LIST=8.6`, then `pip install -e common`.
   - numpy >= 1.24 breaks OpenPCDet (`np.int`, `np.float`, `np.bool`); `/usr/local/cuda-11.8` must not be used with the cu121 torch.
   - Two OpenPCDet bugs are patched from our side without editing OpenPCDet: `custom_dataset.py` imports `Path` only under `__main__` (patched in `bdc26/detect/pcdet_dataset.py`), and the GT sampler crashes on classes with no database entry (handled by `common/tools/pcdet_build_infos.py`).
3. **Simulation env** `bash common/env/setup_bdc_sim.sh` (Open3D 0.19, POT, trimesh) when M6 starts.
4. **Optional `bdc-lion` env** for LION/DSVT/SAFDNet/HEDNet (`happinesslz/LION`): torch 2.1.0 cu118 + spconv-cu118 + `CUDA_HOME=/usr/local/cuda-11.8`.
5. **GPU plan.** Another user runs jobs on all eight GPUs (about 4-6 GB each, often 100% utilization); about 42 GB per GPU stays free, so co-location works but is slower. Ask for a reservation. Placement: V2X on GPUs 4-7 (NUMA 1), LUMPI on 0-3 (NUMA 0), generation on CPU.

**Acceptance (met on 2026-09-30).** `python -c "import torch, spconv, pcdet, bdc26"` reports `2.1.2+cu121`, 8 GPUs; `pytest -q common/tests` passes; a one-epoch smoke training runs on each track (`05` Section 1, D1).

---

## M1. Data ingestion and ForbiddenGuard

**Goal.** Every source on disk, readable through one API, with forbidden and near-forbidden real frames impossible to load by accident.
**Where.** `common/bdc26/config.py` (track configs, data root), `common/bdc26/guard.py`, `common/bdc26/io/{fetch,ut,lumpi,v2x,kit}.py`; `data-<track>/{track.yaml, fetch_ut.py, ingest_kit.py, fetch_real.py, resolve_test_ids.py}`. The full order of steps is in the track data guides (`data-<track>/README.md`).

**Steps.**
1. **UT datasets** (done): `python data-<track>/fetch_ut.py` downloads the Dataverse split zips with 24 parallel range requests (about 65 MB/s; Dataverse gives about 1.5 MB/s per connection), checks MD5s, extracts `pcd`, `lbl`, `sem_seg`, `ins_seg`, and deletes the parts.
2. **Starting kits**: download from each CodaBench Files tab, then `python data-<track>/ingest_kit.py <zip>`. It writes `kit/kit_report.json` with format-level statistics of the test frames (points per frame, in-range count, null fraction, z percentiles). Then read `local_eval.py`, `scoring_program/metrics.py` and `detection_eval.py` end to end and record in `01-CHALLENGE-FACTS.md` Section 4: the subsampling RNG call, the EMD `numItermax`, range inclusivity, GT filtering, matching and tie rules.
3. **Real data** (after licence clearance; both scripts require `--accept-licence`):
   - LUMPI: `fetch_real.py --meta --labels` (labels are guard-filtered while streaming, so blocked rows never reach disk), then `--lidar MeasurementN --range a:b:s`.
   - V2X: `fetch_real.py --points` (agent -1 point clouds only), `resolve_test_ids.py`, then `fetch_real.py --labels` (labels only for guard-allowed frames).
4. **Resolve the challenge IDs.** LUMPI: `resolve_test_ids.py` confirms by exact point matching that test IDs are Measurement4 frame indices. V2X: `resolve_test_ids.py` maps each scenario index to its V2X-Real folder by exact point matching of the 50 test frames against raw frames, fills indices that only occur among the reference IDs from a sorted-folder ordering when that ordering explains at least five resolved pairs, and otherwise maps them to `"*"` (block that frame number in every folder).
5. **Guard behaviour** (`bdc26.guard.ForbiddenGuard`): keys are `(group, frame)` with group = LUMPI measurement or V2X scenario folder; LUMPI blocks `forbidden_frames.txt` plus Measurement4 frames 6400-8199; V2X blocks each forbidden frame +/-20 frames in its folder (or in all folders for `"*"`) and refuses everything until `kit/id_mapping.json` exists. Every allowed access is appended to `real/access_log.csv` with its purpose.

**Acceptance.** `pytest -q common/tests` (guard windows, wildcard indices, guarded label parsing, readers); the fake-data integration test of `resolve_test_ids.py` + `prepare_realval.py` passed on 2026-09-30 (index resolved by exact match, ordering inference, blocked frames excluded, nulls kept at about 29%).

**Pitfalls.** Never download reference-data bundles through the CodaBench API. Never use `kit/reference_data_local/realism_reference/` for anything but a smoke test of the scorer.

---

## M2. Frame and density conventions

**Goal.** Make every source (UT, real, generated) look like the challenge's real test frames: same frame, same density protocol, same null convention.
**Where.** `common/bdc26/frames.py` (`mask_to_range`, `resample`, `strip_nulls`, `frame_stats`), `common/bdc26/boxes.py`; checks via `kit/kit_report.json`.

**Facts to build on.** Real test and reference frames are resampled to exactly 50,000 points (the server counts 2,500,000 masked reference points: mask to the range first, then draw 50,000, with replacement when fewer remain). V2X frames carry about 31% (0,0,0) nulls, so only about 35k points per frame are real returns. LUMPI frames are in the Measurement4 local frame (`meta.json` M4 frame minus (364, 85, 100)), ground near z = -2.1 m; UT-LUMPI shares that frame (ground flat at -2.152). V2X frames are agent -1's (OS1-64) sensor frame; UT-V2X aligns with it to about 0.3 m.

**Steps.**
1. After `ingest_kit.py`, compare `kit_report.json` with the same statistics of canonical UT and real frames (`frame_stats`): N per frame, null fraction, z percentiles, extents. Record the result in `docs/decisions/<date>-frames.md`. Do not fit anything to the test frames.
2. Density: LUMPI training frames are resampled to 50,000 points in range (`prepare_ut.py --n-points`); V2X training frames to 35,000 valid points (`track.yaml` `resample.n_valid_points`; re-measure on legal real frames in M5.3). Real validation frames follow the organizers' protocol exactly (50k with nulls).
3. UT vs real static structure (after real data): overlay 1 m BEV occupancy of 200 frames each and compare median ground z in 10 m tiles; fix residual offsets with a rigid transform fitted on static structure.
4. Label conventions: heading vs point PCA, z vs in-box z-range, extents, on legal real boxes vs UT boxes per class.

**Acceptance.** Ground z per tile agrees within 5 cm; the null fraction of canonical V2X frames matches the kit report within 2 points; UT heading errors have median below 5 degrees.

**Pitfalls.** Training at native density overstates real-val mAP (an ECCV team measured 0.146 at native vs 0.132 at 50k). Nulls are removed inside the detector's data pipeline (`BDCDataset.get_lidar`) but kept in realism frames.

---

## M3. Scorers, validator, packager, registry

**Goal.** Local scores that equal the server's, and zips that cannot fail validation.
**Where.** `common/bdc26/evalap.py` (KITTI-style matching and thresholds, R40/R11, 3D and BEV, IoU 0.5/0.7, classes without GT excluded), `common/bdc26/realism.py` (published protocol and endpoints; EMD both at POT's default cap and converged), `common/bdc26/submit.py` (validator, packager), `common/bdc26/registry.py` (`model-<track>/registry.csv`); CLIs `common/tools/{eval_predictions,score_realism,package_submission}.py`.

**Steps.**
1. After `ingest_kit.py`: run the kit's `local_eval.py` and our evaluators on the same toy submission; they must agree to 1e-6 (AP) and exactly (realism, once the RNG call is copied). Fix `evalap.py`/`realism.py`, not the kit.
2. EMD: optimize against `EMD_exact`; report the value that mirrors the server.
3. Validator checks (run by the packager): 50 files, each <= 1,500,000 bytes and a multiple of 12 (N x 3 only), no NaN/Inf, in-range and null fractions, every test ID present, valid boxes and classes, declaration text verbatim.

**Acceptance (Gate A).** The first submission's server numbers equal the local numbers to 1e-4. `pytest` already covers IoU values, perfect-prediction AP = 1, class exclusion, the "low-score boxes never lower AP" property, NMS, the validator's N x 4 rejection, and the published normalization reproducing the ECCV winner's score.

---

## M4. Baseline detector and first submissions

**Goal.** A legal, sensible submission on both tracks, and a working OpenPCDet data path.
**Where.** Data: `data-<track>/prepare_ut.py` -> `$BDC_DATA/<track>/pcdet/ut-v1/`. Model: `model-<track>/pointpillars-ut/` (`model.yaml`, `train/pcdet_{dataset,model}.yaml`, `train/train.sh`, `validation/evaluate.sh`, `test/{postprocess.yaml,predict.sh}`, `submissions/`). Glue: `common/bdc26/detect/pcdet_dataset.py` (`BDCDataset`), `common/bdc26/detect/postprocess.py`, `common/tools/{pcdet_build_infos,pcdet_train,pcdet_predict}.py`.

**Steps.**
1. `python data-<track>/prepare_ut.py --name ut-v1` (both tracks: classes mapped via `track.yaml`, boxes cropped to the range and filtered to >= 1 point, 50k (LUMPI) or 35k valid (V2X) points, frames 0-8999 train / 9000-9999 val; LUMPI actors rescaled by 1/0.78).
2. `CUDA_VISIBLE_DEVICES=... bash model-<track>/pointpillars-ut/train/train.sh <ngpus> <tag>`: builds OpenPCDet infos and the GT database on first use (failing early if a sampled class is empty), registers `BDCDataset`, and writes everything to `train/output/pcdet_model/<tag>/`. PointPillars, 0.15625 m pillars (512 x 512 over 80 m), xyz only, anchors from UT statistics and KITTI defaults, 40 epochs, adam_onecycle LR 0.003.
3. OpenPCDet's own NMS is class-agnostic when `MULTI_CLASSES_NMS` is off (and that flag is broken for single-head models), so the configs keep near-raw outputs (score 0.01, NMS 0.9) and `test/postprocess.yaml` applies per-class NMS (pedestrian/Person about 0.6-0.7), re-centering and hedged duplicates.
4. `bash validation/evaluate.sh <ckpt> pcdet/ut-v1 val` for synthetic validation now; `pcdet/realval-v1` (the default) once M5 exists. Results go to `validation/results/*.json` and a registry row.
5. `bash test/predict.sh <ckpt>` -> `test/output/predictions.json`; `python common/tools/package_submission.py model-<track>/pointpillars-ut --tag <tag> --pred ... --synthetic pcdet/ut-v1 --team <team>` -> `submissions/<date>_<tag>/`. Upload by hand, then `--record <codabench id> <leaderboard.json>`.

**Acceptance.** One-epoch smoke runs passed on 2026-09-30 for both tracks (infos, GT database, training, post-training evaluation with `n/a` for classes without GT, prediction, scoring, registry). Next: full `ut-v1` runs and the first submissions; expected ballpark V2X combined about 0.6, LUMPI about 0.4.

---

## M5. Measurement: real validation set, label statistics, sensor calibration, realism proxy

**Goal.** Turn the legal real train split into the instruments every later decision uses.

**Where.** `data-<track>/prepare_realval.py` (real val A/B, realism proxy sets, LUMPI `class_report.json`); to build: `common/bdc26/measure/` (label statistics, beam tables, pose fit, return statistics, floor).

### M5.1 Real validation set
- **V2X:** all non-forbidden IC scenarios, frames with stride 5, excluding +/-20 frames around forbidden IDs (the guard does this). Target 1,000-2,000 frames.
- **LUMPI:** Measurement4 frames below 006400 (realval-A) and Measurements 5-6 (realval-B), stride 5-10; **not** Measurements 0-3 (three sensors only). Target 1,000-2,000 frames. **Verify the class-ID mapping** (hypothesis: LUMPI id 6 "unknown" is the challenge's "Van"; `data-lumpi-track/README.md`).
- `prepare_realval.py` canonicalizes, resamples to 50k (V2X nulls kept), maps labels, and writes `pcdet/realval-v1/` with `ImageSets/val.txt` = realval-A (decisions) and `ImageSets/valB.txt` = realval-B (confirmation, touched at most once per week). V2X splits A/B by scenario; LUMPI uses Measurement4 for A and Measurements 5-6 for B.
- **Sanity only:** compare per-class count proportions with the public test GT counts in `01` Section 7.2 (aggregate numbers shown on every detailed-results page). A large mismatch means a wrong class map.

### M5.2 Label statistics (the generator's targets)
Per class: counts per frame; BEV position heatmap (1 m cells); heading field (per cell circular mean and spread); size distribution `(dx, dy, dz)` with mode detection (Gaussian mixture, 1-3 components); box bottom height relative to local ground; points-per-box vs range (the annotation policy: minimum points for a labeled box); box tightness (box extent minus in-box point extent). Output `stats_<track>.json` plus plots.

### M5.3 Sensor calibration (from raw, un-resampled real frames)
- Sensor origin and pose: V2X frames are in the sensor frame (nulls sit at the origin); fit height and tilt from the ground plane (RANSAC plane on points within 25 m). LUMPI: per-sensor extrinsics from the dataset metadata, then refine each sensor's pose by matching its ground rings (the organizers only eyeballed this).
- Beam table per sensor: histogram the elevation angle of points in the sensor frame at 0.005-0.01 degree resolution; peaks are the beams. Initialize from the scan patterns in PCSim (Apache-2.0: Pandar64, HDL-64, PandarQT, VLP-16, OS1-64) and the datasheets (data guides, Section 4), then refine to the real peaks.
- **V2X: decide OS1-64 versus OS1-128 from the data** (64 vs 128 elevation peaks; about +/-16.6 vs +/-22.5 degrees). The ECCV winner reports that the challenge unit is the OS1-64.
- Azimuth resolution and per-beam azimuth offsets from point azimuth spacing per beam.
- Return statistics: per beam x range bin x incidence bin, the fraction of rays with a return (needs the range-image structure: the V2X agent -1 bins are organized 64 x 1024, row 0 = top beam; for LUMPI use the PLY `ray` and `azimuth` fields per sensor). V2X: the null fraction by beam and azimuth.
- Range noise: residuals of points on large planar patches (road, walls).
- Output: `sensors_<track>.yaml` (the `SensorModel` contract in `03` Section 7).

### M5.4 Realism proxy and floor
- `prepare_realval.py` also writes `pcdet/realism-proxy-{1..5}/`: disjoint legal sets of 50 frames (canonical, 50k, nulls kept); score with `common/tools/score_realism.py --ref pcdet/realism-proxy-1 --ref ...`.
- **Floor:** score proxy set i against proxy set j. This is the best achievable realism; a competitor measured about 0.96 (V2X) and 0.93-0.95 (LUMPI).
- Score UT frames, then every generated corpus, against a proxy set; report the variance across proxy sets.

**Acceptance (Gate B).** Real val built and guarded; stats and sensor YAMLs produced; the floor measured; the M4 baseline's real-val per-class AP ordering agrees with its leaderboard per-class AP ordering.

---

## M6. Sensor model and raycaster

**Goal.** Render any scene exactly as the real sensor(s) would see it.

**Where.** `common/bdc26/render/lidar_sim.py` (prototype); to build: `common/bdc26/render/sensor_model.py` (SensorModel, RayDropModel from `sensors_<track>.yaml`).

**Seed.** `common/bdc26/render/lidar_sim.py` (Open3D Embree; per-beam elevations and azimuth offsets, pose, range limits, noise, per-ray drop, instance and triangle IDs). Measured: 262k rays raw in 2.2 ms; a full post-processed 262k-ray scan in 39 ms; the five-sensor LUMPI rig (1.1M rays) in 176 ms.

**Steps.**
1. `SensorModel.from_yaml(sensors_<track>.yaml)`; generate ray directions once per sensor.
2. **Ray-drop model** `RayDropModel.p_return(beam, range, cos_inc, surface_class)`: start with a lookup table fitted in M5.3 (binned return probability); later (optional, gated) a small MLP.
3. **Output formatting per sensor family:**
   - Ouster OS1-64 (V2X): emit the full 64 x 1024 grid; rays without a return become **(0,0,0)** points, which matches the real data and its null fraction.
   - Velodyne/Hesai (LUMPI): drop rays without a return.
4. **Multi-sensor merge** (LUMPI): render each of the five sensors from its fitted pose, transform to the Measurement4 local frame, concatenate, then mask and resample to 50k exactly as the organizers do for real frames.
5. Vectorize the numpy post-processing (it dominates runtime) and run frames in parallel processes (64-128 workers).

**Acceptance.**
- Raycasting the static scene (M9.1) with the fitted V2X model reproduces the real ground-ring radii to within 1% at 5-30 m and the real elevation histogram peak positions to within 0.02 degrees.
- The null fraction of rendered V2X frames matches real within 2 points.
- Throughput of at least 20 frames/s for V2X on 64 cores.

---

## M7. Actors, placement sampler, label conventions

**Goal.** Objects of every scored class that look right to the sensor and are labeled like the real annotators label them.

**Where (to build).** `common/bdc26/actors/` (procedural humans, riders, containers, vehicles; placement sampler; label conventions).

**Asset policy (industrial licence review; details in `07-LITERATURE.md` Sections 3.3 and 4):**

| Use | OK | Not OK |
|---|---|---|
| Humans | Procedural articulated humans; MakeHuman/MPFB2 core assets (CC0); CMU mocap BVH (free incl. commercial); 100STYLE (CC-BY) | SMPL/SMPL-X/AMASS/BEDLAM (non-commercial), Mixamo (AI/ML use banned), RenderPeople |
| Vehicles, bicycles, props | Procedural meshes; Kenney/Quaternius/Poly Haven (CC0); Objaverse/Sketchfab filtered to CC0/CC-BY (keep a CREDITS file); CARLA assets (CC-BY, needs the UE editor to export; strip brand names) | ShapeNet/ModelNet/3D-FUTURE, TurboSquid/Unity/CGTrader "no AI" |

**Steps.**
1. **Procedural pedestrian generator (day 1 of M7):** an articulated body of capsules and ellipsoids (head, neck, torso, pelvis, upper/lower arms, upper/lower legs, feet) with a parametric gait cycle (phase, stride length, arm swing), plus variants for standing, backpacks and strollers. Sample height, shoulder width and depth from real statistics (M5.2, legal frames only). For orientation only: an ECCV team reports V2X walker medians of about 0.74 x 0.72 x 1.73 m; a LUMPI competitor's anchors (provenance unverified, possibly including Measurement4's forbidden tail) put Person near 0.8 x 0.7 x 1.9 m. Do not set parameters from either. Upgrade to Anny (Apache-2.0 parametric body) or MPFB2 meshes posed with CMU BVH only if Gate C is marginal. Evidence that conventions matter more than meshes: PCGen raised pedestrian AP@0.5 from 6.56 to 54.31 just by loosening boxes to the annotator convention.
2. **Riders:** procedural bicycle (two tori, frame tubes, handlebar), e-scooter (deck, stem), motorcycle (body block, wheels) with a seated or standing human. **One box around rider plus vehicle** is the expected convention (verify per track in M5.2). V2X: riders are labeled **pedestrian**; LUMPI: Bicycle and Motorcycle are separate classes.
3. **V2X TrashCan** (counted as truck; about 42% of truck instances): format exploration suggests these are **large static containers several metres long** (roll-off dumpsters or parked refuse vehicles), not wheeled bins. Confirm the size modes and locations in M5.2, then model them as box-like containers with lids and ribs.
4. **Vehicles for G2:** UT already contains vehicles for G1. For G2, start from procedural vehicles (a parametric car/van/truck/bus body: box plus hood, cabin and wheel arches) sized by the real size modes, and add CC0/CC-BY meshes if time permits. LUMPI Truck is multi-modal (competitors report both a box-truck mode and a larger articulated mode): sample from the mixture fitted in M5.2 on legal frames.
5. **Placement sampler:** per class, sample positions from the real BEV heatmap, headings from the local heading field, counts per frame from the real distribution; reject overlaps; snap to local ground.
6. **Label conventions:** boxes follow real statistics, not mesh bounds: `dims = real-convention(dims_mesh)` (fit a per-class affine map from mesh extent to real box extent, or sample the object to fit a sampled real box); z from ground plus half height; heading along motion. Drop labels with fewer than the real policy's minimum points after rendering.

**Acceptance (part of Gate C).** Synthetic label statistics match the real ones: per-class size means within 3%, KS statistic below 0.1 on each dimension, heatmap correlation above 0.8. Visual check of 20 rendered pedestrians and riders at 10, 20 and 35 m next to real examples.

---

## M8. Engine G1: UT+ (ray-consistent insertion)

**Goal.** Add the missing and weak classes to UT frames with correct occlusion, fast.
**Where (to build).** `common/bdc26/render/insert.py`; entry points `data-<track>/generate_g1.py` -> `$BDC_DATA/<track>/gen/g1-v<k>/` -> `pcdet/g1-v<k>/`.

**Steps.**
1. **V2X (one sensor):** convert the UT frame to a range image on the UT sensor's grid (the UT-V2X sensor is a CARLA uniform-beam model; recover its channel angles from the point elevations). Raycast the inserted actors with the **same** grid; per pixel, the nearer return wins (z-buffer); back-project. Points hidden behind an inserted actor disappear, and the actor gets exactly the beam pattern the sensor would produce.
2. **LUMPI (five sensors):** attribute every UT-LUMPI point to its source sensor. UT-LUMPI was rendered by five CARLA sensors with uniform channel tables, so each point's elevation seen from its true sensor lands exactly on one of that sensor's channels. The public script's positions are only a template (they do not match the real rig, and may not match the released data), so **fit** each UT sensor origin by maximizing that quantization. Then run the V2X procedure per sensor, merge, and resample to 50k. Use the same machinery to **re-render UT actors at the correct scale** (`data-lumpi-track/README.md`).
3. **Scenario rules:** pedestrians on sidewalks and crosswalks (from real heatmaps), riders on roads and bike lanes, TrashCan containers where the real ones sit (M5.2 heatmap); avoid collisions with UT vehicles (check against UT boxes).
4. **Labels:** add the inserted boxes to the UT labels (class-mapped) and recompute point counts for every box (occlusion may empty some UT boxes).
5. Produce `gen/g1-v<k>/` corpora of 10k frames each (and a class-balanced variant with more VRUs per frame), exported as `pcdet/g1-v<k>/` and recorded in the track's data README (`data-<track>/README.md` Section 9) Section 4.

**Acceptance (Gate C).** No inserted object has points behind it from the same sensor; a model trained on UT + G1 reaches the Gate C VRU thresholds on real val.

---

## M9. Engine G2: Twin-Raycast

**Goal.** Full control of scene, sensor and objects for the corpus and for realism frames.
**Where (to build).** `common/bdc26/scene/` (static-scene accumulation and meshing); entry points `data-<track>/generate_g2.py` -> `gen/g2-v<k>/` -> `pcdet/g2-v<k>/`.

**Steps.**
1. **Static scene (M9.1):**
   - Default (rule-safe): accumulate the static points of 1,000-2,000 UT frames (points outside all boxes; use UT `sem_seg` labels if present) per sensor in the track frame; build a surface with Open3D (voxel-downsample at 5 cm, estimate normals, Poisson or ball-pivoting reconstruction, trim low-density vertices); keep the road surface as a separate high-resolution mesh.
   - Gated option (Q2): the same procedure on legal real frames (temporal median occupancy to remove movers), which removes the twin-vs-real geometry gap.
2. **Scenario generation (M9.2):** vehicles, VRUs, trash cans and other objects from M7 placed by the sampler; per-frame class counts from real statistics, with an oversampling knob for rare classes.
3. **Rendering (M9.3):** M6 sensor models (fitted poses and beam tables, ray-drop, null format); LUMPI multi-sensor merge; resample to 50k; labels with the real conventions and the visibility filter.
4. **Throughput:** 64-128 worker processes; store generation recipes (seed, actor list, sensor version) so that corpora can be regenerated instead of archived.

**Acceptance (Gate D).** G2 frames score better than UT and G1 frames on the realism proxy, or a model trained with G2 in the mix beats UT + G1 on real-val mAP.

---

## M10. Detector v2

**Goal.** The best detector per track, selected on real val.
**Where.** One new folder per model: `python common/tools/new_model.py <track> <name> --from pointpillars-ut`, then edit `model.yaml` (data versions, status) and `train/pcdet_model.yaml`. Name models `<architecture>-<data>` (for example `centerpoint-g1g2`, `pointpillars-g1`) and list them in the track doc's Models table.

Per-GPU batch sizes on a 48 GB A6000 (start here, raise to about 80% memory): PointPillars/SECOND 8-16, CenterPoint 6-8, Voxel R-CNN 4-6, PV-RCNN++ 2-4, DSVT/SEED 2-4. The smoke runs took about 0.2 s per iteration at batch 4 for PointPillars on a shared GPU.

**Steps.**
1. **Data mix sweep:** UT : G1 : G2 ratios (for example 1:1:0, 1:1:1, 0:1:1), each resampled to 50k.
2. **Architectures, routed per class:** anchor-based PointPillars/SECOND with multi-mode anchors for vehicles and trucks (the ECCV winner's best vehicle model); finer voxels (0.075-0.1 m) with a center or transformer head (CenterPoint, VoxelNeXt, DSVT, TransFusion-L) for pedestrians and riders (roadside benchmarks: InScope pedestrian AP40@0.5 23.8 for pillars vs 49.6 for CenterPoint). Optionally GBlobs input features (BSD-3) as one member, and self-run ALSO pretraining on synthetic frames. Choose 2-3 decorrelated finalists and fuse per class.
3. **Heads for multi-modal classes:** multiple anchors per class (LUMPI Truck with 2-3 modes; V2X pedestrian with walker and rider modes; V2X truck with trash-can, van/truck and bus modes), or a center head with class-specific size regression.
4. **Augmentation:** GT-sampling from synthetic objects (rare classes up-weighted), random object scaling (0.9-1.1), beam/line dropout and point dropout (density robustness), small global rotation (+/-10 degrees; the scene layout is fixed) and scaling (0.95-1.05), flips only if the placement statistics are symmetric enough (test on real val).
5. **Class balance:** CBGS-style sampling or per-class loss weights; watch Person/pedestrian and the small LUMPI classes.
6. **Selection:** real-val-A per-class AP with bootstrap 90% intervals (1,000 resamples over frames); keep a change only if the interval of the difference excludes 0 or the change is cheap and neutral.

**Acceptance (Gate E).** Chosen configs documented in the registry with real-val-A and real-val-B numbers.

---

## M11. Inference stack

**Goal.** Squeeze every AP point out of the models with post-processing selected on real val.
**Where.** `common/bdc26/detect/postprocess.py` (done: score floor, per-class rotated NMS, re-centering, hedged duplicates; configured per model in `test/postprocess.yaml`); to build: `common/bdc26/detect/ensemble.py` (rotated WBF, per-class routing), TTA in `common/tools/pcdet_predict.py`, density re-scoring.

**Steps (each is an ablation row).**
1. Score floor 0.01; up to 500 boxes per frame; never threshold per class.
2. **Per-class NMS IoU** grid search (vehicles 0.05-0.3; pedestrians/persons 0.3-0.8; riders 0.2-0.6). Implement it yourself: OpenPCDet's `MULTI_CLASSES_NMS` asserts (off-by-one label mapping) on single-head multi-class models. The ECCV winner's V2X mAP went from 0.075 to 0.43 by moving pedestrian NMS from 0.3 to 0.7.
3. **Re-centering:** move small-object box centres toward the centroid of in-box points (`c' = (1-a) c + a * centroid`, a in [0, 0.5], at least 3 points); never for vehicles unless real val says otherwise.
4. **Density-aware re-scoring:** `score * f(points_in_box, range)` with a monotone f fitted on real val.
5. **TTA, per class:** x-flip and y-flip if the model was trained with flips; z-offset TTA ({-0.4, 0, +0.4} m for vehicles, {-0.6, 0, +0.6} m for pedestrians, as in RoboSense 2025) against sim-to-real height bias; small-yaw TTA only if it helps. Enable per class: the ECCV winner's flip TTA helped vehicles (+2.6%) and pedestrians (+5.3%) but cost trucks 23%.
6. **Ensemble:** per-class primary/auxiliary routing (luopuu: `s = 0.6 s_primary + 0.4 s_aux` on IoU-0.5 matches, LUMPI val 0.132 to 0.158), or rotated 3D weighted box fusion (about 80 lines on OpenPCDet IoU ops; `ensemble_boxes` 3D fusion is axis-aligned and unusable). Cluster per class by BEV IoU (vehicles, 0.5-0.6) or centre distance (VRUs, 0.5-1.0 m); score-weighted mean of centre and size; heading by weighted mean of (cos 2t, sin 2t), resolved toward the top box; fused score times `min(n_boxes, n_models)/n_models`. MS3D's KDE box fusion (Apache-2.0, 38.7 vs 36.6 AP3D@0.7 for WBF) is the alternative; fix its two known bugs first.
7. **Class-hedged duplicates (LUMPI):** emit a discounted copy of Car boxes as Van, Bicycle as Motorcycle, Truck as Bus (discount factor selected on real val). Per-class AP is independent, so this can only help the receiving class if discounted properly; disclose it in the report.
8. **Gated (Q2):** static-background prior from legal real frames to down-weight boxes on permanent structures.

**Acceptance.** Each step is kept only if it improves real-val-A mAP; the final stack is confirmed on real-val-B.

---

## M12. Frame selection, final packaging, report

**Goal.** The 50 best legal realism frames, bullet-proof zips, and a report written as you go.
**Where.** `common/tools/package_submission.py` (done; `--syn-list` takes the selector's output); to build: `common/tools/select_realism_frames.py`. The report is drafted from `model-<track>/registry.csv` and the `submissions/*/manifest.json` files.

**Steps.**
1. **Pool:** 2,000-5,000 frames from the **same generator configuration** as the final training corpus (G2 or G1), canonicalized, resampled to 50k, V2X nulls included.
2. **Greedy selection:** start from a random 50; swap frames to minimize the converged-EMD proxy against proxy set 1 (use sliced Wasserstein as a fast surrogate inside the loop, with exact EMD every 50 swaps); stop when the improvement is below the proxy's variance across proxy sets 2-5. Guard against overfitting one proxy set: accept a selection only if it improves the mean over all proxy sets.
3. **No metric-only warping** of the selected frames. Any correction that improves the proxy (pose, scale, density) belongs in the generator, where it also reaches the training data.
4. **Memorization guard** (the DQ clause): for every selected frame, compute the nearest-neighbour Chamfer of its foreground points to all legal real train frames; reject frames closer than the real-train-vs-real-held-out distribution. Mandatory if any generator component was fitted to real scans.
5. **Final zips:** produced by `package_submission.py` into `model-<track>/<model>/submissions/<date>_final-<k>/` from tagged checkpoints; validated; local scores in the manifest; dry-run the exact final zip in the dev phase before Oct 30.
6. **Report (4-8 pages, IEEE two-column):** problem; data and rule compliance (guard, exclusion windows, real-data log); engines G1/G2 and the sensor model; VRU synthesis and label conventions; detector and inference stack; ablations from the registry (UT-only baseline in every table); limitations. Draft Sections 1-3 during week 3; finish Nov 3-14.

**Acceptance (Gate F).** Two tagged final systems per track with archived zips, local scores, configs and seeds.
