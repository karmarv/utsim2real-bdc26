# PLAN: LUMPI Track (UCF UrbanTwin Sim2Real LiDAR Challenge, IEEE BigData Cup 2026)

> Read `RESEARCH-OVERVIEW.md` for theory and literature, and `SETUP-AND-STACK.md` for the server, environment, digital-twin pipeline, and local scorer. This file is the concrete, phase-by-phase winning plan for the **LUMPI multi-perspective intersection track**, CodaBench competition 16684.
> Profile: solo, hands-on ML, `bdasl-gpu-server` (8x RTX A6000, 48 GB), development phase to Oct 30, 2026, final submissions Nov 15, 2026. Letter of intent already submitted and registered. Reuse the shared core from `SETUP-AND-STACK.md`; specialize here the Hannover site, the 5-LiDAR rig, and the 8-class set.

---

## 1. Track summary (confirmed Aug 31, 2026)

| Item | Value | Source |
|---|---|---|
| Real dataset | LUMPI, Leibniz University Hannover, Konigsworther Platz intersection | LUMPI + UrbanTwin papers |
| Sensors | Five roadside LiDARs (see 1.1) | Detection paper Table I |
| Scored classes (8) | Person, Car, Bicycle, Motorcycle, Bus, Truck, Van, Unknown | CodaBench |
| Detection range | [-40, -40, -5, 40, 40, 5] (challenge); papers trained with z [-8, 2] | CodaBench / papers |
| Provided synthetic | UT-LUMPI: ~220.3k pts/frame, ~44.2 objects/frame, 6 classes (no Person), DOI 10.7910/DVN/D9SSWD | UrbanTwin datasets paper |
| Organizer baseline | SEED (VoxelNeXt backbone), 12 epochs, Car AP 44.74 (synthetic) vs 42.70 (real) @ IoU 0.5 | Detection paper |
| Scoring | 0.60 * mAP@IoU0.5 (KITTI R40, 8 classes) + 0.40 * mean(norm CD, MMD, EMD, FPD); realism xyz-only, 10k pts, seed 1234 | CodaBench |
| Rule | Detector trained on synthetic only; no real data for training/fine-tuning; forbidden_frames.txt off-limits | CodaBench |

### 1.1 The five-LiDAR rig (exact, match each in CARLA then register)

| Unit | Channels | Upper FOV | Lower FOV | Points/sec | Max range |
|---|---|---|---|---|---|
| Hesai Pandar64 | 64 | +15.0 | -25.0 | 2.60 M | 200 m |
| Velodyne HDL-64E | 64 | +1.9 | -24.6 | 4.97 M | 120 m |
| Hesai PandarQT | 64 | +52.1 | -52.1 | 0.87 M | 20 m |
| Velodyne VLP-16 (x2) | 16 | +15.0 | -15.0 | 0.68 M | 100 m |

The provided UT-LUMPI aggregate is ~220k points/frame, consistent with registering these five into one cloud (real ~219k, synthetic ~220k).

## 2. Winning thesis for this track

LUMPI is harder than V2X-Real in three ways, each an opportunity because most of the 8-participant field will handle them poorly:

1. **Eight classes, including Person, Van, and Unknown.** mAP averages over all classes, so weak/missing classes hurt disproportionately. The provided UT data has no Person; Van and Unknown need deliberate handling. This is the biggest lever.
2. **A five-LiDAR rig.** The scored frames are a dense ~220k-point aggregate. Replicating the per-unit sensors and their registration is what makes density and geometry match, for both the detector and the realism metrics.
3. **Little public detection prior art.** LUMPI has been used more for tracking/labeling than detection, so there is no strong template circulating. A disciplined pipeline stands out.

## 3. The three recommendations (ranked, complementary)

