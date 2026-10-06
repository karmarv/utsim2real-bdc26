# Track 2 models: V2X-Real (`model-v2x-track/`)

> Modeling for Track 2 (CodaBench 16685): the approaches we considered, the selected model and why, and its full lifecycle (preparation, training, validation, test inference, ablations, evaluation, submission). Data, the sensor and the generator are in [`data-v2x-track/README.md`](../data-v2x-track/README.md); the project-wide developer guide is the [root README](../README.md).

## 0. At a glance

| | |
|---|---|
| Selected model | [`routed-g1`](routed-g1): vehicle from [`pointpillars-g1v2`](pointpillars-g1v2), pedestrian from [`pointpillars-g1v3`](pointpillars-g1v3), truck from [`pointpillars-ut`](pointpillars-ut) |
| Real validation (official metric, tuned) | **realval-A mAP 0.572**, realval-B 0.520 |
| Local combined estimate | **0.858** (A) / 0.814 (B); ECCV winner 0.746, live leader 0.611 |
| Ready to upload | [`routed-g1/submissions/2026-10-02_first/submission.zip`](routed-g1/submissions) (git-ignored; validated by the kit's `local_eval.py`) |
| Realism of the submitted frames | R = 0.919 on held-out legal proxies, official scorer (frames from the FOV-masked `g1-v3` val split with 31% nulls) |
| Submit | Section 6.7 |
| Experiment log | [`registry.csv`](registry.csv) |

## 1. Folder conventions and models

Same conventions as Track 1 ([`model-lumpi-track/README.md`](../model-lumpi-track/README.md) Section 1): one folder per model with `model.yaml`, `README.md`, `train/`, `validation/`, `test/`, `submissions/`; experiment log `registry.csv`; new models with `python common/tools/new_model.py v2x <name> --from <existing>`.

| Model | Data | Role | Status |
|---|---|---|---|
| [`pointpillars-ut`](pointpillars-ut) | `pcdet/ut-v1` (UT only; riders are the only pedestrians) | baseline; routed member for truck | trained 40 epochs, tuned |
| [`pointpillars-g1`](pointpillars-g1) | `pcdet/g1-v1` (walkers v1, free placement, gain 1.5) | first G1 model | trained 40 epochs, tuned |
| [`pointpillars-g1v2`](pointpillars-g1v2) | `pcdet/g1-v2` (walker v2 body) | routed member for vehicle | trained 40 epochs, tuned |
| [`pointpillars-g1v3`](pointpillars-g1v3) | `pcdet/g1-v3` (walkers calibrated on legal real walkers, FOV-masked UT) | routed member for pedestrian | trained 40 epochs, tuned |
| [`routed-g1`](routed-g1) | members above | **selected** | first submission packaged |

## 2. Modeling approaches considered

Track-specific constraints: one sensor (OS1-64), 35k valid points per frame plus 31% nulls; a sloped campus (box bottoms from -1 to -7 m in the sensor frame); **pedestrian is 62% of the test objects** and mixes walkers (0.71 x 0.72 x 1.73 m) with riders (about 1.8 m long); trucks are large (median 8.2 m).

| Approach | Pros here | Cons here | Verdict |
|---|---|---|---|
| **PointPillars** with multi-mode anchors | fast (1 h per run on 4 GPUs); one pillar spans the whole z range, so the slope does not need a z prior; the ECCV winner's bimodal vehicle and 3-mode truck anchors took combined from 0.515 to 0.626 | coarse for small objects | **selected base detector** |
| SECOND / Voxel R-CNN | finer z; better on roadside pedestrians in the literature | the slope (18 m vertical spread) makes voxel heights and anchors harder | candidate for pedestrian routing |
| CenterPoint | strong small-object head | heatmap z priors suffer from the slope; the ECCV winner found it no better than pillars here | candidate |
| DSVT / transformers | the ECCV runner-up used DSVT experts per class | heavy; needs more varied synthetic data | later |
| Ground-plane canonicalization | removes the slope (RoboSense 2025 reported +5 AP) | needs a per-frame ground fit on real frames (legal: unlabeled sensor data) | next experiment |
| Per-class routing / fusion | per-class AP is independent; walker versions differ by class | needs real validation (available since the kit) | **used** |

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
python common/tools/package_submission.py model-v2x-track/routed-g1 --tag first --record <codabench_id> <leaderboard.json>
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

## 8. Experiment log and next experiments

| # | Question | Result / plan |
|---|---|---|
| E1 | Resample UT to the real valid count (35k) | in all versions |
| E2 | Walkers (G1) vs riders only | done: pedestrian 0 -> 0.118 |
| E3 | Walker body v1 vs v2 | done: pedestrian 0.118 -> 0.173 |
| E4 | Walkers calibrated on legal real walkers + FOV mask | done: pedestrian 0.173 -> 0.266; realism 0.901 -> 0.919 |
| E5 | Pedestrian NMS and re-centering | tuned per class (Section 6.3) |
| E6 | Ground-plane canonicalization of the sloped scene | next |
| E7 | Architecture routing for pedestrians (SECOND / CenterPoint) | next (M10) |
| E8 | Background density calibration for realism (as Track 1) | next (data guide Section 12) |
| E9 | TTA and weighted box fusion | next (M11) |

## 9. Submission log

| Date | Model / tag | CodaBench id | Local mAP (A / B) | Local R | LB mAP | LB R | LB combined | Note |
|---|---|---|---|---|---|---|---|---|
| 2026-10-02 | `routed-g1` / `first`, hand-edited copy uploaded as `submission_v2x_20261002.zip` | 957439 | 0.572 / 0.520 | 0.919 | | | | Running for 4 days with no log ("Preparing submission..."), cancelled 2026-10-06; counted (1 of 100 used); root README Section 9.1 |
| 2026-10-06 | `routed-g1` / `first`, team KarmaRV | (to upload) | 0.572 / 0.520 | 0.919 | | | | `check_submission.py --set-team KarmaRV` changed only declaration.txt; kit scorer valid in 95 s, 5.9 GB peak; estimate 0.858 |
