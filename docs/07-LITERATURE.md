# 07. Literature and evidence (verified 2026-09-30; named references and detector research added 2026-10-06)

> Every arXiv ID below was resolved against the arXiv API on 2026-09-30. "Use here" says how the work plugs into a module of `04-IMPLEMENTATION-GUIDE.md`. Licence notes matter because the entrant works at an industrial lab. Numbers are as reported by each source and are not comparable across papers.

---

## 1. Audit of the Sep-17 literature review (`RESEARCH-OVERVIEW.md`, removed from the tree; `git show 2a0bc24:reference/RESEARCH-OVERVIEW.md`)

All 40 arXiv IDs resolve to the claimed papers; none are fabricated. Corrections:

| Item | Sep-17 claim | Verified |
|---|---|---|
| MS3D (2304.02431) | IROS 2023; "W->N AP3D 42.2 vs ST3D 35.9" | **ITSC 2023**; those numbers are **AP_BEV**; AP3D is 24.8 vs 20.2 |
| "Single source as multiple density domains" | ECCV 2024 detection DG method, no ID | arXiv:2312.12098; **semantic segmentation only** (detection is listed as future work) |
| LiDAR DG empirical study (2402.17562) | "line downsampling +3 to +7 mAP" | Line downsampling gives **+17.5 Car / +24.5 Ped**; +3-7 comes from a taller voxel. Missed headline: **test-time anchor resizing** took SECOND W->K from 9.9 to 65.7 |
| DRUM (2603.26263) | sim-to-real translation for detection | ICRA 2026, evaluated on **segmentation only** |
| Density-Resampling DG (2311.10845) | "generalization loss", no venue | **ECCV 2024**; physics-aware density augmentation + a self-supervised auxiliary task + a test-time adaptation step |
| ST3D "N->K 18 to 62+" | ST3D | 62.4 is **ST3D++**; ST3D is 54.1 |
| InfraDet3D | ITSC 2023 | arXiv:2305.00314, **IEEE IV 2023** |
| Rope3D "winning solutions respected sensor geometry" | lesson for LiDAR | Rope3D is a **monocular camera** dataset; the claim is unsupported |
| UrbanTwin licence | (not stated) | The papers are CC BY-NC-ND; the **UT datasets are CC0 1.0** |
| Real-data rules | "UDA confirmed disallowed; no real data even unlabeled" | Wrong: the Rules tab allows the real train split for hyperparameter selection and domain adaptation (`01` Section 3) |
| V2X sensor | "Ouster OS1-128" | V2X-Real has **two** infrastructure units, OS1-128 (+/-22.5 deg) and OS1-64 (+/-16.6 deg); the ECCV winner reports that the challenge unit is the **OS1-64**. Verify from the real elevation histogram (M5.3) |

## 2. The most relevant evidence: the ECCV 2026 edition of this challenge

Same scorer, same test data, same rules (summary in `01-CHALLENGE-FACTS.md` Section 7.3).

| Source | What to take from it | Licence |
|---|---|---|
| AMAN_UPG winner reports, `github.com/amanupg/urbantwin-sim2real-{v2x,lumpi}` | Per-class NMS (pedestrian 0.7); re-centering small boxes on interior points; matched-pair size calibration on real train frames (truck length x1.154: truck AP 0.415 to 0.528); density re-ranking; multi-mode anchors (V2X combined 0.515 to 0.626); per-class TTA (flip TTA cost trucks 23%); 50k density; null returns; EMD holds 79-86% of the remaining realism headroom; 35% of LUMPI reference mass lies where the twin has no geometry; LUMPI Bus GT is mostly not buses | **No licence file**: read and cite; do not copy code or weights |
| Luo et al., arXiv:2609.07608 (V2X), 2609.07590 (LUMPI) | 50k resampling for honest validation; RangeLDM "redraws" as an extra training domain; DSVT experts with per-class primary/auxiliary fusion (LUMPI val 0.132 to 0.158); resizing synthetic pedestrians to real dims (0 to 0.142 ped AP); fancy realism transforms fail on the hidden set | arXiv |
| `github.com/NithishaVenkatesh/urbantwin-lumpi` | Real LUMPI anchor sizes; WBF of PointPillars/SECOND; a cautionary tale: realism fitted on the forbidden test frames dropped from 0.906 to 0.593 when refitted legally | MIT |
| Organizer: `github.com/m-shahbaz-kharal/HiFi-DT-Utils` | UT-LUMPI CARLA sensor positions, uniform channel tables, map transform, label conversion | No licence file |
| Organizer leakage study, arXiv:2606.12981 (TUMTraf-V2X) | Expect scrutiny of synthetic frames that copy real ones | arXiv |

## 3. Reading list by module

### 3.1 Sim-to-real for detection, and why box conventions dominate (M5, M7)

