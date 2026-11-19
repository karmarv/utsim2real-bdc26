# 06. Learning path: from first principles to a state-of-the-art Sim2Real system

> Each level teaches the concepts you need for one part of the build, points to a small amount of high-value reading, and ends with a hands-on exercise that **is** a module of the real system (`04-IMPLEMENTATION-GUIDE.md`). You learn by building the entry. Levels 0-5 are required before the Oct 25 feature freeze; Level 7 is optional depth for the report and future work.
> Reading budget: about 1-2 hours per level. Do the exercise the same day.

---

## Level 0: Orientation (1 hour)

**Concepts.** Train-on-synthetic, test-on-real. Domain shift. Why roadside LiDAR is special (fixed sensor, fixed scene, elevated oblique view). The 60/40 score and why detection dominates (`01-CHALLENGE-FACTS.md` Section 4.3).

**Read.** `01-CHALLENGE-FACTS.md`, `02-STRATEGY.md`. Skim the three UrbanTwin papers in `reference/papers/` (abstract, figures, results tables).

**Check yourself.** Why does adding low-confidence detections never lower KITTI AP? Why does the per-frame point count of your 50 synthetic frames not matter to the realism score?

---

## Level 1: LiDAR as a measurement device

**Concepts.**
- Time-of-flight ranging; a spinning multi-beam sensor; **channels (beams)** with fixed elevation angles; azimuth sampling (columns per revolution); frame rate.
- **Beam tables**: uniform or staggered (Ouster OS1) versus non-uniform (HDL-64E, Pandar64, PandarQT). Per-beam azimuth offsets.
- **Range image**: rows = beams, columns = azimuth; the natural lossless representation of one spin.
- **Ray-drop**: no return because of low reflectance, grazing incidence, absorbing or specular surfaces, or maximum range. It is structured, not random.
- Range noise, the near-range blind zone, multi-return, motion distortion (rolling shutter).
- **Mounting pose** (height, tilt, yaw) of a roadside unit sets the entire density field: the concentric ground rings and their spacing encode height and tilt.
- Coordinate frames: sensor frame, world/site frame, and the frame the challenge uses for its test frames.

**Read.**
- Ouster OS1 datasheet and firmware user guide (beam configuration, `beam_altitude_angles`, `lidar_mode`).
- Velodyne HDL-64E and VLP-16 manuals (laser firing order, per-laser elevation tables); Hesai Pandar64 / PandarQT user manuals (channel angle tables).
- Milioto et al., "RangeNet++", IROS 2019 (range-image projection section only).