### Recommendation 1 (primary): Multi-LiDAR twin + exact per-unit match + full 8-class generation
- **What:** Build the Hannover Konigsworther Platz twin, place five virtual LiDARs matched to the rig in 1.1 (each at its real pose), register into one ~220k-point aggregate, and generate all 8 classes, above all **Person** (pedestrians), plus **Van**, with a defined **Unknown** policy. Set object sizes to real LUMPI statistics.
- **Why:** Reproduces the organizers' geospatial-fidelity lever, matches the multi-LiDAR density both the detector and metrics depend on, and covers the classes the provided data misses.
- **Expected impact:** Large, especially from Person and correct Van handling. **Effort:** High (shared core with V2X-Real). **Risk:** Medium (registration); mitigate by submitting from provided UT-LUMPI in week 1.

### Recommendation 2 (realism multiplier): Per-unit ray-drop + aggregate density matching
- **What:** Apply per-unit ray-drop before registration, then match the aggregate's extent, ~220k point count, and radial/height density to the real reference; remove registration seams and outliers. Validate on the local proxy scorer.
- **Why:** The realism metrics compare against the dense real aggregate; matching that distribution wins the 40% and also helps detection.
- **Expected impact:** Medium-large on realism. **Effort:** Medium. **Risk:** Low with the proxy; watch for double-surfaces from registration.

### Recommendation 3 (detection multiplier): Anchor-free multi-class detector + class balance + inference stack
- **What:** **CenterPoint** (anchor-free) as primary, trained geometry-only with class-balanced sampling (CBGS), Random Object Scaling, density resampling, and heavy synthetic copy-paste for rare classes (Person, Bicycle, Motorcycle, Van). Reproduce **SEED (VoxelNeXt)** as a strong second model. Finish with TTA, a multi-seed ensemble with weighted box fusion, and per-class thresholds (critical across 8 imbalanced classes); consider a vehicle-tuned + VRU-tuned two-model split.
- **Why:** Anchor-free heads and class balancing directly address the 8-class imbalance; TTA/ensembling add robust points.
- **Expected impact:** Medium-large on the 8-class mean (rare classes benefit most). **Effort:** Medium. **Risk:** Low.

## 4. Phase-by-phase plan (concrete, mapped to the calendar)

### Phase 0: Setup, reproduce baseline, close the loop (week 1)

Follow `SETUP-AND-STACK.md` Sections 3-8, then:

```bash
# 1. Get UT-LUMPI (Harvard Dataverse DOI 10.7910/DVN/D9SSWD) -> convert to OpenPCDet (8 classes)
# 2. Reproduce a baseline. SEED is the organizer model; CenterPoint is faster to iterate.
cd OpenPCDet/tools
CUDA_VISIBLE_DEVICES=0,1,2,3 bash scripts/dist_train.sh 4 \
  --cfg_file cfgs/custom_models/centerpoint_lumpi.yaml --sync_bn --extra_tag lumpi_cp_base
# 3. Inference on the 50 real test frames -> package -> first submission
```

Illustrative dataset config (note the challenge z-range differs from the papers):

```yaml
# cfgs/dataset_configs/lumpi_dataset.yaml
DATASET: 'CustomDataset'
POINT_CLOUD_RANGE: [-40, -40, -5, 40, 40, 5]     # challenge range; ablate against paper's [-8,2]
CLASS_NAMES: ['Person','Car','Bicycle','Motorcycle','Bus','Truck','Van','Unknown']
DATA_PROCESSOR:
  - NAME: mask_points_and_boxes_outside_range
    REMOVE_OUTSIDE_BOXES: True
  - NAME: transform_points_to_voxels
    VOXEL_SIZE: [0.1, 0.1, 0.125]                  # (5-(-5))/0.125 = 80 z-voxels; tune
POINT_FEATURE_ENCODING:
  used_feature_list: ['x', 'y', 'z']
DATA_AUGMENTOR:
  AUG_CONFIG_LIST:
    - NAME: gt_sampling                            # SYNTHETIC objects only (rule-safe)
      SAMPLE_GROUPS: ['Person:15','Bicycle:12','Motorcycle:10','Van:10','Bus:6','Truck:6']
    - NAME: random_world_flip
    - NAME: random_world_rotation
      WORLD_ROT_ANGLE: [-0.785, 0.785]
    - NAME: random_world_scaling
      WORLD_SCALE_RANGE: [0.95, 1.05]
    - NAME: random_object_scaling
      SCALE_RANGE: [0.9, 1.1]
```