| Work | ID / venue | Key result | Use here |
|---|---|---|---|
| Statistical Normalization ("Train in Germany, Test in the USA") | 2005.08139, CVPR 2020 | nuScenes->KITTI Car (PointRCNN, moderate, IoU 0.7) AP3D 10.7 to 31.0, APBEV 39.8 to 67.4 by matching object sizes (KITTI-trained 68.9; Table 4; corrected 2026-10-18) | Size synthetic objects and labels to real train-split statistics |
| PCGen | 2210.08738 | Pedestrians 6.56 to **54.31** 3D AP@0.5 (real 61.62) with "CAD Modified": boxes loosened **and** poses filtered, both fitted to real box and point statistics (not loosening alone; corrected 2026-10-18); per-ray drop MLP +1.4 | Fit label conventions per class (M7); simple learned ray-drop (M6) |
| Synth It Like KITTI | 2502.15076, ROBOVIS 2025 | Simulated intensity hurt transfer; box convention mattered | xyz only; conventions first |
| Huch et al. | 2303.01899, IEEE T-IV 2023 | ~14% AP drop sim-to-real; a range-noise model helps, downsampling alone does not | Range noise in M6 |
| CTS | 2406.18129 | Naive CARLA to KITTI is about 4 AP3D; with sim-to-real UDA 45.3 | Shows the size of the naive gap; the UDA part is gated |
| UrbanTwin trilogy | 2509.02903, 2509.02904, 2509.06781 (OJ-ITS 2026) | Twin fidelity beats a generic map; synthetic-only Car AP 63.2 (V2X), 44.7 (LUMPI) | Engine G1 base data |

### 3.2 Sensor simulation, insertion and ray-drop (M6, M8, M9)

| Work | ID / venue | Key idea | Code / licence | Use here |
|---|---|---|---|---|
| LiDARsim | 2006.09348, CVPR 2020 | Surfel map from real sweeps + asset bank + learned ray-drop | Closed | Blueprint of G2 |
| LiDAR-Aug | Fang et al., CVPR 2021 | Rendering-based insertion with occlusion | - | G1 insertion |
| DR.CPO | 2303.12743 | Whole-body object construction, hidden-point-removal occlusion, distance-adaptive density; +2.08 mAP KITTI, best on ped/cyc | SNU-DRL/DRCPO, Apache-2.0, OpenPCDet | Reference for occlusion-correct VRU insertion |
| Real3D-Aug | 2206.07634, CVWW 2023 | Placement search + occlusion; +6.65 AP hard pedestrian | No licence | Re-implement the placement logic |
| PCSim (infrastructure LiDAR placement) | 2211.15975, ICRA 2023 | CARLA plugin with real scan patterns: **Pandar64, HDL-64, PandarQT, VLP-16, OS1-64** | PJLab-ADG/PCSim, Apache-2.0 | Starting beam tables for M5.3/M6 |
| ReSimAD | 2309.05527, ICLR 2024 | Real mesh reconstruction then re-simulation of a target LiDAR | 3DTrans Apache-2.0 | Recipe for the gated real-reconstructed scene |
| Roadside background subtraction | 2201.04756; 2510.22390 (ICVES 2025) | Per-(beam, azimuth) background models for fixed sensors | not checked | Label-free foreground for ray-drop fitting; movers removal |
| DUSty / DUSty v2 | 2102.11952 IROS 2021; 2210.11750 WACV 2023 | GAN-learned per-pixel ray-drop | MIT | Optional learned drop (gated) |
| LidarDM | 2404.02903, ICRA 2025 | Layout to mesh world to raycast + learned stochastic ray-drop | MIT (Waymo weights gated) | Design reference only |
| NFL | 2305.01643, ICCV 2023 | Physical beam model (divergence, second returns, drop) | No code | Background reading |

For a fixed sensor the strongest cheap ray-drop model is statistical: per-(beam, azimuth) return probability for the static background plus a range/incidence-conditioned drop for objects, all fitted on unlabeled train-split frames.

### 3.3 Humans and riders (M7)

| Work | ID | Use here | Licence |
|---|---|---|---|
| Anny body model | 2511.03589, ECCV 2026 | Licence-clean parametric human (all ages) to replace SMPL | naver/anny, Apache-2.0 |
| MakeHuman / MPFB2 core assets | - | Base meshes and clothing | CC0 exports |
| CMU MoCap (BVH/AMC originals), 100STYLE | - | Gait and pose sequences | Free incl. commercial / CC BY 4.0 |
| DAPT human synthesis; LiDAR HMP | 2412.13454 AAAI 2025; 2408.08202 ACM MM 2024 | Raycast humans with laser-level occlusion | - |
| Paved2Paradise | 2312.01117, CVPRW 2024 | Compositing background and object captures | MIT |

Avoid: SMPL/SMPL-X/AMASS/BEDLAM/AGORA (non-commercial, including training for commercial use), Mixamo (AI/ML use banned), RenderPeople, real human LiDAR captures (SLOPER4D, LiDARCap: real data).

### 3.4 Detectors, and what works on roadside data (M4, M10)

| Detector | ID / venue | In mainline OpenPCDet | Roadside evidence | Licence |
|---|---|---|---|---|
| PointPillars | 1812.05784, CVPR 2019 | Yes | ECCV winner's model (strong on vehicles with multi-mode anchors); **weak on pedestrians** (InScope ped AP40@0.5 23.8) | Apache |
| SECOND | Sensors 2018 | Yes | Beats pillars on DAIR-V2X-I pedestrians | Apache |
| CenterPoint | 2006.11275, CVPR 2021 | Yes | InScope ped 49.6 vs pillars 23.8 | Apache/MIT |
| Voxel R-CNN | 2012.15712, AAAI 2021 | Yes | Two-stage refinement helps IoU 0.5 | Apache |
| PV-RCNN++ | 2102.00463, IJCV | Yes | Top of InScope mAP40 | Apache |
| TransFusion-L | 2203.11496, CVPR 2022 | Yes | Best pedestrian AP on HoloVIC (45.5 vs 27.4 pillars) | Apache |
| VoxelNeXt | 2303.11301, CVPR 2023 | Yes | Built-in double-flip TTA | Apache |
| DSVT | 2301.06051, CVPR 2023 | Yes | ECCV runner-up's backbone | Apache |
| HEDNet / SAFDNet | 2310.20234 / 2403.05817 | LION fork | Strong fully sparse | Apache |
| LION | 2407.18232, NeurIPS 2024 | LION fork | RoboSense 2025 cross-platform winner | Apache |

