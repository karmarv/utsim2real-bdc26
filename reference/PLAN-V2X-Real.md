# PLAN: V2X-Real Track (UCF UrbanTwin Sim2Real LiDAR Challenge, IEEE BigData Cup 2026)

> Read `RESEARCH-OVERVIEW.md` for theory and literature, and `SETUP-AND-STACK.md` for the server, environment, digital-twin pipeline, and local scorer. This file is the concrete, phase-by-phase winning plan for the **V2X-Real infrastructure-centric track**, CodaBench competition 16685.
> Profile: solo, hands-on ML, `bdasl-gpu-server` (8x RTX A6000, 48 GB), development phase to Oct 30, 2026, final submissions Nov 15, 2026. Letter of intent already submitted and registered.

---

## 1. Track summary (confirmed Aug 31, 2026)

| Item | Value | Source |
|---|---|---|
| Real dataset | V2X-Real, UCLA Mobility Lab, infrastructure-centric subset (V2X-Real-IC) | CodaBench + V2X-Real paper |
| Site | SE corner, Westwood Plaza x Charles E. Young Dr South, UCLA campus, Los Angeles | UrbanTwin datasets paper |
| Ego sensor | Ouster OS1-128 roadside unit (an OS1-64 is also present) | V2X-Real paper |
| Scored classes (3) | vehicle, pedestrian, truck | CodaBench |
| Detection range | [-40, -40, -8, 40, 40, 2] | CodaBench |
| Provided synthetic | UT-V2X-Real-IC: ~53.6k pts/frame, ~13.9 objects/frame, 6 classes (no pedestrians), DOI 10.7910/DVN/N6N4UR | UrbanTwin datasets paper |
| Organizer baseline | SECOND, 56 epochs on 8,000 synthetic frames, Car AP = 63.18 @ 3D IoU 0.5 (no real data) | UrbanTwin datasets paper |
| Scoring | 0.60 * mAP@IoU0.5 (KITTI R40, 3 classes) + 0.40 * mean(norm CD, MMD, EMD, FPD); realism xyz-only, 10k pts, seed 1234 | CodaBench |
| Rule | Detector trained on synthetic only; no real data for training or fine-tuning; forbidden_frames.txt off-limits | CodaBench |

## 2. Winning thesis for this track

The organizers' SECOD reaches 63.18 Car AP with zero real data. That is a **single-class Car** number; the leaderboard scores **mAP over vehicle, pedestrian, truck**. Your margin comes from three moves, in priority order:

1. **Cover all three classes, above all pedestrians.** The provided UT data has no pedestrians and folds vehicles into six generic classes. On a 3-class mAP a missing pedestrian class is a hard zero. The organizers themselves flag pedestrians as future work (MetaHuman + AMASS); you can preempt them.
2. **Engineer the 40% realism term** (ray-drop + density matching to the Ouster profile), which they validated on different metrics and which most entrants will ignore.
3. **Beat SECOND with a stronger detector and the full inference stack** (Voxel R-CNN or CenterPoint, TTA, multi-seed ensemble, per-class thresholds).

You are solo and also entering LUMPI, so build the shared core in `SETUP-AND-STACK.md` once and specialize here only the site, the Ouster sensor, and the 3-class set.

## 3. The three recommendations (ranked, complementary)

### Recommendation 1 (primary): Digital-twin fidelity + exact Ouster match + full 3-class generation
- **What:** Reproduce the UrbanTwin V2X-Real-IC twin (UCLA Westwood x Charles Young site), place an OS1-128-matched virtual LiDAR at the real infrastructure pose, and add **pedestrian** and distinct **truck** actors so all three scored classes are well represented. Set object dimensions to the real V2X-Real class-size statistics.
- **Why:** The organizers' proven lever (geospatial fidelity + sensor match) plus the class gap they left open. Moves detection and realism together.
- **Expected impact:** Large. Matches or beats 63.18 on vehicles and adds the pedestrian class the field will mostly miss.
- **Effort:** High (main build, shared with LUMPI). **Risk:** Medium; mitigate by submitting from provided UT data in week 1 while the twin is built.

### Recommendation 2 (realism multiplier): Ouster ray-drop + density matching for the 40%
- **What:** A refinement stage that matches the Ouster point distribution: calibrate ray-drop so per-range and per-height density histograms match the real profile, match ~54k points/frame and the exact [-40,-40,-8,40,40,2] crop, remove outliers. Validate on the local proxy scorer.
- **Why:** CD/MMD/EMD/FPD are geometric; matching the sensor's point distribution is the highest-leverage, lowest-risk way to win the 40%, and realistic sparsity also helps detection.
- **Expected impact:** Medium-large on realism; small positive on detection. **Effort:** Medium. **Risk:** Low with the proxy scorer.

