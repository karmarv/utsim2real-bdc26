# Track 2 data: V2X-Real (`data-v2x-track/`)

> Everything about the data of Track 2 (CodaBench 16685): sources and licences, the sensor and coordinate frame, classes, the forbidden-frame mapping and guard, every preparation script with its inputs and outputs, the synthetic-data generator (engine G1) and its calibration against legal real data, the dataset versions on disk, and what we measured. The model side is in [`model-v2x-track/README.md`](../model-v2x-track/README.md); the project-wide developer guide is the [root README](../README.md).

## 0. At a glance

| Item | Value |
|---|---|
| Test input | 50 real V2X-Real frames of the infrastructure lidar (agent -1), float32 N x 3, 49,405-50,000 points each, **31.1% stored as (0,0,0) null returns** |
| Point-cloud range | `[-40, -40, -8, 40, 40, 2]` (inclusive bounds in the scorer) |
| Classes | vehicle, pedestrian, truck (the official V2X-Real super-classes) |
| Test GT counts (public) | vehicle 470, **pedestrian 953**, truck 124 |
| Forbidden frames | 100 IDs `<scenario index>_<frame>`; all resolved ones are V2X-Real **train**-split scenes |
| Synthetic source | UT-V2X-Real-IC, the organizers' CARLA twin (CC0), 10,000 frames |
| Real source | V2X-Real (UCLA), UCLA Academic licence, dataset "All Rights Reserved": validation, calibration and statistics only, never training |
| Track config | [`track.yaml`](track.yaml) |

## 1. Scripts in this folder

Run from the repository root after `source common/env/activate.sh`.

| Script | Purpose | Inputs | Outputs (under `$BDC_DATA/v2x-track/`) |
|---|---|---|---|
| [`fetch_ut.py`](fetch_ut.py) | Download UT-V2X-Real-IC from Dataverse (MD5 against [`manifests/`](manifests)) | internet | `ut/UCF-DT-V2X-Real-Seq-1/{pcd,lbl,sem_seg,ins_seg}/` (20 GB) |
| [`ingest_kit.py`](ingest_kit.py) | Unpack the starting kit, report the test-frame format | `common/kit/v2x_real_starting_kit.zip` | `kit/`, `kit/kit_report.json` |
| [`fetch_real.py`](fetch_real.py) | Download V2X-Real agent -1 data from the UCLA box shares (remote zip, range requests): `--points` (all bins), `--labels` (yaml of guard-allowed frames only). Requires `--accept-licence` | internet, licence | `real/raw/<split>/<scenario>/-1/<frame>.{bin,yaml}` |
| [`resolve_test_ids.py`](resolve_test_ids.py) | Map challenge scenario indices to V2X-Real folders (exact point matching of the 50 test frames against raw frames; monotone-subset bounds for the rest). **Required by the guard** | kit, raw bins | `kit/id_mapping.json`, `kit/id_mapping_report.json` |
| [`prepare_ut.py`](prepare_ut.py) | UT frames -> OpenPCDet dataset: super-classes, resample to 35,000 valid points in range | `ut/` | `pcdet/ut-v1/` |
| [`prepare_realval.py`](prepare_realval.py) | Real validation set A/B (split by scenario), realism proxies (guarded) | `real/raw/` | `pcdet/realval-v1/`, `pcdet/realism-proxy-{1..5}/` |
| [`prepare_g1.py`](prepare_g1.py) | Engine G1: UT frames + ray-cast walkers (OS1-64 model), optional FOV mask, real placement prior | `ut/`, `gen/os1_64_calib_v1.npz`, `gen/walker_prior_v1.npz` | `pcdet/g1-v*/` |

## 2. Sources and licences

| Source | Where | Size | What we take | Licence | Status (2026-10-02) |
|---|---|---|---|---|---|
| Starting kit | CodaBench 16685, Files tab (login) | 22.3 MB | everything | challenge terms | ingested |
| UT-V2X-Real-IC | Dataverse doi:10.7910/DVN/N6N4UR (10 zip parts) | 21.3 GB | `pcd`, `lbl`, `sem_seg`, `ins_seg` | **CC0** | downloaded and verified |
| V2X-Real | project page `https://mobility-lab.seas.ucla.edu/v2x-real/`; Lidar-64 release on UCLA box (share ids in `track.yaml`) | 28.3 GB | agent -1 bins of all splits (7,742 frames), yaml of guard-allowed frames (4,853) | **UCLA Academic; "All Rights Reserved"** | downloaded on the entrant's instruction ([decision record](../docs/decisions/2026-09-30-rules-real-data-download.md)); legal sign-off open |

