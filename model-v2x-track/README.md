# Track 2 models: V2X-Real (`model-v2x-track/`)

> Modeling for Track 2 (CodaBench 16685): the approaches we considered, the selected model and why, and its full lifecycle (preparation, training, validation, test inference, ablations, evaluation, submission). Data, the sensor and the generator are in [`data-v2x-track/README.md`](../data-v2x-track/README.md); the project-wide developer guide is the [root README](../README.md).

## 0. At a glance

| | |
|---|---|
| Selected model | [`routed-g1`](routed-g1): vehicle from [`pointpillars-g1v2`](pointpillars-g1v2), pedestrian from [`pointpillars-g1v3`](pointpillars-g1v3), truck from [`pointpillars-ut`](pointpillars-ut) |
| Real validation (official metric, tuned) | **realval-A mAP 0.572**, realval-B 0.520 |
| Local combined estimate | 0.858 (A) / 0.814 (B); ECCV winner 0.746 |
| CodaBench (current entry) | **972563: combined 0.7855** (mAP 0.4869, R 0.9203), S1+C1 ([`routed-g1z`](routed-g1z)), rank 1 on 2026-10-09 (Section 9) |
| CodaBench (previous) | 965633: combined 0.7665 (mAP 0.4648), S1 ([`routed-g1`](routed-g1)), 2026-10-06 |
| Submitted zip | current entry: [`routed-g1z/submissions/2026-10-09_zcal/submission_v2x.zip`](routed-g1z/submissions/2026-10-09_zcal/submission_v2x.zip) (tag 1.0); S1: `submission_v2x_karmarv.zip` (release 0.1) |
| Realism of the submitted frames | R = 0.919 on held-out legal proxies, official scorer (frames from the FOV-masked `g1-v3` val split with 31% nulls) |
| Submit | Section 6.7 |
| Strategy | S1 submitted; next S2 (root README Section 8, [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#8-strategy-routes-after-s1) Section 8) |
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
| [`routed-g1z`](routed-g1z) | `routed-g1` + range-dependent z calibration (C1) | **selected** (S1+C1) | submitted (972563, **0.7855**; Section 7.4) |

## 2. Modeling approaches considered

Track-specific constraints: one sensor (OS1-64), 35k valid points per frame plus 31% nulls; a sloped campus (box bottoms from -1 to -7 m in the sensor frame); **pedestrian is 62% of the test objects** and mixes walkers (0.71 x 0.72 x 1.73 m) with riders (about 1.8 m long); trucks are large (median 8.2 m).

| Approach | Pros here | Cons here | Verdict |
|---|---|---|---|
| **PointPillars** with multi-mode anchors | fast (1 h per run on 4 GPUs); one pillar spans the whole z range, so the slope does not need a z prior; the ECCV winner's bimodal vehicle and 3-mode truck anchors took combined from 0.515 to 0.626 | coarse for small objects | **selected base detector** |
| SECOND / Voxel R-CNN | finer z; better on roadside pedestrians in the literature | the slope (18 m vertical spread) makes voxel heights and anchors harder | Voxel R-CNN is the lighter option of strategy S4 ([`docs/02` 8.4](../docs/02-STRATEGY.md#84-s4-two-stage-refinement)) |
| CenterPoint | strong small-object head | heatmap z priors suffer from the slope; the ECCV winner found it no better than pillars here | **strategy S2 (next)**: pedestrian specialist ([`docs/02` 8.2](../docs/02-STRATEGY.md#82-s2-center-routed-small-objects)) |
| DSVT / transformers | the ECCV runner-up used DSVT experts per class | heavy; needs more varied synthetic data; scored below S1 here | strategy S6, only if time remains |
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

## 8. Experiment log and next experiments

| # | Question | Result / plan |
|---|---|---|
| E1 | Resample UT to the real valid count (35k) | in all versions |
| E2 | Walkers (G1) vs riders only | done: pedestrian 0 -> 0.118 |
| E3 | Walker body v1 vs v2 | done: pedestrian 0.118 -> 0.173 |
| E4 | Walkers calibrated on legal real walkers + FOV mask | done: pedestrian 0.173 -> 0.266; realism 0.901 -> 0.919 |
| E5 | Pedestrian NMS and re-centering | tuned per class (Section 6.3) |
| E6 | Ground-plane canonicalization of the sloped scene | part of the S4 diagnosis (`docs/02` Section 8.1.2 D2 and Section 8.4 step 0) |
| E7 | Architecture routing for pedestrians (CenterPoint) | **next: strategy S2** |
| E8 | Background density calibration for realism (as Track 1) | next (data guide Section 12) |
| E9 | TTA and weighted box fusion, height TTA | strategy S3 |

## 9. Submission log

| Date | Model / tag | CodaBench id | Local mAP (A / B) | Local R | LB mAP | LB R | LB combined | Note |
|---|---|---|---|---|---|---|---|---|
| 2026-10-02 | `routed-g1` / `first`, hand-edited copy uploaded as `submission_v2x_20261002.zip` | 957439 | 0.572 / 0.520 | 0.919 | | | | Running for 4 days with no log ("Preparing submission..."), cancelled 2026-10-06; counted (1 of 100 used); Section 10.6 |
| 2026-10-06 | `routed-g1` / `first`, team KarmaRV, uploaded unchanged as `submission_v2x_karmarv.zip` | 965633 | 0.572 / 0.520 | 0.919 | **0.4648** | **0.9203** | **0.7665** | strategy S1; rank 1 of 34 (next 0.6114); server record [`codabench_965633.json`](routed-g1/submissions/2026-10-02_first/codabench_965633.json) |
| 2026-10-09 | `routed-g1z` / `zcal` (S1+C1 z calibration), the packaged zip unchanged | 972563 | 0.585 / 0.537 | 0.919 | **0.4869** | **0.9203** | **0.7855** | strategy S1+C1; rank 1 of 19 (next 0.6616); scored in about 4 min; server record [`codabench_972563.json`](routed-g1z/submissions/2026-10-09_zcal/codabench_972563.json); [decision record](../docs/decisions/2026-10-09-s1-closeout-z-calibration.md) |

### 9.1 Local vs leaderboard per class (3D AP@0.5 R40)

| | mAP | vehicle | pedestrian | truck | BEV mAP@0.5 |
|---|---|---|---|---|---|
| **972563 leaderboard (S1+C1)** | **0.4869** | 0.605 | 0.281 | 0.574 | 0.5696 |
| S1+C1 realval-A / realval-B | 0.585 / 0.537 | 0.641 / 0.685 | 0.290 / 0.252 | 0.822 / 0.673 | |
| 965633 leaderboard (S1) | 0.4648 | 0.585 | 0.235 | 0.574 | 0.5696 |
| S1 realval-A / realval-B | 0.572 / 0.520 | 0.627 / 0.662 | 0.266 / 0.226 | 0.822 / 0.673 | |
| leaderboard / realval-B (S1 -> S1+C1) | 0.89 -> 0.91 | 0.88 -> 0.88 | 1.04 -> 1.12 | 0.85 | |

The z calibration changed only z, so BEV AP and realism are identical; it gained more on the test frames than on realval-B for pedestrians (+0.046 vs +0.026) and about the same for vehicles (+0.020 vs +0.023), and the leaderboard BEV-3D gap fell from 0.105 to 0.083.

Realism on the server: CD 2.215, MMD 0.00329, EMD 1.414, FPD 1.092, R 0.9203 (local proxy 4: 2.181, 0.00384, 1.441, 1.126, 0.9188). Vehicle and pedestrian transfer close to realval-B; the truck route (the UT-only run, chosen on realval-A) loses the most (analysis: Section 9.4; next strategy: root README Section 8 and [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#8-strategy-routes-after-s1) Section 8).

### 9.2 Artifacts

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
| leaderboard (965633 and 972563, identical frames) | 2.215 | 0.00329 | 1.414 | 1.092 | **0.9203** |
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
| Local estimate was optimistic | estimate A / B / leaderboard: S1 0.858 / 0.814 / 0.767; S1+C1 0.869 / 0.828 / 0.786 | report the realval-B estimate; it overstates by about 0.045 |

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

Each submission is a folder `<model>/submissions/<date>_<tag>/` with `manifest.json`, `synthetic_ids.txt` and, after an upload, `codabench_<id>.json`; the working `submission.zip` is git-ignored; the zip of a leaderboard entry is committed beside it as `submission_<track>.zip` and listed in [`RELEASES.md`](../RELEASES.md).

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
| [`scorecard.py`](../common/bdc26/scorecard.py), [`diagnostics.py`](../common/bdc26/diagnostics.py), [`detect/zcalib.py`](../common/bdc26/detect/zcalib.py) | strategy scorecard and paired frame bootstrap; error breakdowns (box errors, AP by range, recall by points); range-dependent z calibration |
| [`submit.py`](../common/bdc26/submit.py), [`registry.py`](../common/bdc26/registry.py) | packaging and validation; experiment log |

Tools ([`common/tools/`](../common/tools)): `pcdet_build_infos`, `pcdet_train`, `pcdet_predict`, `eval_predictions`, `tune_postprocess`, `route_predictions`, `fit_density_prior`, `select_realism_frames`, `score_realism`, `package_submission`, `check_submission`, `scorecard`, `new_model`, `write_model_readmes`; each has a docstring with usage.

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