**Do (module M5, part 1).** Read `common/bdc26/io/lumpi.py` (`read_ply`, `read_sessions`) and `common/bdc26/io/v2x.py`. Load 200 guard-allowed real frames of each sensor (after `fetch_real.py`). Compute each point's elevation angle `atan2(z', sqrt(x'^2+y'^2))` in the sensor frame, histogram it at 0.01 degrees, and recover the beam table by peak finding. Fit the sensor height and tilt from the ground rings. Compare against the datasheet.

**Check yourself.** Why can CARLA's `ray_cast` sensor not reproduce an HDL-64E? What does a 1 degree tilt error do to the ground-ring radius at 30 m?

---

## Level 2: 3D object detection fundamentals

**Concepts.**
- The 7-DoF box `[x, y, z, dx, dy, dz, heading]`; the OpenPCDet convention (centre, full extents, heading about +Z).
- **3D IoU** = oriented BEV polygon intersection x height overlap. Why IoU 0.5 punishes a 0.3 m z error on a 1.7 m pedestrian.
- **AP**: sort by score, precision/recall curve, interpolated precision, **R40** (40 recall positions, Simonelli et al. 2019) versus R11; mAP over classes; class exclusion when there is no GT.
- Point-cloud encoders: **voxels** (VoxelNet), **sparse 3D convolution** (SECOND), **pillars** (PointPillars), points (PointNet/PointNet++).
- Heads: anchor-based (SECOND) versus **center-based anchor-free** (CenterPoint); one-stage versus two-stage refinement (Voxel R-CNN, PV-RCNN); fully sparse heads (VoxelNeXt).
- Training: target assignment, focal loss, the regression parameterization of size and heading, NMS.
- Data augmentation: **GT-sampling / copy-paste** (introduced by SECOND), global rotation/scale/flip, per-object noise.

**Read.**
- Yan et al., "SECOND", Sensors 2018.
- Lang et al., "PointPillars", CVPR 2019, arXiv:1812.05784.
- Yin et al., "CenterPoint", CVPR 2021, arXiv:2006.11275.
- OpenPCDet `docs/GETTING_STARTED.md` and `docs/CUSTOM_DATASET_TUTORIAL.md`.

**Do (modules M3 + M4).** Read `common/bdc26/evalap.py` next to OpenPCDet's `kitti_object_eval_python/eval.py` and explain every difference; run `pytest -q common/tests -k "iou or ap"` and add one fixture of your own (a rotated box pair with a hand-computed IoU). Then train `model-v2x-track/archive/pointpillars-ut` (`train/train.sh`), run `validation/evaluate.sh`, and read its per-class AP in `validation/results/`.

**Check yourself.** Why do anchor-free heads cope better with unusual box sizes? What does GT-sampling do to the class balance of a batch?

---

## Level 3: The Sim2Real gap, formally

**Concepts.**
- Domain shift taxonomy: **covariate shift** (the input distribution changes: density, beam pattern, noise, background), **label/prior shift** (class frequencies change), **concept shift** (the annotation convention changes: what a "Bicycle" box contains).
- The dominant LiDAR gaps: point density and beam pattern; **object size priors** (a detector's regression head memorizes source sizes); viewpoint and mounting; missing points (occlusion, ray-drop); intensity; scene content.
- **Statistical Normalization**: rescale source boxes to target mean sizes. **Random Object Scaling** (ST3D). Beam/line down-sampling.
- Regimes: domain randomization (make the source broad) versus **domain matching** (make the source look like one known target), domain generalization (no target data) versus **unsupervised domain adaptation** (unlabeled target data) versus supervised fine-tuning (forbidden here).
- Why this challenge is a **domain-matching** problem: the target sensor and site are known and measurable.

**Read.**
- Wang et al., "Train in Germany, Test in the USA", CVPR 2020, arXiv:2005.08139.
- Yang et al., "ST3D", CVPR 2021, arXiv:2103.05346 (sections on ROS and pseudo-labels).
- The UrbanTwin detection paper (`reference/papers/High-Fidelity_Digital_Twins...pdf`), results and ablations.

**Do (module M5, part 2).** Build the real validation set (`data-<track>/prepare_realval.py`; for LUMPI read `class_report.json`) and compute real-vs-UT statistics per class: counts, sizes (dx, dy, dz), z-centre relative to ground, heading distribution, points per box versus range. Every mismatch you find is a generator hyperparameter to fix.

**Check yourself.** If UT cars are 4.9 m long and real cars average 4.5 m, what happens to BEV IoU for a perfectly centred prediction?

---

## Level 4: LiDAR simulation

**Concepts.**
- **Raycasting** against triangle meshes; bounding-volume hierarchies; Embree. Rays per frame, rays per second.
- A **sensor model** is: beam table + azimuth grid + pose + range limits + noise + **ray-drop model**. Fit each part to real data.
- Scene representation: meshes, surfels, voxels, neural fields. Static versus dynamic content.
- **Asset insertion** with correct occlusion: render the object with the same rays, z-buffer merge with the background range image (LiDAR-Aug, Fang et al., CVPR 2021).
- **Reconstruction-based simulation** (LiDARsim: build a scene from real scans, insert assets, learn ray-drop) versus game-engine simulation (CARLA) versus neural rendering (NeRF/3DGS for LiDAR).
- Labels for free: every hit carries an instance ID, so boxes and point counts are exact. Real annotators, however, follow a policy (minimum points, box tightness), and your labels must follow the same policy.

**Read.**
- Manivasagam et al., "LiDARsim", CVPR 2020, arXiv:2006.09348.
- Fang et al., "LiDAR-Aug: A General Rendering-based Augmentation Framework for 3D Object Detection", CVPR 2021.
- Open3D `RaycastingScene` tutorial; CARLA sensor reference (`ref_sensors`, LiDAR section) to see what a game-engine sensor does and does not model.

**Do (modules M6, M7, M8).** Start from `common/bdc26/render/lidar_sim.py` and build the sensor model with a per-beam table (M6), the procedural pedestrian and cyclist generator (M7), and ray-consistent insertion into UT frames (M8, engine G1).

**Check yourself.** Why must an inserted pedestrian remove the background points behind it? Why is uniform random ray-drop a poor model?

---

## Level 5: Measuring distributional realism

**Concepts.**
- Point sets as empirical distributions. **Chamfer distance** (nearest-neighbour; insensitive to density), **EMD / Wasserstein-1** (optimal transport; sensitive to where mass sits), **MMD** (kernel two-sample statistic; the median heuristic), **Frechet distance** between Gaussians (only mean and covariance).
- **Sampling floor**: two independent 10k samples of the same distribution still have non-zero CD and EMD. Measure it with two disjoint real sets.
- Pooling: the challenge pools 50 frames, so for a fixed sensor the static background dominates.
- Metric gaming versus real fidelity; why the organizers inspect submitted frames.

**Read.**
- Achlioptas et al., "Learning Representations and Generative Models for 3D Point Clouds", ICML 2018, arXiv:1707.02392 (CD/EMD for point clouds).
- Gretton et al., "A Kernel Two-Sample Test", JMLR 2012 (MMD, sections 1-3).
- Heusel et al., FID, NeurIPS 2017, arXiv:1706.08500 (the Frechet formula).
- Flamary et al., "POT: Python Optimal Transport", JMLR 2021 (`ot.emd2`).

**Do (modules M3 + M5 + M12).** Read `common/bdc26/realism.py` against the kit's `local_eval.py` and make them agree exactly; compute the real-vs-real floor with `common/tools/score_realism.py --syn pcdet/realism-proxy-1 --ref pcdet/realism-proxy-2 ...`; score UT frames and your G1/G2 frames against the real proxy; then write `common/tools/select_realism_frames.py`.

**Check yourself.** Why is EMD the largest realism penalty in every leaderboard entry? What does FPD ignore?

---

## Level 6: A competition-grade detector

**Concepts.**
- Strong LiDAR-only detectors: CenterPoint, **VoxelNeXt** (fully sparse), Voxel R-CNN, PV-RCNN++, sparse window transformers (DSVT). Capacity versus overfitting to the synthetic sampling pattern.
- Class imbalance: **CBGS** (class-balanced grouping and sampling), copy-paste rates, per-class heads.
- Domain-generalization augmentation: random object scaling, beam down-sampling, point dropout, jitter; physically consistent versus arbitrary.
- Ensembling: multi-seed and multi-architecture; **3D weighted box fusion**; TTA with flips and small rotations; why TTA must respect the fixed roadside geometry.
- Model selection under a small test set: variance of AP on 50 frames, bootstrap confidence intervals, why you decide on a larger real validation set.

**Read.**
- Chen et al., "VoxelNeXt", CVPR 2023, arXiv:2303.11301.
- Deng et al., "Voxel R-CNN", AAAI 2021, arXiv:2012.15712.
- Zhu et al., "Class-balanced Grouping and Sampling", arXiv:1908.09492.
- Solovyev et al., "Weighted Boxes Fusion", arXiv:1910.13302.

**Do (modules M10 + M11).** Scaffold new models with `common/tools/new_model.py`, train two or three architectures on the final corpus, select on real val with bootstrap intervals, and build the TTA and rotated-WBF stack in `common/bdc26/detect/`.

**Check yourself.** Why can yaw-rotation TTA hurt a roadside detector trained with small rotation augmentation? How many real-val frames do you need to tell a 2 AP point difference from noise?

---

## Level 7: The research frontier (optional; for the report and beyond)

**Topics.** Neural LiDAR rendering (NeRF- and Gaussian-splatting-based LiDAR simulation), diffusion and flow models for range images, sim-to-real translation of LiDAR, unsupervised domain adaptation and test-time adaptation for 3D detection, point-cloud foundation models. The verified reading list, with notes on what is usable under this challenge's rules, is in `07-LITERATURE.md`.

**Do.** Pick one gated branch from `02-STRATEGY.md` Section 6, if the organizers approve it, and run it as a controlled ablation.

---

## Level 8: Research practice (runs through every level)

- **One change per experiment.** Every run is registered with its config hash, data version, seed, real-val AP per class, and realism proxy.
- **Ablation table from day 1.** It becomes Section 5 of the report.
- **Reproducibility.** Seeds, pinned environments, a script per figure.
- **Honest baselines.** Always report the UT-only baseline next to your system.
- **Report (4-8 pages, IEEE format):** problem, method (engines G1/G2, sensor model, VRU synthesis, detector), rule compliance, ablations, limitations.