## 3. Data on disk

```
$BDC_DATA/v2x-track/
├── kit/                     # starting kit + kit_report.json + id_mapping.json + id_mapping_report.json
├── ut/UCF-DT-V2X-Real-Seq-1/{pcd,lbl,sem_seg,ins_seg}/
├── real/raw/{train,val,test}/<scenario>/-1/<frame>.bin (+ .yaml for guard-allowed frames), real/access_log.csv
├── pcdet/<version>/         # OpenPCDet datasets (Section 9)
└── gen/                     # os1_64_calib_v1.npz (measured beam table), walker_prior_v1.npz (legal walker rows)
```

## 4. The sensor and the frame

The scored sensor is the infrastructure **Ouster OS1-64 (agent -1)**. Measured on legal unlabeled frames (`gen/os1_64_calib_v1.npz`):

| Property | Value |
|---|---|
| Layout | organized 64 x 1024 (65,536 points per bin, float32 x 4), 10 Hz |
| Beam table | rows +16.13 to -16.77 deg, median spacing 0.53 deg; each ring has constant elevation in the bin's frame (std 0.06-0.07 deg), so **the bins are in the sensor's own frame** (the mount itself is tilted a few degrees: V2X-Real `lidar_pose` roll -2.9, pitch -1.6 deg) |
| Valid returns | 76% of a raw bin; the rest are (0,0,0) nulls (kept by the organizers: 31% of a 50k test frame) |
| Organizer frames | mask to range, then a 50k draw; since only about 51k raw points (35k valid + 16k nulls) lie in range, the draw keeps almost all of them |
| Scene | sloped campus: walker box bottoms at -3.5 m near the pole, about -2 to -1 m at 10-30 m, -4.7 m beyond 30 m |
| Near field | no returns below -16.8 deg: within about 10 m only the upper body of a person is visible (median hit height 1.41 m) |

**UT-V2X uses a different, wider sensor** at the same pose: about 106k points per frame (69k valid in range), elevations from -56 to +25 deg, so it sees ground under the pole that the real unit never returns. Its rings vary with azimuth in this frame (a level CARLA lidar whose points were rotated into the real, tilted sensor frame; a plane fit to the sloped ground is 6 deg from z, 3.4 m below the origin). Consequences: `ut-v1` resamples UT to the real valid count (35,000); `g1-v3` also masks UT points to the measured OS1-64 field of view.

## 5. Classes

