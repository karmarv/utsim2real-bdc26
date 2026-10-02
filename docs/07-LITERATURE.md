# 07. Literature and evidence (verified 2026-09-30)

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
| Statistical Normalization ("Train in Germany, Test in the USA") | 2005.08139, CVPR 2020 | nuScenes->KITTI Car AP3D 19.0 to 54.8 by matching object sizes | Size synthetic objects and labels to real train-split statistics |
| PCGen | 2210.08738 | Pedestrians 6.56 to **54.31** AP@0.5 just by loosening boxes to the annotator convention; per-ray drop MLP +1.4 | Fit label conventions per class (M7); simple learned ray-drop (M6) |
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