Roadside benchmarks: V2X-Real IC no-fusion PointPillars ped AP@0.5 12.7 (2403.16034); DAIR-V2X-I (2204.05575); HoloVIC (2403.02640); InScope (2407.21581); RCooper (2403.10145); TUMTraf-I (2306.09266).

Lesson: route classes. Anchor-based pillars/SECOND with multi-mode anchors for vehicles and trucks; finer voxels with center or transformer heads for pedestrians and riders; fuse per class.

Avoid: SEED (no licence file), PillarNeXt (CC BY-NC-SA), FocalFormer3D (NVIDIA NC). OpenPCDet master's `MULTI_CLASSES_NMS` has an off-by-one assertion on single-head multi-class models: write your own per-class NMS.

### 3.5 Domain generalization and augmentation (M10)

| Work | ID / venue | Result | Use here |
|---|---|---|---|
| GBlobs | 2503.08639, CVPR 2025; 2510.18539 (RoboSense 2025 placement track winner) | +21 mAP W->K over DG SOTA; parameter-free local-covariance input features | One portfolio member (BSD-3, OpenPCDet) |
| Empirical LiDAR DG study | 2402.17562, CVPR 2024 | Anchor sizes, voxel height, line downsampling | Anchors from real statistics; line dropout if the real frames are sparser |
| DTS (random beam re-sampling) | 2304.09446, CVPR 2023 | Closes 88-94% of the N->K gap (with self-training) | RBRS as a source-only augmentation |
| LiDAR Distillation | 2203.14956, ECCV 2022 | Beam downsampling for density robustness | Augmentation |
| PDDA (density resampling) | 2311.10845, ECCV 2024 | Physics-aware density augmentation | Cover the 50k test density |
| 3D-VField | 2112.04764, CVPR 2022 | Ray-constrained adversarial deformation | Optional |
| ST3D random object scaling | 2103.05346, CVPR 2021 | ROS | Augmentation |

### 3.6 Unsupervised domain adaptation and self-training (gated, `02` Section 6)

ST3D / ST3D++ (2103.05346, 2108.06682), MS3D / MS3D++ (2304.02431 ITSC 2023, 2308.05988 T-IV 2024; KDE box fusion is also a good ensembler), ReDB (2307.07944, ICCV 2023), CTS (2406.18129), SOAP (2401.04230, WACV 2024; stationary-object aggregation suits a fixed sensor). Use only after a written organizer "yes". Test-time adaptation on the 50 test frames (MOS 2406.14878, DPO 2406.13891) is out: the test frames are forbidden for fitting.

### 3.7 Generative models (optional, gated for real-trained priors)

Every public box-conditioned checkpoint was trained with real labels on non-commercial data, so only two uses are clean: an unconditional prior retrained on unlabeled train-split scans to refine simulator frames, or a model trained on synthetic pairs. Candidates: R2DM (2309.09256, ICRA 2024, MIT), RangeLDM (2403.10094, ECCV 2024, MIT; used by the ECCV runner-up), R2Flow (2412.02241, ICRA 2025), DRUM-style masked refinement (2603.26263). Any generator trained on one intersection needs a memorization check against real train frames before its output is submitted.

### 3.8 Inference and ensembling (M11)

| Source | ID | What worked | Use here |
|---|---|---|---|
| HorizonLiDAR3D, Waymo 2020 1st | 2006.15505 | Rotated WBF +2.2, TTA +2.6, per-class threshold search +1.6 (a ranking effect in their metric) | Rotated WBF + TTA |
| CenterPoint nuScenes 2020 | 2006.11275 | Double flip, yaw TTA, 5-model ensemble, empty-box filter | Flip TTA, empty-box filter |
| PV-RCNN Waymo 2020 report | 2008.12599 | Soft-NMS, box voting | Box voting after NMS |
| MS3D KDE box fusion | 2304.02431 | KBF 38.7 vs WBF 36.6 vs NMS 34.9 AP3D@0.7 | Alternative to WBF (Apache-2.0; two known bugs) |
| RoboSense 2025 | 2601.05014 | Ground-plane canonicalization +5.1; height TTA {-0.4, 0, +0.4} m (cars), {-0.6, 0, +0.6} m (peds) | z-offset TTA for sim-to-real height bias |
| AFDetV2 / CIA-SSD | 2112.09205 / 2012.03015 | IoU-aware rescoring | Score calibration |

### 3.9 Pre-training (optional)

Checkpoints with real labels anywhere in their lineage are forbidden; public self-supervised checkpoints carry non-commercial data licences. The clean route is to run a self-supervised objective yourself on synthetic frames: ALSO (2212.05867, CVPR 2023, Apache-2.0, about +1-2 mAP) or Occupancy-MAE (2206.09900, Apache-2.0).

### 3.10 Metrics (M3)