### Recommendation 3 (detection multiplier): Robust detector + DG augmentation + inference stack
- **What:** Train **Voxel R-CNN** (accuracy) and **CenterPoint** (anchor-free) geometry-only, with Random Object Scaling, DTS-style density resampling, and synthetic copy-paste for pedestrians/trucks. Optionally a GBlobs front-end. Finish with TTA (yaw/scale/z-flip), a multi-seed + multi-arch ensemble with weighted box fusion, and per-class thresholds.
- **Why:** The repeatable challenge-winning pattern; several mAP points at near-zero risk.
- **Expected impact:** Medium. **Effort:** Medium (config + inference plumbing). **Risk:** Low.

## 4. Phase-by-phase plan (concrete, mapped to the calendar)

Development phase closes **Oct 30, 2026, 7 PM CDT**; final phase Nov 1-15. Timeline below assumes a start in early September.

### Phase 0: Setup, reproduce baseline, close the loop (week 1)

Goal: a legal submission on the leaderboard and a local scorer that matches it. Follow `SETUP-AND-STACK.md` Sections 3-8, then:

```bash
# 1. Get UT-V2X-Real-IC (Harvard Dataverse DOI 10.7910/DVN/N6N4UR) -> convert to OpenPCDet
# 2. Reproduce SECOND baseline (organizer used 56 epochs, 8,000 frames)
cd OpenPCDet/tools
CUDA_VISIBLE_DEVICES=0,1,2,3 bash scripts/dist_train.sh 4 \
  --cfg_file cfgs/custom_models/second_v2x.yaml --extra_tag v2x_second_base
# 3. Inference on the 50 real test frames -> package -> first submission
```

Illustrative dataset config (verify ranges against `config.json`):

```yaml
# cfgs/dataset_configs/v2x_dataset.yaml
DATASET: 'CustomDataset'
POINT_CLOUD_RANGE: [-40, -40, -8, 40, 40, 2]
CLASS_NAMES: ['vehicle', 'pedestrian', 'truck']
DATA_PROCESSOR:
  - NAME: mask_points_and_boxes_outside_range
    REMOVE_OUTSIDE_BOXES: True
  - NAME: transform_points_to_voxels
    VOXEL_SIZE: [0.1, 0.1, 0.125]     # (2 - (-8))/0.125 = 80 z-voxels; tune
POINT_FEATURE_ENCODING:
  used_feature_list: ['x', 'y', 'z']  # geometry-only default (robust; intensity optional)
DATA_AUGMENTOR:
  AUG_CONFIG_LIST:
    - NAME: gt_sampling                # copy-paste; SYNTHETIC objects only (rule-safe)
      SAMPLE_GROUPS: ['vehicle:12','pedestrian:12','truck:8']
    - NAME: random_world_flip
    - NAME: random_world_rotation
      WORLD_ROT_ANGLE: [-0.785, 0.785]
    - NAME: random_world_scaling
      WORLD_SCALE_RANGE: [0.95, 1.05]
    - NAME: random_object_scaling      # ROS; unimodal size match to real
      SCALE_RANGE: [0.9, 1.1]
```

Exit criterion: local combined score approximates the leaderboard within a small margin.

### Phase 1: V2X-Real-IC digital twin + Ouster match (weeks 2-3)