**Official super-class map** (`track.yaml` `real.super_class_map`, from OpenCOOD):
vehicle = LongVehicle, Car, PoliceCar; pedestrian = Child, RoadWorker, Pedestrian, Scooter, ScooterRider, Motorcycle, MotorcyleRider, BicycleRider; truck = Truck, Van, TrashCan, ConcreteTruck, Bus. Other types are dropped (`bdc26.classmap.v2x_super_class`; note the dataset's spelling `MotorcyleRider`).

Legal real statistics (`pcdet/realval-v1`, realval-A = 688 frames):

| Class | Per frame | Median l x w x h (p10 / p90 length) |
|---|---|---|
| vehicle | 8.1 | 4.64 x 2.06 x 1.68 m (4.16 / 5.13) |
| pedestrian | 16.2 | 0.71 x 0.72 x 1.73 m (0.54 / 1.00); 70,818 walker rows (Pedestrian, Child, RoadWorker) on legal frames |
| truck | 1.7 | 8.20 x 2.88 x 2.58 m (5.84 / 12.64) |

**UT-V2X classes** (`track.yaml` `ut.class_map`): Car, Unknown -> vehicle; Van, Truck, Bus -> truck; BicycleRider, MotorcyleRider -> pedestrian. **UT-V2X has no walking pedestrian**: engine G1 adds them.

Labels are OPV2V-style yaml per frame (world `location`, half `extent`, `angle` [roll, yaw, pitch] in degrees, `lidar_pose`); `bdc26.io.v2x.labels_in_sensor_frame` converts them exactly as OpenCOOD (`x1_to_x2`), keeping yaw only, full extents.

## 6. Forbidden frames, ID mapping and guard

- Challenge IDs are `<scenario index>_<6-digit frame>`. The index-to-folder mapping is not published, so `resolve_test_ids.py` recovers it:
  1. exact point matching of each of the 50 test frames against raw agent -1 frames with the same frame number (the organizers' frames are subsets of raw points): **26 indices resolved, all V2X-Real train-split scenes**;
  2. the resolved indices are strictly increasing positions in the sorted list of the 43 train scenes (the challenge indexes a sorted subset). Each of the 6 indices that occur only among the realism-reference IDs (17, 18, 19, 25, 26, 31) lies between resolved neighbours, so it maps to the **list of 1-3 candidate scenes** in that gap;
  3. anything still unresolved would map to `"*"` (block that frame number in every scene); none remains.
- The guard blocks every forbidden frame +/- 20 frames in its scene, in every candidate scene for listed indices, and refuses all V2X real data until `kit/id_mapping.json` exists. `fetch_real.py --labels`, `prepare_realval.py`, `prepare_g1.py` (walker prior) and the calibration scripts go through it; every access is logged in `real/access_log.csv`.
- V2X-Real val and test splits contain no forbidden frame; 4,853 of 7,742 agent -1 frames have guard-allowed labels.
- The day-0 research-exposure frames were checked against the resolved guard ([decision record](../docs/decisions/2026-09-30-rules-research-exposure.md)).

## 7. Preparation pipeline, step by step

```bash
python data-v2x-track/fetch_ut.py                                              # 21 GB
python data-v2x-track/ingest_kit.py common/kit/v2x_real_starting_kit.zip
python data-v2x-track/prepare_ut.py --name ut-v1                               # baseline training data
python data-v2x-track/fetch_real.py --accept-licence --points --workers 16     # agent -1 bins of all splits
python data-v2x-track/resolve_test_ids.py                                      # kit/id_mapping.json (guard)
python data-v2x-track/fetch_real.py --accept-licence --labels --workers 16     # yaml of allowed frames only
python data-v2x-track/prepare_realval.py --name realval-v1 --stride 5          # realval A/B + realism proxies
OMP_NUM_THREADS=1 python data-v2x-track/prepare_g1.py --name g1-v3 --workers 48 \
    --walker v2 --placement prior --walkers 16 --density-gain 2.5 --fov-mask    # selected corpus (Section 8)
```

- `pcdet/realval-v1`: every 5th guard-allowed labeled frame, masked and resampled to 50,000 points **keeping the nulls** (null fraction 0.309, like the test frames); split by scenario (md5 of the name): `val` = **realval-A** (688 frames, selection), `valB` = **realval-B** (298 frames, check). Never used for training.
- `pcdet/realism-proxy-{1..5}`: 5 x 50 disjoint realval frames for local realism scoring.
- The walker prior `gen/walker_prior_v1.npz` is built on first use of `--placement prior`; the beam table `gen/os1_64_calib_v1.npz` was fitted once on 23 legal unlabeled frames (per-ring elevation medians; a search for a residual rotation between the bins and the beam axes found none).

## 8. Engine G1 for V2X, and its calibration

Same machinery as Track 1 ([`data-lumpi-track/README.md`](../data-lumpi-track/README.md) Section 8.7): procedural walkers ([`pedsim.py`](../common/bdc26/render/pedsim.py)), analytic ray casting with the sensor model, exact occlusion of frame points behind walkers, range-image blocking of walker returns behind geometry. V2X specifics:
- one sensor, the OS1-64 at the frame origin (the frame is its sensor frame);
- UT-V2X points are resampled to 35,000 valid points per frame, so walker returns need more azimuth columns than the real 1,024 to end up at the real density after resampling (`--density-gain`);
- `--fov-mask` drops UT points outside the measured OS1-64 field of view (+16.4 / -17.0 deg with half-step margins);
- `--placement prior` copies position, heading, l/w/h and the **ground height (box bottom)** of a random legal real walker row; UT-V2X is aligned with the real sensor frame, so real positions are valid in UT frames.

Calibration (walker points at 50k, median by range; real = realval-A walkers, 10,742 boxes):

| Corpus | Settings | 0-10 m | 10-20 m | 20-30 m | 30-45 m |
|---|---|---|---|---|---|
| real | | 46 | 36 | 19 | 7 |
| `g1-v1` | walker v1, free placement, KITTI-like boxes, gain 1.5 | 78 | 24 | 8 | 4 |
| sweep | v2, prior placement, gain 3.0, no FOV mask | 136 | 41 | 17 | 6 |
| sweep | + FOV mask, ground from the frame | 151 | 40 | 18 | 6 |
| **`g1-v3`** | + ground from the real box bottom, gain 2.5 | **52** | **40** | **18** | **7** |

The near-field excess in the middle rows came from where walkers could be placed: with ground estimated from the (masked) frame, only walkers on raised spots near the pole survived; real box bottoms remove that bias.

## 9. Dataset versions (`$BDC_DATA/v2x-track/pcdet/`)

| Version | Built by | Content | Used by |
|---|---|---|---|
| `ut-v1` | `prepare_ut.py --name ut-v1` | UT-V2X, super-classes, 35,000 valid points in range; frames 0-8999 train, 9000-9999 val | `pointpillars-ut` |
| `smoke-v2x` | `prepare_ut.py --name smoke-v2x --frames 1000` | first 1,000 frames | smoke tests |
| `realval-v1` | `prepare_realval.py --stride 5` | real, guard-allowed: A 688 / B 298 frames, 50k points with nulls | validation only |
| `realism-proxy-{1..5}` | `prepare_realval.py` | 5 x 50 disjoint realval frames | local realism only |
| `g1-v1` | `prepare_g1.py --name g1-v1` | `ut-v1` + Poisson(12) walkers v1, free placement, KITTI-like boxes, gain 1.5 | `pointpillars-g1` |
| `g1-v2` | `prepare_g1.py --name g1-v2 --walker v2` | `g1-v1` with the v2 body | `pointpillars-g1v2` |
| `g1-v3` | `prepare_g1.py --name g1-v3 --walker v2 --placement prior --walkers 16 --density-gain 2.5 --fov-mask` | calibrated walkers (Section 8), FOV-masked UT | `pointpillars-g1v3` |

## 10. What we measured

| Finding | Evidence | Consequence |
|---|---|---|
| UT-V2X emulates a denser, wider sensor | 69k vs 35k valid points in range; elevations -56..+25 vs +16.1..-16.8 deg | resample to 35k (`ut-v1`); FOV mask (`g1-v3`) |
| The real bins are in the OS1-64's own frame, 64 x 1024 | ring elevations constant in the bin frame | walkers cast in frame coordinates with the measured table |
| Test frames keep (0,0,0) nulls | 31.1% in the kit frames; 30.9% in realval | realism frames get 31% nulls at packaging (`track.yaml` `resample.null_fraction`) |
| All resolved forbidden frames are train-split scenes, indexed as a sorted subset | 26 indices at increasing sorted positions | V2X-Real val/test splits fully legal; bounded candidates instead of wildcards |
| UT-V2X has no walking pedestrian | label scan | G1 walkers |
| v1 walkers are too sparse beyond 10 m and look too dense near the pole | Section 8 table | `g1-v3` calibration |
| Real pedestrian boxes follow the KITTI-like convention closely | 0.71 x 0.72 x 1.73 m | prior placement copies real boxes in `g1-v3` |
| Masking UT points to the OS1-64 field of view improves realism | held-out proxies (31% nulls, official scorer): R 0.901 (`g1-v1`) -> 0.916 (`g1-v3`), 0.922 after frame selection | realism frames from `g1-v3` |
| Calibrated walkers detect real pedestrians much better | realval-A pedestrian AP 0.118 (`g1-v1`) -> 0.173 (`g1-v2`) -> 0.266 (`g1-v3`) | `pointpillars-g1v3` is the pedestrian member of `routed-g1` |

## 11. Pitfalls

- Pedestrians and riders share one class: two size modes in one class (anchors [0.8, 0.6, 1.73] and [1.76, 0.6, 1.73]).
- Never use agent -2 (OS1-128): different pose and field of view.
- `BDCDataset.get_lidar` strips nulls for detection; realism and realval frames keep them.
- GT-sampling needs datasets spanning the whole UT sequence (riders are sparse early on).
- Predictions must be in agent -1's lidar frame (an ECCV-edition platform bug once exported GT in the world frame: every AP was exactly 0).

## 12. Next steps (data side)

1. Background density calibration for V2X realism (as Track 1), now that legal proxies exist.
2. Riders and scooter riders in the real conventions; containers and other truck-class objects from legal truck statistics.
3. Engine G2: re-simulate the static scene with the OS1-64 model including the null grid.
