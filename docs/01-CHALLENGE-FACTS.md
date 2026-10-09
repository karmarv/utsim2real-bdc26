# 01. Challenge facts (verified ground truth)

> Verified 2026-09-30, **updated 2026-10-02** with the ingested starting kits (their `scoring_program/` is the server's code) and the live CodaBench pages and API. Verified against:
> - the challenge site (`index.html`, `lumpi.html`, `v2x.html`) and its git history;
> - the CodaBench public API for the IEEE instances (16684 LUMPI, 16685 V2X-Real) and the finished ECCV/DriveX instances (16047, 16048): pages, phases, datasets, leaderboards;
> - the public per-submission "detailed results" pages of the top entries;
> - the starter-kit `config.json` copies committed by the ECCV winner (`github.com/amanupg/urbantwin-sim2real-{lumpi,v2x}`);
> - the four organizer papers and the organizer's generation script (`github.com/m-shahbaz-kharal/HiFi-DT-Utils`).
>
> The published normalization reproduces **all 60 public leaderboard rows to within 8e-5**. Items marked **ASK** must be confirmed with the organizers (Section 10). The evidence behind these facts is summarized in `07-LITERATURE.md` Section 2 (ECCV edition) and Section 4 (licences).

---

## 1. Tracks

| | Track A: LUMPI (CodaBench 16684) | Track B: V2X-Real (CodaBench 16685) |
|---|---|---|
| Real dataset | LUMPI, Leibniz University Hannover, Koenigsworther Platz | V2X-Real, UCLA, infrastructure-centric (IC) subset |
| Scored classes | Person, Car, Bicycle, Motorcycle, Bus, Truck, Van, Unknown | vehicle, pedestrian, truck |
| **Classes with test GT (the mean is over these)** | **7** (Unknown has 0 GT) | 3 |
| Point-cloud range | `[-40, -40, -5, 40, 40, 5]` | `[-40, -40, -8, 40, 40, 2]` |
| Test-frame IDs | `006498` ... `008100` (6-digit, one Measurement) | `<scenario>_<frame>`, e.g. `10_000043` (32 scenarios) |
| Forbidden window | all 100 IDs lie in **006497-008109**: one ~161 s window, which is the last 20% of LUMPI Measurement4 (the organizers' paper test split) | spread over 32 scenarios, 1-7 per scenario |
| Real sensor(s) | 5 LiDARs merged (Pandar64, HDL-64E S3, PandarQT, 2x VLP-16), tripod height; Measurement4 local frame, ground about z = -2.1 m | **Ouster OS1-64 (V2X-Real agent -1)**, 64 x 1024, about +/-16.7 deg, about 2.2 m above local ground; sensor frame; (0,0,0) null returns |
| Real-data licence | **CC BY-NC 3.0** | **Academic only ('All Rights Reserved')** |
| Organizer synthetic set | UT-LUMPI, doi:10.7910/DVN/D9SSWD, 10K frames, xyz only, about 52 GB, **CC0**; actors at **0.78x** real size | UT-V2X-Real-IC, doi:10.7910/DVN/N6N4UR, 10K frames, xyz only, about 21 GB, **CC0**; wide-FOV sensor emulation |
| Published reference (Car only) | SEED UT-trained 0.4474 | SECOND UT-trained 0.6318 |
| Participants (2026-10-02) | 31 (165 submissions) | 34 (164 submissions) |

The organizers state the UT datasets "may serve as training data or as a template for participants' own synthesis".

## 2. Timeline

CodaBench phase boundaries are in UTC. US daylight saving time ends Sun Nov 1, 2026.

| Event | UTC | Pacific | Central |
|---|---|---|---|
| Dev phase closes | 2026-10-31 00:00 | Fri Oct 30, 17:00 PDT | Fri Oct 30, 19:00 CDT |
| LOI form closes (if not already filed) | 2026-10-31 00:00 | Fri Oct 30, 17:00 PDT | Fri Oct 30, 20:00 EDT (stated) |
| Final phase opens | 2026-11-01 00:00 | Sat Oct 31, 17:00 PDT | Sat Oct 31, 19:00 CDT |
| **Final phase closes** | 2026-11-15 00:00 | **Sat Nov 14, 16:00 PST** | **Sat Nov 14, 18:00 CST** |
| Challenge report (4-8 pages) | Nov 15 | | |
| Cup camera-ready / final report and solutions | Nov 20 | | |
| Winners | Nov 25 | | |
| IEEE BigData 2026, Phoenix | Dec 14-17 | | |

| Phase | Per day | Total | Leaderboard | Notes |
|---|---|---|---|---|
| Development | 5 | 100 | Public, `Force_Best` | Scored on the **same** test and reference data as the final phase |
| Final | **1** | **5** | Hidden until close, `Force_Best` | Dev submissions are not carried over |

Execution limit per submission: 1200 s. Prize pool: USD 2,000 (per track $500 / $300 / $200). Top-3 per track are invited to the paper track (CyberChair subarea SC04, up to 10 pages including references, IEEE two-column) and must be ready to release code for verification.

## 3. Rules

The CodaBench Terms (item 1) bind you to the **Rules tab**:

**Allowed**
- "Any simulation framework or generative model (CARLA, Helios++, OpenScene, neural radiance fields, diffusion, GANs, custom physics). Open or closed source, what matters is the synthesized data."
- "Any 3D object detector architecture, trained on your synthetic data only."
- "Augmentations applied during detector training (rotation, scale, flip, ground-truth sampling, noise)."
- **"Using the train split of the public real dataset for hyperparameter selection or domain adaptation, provided no forbidden frame is touched."**

**Forbidden**
- "Training, validating, hyperparameter-tuning, or otherwise observing ground truth from any of the 100 frames listed in `forbidden_frames.txt`."
- "Submitting predictions produced by a model that has been trained on real labels for any roadside-LiDAR dataset."
- "Reverse-engineering or inferring the held-out realism reference frames via Codabench's leaderboard signal (e.g., probing submissions ...)."
- Multiple accounts, sub-team accounts, cross-team coordination.
- The website adds: "Using real data for training, including fine-tuning. The detector must be trained on your synthetic data only." (The website wording was tightened and then softened on Jul 7; the CodaBench Rules tab kept the Allowed clause.)

**Disqualification:** organizers may inspect submissions for "synthetic frames that suspiciously resemble held-out real frames" and "predictions whose distribution implies access to held-out ground truth". The organizer has published his own leakage study on another benchmark, so expect scrutiny.

**Declaration (verbatim):** "I confirm that I did not train on any frame listed in forbidden_frames.txt, and that all submitted detections were produced by a model trained only on synthetic data I generated."

### 3.1 Our operating interpretation

| Use of real data | Status |
|---|---|
| Real **labeled** non-forbidden frames as a **validation set** (checkpoint, architecture, augmentation, NMS, ensemble selection) | **Allowed** ("hyperparameter selection") |
| Real label **statistics** (class frequencies, box-size distributions, box conventions, placement heatmaps) to set generator parameters | **Allowed**; state it in the report |
| A handful of post-processing scalars (per-class NMS IoU, size scale factors, score re-weighting) selected on real val | **Allowed as hyperparameter selection**; ASK to be safe, and prefer fixing sizes in the generator |
| Real unlabeled frames to measure the sensor (beam table, pose, null-return rate, ray-drop statistics) | **Allowed** (the organizers estimated sensor pose from a real frame) |
| Gradient-free adaptation at inference (background occupancy prior from train-split frames, BN statistics) | **Likely allowed** ("domain adaptation"); ASK |
| Self-training / pseudo-labels on unlabeled real frames | **Gray**; ASK; default off |
| Generator fitted to real scans (reconstructed static mesh, learned ray-drop, diffusion trained on real) | **Gray**; ASK; default off |
| Affine or quantile warping applied **only** to the 50 submitted frames to match real moments | **Avoid.** Not forbidden, but it decouples the submitted frames from the training data, and the winners tuned it with server probes |
| Using statistics of the 50 released test point clouds for anything but running inference | **Forbidden** (they are forbidden frames) |
| The starter kit's `reference_data_local/realism_reference/` frames | **Forbidden for fitting**: a competitor found them byte-identical to the 50 detection-test frames. Use it only to check that `local_eval.py` runs |
| **Hidden-GT reference bundles** that the CodaBench API reportedly exposes | **Never download.** That is observing forbidden ground truth (disqualification) |
| Any real frame in LUMPI **006400-008200**, or within +/-20 frames of a V2X forbidden frame | **Self-excluded** (near-duplicates of forbidden frames; avoids the "suspiciously resemble" clause) |

## 4. Scoring (exact)

### 4.1 Formula and endpoints (`config.json`, identical for both tracks)

```
score_detection = clip( mAP / 0.70 , 0, 1 )          # mAP = mean over classes with GT of 3D AP@0.5, R40
score_realism   = 1 - 1/4 * [ clip((CD - 2.0)/28.0) + clip(MMD/0.5) + clip(EMD/5.0) + clip(FPD/50.0) ]
score_combined  = 0.6 * score_detection + 0.4 * score_realism
```

`normalization`: CD [2.0, 30.0], MMD [0.0, 0.5], EMD [0.0, 5.0], FPD [0.0, 50.0], AP [0.0, 0.7].

### 4.2 Realism protocol (the kit's `scoring_program/metrics.py`; reproduced bit-for-bit by `common/bdc26/realism.py`)

1. Concatenate the 50 synthetic frames and the 50 real reference frames (float32; N x 4 files drop the 4th column).
2. **Mask to the range first, bounds inclusive** (`>=` and `<=`), then subsample to 10,000 points per side.
3. **One** numpy `default_rng(1234)` draws, in order: the synthetic subsample, the real subsample (without replacement unless fewer than 10k points), then 1,000 + 1,000 points for the MMD bandwidth.
4. Points at **(0,0,0) are kept** (they are inside the range).
5. CD = mean squared nearest-neighbour distance, both directions summed; MMD^2 unbiased RBF on the full 10k x 10k matrices, gamma = 1 / (2 median squared distance) over the 2,000 bandwidth points, zero distances dropped; **EMD = sqrt(W1)** with POT `ot.emd2(numItermax=10_000_000)` (converged); FPD = Frechet distance between 3-variate Gaussians.
6. The real reference is **50 frames x 50,000 points** on both tracks (the organizers resample real frames to 50k after masking). **31.1% of V2X test-frame points are (0,0,0) null returns** (measured on the kit's test frames, format only); a synthetic set without that point mass pays a large EMD/CD penalty.
7. Normalization endpoints come from `config.json`; `n_realism_frames` there must equal the number of submitted frames (50 on the server; the kit's dummy config says 5).
8. **Submit N x 3 float32.** A file of 150,000 floats was parsed as N x 3; an N x 4 file whose length is divisible by 3 is read as N x 3.

### 4.3 Detection protocol (the kit's `scoring_program/detection_eval.py`; reproduced bit-for-bit by `common/bdc26/evalap.py`)

- Per class and IoU threshold (0.5 primary, 0.7 reported), over the frames of `detection_gt.json`:
  1. in each frame, the class's predictions sorted by score (stable) each take the **unused GT of the class with the highest IoU** and are true positives if that IoU >= threshold (VOC-style greedy matching, prediction-centric, not KITTI's GT-centric statistics);
  2. predictions in frames without GT of the class are false positives;
  3. all predictions pooled and ordered by score (`np.argsort(-score)`); precision / recall curve; **AP_R40 = mean over r in {1/40, ..., 1} of max precision at recall >= r** (AP_R11 over {0, 0.1, ..., 1}).
- 3D IoU = shapely polygon intersection of the BEV rectangles x z overlap / (vol_a + vol_b - inter); BEV IoU = polygon IoU; boxes `[x, y, z, dx, dy, dz, heading]` in the LiDAR frame, full extents; **180-degree heading flips do not change IoU**.
- Class strings compare **case-insensitively**; a missing `class` defaults to "Car"; unrecognized class strings are discarded. Classes with 0 test GT are excluded from the mean (NaN). No KITTI difficulty filter; **no range or point-count filter on GT or predictions** in the code (GT filtering, if any, happened when the organizers built `detection_gt.json`).
- **No cap on predictions** (18k and 56k boxes both scored); scores must be in [0, 1] per the format spec; the **same box may be emitted under several classes** (per-class AP is independent).
- The Evaluation page calls this "KITTI 40-point interpolated AP"; the shipped code is the authority.

### 4.4 What the score math implies

```
combined = 0.857 * mAP + 0.4 * R        (mAP <= 0.70)
```

| Lever | Marginal value (combined) |
|---|---|
| +0.01 mAP | +0.0086 |
| One LUMPI class from AP 0.05 to 0.35 (1 of 7) | +0.037 |
| V2X pedestrian from AP 0.19 to 0.45 (1 of 3) | +0.074 |
| EMD -0.1 m | +0.0020 |
| CD -1.0 | +0.0036 |
| FPD -1.0 | +0.0020 |
| MMD -0.001 | +0.0002 |

- **EMD is the dominant realism term** (EMD/5 is 0.23-0.37 for good entries; the others are 0.00-0.04 each).
- **Realism ceilings** measured by a competitor on independent real-vs-real sets: V2X 0.961, LUMPI 0.933-0.947; real-vs-real EMD on 10k samples is about 0.9-1.0 m. The best observed synthetic R is 0.925 (V2X) and 0.937 (LUMPI). **Randomly chosen raw UT-LUMPI frames score only about 0.59** (per the ECCV winner), so LUMPI realism needs deliberate work; raw UT-V2X frames score about 0.83.
- **Detection decides rankings.** The largest open gaps are per class (Section 7.2).
- **Never threshold aggressively.** Interpolated AP cannot decrease when lower-scored boxes are added. Keep a low score floor and many boxes.
- **Always predict every class**, including Van for LUMPI (79 test GT) and Unknown (excluded anyway, so harmless).

## 5. Submission format

```
submission.zip
├── synthetic/
│   ├── 0001.bin ... 0050.bin     # exactly 50; raw float32 row-major N x 3 (x,y,z metres); each <= 1.5 MB (~125k pts)
├── predictions.json              # one key per ID in detection_test_frame_ids.json (empty list allowed)
└── declaration.pdf               # signed; declaration.txt with the verbatim statement also accepted
```

```json
{ "<frame_id>": [ {"box": [x, y, z, dx, dy, dz, heading], "score": 0.97, "class": "Car"} ], "<frame_id_2>": [] }
```

Server checks (`score.py`): declaration (PDF starting with `%PDF`, or text containing "I confirm that I did not train on any frame listed in"); exactly `n_realism_frames` files in `synthetic/`, each <= 1,500,000 bytes; `predictions.json` keys **exactly** the expected IDs (missing or extra IDs fail); each detection a dict with `box` (7 values) and `score`. The format spec adds: total uncompressed size under about 75 MB; score in [0, 1]; valid class strings (others discarded).

Our validator (`common/bdc26/submit.py`, module M3) checks all of these plus: each file a multiple of 12 bytes (N x 3 float32), no NaN/Inf, positive box extents, finite scores; and reports the in-range and (0,0,0) fractions.

## 6. Starting kit (ingested 2026-10-02; `data-<track>/ingest_kit.py`)

| File | Use |
|---|---|
| `scoring_program/{score.py, detection_eval.py, metrics.py}` | the server's scoring code (identical for both tracks); parity tests in `common/tests/test_official_parity.py` |
| `local_eval.py` | runs `score.py` locally on a zip with a reference folder (`python local_eval.py submission.zip [reference_dir]`) |
| `reference_data_dummy/` | `config.json` (track name, range, class names, test IDs, normalization, `n_realism_frames: 5`), 5 token realism frames, empty `detection_gt.json`: a **format check only**; to get a meaningful local realism score, put 50 legal frames there and set `n_realism_frames` to 50. Never fit anything to kit data |
| `detection_test_frames/` + `detection_test_frame_ids.json` | the 50 inputs (LUMPI: exactly 50,000 points per frame, all in range; V2X: 49,405-50,000 points, 31.1% nulls); inference and format checks only |
| `forbidden_frames.txt` | 100 IDs (50 test + 50 realism reference) fed to the ForbiddenGuard |
| `make_dummy_submission.py`, `submission_format.md`, `declaration_template.{pdf,txt}`, `requirements.txt` (numpy >= 1.24, scipy, shapely >= 2.0, POT >= 0.9) | format reference; the scorer also runs on numpy 1.23.5 |

V2X forbidden IDs: all 26 scenario indices that occur among the test IDs resolve, by exact point matching, to **V2X-Real train-split scenes**, at strictly increasing positions in the sorted train-scene list; the 6 indices that occur only among the realism-reference IDs are bounded to 1-3 candidate scenes each (`data-v2x-track/README.md` Section 6). V2X-Real val and test splits hold no forbidden frame.

## 7. Leaderboard intelligence

### 7.1 Overall (R = back-computed realism score)

**ECCV V2X final (same scorer and data as IEEE):** amanupg 0.7457 (mAP 0.438, R 0.925); luopuu 0.7421 (mAP 0.452, R 0.887); loopy 0.6512.
**ECCV LUMPI final:** amanupg 0.4793 (mAP 0.133, R 0.913); y1nnng 0.4782; best realism R 0.937 (deleted user).
**IEEE live (2026-10-09, public leaderboard API):** V2X: KarmaRV 0.7855 (972563, mAP 0.487, R 0.920), linyongchun 0.6616 (972310, mAP 0.354, CD 2.72, EMD 1.72, FPD 2.07), IAsystems 0.5375; 19 entries. LUMPI: **Raj Patil 0.4784** (966997, Oct 7: mAP 0.1185, 3D@0.7 0.016, CD 0.877, MMD 0.0001, EMD 1.108, FPD 0.498, so R about 0.942, above the best ECCV realism 0.937 and near the real-vs-real ceiling 0.933-0.947), KarmaRV 0.4728 (965614), tesla2026 0.2769; 18 entries. Earlier (2026-10-02): V2X leader 0.6114, LUMPI leader 0.2769; sixteen accounts shared one template (dummy LUMPI frames, raw UT-V2X frames, exactly 100 boxes per frame). Expect the ECCV teams to enter late.

### 7.2 Per class (test GT counts are shown publicly on every detailed-results page)

| Track | Class | Test GT | Best AP (team) | Winner's AP | Our target |
|---|---|---|---|---|---|
| V2X | vehicle | 470 | 0.670 (luopuu) | 0.592 | 0.70 |
| V2X | **pedestrian** (includes cyclists and scooter/motorcycle riders) | **953** | **0.189** (amanupg) | 0.189 | **0.45** |
| V2X | truck (includes TrashCan 42%, Van, Bus) | 124 | 0.592 (luopuu) | 0.533 | 0.60 |
| LUMPI | **Person** | **512** | 0.206 (luopuu) | 0.149 | **0.40** |
| LUMPI | Car | 1258 | 0.643 (amanupg) | 0.643 | 0.66 |
| LUMPI | Bicycle | 82 | 0.187 (thedev) | 0.078 | 0.30 |
| LUMPI | Motorcycle | 27 | 0.118 (IEEE cohort) | 0.020 | 0.15 |
| LUMPI | Bus (GT mostly two-wheeler sized per a competitor's inspection) | 25 | 0.021 | 0.000 | 0.05 |
| LUMPI | **Truck** | **192** | 0.068 | 0.011 | **0.30** |
| LUMPI | Van (LUMPI id 6 "unknown" objects; [`data-lumpi-track/README.md`](../data-lumpi-track/README.md) Section 5) | 79 | 0.077 | 0.032 | 0.20 |

What this says:
- **V2X pedestrian is the single biggest open lever** (62% of test objects, best AP 0.19). The class mixes walkers (about 0.74 x 0.72 x 1.73 m) and riders (about 1.8 x 0.8 x 1.75 m).
- **LUMPI Person, Truck, Bicycle and Van** are all far below what a good synthetic pipeline should reach.
- 3D mAP@0.7 is near zero for everyone, and BEV exceeds 3D by 0.05-0.09 on V2X: **box height and z-centre conventions are systematically off**. UT synthetic boxes are about 17% smaller in volume than the human labels.

### 7.3 What the ECCV winners did (public reports; read for ideas, their code has no licence)

- **amanupg (1st both tracks):** PointPillars trained on UT twin data plus ray-cast inserted pedestrians, cyclists and (V2X) trash cans. The main levers were post-processing: per-class NMS (V2X pedestrian IoU 0.7 took mAP from 0.075 to 0.43), pedestrian re-centering on interior points, size calibration against real labels, density-based re-ranking, and Van/Car duplicate emission. Realism: frame selection, density resampling, per-axis affine moment alignment tuned by server probes, and injected (0,0,0) nulls for V2X.
- **luopuu (2nd V2X; arXiv:2609.07590, 2609.07608):** resampled synthetic frames to 50k points (native density overstates real-val mAP), added RangeLDM diffusion redraws, used DSVT plus PointPillars specialists with per-class fusion, and resized pedestrians to real dimensions (synthetic ones were 1.84 m long, capping IoU near 0.35).
- **Common gap:** nobody generated pedestrians and riders that match the real annotation conventions, and nobody modelled the real multi-sensor beam tables.

## 8. Known platform issues

- V2X: GT was once exported in the world frame (every class AP = 0.0000). Fixed on 2026-07-25; the IEEE instance uses the fixed data. If every class returns exactly 0, report it at once.
- The starter kit's `reference_data_local/realism_reference/` duplicates the test frames (see Section 3.1).

## 9. Integrity practice (for the report)

- One `ForbiddenGuard` in every real-data loader, plus the self-exclusion windows in Section 3.1, and a log of every real-data use.
- Submitted synthetic frames come from the same generator configuration as the training corpus; frame selection is done against our own legal real proxy.
- No realism probes, no use of test-frame statistics, no metric-only warping.
- Keep the local score next to every submission ID.

## 10. Questions for the organizers (email Muhammad.Shahbaz@ucf.edu on day 1)

1. Is self-training or pseudo-labeling on unlabeled, non-forbidden real train-split frames permitted as "domain adaptation"?
2. May a generator be fitted to non-forbidden real scans (reconstructed static scene, learned ray-drop, diffusion model), and may a static-background occupancy map from train-split frames be used at inference?
3. May a small set of post-processing parameters (per-class size scale factors, NMS IoU) be selected on labeled non-forbidden real frames?
4. Does `local_eval.py` drop GT boxes with zero LiDAR points or outside the range, and are range bounds inclusive?
5. What is the exact report submission channel and format (Nov 15 report vs Nov 20 camera-ready)?
6. Please confirm our LOI registration for both IEEE tracks.
7. (Only if the clean re-uploads also fail.) Submissions 957399 (Track 1, Failed with no message) and 957439 (Track 2, Running for 4 days with no log, cancelled): can you see a worker error, and does the default queue give the scorer the 6 GB it needs for the 10k x 10k MMD?