1. Build the UCLA Westwood x Charles Young twin per `SETUP-AND-STACK.md` Section 6 (Cesium mesh -> Blender cleanup -> RoadRunner roads -> CARLA).
2. Configure the OS1-128 virtual sensor at the real infrastructure pose (estimate pose from one public V2X-Real-IC frame's ground rings). Match beam count, vertical FOV, azimuth resolution, range, point rate.
3. Generate on GPU 0-1 in background while GPU 2-7 keep training the baseline.
4. Retrain SECOND on twin data; compare to the provided-UT result. Expect the twin to match or improve.

### Phase 2: All three classes + robust detectors (weeks 3-5)

1. **Pedestrians (highest-value):** spawn CARLA walker actors; if default humans look too clean for LiDAR, improve with better human assets or the organizers' own planned route (Unreal MetaHuman + AMASS motion). Even imperfect pedestrians beat a zero on the class-averaged mAP. Oversample via copy-paste.
2. Map raw V2X-Real categories to the 3 super-classes exactly (car/van/bus/box-truck/scooter/motorcycle/bicycle into vehicle vs truck vs pedestrian) and fix size priors per class.
3. Train **Voxel R-CNN** and **CenterPoint** geometry-only:

```bash
# CenterPoint (anchor-free), 4-way DDP on GPU 2-5
CUDA_VISIBLE_DEVICES=2,3,4,5 bash scripts/dist_train.sh 4 \
  --cfg_file cfgs/custom_models/centerpoint_v2x.yaml --sync_bn \
  --extra_tag v2x_cp_3cls --fix_random_seed
# Voxel R-CNN on GPU 6-7 in parallel
CUDA_VISIBLE_DEVICES=6,7 bash scripts/dist_train.sh 2 \
  --cfg_file cfgs/custom_models/voxelrcnn_v2x.yaml --sync_bn --extra_tag v2x_vrcnn_3cls
```

4. Add DTS-style density resampling and (optionally) a GBlobs front-end. Track per-class AP on a synthetic val split.

### Phase 3: Realism refinement for the 40% (weeks 4-6, overlaps Phase 2)

1. Calibrate ray-drop and `noise_stddev` so synthetic density matches the real Ouster profile (per `SETUP-AND-STACK.md` Section 6.2); match ~54k pts/frame and the exact crop.
2. Select the 50 submission frames to minimize CD/MMD/EMD/FPD on the proxy scorer while preserving frame-to-frame diversity (protect FPD covariance and MMD).
3. Confirm the realism term improved without hurting detection.

### Phase 4: Inference stack + leaderboard climb (weeks 6-8)

1. TTA at inference (yaw rotations, mild scaling, z-flip) on the 50 real frames.
2. Multi-seed + multi-arch ensemble (Voxel R-CNN + CenterPoint) fused with weighted box fusion.
3. Per-class score/NMS threshold tuning on synthetic val; confirm the leaderboard delta.
4. Lock a scripted, reproducible submission bundle (fixed seeds, versioned configs).

### Phase 5: Final phase + report (Nov 1-15)

Five hidden-leaderboard submissions: spend them on your best single model, best ensemble, and one or two controlled variants. Draft the 4-8 page report from the ablation table (Section 5) as you go, targeting the top-3 paper invitation.

## 5. Experiments and ablations (log the combined score for each)

| # | Factor | Compare | Hypothesis |
|---|---|---|---|
| E1 | Data source | provided UT vs your twin | twin matches/beats |
| E2 | Sensor fidelity | generic vs exact OS1-128 + real pose | improves detection + realism |
| E3 | Classes | 6-class provided vs full 3-class incl. pedestrians | pedestrian coverage is the biggest mAP lever |
| E4 | Object sizes | CARLA defaults vs real class-size-matched | improves AP at IoU 0.5 |
| E5 | Ray-drop/density | none vs calibrated | large realism gain, small detection gain |
| E6 | Detector | SECOND vs Voxel R-CNN vs CenterPoint | anchor-free/two-stage beats SECOND |
| E7 | DG aug | none vs ROS + density resampling (+ GBlobs) | improves real-test transfer |
| E8 | Inference | single vs TTA vs TTA+ensemble+per-class thresholds | monotonic gains |
| E9 | Intensity | geometry-only vs xyzi | test whether intensity helps or hurts transfer |

## 6. Track-specific gotchas

- **IC ego frame:** detector operates in the roadside unit frame; keep coordinates consistent across generation, training, and the 50 real test frames.
- **Ouster geometry:** match the OS1-128 vertical beam-angle table, not just "128 beams"; there is a near-field blind zone. Confirm from the datasheet and a real frame.
- **Class collapse:** the 3 classes are super-classes; a wrong raw-to-super mapping silently tanks AP.
- **Range crop:** use exactly [-40,-40,-8,40,40,2]; the original V2X-Real paper used a wider range.
- **Sparse far objects:** ensure realistic sparsity at range so the detector does not overfit dense clean synthetic objects.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Twin build eats the calendar | Submit from provided UT data week 1; build twin in parallel on GPU 0-1 |
| Pedestrian synthesis unrealistic | Better assets or MetaHuman+AMASS; oversample; imperfect beats zero |
| Realism refinement hurts detection | Keep generation and refinement separate; validate both terms before each submission |
| Overfitting the public leaderboard | Trust the local scorer; reserve final-phase submissions for vetted models |

## 8. Milestone checklist

- [ ] `SETUP-AND-STACK.md` stack stood up; UT-V2X-Real-IC converted; SECOND ~63 reproduced; first submission made
- [ ] Local scorer matches leaderboard
- [ ] UCLA-site twin + OS1-128-matched sensor generating labeled frames
- [ ] All 3 classes incl. pedestrians; sizes matched to real stats
- [ ] Voxel R-CNN + CenterPoint trained geometry-only with DG aug
- [ ] Ray-drop/density calibrated; 50 realism frames selected on the proxy
- [ ] TTA + ensemble + per-class thresholds
- [ ] Ablation table E1-E9 complete; report drafted

## 9. Quick reference

- CodaBench (V2X-Real, IEEE BigData): https://www.codabench.org/competitions/16685/
- Provided synthetic data: Harvard Dataverse DOI 10.7910/DVN/N6N4UR (dataverse.harvard.edu/dataverse/ucf-ut)
- V2X-Real dataset/code: https://github.com/ucla-mobility/V2X-Real ; paper arXiv:2403.16034
- UrbanTwin papers: arXiv:2509.02903, arXiv:2509.02904, and OJ-ITS 2026 (DOI 10.1109/OJITS.2026.3655581); PDFs in `reference/papers/`
- Method references: see `RESEARCH-OVERVIEW.md` Section 12; stack and configs: `SETUP-AND-STACK.md`

> Confirm from the starting kit once: `config.json` normalization endpoints and the exact submission folder structure. All track facts above are confirmed from CodaBench and the papers.