Achlioptas et al. 1707.02392 (CD/EMD for point clouds); Gretton et al., JMLR 2012 (MMD); Heusel et al. 1706.08500 (FID/Frechet); TreeGAN 1905.06292 (original feature-space FPD, not the challenge's xyz FPD); Flamary et al., JMLR 2021 (POT).

## 4. Licence register (for Hitachi counsel)

**Use statement (2026-10-18).** All work in this repository is academic, non-commercial research: the challenge entries, their reports and papers. That is within the non-commercial and academic terms below (LUMPI CC BY-NC 3.0, V2X-Real academic use). No derived asset is used commercially; any product use at Hitachi will be built on a separate open-source stack.

| Item | Licence | Risk | Action |
|---|---|---|---|
| UT-LUMPI, UT-V2X-Real-IC | CC0 1.0 | None | Use |
| **LUMPI real data** | **CC BY-NC 3.0** | Non-commercial | Confirm that competition research use is acceptable; do not ship derived assets commercially |
| **V2X-Real** | **UCLA Academic Software License** (academic or non-profit researchers; commercial entities must contact UCLA). Dataset terms: check the download page | **May not cover a corporate researcher** | **Legal check on D0.** If blocked, run V2X without a real validation set (UT + synthetic val, leaderboard confirmation only) |
| OpenPCDet, LION fork, MS3D, DR.CPO, PCSim | Apache-2.0 | None | Use |
| GBlobs | BSD-3 | None | Use |
| LiGuard-2.x | MIT | None | Use |
| HiFi-DT-Utils (organizer script) | No licence | Low (read the parameters, do not redistribute) | Re-implement |
| ECCV winner repos | No licence | Copying is infringement | Read and cite only |
| SEED | No licence | Low for a competition, blocked for internal reuse | Avoid |
| MakeHuman/MPFB2 core, Kenney, Quaternius, Poly Haven | CC0 | None | Use |
| CARLA assets | CC-BY 4.0 (Epic-material and brand caveats) | Low | Credit; strip brand names |
| Objaverse / Sketchfab | Per object | Mixed | Filter to CC0/CC-BY; keep CREDITS |
| SMPL-family, AMASS, Mixamo, RenderPeople, ShapeNet, TurboSquid | Non-commercial or AI/ML banned | High | Do not use |
| RangeLDM / R2DM code | MIT | None; released weights use NC data | Retrain if needed |

## 5. Not recommended (and why)

- NeRF/3DGS reconstruction of the site: every method assumes a moving ego sensor, and several ship Inria non-commercial code (GS-LiDAR, LiDAR-RT). An explicit mesh from accumulated scans does the same job for a fixed sensor.
- Public generative or pretrained checkpoints: real-label lineage or non-commercial data.
- Test-time adaptation on the test frames: forbidden frames, 50-frame sample, unlicensed code.
- Working on LUMPI Bus beyond hedged duplicates: the GT is mostly not buses.
- Heavy multi-hypothesis class emission beyond measured confusions: about +0.001 combined, and it reads as metric mechanics in a paper.

## 6. Named references (R1-R42)

The root README, [`02-STRATEGY.md`](02-STRATEGY.md) and the track model READMEs cite these as **[Rn]**, and each citation links to the entry below. Each entry gives the work, a link, what we use it for, and the evidence we rely on. Numbers are as reported by each source and are not comparable across papers. R1-R23 were verified on 2026-09-30; R24-R42 were added on 2026-10-06 for the next strategies ([Section 7](#7-detector-research-for-the-next-strategies-2026-10-06)).

### Challenge, data and framework

#### R1 UrbanTwin papers
UCF Urbanity Lab, the UrbanTwin papers: [arXiv:2509.02903](https://arxiv.org/abs/2509.02903), [arXiv:2509.02904](https://arxiv.org/abs/2509.02904), [arXiv:2509.06781](https://arxiv.org/abs/2509.06781) (OJ-ITS 2026); PDFs in [`reference/papers/`](reference/papers). **Used for:** the CC0 twin datasets UT-LUMPI and UT-V2X-Real-IC (the base of every strategy) and the challenge protocol and metrics. **Evidence:** twin fidelity beats a generic map; synthetic-only Car AP 63.2 (V2X) and 44.7 (LUMPI).

#### R2 LiGuard
The organizers' LiDAR research framework (PDF in [`reference/papers/`](reference/papers); LiGuard-2.x is MIT). **Used for:** data and label conventions of the organizer pipeline.

#### R3 LUMPI dataset
Busch et al., *LUMPI: The Leibniz University Multi-Perspective Intersection Dataset*, IEEE IV 2022; files at [data.uni-hannover.de/vault/ikg/busch/LUMPI](https://data.uni-hannover.de/vault/ikg/busch/LUMPI/) (CC BY-NC 3.0). **Used for:** Track 1 real validation (realval-A/B), sensor poses and beam tables of the five Measurement4 lidars, legal label statistics.

#### R4 V2X-Real dataset
Xiang et al., *V2X-Real*, ECCV 2024, [arXiv:2403.16034](https://arxiv.org/abs/2403.16034) (UCLA Academic licence). **Used for:** Track 2 real validation, the measured OS1-64 beam table, legal walker statistics. **Evidence:** infrastructure no-fusion PointPillars pedestrian AP@0.5 12.7.

#### R5 PointPillars
Lang et al., *PointPillars: Fast Encoders for Object Detection from Point Clouds*, CVPR 2019, [arXiv:1812.05784](https://arxiv.org/abs/1812.05784). **Used for:** the S1 detector on both tracks. **Evidence:** the ECCV 2026 winner's detector ([R19](#r19-eccv-2026-winner-reports)); weak on small objects in roadside benchmarks ([R24](#r24-inscope)).

#### R6 OpenPCDet
OpenPCDet Development Team, [github.com/open-mmlab/OpenPCDet](https://github.com/open-mmlab/OpenPCDet) (Apache-2.0), commit 233f849. **Used for:** training and inference of every model; its mainline already ships PointPillars, SECOND, CenterPoint, PV-RCNN++, Voxel R-CNN, VoxelNeXt, DSVT, TransFusion-L and PillarNet configs (checked 2026-10-06; DSVT and the dynamic pillar encoders also need `torch_scatter`, not installed yet).

### Sim-to-real transfer and object insertion

#### R7 Statistical normalization
Wang et al., *Train in Germany, Test in the USA: Making 3D Object Detectors Generalize*, CVPR 2020, [arXiv:2005.08139](https://arxiv.org/abs/2005.08139). **Used for:** S1 size conventions (actor scale fix, size calibration). **Evidence:** nuScenes to KITTI Car (PointRCNN, moderate, IoU 0.7, Table 4) AP3D 10.7 to 31.0 and APBEV 39.8 to 67.4 by matching object sizes; KITTI-trained 68.9 (corrected 2026-10-18: the earlier "19.0 to 54.8" is not in the paper). With ground-truth sizes (Table S11) AP3D reaches 47.3.

#### R8 PCGen
*PCGen: Point Cloud Generator for LiDAR Simulation*, [arXiv:2210.08738](https://arxiv.org/abs/2210.08738). **Used for:** annotator box conventions for pedestrians. **Evidence:** pedestrian 3D AP@0.5 6.56 (naive CAD) to 54.31 ("CAD Modified": boxes loosened and poses filtered, both fitted to real box and point statistics) against 61.62 for real data; venue unverified (corrected 2026-10-18).

#### R9 LiDAR-Aug
Fang et al., *LiDAR-Aug: A General Rendering-Based Augmentation Framework for 3D Object Detection*, CVPR 2021. **Used for:** S1 rendering-based walker insertion with occlusion.

#### R10 DR.CPO
[arXiv:2303.12743](https://arxiv.org/abs/2303.12743) (SNU-DRL/DRCPO, Apache-2.0). **Used for:** occlusion-correct whole-body insertion of vulnerable road users. **Evidence:** +2.08 mAP on KITTI, best on pedestrians and cyclists.

#### R11 Real3D-Aug
[arXiv:2206.07634](https://arxiv.org/abs/2206.07634), CVWW 2023. **Used for:** placement with occlusion. **Evidence:** +6.65 AP on hard pedestrians.

#### R12 Huch et al. sim-to-real gap
Huch et al., [arXiv:2303.01899](https://arxiv.org/abs/2303.01899), IEEE T-IV 2023. **Used for:** sizing the sim-to-real gap and the value of range noise. **Evidence:** about 14% AP drop sim-to-real; range noise helps, downsampling alone does not.

#### R13 LiDARsim
Manivasagam et al., *LiDARsim*, CVPR 2020, [arXiv:2006.09348](https://arxiv.org/abs/2006.09348). **Used for:** the statistical sensor model and the blueprint of engine G2 (surfels from real sweeps plus learned ray-drop).

### Metrics

#### R14 R40 average precision
Simonelli et al., *Disentangling Monocular 3D Object Detection*, ICCV 2019, [arXiv:1905.12365](https://arxiv.org/abs/1905.12365). **Used for:** the 40-recall-point interpolated AP of the scorer.

#### R15 Chamfer and Earth Mover's distances
Achlioptas et al., ICML 2018, [arXiv:1707.02392](https://arxiv.org/abs/1707.02392). **Used for:** the CD and EMD realism terms.

#### R16 Maximum mean discrepancy
Gretton et al., *A Kernel Two-Sample Test*, [JMLR 13, 2012](https://jmlr.org/papers/v13/gretton12a.html). **Used for:** the MMD realism term.

#### R17 Frechet distance
Heusel et al., NeurIPS 2017, [arXiv:1706.08500](https://arxiv.org/abs/1706.08500). **Used for:** the FPD realism term (the challenge applies it to xyz, not to network features).

#### R18 POT
Flamary et al., *POT: Python Optimal Transport*, [JMLR 22, 2021](https://jmlr.org/papers/v22/20-451.html). **Used for:** the EMD solver of the scorer and of `bdc26.realism`.

### This challenge's ECCV 2026 edition

#### R19 ECCV 2026 winner reports
amanupg, [urbantwin-sim2real-v2x](https://github.com/amanupg/urbantwin-sim2real-v2x) and [urbantwin-sim2real-lumpi](https://github.com/amanupg/urbantwin-sim2real-lumpi) (no licence: read and cite only). **Used for:** per-class NMS, re-centering, size calibration, null returns, realism findings. **Evidence:** V2X 0.7457 (mAP 0.438, R 0.925), LUMPI 0.4793 (mAP 0.133, R 0.913); per-class NMS took V2X pedestrian-dominated mAP from 0.075 to 0.43; 35% of the LUMPI reference mass lies where the twin has no geometry; the report found CenterPoint no better than PointPillars on this data (as summarized in our track READMEs; re-check before relying on it).

#### R20 ECCV 2026 runner-up reports
Luo et al., [arXiv:2609.07608](https://arxiv.org/abs/2609.07608) (V2X) and [arXiv:2609.07590](https://arxiv.org/abs/2609.07590) (LUMPI). **Used for:** evidence on sparse transformers in this exact setting. **Evidence:** DSVT experts (0.2 m voxels, range [-40, -40, -8, 40, 40, 2], 40-60 epochs) with PointPillars Car/Bus specialists and class-aware fusion (`s = 0.6 s_primary + 0.4 s_aux` for same-class matches at IoU >= 0.5); LUMPI local mAP 0.132 to 0.158 through routing, calibration and fusion; hidden test LUMPI combined 0.4692 (mAP 0.1258, R 0.9035), V2X 0.7421 (mAP 0.4518, R 0.8871); resizing synthetic pedestrians to real dimensions took pedestrian AP from 0 to 0.142.

### Detectors

#### R21 SECOND
Yan, Mao, Li, *SECOND: Sparsely Embedded Convolutional Detection*, [Sensors 2018](https://www.mdpi.com/1424-8220/18/10/3337). **Used for:** the sparse 3D voxel backbone inside CenterPoint (S2) and Voxel R-CNN (S4). **Evidence:** beats pillars on DAIR-V2X-I roadside pedestrians.

#### R22 CenterPoint
Yin, Zhou, Krahenbuhl, *Center-based 3D Object Detection and Tracking*, CVPR 2021, [arXiv:2006.11275](https://arxiv.org/abs/2006.11275). **Used for:** S2 small-class specialists. **Evidence:** anchor-free center heat-map head; on roadside data see [R24](#r24-inscope); double-flip and yaw TTA in its nuScenes entry.

#### R24 InScope
*InScope: A New Real-world 3D Infrastructure-side Collaborative Perception Dataset for Open Traffic Scenarios*, [arXiv:2407.21581](https://arxiv.org/abs/2407.21581). **Used for:** roadside evidence for S2. **Evidence:** cyclist AP PointPillars 58.46 vs CenterPoint 74.74; pedestrian AP40@0.5 23.8 vs 49.6; PV-RCNN++ top in mAP40.

#### R25 Robo3D
Kong et al., *Robo3D: Towards Robust and Reliable 3D Perception against Corruptions*, ICCV 2023, [arXiv:2303.17597](https://arxiv.org/abs/2303.17597). **Used for:** robustness of detector families to sensor and weather corruptions (a proxy for domain shift). **Evidence:** mean corruption error (lower is better) PV-RCNN++ 91.60, CenterPoint 100.00, PV-RCNN 104.90, SECOND 121.43, PointPillars 127.53.

#### R26 LiDAR domain generalization study
*An Empirical Study of the Generalization Ability of LiDAR 3D Object Detectors to Unseen Domains*, CVPR 2024, [arXiv:2402.17562](https://arxiv.org/abs/2402.17562). **Used for:** S5 and the size-calibration rationale of S1. **Evidence:** transformer backbones with local point features are more robust than 3D CNNs; test-time anchor resizing took SECOND Waymo to KITTI from 9.9 to 65.7; line downsampling +17.5 Car / +24.5 Ped for low-resolution targets.

#### R29 PV-RCNN++
Shi et al., *PV-RCNN++*, IJCV 2023, [arXiv:2102.00463](https://arxiv.org/abs/2102.00463). **Used for:** S4 two-stage refinement (its OpenPCDet config uses a center-based first stage). **Evidence:** most robust detector in [R25](#r25-robo3d); top InScope mAP40 ([R24](#r24-inscope)).

#### R30 Voxel R-CNN
Deng et al., *Voxel R-CNN*, AAAI 2021, [arXiv:2012.15712](https://arxiv.org/abs/2012.15712). **Used for:** S4, the lighter two-stage alternative. **Evidence:** voxel RoI pooling refines boxes at IoU 0.5-0.7 at near one-stage speed.

#### R31 DSVT
Wang et al., *DSVT: Dynamic Sparse Voxel Transformer with Rotated Sets*, CVPR 2023, [arXiv:2301.06051](https://arxiv.org/abs/2301.06051). **Used for:** S6. **Evidence:** the ECCV runner-up's backbone ([R20](#r20-eccv-2026-runner-up-reports)), which scored below our S1 PointPillars on both tracks.

#### R32 LION
Liu et al., *LION: Linear Group RNN for 3D Object Detection in Point Clouds*, NeurIPS 2024, [arXiv:2407.18232](https://arxiv.org/abs/2407.18232) (Apache-2.0 fork of OpenPCDet). **Used for:** S6 option. **Evidence:** state of the art on Waymo and nuScenes with Mamba, RWKV or RetNet operators; 3D voxel generation densifies sparse foreground; needs a Mamba build.

#### R33 HEDNet and SAFDNet
Zhang et al., *HEDNet*, NeurIPS 2023, [arXiv:2310.20234](https://arxiv.org/abs/2310.20234); *SAFDNet*, CVPR 2024, [arXiv:2403.05817](https://arxiv.org/abs/2403.05817). **Used for:** S6 option (fully sparse). **Evidence:** on Argoverse2 SAFDNet beats HEDNet by 2.6 mAP at 2.1x the speed.

#### R34 VoxelNeXt
Chen et al., CVPR 2023, [arXiv:2303.11301](https://arxiv.org/abs/2303.11301). **Used for:** S6 option in mainline OpenPCDet. **Evidence:** fully sparse, built-in double-flip TTA config.

#### R35 TransFusion-L
Bai et al., CVPR 2022, [arXiv:2203.11496](https://arxiv.org/abs/2203.11496). **Used for:** S6 option. **Evidence:** best pedestrian AP on HoloVIC ([arXiv:2403.02640](https://arxiv.org/abs/2403.02640)): 45.5 vs 27.4 for pillars.

#### R41 PillarNet
Shi et al., *PillarNet*, ECCV 2022, [arXiv:2205.07403](https://arxiv.org/abs/2205.07403). **Used for:** S2 fallback: a center-head pillar detector that keeps the pillar encoding's density robustness.

#### R42 MMDetection3D model comparison (secondary source)
[zenn.dev/iasl/articles/3385bfcdf892e4](https://zenn.dev/iasl/articles/3385bfcdf892e4), reproducing MMDetection3D checkpoints. **Used for:** a same-framework comparison for S2. **Evidence:** nuScenes mAP PointPillars 39.25 vs CenterPoint 57.28, pedestrian 71.83 vs 84.68. Secondary source: cite the primary papers in the report.

### Domain generalization and augmentation

#### R27 GBlobs
Malic et al., *GBlobs: Explicit Local Structure via Gaussian Blobs for Improved Cross-Domain LiDAR-based 3D Object Detection*, CVPR 2025, [arXiv:2503.08639](https://arxiv.org/abs/2503.08639) (BSD-3, OpenPCDet). **Used for:** S5. **Evidence:** parameter-free local covariance input features in place of absolute xyz; beats the single-source DG state of the art by over 21 mAP (Waymo to KITTI), 13 (KITTI to Waymo) and 12 (nuScenes to KITTI); multi-source +17 / +12 / +5 on Waymo / KITTI / ONCE. **Code:** [github.com/malicd/GBlobs](https://github.com/malicd/GBlobs) (BSD-3): `GBlobsVFE`, 12 values per voxel (offset of the mean from the voxel centre, 3 x 3 sample covariance); ported as `common/bdc26/detect/gblobs_vfe.py`. **S5 outcome (2026-10-11):** at our density 80-83% of the 0.1 m voxels hold one point, so the covariance was taken over 0.4 m cells; as a member it lost (absolute position is real signal at a fixed intersection), inside fusions it helped ([`02-STRATEGY.md` 8.5.1](02-STRATEGY.md#851-results-2026-10-11)).

#### R28 GBlobs for sensor placement
*GBlobs: Local LiDAR Geometry for Improved Sensor Placement Generalization*, [arXiv:2510.18539](https://arxiv.org/abs/2510.18539). **Used for:** S5. **Evidence:** top of RoboSense 2025 Track 3 (detection under different sensor placements).

#### R36 DTS random beam re-sampling
[arXiv:2304.09446](https://arxiv.org/abs/2304.09446), CVPR 2023. **Used for:** S5 augmentation. **Evidence:** closes 88-94% of the nuScenes to KITTI gap together with self-training (beam re-sampling alone is source-only and allowed).

#### R40 ST3D
Yang et al., *ST3D*, CVPR 2021, [arXiv:2103.05346](https://arxiv.org/abs/2103.05346). **Used for:** random object scaling (S5 augmentation); its self-training part is rule-gated (`01` Section 10, question 1). **S5 outcome (2026-10-11):** class-wise anisotropic object scaling about the box bottom with ranges from legal real label sizes (`common/bdc26/detect/augment.py`) lifted every anchor-free and two-stage member (V2X Voxel R-CNN B 0.632 -> 0.667) and the size-gap classes (LUMPI Truck, Bus, Bicycle) ([`02-STRATEGY.md` 8.5.1](02-STRATEGY.md#851-results-2026-10-11)).

### Fusion and test-time augmentation

#### R23 Weighted Boxes Fusion
Solovyev et al., [arXiv:1910.13302](https://arxiv.org/abs/1910.13302). **Used for:** S3 fusion of routed members.

#### R37 MS3D KDE box fusion
[arXiv:2304.02431](https://arxiv.org/abs/2304.02431), ITSC 2023 (Apache-2.0; two known bugs). **Used for:** S3 alternative to WBF. **Evidence:** KDE box fusion 38.7 vs WBF 36.6 vs NMS 34.9 AP3D@0.7.

#### R38 HorizonLiDAR3D
Waymo 2020 1st place, [arXiv:2006.15505](https://arxiv.org/abs/2006.15505). **Used for:** S3. **Evidence:** rotated WBF +2.2, TTA +2.6.

#### R39 RoboSense 2025 report
[arXiv:2601.05014](https://arxiv.org/abs/2601.05014). **Used for:** S3 height TTA and the V2X ground-plane experiment. **Evidence:** ground-plane canonicalization +5.1; height TTA {-0.4, 0, +0.4} m for cars and {-0.6, 0, +0.6} m for pedestrians.

#### R43 Deep ensembles under dataset shift
Ovadia et al., "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift", NeurIPS 2019 ([arXiv 1906.02530](https://arxiv.org/pdf/1906.02530)). Ensembles of independently initialized models were the most robust method under dataset shift across images, text and tabular data, and small ensembles (about five members) sufficed; in-distribution accuracy was a weak proxy for behaviour under shift. Used for S6 (seed bags): sim-to-real is a dataset shift, and our measured seed spread is up to 0.17 AP per class.

#### R44 AFDetV2 (SWA)
Hu et al., "AFDetV2: Rethinking the Necessity of the Second Stage for Object Detection from Point Clouds" ([arXiv 2107.14342](https://arxiv.org/pdf/2107.14342)). Applies stochastic weight averaging to a LiDAR detector: five extra epochs at a tenth of the learning rate with a cyclic schedule, five checkpoints averaged, batch-norm statistics refitted, for about +0.2 mAPH/L2 on Waymo. Reason S6 does not use weight averaging.

## 7. Detector research for the next strategies (2026-10-06)

**Question.** Which detector-side routes beat S1 (PointPillars, [R5](#r5-pointpillars)) on this challenge, and where should CenterPoint ([R22](#r22-centerpoint)) be used? The strategies themselves (effort, risk, steps, gates) are in [`02-STRATEGY.md` Section 8](02-STRATEGY.md#8-strategy-routes-after-s1).

**What the first leaderboard results say** (submissions 965614 and 965633, details in the track model READMEs Section 9):
1. Detector capacity is not the first bottleneck: S1's PointPillars beat the ECCV runner-up's DSVT ensembles on both tracks (mAP 0.136 vs 0.126 LUMPI, 0.465 vs 0.452 V2X; [R20](#r20-eccv-2026-runner-up-reports)).
2. Transfer is: LUMPI Person 0.340 on realval-A vs 0.117 on the test frames, Bicycle 0.265 vs 0.053, Truck 0.200 vs 0.028, with 512, 82 and 192 test GT boxes (from the kit's `config.json`), so these are real gaps, not sampling noise.
3. Height and z cost V2X 0.105 mAP: BEV@0.5 0.570 vs 3D@0.5 0.465.
4. Localization is near the threshold: 3D mAP@0.7 is 0.050 (LUMPI) and 0.056 (V2X).

**Evidence by route.**

| Route | Best evidence for | Evidence against or unknown |
|---|---|---|
| Center heads for small classes (S2) | InScope cyclist 58.46 to 74.74 and pedestrian 23.8 to 49.6 vs pillars [R24](#r24-inscope); nuScenes pedestrian 71.8 to 84.7 [R42](#r42-mmdetection3d-model-comparison-secondary-source); mainline OpenPCDet [R6](#r6-openpcdet) | the ECCV winner reports CenterPoint no better than pillars here [R19](#r19-eccv-2026-winner-reports); real-data benchmarks, not synthetic-to-real |
| Fusion and TTA (S3) | WBF +2.2 and TTA +2.6 [R38](#r38-horizonlidar3d); KDE fusion beats WBF and NMS [R37](#r37-ms3d-kde-box-fusion); the runner-up's class-aware fusion added +0.026 local mAP [R20](#r20-eccv-2026-runner-up-reports); height TTA [R39](#r39-robosense-2025-report) | gains measured in-domain; fusion knobs are tuned on validation, which is how LUMPI over-fit realval-A |
| Two-stage refinement (S4) | most robust family under corruptions [R25](#r25-robo3d); top InScope mAP40 [R24](#r24-inscope); point-level refinement targets the V2X z and the IoU-0.7 gaps [R29](#r29-pv-rcnn), [R30](#r30-voxel-r-cnn) | refinement may relearn synthetic box conventions that post-processing corrects; 3-4x training cost |
| Domain-generalizing inputs (S5) | +21 mAP Waymo to KITTI [R27](#r27-gblobs); RoboSense 2025 placement winner [R28](#r28-gblobs-for-sensor-placement); local point features generalize better [R26](#r26-lidar-domain-generalization-study); beam re-sampling [R36](#r36-dts-random-beam-re-sampling) | measured real-to-real; the twin is the same intersection as the test, so absolute position is partly legitimate signal |
| Sparse transformers (S6) | state of the art on Waymo and nuScenes [R31](#r31-dsvt), [R32](#r32-lion), [R33](#r33-hednet-and-safdnet) | the only evidence in this challenge is negative [R20](#r20-eccv-2026-runner-up-reports); `torch_scatter` or a Mamba build needed; slow |

**S2 outcome against the evidence (2026-10-09).** The real-data benchmarks ([R24](#r24-inscope), [R42](#r42-mmdetection3d-model-comparison-secondary-source)) predicted large small-object gains for center heads; in this synthetic-to-real setting CenterPoint won only LUMPI Bicycle (realval-B 0.102 -> 0.128) and lost LUMPI Person (0.134 -> 0.038), which matches the ECCV winner's report that CenterPoint was no better than pillars here ([R19](#r19-eccv-2026-winner-reports)). The cause measured on legal validation: finer voxels detect static structures the twin lacks as walkers (1.8-2.7x more static false positives). Two predictions held: z voxels cut the V2X pedestrian BEV-3D gap (0.158 -> 0.112 on realval-B), and center heads localize better at IoU 0.7 (0.082 vs 0.058). The literature lever that matches the measured error is hard-negative insertion with occlusion-correct rendering ([R9](#r9-lidar-aug), [R10](#r10-drcpo), [R11](#r11-real3d-aug)) applied to static clutter rather than to actors. Details: [`02-STRATEGY.md` Section 8.2.1](02-STRATEGY.md#821-results-2026-10-09).

**Conclusions carried into the strategy.** Route detectors by class (small classes to center heads, vehicles stay on pillars), fix height and localization with refinement or TTA, and gate every change on realval-B, because the transfer gap, not the architecture, decided the first leaderboard results. Rule-gated self-training ([R40](#r40-st3d)) remains the strongest unexplored sim-to-real lever and stays off until the organizers answer.