To reproduce the exact organizer SEED baseline (config anchor from the detection paper): SEED (Large) with a VoxelNeXt 5-stage 256-out-channel backbone, AdamW + OneCycle, LR 0.002, 12 epochs, range z [-8, 2], KITTI AP@0.5. Expect Car AP ~44-45.

### Phase 1: Multi-LiDAR twin + per-unit match + registration (weeks 2-3)

1. Build the Hannover twin per `SETUP-AND-STACK.md` Section 6.
2. Place five virtual LiDARs matched to the rig in 1.1, each at its real pose (estimate poses from one public LUMPI frame's ground rings).
3. **Register** the five clouds into one aggregate matching the ~220k-point profile:

```python
import open3d as o3d, numpy as np
def register_merge(clouds, extrinsics):          # extrinsics: list of 4x4 to a common frame
    merged = o3d.geometry.PointCloud()
    for pts, T in zip(clouds, extrinsics):
        pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts[:, :3]))
        pc.transform(T); merged += pc
    # optional ICP refine of noisier units to the 64-beam reference before merge
    return np.asarray(merged.points)
```

4. Export unified boxes/classes/instances from CARLA actors. Retrain the baseline on twin data; compare to provided-UT.

### Phase 2: Full 8-class generation + robust multi-class detector (weeks 3-5)

1. Generate all 8 classes with correct assets and size priors. Priority: **Person** (CARLA walkers; upgrade with MetaHuman + AMASS as the organizers plan), then **Van**, **Bicycle**, **Motorcycle**.
2. **Unknown policy:** confirm how Unknown is scored, then choose deliberately: generate diverse miscellaneous/rare road users mapped to Unknown, or, if it is lightly weighted, de-prioritize it. Do not leave it as a silent zero.
3. Train **CenterPoint** geometry-only with **class-balanced sampling** and heavy copy-paste for rare classes:

```bash
# CenterPoint + CBGS, 6-way DDP on GPU 2-7 (GPU 0-1 generating)
CUDA_VISIBLE_DEVICES=2,3,4,5,6,7 bash scripts/dist_train.sh 6 \
  --cfg_file cfgs/custom_models/centerpoint_cbgs_lumpi.yaml --sync_bn \
  --extra_tag lumpi_cp_8cls --fix_random_seed
```

4. Reproduce SEED (VoxelNeXt) as a decorrelated second model for the ensemble. Track per-class AP (watch Person, Van, Unknown), not just the mean.

### Phase 3: Realism refinement for the dense aggregate (weeks 4-6, overlaps Phase 2)

1. Per-unit ray-drop before registration; then match the aggregate extent, ~220k point count, and density histograms to the real reference.
2. Remove registration seams, double-surfaces, and outliers that inflate CD and EMD (dense clouds make EMD costly: use Sinkhorn for iteration, exact network-simplex only for final checks, per `SETUP-AND-STACK.md` Section 7).
3. Select the 50 submission frames to minimize CD/MMD/EMD/FPD while preserving diversity.

### Phase 4: Inference stack + climb (weeks 6-8)

1. TTA (yaw, mild scale, z-flip).
2. Multi-seed ensemble with weighted box fusion; consider a vehicle-tuned + VRU-tuned two-model fusion.
3. Per-class threshold tuning (especially important across 8 imbalanced classes).
4. Lock a reproducible submission pipeline.

### Phase 5: Final phase + report (Nov 1-15)

Five hidden-leaderboard submissions spent deliberately; draft the 4-8 page report from the ablation table, targeting the top-3 paper invitation.

## 5. Experiments and ablations (log the combined score for each)

| # | Factor | Compare | Hypothesis |
|---|---|---|---|
| E1 | Data source | provided UT-LUMPI vs your multi-LiDAR twin | twin matches/beats |
| E2 | Sensor fidelity | generic vs exact 5-unit match + registration | improves detection + realism |
| E3 | Classes | 6-class provided vs full 8-class incl. Person + Unknown policy | biggest mAP gain from VRUs |
| E4 | Object sizes | CARLA defaults vs real class-size-matched | improves AP, esp. Van |
| E5 | Ray-drop/density | none vs per-unit ray-drop + aggregate match | large realism gain |
| E6 | Detector | CenterPoint+CBGS vs SEED(VoxelNeXt) vs SECOND | anchor-free + CBGS wins on 8 classes |
| E7 | Range | challenge [-5,5] vs paper [-8,2] | pick the higher combined score |
| E8 | DG aug | none vs ROS + density resampling (+ GBlobs) | improves transfer |
| E9 | Inference | single vs TTA vs TTA+ensemble+per-class thresholds | monotonic gains |

## 6. Track-specific gotchas

- **Multi-LiDAR representation:** confirm whether the scored frames are a single aggregate or per-unit; the ~220k profile says aggregate. Match exactly.
- **Heterogeneous beams:** the rig spans 16-64 layers with very different vertical FOVs (the PandarQT is +/-52 deg); a single averaged sensor cannot reproduce the aggregate density.
- **"Unknown" class:** not a natural detector class; confirm scoring and adopt an explicit policy.
- **Van vs Car vs Truck:** distinct classes with overlapping geometry; correct assets and size priors or you lose Van AP.
- **Coordinate frame:** LUMPI uses a georeferenced world/intersection frame, not an ego frame; keep generation, training, and the 50 test frames consistent.
- **z-range mismatch:** the challenge uses [-5,5], the papers used [-8,2]; ablate and use the challenge value for scoring.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Multi-LiDAR registration is fiddly | Start from provided aggregated UT-LUMPI; add registration incrementally; validate density vs real |
| Unknown class ill-defined | Confirm scoring; adopt a clear generate-and-map or de-prioritize policy; document it |
| 8-class imbalance sinks mean AP | CBGS, copy-paste for rare classes, per-class thresholds, possibly a two-model split |
| Person/VRU realism | Better assets, MetaHuman+AMASS, oversampling; imperfect beats zero |
| Dense-cloud EMD/MMD cost | Sinkhorn for iteration, exact only for final; consistent subsampling |

## 8. Milestone checklist

- [ ] `SETUP-AND-STACK.md` stack stood up; UT-LUMPI converted (8 classes); baseline reproduced; first submission made
- [ ] Local scorer matches leaderboard
- [ ] Multi-LiDAR twin + 5-unit match + registration to ~220k aggregate
- [ ] All 8 classes; Person included; Van correct; Unknown policy defined
- [ ] CenterPoint+CBGS and SEED(VoxelNeXt) trained geometry-only
- [ ] Per-unit ray-drop + density match; 50 realism frames selected on the proxy
- [ ] TTA + ensemble + per-class thresholds (consider vehicle/VRU split)
- [ ] Ablation table E1-E9 complete; report drafted

## 9. Quick reference

- CodaBench (LUMPI, IEEE BigData): https://www.codabench.org/competitions/16684/
- Provided synthetic data: Harvard Dataverse DOI 10.7910/DVN/D9SSWD (dataverse.harvard.edu/dataverse/ucf-ut)
- LUMPI dataset: https://data.uni-hannover.de/dataset/lumpi ; paper Busch et al., IEEE IV 2022, DOI 10.1109/IV51971.2022.9827157
- UrbanTwin papers: arXiv:2509.02903, arXiv:2509.02904, OJ-ITS 2026 (DOI 10.1109/OJITS.2026.3655581); PDFs in `reference/papers/`
- Method references: `RESEARCH-OVERVIEW.md` Section 12; stack and configs: `SETUP-AND-STACK.md`

> Confirm from the starting kit once: `config.json` normalization endpoints, the exact submission folder structure, and how Unknown is scored. All track facts above are confirmed from CodaBench and the papers.

