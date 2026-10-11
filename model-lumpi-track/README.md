# Track 1 models: LUMPI (`model-lumpi-track/`)

> Modeling for Track 1 (CodaBench 16684): the approaches we considered, the selected model and why, and the selected model's full lifecycle (preparation, training, validation, test inference, ablations, evaluation, submission). Data and the generator are in [`data-lumpi-track/README.md`](../data-lumpi-track/README.md); the project-wide developer guide is the [root README](../README.md).

## 0. At a glance

| | |
|---|---|
| Selected model | [`routed-g4`](routed-g4) (S4): S3 portfolio plus Bicycle fused from the two-stage members (Voxel R-CNN, PV-RCNN++); per-class score floors (Section 7.7); S1 baseline [`routed-g1`](routed-g1) (two PointPillars models on engine-G1 data) |
| Real validation (official metric, tuned) | **realval-A mAP 0.313**, realval-B 0.188, late-A 0.304 (S4); S3 0.301 / 0.184; S1 0.260 / 0.166 (Section 7) |
| Realism of the submitted frames | R = 0.906 on held-out legal proxies, official scorer (raw UT frames: 0.59) |
| Local combined estimate | 0.523 (B) for S4; leaderboard 0.5040 (Section 9.4); ECCV winner 0.479 |
| Competition | **rank 1 of 18** (S4, 0.5040); second Raj Patil 0.4794 (977527) with mAP 0.1196 but realism R 0.942 (ours 0.891): LUMPI realism is the open lever ([`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#87-parallel-and-gated-work) Section 8.7) |
| CodaBench | **975871 (S4): combined 0.5040** (mAP 0.1721, R 0.8912), rank 1 of 18 on 2026-10-11; S5 upload 978931 scored 0.5039 (not listed, not confirmed; Section 7.8); earlier 974348 (S3, 0.5015 by its log), 965614 (S1, 0.4728) (Section 9; root README Section 9) |
| Submitted zip | current entry S4: [`routed-g4/submissions/2026-10-10_s4/lumpi_s4_submission.zip`](routed-g4/submissions/2026-10-10_s4/lumpi_s4_submission.zip) (tag 4.0); S5 (not listed): [`routed-g5/submissions/2026-10-11_s5/lumpi_s5_submission.zip`](routed-g5/submissions/2026-10-11_s5/lumpi_s5_submission.zip) (tag 5.0); S3: [`lumpi_s3_submission.zip`](routed-g3/submissions/2026-10-09_s3/lumpi_s3_submission.zip) (tag 3.0); S1: [`submission_lumpi.zip`](routed-g1/submissions/2026-10-02_first/submission_lumpi.zip) (tag 1.0; uploaded as `submission_lumpi_karmarv.zip`, release 0.1) |
| Submit | `bash model-lumpi-track/routed-g4/test/make_submission.sh <tag> [team]` (Section 6.7; team defaults to `$BDC_TEAM`) |
| Strategy | S1, S3 and **S4 submitted** (Sections 7.6, 7.7; S4 below its upload gate, uploaded by the entrant's call); S2 done, below the upload gate (Section 7.5); **S5 submitted, not confirmed** (Section 7.8; S4 stays the entry); next R3 (root README Section 8, [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#8-strategy-routes-after-s1) Section 8) |
| Experiment log | [`registry.csv`](registry.csv) (one row per evaluation and submission) |

## 1. Folder conventions

One folder per model. A model is a detector configuration plus the dataset version it was trained on.

```
model-lumpi-track/
├── README.md                 this file
├── registry.csv              experiment log (bdc26.registry), appended by eval_predictions.py and package_submission.py
└── <model>/
    ├── README.md             what this model is, how to run it, its results
    ├── model.yaml            model card read by the tools: track, data.train, data.realval, realism_frames, members (routed)
    ├── train/                pcdet_model.yaml (+ _BASE_CONFIG_ pcdet_dataset.yaml), train.sh; output/ (git-ignored: ckpt, logs, tensorboard)
    ├── validation/           evaluate.sh, tune_and_eval.sh; output/ (git-ignored predictions); results/ (tracked JSON, local_scores.json)
    ├── test/                 postprocess.yaml (selected on real val), predict.sh, make_submission.sh, synthetic_ids.txt; output/ (git-ignored)
    └── submissions/<date>_<tag>/   manifest.json, synthetic_ids.txt, codabench_<id>.json, <track>_<strategy>_submission.zip (tracked; 1.0 entries: submission_<track>.zip); submission.zip (git-ignored)
```

Create a model with `python common/tools/new_model.py lumpi <name> --from <existing>` (copies configs, never outputs), then edit `model.yaml` and `train/pcdet_model.yaml`.

| Model | Data | Role | Status |
|---|---|---|---|
| [`pointpillars-ut`](pointpillars-ut) | `pcdet/ut-v1` (UT only, actors x 1/0.78, Van -> Car) | baseline and ablation (what G1 adds) | run2 trained 40 epochs |
| [`pointpillars-g1`](pointpillars-g1) | `pcdet/g1-v2` (walkers v1, Van as Van, calibrated density) | routed member | trained 40 epochs, tuned |
| [`pointpillars-g1v3`](pointpillars-g1v3) | `pcdet/g1-v3` (walkers v2) | routed member | trained 40 epochs, tuned |
| [`routed-g1`](routed-g1) | members above | S1 | submitted (965614) |
| [`centerpoint-g1v3`](centerpoint-g1v3) | `pcdet/g1-v3` | S2 member: CenterPoint, stride 8 | trained 40 epochs (label fix), tuned; wins Bicycle (Section 7.5) |
| [`centerpoint-s4-g1v3`](centerpoint-s4-g1v3) | `pcdet/g1-v3` | S2 variant: CenterPoint, stride 4 | trained 40 epochs, tuned; no class won |
| [`routed-g2`](routed-g2) | `routed-g1` members + `cp` (+ `cp4`) | S2 candidate | Bicycle from `cp`; below the upload gate (+0.003); package `2026-10-09_s2/lumpi_s2_submission.zip` checked, not uploaded |
| [`routed-g3`](routed-g3) | `routed-g2` members and their TTA variants (`<member>_tta`) | S3 | submitted (974348, 0.5015 by its scorer log, never listed; Section 7.6) |
| [`voxelrcnn-g1v3`](voxelrcnn-g1v3) | `pcdet/g1-v3` | S4 member: Voxel R-CNN (CenterPoint stage 1, voxel RoI pooling) | trained 40 epochs, per-class score blend, tuned plain and TTA (Section 7.7) |
| [`pvrcnnpp-g1v3`](pvrcnnpp-g1v3) | `pcdet/g1-v3` | S4 member: PV-RCNN++ (CenterPoint stage 1, keypoint RoI pooling) | trained 40 epochs, per-class score blend, tuned plain and TTA (Section 7.7) |
| [`routed-g4`](routed-g4) | `routed-g3` members + `vr`, `pv` and their TTA variants | **selected** (S4) | submitted (975871, **0.5040**, rank 1; below its upload gate; Section 7.7) |
| [`voxelrcnn-gblobs-g1v3`](voxelrcnn-gblobs-g1v3) | `pcdet/g1-v3` | S5 run a: Voxel R-CNN with GBlobs inputs (cell covariance) | trained, tuned plain and TTA; below its parent alone, used in the Car fusion (Section 7.8) |
| [`voxelrcnn-ros-g1v3`](voxelrcnn-ros-g1v3) | `pcdet/g1-v3` | S5 run b: Voxel R-CNN with class-wise object scaling | trained, tuned plain and TTA; Bus route, Bicycle fusion (Section 7.8) |
| [`pvrcnnpp-ros-g1v3`](pvrcnnpp-ros-g1v3) | `pcdet/g1-v3` | S5 extension: PV-RCNN++ with object scaling | trained, tuned plain and TTA; Truck, Bicycle and Car fusions |
| [`pointpillars-ros-g1v3`](pointpillars-ros-g1v3) | `pcdet/g1-v3` | S5 extension: PointPillars g1v3 with object scaling | trained, tuned plain and TTA; Truck and Car fusions |
| [`routed-g5`](routed-g5) | `routed-g4` members + the four S5 runs (plain and TTA) | S5 | submitted (978931, 0.5039: 0.00007 below S4, not confirmed; Section 7.8) |

## 2. Modeling approaches considered

What matters for this challenge (from [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md) and the competitor reports in [`docs/01-CHALLENGE-FACTS.md`](../docs/01-CHALLENGE-FACTS.md) Section 7):
- the detector is trained on synthetic data only and scored on real data, so **robustness to the sim-to-real gap** matters more than benchmark accuracy;
- the score is a 7-class mean of 3D AP at IoU 0.5, so **small and rare classes** (Person, Bicycle, Van, Truck, Bus, Motorcycle) count as much as Car;
- every architecture change needs fast iteration (many generator versions, real-validation loops) on shared GPUs.

| Approach | Pros for this challenge | Cons for this challenge | Verdict |
|---|---|---|---|
| **PointPillars** (anchor-based, pillars) | fast (40 epochs on 9k frames in about 2 h on 4 GPUs); robust to density changes; multi-mode anchors fit fixed size conventions; won the ECCV edition on both tracks | coarse z (one pillar spans 10 m); weaker on small objects in the literature (InScope pedestrian AP 23.8 vs 49.6 for CenterPoint) | **selected as the base detector** (best speed / robustness trade-off; small-class weakness addressed with synthetic Persons and per-class post-processing) |
| SECOND (sparse voxels, anchors) | finer z than pillars; beats pillars on roadside pedestrians (DAIR-V2X-I) | slower; voxel features more sensitive to density mismatch | the sparse voxel backbone of the S2 CenterPoint members |
| CenterPoint (center heads) | strong on small objects; no anchor tuning | heatmap head sensitive to density and box-convention shifts; the ECCV winner found it no better than pillars here | **strategy S2 (next)**: Person, Bicycle, Motorcycle specialists ([`docs/02` 8.2](../docs/02-STRATEGY.md#82-s2-center-routed-small-objects)) |
| PV-RCNN++ / Voxel R-CNN (two-stage) | top accuracy on roadside benchmarks | 3-5x slower; refinement stage may relearn synthetic box conventions | strategy S4 ([`docs/02` 8.4](../docs/02-STRATEGY.md#84-s4-two-stage-refinement)) |
| VoxelNeXt / DSVT / LION / HEDNet (fully sparse, transformers) | state-of-the-art; DSVT experts were the ECCV runner-up's backbone | heavy; needs more data diversity than one 10k-frame twin; LION needs its own fork | strategy S6, only if time remains ([`docs/02` 8.6](../docs/02-STRATEGY.md#86-s6-sparse-transformer-experts)) |
| Domain adaptation (self-training on real frames, BN adaptation) | can close the gap without labels | self-training on real frames is a gray area ([`01`](../docs/01-CHALLENGE-FACTS.md) Section 3.1); the detector must stay "trained on synthetic data only" | not used |
| Ensembles / per-class routing / WBF | per-class AP is independent, so a class can come from the model that is best for it; run-to-run variance is large on rare classes | needs a real validation set to choose routes (we have one: realval-A/B) | **used** (routing in S1); fusion and TTA are strategy S3 ([`docs/02` 8.3](../docs/02-STRATEGY.md#83-s3-fused-portfolio-with-tta)) |

**Why the selected model.** `routed-g1` takes each class from the better of two PointPillars G1 runs on real validation. Compared with a single PointPillars model it gains where training variance is large (Bicycle, Truck, Bus, Motorcycle) and uses walker v2 for Person, which transfers better to other measurements. Compared with heavier architectures it trains in 2 hours, which let us iterate on the generator (the biggest lever: synthetic Persons, Van class, density calibration). Cons: two forward passes at inference; routing is chosen on realval-A, the same measurement the test frames come from, so realval-A numbers are optimistic (realval-B is the check); PointPillars' coarse z limits 3D IoU for small objects (Person boxes are predicted too tall; the size calibration in post-processing partly compensates).

## 3. The detector configuration (`pointpillars-g1`, `pointpillars-g1v3`)

| Setting | Value | Why |
|---|---|---|
| Framework | OpenPCDet 0.6.0 (commit 233f849) with the `BDCDataset` adapter ([`common/bdc26/detect/pcdet_dataset.py`](../common/bdc26/detect/pcdet_dataset.py)) | OpenPCDet's 7-DoF box convention is the challenge's |
| Input | xyz only, 50,000 points in `[-40, -40, -5, 40, 40, 5]` | the test frames carry no intensity |
| Pillars | 0.15625 m, 512 x 512 grid, one pillar spans z [-5, 5], 32 points per pillar, 40,000 pillars | a 50k-point LUMPI frame fills about 31k pillars |
| Backbone / head | PillarVFE 64 -> BaseBEVBackbone [64, 128, 256] -> AnchorHeadSingle with direction classifier | standard PointPillars |
| Anchors (l, w, h; bottom at -2.15 m) | Person 0.78 x 0.75 x 1.90 (legal M4 median); Car 4.79 x 1.99 x 1.58; Bicycle 1.76 x 0.6 x 1.73; Motorcycle 2.19 x 0.87 x 1.53; Bus 10.27 x 3.94 x 4.25; Truck 7.94 x 2.89 x 3.46; Van 5.92 x 1.99 x 2.43; Unknown as Car | training-label medians (rescaled UT boxes, generator boxes) |
| Augmentation | GT-sampling Person 6, Car 6, Bicycle 10, Motorcycle 6, Bus 3, Truck 6, Van 6 (min 5 points); flips x/y; rotation +/-10 deg; scaling 0.95-1.05 | rare classes need GT-sampling |
| Optimization | 40 epochs, batch 6 per GPU on 4 GPUs, adam_onecycle LR 0.003, weight decay 0.01, `--fix_random_seed` | the one-cycle schedule matters: epoch 11 (high LR) found only 28% of real Persons, epoch 40 81% |
| OpenPCDet NMS | score 0.01, class-agnostic NMS 0.9, 1,000 boxes | keeps near-raw outputs; real NMS is per class in post-processing |
| Post-processing ([`common/bdc26/detect/postprocess.py`](../common/bdc26/detect/postprocess.py), `test/postprocess.yaml`) | per class: score floor, top-400 pre-NMS, rotated NMS IoU, re-centering on in-box points, size scale about the bottom centre, z offset; cross-class hedged copies | all selected on real validation (Section 6.3) |

## 4. Engine G1 data in one paragraph

UT-LUMPI frames with the actor scale fix, plus about 16 procedural walkers per frame ray-cast with the five real Measurement4 lidars, placed at legal real Person positions with real box sizes, inserted with per-sensor occlusion; UT Van trained as Van; background resampled toward the real spatial density. Full description and checks: [`data-lumpi-track/README.md`](../data-lumpi-track/README.md) Section 8.7.

## 5. Selected model lifecycle at a glance

```mermaid
flowchart TB
  P[6.1 Preparation<br/>g1-v2, g1-v3 + infos] --> T[6.2 Training<br/>2 x PointPillars, 40 epochs, 4 GPUs]
  T --> V[6.3 Validation<br/>raw preds on realval A/B<br/>two-phase tuner -> postprocess.yaml]
  V --> R[6.4 Routing<br/>best member per class on A, ties by B]
  R --> I[6.5 Test inference<br/>50 kit frames, both members]
  I --> E[6.6 Evaluation<br/>official metric, realism on held-out proxies]
  E --> S[6.7 Submission<br/>zip, validation, upload, record]
  V -.-> A[Ablations, Section 7]
```

## 6. Selected model lifecycle, step by step

All commands from the repository root after `source common/env/activate.sh`. GPU numbers are examples (`CUDA_VISIBLE_DEVICES`).

### 6.1 Preparation
```bash
python data-lumpi-track/prepare_g1.py --name g1-v1 --workers 64                                   # density-prior input
python common/tools/fit_density_prior.py --track lumpi --real pcdet/realval-v1 --syn pcdet/g1-v1 --out gen/density_prior_v1.npz
OMP_NUM_THREADS=1 python data-lumpi-track/prepare_g1.py --name g1-v2 --density-prior gen/density_prior_v1.npz --workers 64
OMP_NUM_THREADS=1 python data-lumpi-track/prepare_g1.py --name g1-v3 --walker v2 --density-prior gen/density_prior_v1.npz --workers 64
```
Prerequisites (data guide Section 8): UT-LUMPI, real labels and frames, `pcdet/realval-v1`. The infos and GT database are built by `train.sh` on first use.

### 6.2 Training
```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 bash model-lumpi-track/pointpillars-g1/train/train.sh 4 run1 --fix_random_seed --workers 6
CUDA_VISIBLE_DEVICES=4,5,6,7 bash model-lumpi-track/pointpillars-g1v3/train/train.sh 4 run1 --fix_random_seed --workers 6
```
`train.sh NGPUS TAG [OpenPCDet train.py flags]` builds missing infos, then runs OpenPCDet's `tools/train.py` through [`common/tools/pcdet_train.py`](../common/tools/pcdet_train.py) (registers `BDCDataset`, injects the dataset path from `model.yaml`). Outputs: `train/output/pcdet_model/<TAG>/ckpt/checkpoint_epoch_N.pth`, `train_*.log`, `tensorboard/`. About 2 h on 4 A6000s (up to 45 GB per GPU at batch 6); at the end OpenPCDet evaluates the synthetic val split (`g1-v2` val: mAP 0.800), which only checks that training converged.

### 6.3 Validation and post-processing selection
```bash
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/pointpillars-g1/validation/tune_and_eval.sh \
    model-lumpi-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth
```
[`tune_and_eval.sh`](pointpillars-g1/validation/tune_and_eval.sh) runs:
1. raw predictions (OpenPCDet outputs, score >= 0.01) on realval-A (`val`) and realval-B (`valB`) with [`pcdet_predict.py --raw`](../common/tools/pcdet_predict.py);
2. [`tune_postprocess.py`](../common/tools/tune_postprocess.py), per class and independently (per-class AP does not depend on other classes):
   - phase 1, detector behaviour: NMS IoU in {0.01, ..., 0.7}, re-centering in {0, 0.25, 0.5} for Person/Bicycle/Motorcycle; kept only if realval-B does not drop by more than 0.005;
   - phase 2, box convention: z offset in {-0.3, ..., 0.3} m and size scale {0.85, ..., 1.16} (length/width together, then height), only for classes with 500+ GT in A; not guarded by B because conventions differ by measurement (M4 Person boxes 0.77 m long, M5-6 0.96-0.99 m);
   - greedy cross-class hedges (discounted copies, factors {0.1, 0.3, 0.6}) where they add at least 0.002 AP on A;
   - the search uses the fast float32 IoU; the result is written to `test/postprocess.yaml` (previous config kept as `.prev`, report in `test/postprocess.report.json`);
3. post-processed predictions on A and B, scored with the official metric ([`eval_predictions.py`](../common/tools/eval_predictions.py), exact IoUs), registry rows, `validation/results/local_scores.json`.

### 6.4 Routing
```bash
python common/tools/route_predictions.py select model-lumpi-track/routed-g1
```
For every class: the member with the best realval-A AP; within 0.005 of the best, the one with the higher realval-B AP. The route is written into [`routed-g1/model.yaml`](routed-g1/model.yaml) and the table into `routed-g1/validation/results/route_table.json`. Verify by merging the members' validation predictions (`route_predictions.py merge ... --pred g1=... --pred g1v3=...`) and scoring them with `eval_predictions.py`.

### 6.5 Test inference
`pcdet_predict.py <member> --ckpt <ckpt> --frames kit` runs each member on the 50 kit frames with its own `test/postprocess.yaml`; `route_predictions.py merge` keeps each class from its routed member. Both steps are inside `make_submission.sh` (6.7). The test frames are used for nothing else.

### 6.6 Evaluation
- **Detection:** [`common/bdc26/evalap.py`](../common/bdc26/evalap.py) implements the official scorer exactly (VOC-style greedy matching, 40-point interpolation, classes without GT excluded); parity with the kit's `scoring_program` is a unit test ([`common/tests/test_official_parity.py`](../common/tests/test_official_parity.py)).
- **Realism:** [`common/bdc26/realism.py`](../common/bdc26/realism.py) reproduces `scoring_program/metrics.py` bit-for-bit; [`score_realism.py`](../common/tools/score_realism.py) scores a zip against the held-out legal proxies 4-5. The 50 frames are chosen once by [`select_realism_frames.py`](../common/tools/select_realism_frames.py) (pooled-moment matching to proxies 1-3).
- **Combined estimate:** `0.6 * clip(mAP / 0.7) + 0.4 * R`, printed by `make_submission.sh` with the realval-A mAP.

### 6.7 Submission
```bash
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g1/test/make_submission.sh first
python common/tools/check_submission.py --track lumpi model-lumpi-track/routed-g1/submissions/<date>_first/submission.zip --official
# upload that submission.zip unchanged on CodaBench 16684 (Submit tab); never unzip, edit or re-zip it. Then:
python common/tools/package_submission.py model-lumpi-track/routed-g1 --tag first --record <codabench_id> model-lumpi-track/routed-g1/submissions/<date>_first/codabench_<codabench_id>.json
```
The packager writes `submission.zip` (50 synthetic frames from `test/synthetic_ids.txt`, `predictions.json` for every test ID, `declaration.txt`), validates it against the published spec, and stores `manifest.json` (model, route, frames, local scores, validation result). Packaging rules, the pre-upload check and failure handling: Sections 10.4-10.6.

## 7. Results and ablations

Numbers are 3D AP at IoU 0.5 (R40) with the **official metric**, mean over the 7 classes with test GT; realval-A = 1,280 Measurement4 frames (selection split), realval-B = 867 Measurement5-6 frames (check). Every row is in [`registry.csv`](registry.csv).

### 7.1 Models (official metric, tuned post-processing)

| Model | Training data | realval-A | realval-B | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van |
|---|---|---|---|---|---|---|---|---|---|---|
| `pointpillars-ut` (baseline) | `ut-v1`: UT only, Van -> Car | 0.168 | 0.127 | 0.000 | 0.843 | 0.124 | 0.005 | 0.006 | 0.166 | 0.034 |
| `pointpillars-g1` | `g1-v2`: + walkers v1, Van as Van, calibrated density | 0.253 | 0.156 | 0.341 | 0.874 | 0.265 | 0.010 | 0.006 | 0.154 | 0.122 |
| `pointpillars-g1v3` | `g1-v3`: + walker v2 | 0.248 | 0.163 | 0.340 | 0.873 | 0.186 | 0.008 | 0.011 | 0.200 | 0.118 |
| **`routed-g1`** (selected) | per class from the two above | **0.260** | **0.166** | 0.340 | 0.874 | 0.265 | 0.008 | 0.011 | 0.200 | 0.122 |

realval-B per class for `routed-g1`: Person 0.134, Car 0.770, Bicycle 0.102, Motorcycle 0.015, Bus 0.012, Truck 0.131, Van 0.001. The route: Person, Motorcycle, Bus, Truck from `g1v3`; Car, Bicycle, Van (and Unknown) from `g1`.

Reference points: ECCV 2026 winner on the test set, mAP 0.133 (Person 0.149, Car 0.643, Bicycle 0.078, Van 0.032, Motorcycle 0.020, Truck 0.011, Bus 0.000); live IEEE development leader mAP 0.102 (2026-10-02).

### 7.2 Ablations

| Question | Comparison | Result (realval-A mAP unless noted) |
|---|---|---|
| What does engine G1 add? | `pointpillars-ut` vs `pointpillars-g1` | 0.168 -> 0.253 (+0.085): Person 0 -> 0.341, Van 0.034 -> 0.122, Bicycle 0.124 -> 0.265 |
| Walker v1 vs v2 | `g1` vs `g1v3` | equal on A for Person (0.341 vs 0.340); on realval-B Person 0.091 -> 0.134 (v2 transfers to other measurements) |
| Training variance | `g1` vs `g1v3` on classes whose data are identical | Bicycle 0.265 vs 0.186, Truck 0.154 vs 0.200: large, so per-class routing pays (+0.007 over the best single model) |
| Post-processing (`g1`) | start config -> + NMS / re-centering -> + size and z -> + hedges | 0.210 -> 0.213 -> 0.242 -> 0.253 (box-convention calibration is the largest part: Person +0.049, Bicycle +0.109 with re-centering, Truck +0.019) |
| Training length | `g1` epoch 11 vs epoch 40 (untuned, KITTI-style metric at the time) | Person recall at BEV IoU 0.25 on real frames 28% -> 81% |
| Realism: density calibration and selection | raw UT frames -> `g1-v2` random 50 -> selected 50 (held-out proxies 4-5, official scorer) | R 0.59 -> 0.88 -> 0.906 (CD 1.63, MMD 0.0012, EMD 1.53 m, FPD 3.4); the first two values used the faster capped EMD solver, about 0.005 pessimistic |

### 7.3 Local estimate of the first submission

`routed-g1/submissions/2026-10-02_first/submission.zip`: realval-A mAP 0.260, realism R 0.906 (the kit's `local_eval.py` with 50 legal frames as the reference) -> **combined about 0.585** (0.505 with the realval-B mAP). The zip passes the kit's own validation (`valid_submission: 1`).

### 7.4 S1 close-out diagnostics (2026-10-09)

Official metric on legal real validation, S1 `routed-g1` predictions; files in [`routed-g1/validation/results/diagnostics/`](routed-g1/validation/results/diagnostics) and [`scorecard.json`](routed-g1/validation/results/scorecard.json). Summary and decisions: [`docs/02-STRATEGY.md` Section 8.1.3](../docs/02-STRATEGY.md#813-close-out-results-2026-10-09).

| Diagnostic | Finding |
|---|---|
| Test class mix vs realval-A (objects per frame) | Person 10.2 vs 17.4, Car 25.2 vs 27.9, Bicycle 1.6 vs 4.8, Motorcycle 0.54 vs 0.02, Bus 0.50 vs 0.17, Truck 3.8 vs 1.0, Van 1.6 vs 1.4 (realval-B: Truck 1.7, Motorcycle 0.30, Bus 0.31) |
| Drift toward the test window (realval-A frame bands 0-3199 / 3200-4799 / 4800-6399) | mAP 0.272 / 0.237 / 0.255; Person 0.421 / 0.225 / 0.196; Bicycle 0.278 / 0.283 / 0.232; Truck 0.223 / 0.002 / 0.387. The late band (late-A, 320 frames) has the test's Person density and is now part of the LUMPI gate |
| Height and z (BEV-matched pairs, score >= 0.1) | 91% (A) / 84% (B) of matched Persons reach 3D IoU 0.5; Persons 0.07-0.08 m too tall, Cars 0.08 m too low, Buses 2.7 m too short; BEV-3D gap 0.025 on B: height is not LUMPI's problem |
| Recall by points in the GT box (score >= 0.3, 3D IoU 0.5) | Person 0.24 / 0.51 / 0.65 / 0.64 (1-10 / 10-30 / 30-100 / 100+ points) on A; 0.21 / 0.38 / 0.42 / 0.23 on B (dense Persons missed on Measurement5-6); Truck 0.26-0.51 below 100 points |
| AP by range (0-15 / 15-30 / 30-45 / 45+ m) | Person 0.005 / 0.355 / 0.322 / 0.028; Bicycle 0.42 / 0.35 / 0.11 / 0.03; Truck 0.47 / 0.27 / 0.17 / 0.03; Van 0.12 / 0.36 / 0.06 / 0.04 |
| Truck lengths | real realval-A trucks: 5-6 m (224), 8-9 m (364), 12-14 m (213), 14-20 m (176); **synthetic `g1-v3` trucks: at most 8.47 m**; GT trucks over 12 m are predicted near 9.2 m. A generator gap (long trucks and trailers), not a post-processing one |
| Joint routing (A and B) | same route as S1 (Motorcycle from `g1` fails the class gate) |
| Range-dependent z calibration (C1) | no class passes the class gate (largest realval-B gain +0.004); [decision record](../docs/decisions/2026-10-09-s1-closeout-z-calibration.md) |

**Outcome:** no new LUMPI submission from the close-out; S1 stays the Track 1 entry.

### 7.5 S2 results: CenterPoint members (2026-10-09)

Official metric, tuned post-processing, realval-A / realval-B (late-A for the selected route). Summary, gates and lessons: [`docs/02-STRATEGY.md` Section 8.2.1](../docs/02-STRATEGY.md#821-results-2026-10-09); [decision record](../docs/decisions/2026-10-09-s2-center-routed.md).

| Member | Person | Car | Bicycle | Motorcycle | Truck | Van | mAP |
|---|---|---|---|---|---|---|---|
| S1 route (`g1`, `g1v3`) | **0.340 / 0.134** | **0.874 / 0.770** | 0.265 / 0.102 | 0.008 / 0.015 | **0.200 / 0.131** | 0.122 / 0.001 | 0.260 / 0.166 |
| `centerpoint-g1v3` (stride 8) | 0.095 / 0.038 | 0.848 / 0.756 | **0.350 / 0.128** | 0.069 / 0.022 | 0.137 / 0.077 | 0.119 / 0.001 | 0.233 / 0.147 |
| `centerpoint-s4-g1v3` (stride 4) | 0.168 / 0.047 | 0.844 / 0.749 | 0.318 / **0.134** | 0.057 / 0.023 | 0.118 / 0.109 | 0.087 / 0.001 | 0.230 / 0.153 |

- **Gate:** Bicycle moves to `centerpoint-g1v3` (B 0.102 -> 0.128, P(gain) 1.00, A 0.265 -> 0.350); Motorcycle (B +0.007) and Bus fail; everything else keeps its S1 member. `routed-g2`: A 0.260 -> 0.272, late-A 0.255 -> 0.271, B 0.1664 -> 0.1700; combined estimate (B) 0.5047 -> 0.5078, **+0.0031, below the +0.005 upload gate**. Package `routed-g2/submissions/2026-10-09_s2/lumpi_s2_submission.zip` (same 50 frames as S1, only the Bicycle boxes differ; kit scorer valid in 156 s) is kept for an optional confirmation upload.

- **Why the Person collapses:** CenterPoint emits about 39 Person boxes per frame scoring >= 0.5 against 17 real Persons; 69% of its unmatched ones sit in the same 1 m cells in at least 20% of the frames (static structures such as poles, signs and trees, which the twin does not contain), 2.7x more than the pillars. Removing those cells with the labels (an upper bound) would lift the S1 Person from 0.340 to 0.400 on A.
- **What it does well:** Bicycle (raw 0.196 vs 0.058 for the pillars on a 320-frame sample) and Car before tuning (0.805 vs 0.753).
- **Bug fixed on the way:** OpenPCDet's `CenterHead.assign_targets` trained the Car head on Motorcycles with these head groups; see `common/bdc26/detect/pcdet_patches.py`.

### 7.6 S3 results: TTA variants, fusion and score floors (2026-10-09)

Official metric, realval-A / realval-B. Summary, gates and lessons: [`docs/02-STRATEGY.md` Section 8.3.1](../docs/02-STRATEGY.md#831-results-2026-10-09); [decision record](../docs/decisions/2026-10-09-s3-fused-portfolio.md).

| Class | S2 route | S3 (`routed-g3`) | From | dB (bootstrap P) |
|---|---|---|---|---|
| Person | 0.340 / 0.134 | **0.396 / 0.145** | fused `g1v3_tta` + `g1_tta` (IoU 0.5) | +0.011 (1.00) |
| Car | 0.874 / 0.770 | **0.898 / 0.792** | fused `g1v3_tta` + `cp_tta` (IoU 0.7) | +0.022 (1.00) |
| Bicycle | 0.350 / 0.128 | **0.444 / 0.173** | fused `cp4_tta` + `cp_tta` (IoU 0.5) | +0.045 (1.00) |
| Truck | 0.200 / 0.131 | **0.231 / 0.153** | `g1v3_tta` | +0.023 (1.00) |
| Motorcycle, Bus, Van | B 0.015, 0.012, 0.001 | B 0.013, 0.011, 0.001 | S2 members (score floors cost -0.001) | gate failed for every change |
| **mAP** (late-A) | 0.272 / 0.170 (0.271) | **0.301 / 0.184 (0.298)** | | +0.014 (+0.012 to +0.016) |

- **TTA per member** (8 views: flips, yaw +/-5 deg, z +/-0.25 m; each variant with its own tuned `test/postprocess_tta.yaml`): Person on B from 0.091 to 0.141 for `g1` and from 0.038 to 0.081 for `centerpoint-g1v3`, Bicycle up for all four members, Car +0.009 to +0.024; `g1v3` Person is the exception (B 0.134 -> 0.128).
- **Static false positives** (Person on B, boxes ranked above the median true-positive score): 9.7 -> 4.1 per frame with fusion; 41% of the remaining unmatched ones are still static: R3 (static hard negatives) is the next Person lever.
- **Gated out:** Motorcycle fusion of `cp_tta` + `cp4` (A 0.008 -> 0.143, but B only +0.008, P 0.92); the Person fusion is the fragile gain (selected on realval-A alone, its pair loses on B).
- **Upload gate:** combined estimate (B) 0.505 (S1, uploaded) -> **0.520**, late-A 0.255 -> 0.298, R 0.905 (same 50 frames); kit scorer 181 s with 17,193 boxes (score floors: 1,045 -> 359 boxes per realval-A frame for -0.0007 B-mAP). **Passed.** Projected before the upload (0.82 x B): mAP about 0.151, combined about 0.486.
- **Leaderboard (974348, 2026-10-10, scorer log):** combined **0.5015**, mAP 0.1692 (Person 0.157, Car 0.652, Bicycle **0.224**, Truck 0.033, Van 0.117), 3D@0.7 0.0609, BEV 0.1781; confirmation passed by the log (+0.029 over 965614). CodaBench kept the submission in Running after the scorer printed DONE (Section 10.6). The gain was 1.89 x the realval-B gain and 0.81 x the realval-A gain (Section 9.4).

### 7.7 S4 results: two-stage members (2026-10-10)

Official metric, realval-A / realval-B. Review, plan, results and lessons: [`docs/02-STRATEGY.md` Sections 8.4 and 8.4.1](../docs/02-STRATEGY.md#841-results-2026-10-10); [decision record](../docs/decisions/2026-10-10-s4-two-stage.md).

| Member or step | Person | Car | Bicycle | Truck | mAP |
|---|---|---|---|---|---|
| `centerpoint-g1v3` (stage 1 alone), TTA | 0.211 / 0.081 | 0.886 / 0.780 | 0.406 / 0.155 | 0.162 / 0.113 | 0.275 / 0.165 |
| `voxelrcnn-g1v3`, TTA | 0.289 / 0.069 | 0.895 / 0.775 | 0.487 / **0.195** | 0.217 / 0.118 | 0.295 / 0.170 |
| `pvrcnnpp-g1v3`, TTA | 0.309 / 0.073 | 0.887 / 0.787 | 0.493 / 0.182 | 0.314 / 0.108 | 0.312 / 0.167 |
| S3 portfolio (`routed-g3`) | 0.396 / 0.145 | 0.898 / 0.792 | 0.444 / 0.173 | 0.231 / 0.153 | 0.301 / 0.184 |
| **S4 portfolio (`routed-g4`)** | 0.396 / 0.145 | 0.898 / 0.792 | **0.525 / 0.202** | 0.231 / 0.153 | **0.313 / 0.188** |

- **Routing and fusion:** Bicycle from `vr_tta` + `pv_tta` (IoU 0.7), B +0.029 (P 1.00); Car narrowly fails (`pv_tta` + `g1v3_tta`, B +0.0097); Truck from `pv_tta` gains A +0.08 but loses B 0.05 (gated out); Person keeps the S3 pillar fusion (the two-stage Persons reach only B 0.07).
- **Upload gate:** combined estimate (B) 0.520 -> 0.523 (bar 0.525), late-A 0.298 -> 0.304, R 0.905; kit scorer 182 s with 17,004 boxes. **Failed** (+0.003); uploaded by the entrant's call.
- **Leaderboard (975871, 2026-10-10):** combined **0.5040**, mAP 0.1721 (Bicycle 0.224 -> **0.244**; every other class identical to S3), rank **1 of 18**; confirmation passed (+0.0025 over the S3 log). The B-based estimate was right (+0.003); the A-based projection was not (+0.009): the gain was 0.25 x the A gain and 0.72 x the B gain.

### 7.8 S5 results: object scaling and GBlobs (2026-10-11)

Official metric, realval-A / realval-B, TTA members. Review, plan, results and lessons: [`docs/02-STRATEGY.md` Sections 8.5 and 8.5.1](../docs/02-STRATEGY.md#851-results-2026-10-11); [decision record](../docs/decisions/2026-10-11-s5-object-scaling.md).

| Member or step | Person | Car | Bicycle | Bus | Truck | mAP |
|---|---|---|---|---|---|---|
| `voxelrcnn-g1v3` (parent) | 0.289 / 0.069 | 0.895 / 0.775 | 0.487 / 0.195 | 0.010 / 0.010 | 0.217 / 0.118 | 0.295 / 0.170 |
| `voxelrcnn-gblobs-g1v3` (run a) | 0.177 / 0.058 | 0.895 / 0.783 | 0.459 / 0.178 | 0.010 / 0.010 | 0.218 / 0.086 | 0.276 / 0.162 |
| `voxelrcnn-ros-g1v3` (run b) | 0.287 / 0.084 | 0.895 / 0.788 | **0.540 / 0.220** | **0.018 / 0.077** | 0.362 / 0.142 | **0.322 / 0.189** |
| `pvrcnnpp-ros-g1v3` (extension) | 0.243 / 0.070 | **0.897 / 0.797** | 0.499 / 0.201 | 0.023 / 0.061 | **0.397 / 0.162** | 0.312 / 0.186 |
| `pointpillars-ros-g1v3` (extension) | 0.332 / **0.151** | 0.894 / 0.784 | 0.274 / 0.118 | 0.025 / 0.050 | 0.366 / **0.190** | 0.287 / 0.187 |
| S4 portfolio (`routed-g4`) | 0.396 / 0.145 | 0.898 / 0.792 | 0.525 / 0.202 | 0.011 / 0.011 | 0.231 / 0.153 | 0.313 / 0.188 |
| **S5 portfolio (`routed-g5`)** | 0.396 / 0.145 | **0.909 / 0.806** | **0.565 / 0.225** | **0.016 / 0.075** | **0.433 / 0.200** | **0.350 / 0.209** |

- **Routing and fusion:** Truck from `pvros_tta` + `ppros_tta` (B +0.047, late-A 0.414 -> 0.598), Bicycle from `vrros_tta` + `pvros_tta` + `pv_tta` (+0.023), Car from `pvros_tta` + `vrgb_tta` + `ppros_tta` (+0.014), Bus from `vrros_tta` (+0.064); Person keeps the S3 pillar fusion (best candidate B +0.006).
- **Why ROS helps:** the synthetic bicycles (1.66 x 0.58 x 1.62 m, no spread) and trucks (at most 8.47 m) are scaled to cover the real 2.00 x 0.85 x 1.90 m bicycles and 5.6-17.1 m trucks; Bus recall at IoU 0.5 0.20 -> 0.42 (Bus shares the head with Truck). GBlobs costs Person (A 0.189 -> 0.098 for the member).
- **Upload gate:** combined estimate (B) 0.523 -> **0.541** (bar 0.528), late-A 0.304 -> 0.335, R 0.905; kit scorer 146 s with 13,831 boxes. **Passed.** Projection: combined about 0.519 (0.514-0.541).
- **Leaderboard (978931, 2026-10-11):** 0.5039 (mAP 0.1720) against the S4 entry's 0.5040: **confirmation failed** (Truck 0.033 -> 0.072, Bicycle 0.244 -> 0.215, Car 0.652 -> 0.642). Diagnosis ([`docs/02` 8.5.1](../docs/02-STRATEGY.md#851-results-2026-10-11)): the changes lie outside the test-size sampling range; the size-augmented Bicycle members fire 18% more often on the test frames (realval +4%), motorcycle confusion explains little of it; the Car change was weak locally (pooled A+B P 0.64). S4 stays the entry; from R3 on the class gate also requires a pooled A+B gain.

## 8. Experiment log and next experiments

| # | Question | Result / plan |
|---|---|---|
| E1 | Actor scale fix (`ut-noscale-v1` vs `ut-v1`) | planned (the 0.78^3 IoU cap argues for it) |
| E2 | UT Van -> Van and hedges | done: Van 0.034 (baseline, hedge only) -> 0.122 |
| E3 | Synthetic Persons (G1) | done: Person 0 -> 0.341 on realval-A; mAP 0.168 -> 0.253 |
| E4 | Walker v2 | done: Person on realval-B 0.091 -> 0.134; equal on A |
| E5 | Calibrated background density | done: realism 0.59 -> 0.88 (0.906 with frame selection) |
| E6 | Per-class post-processing | done: 0.210 -> 0.253 for `g1` (Section 7.2) |
| E7 | Architecture routing (CenterPoint for Person, Bicycle, Motorcycle) | done (S2): Bicycle moves to CenterPoint; Person collapses on static false positives (Section 7.5) |
| E8 | Truck size modes, Bus convention | next (M7); close-out D5: the synthetic trucks stop at 8.47 m while 29% of real trucks are 12-20 m, so long trucks and trailers must enter the generator (Section 7.4) |
| E9 | TTA and weighted box fusion | done (S3): Person, Car, Bicycle, Truck up on B; mAP B 0.170 -> 0.184 (Section 7.6) |
| E11 | Two-stage refinement (Voxel R-CNN, PV-RCNN++) | done (S4): Bicycle B 0.173 -> 0.202; Person and Truck unchanged; below the upload gate (Section 7.7) |
| E12 | GBlobs inputs and class-wise object scaling | done (S5): object scaling helps every anchor-free and two-stage member; GBlobs only inside fusions (Section 7.8) |
| E10 | Static clutter and G2 for realism and hard negatives | in parallel with S2-S5 (`docs/02` Section 8.7, R track; promoted 2026-10-09): the cheapest LUMPI gain |

## 9. Submission log

| Date | Model / tag | CodaBench id | Local mAP (A / B) | Local R | LB mAP | LB R | LB combined | Note |
|---|---|---|---|---|---|---|---|---|
| 2026-10-02 | `routed-g1` / `first`, hand-edited copy (team typed into declaration.txt, re-zipped) | 957399 | 0.260 / 0.166 | 0.906 | | | | Failed after a few hours, no score; not counted (0 of 100 used); Section 10.6 |
| 2026-10-06 | `routed-g1` / `first`, team KarmaRV, uploaded unchanged as `submission_lumpi_karmarv.zip` | 965614 | 0.260 / 0.166 | 0.906 | **0.1357** | **0.8912** | **0.4728** | strategy S1; rank 1 of 31 (next 0.2769); server record [`codabench_965614.json`](routed-g1/submissions/2026-10-02_first/codabench_965614.json) |
| 2026-10-10 | `routed-g3` / `s3` (strategy S3), uploaded unchanged as `lumpi_s3_submission.zip` | 974348 | 0.301 / 0.184 | 0.905 | **0.1692** | **0.8912** | **0.5015** | strategy S3; scores from the scorer log (DONE), status Running afterwards, not listed yet; kit scorer 181 s, 17,193 boxes; server record [`codabench_974348.json`](routed-g3/submissions/2026-10-09_s3/codabench_974348.json); [decision record](../docs/decisions/2026-10-09-s3-fused-portfolio.md) |
| 2026-10-10 | `routed-g4` / `s4` (strategy S4), uploaded unchanged as `lumpi_s4_submission.zip` (below the upload gate, the entrant's call) | 975871 | 0.313 / 0.188 | 0.905 | **0.1721** | **0.8912** | **0.5040** | strategy S4; **rank 1 of 18** (next 0.4784); kit scorer 182 s, 17,004 boxes; server record [`codabench_975871.json`](routed-g4/submissions/2026-10-10_s4/codabench_975871.json); [decision record](../docs/decisions/2026-10-10-s4-two-stage.md) |
| 2026-10-11 | `routed-g5` / `s5` (strategy S5), uploaded unchanged as `lumpi_s5_submission.zip` | 978931 | 0.350 / 0.209 | 0.905 | 0.1720 | 0.8912 | 0.5039 | strategy S5; 0.00007 below the S4 entry, not listed; **confirmation failed**, diagnosed; kit scorer 146 s, 13,831 boxes; server record [`codabench_978931.json`](routed-g5/submissions/2026-10-11_s5/codabench_978931.json); [decision record](../docs/decisions/2026-10-11-s5-object-scaling.md) |

### 9.1 Local vs leaderboard per class (3D AP@0.5 R40)

| | mAP | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van |
|---|---|---|---|---|---|---|---|---|
| S5 leaderboard (978931, not listed) | 0.1720 | 0.157 | 0.642 | 0.215 | 0.001 | 0.001 | 0.072 | 0.117 |
| S5 realval-A / realval-B | 0.350 / 0.209 | 0.396 / 0.145 | 0.909 / 0.806 | 0.565 / 0.225 | 0.008 / 0.013 | 0.016 / 0.075 | 0.433 / 0.200 | 0.120 / 0.001 |
| **S4 leaderboard (975871, the entry)** | **0.1721** | 0.157 | 0.652 | **0.244** | 0.001 | 0.000 | 0.033 | 0.117 |
| S4 realval-A / realval-B | 0.313 / 0.188 | 0.396 / 0.145 | 0.898 / 0.792 | 0.525 / 0.202 | 0.008 / 0.013 | 0.011 / 0.011 | 0.231 / 0.153 | 0.120 / 0.001 |
| S3 leaderboard (974348, scorer log) | 0.1692 | 0.157 | 0.652 | **0.224** | 0.001 | 0.000 | 0.033 | 0.117 |
| S3 realval-A / realval-B | 0.301 / 0.184 | 0.396 / 0.145 | 0.898 / 0.792 | 0.444 / 0.173 | 0.008 / 0.013 | 0.011 / 0.011 | 0.231 / 0.153 | 0.120 / 0.001 |
| S3 leaderboard / realval-B | 0.92 | 1.08 | 0.82 | 1.29 | | | 0.22 | |
| leaderboard gain / realval-A gain (S1 -> S3) | 0.81 | 0.71 | 0.81 | 0.96 | | | 0.16 | |
| S1 leaderboard (965614) | 0.1357 | 0.117 | 0.633 | 0.053 | 0.001 | 0.000 | 0.028 | 0.118 |
| S1 realval-A | 0.260 | 0.340 | 0.874 | 0.265 | 0.008 | 0.011 | 0.200 | 0.122 |
| S1 realval-B | 0.166 | 0.134 | 0.770 | 0.102 | 0.015 | 0.012 | 0.131 | 0.001 |
| S1 leaderboard / realval-A | 0.52 | 0.34 | 0.72 | 0.20 | | | 0.14 | 0.97 |

Realism on the server: CD 1.690, MMD 0.00187, EMD 1.647, FPD 5.095, R 0.8912 (local proxy 4: 1.629, 0.00117, 1.530, 3.447, 0.9057). Van and Car transfer; Person, Bicycle and Truck lose most of their realval-A AP, so the realval-A selection does not represent the test window well (analysis: Section 9.4; next strategy: root README Section 8 and [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#8-strategy-routes-after-s1) Section 8).

### 9.2 Artifacts

S5 (978931, not listed): model [`routed-g5`](routed-g5) ([`model.yaml`](routed-g5/model.yaml)); the upload copy [`lumpi_s5_submission.zip`](routed-g5/submissions/2026-10-11_s5/lumpi_s5_submission.zip) (md5 `9f2c925c3976679b5b2038bfde5f7566`, in its [`manifest.json`](routed-g5/submissions/2026-10-11_s5/manifest.json)); server record [`codabench_978931.json`](routed-g5/submissions/2026-10-11_s5/codabench_978931.json).

S4 (975871): model [`routed-g4`](routed-g4) ([`model.yaml`](routed-g4/model.yaml): members with the two-stage members and TTA variants, `route`, `fusion`, `budget`); the upload copy [`lumpi_s4_submission.zip`](routed-g4/submissions/2026-10-10_s4/lumpi_s4_submission.zip) (md5 `ce3dc93c3f7defd7e0ca74bd0efc702a`, byte-identical to the folder's `submission.zip`, in its [`manifest.json`](routed-g4/submissions/2026-10-10_s4/manifest.json)); server record [`codabench_975871.json`](routed-g4/submissions/2026-10-10_s4/codabench_975871.json); reproducible from the committed `model.yaml` and the saved member predictions.

S3 (974348): model [`routed-g3`](routed-g3) ([`model.yaml`](routed-g3/model.yaml): members with TTA variants, `route`, `fusion`, `budget`); the upload copy [`lumpi_s3_submission.zip`](routed-g3/submissions/2026-10-09_s3/lumpi_s3_submission.zip) (md5 `9133dd7d9d8b377ec9228b79b75065a0`, byte-identical to the folder's `submission.zip`, in its [`manifest.json`](routed-g3/submissions/2026-10-09_s3/manifest.json)); server record [`codabench_974348.json`](routed-g3/submissions/2026-10-09_s3/codabench_974348.json) (scorer log); reproducible: the zip's predictions equal `route_predictions.py merge` of the saved member predictions with the committed `model.yaml`.

965614 (strategy S1):

| | |
|---|---|
| Model | [`routed-g1`](routed-g1) ([at tag 0.1](https://github.com/karmarv/utsim2real-bdc26/tree/0.1/model-lumpi-track/routed-g1)); members and route in [`routed-g1/model.yaml`](routed-g1/model.yaml); checkpoints are not in git |
| Submitted file | [`submission_lumpi.zip`](routed-g1/submissions/2026-10-02_first/submission_lumpi.zip) (tag 1.0), uploaded as [`submission_lumpi_karmarv.zip`](https://github.com/karmarv/utsim2real-bdc26/releases/download/0.1/submission_lumpi_karmarv.zip) (GitHub release [0.1](https://github.com/karmarv/utsim2real-bdc26/releases/tag/0.1)), the packaged zip unchanged, md5 `ea2c76393d6f8868762d6bac1ac03fa8` |
| Manifest | [`manifest.json`](routed-g1/submissions/2026-10-02_first/manifest.json) (checkpoints, route, frames, local scores, validation, CodaBench attempts), [`synthetic_ids.txt`](routed-g1/submissions/2026-10-02_first/synthetic_ids.txt) |
| Server record | [`codabench_965614.json`](routed-g1/submissions/2026-10-02_first/codabench_965614.json): every `scores.json` field and the scoring log |
| Leaderboard | [CodaBench 16684 results](https://www.codabench.org/competitions/16684/#/results-tab) |

### 9.3 Realism on the server

| | CD | MMD | EMD | FPD | R |
|---|---|---|---|---|---|
| leaderboard (965614 to 978931, identical frames) | 1.690 | 0.00187 | 1.647 | 5.095 | **0.8912** |
| local, held-out proxy 4 | 1.629 | 0.00117 | 1.530 | 3.447 | 0.9057 |
| ECCV 2026 winner | | | | | 0.913 |
| other IEEE entries (identical values: the kit's dummy frames) | 10.245 | 0.0677 | 3.39 | 119.5 | 0.473 |

Both sides pooled 2,500,000 points before subsampling (50 x 50,000), so the packaged density was used as intended. Share of the realism loss (1 - R) per term: EMD 76%, FPD 23%, MMD 1%, CD 0% (CD below 2 is free).

### 9.4 What transferred and what did not

| Finding | Evidence | Implication |
|---|---|---|
| Realism transfers, but less than on V2X | R 0.891 vs 0.906 locally (FPD 5.1 vs 3.4, EMD 1.65 vs 1.53) | the frames are slightly too average: the test-window reference has static structure the twin lacks (35% of the reference mass, [R19](../docs/07-LITERATURE.md#r19-eccv-2026-winner-reports)); engine G2 static clutter (`docs/02` Section 8.7, R track; promoted 2026-10-09) |
| Car and Van transfer | Car 0.633 (A 0.874, B 0.770); Van 0.118 (A 0.122) | keep the pillar members for vehicles in every later strategy |
| Person, Bicycle and Truck do not | Person 0.117 (A 0.340), Bicycle 0.053 (A 0.265), Truck 0.028 (A 0.200), with 512, 82 and 192 test GT boxes, so real gaps | realval-A (Measurement4 frames 0-6399) precedes the excluded last 20% of the recording, which holds the forbidden frames (6497-8109) and presumably the test frames; post-processing tuned on A partly fits A; select on A and B jointly (S2 onward) |
| Combined below the ECCV winner despite higher mAP | 0.4728 vs 0.4793: mAP 0.136 vs 0.133, R 0.891 vs 0.913 | +0.022 R is worth +0.009 combined: the cheapest LUMPI gain |
| Local estimate was optimistic | estimate A / B / leaderboard: 0.585 / 0.505 / 0.473; S3 0.620 / 0.520 / 0.501 | report the realval-B estimate; treat realval-A as an upper bound for levels |
| S3 gains transferred more than realval-B predicted | mAP +0.034 on the leaderboard vs +0.018 on B (1.89 x), but 0.81 x the realval-A gain (V2X: 0.80 x) | levels follow B, gains follow A: project the leaderboard from the A gain |
| Bicycle is the first weak class that moved | 0.053 -> 0.224 (B 0.102 -> 0.173, A 0.265 -> 0.444) | CenterPoint plus TTA and fusion fit the bikes of the test window; keep both CenterPoint members |
| S4 changed only Bicycle, as gated | 0.224 -> 0.244 (A +0.081, B +0.029); the other six classes identical on the leaderboard | the merge changes exactly the gated classes; the gain was 0.25 x A and 0.72 x B (S3: 0.81 x A, 1.89 x B): project with 0.6 x the mean of both || Truck still does not transfer | 0.028 -> 0.033 (B +0.022) | the synthetic trucks stop at 8.47 m (close-out D5): long trucks in the generator (R3) |
| S5 did not transfer on LUMPI | Truck +0.038 but Bicycle -0.030 and Car -0.010, each outside the test-size sampling range (P <= 0.02) | the test window answers the size-augmented Bicycle members with false positives no local split shows; the class gate adds a pooled A+B condition from R3 on |

## 10. Local evaluation and packaging

Everything here runs locally before an upload. The metrics are common to both tracks; the numbers are this track's.

### 10.1 Detection metric

As the scorer computes it (`scoring_program/detection_eval.py`, reproduced by [`common/bdc26/evalap.py`](../common/bdc26/evalap.py), checked by [`common/tests/test_official_parity.py`](../common/tests/test_official_parity.py)):
- per class and IoU threshold (0.5 primary, 0.7 reported): in each frame, predictions sorted by score each take the unused GT with the highest IoU and count as true positives if IoU >= threshold; predictions in frames without GT of the class are false positives; AP = mean over 40 recall points of the interpolated precision (R40 [R14](../docs/07-LITERATURE.md#r14-r40-average-precision); R11 reported);
- 3D IoU = oriented BEV polygon intersection x z overlap / union volume; class names match case-insensitively; a missing `class` defaults to "Car"; classes without test GT are excluded from the mean; no difficulty filter, no cap on the number of boxes;
- this track: mAP over the 7 classes with test GT (Unknown has none); test GT counts (kit `config.json`): Person 512, Car 1,258, Bicycle 82, Motorcycle 27, Bus 25, Truck 192, Van 79;
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
| this track's frames | LUMPI frames have no (0,0,0) nulls: the packager writes 50,000 real-range points per frame |

Each submission is a folder `<model>/submissions/<date>_<tag>/` with `manifest.json`, `synthetic_ids.txt`, the upload copy `lumpi_<strategy>_submission.zip` (byte-identical to `submission.zip`, written by the packager; upload this file unchanged) and, after an upload, `codabench_<id>.json`; the working `submission.zip` is git-ignored; the upload copy is committed (from 3.0; the 1.0 entries as `submission_<track>.zip`), and the leaderboard entries are listed in [`RELEASES.md`](../RELEASES.md).

### 10.5 Server cost and the pre-upload check

Both competitions use CodaBench's shared default queue, Docker image `codalab/codalab-legacy:py312` and a 1,200 s execution limit. The worker unzips the upload into `/app/input/res`, `run.sh` pip-installs numpy, scipy, shapely and POT, then `score.py` validates and scores; on a validation error it prints `[scoring] FATAL: <reason>`, writes zeros and `Infinity` into `scores.json` and the reason into `detailed_results.html`, and exits 0.

[`check_submission.py`](../common/tools/check_submission.py) `--official` runs the kit's scorer on a zip with a legal stand-in reference (realism-proxy-4 frames; realval labels under the test IDs) and reports validity, realism, wall time and peak memory. This track's S1 zip: 134 s, 5.9 GB peak. Memory is the same for every participant (10,000-point subsamples; the dense MMD matrices dominate); time grows with the number of boxes (17,095 in S1); a per-class box cap of 100 would cost -0.0005 mAP on realval-A, so it stays off.

### 10.6 When a CodaBench submission fails or hangs

| Symptom on the Submissions page | Most likely cause | What to do |
|---|---|---|
| Failed within minutes, or a score row of zeros | validation (declaration, `synthetic/`, prediction IDs) | read the scoring stdout (`FATAL:` line) and `detailed_results.html`; fix with the packager, never by hand |
| Failed with no message after hours in the queue | as above, but the `Infinity` fields may not be storable; or the worker died | collect the logs; re-check the exact uploaded file with `check_submission.py` |
| Running or "Preparing submission..." for more than a day with no log | no worker ran it, or the worker was lost | cancel and upload the same checked zip once more; if it hangs again, write to the organizers with the ids |
| Failed after about 20 minutes | the 1,200 s limit | compare with the `--official` wall time; only then consider the box cap |
| Running for hours although the scoring log already shows `[scoring] DONE: scores=...` (S3 upload, 2026-10-10) | the scorer finished; the platform did not finish the post-scoring step (storing the results) | keep the log (it holds every score); wait; if it ends as Failed or stays Running for a day, upload the same checked zip once more (it costs one of 5 per day) and report the id to the organizers |

Collect for every failed or stuck submission: the id, the status tooltip, the expanded row (scoring stdout and stderr, detailed results), the exact uploaded file (`unzip -l`, `check_submission.py --official`), its name, size and checksum, and how it was made. History: [`docs/decisions/2026-10-06-s1-first-submission.md`](../docs/decisions/2026-10-06-s1-first-submission.md).

### 10.7 Submission budget

Development phase 5 per day / 100 in total (public leaderboard, ends Oct 30, 17:00 PDT); final phase **1 per day / 5 in total, hidden leaderboard, development submissions do not carry over**. One development submission per strategy to confirm the local estimate; never tune against the leaderboard (probing the realism reference is forbidden). The schedule: [`docs/05-SCHEDULE-AND-RUNBOOK.md`](../docs/05-SCHEDULE-AND-RUNBOOK.md); the gates, the progression tracker and the submission register: [`docs/decisions/README.md`](../docs/decisions/README.md#3-evaluation-protocol-and-gates) Sections 2-4.

## 11. Integrity rules and real-data uses

The code enforces, for this track:
- the detector is trained on synthetic data only (training sets are `pcdet/ut-*` and `pcdet/g1-*` built from UT frames; real sets are named `realval-*` and `realism-proxy-*` and no training config points at them);
- every real-data reader goes through `bdc26.guard.ForbiddenGuard`: the 100 forbidden frames plus the self-exclusion window Measurement4 6400-8199 (the forbidden IDs lie in 6497-8109); every allowed access is logged with its purpose in `$BDC_DATA/lumpi-track/real/access_log.csv`;
- the 50 test frames are read only for inference and format checks; nothing is fitted to kit data; no reference bundles; no realism probing; no warping of submitted frames toward real statistics.

Uses of legal real data (allowed by the Rules tab: "hyperparameter selection or domain adaptation, provided no forbidden frame is touched"), all to be disclosed in the report:

| Use | Record |
|---|---|
| Validation, post-processing selection, routing (realval-A = Measurement4 0-6399 every 5th; realval-B = Measurement5-6) | Sections 6.3-6.4 and 10.3 |
| Sensor metadata: poses and beam tables of the five Measurement4 lidars (`meta.json`) | [`docs/decisions/2026-09-30-s1-g1-generator.md`](../docs/decisions/2026-09-30-s1-g1-generator.md) |
| Label statistics for the generator: Person positions, headings and box sizes | same |
| Background density prior from 400 unlabeled legal frames (gray area: "domain adaptation"; disclosed, ask the organizers) | same |
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
- Track facts live in `data-lumpi-track/track.yaml`, never as constants in code.
- Dataset versions are immutable: build a new name and record it in [`data-lumpi-track/README.md`](../data-lumpi-track/README.md) Section 9 with the command that built it.
- A model is a folder (`python common/tools/new_model.py lumpi <name> --from <model>`); outputs stay in git-ignored `output/`; decisions go to `registry.csv` and the model README.
- A strategy is named (root README Section 8, [`docs/02-STRATEGY.md`](../docs/02-STRATEGY.md#8-strategy-routes-after-s1) Section 8); every CodaBench submission is listed under it in the root README Section 9 and in Section 9 here.
- Real data only through the guard, with a purpose string; a new use of real data gets a decision record before it influences a submission.
- Evaluate with the official metric (`bdc26.evalap.evaluate`, `bdc26.realism.score`); never report KITTI-style numbers as challenge numbers.
- Match the surrounding code; new dependencies go into `requirements.txt`.

### 12.3 Typical contributions
| Task | Where | Check |
|---|---|---|
| New generator feature | `common/bdc26/render/`, an option in `data-lumpi-track/prepare_g1.py` | a statistic against legal real data; a new dataset version |
| New detector (S2, S4, S6) | a new model folder; `train/pcdet_model.yaml` | `tune_and_eval.sh`, then a member of a routed or fused model |
| New post-processing or fusion knob (S3) | `common/bdc26/detect/`, `common/tools/tune_postprocess.py` | realval-A gain that holds on realval-B |
| Metrics or packaging fix | `evalap.py`, `realism.py`, `submit.py` | `python -m pytest -q common/tests`, including the official-parity tests |

### 12.4 Running long jobs on the shared server
- Check `nvidia-smi` and `df -h` first; pin GPUs with `CUDA_VISIBLE_DEVICES` (LUMPI 0-3, V2X 4-7 match the NUMA nodes).
- Generation: `OMP_NUM_THREADS=1` with many workers. Training: `--workers 6` per GPU.
- Stop jobs by PID, not by pattern; never edit a shell script while a run of it is executing.
- Run the tests before every commit.
