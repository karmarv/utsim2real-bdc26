# Track 2 models: V2X-Real (`model-v2x-track/`)

> Modeling for Track 2 (CodaBench 16685): the approaches we considered, the selected model and why, and its full lifecycle (preparation, training, validation, test inference, ablations, evaluation, submission). Data, the sensor and the generator are in [`data-v2x-track/README.md`](../data-v2x-track/README.md); the project-wide developer guide is the [root README](../README.md).

## 0. At a glance

| | |
|---|---|
| Selected model | [`routed-g9`](routed-g9) (S7 step 1, the entry): the S6 variant b portfolio with boxes that hold fewer points than the real labels' visibility cut ranked last (pedestrian k = 6, vehicle k = 5; Section 7.12); before: [`routed-g8b`](routed-g8b) (S6 variant b) |
| Real validation (official metric, tuned) | **realval-A mAP 0.734**, realval-B 0.721 (S7); S6b 0.727 / 0.712; R5 0.714 / 0.710; R3 0.701 / 0.703; S5 0.694 / 0.699; S1 0.572 / 0.520 |
| Local combined estimate | 0.992 (B, unclipped) for S7; leaderboard 0.8982 (Section 9); ECCV winner 0.746 |
| CodaBench (current entry) | **1001919: combined 0.8982** (mAP 0.6124, R 0.9332), S7 step 1 ([`routed-g9`](routed-g9)), rank 1 of 23 on 2026-10-19 (Section 9) |
| CodaBench (previous) | 995877: 0.8931 (S6 variant b); 990255: 0.8852 (R5); 986496: 0.8789 (R3); 978945: 0.8730 (S5); 975938: 0.8485 (S4); 974400: 0.8381 (S3); 972563: 0.7855 (S1+C1); 965633: 0.7665 (S1) |
| Submitted zip | current entry: [`routed-g9/submissions/2026-10-18_s7/v2x_s7_submission.zip`](routed-g9/submissions/2026-10-18_s7/v2x_s7_submission.zip) (its members are the release-6.0 weights, [`releases/6.0/weights.json`](../releases/6.0/weights.json)); S6b: [`v2x_s6b_submission.zip`](routed-g8b/submissions/2026-10-16_s6b/v2x_s6b_submission.zip) (tag 6.0); R5: [`v2x_r5_submission.zip`](routed-g7/submissions/2026-10-14_r5/v2x_r5_submission.zip) (tag 5.2); R3: [`v2x_r3_submission.zip`](routed-g6/submissions/2026-10-12_r3/v2x_r3_submission.zip) (tag 5.1) |
| Realism of the submitted frames | **R = 0.933 on the server** (R5 frames from `g1-v5`: background density prior, 31% nulls; 0.937 on held-out legal proxies); R3 frames 0.927 (`g1-v4`); S1-S5 0.920 (`g1-v3`) |
| Submit | Section 6.7 |
| Strategy | S1, S1+C1, S3, S4, S5, R3, R5, S6 (variant b) and **S7 step 1 submitted**; **S7 step 1 is the entry** (Section 7.12: pedestrian +0.015 on the leaderboard); S7 step 2 (visibility-matched training labels) running; S2 done without a new V2X version (Section 7.5); next: root README Section 8, [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#811-s7-visibility-rule-v2x-2026-10-18) Section 8.11 |
| Experiment log | [`registry.csv`](registry.csv) |

## 1. Folder conventions and models

Same conventions as Track 1 ([`model-lumpi-track/README.md`](../model-lumpi-track/README.md) Section 1): one folder per model with `model.yaml`, `README.md`, `train/`, `validation/`, `test/`, `submissions/`; experiment log `registry.csv`; new models with `python common/tools/new_model.py v2x <name> --from <existing>`.

| Model | Data | Role | Status |
|---|---|---|---|
| [`pointpillars-ut`](pointpillars-ut) | `pcdet/ut-v1` (UT only; riders are the only pedestrians) | baseline; routed member for truck | trained 40 epochs, tuned |
| [`pointpillars-g1`](pointpillars-g1) | `pcdet/g1-v1` (walkers v1, free placement, gain 1.5) | first G1 model | trained 40 epochs, tuned |
| [`pointpillars-g1v2`](pointpillars-g1v2) | `pcdet/g1-v2` (walker v2 body) | routed member for vehicle | trained 40 epochs, tuned |
| [`pointpillars-g1v3`](pointpillars-g1v3) | `pcdet/g1-v3` (walkers calibrated on legal real walkers, FOV-masked UT) | routed member for pedestrian | trained 40 epochs, tuned |
| [`routed-g1`](routed-g1) | members above | S1 | submitted (965633, 0.7665) |
| [`routed-g1z`](routed-g1z) | `routed-g1` + range-dependent z calibration (C1) | S1+C1 | submitted (972563, 0.7855; Section 7.4) |
| [`centerpoint-g1v3`](centerpoint-g1v3) | `pcdet/g1-v3` | S2 member: CenterPoint, stride 8 | trained 40 epochs (label fix), tuned; no class won (Section 7.5) |
| [`centerpoint-s4-g1v3`](centerpoint-s4-g1v3) | `pcdet/g1-v3` | S2 variant: CenterPoint, stride 4 | trained 40 epochs, tuned; no class won |
| [`routed-g2`](routed-g2) | members of `routed-g1z` + `cp`, `cp4` | S2 candidate | route and calibration unchanged from S1+C1: no new version |
| [`routed-g3`](routed-g3) | `routed-g2` members and their TTA variants (`<member>_tta`) | S3 | submitted (974400, 0.8381; Section 7.6) |
| [`voxelrcnn-g1v3`](voxelrcnn-g1v3) | `pcdet/g1-v3` | S4 member: Voxel R-CNN (CenterPoint stage 1, voxel RoI pooling) | trained 40 epochs, per-class score blend, tuned plain and TTA (Section 7.7) |
| [`pvrcnnpp-g1v3`](pvrcnnpp-g1v3) | `pcdet/g1-v3` | S4 member: PV-RCNN++ (CenterPoint stage 1, keypoint RoI pooling) | trained 40 epochs, per-class score blend, tuned plain and TTA (Section 7.7) |
| [`routed-g4`](routed-g4) | `routed-g3` members + `vr`, `pv` and their TTA variants | S4 | submitted (975938, 0.8485; Section 7.7) |
| [`voxelrcnn-gblobs-g1v3`](voxelrcnn-gblobs-g1v3) | `pcdet/g1-v3` | S5 run a: Voxel R-CNN with GBlobs inputs (cell covariance) | trained, tuned plain and TTA; below its parent alone, used in the vehicle fusion (Section 7.8) |
| [`voxelrcnn-ros-g1v3`](voxelrcnn-ros-g1v3) | `pcdet/g1-v3` | S5 run b: Voxel R-CNN with class-wise object scaling | trained, tuned plain and TTA; in the pedestrian and truck fusions (Section 7.8) |
| [`pvrcnnpp-ros-g1v3`](pvrcnnpp-ros-g1v3) | `pcdet/g1-v3` | S5 extension: PV-RCNN++ with object scaling | trained, tuned plain and TTA; in the vehicle and truck fusions |
| [`pointpillars-ros-g1v3`](pointpillars-ros-g1v3) | `pcdet/g1-v3` | S5 extension: PointPillars g1v3 with object scaling | trained, tuned; below its parent (one truck anchor) |
| [`routed-g5`](routed-g5) | `routed-g4` members + the four S5 runs (plain and TTA) | S5 | submitted (978945, 0.8730, the entry until R3; Section 7.8) |
| [`pointpillars-g1v4`](pointpillars-g1v4) | `pcdet/g1-v4` (engine G2-lite) | R3 wave 0: `pointpillars-g1v3` on the new corpus, truck anchors at the new label sizes | trained, tuned plain and TTA; every class above its parent (Section 7.9) |
| [`voxelrcnn-ros-g1v4`](voxelrcnn-ros-g1v4) | `pcdet/g1-v4` | R3: `voxelrcnn-ros-g1v3` on the new corpus (ROS capped at real sizes; the uncapped run is kept as `run0_rostail`) | trained, tuned plain and TTA; pedestrian fusion |
| [`pvrcnnpp-ros-g1v4`](pvrcnnpp-ros-g1v4) | `pcdet/g1-v4` | R3: `pvrcnnpp-ros-g1v3` on the new corpus (ROS capped) | trained, tuned plain and TTA |
| [`routed-g6`](routed-g6) | `routed-g5` (incumbent) + R3 members (plain and TTA) | R3 | submitted (986496, 0.8789; Section 7.9) |
| [`voxelrcnn-ros-g1v4-s2`](voxelrcnn-ros-g1v4-s2), [`pvrcnnpp-ros-g1v4-s2`](pvrcnnpp-ros-g1v4-s2) | `pcdet/g1-v4` | R5: seed 1666 of the R3 two-stage members | trained, tuned plain and TTA; vehicle fusion (Section 7.10) |
| [`pointpillars-g1v5`](pointpillars-g1v5), [`voxelrcnn-ros-g1v5`](voxelrcnn-ros-g1v5), [`pvrcnnpp-ros-g1v5`](pvrcnnpp-ros-g1v5) | `pcdet/g1-v5` (G2-lite with the first V2X density prior) | R5: the R3 member set on the R5 corpus | trained, tuned plain and TTA; truck `pp5_tta` |
| [`routed-g7`](routed-g7) | `routed-g6` (incumbent) + the R5 members | R5 | submitted (990255, 0.8852; Section 7.10) |
| [`voxelrcnn-ros-g1v5-s2`](voxelrcnn-ros-g1v5-s2), [`-s3`](voxelrcnn-ros-g1v5-s3), [`pvrcnnpp-ros-g1v5-s2`](pvrcnnpp-ros-g1v5-s2), [`-s3`](pvrcnnpp-ros-g1v5-s3) | `pcdet/g1-v5` | S6: seeds 1666 and 2666 | trained, tuned plain and TTA (Section 7.11) |
| [`bag-voxelrcnn-ros-g1v5`](bag-voxelrcnn-ros-g1v5), [`bag-pvrcnnpp-ros-g1v5`](bag-pvrcnnpp-ros-g1v5), [`bag-voxelrcnn-ros-g1v4`](bag-voxelrcnn-ros-g1v4), [`bag-pvrcnnpp-ros-g1v4`](bag-pvrcnnpp-ros-g1v4) | seeds 666-2666 (`g1-v5`); 666, 1666 (`g1-v4`) | S6 seed bags (weighted box fusion of the seeds' tuned predictions) | at or above the best seed on A and B; vehicle and truck fusions of `routed-g8b` |
| [`routed-g8`](routed-g8) | `routed-g7` (incumbent) + the S6 seeds and bags | S6 (gated) | equal to R5 (no class passed the class gate): not uploaded |
| [`routed-g8b`](routed-g8b) | `routed-g8` with vehicle and truck by the pooled rule | S6 variant b | submitted (995877, 0.8931, rank 1 of 23; Section 7.11), the entry until S7 |
| [`routed-g9`](routed-g9) | `routed-g8b` + the S7 sparse-box demotion (`sparse_demotion: {vehicle: 5, pedestrian: 6}`) | **selected** (S7 step 1) | submitted (1001919, **0.8982**, rank 1 of 23; Section 7.12) |
| [`voxelrcnn-ros-g1v5m`](voxelrcnn-ros-g1v5m), [`-s2`](voxelrcnn-ros-g1v5m-s2), [`-s3`](voxelrcnn-ros-g1v5m-s3), [`pvrcnnpp-ros-g1v5m`](pvrcnnpp-ros-g1v5m), [`-s2`](pvrcnnpp-ros-g1v5m-s2), [`-s3`](pvrcnnpp-ros-g1v5m-s3) | `pcdet/g1-v5m` (the `g1-v5` frames, labels with the S7 visibility rule) | S7 step 2: the `g1-v5` two-stage configs, seeds 666 / 1666 / 2666 | done (S7 step 2; members of `routed-g10`) |
| [`bag-voxelrcnn-ros-g1v5m`](bag-voxelrcnn-ros-g1v5m), [`bag-pvrcnnpp-ros-g1v5m`](bag-pvrcnnpp-ros-g1v5m) | the three seeds of each | S7 step 2 seed bags; compared with the `g1-v5` bags of the same seeds | done: pedestrian +0.001 to +0.008 pooled, vehicle and truck mixed ([record](../docs/decisions/2026-10-18-s7-visibility-rule.md)) |
| [`routed-g10`](routed-g10) | `routed-g9` + the two S7 bags | S7 step 2 portfolio | not uploaded: A 0.738 / B 0.722, projection +0.0014 (below +0.003) |
| [`voxelrcnn-ros-g1v5d2`](voxelrcnn-ros-g1v5d2), [`-d3`](voxelrcnn-ros-g1v5d3), [`pvrcnnpp-ros-g1v5d2`](pvrcnnpp-ros-g1v5d2), [`-d3`](pvrcnnpp-ros-g1v5d3) | `pcdet/g1-v5d2`, `g1-v5d3` (fresh `g1-v5` generator draws, seeds 2234 / 3234); training seeds 4666 / 5666 | S7.4 draw members | done: inside the seeds' spread (TTA A 0.669-0.682) |
| [`bag-voxelrcnn-ros-g1v5x`](bag-voxelrcnn-ros-g1v5x), [`bag-pvrcnnpp-ros-g1v5x`](bag-pvrcnnpp-ros-g1v5x) | the three seeds + both draws (5 each) | S7.4 extended bags | done: TTA +0.0017 / +0.0030 and +0.0037 / +0.0031 over the 3-seed bags |
| [`routed-g11`](routed-g11), [`routed-g12`](routed-g12) | `routed-g9` + the draw runs and extended bags; `routed-g12` = the S7.6 bag swap and pooled budget | S7.4 and S7.6 portfolios | equal to the entry (no class passed; [record](../docs/decisions/2026-10-26-s7-final-revisions.md)); `routed-g12` packaged as [`v2x_s7s_submission.zip`](routed-g12/submissions/2026-10-27_s7s/v2x_s7s_submission.zip) on the entrant's request: frames byte-identical to 1001919, predictions equal, kit 153 s; expected 0.8982 |

## 2. Modeling approaches considered

Track-specific constraints: one sensor (OS1-64), 35k valid points per frame plus 31% nulls; a sloped campus (box bottoms from -1 to -7 m in the sensor frame); **pedestrian is 62% of the test objects** and mixes walkers (0.71 x 0.72 x 1.73 m) with riders (about 1.8 m long); trucks are large (median 8.2 m).

| Approach | Pros here | Cons here | Verdict |
|---|---|---|---|
| **PointPillars** with multi-mode anchors | fast (1 h per run on 4 GPUs); one pillar spans the whole z range, so the slope does not need a z prior; the ECCV winner's bimodal vehicle and 3-mode truck anchors took combined from 0.515 to 0.626 | coarse for small objects | **selected base detector** |
| SECOND / Voxel R-CNN | finer z; better on roadside pedestrians in the literature | the slope (18 m vertical spread) makes voxel heights and anchors harder | Voxel R-CNN is the lighter option of strategy S4 ([`docs/02` 8.4](../docs/02-STRATEGY.md#84-s4-two-stage-refinement)) |
| CenterPoint | strong small-object head | heatmap z priors suffer from the slope; the ECCV winner found it no better than pillars here | **strategy S2 (next)**: pedestrian specialist ([`docs/02` 8.2](../docs/02-STRATEGY.md#82-s2-center-routed-small-objects)) |
| DSVT / transformers | the ECCV runner-up used DSVT experts per class | heavy; needs more varied synthetic data; scored below S1 here | optional research track of S6 (S6 re-planned on 2026-10-15 as seed bags, [`docs/02` 8.6](../docs/02-STRATEGY.md#86-s6-variance-controlled-final-portfolio-re-planned-2026-10-15)) |
| Ground-plane canonicalization | removes the slope (RoboSense 2025 reported +5 AP) | needs a per-frame ground fit on real frames (legal: unlabeled sensor data) | next experiment |
| Per-class routing / fusion | per-class AP is independent; walker versions differ by class | needs real validation (available since the kit) | **used** (routing in S1); fusion and TTA are strategy S3 |

**Why the selected model.** PointPillars trains in an hour, so generator iterations (walkers, FOV mask, density) are cheap, and the generator is where the pedestrian points are: UT-V2X has no walkers at all. Per-class routing then takes vehicles, pedestrians and trucks from the members that are best for each on real validation. Cons: two forward passes; routing chosen on realval-A (scene-disjoint from realval-B, which is the check); small-object precision is limited by pillar resolution.

## 3. The detector configuration

| Setting | Value |
|---|---|
| Input | xyz in `[-40, -40, -8, 40, 40, 2]`; `BDCDataset.get_lidar` strips (0,0,0) nulls |
| Pillars | 0.15625 m, 512 x 512, one pillar spans z [-8, 2], 32 points per pillar, 30,000 / 40,000 pillars (train / test) |
| Anchors (bottom -2.5 m) | vehicle 4.47 x 1.95 x 1.55; pedestrian walker 0.8 x 0.6 x 1.73 and rider 1.76 x 0.6 x 1.73; truck 4.64 x 1.96 x 2.06, 6.74 x 2.75 x 3.04, 10.27 x 3.94 x 4.25 |
| Augmentation | GT-sampling vehicle 8 / pedestrian 12 / truck 6 (min 5 points); flips x/y; rotation +/-10 deg; scaling 0.95-1.05 |
| Optimization | 40 epochs, batch 8 per GPU on 4 GPUs, adam_onecycle LR 0.003, `--fix_random_seed` |
| Post-processing | per class, selected on realval-A (Section 6.3); realism frames get 31% (0,0,0) nulls at packaging |

## 4. Engine G1 data in one paragraph

UT-V2X frames resampled to 35,000 valid points, plus 12-16 procedural walkers per frame ray-cast with the OS1-64 model; `g1-v3` places walkers at legal real walker positions with real box sizes and ground heights, masks UT points to the measured OS1-64 field of view, casts with the measured beam table and matches real walker point counts at every range (52 / 40 / 18 / 7 vs 46 / 36 / 19 / 7 points at 0-10 / 10-20 / 20-30 / 30-45 m). Details: [`data-v2x-track/README.md`](../data-v2x-track/README.md) Section 8.

## 5. Lifecycle

The lifecycle is the same as Track 1 ([`model-lumpi-track/README.md`](../model-lumpi-track/README.md) Section 5 diagram): preparation, training, real validation and tuning, routing, test inference, evaluation, submission.

## 6. Selected model lifecycle, step by step

From the repository root after `source common/env/activate.sh`.

### 6.1 Preparation
```bash
python data-v2x-track/resolve_test_ids.py                 # guard mapping (needs the kit and the raw bins)
python data-v2x-track/prepare_realval.py --stride 5       # realval-v1 + realism proxies
OMP_NUM_THREADS=1 python data-v2x-track/prepare_g1.py --name g1-v3 --workers 48 \
    --walker v2 --placement prior --walkers 16 --density-gain 2.5 --fov-mask
```

### 6.2 Training
```bash
CUDA_VISIBLE_DEVICES=4,5,6,7 bash model-v2x-track/pointpillars-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6
```
About 1 hour; checkpoints in `train/output/pcdet_model/run1/ckpt/`.

### 6.3 Validation and post-processing selection
```bash
CUDA_VISIBLE_DEVICES=4 bash model-v2x-track/pointpillars-g1v3/validation/tune_and_eval.sh \
    model-v2x-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth
```
Two-phase per-class tuning on realval-A (behaviour knobs guarded by realval-B; box-convention knobs on A), hedges, official-metric scores on A and B (`validation/results/local_scores.json`, `registry.csv`). Mechanics: [`model-lumpi-track/README.md`](../model-lumpi-track/README.md) Section 6.3.

### 6.4 Routing
```bash
python common/tools/route_predictions.py select model-v2x-track/routed-g1
```

### 6.5 Realism frames
```bash
python common/tools/select_realism_frames.py --track v2x --syn pcdet/g1-v3 --split val \
    --fit-ref pcdet/realism-proxy-1 --fit-ref pcdet/realism-proxy-2 --fit-ref pcdet/realism-proxy-3 \
    --test-ref pcdet/realism-proxy-4 --test-ref pcdet/realism-proxy-5 --out model-v2x-track/routed-g1/test/synthetic_ids.txt
```
Frames are scored with the 31% nulls the packager adds.

### 6.6 Test inference and evaluation
As Track 1 (Sections 6.5-6.6 there): every member predicts the 50 kit frames with its own `test/postprocess.yaml`; `route_predictions.py merge` combines them; official-metric detection and realism scoring locally.

### 6.7 Submission
```bash
CUDA_VISIBLE_DEVICES=4 bash model-v2x-track/routed-g1/test/make_submission.sh first
# single model: bash model-v2x-track/pointpillars-g1/test/make_submission.sh <ckpt> first
python common/tools/check_submission.py --track v2x model-v2x-track/routed-g1/submissions/<date>_first/submission.zip --official
# upload that submission.zip unchanged on CodaBench 16685; never unzip, edit or re-zip it. Then:
python common/tools/package_submission.py model-v2x-track/routed-g1 --tag first --record <codabench_id> model-v2x-track/routed-g1/submissions/<date>_first/codabench_<codabench_id>.json
```

## 7. Results and ablations

Official metric, 3D AP at IoU 0.5 (R40), mean over vehicle, pedestrian, truck; realval-A = 688 frames, realval-B = 298 frames (other scenes).

### 7.1 Models (official metric, tuned post-processing)

| Model | Training data | realval-A | realval-B | vehicle | pedestrian | truck |
|---|---|---|---|---|---|---|
| `pointpillars-ut` (baseline) | `ut-v1`: UT only (riders, no walkers) | 0.465 | 0.419 | 0.574 | 0.000 | **0.822** |
| `pointpillars-g1` | `g1-v1`: + walkers v1, free placement, gain 1.5 | 0.459 | 0.404 | 0.620 | 0.118 | 0.639 |
| `pointpillars-g1v2` | `g1-v2`: + walker v2 body | 0.527 | 0.477 | **0.627** | 0.173 | 0.781 |
| `pointpillars-g1v3` | `g1-v3`: walkers calibrated on legal real walkers, FOV mask, measured beams | 0.511 | 0.466 | 0.563 | **0.266** | 0.703 |
| **`routed-g1`** (selected) | per class from the best member | **0.572** | **0.520** | 0.627 | 0.266 | 0.822 |

realval-B per class for `routed-g1`: vehicle 0.662, pedestrian 0.226, truck 0.673. Reference points: ECCV 2026 winner on the test set, mAP 0.438 (vehicle 0.592, pedestrian 0.189, truck 0.533); live IEEE development leader mAP 0.302 (2026-10-02).

### 7.2 Ablations

| Question | Comparison | Result (realval-A) |
|---|---|---|
| Walkers at all | `pointpillars-ut` vs `pointpillars-g1` | pedestrian 0 -> 0.118 (UT riders alone never match real walkers) |
| Walker body model | `g1` (v1) vs `g1v2` (v2: deeper torso, arm swing, bags, yaw scatter) | pedestrian 0.118 -> 0.173; mAP 0.459 -> 0.527 |
| Walkers calibrated on legal real data + FOV mask | `g1v2` vs `g1v3` | pedestrian 0.173 -> 0.266 (B: 0.174 -> 0.226) |
| Training variance on classes with identical data | vehicle and truck across the four runs | truck 0.639-0.822, vehicle 0.563-0.627: per-class routing gains +0.045 over the best single model |
| Post-processing (`g1v3`) | start config -> tuned + hedges | vehicle 0.480 -> 0.563, pedestrian 0.253 -> 0.266, truck 0.566 -> 0.703 (size and z calibration dominate) |
| Realism: FOV mask and frame selection | `g1-v1` random -> `g1-v3` random -> `g1-v3` selected (held-out proxies, 31% nulls, official scorer) | R 0.901 -> 0.916 -> 0.922 (the packaged zip, with its own null draw: 0.919) |

### 7.3 Local estimate of the first submission

`routed-g1/submissions/2026-10-02_first/submission.zip`: realval-A mAP 0.572, realism R 0.919 (the kit's `local_eval.py` with 50 legal frames as the reference agrees to every printed digit) -> **combined about 0.858** (0.814 with the realval-B mAP).

### 7.4 S1 close-out diagnostics and the C1 candidate (2026-10-09)

Official metric on legal real validation, S1 `routed-g1` predictions; files in [`routed-g1/validation/results/diagnostics/`](routed-g1/validation/results/diagnostics). Summary and decisions: [`docs/02-STRATEGY.md` Section 8.1.3](../docs/02-STRATEGY.md#813-close-out-results-2026-10-09).

| Diagnostic | Finding |
|---|---|
| Test class mix vs realval-A (objects per frame) | vehicle 9.4 vs 8.1, pedestrian 19.1 vs 16.2, truck 2.5 vs 1.7 (close) |
| BEV-3D gap (mAP) | 0.103 on A, 0.146 on B; pedestrian BEV 0.426 vs 3D 0.266 (A), 0.384 vs 0.226 (B) |
| Pedestrian centre z error by range (0-10 / 10-20 / 20-30 / 30+ m) | +0.16 / +0.08 / +0.03 / -0.11 m on A; +0.16 / +0.06 / +0.04 / -0.11 m on B; heights +0.10 m |
| Vehicle and truck z error by range | vehicle +0.02 / +0.09 / +0.09 / -0.12 m; truck heights +0.35 m, lengths -0.1 m median with a 2 m spread |
| AP by range | pedestrian 0.18 / 0.36 / 0.35 / 0.15; vehicle 0.81 / 0.84 / 0.52 / 0.40; truck 0.23 / 0.33 / 0.92 / 0.53 |
| Recall by points (score >= 0.3, 3D IoU 0.5) | pedestrian 0.51 / 0.63 / 0.60 / 0.70 for 1-10 / 10-30 / 30-100 / 100+ points; vehicle 0.12 / 0.32 / 0.65 / 0.89 |
| Joint routing (A and B) | same route as S1 |

**C1, range-dependent z calibration** (`z += z0 + z_per_m * range` per class after routing, selected on A, class gate on B; [decision record](../docs/decisions/2026-10-09-s1-closeout-z-calibration.md)):

| Class | (z0, z_per_m) | realval-A | realval-B | Gate |
|---|---|---|---|---|
| vehicle | (-0.15, +0.005) | 0.627 -> 0.641 | 0.662 -> 0.685 (P 1.00) | kept |
| pedestrian | (-0.175, +0.0075) | 0.266 -> 0.290 | 0.226 -> 0.252 (P 1.00) | kept |
| truck | (-0.025, +0.0025) | +0.002 | +0.002 | dropped |
| **mAP** | | **0.572 -> 0.585** | **0.520 -> 0.537** (90% interval +0.014 to +0.021) | |

Candidate model [`routed-g1z`](routed-g1z): S1's members and route plus the calibration; BEV-3D gap on B 0.146 -> 0.129; combined estimate (B) 0.814 -> 0.828; zip `routed-g1z/submissions/2026-10-09_zcal/` (same 50 frames as S1, official check valid in 86 s). **Outcome: submitted as 972563 (S1+C1): combined 0.7665 -> 0.7855, confirmed** (Section 9.1).

### 7.5 S2 results: CenterPoint members (2026-10-09)

Official metric, tuned post-processing, realval-A / realval-B. Summary, gates and lessons: [`docs/02-STRATEGY.md` Section 8.2.1](../docs/02-STRATEGY.md#821-results-2026-10-09); [decision record](../docs/decisions/2026-10-09-s2-center-routed.md).

| Member | vehicle | pedestrian | truck | mAP | BEV-3D gap (B) | 3D@0.7 (B) |
|---|---|---|---|---|---|---|
| S1+C1 route (`g1v2` + C1, `g1v3` + C1, `ut`) | 0.641 / 0.685 | **0.290** / 0.252 | **0.822 / 0.673** | **0.585 / 0.537** | 0.129 | 0.055 |
| `centerpoint-g1v3` (stride 8) | 0.650 / 0.675 | 0.252 / **0.279** | 0.750 / 0.520 | 0.551 / 0.492 | 0.114 | 0.052 |
| `centerpoint-s4-g1v3` (stride 4) | **0.685** / 0.681 | 0.256 / 0.277 | 0.611 / 0.502 | 0.517 / 0.487 | 0.116 | **0.082** |

- **Gate:** no class passes (`route_predictions.py select --rule joint --calibrated`): vehicle from stride 4 gains +0.045 on A but -0.004 on B; the CenterPoint pedestrian gains +0.027 on B but loses 0.038 on A, so the incumbent keeps the best joint AP. `routed-g2` equals S1+C1 (A 0.585, B 0.537): no new V2X version.
- **Height:** the CenterPoint pedestrian has the same BEV AP as the pillar member on B (0.391 vs 0.384) but a smaller BEV-3D gap (0.112 vs 0.158), and no range-dependent z calibration passes for it: z voxels remove most of the bias C1 corrects.
- **Static false positives:** 72-77% of the unmatched pedestrian boxes scoring >= 0.5 repeat in the same 1 m cells across at least 20% of a scene's frames (both architectures; CenterPoint 1.8x more). Removing them with the labels (an upper bound) would lift the S1+C1 pedestrian from 0.290 to 0.356 (A) and 0.252 to 0.346 (B): the twin lacks the static structures, so they are never negatives in training.
- **Bug fixed on the way:** OpenPCDet's `CenterHead.assign_targets` relabeled pedestrians as vehicles in this head layout (vehicle 3D AP 0.019 at epoch 12 before the fix, 0.546 after); see `common/bdc26/detect/pcdet_patches.py`.

### 7.6 S3 results: TTA variants, fusion and score floors (2026-10-09)

Official metric, realval-A / realval-B. Summary, gates and lessons: [`docs/02-STRATEGY.md` Section 8.3.1](../docs/02-STRATEGY.md#831-results-2026-10-09); [decision record](../docs/decisions/2026-10-09-s3-fused-portfolio.md).

| Step | vehicle | pedestrian | truck | mAP | BEV-3D gap (B) | 3D@0.7 (B) |
|---|---|---|---|---|---|---|
| S1+C1 = S2 route (`g1v2` + C1, `g1v3` + C1, `ut`) | 0.641 / 0.685 | 0.290 / 0.252 | 0.822 / 0.673 | 0.585 / 0.537 | 0.129 | 0.055 |
| TTA variants routed (`cp_tta`, `g1v3_tta` + C1', `ut_tta` + C1') | 0.723 / 0.766 | 0.316 / 0.296 | 0.866 / 0.788 | 0.635 / 0.617 | | |
| fused pairs (`cp_tta` + `g1v2_tta`, `g1v3_tta` + `cp4_tta`, `ut_tta` + `g1v2_tta`; IoU 0.5) | 0.758 / 0.821 | 0.350 / 0.362 | 0.877 / 0.814 | 0.662 / 0.666 | 0.063 | 0.078 |
| **with score floors (0.05, 0.075, 0.2): `routed-g3`** | **0.757 / 0.819** | **0.350 / 0.361** | **0.876 / 0.812** | **0.661 / 0.664** | **0.062** | **0.078** |

- **TTA per member** (8 views: flips, yaw +/-5 deg, z +/-0.25 m; each variant with its own tuned `test/postprocess_tta.yaml`): on B, truck +0.09 to +0.14 for every pillar member, vehicle +0.02 to +0.09 (except `g1v3`), pedestrian +0.03 to +0.05 for `g1v3` and both CenterPoint members. C1' is the gated z calibration of the TTA variant (pedestrian z0 -0.225 m, 0.0075 per m).
- **Every class passes the class gate** against S2 (P(gain) 1.00): vehicle +0.134, pedestrian +0.109, truck +0.139 on B; mAP +0.127 (90% interval +0.114 to +0.137). Selected on realval-A alone, B-mAP is still 0.653.
- **Height:** the BEV-3D gap on B halves (0.129 -> 0.062), from the z-shift views and the CenterPoint z voxels in the fused pairs.
- **Static false positives** (pedestrian on B, ranked above the median true-positive score): 6.2 -> 1.8 per frame; 58% of the remaining unmatched ones are still static (R3).
- **Upload gate:** combined estimate (B) 0.828 -> **0.937**, R 0.919 (same 50 frames); kit scorer 74 s with 10,671 boxes (unbudgeted: 48,110 boxes, 224 s; score floors: 955 -> 207 boxes per realval-A frame for -0.0014 B-mAP). **Passed.** Projected before the upload (0.91 x B): mAP about 0.60, combined about 0.89.
- **Leaderboard (974400, 2026-10-10):** combined **0.8381**, mAP 0.5483 (vehicle 0.681, pedestrian 0.346, truck 0.619), 3D@0.7 0.0755, BEV 0.6179, rank 1 of 19; confirmation passed (+0.053 over 972563). The gain was 0.48 x the realval-B gain but 0.80 x the realval-A gain (Section 9.4).

### 7.7 S4 results: two-stage members (2026-10-10)

Official metric, realval-A / realval-B. Review, plan, results and lessons: [`docs/02-STRATEGY.md` Sections 8.4 and 8.4.1](../docs/02-STRATEGY.md#841-results-2026-10-10); [decision record](../docs/decisions/2026-10-10-s4-two-stage.md).

| Member or step | vehicle | pedestrian | truck | mAP | localization loss on B (vehicle / pedestrian) |
|---|---|---|---|---|---|
| `centerpoint-g1v3` (stage 1 alone), TTA | 0.723 / 0.766 | 0.282 / 0.324 | 0.723 / 0.528 | 0.576 / 0.539 | 0.102 / 0.289 |
| `voxelrcnn-g1v3`, TTA | 0.796 / 0.820 | 0.323 / 0.359 | 0.822 / 0.715 | 0.647 / 0.632 | 0.069 / 0.300 |
| `pvrcnnpp-g1v3`, TTA | 0.794 / **0.831** | 0.318 / **0.374** | 0.810 / 0.727 | 0.641 / 0.644 | 0.056 / 0.266 |
| S3 portfolio (`routed-g3`) | 0.757 / 0.819 | 0.350 / 0.361 | 0.876 / 0.812 | 0.661 / 0.664 | 0.090 / 0.274 |
| **S4 portfolio (`routed-g4`)** | **0.806 / 0.843** | 0.350 / 0.361 | **0.896 / 0.834** | **0.684 / 0.679** | 0.054 / 0.274 |

- **Routing and fusion:** vehicle from `pv_tta` + `vr_tta` (IoU 0.7), truck from the triple `g1v3_tta` + `g1v2_tta` + `vr_tta` (IoU 0.7), pedestrian keeps the S3 fusion `g1v3_tta` + `cp4_tta`; vehicle B +0.024 and truck +0.022 against S3 (P 1.00 and 0.99), mAP +0.015 (+0.011 to +0.022).
- **Score blend per class** (`ROI_HEAD.SCORE_BLEND_ALPHA` [0.5, 0.5, 1]): the class-agnostic IoU head under-serves trucks (Voxel R-CNN truck A 0.218 with the IoU score alone, 0.570 with the stage-1 score).
- **Hypothesis check:** the second stage halves the vehicle localization loss and doubles 3D@0.7 on B (0.078 -> 0.146), but the pedestrian localization loss stays at 0.27-0.30; the two-stage pedestrian gain is ranking.
- **Upload gate:** combined estimate (B) 0.937 -> **0.950** (bar 0.942), R 0.919; kit scorer 80 s with 13,028 boxes. **Passed.** Projected before the upload (0.8 x the A gain): combined about 0.854.
- **Leaderboard (975938, 2026-10-11):** combined **0.8485**, mAP 0.5605 (vehicle 0.707, pedestrian 0.346 identical to S3, truck 0.628), 3D@0.7 0.1118 (S3 0.0755), BEV 0.6219, rank 1 of 19; confirmation passed (+0.010). The gain was 0.53 x the realval-A gain and 0.80 x the realval-B gain (Section 9.4).

### 7.8 S5 results: object scaling and GBlobs (2026-10-11)

Official metric, realval-A / realval-B, TTA members. Review, plan, results and lessons: [`docs/02-STRATEGY.md` Sections 8.5 and 8.5.1](../docs/02-STRATEGY.md#851-results-2026-10-11); [decision record](../docs/decisions/2026-10-11-s5-object-scaling.md).

| Member or step | vehicle | pedestrian | truck | mAP |
|---|---|---|---|---|
| `voxelrcnn-g1v3` (parent) | 0.796 / 0.820 | 0.323 / 0.359 | 0.822 / 0.715 | 0.647 / 0.632 |
| `voxelrcnn-gblobs-g1v3` (run a, GBlobs cell covariance) | 0.809 / 0.830 | 0.310 / 0.357 | 0.788 / 0.674 | 0.635 / 0.621 |
| `voxelrcnn-ros-g1v3` (run b, object scaling) | 0.787 / 0.811 | **0.349 / 0.393** | **0.856 / 0.797** | **0.664 / 0.667** |
| `pvrcnnpp-ros-g1v3` (extension) | 0.790 / 0.810 | 0.307 / 0.354 | 0.829 / 0.786 | 0.642 / 0.650 |
| `pointpillars-ros-g1v3` (extension) | 0.643 / 0.649 | 0.278 / 0.251 | 0.672 / 0.546 | 0.531 / 0.482 |
| S4 portfolio (`routed-g4`) | 0.806 / 0.843 | 0.350 / 0.361 | 0.896 / 0.834 | 0.684 / 0.679 |
| **S5 portfolio (`routed-g5`)** | **0.828 / 0.852** | **0.350 / 0.397** | **0.905 / 0.848** | **0.694 / 0.699** |

- **Routing and fusion:** pedestrian from `vrros_tta` + `pv_tta` (B +0.036), truck from `ut_tta` + `vrros_tta` + `pvros_tta` (+0.014), vehicle from `vrgb_tta` + `pv_tta` + `pvros_tta` (+0.009 after the score floors; the GBlobs member only helps inside the fusion).
- **Why ROS helps:** truck localization loss on B 0.050 -> 0.009 (stretched trucks cover the real 5.7-13.1 m), pedestrian ranking loss 0.316 -> 0.289 with only mild walker scaling. The anchor-based pillars lose trucks (one 7.94 m anchor).
- **Upload gate:** combined estimate (B) 0.950 -> **0.967** (bar 0.955), R 0.919; kit scorer 58 s with 8,896 boxes. **Passed.** Projection: combined about 0.856 (0.852-0.868).
- **Leaderboard (978945, 2026-10-11):** combined **0.8730**, mAP 0.5890 (vehicle 0.718, pedestrian **0.391**, truck 0.657), 3D@0.7 0.196, rank 1 of 19; confirmation passed (+0.024), above the projected range: the pedestrian gain (+0.046) followed realval-B (+0.036), not A (0.000).

### 7.9 R3 results: engine G2-lite corpus `g1-v4` (2026-10-12)

Official metric, realval-A / realval-B, TTA members. Review, plan, results and lessons: [`docs/02-STRATEGY.md` Sections 8.7.1 and 8.7.2](../docs/02-STRATEGY.md#872-r3-results-2026-10-11-to-2026-10-13); [decision record](../docs/decisions/2026-10-12-r3-g2-lite.md).

| Member or step | vehicle | pedestrian | truck | mAP |
|---|---|---|---|---|
| `pointpillars-g1v3` (parent of wave 0) | 0.598 / 0.604 | 0.267 / 0.257 | 0.839 / 0.704 | 0.568 / 0.522 |
| `pointpillars-g1v4` (data only) | **0.690 / 0.667** | **0.288 / 0.278** | **0.859 / 0.758** | **0.612 / 0.567** |
| `voxelrcnn-ros-g1v4` (ROS capped) | **0.831 / 0.832** | 0.340 / 0.376 | 0.849 / 0.803 | 0.673 / 0.670 |
| `voxelrcnn-ros-g1v4` `run0_rostail` (uncapped ROS) | 0.825 / 0.830 | 0.336 / 0.371 | 0.509 / 0.418 | 0.557 / 0.540 |
| `pvrcnnpp-ros-g1v4` (ROS capped) | 0.826 / 0.816 | 0.328 / 0.369 | 0.834 / 0.813 | 0.663 / 0.666 |
| S5 portfolio (`routed-g5`, the entry) | 0.828 / 0.852 | 0.350 / 0.397 | 0.905 / 0.848 | 0.694 / 0.699 |
| **R3 portfolio (`routed-g6`)** | 0.828 / 0.852 | **0.370 / 0.408** | 0.905 / 0.848 | **0.701 / 0.703** |

- **Routing and fusion** (built on the S5 entry): pedestrian from `vrros_tta` + `vrros4_tta` (B +0.011, pooled +0.022); vehicle and truck keep the S5 fusions (best candidates +0.009 on B, under the 0.01 bar).
- **What the corpus changes:** real truck sizes (5.20 x 2.07 m -> 7.97 x 2.88 m, real 8.20 x 2.89 m) take the pillars' truck localization loss from 0.20 to 0.004 with class-wise anchors; static clutter cuts confident static pedestrian false positives (pillars 6.2 -> 3.6 per frame on B). The first two-stage run, with an uncapped ROS length range on top of the real sizes, fitted about one 19.7 m false truck per frame onto a long static structure; ROS is now capped at the real 99th-percentile sizes.
- **Realism:** the 50 frames from `g1-v4` score 0.925 as packaged (S5 zip 0.919).
- **Upload gate:** combined estimate (B, unclipped from R3 on) 0.967 -> **0.973** (bar 0.972; 0.970 clipped), kit scorer 56 s with 8,682 boxes: **passed, by 0.0006**. Projection: combined 0.876-0.878 against the 0.8730 entry.
- **Leaderboard (986496, 2026-10-14):** combined **0.8789**, mAP 0.5929 (vehicle 0.719 and truck 0.657 identical, pedestrian 0.391 -> **0.403**), R 0.9203 -> **0.9268**, rank 1 of 19; confirmation passed (+0.0059, at the top of the projected range). Both gains followed the local numbers: pedestrian +0.012 against +0.011 on B, realism +0.0065 against +0.0064 as packaged.

### 7.10 R5 results: first density prior, seeds, `g1-v5` members, walker tail copies (2026-10-14)

Full tables: [`docs/02-STRATEGY.md` Section 8.9.1](../docs/02-STRATEGY.md#891-r5-results-2026-10-14); record [`2026-10-14-r5-realism-led.md`](../docs/decisions/2026-10-14-r5-realism-led.md).

| Item | realval-A / realval-B |
|---|---|
| Density prior v1 (8 m cells) in `g1-v5` | realism of the selected frames 0.925 -> 0.937 as packaged (held-out proxies 4-5) |
| `voxelrcnn-ros-g1v4-s2` (seed 1666), TTA | 0.650 / 0.619 (R3 member 0.673 / 0.670); truck 0.636 against 0.803: seed variance |
| `pvrcnnpp-ros-g1v4-s2` (seed 1666), TTA | 0.671 / 0.671 (0.663 / 0.666) |
| `pointpillars-g1v5`, TTA | 0.641 / 0.589 (`g1-v4`: 0.612 / 0.567); truck 0.758 -> 0.827 |
| `voxelrcnn-ros-g1v5`, `pvrcnnpp-ros-g1v5`, TTA | 0.651 / 0.639 (pedestrian 0.384), 0.684 / 0.669 |
| `routed-g7` vehicle (`pvros4s2_tta` + `vrros4s2_tta` + `vrros5_tta`, IoU 0.7) | 0.828 / 0.852 -> **0.857 / 0.864** |
| `routed-g7` pedestrian (tail copies r 0.15 m) | 0.370 / 0.408 -> **0.381 / 0.418** |
| `routed-g7` mAP | 0.701 / 0.703 -> **0.714 / 0.710**; estimate 0.973 -> **0.983** (bar 0.978): upload gate passed |
| **Leaderboard (2026-10-15)** | 990255: **0.8852** (mAP 0.5972, R 0.9332): pedestrian 0.403 -> 0.413, vehicle 0.719 -> 0.721, realism 0.927 -> 0.933 (EMD 1.345 -> 1.182, FPD 0.733 -> 1.468); rank 1 of 20 |

### 7.11 S6 results: seed bags (2026-10-16)

Full tables: [`docs/02-STRATEGY.md` Section 8.6.1](../docs/02-STRATEGY.md#861-s6-results-2026-10-15-to-2026-10-16); record [`2026-10-16-s6-variance-controlled.md`](../docs/decisions/2026-10-16-s6-variance-controlled.md).

| Item | realval-A / realval-B |
|---|---|
| Seeds `voxelrcnn-ros-g1v5-s2/-s3`, `pvrcnnpp-ros-g1v5-s2/-s3`, TTA | Voxel R-CNN 0.690 / 0.691 and 0.669 / 0.650 (truck B 0.832, 0.740; seed 666: 0.697); PV-RCNN++ 0.689 / 0.680 and 0.667 / 0.660 |
| `bag-voxelrcnn-ros-g1v5` (seeds 666-2666), TTA | **0.708 / 0.697** (best seed 0.690 / 0.691); vehicle 0.861, pedestrian 0.407 |
| `bag-pvrcnnpp-ros-g1v5` (seeds 666-2666), TTA | **0.702 / 0.694** (best seed 0.689 / 0.680); truck 0.842 |
| `bag-voxelrcnn-ros-g1v4`, `bag-pvrcnnpp-ros-g1v4` (seeds 666, 1666), TTA | 0.677 / 0.676 and 0.679 / 0.681 |
| `routed-g8` (select, fuse, final gate against `routed-g7`) | select routed every class to a bag (0.707 / 0.703); fuse kept the R5 fusions: vehicle +0.005 (P 0.94), pedestrian -0.006, truck -0.001 (A +0.030, pooled +0.022); final gate: predictions identical to R5 |
| Result | **equal to R5** (0.714 / 0.710, estimate 0.983, bar 0.988): no upload |

**Leaderboard (2026-10-17):** 995877 (variant b `routed-g8b`) **0.8931** (mAP 0.6065): **vehicle 0.721 -> 0.735, truck 0.657 -> 0.671**, pedestrian and realism identical; rank 1 of 23.

### 7.12 S7 results: visibility rule (2026-10-18)

Full tables: [`docs/02-STRATEGY.md` Section 8.11](../docs/02-STRATEGY.md#811-s7-visibility-rule-v2x-2026-10-18); record [`2026-10-18-s7-visibility-rule.md`](../docs/decisions/2026-10-18-s7-visibility-rule.md); statistics in [`../data-v2x-track/README.md`](../data-v2x-track/README.md) (label visibility).

| Item | realval-A / realval-B |
|---|---|
| Real labels: points per box (p1 / p2 / p5) | pedestrian 5 / 6 / 6 (1.6-1.7% below 6); vehicle 7 / 8 / 10; truck 15-30 / 18-32 / 31-51. Synthetic `g1-v5` pedestrians: 16.3% below 6 (38.4% beyond 30 m) |
| Step 1, pedestrian k = 6 (ranked last below 6 points) | 0.3805 -> **0.3985** / 0.4179 -> **0.4413**; pooled +0.0197 (P 1.00); k = 7 loses (-0.0022 pooled) |
| Step 1, vehicle k = 5 | 0.8654 -> 0.8678 / 0.8693 -> 0.8723; pooled +0.0022 (P 1.00) |
| `routed-g9` | **0.734 / 0.721** (S6b 0.727 / 0.712); unmatched confident pedestrian boxes on B 8.0 -> 5.1 per frame; recall unchanged; projection +0.0040: upload gate passed |
| Leaderboard (2026-10-19) | **1001919: 0.8982** (mAP 0.6124): pedestrian 0.413 -> **0.429** (0.85 x A, 0.66 x B), vehicle 0.735 -> 0.737, truck and realism identical; rank 1 of 23 |
| Step 2 | done (2026-10-19): `routed-g10` A 0.7377 / B 0.7223, projection +0.0014: not uploaded |
| S7.4 and S7.6 (2026-10-26/27) | generator-draw bags, bag swap, pooled budget: no class passed against the entry; the entry stays the submission-ready version ([record](../docs/decisions/2026-10-26-s7-final-revisions.md)) |

## 8. Experiment log and next experiments

| # | Question | Result / plan |
|---|---|---|
| E1 | Resample UT to the real valid count (35k) | in all versions |
| E2 | Walkers (G1) vs riders only | done: pedestrian 0 -> 0.118 |
| E3 | Walker body v1 vs v2 | done: pedestrian 0.118 -> 0.173 |
| E4 | Walkers calibrated on legal real walkers + FOV mask | done: pedestrian 0.173 -> 0.266; realism 0.901 -> 0.919 |
| E5 | Pedestrian NMS and re-centering | tuned per class (Section 6.3) |
| E6 | Ground-plane canonicalization of the sloped scene | part of the S4 diagnosis (`docs/02` Section 8.1.2 D2 and Section 8.4 step 0) |
| E7 | Architecture routing for pedestrians (CenterPoint) | done (S2): no class passes the class gate; static false positives are the main pedestrian error (Section 7.5) |
| E8 | Background density calibration for realism (as Track 1) | done (R5, E14): first prior `gen/density_prior_v1.npz`; realism 0.925 -> 0.937 as packaged (Section 7.10) |
| E13 | Engine G2-lite (real-size re-cast trucks, static clutter) | done (R3): pillars up on every class; pedestrian static false positives down; portfolio pedestrian +0.011 on B (Section 7.9) |
| E9 | TTA and weighted box fusion, height TTA | done (S3): every class up on B; mAP B 0.537 -> 0.664; BEV-3D gap 0.129 -> 0.062 (Section 7.6) |
| E11 | Two-stage refinement (Voxel R-CNN, PV-RCNN++) | done (S4): vehicle and truck up on B; pedestrian localization unchanged (Section 7.7) |
| E12 | GBlobs inputs and class-wise object scaling | done (S5): object scaling helps every anchor-free and two-stage member; GBlobs only inside fusions (Section 7.8) |
| E14 | Background density prior (E8) for the G2-lite corpus | done (R5): `gen/density_prior_v1.npz`, corpus `g1-v5`; realism 0.925 -> 0.937; pillars truck +0.07 on B (Section 7.10) |
| E15 | Seeds and walker tail copies | done (R5): large seed variance on truck; pedestrian copies +0.010 on B (Section 7.10) |
| E16 | Seed bags | done (S6): every bag at or above its best seed, none above the R5 fusions on B; `routed-g8` equals R5 (Section 7.11) |
| E17 | Sparse-box demotion at the real labels' visibility cut (S7 step 1) | done: pedestrian +0.018 (A) / +0.023 (B), vehicle +0.002 / +0.003; leaderboard 1001919 **0.8982** (pedestrian +0.015), the entry (Section 7.12) |
| E18 | Training labels with the same visibility rule (S7 step 2, corpus `g1-v5m`) | done: projection +0.0014, not uploaded (Section 7.12) |
| E19 | Generator-draw bags, bag swap and pooled budget (S7.4, S7.6) | done: bags +0.002 to +0.004 alone, nothing passed inside the portfolio; truck swap +0.002 on both splits, pooled P 0.70 ([record](../docs/decisions/2026-10-26-s7-final-revisions.md)) |

## 9. Submission log

| Date | Model / tag | CodaBench id | Local mAP (A / B) | Local R | LB mAP | LB R | LB combined | Note |
|---|---|---|---|---|---|---|---|---|
| 2026-10-02 | `routed-g1` / `first`, hand-edited copy uploaded as `submission_v2x_20261002.zip` | 957439 | 0.572 / 0.520 | 0.919 | | | | Running for 4 days with no log ("Preparing submission..."), cancelled 2026-10-06; counted (1 of 100 used); Section 10.6 |
| 2026-10-06 | `routed-g1` / `first`, team KarmaRV, uploaded unchanged as `submission_v2x_karmarv.zip` | 965633 | 0.572 / 0.520 | 0.919 | **0.4648** | **0.9203** | **0.7665** | strategy S1; rank 1 of 34 (next 0.6114); server record [`codabench_965633.json`](routed-g1/submissions/2026-10-02_first/codabench_965633.json) |
| 2026-10-09 | `routed-g1z` / `zcal` (S1+C1 z calibration), the packaged zip unchanged | 972563 | 0.585 / 0.537 | 0.919 | **0.4869** | **0.9203** | **0.7855** | strategy S1+C1; rank 1 of 19 (next 0.6616); scored in about 4 min; server record [`codabench_972563.json`](routed-g1z/submissions/2026-10-09_zcal/codabench_972563.json); [decision record](../docs/decisions/2026-10-09-s1-closeout-z-calibration.md) |
| 2026-10-10 | `routed-g3` / `s3` (strategy S3), uploaded unchanged as `v2x_s3_submission.zip` | 974400 | 0.661 / 0.664 | 0.919 | **0.5483** | **0.9203** | **0.8381** | strategy S3; rank 1 of 19 (next 0.6616); kit scorer 74 s, 10,671 boxes; server record [`codabench_974400.json`](routed-g3/submissions/2026-10-09_s3/codabench_974400.json); [decision record](../docs/decisions/2026-10-09-s3-fused-portfolio.md) |
| 2026-10-10 | `routed-g4` / `s4` (strategy S4), uploaded unchanged as `v2x_s4_submission.zip` | 975938 | 0.684 / 0.679 | 0.919 | **0.5605** | **0.9203** | **0.8485** | strategy S4; rank 1 of 19 (next 0.6616); kit scorer 80 s, 13,028 boxes; server record [`codabench_975938.json`](routed-g4/submissions/2026-10-10_s4/codabench_975938.json); [decision record](../docs/decisions/2026-10-10-s4-two-stage.md) |
| 2026-10-11 | `routed-g5` / `s5` (strategy S5), uploaded unchanged as `v2x_s5_submission.zip` | 978945 | 0.694 / 0.699 | 0.919 | **0.5890** | **0.9203** | **0.8730** | strategy S5; rank 1 of 19 (next 0.6616); kit scorer 58 s, 8,896 boxes; server record [`codabench_978945.json`](routed-g5/submissions/2026-10-11_s5/codabench_978945.json); [decision record](../docs/decisions/2026-10-11-s5-object-scaling.md) |
| 2026-10-13 | `routed-g6` / `r3` (strategy R3), uploaded unchanged as `v2x_r3_submission.zip` | 986496 | 0.701 / 0.703 | 0.925 | **0.5929** | **0.9268** | **0.8789** | strategy R3; rank 1 of 19 (next 0.6616); kit scorer 56 s, 8,682 boxes; server record [`codabench_986496.json`](routed-g6/submissions/2026-10-12_r3/codabench_986496.json); [decision record](../docs/decisions/2026-10-12-r3-g2-lite.md) |
| 2026-10-15 | `routed-g7` / `r5` (strategy R5), uploaded unchanged as `v2x_r5_submission.zip` | 990255 | 0.714 / 0.710 | 0.937 | **0.5972** | **0.9332** | **0.8852** | strategy R5; **rank 1 of 20** (next 0.6616); confirmed (+0.0063: pedestrian +0.011, vehicle +0.002, realism +0.0065); kit scorer 132 s, 24,759 boxes; server record [`codabench_990255.json`](routed-g7/submissions/2026-10-14_r5/codabench_990255.json); [decision record](../docs/decisions/2026-10-14-r5-realism-led.md) |
| 2026-10-17 | `routed-g8b` / `s6b` (S6 variant b), uploaded unchanged as `v2x_s6b_submission.zip` | 995877 | 0.727 / 0.712 | 0.937 | **0.6065** | **0.9332** | **0.8931** | S6 variant b (not through the upload gate; a complete-system comparison at the entrant's request); **rank 1 of 23** (next 0.7555); confirmed (+0.0079: vehicle +0.014, truck +0.014, pedestrian and realism identical); kit scorer 137 s, 24,284 boxes; server record [`codabench_995877.json`](routed-g8b/submissions/2026-10-16_s6b/codabench_995877.json) |
| 2026-10-19 | `routed-g9` / `s7` (S7 step 1), uploaded unchanged as `v2x_s7_submission.zip` | 1001919 | 0.734 / 0.721 | 0.937 | **0.6124** | **0.9332** | **0.8982** | S7 step 1 (upload gate passed: projection +0.0040); **rank 1 of 23** (next 0.7555); confirmed (+0.0051: pedestrian +0.0154, vehicle +0.0023, truck and realism identical); kit scorer 141 s, 24,284 boxes; server record [`codabench_1001919.json`](routed-g9/submissions/2026-10-18_s7/codabench_1001919.json) |

### 9.1 Local vs leaderboard per class (3D AP@0.5 R40)

| | mAP | vehicle | pedestrian | truck | BEV mAP@0.5 |
|---|---|---|---|---|---|
| **1001919 leaderboard (S7 step 1)** | **0.6124** | **0.737** | **0.429** | **0.671** | 0.6662 |
| S7 realval-A / realval-B | 0.734 / 0.721 | 0.868 / 0.872 | 0.399 / 0.441 | 0.936 / 0.848 | |
| 995877 leaderboard (S6 variant b) | 0.6065 | 0.735 | 0.413 | 0.671 | 0.6583 |
| S6b realval-A / realval-B | 0.727 / 0.712 | 0.865 / 0.869 | 0.381 / 0.418 | 0.936 / 0.848 | |
| 990255 leaderboard (R5) | **0.5972** | 0.721 | 0.413 | 0.657 | 0.6482 |
| R5 realval-A / realval-B | 0.714 / 0.710 | 0.857 / 0.864 | 0.381 / 0.418 | 0.905 / 0.848 | |
| 986496 leaderboard (R3) | **0.5929** | 0.719 | 0.403 | 0.657 | 0.6428 |
| R3 realval-A / realval-B | 0.701 / 0.703 | 0.828 / 0.852 | 0.370 / 0.408 | 0.905 / 0.848 | |
| 978945 leaderboard (S5) | 0.5890 | 0.718 | 0.391 | 0.657 | 0.6389 |
| S5 realval-A / realval-B | 0.694 / 0.699 | 0.828 / 0.852 | 0.350 / 0.397 | 0.905 / 0.848 | |
| 975938 leaderboard (S4) | 0.5605 | 0.707 | 0.346 | 0.628 | 0.6219 |
| S4 realval-A / realval-B | 0.684 / 0.679 | 0.806 / 0.843 | 0.350 / 0.361 | 0.896 / 0.834 | |
| 974400 leaderboard (S3) | 0.5483 | 0.681 | 0.346 | 0.619 | 0.6179 |
| S3 realval-A / realval-B | 0.661 / 0.664 | 0.757 / 0.819 | 0.350 / 0.361 | 0.876 / 0.812 | |
| 972563 leaderboard (S1+C1) | 0.4869 | 0.605 | 0.281 | 0.574 | 0.5696 |
| S1+C1 realval-A / realval-B | 0.585 / 0.537 | 0.641 / 0.685 | 0.290 / 0.252 | 0.822 / 0.673 | |
| 965633 leaderboard (S1) | 0.4648 | 0.585 | 0.235 | 0.574 | 0.5696 |
| S1 realval-A / realval-B | 0.572 / 0.520 | 0.627 / 0.662 | 0.266 / 0.226 | 0.822 / 0.673 | |
| leaderboard / realval-B (S1 -> S1+C1) | 0.89 -> 0.91 | 0.88 -> 0.88 | 1.04 -> 1.12 | 0.85 | |
| leaderboard / realval-B (S3) | 0.83 | 0.83 | 0.96 | 0.76 | |
| leaderboard gain / realval-A gain (S1+C1 -> S3) | 0.80 | 0.65 | 1.07 | 0.82 | |
| leaderboard / realval-B (S4) | 0.82 | 0.84 | 0.96 | 0.75 | |
| leaderboard gain / realval-A gain, / realval-B gain (S3 -> S4) | 0.53, 0.80 | 0.54, 1.11 | (unchanged) | 0.50, 0.45 | |
| leaderboard gain / realval-A gain, / realval-B gain (S4 -> S5) | 2.83, 1.46 | 0.50, 1.23 | (A 0.000), 1.27 | 3.28, 2.04 | |
| leaderboard gain / realval-A gain, / realval-B gain (S5 -> R3) | 0.57, 1.05 | (unchanged) | 0.60, 1.07 | (unchanged) | |
| leaderboard gain / realval-A gain, / realval-B gain (S6b -> S7) | 0.87, 0.67 | 0.98, 0.79 | 0.85, 0.66 | (unchanged) | |
S3 changed only the detections (same 50 frames, identical realism): the leaderboard BEV-3D gap fell from 0.083 to 0.070 (realval-B: 0.129 to 0.062), 3D@0.7 rose from 0.0555 to 0.0755. The S1+C1 z calibration changed only z, so BEV AP and realism are identical; it gained more on the test frames than on realval-B for pedestrians (+0.046 vs +0.026) and about the same for vehicles (+0.020 vs +0.023), and the leaderboard BEV-3D gap fell from 0.105 to 0.083.

Realism on the server: CD 2.215, MMD 0.00329, EMD 1.414, FPD 1.092, R 0.9203 (local proxy 4: 2.181, 0.00384, 1.441, 1.126, 0.9188). Vehicle and pedestrian transfer close to realval-B; the truck route (the UT-only run, chosen on realval-A) loses the most (analysis: Section 9.4; next strategy: root README Section 8 and [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#8-strategy-routes-after-s1) Section 8).

### 9.2 Artifacts

S6 variant b (995877, the entry): model [`routed-g8b`](routed-g8b) ([`model.yaml`](routed-g8b/model.yaml)); the upload copy [`v2x_s6b_submission.zip`](routed-g8b/submissions/2026-10-16_s6b/v2x_s6b_submission.zip) (md5 `00a80bb32c5019b6d9913555efebc6b6`, in its [`manifest.json`](routed-g8b/submissions/2026-10-16_s6b/manifest.json)); server record [`codabench_995877.json`](routed-g8b/submissions/2026-10-16_s6b/codabench_995877.json); the 10 checkpoints (two bags of three seeds and four single members) as assets of release 6.0 ([`releases/6.0/weights.json`](../releases/6.0/weights.json); `python common/tools/release_weights.py fetch --tag 6.0 --version v2x:s6b`); reproduction from the weights: [`routed-g8b/test/reproduce_s6b.sh`](routed-g8b/test/reproduce_s6b.sh) (test frames) and [`reproduce_s6b_validation.sh`](routed-g8b/test/reproduce_s6b_validation.sh) (realval-A/B).

990255 (R5): model [`routed-g7`](routed-g7) ([`model.yaml`](routed-g7/model.yaml)); the upload copy [`v2x_r5_submission.zip`](routed-g7/submissions/2026-10-14_r5/v2x_r5_submission.zip) (md5 `0d339f79a21059a8c97211d4d7c15533`, in its [`manifest.json`](routed-g7/submissions/2026-10-14_r5/manifest.json)); server record [`codabench_990255.json`](routed-g7/submissions/2026-10-14_r5/codabench_990255.json); realism frames from `pcdet/g1-v5` ([`synthetic_ids.txt`](routed-g7/submissions/2026-10-14_r5/synthetic_ids.txt)).

986496 (R3): model [`routed-g6`](routed-g6) ([`model.yaml`](routed-g6/model.yaml)); the upload copy [`v2x_r3_submission.zip`](routed-g6/submissions/2026-10-12_r3/v2x_r3_submission.zip) (md5 `510eb8f9a775539c87ce323f9b13bc1b`, in its [`manifest.json`](routed-g6/submissions/2026-10-12_r3/manifest.json)); server record [`codabench_986496.json`](routed-g6/submissions/2026-10-12_r3/codabench_986496.json); realism frames from `pcdet/g1-v4`; server realism CD 2.181, MMD 0.00146, EMD 1.345, FPD 0.733, R 0.9268 (S1-S5 frames: 2.215, 0.00329, 1.414, 1.092, 0.9203).

978945 (S5): model [`routed-g5`](routed-g5) ([`model.yaml`](routed-g5/model.yaml)); the upload copy [`v2x_s5_submission.zip`](routed-g5/submissions/2026-10-11_s5/v2x_s5_submission.zip) (md5 `e5b258652c9aa0f783f3cdfbd614d687`, in its [`manifest.json`](routed-g5/submissions/2026-10-11_s5/manifest.json)); server record [`codabench_978945.json`](routed-g5/submissions/2026-10-11_s5/codabench_978945.json); reproducible from the committed `model.yaml`.

975938 (S4): model [`routed-g4`](routed-g4) ([`model.yaml`](routed-g4/model.yaml): members with the two-stage members and TTA variants, `route`, `calibration`, `fusion` with a triple, `budget`); the upload copy [`v2x_s4_submission.zip`](routed-g4/submissions/2026-10-10_s4/v2x_s4_submission.zip) (md5 `29c8f7a9887d1443cd7f23289ecfc8b1`, byte-identical to the folder's `submission.zip`, in its [`manifest.json`](routed-g4/submissions/2026-10-10_s4/manifest.json)); server record [`codabench_975938.json`](routed-g4/submissions/2026-10-10_s4/codabench_975938.json); reproducible from the committed `model.yaml` and the saved member predictions.

974400 (S3): model [`routed-g3`](routed-g3) ([`model.yaml`](routed-g3/model.yaml): members with TTA variants, `route`, `calibration`, `fusion`, `budget`); the upload copy [`v2x_s3_submission.zip`](routed-g3/submissions/2026-10-09_s3/v2x_s3_submission.zip) (md5 `5e46f9450feb7846455c4b8428483641`, byte-identical to the folder's `submission.zip`, in its [`manifest.json`](routed-g3/submissions/2026-10-09_s3/manifest.json)); server record [`codabench_974400.json`](routed-g3/submissions/2026-10-09_s3/codabench_974400.json); reproducible: the zip's predictions equal `route_predictions.py merge` of the saved member predictions with the committed `model.yaml`.

972563 (S1+C1): model [`routed-g1z`](routed-g1z) ([`model.yaml`](routed-g1z/model.yaml): S1 members and route plus `calibration`); the packaged zip of [`routed-g1z/submissions/2026-10-09_zcal/`](routed-g1z/submissions/2026-10-09_zcal) committed as [`submission_v2x.zip`](routed-g1z/submissions/2026-10-09_zcal/submission_v2x.zip) (md5 `7fbb973e2c1715dea66d7850b8bde11f`, also in its [`manifest.json`](routed-g1z/submissions/2026-10-09_zcal/manifest.json); tag 1.0); server record [`codabench_972563.json`](routed-g1z/submissions/2026-10-09_zcal/codabench_972563.json); register row: [`docs/decisions/README.md`](../docs/decisions/README.md#2-submission-register).

965633 (S1):

| | |
|---|---|
| Model | [`routed-g1`](routed-g1) ([at tag 0.1](https://github.com/karmarv/utsim2real-bdc26/tree/0.1/model-v2x-track/routed-g1)); members and route in [`routed-g1/model.yaml`](routed-g1/model.yaml); checkpoints are not in git |
| Submitted file | [`submission_v2x_karmarv.zip`](https://github.com/karmarv/utsim2real-bdc26/releases/download/0.1/submission_v2x_karmarv.zip) (GitHub release [0.1](https://github.com/karmarv/utsim2real-bdc26/releases/tag/0.1)), the packaged zip unchanged, md5 `5343da990d5cdd1f34df379433479e2a` |
| Manifest | [`manifest.json`](routed-g1/submissions/2026-10-02_first/manifest.json) (checkpoints, route, frames, local scores, validation, CodaBench attempts), [`synthetic_ids.txt`](routed-g1/submissions/2026-10-02_first/synthetic_ids.txt) |
| Server record | [`codabench_965633.json`](routed-g1/submissions/2026-10-02_first/codabench_965633.json): every `scores.json` field and the scoring log |
| Leaderboard | [CodaBench 16685 results](https://www.codabench.org/competitions/16685/#/results-tab) |

### 9.3 Realism on the server

| | CD | MMD | EMD | FPD | R |
|---|---|---|---|---|---|
| leaderboard S6b (995877, the R5 frames) | 1.986 | 0.00063 | 1.182 | 1.468 | 0.9332 (identical) |
| **leaderboard R5 (990255, frames from `g1-v5`)** | 1.986 | 0.00063 | 1.182 | 1.468 | **0.9332** |
| local R5, held-out proxies 4 / 5 | | | 1.209 / 1.176 | 1.36 / 1.19 | 0.935 / 0.938 |
| leaderboard R3 (986496, frames from `g1-v4`) | 2.181 | 0.00146 | 1.345 | 0.733 | 0.9268 |
| leaderboard (965633 to 978945, identical frames) | 2.215 | 0.00329 | 1.414 | 1.092 | **0.9203** |
| local, held-out proxy 4 | 2.181 | 0.00384 | 1.441 | 1.126 | 0.9188 |
| ECCV 2026 winner | | | | | 0.925 |

Both sides pooled 2,500,000 points before subsampling (50 x 50,000), so the packaged density was used as intended. Share of the realism loss (1 - R) per term: EMD 89%, FPD 7%, CD 2%, MMD 2%.

### 9.4 What transferred and what did not

| Finding | Evidence | Implication |
|---|---|---|
| Realism transfers | R 0.920 vs 0.919 locally | the FOV mask, null returns and frame selection work; EMD is the remaining realism term |
| Vehicle and pedestrian transfer close to realval-B | vehicle 0.585 (B 0.662), pedestrian 0.235 (B 0.226) | pedestrian (953 test GT, the largest class) is limited by the detector, not by transfer: the S2 target |
| Truck does not | truck 0.574 (A 0.822, B 0.673) | the truck route (the UT-only run, best on A) lost the most; route on A and B jointly and add truck size modes |
| Height costs 0.105 mAP | BEV@0.5 0.570 vs 3D@0.5 0.465 (S1) | realval shows the same gap (0.103 A, 0.146 B), caused partly by a range-dependent z bias: C1 removed part of it (leaderboard gap 0.083, Section 7.4); the rest is the S2-S4 target |
| Local estimate was optimistic | estimate A / B / leaderboard: S1 0.858 / 0.814 / 0.767; S1+C1 0.869 / 0.828 / 0.786; S3 0.934 / 0.937 / 0.838 | the B estimate overstated S3 by 0.099: its large B gain did not transfer in full |
| S3 gains transferred at 0.80 x the realval-A gain, 0.48 x the realval-B gain | vehicle +0.076 (B +0.134), pedestrian +0.064 (B +0.109), truck +0.044 (B +0.139) | project the leaderboard from the A gain (same factor on LUMPI, 0.81); B took part in every joint ranking and is the smaller split |
| Truck transfers least | S3 truck leaderboard / B 0.76 (S1 0.85); gain 0.32 x B | the TTA truck route and its fusion pair won mostly on B; long trucks in the generator (R3) |
| Height improved on the test frames too | BEV-3D gap 0.083 -> 0.070, 3D@0.7 0.0555 -> 0.0755 | z-shift views and CenterPoint z voxels transfer; S4 is now judged on 3D@0.7 |
| S4 gains transferred at 0.53 x the A gain, 0.80 x the B gain (reverse of S3) | vehicle +0.027 (A +0.049, B +0.024), truck +0.010 (A +0.020, B +0.022); pedestrian identical | no local split predicts the size of a gain (five uploads: 0.25-1.9 x); project with 0.6 x the mean of the A and B gains |
| Two-stage refinement transfers for vehicles | 3D@0.7 0.0755 -> 0.1118 on the leaderboard (B 0.078 -> 0.146) | the second stage localizes vehicles and trucks better on real frames too |
| S5 pedestrian gain followed realval-B | pedestrian +0.046 on the leaderboard (B +0.036, A 0.000); combined 0.8730 above the projected 0.852-0.868 | for V2X, B (other scenes) is the better predictor of walker gains |
| R5 walker tail copies transferred as constructed | pedestrian +0.0105 on the leaderboard against +0.0098 on B (1.07 x) | copies below every original box cannot lower AP; they are worth keeping on walker classes |
| R5 vehicle fusion of new members did not | vehicle +0.0023 against +0.0119 on B (0.19 x); 3D@0.7 0.198 -> 0.187 (B 0.180 -> 0.170) | fusions of seed members gain locally more than on the test frames |
| R5 realism transferred at 0.58 x | R 0.927 -> 0.933 (local +0.011): EMD 1.345 -> 1.182 (about 0.9 x) but FPD 0.733 -> 1.468 on the server while it fell locally | the local proxies do not hold the hidden reference's mean and covariance; judge EMD and FPD separately |
| S6 bag fusions transferred above every local projection | vehicle +0.014 (A +0.008, B +0.005), truck +0.014 (A +0.030, B flat); combined +0.0079 against an estimate of +0.0014 (B) and a projection of +0.0037 | the +0.01-on-B requirement of the class gate rejected both; the pooled A+B condition (vehicle +0.007, truck +0.024 on the final predictions, P 1.00) had the sign right; 3D mAP@0.7 fell 0.187 -> 0.165 although it rose on B (0.170 -> 0.221) |
## 10. Local evaluation and packaging

Everything here runs locally before an upload. The metrics are common to both tracks; the numbers are this track's.

### 10.1 Detection metric

As the scorer computes it (`scoring_program/detection_eval.py`, reproduced by [`common/bdc26/evalap.py`](../common/bdc26/evalap.py), checked by [`common/tests/test_official_parity.py`](../common/tests/test_official_parity.py)):
- per class and IoU threshold (0.5 primary, 0.7 reported): in each frame, predictions sorted by score each take the unused GT with the highest IoU and count as true positives if IoU >= threshold; predictions in frames without GT of the class are false positives; AP = mean over 40 recall points of the interpolated precision (R40 [R14](../docs/07-LITERATURE.md#r14-r40-average-precision); R11 reported);
- 3D IoU = oriented BEV polygon intersection x z overlap / union volume; class names match case-insensitively; a missing `class` defaults to "Car"; classes without test GT are excluded from the mean; no difficulty filter, no cap on the number of boxes;
- this track: mAP over vehicle, pedestrian and truck; test GT counts (kit `config.json`): vehicle 470, pedestrian 953, truck 124;
- consequences: never threshold scores aggressively (low-scored boxes cannot lower AP); per-class NMS matters (duplicates are false positives); a box may be emitted under several classes (hedges).

### 10.2 Realism metric

`scoring_program/metrics.py`, reproduced bit-for-bit by [`common/bdc26/realism.py`](../common/bdc26/realism.py): concatenate the 50 frames per side, mask to the range (inclusive; (0,0,0) points are inside), one RNG with seed 1234 draws 10,000 synthetic then 10,000 real points; CD (squared L2) and EMD = sqrt(W1) [R15](../docs/07-LITERATURE.md#r15-chamfer-and-earth-movers-distances) with POT [R18](../docs/07-LITERATURE.md#r18-pot) (10M iterations), unbiased RBF MMD with a median-heuristic bandwidth [R16](../docs/07-LITERATURE.md#r16-maximum-mean-discrepancy), FPD (Gaussian Frechet distance on xyz [R17](../docs/07-LITERATURE.md#r17-frechet-distance)).
```
R = 1 - mean( clip((CD-2)/28), clip(MMD/0.5), clip(EMD/5), clip(FPD/50) )        combined = 0.6 * clip(mAP / 0.7) + 0.4 * R
```
The real reference is 50 held-out frames we never see; locally we score against 5 sets of 50 legal real frames (`pcdet/realism-proxy-*`; 1-3 select, 4-5 are held out). Sensitivity of each term: [`docs/01-CHALLENGE-FACTS.md`](../docs/01-CHALLENGE-FACTS.md) Section 4.

### 10.3 Local estimates and how far to trust them

| Number | Tool | Meaning |
|---|---|---|
| realval-A mAP | `tune_and_eval.sh`, [`eval_predictions.py`](../common/tools/eval_predictions.py) | official metric on legal real frames; also the selection split, so optimistic |
| realval-B mAP | same | a second real split never used for selection |
| R (held-out proxies 4-5) | [`score_realism.py`](../common/tools/score_realism.py), [`select_realism_frames.py`](../common/tools/select_realism_frames.py) | official realism score against legal frames not used for any choice |
| combined estimate | `make_submission.sh` | `0.6 * clip(mAP / 0.7) + 0.4 * R`; **use the realval-B mAP** (Section 9.4) |

Local results of every model are in Section 7; the leaderboard calibration is in Section 9.

### 10.4 Packaging rules

| Rule (kit `submission_format.md`, scorer `score.py`) | How the packager ([`common/bdc26/submit.py`](../common/bdc26/submit.py)) handles it |
|---|---|
| exactly 50 `synthetic/*.bin`, float32 N x 3 (N x 4 accepted), each <= 1,500,000 bytes, total < ~75 MB | 50 x 50,000 points (600 KB each); validation errors stop packaging |
| `predictions.json`: exactly the 50 test IDs as keys (empty lists allowed); boxes of 7 floats, positive extents; score in [0, 1]; valid class strings | built from the routed or single-model predictions; every test ID present; classes from `track.yaml` |
| declaration.pdf (signed) or declaration.txt containing the verbatim statement | `declaration.txt` with the statement, `Team: $BDC_TEAM` (KarmaRV) and the date; validation fails on an empty team |
| the scorer reads `synthetic/`, `predictions.json` and `declaration.*` at the zip root | exactly these entries; `check_submission.py` rejects anything else (a nested folder, `__MACOSX/`, `.DS_Store`) |
| this track's frames | 31% of each realism frame are (0,0,0) nulls, as in the real frames (`track.yaml` `resample.null_fraction`) |

Each submission is a folder `<model>/submissions/<date>_<tag>/` with `manifest.json`, `synthetic_ids.txt`, the upload copy `v2x_<strategy>_submission.zip` (byte-identical to `submission.zip`, written by the packager; upload this file unchanged) and, after an upload, `codabench_<id>.json`; the working `submission.zip` is git-ignored; the upload copy is committed (from 3.0; the 1.0 entries as `submission_<track>.zip`), and the leaderboard entries are listed in [`RELEASES.md`](../RELEASES.md).

### 10.5 Server cost and the pre-upload check

Both competitions use CodaBench's shared default queue, Docker image `codalab/codalab-legacy:py312` and a 1,200 s execution limit. The worker unzips the upload into `/app/input/res`, `run.sh` pip-installs numpy, scipy, shapely and POT, then `score.py` validates and scores; on a validation error it prints `[scoring] FATAL: <reason>`, writes zeros and `Infinity` into `scores.json` and the reason into `detailed_results.html`, and exits 0.

[`check_submission.py`](../common/tools/check_submission.py) `--official` runs the kit's scorer on a zip with a legal stand-in reference (realism-proxy-4 frames; realval labels under the test IDs) and reports validity, realism, wall time and peak memory. This track's S1 zip: 95 s, 5.9 GB peak. Memory is the same for every participant (10,000-point subsamples; the dense MMD matrices dominate); time grows with the number of boxes (18,728 in S1); a per-class box cap of 100 would cost -0.0013 mAP on realval-A, so it stays off.

### 10.6 When a CodaBench submission fails or hangs

| Symptom on the Submissions page | Most likely cause | What to do |
|---|---|---|
| Failed within minutes, or a score row of zeros | validation (declaration, `synthetic/`, prediction IDs) | read the scoring stdout (`FATAL:` line) and `detailed_results.html`; fix with the packager, never by hand |
| Failed with no message after hours in the queue | as above, but the `Infinity` fields may not be storable; or the worker died | collect the logs; re-check the exact uploaded file with `check_submission.py` |
| Running or "Preparing submission..." for more than a day with no log | no worker ran it, or the worker was lost | cancel and upload the same checked zip once more; if it hangs again, write to the organizers with the ids |
| Failed after about 20 minutes | the 1,200 s limit | compare with the `--official` wall time; only then consider the box cap |

Collect for every failed or stuck submission: the id, the status tooltip, the expanded row (scoring stdout and stderr, detailed results), the exact uploaded file (`unzip -l`, `check_submission.py --official`), its name, size and checksum, and how it was made. History: [`docs/decisions/2026-10-06-s1-first-submission.md`](../docs/decisions/2026-10-06-s1-first-submission.md).

### 10.7 Submission budget

Development phase 5 per day / 100 in total (public leaderboard, ends Oct 30, 17:00 PDT); final phase **1 per day / 5 in total, hidden leaderboard, development submissions do not carry over**. One development submission per strategy to confirm the local estimate; never tune against the leaderboard (probing the realism reference is forbidden). The schedule: [`docs/05-SCHEDULE-AND-RUNBOOK.md`](../docs/05-SCHEDULE-AND-RUNBOOK.md); the gates, the progression tracker and the submission register: [`docs/decisions/README.md`](../docs/decisions/README.md#3-evaluation-protocol-and-gates) Sections 2-4.

## 11. Integrity rules and real-data uses

The code enforces, for this track:
- the detector is trained on synthetic data only (training sets are `pcdet/ut-*` and `pcdet/g1-*` built from UT frames; real sets are named `realval-*` and `realism-proxy-*` and no training config points at them);
- every real-data reader goes through `bdc26.guard.ForbiddenGuard`: the 100 forbidden frames (all in V2X-Real train scenes) plus +/-20 frames around each forbidden frame in its scene or in each candidate scene; every allowed access is logged with its purpose in `$BDC_DATA/v2x-track/real/access_log.csv`;
- the 50 test frames are read only for inference and format checks; nothing is fitted to kit data; no reference bundles; no realism probing; no warping of submitted frames toward real statistics.

Uses of legal real data (allowed by the Rules tab: "hyperparameter selection or domain adaptation, provided no forbidden frame is touched"), all to be disclosed in the report:

| Use | Record |
|---|---|
| Validation, post-processing selection, routing (realval-A and realval-B are scene-disjoint) | Sections 6.3-6.4 and 10.3 |
| Sensor measurement: the OS1-64 beam table from 23 legal unlabeled frames; field of view | [`docs/decisions/2026-09-30-s1-g1-generator.md`](../docs/decisions/2026-09-30-s1-g1-generator.md) |
| Label statistics for the generator: 70,818 legal walker boxes (positions, sizes, ground heights) | same |
| Test-ID resolution for the guard (point matching, format only) | [`data-v2x-track/README.md`](../data-v2x-track/README.md) |
| Research-phase exposure before the guard existed, and its follow-up check | [`docs/decisions/2026-09-30-rules-research-exposure.md`](../docs/decisions/2026-09-30-rules-research-exposure.md) |
| Downloading real data on the entrant's instruction; licence sign-off still open | [`docs/decisions/2026-09-30-rules-real-data-download.md`](../docs/decisions/2026-09-30-rules-real-data-download.md) |

All decision records: [`docs/decisions/`](../docs/decisions). Open questions for the organizers: [`docs/01-CHALLENGE-FACTS.md`](../docs/01-CHALLENGE-FACTS.md) Section 10.

## 12. Contributing

### 12.1 Code map (`common/bdc26/`, shared by both tracks)

| Module | What it does |
|---|---|
| [`config.py`](../common/bdc26/config.py) | `load_track("lumpi"\|"v2x")`: the track config (`data-<track>/track.yaml`) plus paths (`kit`, `ut`, `real`, `pcdet`, `gen`, `model_dir`) |
| [`guard.py`](../common/bdc26/guard.py) | `ForbiddenGuard`: blocks forbidden frames and windows, logs allowed access |
| [`io/`](../common/bdc26/io) | `fetch.py` (parallel, resumable downloads), readers `ut.py`, `lumpi.py`, `v2x.py`, `kit.py` |
| [`frames.py`](../common/bdc26/frames.py), [`boxes.py`](../common/bdc26/boxes.py), [`classmap.py`](../common/bdc26/classmap.py) | range masks, organizer-style resampling, nulls; box geometry, points in boxes, actor scaling; class maps |
| [`prep.py`](../common/bdc26/prep.py), [`pcdet_export.py`](../common/bdc26/pcdet_export.py) | UT frame -> training frame; OpenPCDet dataset writer with provenance card |
| [`render/pedsim.py`](../common/bdc26/render/pedsim.py), [`render/g1.py`](../common/bdc26/render/g1.py), [`density.py`](../common/bdc26/density.py) | engine G1: walker model, sensors, ray casting, ray-consistent insertion, placement; background density prior |
| [`detect/pcdet_dataset.py`](../common/bdc26/detect/pcdet_dataset.py), [`detect/postprocess.py`](../common/bdc26/detect/postprocess.py) | OpenPCDet dataset adapter; per-class post-processing |
| [`evalap.py`](../common/bdc26/evalap.py), [`realism.py`](../common/bdc26/realism.py) | the official detection and realism metrics |
| [`detect/pcdet_patches.py`](../common/bdc26/detect/pcdet_patches.py) | runtime fix of OpenPCDet's CenterHead label corruption (applied by `register()`) |
| [`scorecard.py`](../common/bdc26/scorecard.py), [`diagnostics.py`](../common/bdc26/diagnostics.py), [`detect/zcalib.py`](../common/bdc26/detect/zcalib.py) | strategy scorecard and paired frame bootstrap; error breakdowns (box errors, AP by range, recall by points); range-dependent z calibration |
| [`submit.py`](../common/bdc26/submit.py), [`registry.py`](../common/bdc26/registry.py) | packaging and validation; experiment log |

Tools ([`common/tools/`](../common/tools)): `pcdet_build_infos`, `pcdet_train`, `pcdet_predict`, `eval_predictions`, `tune_postprocess`, `route_predictions`, `fit_density_prior`, `select_realism_frames`, `score_realism`, `package_submission`, `check_submission`, `scorecard`, `pcdet_smoke`, `new_model`, `write_model_readmes`; each has a docstring with usage. `route_predictions.py` modes: `select` (`--rule joint`, `--calibrated`), `validate`, `calibrate`, `merge`.

### 12.2 Conventions
- Track facts live in `data-v2x-track/track.yaml`, never as constants in code.
- Dataset versions are immutable: build a new name and record it in [`data-v2x-track/README.md`](../data-v2x-track/README.md) Section 9 with the command that built it.
- A model is a folder (`python common/tools/new_model.py v2x <name> --from <model>`); outputs stay in git-ignored `output/`; decisions go to `registry.csv` and the model README.
- A strategy is named (root README Section 8, [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#8-strategy-routes-after-s1) Section 8); every CodaBench submission is listed under it in the root README Section 9 and in Section 9 here.
- Real data only through the guard, with a purpose string; a new use of real data gets a decision record before it influences a submission.
- Evaluate with the official metric (`bdc26.evalap.evaluate`, `bdc26.realism.score`); never report KITTI-style numbers as challenge numbers.
- Match the surrounding code; new dependencies go into `requirements.txt`.

### 12.3 Typical contributions
| Task | Where | Check |
|---|---|---|
| New generator feature | `common/bdc26/render/`, an option in `data-v2x-track/prepare_g1.py` | a statistic against legal real data; a new dataset version |
| New detector (S2, S4, S6) | a new model folder; `train/pcdet_model.yaml` | `tune_and_eval.sh`, then a member of a routed or fused model |
| New post-processing or fusion knob (S3) | `common/bdc26/detect/`, `common/tools/tune_postprocess.py` | realval-A gain that holds on realval-B |
| Metrics or packaging fix | `evalap.py`, `realism.py`, `submit.py` | `python -m pytest -q common/tests`, including the official-parity tests |

### 12.4 Running long jobs on the shared server
- Check `nvidia-smi` and `df -h` first; pin GPUs with `CUDA_VISIBLE_DEVICES` (LUMPI 0-3, V2X 4-7 match the NUMA nodes).
- Generation: `OMP_NUM_THREADS=1` with many workers. Training: `--workers 6` per GPU.
- Stop jobs by PID, not by pattern; never edit a shell script while a run of it is executing.
- Run the tests before every commit.
