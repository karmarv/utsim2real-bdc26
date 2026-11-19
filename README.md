# UrbanTwin Sim2Real LiDAR Challenge 2026: Team KarmaRV

Synthetic-only roadside LiDAR 3D object detection for the **UCF UrbanTwin Sim2Real LiDAR Challenge** at the IEEE BigData
Cup 2026 ([challenge website](https://urbanity-lab.github.io/bdc2026-urbantwin-sim2real/)), both tracks. Every detector is
trained on synthetic data only; real data is used for validation, model selection and label statistics, and no forbidden
frame is used (Section 5).

This README describes the **two final ranked submissions** and how to **reproduce them** from this repository. The full
development history (strategies S1-S10, every release and decision record) is in [`DEVELOPMENT.md`](DEVELOPMENT.md).

**Contents:** [1 Final results](#1-final-results) · [2 The final systems](#2-the-final-systems) ·
[3 Repository layout](#3-repository-layout) · [4 Reproduce the final submissions](#4-reproduce-the-final-submissions) ·
[5 Real-data use and compliance](#5-real-data-use-and-compliance) · [6 Papers](#6-papers) ·
[7 Development history](#7-development-history) · [8 Licence](#8-licence)

## 1. Final results

Official final-phase results (CodaBench scoring output; each entry is the team's best upload and is marked as the final
submission on its track):

| Track | Final rank | CodaBench entry | Combined | 3D mAP@0.5 (R40) | Realism R | System | Weights (release) |
|---|---|---|---|---|---|---|---|
| **V2X-Real** ([16685](https://www.codabench.org/competitions/16685/)) | **joint 1st** (46 teams) | **1051825** | **0.8944** (0.894399) | 0.6045 (0.604516) | 0.9406 (0.940605) | [`model-v2x-track/routed-s10-4-v4`](model-v2x-track/routed-s10-4-v4) | [10.4](https://github.com/karmarv/utsim2real-bdc26/releases/tag/10.4) |
| **LUMPI** ([16684](https://www.codabench.org/competitions/16684/)) | **2nd** (44 teams) | **1053789** | **0.5430** (0.542997) | 0.1975 (0.197537) | 0.9342 (0.934200) | [`model-lumpi-track/routed-s10-5-l12e`](model-lumpi-track/routed-s10-5-l12e) | [10.5](https://github.com/karmarv/utsim2real-bdc26/releases/tag/10.5) |

| Track | Per-class 3D AP@0.5 (R40), official |
|---|---|
| V2X-Real | vehicle 0.7432, pedestrian 0.4109, truck 0.6595 |
| LUMPI | Person 0.3159, Car 0.6833, Bicycle 0.1427, Motorcycle 0.0179, Bus 0.0004, Truck 0.0700, Van 0.1525 |

- **Confirmations from the organizers (Nov 18, 2026):** submission **1053789** is the KarmaRV entry on record for the
  LUMPI track (an earlier result email listed another ID by mistake), and both papers (CyberChair SC04204 and SC04205)
  were received and follow the guidelines. The V2X-Real 1st place is shared with one other team, as announced by the
  organizers.
- **Combined score** = 0.6 x clip(mAP / 0.7) + 0.4 x R, where R is the realism of the 50 submitted synthetic frames
  (Chamfer, MMD, EMD and Frechet distances to held-out real frames).
- Server records of the two entries:
  [`codabench_1051825.json`](model-v2x-track/routed-s10-4-v4/submissions/2026-11-13_s10-4-v4/codabench_1051825.json),
  [`codabench_1053789.json`](model-lumpi-track/routed-s10-5-l12e/submissions/2026-11-15_s10-5-l12e/codabench_1053789.json).

## 2. The final systems

Both systems are **routed ensembles**: OpenPCDet detectors (Voxel R-CNN, PV-RCNN++, DSVT, VoxelNeXt, PointPillars)
trained only on our synthetic corpora, run with test-time augmentation (4 views: flips, yaw and z; 12 views add scale),
combined per class by weighted box fusion, then passed through test-time stages chosen on real validation data. Every
member, route, fusion set and stage is written in the system card `model.yaml`; the reproduction script runs exactly that.

| | V2X-Real: `routed-s10-4-v4` (entry 1051825) | LUMPI: `routed-s10-5-l12e` (entry 1053789) |
|---|---|---|
| Synthetic training data | `g1-v6` corpus family: the UT-V2X-Real-IC digital twin with ray-cast walkers placed on the twin's scene map, real-size actors, clutter and a calibrated background density (generator draws `g1-v6` ... `g1-v6d5`) | the same engine on UT-LUMPI (`g1-v6`, `g1-v6d2`, the union `g1-v6j`) |
| Detectors (checkpoints) | 7: Voxel R-CNN-ROS x 5 generator draws, Voxel R-CNN-ROS with GT-sampling fade, DSVT-Pillar | 14: Voxel R-CNN-ROS (x5), PV-RCNN++-ROS (x3), PointPillars-ROS (x3), VoxelNeXt-ROS (x2), DSVT-Pillar |
| Per-class fusion | vehicle: draw bag + DSVT; pedestrian: three Voxel R-CNN members (12 views); truck: 5-draw bag + Voxel R-CNN | Person, Car, Bicycle, Motorcycle, Truck: 2-3 member fusions; Bus, Van: one routed member |
| Test-time stages | anchored size calibration; sparse-box and overhead-point demotion; tail copies; size step toward real median boxes (pedestrian height, vehicle footprint) | anchored size calibration; size step toward train-split medians (Person height, Car and Bicycle footprint); low-score duplicate and cross-class copies (Bus, Van -> Truck; Bicycle -> Person; Car -> Van; Motorcycle -> Bicycle; Truck -> Bus), each ranked below every box of its class |
| 50 synthetic frames | from the detectors' training corpus `g1-v6`; packaging adds the sensor's no-return points (31% of each frame, the real frame format) | from the detectors' training corpus `g1-v6` (byte-identical to the corpus frames) |

Track details: [`model-v2x-track/README.md`](model-v2x-track/README.md) and
[`model-lumpi-track/README.md`](model-lumpi-track/README.md).

## 3. Repository layout

```
utsim2real-bdc26/
├── README.md                     this file: the final submissions and how to reproduce them
├── DEVELOPMENT.md                the development guide: strategies S1-S10, workflow, all submissions
├── RELEASES.md                   release map: tags, leaderboard submissions, weights
├── requirements.txt              pinned direct dependencies (Python 3.10, CUDA 12.1 wheels)
├── requirements-lock.txt         the full pinned set (installed as constraints)
├── common/                       shared code: bdc26 package, tools/, pipeline/, env/ (setup), tests/
├── data-lumpi-track/             track config (track.yaml), starting-kit ingest, data preparation, generator
├── data-v2x-track/
├── model-v2x-track/
│   ├── routed-s10-4-v4/          FINAL V2X system: model.yaml, test/reproduce_s10-4-v4.sh,
│   │                             submissions/2026-11-13_s10-4-v4/ (scored zip, manifest, server record,
│   │                             saved member test predictions)
│   ├── <9 member folders>        the detectors and seed bags it uses (configs, tuned post-processing)
│   ├── archive/                  every other model folder of the development (not needed to reproduce)
│   ├── README.md                 the final V2X system
│   └── DEVELOPMENT.md            the track's development history
├── model-lumpi-track/
│   ├── routed-s10-5-l12e/        FINAL LUMPI system (same structure)
│   ├── <17 member folders>
│   ├── archive/
│   ├── README.md
│   └── DEVELOPMENT.md
├── releases/<tag>/weights.json   per release: every checkpoint and zip (GitHub asset name, path, md5, versions)
└── docs/                         plan of record, decision records (decisions/), and paper-bigdata2026/: the papers
                                  (paper-v2x-real/, paper-lumpi/) and the final challenge reports (final-report/)
```

Checkpoints are not in git: they are assets of the GitHub releases (Section 4.4) and land at
`model-<track>/<member>/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth`. Large data lives outside the
repository under `$BDC_DATA` (default `../bdc26-data`).

## 4. Reproduce the final submissions

Each scored zip is committed with its system: `model-<track>/<system>/submissions/<date>_<tag>/` holds the zip exactly as
uploaded (md5 in `manifest.json`), the server's scoring record `codabench_<id>.json`, and the saved test predictions of
every member (`member_predictions_<tag>.zip`). Two checks reproduce each entry:

| Check | What it shows | Needs | Time |
|---|---|---|---|
| **Check 1: exact re-merge** (Sections 4.5, 4.6) | the committed system card (`model.yaml`: routes, fusion, test-time stages) turns the members' saved test predictions into the scored `predictions.json`, **identical** to the last digit | the environment (Section 4.2) and the starting kits; no checkpoint, no GPU at run time | under 1 minute per track |
| **Check 2: full re-inference** (Sections 4.5, 4.6) | the released checkpoints, run from scratch on the 50 kit test frames, give the same predictions up to GPU floating-point nondeterminism; the repackaged zip passes the official starting-kit scorer and its 50 synthetic frames are byte-identical to the scored ones | one GPU and the checkpoints (Section 4.4) | 12 to 17 minutes per track on one RTX A6000 |

**Quick start** (Sections 4.1-4.4 explain the setup; Sections 4.5 (V2X-Real) and 4.6 (LUMPI) give each track's commands and expected output):

```bash
# 1. Environment (Section 4.2). On a machine other than ours, first export CUDA_HOME and TORCH_CUDA_ARCH_LIST.
git clone https://github.com/karmarv/utsim2real-bdc26.git && cd utsim2real-bdc26
python3.10 -m venv .venv_ut
bash common/env/setup_venv_ut.sh
source common/env/activate.sh

# 2. Starting kits (Section 4.3): download both zips from CodaBench into common/kit/, then unpack them.
mkdir -p common/kit
python data-v2x-track/ingest_kit.py common/kit/v2x_real_starting_kit.zip
python data-lumpi-track/ingest_kit.py common/kit/lumpi_starting_kit.zip

# 3. Check 1: exact re-merge, CPU only. Prints IDENTICAL for each track.
python common/tools/reproduce_submission.py model-v2x-track/routed-s10-4-v4 --tag s10-4-v4 --saved
python common/tools/reproduce_submission.py model-lumpi-track/routed-s10-5-l12e --tag s10-5-l12e --saved

# 4. Check 2: checkpoints (Section 4.4), then full re-inference on one GPU.
python common/tools/release_weights.py fetch --tag 10.4 --version v2x:s10-4-v4
python common/tools/release_weights.py fetch --tag 10.5 --version lumpi:s10-5-l12e
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-s10-4-v4/test/reproduce_s10-4-v4.sh
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-s10-5-l12e/test/reproduce_s10-5-l12e.sh
```

### 4.1 Prerequisites

| Item | Requirement | Tested with |
|---|---|---|
| OS | Linux x86_64 | Ubuntu 20.04, kernel 5.4 |
| GPU (Check 2 only) | one NVIDIA GPU with compute capability 7.0 to 9.0 (the pinned torch 2.1.2+cu121 predates Blackwell); 32 GB or more is the safe choice: up to 29 GB was in use during our LUMPI run (12-view test-time augmentation; PyTorch's cache included), and smaller cards are untested | RTX A6000 48 GB |
| Driver and CUDA | NVIDIA driver >= 530 (CUDA 12.1 wheels); a CUDA 12.x toolkit with `nvcc` to build OpenPCDet's ops (`CUDA_HOME`) | driver 570, CUDA 12.8 |
| Python | 3.10 with `venv` | 3.10.13 |
| Build tools | git, curl, a C++17 compiler (gcc 9 or newer) | gcc 9.4 |
| Disk | about 15 GB: the clone (about 3 GB; the history holds every scored zip), virtual environment and OpenPCDet build (about 7 GB), checkpoints (V2X 1.5 GB, LUMPI 2.3 GB), starting kits and outputs | |
| Starting kits | the two CodaBench starting kits (Files tab of each competition; CodaBench login) | |

No real dataset is needed to reproduce the test-set submissions.

### 4.2 Environment

```bash
git clone https://github.com/karmarv/utsim2real-bdc26.git
cd utsim2real-bdc26
python3.10 -m venv .venv_ut
```

OpenPCDet's CUDA ops are compiled for one GPU architecture. The defaults in
[`common/env/bdc26.env`](common/env/bdc26.env) are those of our machine (`CUDA_HOME=/usr/local/cuda-12.8`,
`TORCH_CUDA_ARCH_LIST=8.6` for the RTX A6000). On another machine, set both before the build (the compute capability is
listed at [developer.nvidia.com/cuda-gpus](https://developer.nvidia.com/cuda-gpus): 8.0 A100, 8.6 RTX 30xx/A6000,
8.9 RTX 40xx/L40, 9.0 H100):

```bash
export CUDA_HOME=/usr/local/cuda-12.4            # your CUDA 12.x toolkit
export TORCH_CUDA_ARCH_LIST="8.0"                # your GPU's compute capability
bash common/env/setup_venv_ut.sh
```

[`setup_venv_ut.sh`](common/env/setup_venv_ut.sh) (about 15 minutes) installs [`requirements.txt`](requirements.txt) with
[`requirements-lock.txt`](requirements-lock.txt) as constraints (torch 2.1.2+cu121, spconv-cu121 2.3.8, numpy 1.23.5,
...), clones OpenPCDet at commit `233f849` into `$BDC_DATA/third_party/OpenPCDet`, builds its CUDA ops, installs this
repository's `bdc26` package in editable mode, and checks the GPU and the IoU operator. Then, in every new shell:

```bash
source common/env/activate.sh          # sets BDC_REPO, BDC_DATA (default ../bdc26-data), PYTHONPATH, CUDA_HOME; activates .venv_ut
python -m pytest -q common/tests       # optional: the test suite (includes parity with the official scorer)
```

To keep data elsewhere, `export BDC_DATA=/path/to/data` before `source common/env/activate.sh`
(defaults in [`common/env/bdc26.env`](common/env/bdc26.env)).

### 4.3 Starting kits (test frames and the official scorer)

Download `lumpi_starting_kit.zip` and `v2x_real_starting_kit.zip` from the Files tabs of the two CodaBench competitions
into `common/kit/` (create it with `mkdir -p common/kit`; its zips are git-ignored), then unpack them into `$BDC_DATA`:

```bash
python data-v2x-track/ingest_kit.py common/kit/v2x_real_starting_kit.zip
python data-lumpi-track/ingest_kit.py common/kit/lumpi_starting_kit.zip
```

Each command unpacks its kit to `$BDC_DATA/<track>-track/kit/` and prints a format report. The 50 test frames are used
for inference and format checks only.

### 4.4 Checkpoints

The checkpoints of each entry are assets of its GitHub release; the manifest in `releases/<tag>/weights.json` lists
every file with its md5. Download and verify (no GitHub token needed; files already present with the right md5, such
as the scored zips that are in git, are skipped; each checkpoint lands at its path in the manifest):

```bash
python common/tools/release_weights.py fetch --tag 10.4 --version v2x:s10-4-v4        # V2X: 7 checkpoints + the scored zip
python common/tools/release_weights.py fetch --tag 10.5 --version lumpi:s10-5-l12e    # LUMPI: 14 checkpoints + the scored zip
python common/tools/release_weights.py verify --tag 10.4 --version v2x:s10-4-v4       # md5 of every file in place
python common/tools/release_weights.py verify --tag 10.5 --version lumpi:s10-5-l12e
```

### 4.5 V2X-Real track: reproduce entry 1051825

Entry **1051825**: combined 0.894399 (3D mAP 0.604516, realism 0.940605). System
[`model-v2x-track/routed-s10-4-v4`](model-v2x-track/routed-s10-4-v4) ([track README](model-v2x-track/README.md)); checkpoints in release
[10.4](https://github.com/karmarv/utsim2real-bdc26/releases/tag/10.4) (7 files, 1.5 GB).

**Quick start** (setup details: Sections 4.1-4.4):

```bash
git clone https://github.com/karmarv/utsim2real-bdc26.git && cd utsim2real-bdc26
# on a GPU other than an RTX A6000, first: export CUDA_HOME=<CUDA 12.x> TORCH_CUDA_ARCH_LIST=<compute capability>
python3.10 -m venv .venv_ut && bash common/env/setup_venv_ut.sh
source common/env/activate.sh
mkdir -p common/kit      # put v2x_real_starting_kit.zip here (CodaBench 16685, Files tab)
python data-v2x-track/ingest_kit.py common/kit/v2x_real_starting_kit.zip

# Check 1, exact re-merge (CPU, about 25 s): expected IDENTICAL, exit code 0
python common/tools/reproduce_submission.py model-v2x-track/routed-s10-4-v4 --tag s10-4-v4 --saved

# Check 2, full re-inference (one GPU, about 12 minutes): expected EQUIVALENT, exit code 0
python common/tools/release_weights.py fetch --tag 10.4 --version v2x:s10-4-v4
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-s10-4-v4/test/reproduce_s10-4-v4.sh
```

**Check 1: exact re-merge.** Merges the members' saved test predictions
([`member_predictions_s10-4-v4.zip`](model-v2x-track/routed-s10-4-v4/submissions/2026-11-13_s10-4-v4/member_predictions_s10-4-v4.zip), committed next to the scored zip) with the
committed [`model.yaml`](model-v2x-track/routed-s10-4-v4/model.yaml) and compares the result box by box with the scored `predictions.json`.
Expected: exit code 0 and

```
re-merge of 6 saved members with model-v2x-track/routed-s10-4-v4/model.yaml: IDENTICAL to the scored model-v2x-track/routed-s10-4-v4/submissions/2026-11-13_s10-4-v4/v2x_s10-4-v4_submission.zip
```

(41,252 boxes, maximum difference 0.0.)

**Check 2: full re-inference.** Downloads the 7 checkpoints of release 10.4 (md5-verified), reruns them on the 50
test frames of the starting kit, repackages the submission, validates it with the starting-kit scorer and compares it
with the scored zip (Section 4.7). Expected: exit code 0, ending with

```
reproduction: EQUIVALENT (GPU nondeterminism: run it on an idle GPU for an exact match) (scored zip model-v2x-track/routed-s10-4-v4/submissions/2026-11-13_s10-4-v4/v2x_s10-4-v4_submission.zip; frames identical)
```

| Check | Our result (Nov 19, 2026) |
|---|---|
| Inference | 11 runs: 7 checkpoints, two seed bags, 4 or 12 test-time views |
| Boxes against the scored zip | 41,248 re-inferred, 41,252 scored; 41,239 matched; the 22 unmatched all score below 0.3 |
| Matched boxes, 99th percentile | centre 3.3 mm, score 0.00008 |
| 50 synthetic frames | byte-identical (`"synthetic_frames_identical": true`) |
| Starting-kit scorer | `"valid": true` (kit dummy reference, 19 s) |
| Repackaged zip | `model-v2x-track/routed-s10-4-v4/test/output/repro-s10-4-v4/submission.zip` |

**Scores: leaderboard and local evaluation.** The leaderboard row is the organizers' scoring of entry 1051825 on the
50 test frames. The local rows apply the same official metric (3D AP@0.5, R40) to legal real validation frames that
were never used for training ([`data-v2x-track/README.md`](data-v2x-track/README.md)): as recorded when the system was
selected ([`scorecard.json`](model-v2x-track/routed-s10-4-v4/validation/results/scorecard.json)) and as recomputed on
Nov 19 from the release 10.4 checkpoints by
[`test/reproduce_s10-4-v4_validation.sh`](model-v2x-track/routed-s10-4-v4/test/reproduce_s10-4-v4_validation.sh)
([result](model-v2x-track/routed-s10-4-v4/validation/results/reproduce_s10-4-v4_validation.json): EQUIVALENT, largest
per-class difference 0.00015).

| Evaluation | Frames | vehicle | pedestrian | truck | 3D mAP | Realism R | Combined |
|---|---|---|---|---|---|---|---|
| **Leaderboard 1051825** (organizers' server) | 50 test | 0.7432 | 0.4109 | 0.6595 | 0.6045 | 0.9406 | **0.8944** |
| Local realval-A, recorded at selection (Nov 13) | 688 real | 0.8732 | 0.4091 | 0.9113 | 0.7312 | 0.9415 | 0.9766 |
| Local realval-A, reproduced (Nov 19) | 688 real | 0.8731 | 0.4091 | 0.9113 | 0.7312 | 0.9415 | 0.9766 |
| Local realval-B, recorded at selection (Nov 13) | 298 real | 0.8810 | 0.4013 | 0.8528 | 0.7117 | 0.9415 | 0.9766 |
| Local realval-B, reproduced (Nov 19) | 298 real | 0.8810 | 0.4013 | 0.8528 | 0.7117 | 0.9415 | 0.9766 |

- **Local realism R:** the official starting-kit scorer on the 50 submitted frames against 50 held-out legal real
  frames (`realism-proxy-4`): 0.941485 at selection and again on Nov 19. The server's hidden reference gave 0.940605.
- **Local combined:** the challenge formula with the local mAP and R. Both validation splits pass the mAP cap of 0.7,
  so their combined score saturates. On the test frames pedestrian AP agrees with validation within 0.01, vehicle is
  0.13-0.14 lower, and truck (0.66 on 124 test boxes) is 0.19-0.25 lower.
- Recomputing the local rows needs the prepared real validation data (licensed, not redistributed; Section 4.9) and
  about 3 GPU-hours (18 inference runs, independent of each other; we spread them over 8 GPUs).

### 4.6 LUMPI track: reproduce entry 1053789

Entry **1053789**: combined 0.542997 (3D mAP 0.197537, realism 0.934200). System
[`model-lumpi-track/routed-s10-5-l12e`](model-lumpi-track/routed-s10-5-l12e) ([track README](model-lumpi-track/README.md)); checkpoints in release
[10.5](https://github.com/karmarv/utsim2real-bdc26/releases/tag/10.5) (14 files, 2.3 GB).

**Quick start** (setup details: Sections 4.1-4.4):

```bash
git clone https://github.com/karmarv/utsim2real-bdc26.git && cd utsim2real-bdc26
# on a GPU other than an RTX A6000, first: export CUDA_HOME=<CUDA 12.x> TORCH_CUDA_ARCH_LIST=<compute capability>
python3.10 -m venv .venv_ut && bash common/env/setup_venv_ut.sh
source common/env/activate.sh
mkdir -p common/kit      # put lumpi_starting_kit.zip here (CodaBench 16684, Files tab)
python data-lumpi-track/ingest_kit.py common/kit/lumpi_starting_kit.zip

# Check 1, exact re-merge (CPU, about 10 s): expected IDENTICAL, exit code 0
python common/tools/reproduce_submission.py model-lumpi-track/routed-s10-5-l12e --tag s10-5-l12e --saved

# Check 2, full re-inference (one GPU, about 17 minutes): expected one fusion merge/split (below), exit code 1
python common/tools/release_weights.py fetch --tag 10.5 --version lumpi:s10-5-l12e
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-s10-5-l12e/test/reproduce_s10-5-l12e.sh
```

**Check 1: exact re-merge.** Merges the members' saved test predictions
([`member_predictions_s10-5-l12e.zip`](model-lumpi-track/routed-s10-5-l12e/submissions/2026-11-15_s10-5-l12e/member_predictions_s10-5-l12e.zip), committed next to the scored zip) with
the committed [`model.yaml`](model-lumpi-track/routed-s10-5-l12e/model.yaml) and compares the result box by box with the scored `predictions.json`.
Expected: exit code 0 and

```
re-merge of 14 saved members with model-lumpi-track/routed-s10-5-l12e/model.yaml: IDENTICAL to the scored model-lumpi-track/routed-s10-5-l12e/submissions/2026-11-15_s10-5-l12e/lumpi_s10-5-l12e_submission.zip
```

(38,047 boxes, maximum difference 0.0.)

**Check 2: full re-inference.** Downloads the 14 checkpoints of release 10.5 (md5-verified), reruns them on the 50
test frames of the starting kit, repackages the submission, validates it with the starting-kit scorer and compares it
with the scored zip (Section 4.7). Expected: exit code 1, ending with

```
reproduction: DIFFERENT under the strict rule only by 1 box fusion merge/split decision(s) (listed above under unmatched_above_0.3 / merge_split_with); every other box matched within the tolerance. The exact check is the re-merge of the saved member predictions (--saved) (scored zip model-lumpi-track/routed-s10-5-l12e/submissions/2026-11-15_s10-5-l12e/lumpi_s10-5-l12e_submission.zip; frames identical)
```

| Check | Our result (Nov 19, 2026) |
|---|---|
| Inference | 17 runs: 14 checkpoints, three seed bags, 4 or 12 test-time views |
| Boxes against the scored zip | 38,033 re-inferred, 38,047 scored; 37,980 matched; of the 120 unmatched, one scores above 0.3 (below), two are the Truck pair it replaces, and the other 117 score below 0.15 |
| Matched boxes, 99th percentile | centre 2.3 cm, score 0.0005 |
| 50 synthetic frames | byte-identical (`"synthetic_frames_identical": true`) |
| Starting-kit scorer | `"valid": true` (kit dummy reference, 22 s) |
| Repackaged zip | `model-lumpi-track/routed-s10-5-l12e/test/output/repro-s10-5-l12e/submission.zip` |

**The one LUMPI difference** (printed under `unmatched_above_0.3`): in kit frame 007209 the scored zip has two
overlapping Truck boxes (scores 0.24 and 0.21), while the re-inference has one fused Truck box (0.45) in their place. It
starts inside the two-seed PV-RCNN++ bag that is one of the two Truck members: its two seeds score this truck almost
equally (0.428 and 0.427) with boxes overlapping at 3D IoU 0.68, so floating-point differences change how weighted box
fusion clusters them, and the bag's box for this truck lies 0.7 m from its position in the scored run. The Truck class
fusion (IoU 0.7) then merges it with the other member's box instead of keeping both. Our two runs on Nov 19 (the
working checkout and a fresh copy) both give the merged box. Every other box agrees within the tolerance, and Check 1
shows that the scored predictions follow exactly from the saved member predictions and the committed card.

**Scores: leaderboard and local evaluation.** The leaderboard row is the organizers' scoring of entry 1053789 on the
50 test frames. The local rows apply the same official metric (3D AP@0.5, R40) to legal real validation frames that
were never used for training ([`data-lumpi-track/README.md`](data-lumpi-track/README.md)): as recorded when the system
was selected ([`scorecard.json`](model-lumpi-track/routed-s10-5-l12e/validation/results/scorecard.json)) and as
recomputed on Nov 19 from the release 10.5 checkpoints by
[`test/reproduce_s10-5-l12e_validation.sh`](model-lumpi-track/routed-s10-5-l12e/test/reproduce_s10-5-l12e_validation.sh)
([result](model-lumpi-track/routed-s10-5-l12e/validation/results/reproduce_s10-5-l12e_validation.json): EQUIVALENT,
largest per-class difference 0.0003).

| Evaluation | Frames | Person | Car | Bicycle | Motorcycle | Bus | Truck | Van | 3D mAP | Realism R | Combined |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Leaderboard 1053789** (organizers' server) | 50 test | 0.3159 | 0.6833 | 0.1427 | 0.0179 | 0.0004 | 0.0700 | 0.1525 | 0.1975 | 0.9342 | **0.5430** |
| Local realval-A, recorded at selection (Nov 15) | 1,280 real | 0.6101 | 0.9086 | 0.6545 | 0.2400 | 0.0108 | 0.3881 | 0.1086 | 0.4172 | 0.9404 | 0.7338 |
| Local realval-A, reproduced (Nov 19) | 1,280 real | 0.6100 | 0.9086 | 0.6545 | 0.2400 | 0.0108 | 0.3881 | 0.1086 | 0.4172 | 0.9404 | 0.7338 |
| Local late-A, recorded at selection (Nov 15) | 320 real | 0.4659 | 0.8797 | 0.5102 | 0.0006 | 0.0007 | 0.5548 | 0.0819 | 0.3563 | 0.9404 | 0.6815 |
| Local late-A, reproduced (Nov 19) | 320 real | 0.4656 | 0.8797 | 0.5102 | 0.0006 | 0.0007 | 0.5548 | 0.0819 | 0.3562 | 0.9404 | 0.6815 |
| Local realval-B, recorded at selection (Nov 15) | 867 real | 0.2502 | 0.8034 | 0.2868 | 0.0497 | 0.0645 | 0.2422 | 0.0012 | 0.2426 | 0.9404 | 0.5841 |
| Local realval-B, reproduced (Nov 19) | 867 real | 0.2502 | 0.8034 | 0.2869 | 0.0497 | 0.0645 | 0.2422 | 0.0012 | 0.2426 | 0.9404 | 0.5841 |

- **Frames:** realval-A is 1,280 frames of Measurement4, the recording the test frames come from; late-A is its 320
  frames nearest the test window (frames 4800-6399); realval-B is 867 frames of Measurements 5-6 (another session,
  partly automatic labels, and its Van labels are not vans, so its Van AP is not comparable).
- **Local realism R:** the official starting-kit scorer on the 50 submitted frames against 50 held-out legal real
  frames (`realism-proxy-4`): 0.940414 at selection and again on Nov 19. The server's hidden reference gave 0.934200.
- **Local combined:** the challenge formula with the local mAP and R. The test mAP (0.198) is below every local split
  (0.243-0.417): Car, Bicycle and Truck are 0.12-0.17 below even realval-B, Person lies between realval-B and late-A,
  and Van is the one class above its validation AP. The LUMPI report ([Section 6](#6-papers)) discusses the gap.
- Recomputing the local rows needs the prepared real validation data (licensed, not redistributed; Section 4.9) and
  about 10 GPU-hours (34 inference runs, independent of each other; we spread them over 8 GPUs).

### 4.7 How the reproduction works

**Check 1** ([`reproduce_submission.py`](common/tools/reproduce_submission.py) `--saved`) merges the saved member
predictions with the committed `model.yaml` ([`route_predictions.py`](common/tools/route_predictions.py) `merge_card`)
and compares the result box by box with the `predictions.json` inside the scored zip; it exits with 0 when they are
identical. We ran it on a fresh clone and with no GPU visible.

**Check 2** (`test/reproduce_<tag>.sh` in each system folder) runs six steps:

1. **Inference** of every member on the 50 kit test frames with its checkpoint, its test-time views and its tuned
   post-processing file (`test/postprocess*.yaml`); seed bags fuse their members' predictions
   ([`pcdet_predict.py`](common/tools/pcdet_predict.py), [`bag_predictions.py`](common/tools/bag_predictions.py)).
2. **Merge** with the committed system card ([`route_predictions.py`](common/tools/route_predictions.py) `merge`).
3. **Compare** the merged predictions with the scored zip's (`reproduce_submission.py --compare`; informative, the
   script continues).
4. **Repackage** with the same 50 synthetic frames, taken from the scored zip when the synthetic corpus is not present,
   and the declaration ([`package_submission.py`](common/tools/package_submission.py)).
5. **Check** the new zip with the official starting-kit scorer
   ([`check_submission.py`](common/tools/check_submission.py) `--official`): structure, validity and the scorer's run.
   Without our real validation data it uses the kit's dummy reference, so its realism number and run time are not
   indicative of the server.
6. **Compare** the new zip with the scored one, predictions and the 50 frames (`reproduce_submission.py --compare-zip`);
   this prints the verdict and sets the exit code.

Outputs go to `model-<track>/<system>/test/output/` (git-ignored).

**The comparison.** Boxes are matched per frame and class (Hungarian assignment on centres, within 0.5 m). A run is
EQUIVALENT when no box scored above 0.3 is left unmatched and 99% of the matched boxes agree within 0.1 m and 0.01 in
score. Sparse-convolution and point-operator kernels on the GPU are not bit-deterministic (two of our runs on idle GPUs
differ by 0.04 mm at the 99th percentile), so IDENTICAL is not expected from re-inference; Check 1 is the exact check.
Each track's results above are from our working checkout; a fresh copy of the repository with only the starting kits
under `$BDC_DATA` and the checkpoints verified against the release manifests gave the same verdicts.

The official leaderboard numbers (Section 1) come from the organizers' server, which scores against held-out ground
truth and a held-out realism reference that the starting kit does not carry; the server's scoring record of each entry
is committed next to its zip (`codabench_<id>.json`).

### 4.8 Troubleshooting

- `source common/env/activate.sh` activates a conda environment instead of `.venv_ut`: the setup did not finish (it
  marks the environment ready only after its checks pass). Rerun `bash common/env/setup_venv_ut.sh` and read its first
  error.
- `no kernel image is available for execution on the device`, or an import error from `pcdet`: OpenPCDet's ops were
  built for another GPU architecture or CUDA toolkit. Set `CUDA_HOME` and `TORCH_CUDA_ARCH_LIST` (Section 4.2), remove
  `$BDC_DATA/third_party/OpenPCDet`, and rerun the setup.
- `forbidden_frames.txt missing` or `starting kit not ingested`: run Section 4.3 in an activated shell.
- `CUDA out of memory` in Check 2: use a GPU that no other job shares, or a larger one (Section 4.1).

### 4.9 Optional: validation and retraining

- **Validation reproduction** (real validation data needed): each system folder also has
  `test/reproduce_<tag>_validation.sh`, which reruns every member on realval-A and realval-B from its checkpoint, merges
  the predictions with the committed `model.yaml` and recomputes the local scores behind the selection. Our results for
  the two final systems are in the score tables of Sections 4.5 and 4.6. Preparing the real validation sets needs the LUMPI and V2X-Real licences
  ([`data-lumpi-track/README.md`](data-lumpi-track/README.md), [`data-v2x-track/README.md`](data-v2x-track/README.md)).
- **Retraining** from scratch: each member folder has `train/train.sh` (OpenPCDet config in `train/pcdet_model.yaml`,
  the corpus and seed in `model.yaml`); the corpora are generated with `data-<track>/prepare_g1.py` from the organizers'
  UT synthetic sets. The full workflow (data, generation, training, tuning, routing and fusion) is
  [`DEVELOPMENT.md`](DEVELOPMENT.md) Section 6.

## 5. Real-data use and compliance

The challenge reports (Section 6) give the full real-data-use statement the organizers asked for; in short:

- **Training:** synthetic data only. No real frame or real label is a training input or a training target (no
  pretraining, fine-tuning or pseudo-labels on real frames). Clean-corpus rules are enforced in code
  (`common/tools/clean_check.py`) before packaging.
- **Guard:** every real-data reader goes through one guard ([`common/bdc26/guard.py`](common/bdc26/guard.py)) that
  refuses the forbidden frames (the 50 test frames and the 50 realism-reference frames), logs each read with its
  purpose, and excludes a self-imposed window around them (LUMPI: Measurement 4 frames 6400-8199; V2X-Real: 20 frames
  on either side of each forbidden frame). The remaining real frames are the legal frames.
- **Legal real frames were used for:** validation and selection (realval-A and realval-B; LUMPI also late-A); label
  statistics in the generator (walker box mixture and distance histogram, size quantiles, per-class ray dropout, points
  per walker), in training augmentation (the 99th-percentile size caps of object scaling) and at test time (anchored
  size offsets, V2X visibility counts, and the median sizes of the final size step: LUMPI train-split medians, V2X
  realval-A medians); realism calibration (a density prior from 400 unlabelled frames, the sensor beam tables, and the
  choice of the 50 frames against legal proxy sets).
- **Test frames:** inference only (V2X also counts points inside the predicted boxes for the visibility and overhead
  stages); every copy stage duplicates the detector's own boxes. The starting kit's realism reference is used only by
  the local format check of Section 4.7, never for fitting or selection.
- **Submitted frames:** the 50 synthetic frames of each entry come from the detectors' own training corpus, as the
  organizers asked (Nov 12, 2026). The organizers confirmed that the real-data uses listed above are allowed
  (Nov 10, 2026).
- **Disclosures** made to the organizers (described in the reports): earlier corpora with label-placed walkers and the
  LUMPI frames-only re-cast; the affected uploads were removed or are not ranked, and the final entries use neither.

## 6. Papers

| Track | IEEE BigData 2026 proceedings (CyberChair) | Files |
|---|---|---|
| V2X-Real | SC04204, "Pedestrian Synthesis and Detector Fusion for Synthetic-Only Roadside LiDAR Detection on V2X-Real" | [`docs/paper-bigdata2026/paper-v2x-real/`](docs/paper-bigdata2026/paper-v2x-real) |
| LUMPI | SC04205, "Digital Twin Augmentation and Classwise Detector Fusion for Synthetic-Only Multi-LiDAR Detection on LUMPI" | [`docs/paper-bigdata2026/paper-lumpi/`](docs/paper-bigdata2026/paper-lumpi) |

The final challenge reports are in [`docs/paper-bigdata2026/final-report/`](docs/paper-bigdata2026/final-report). arXiv versions
are in moderation (Nov 18, 2026).

## 7. Development history

- [`DEVELOPMENT.md`](DEVELOPMENT.md): the development guide used during the challenge (workflow, strategies S1-S10, all
  CodaBench submissions).
- [`RELEASES.md`](RELEASES.md): every release tag, its leaderboard submissions and weights. Older versions are reproduced
  from their tag (`git checkout <tag>`), where every model folder is at its original path.
- [`docs/decisions/`](docs/decisions): the decision records, from the first submission to the final push.
- `model-<track>/archive/`: every model folder of the development that the final systems do not use (configs, tuned
  post-processing, validation results, scored zips of earlier entries).

## 8. Licence

Code: Apache 2.0 ([`LICENSE`](LICENSE)). Data keeps its own licence (UT twins CC0; LUMPI CC BY-NC 3.0; V2X-Real UCLA
Academic licence). No real frame or real label is in this repository; the validation results hold scores only.
