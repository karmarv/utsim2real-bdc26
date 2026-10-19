# Sensor, Scene, Scribe (S3): value, strategy, framework and execution plan

> Branch `synth-cv`. Written 2026-10-18 after pilot P0. It sets the order of work for the research line and turns the CVPR idea of [`RESEARCH-AGENDA.md`](RESEARCH-AGENDA.md) Section 13 into a framework, **S3-Twin**, that applies to any UrbanTwin site. Evidence references: P0 records in `synth-<track>-track/experiments/P0-scribe-pilot/`; literature R1-R124 ([`LITERATURE.md`](LITERATURE.md), `docs/07-LITERATURE.md`).

## 0. Brief

**The idea in one paragraph.** A synthetic LiDAR dataset is made in three steps:
1. a scene is built;
2. a sensor scans it;
3. someone draws the boxes.

Real datasets go through the same three steps, so a twin can be wrong in three places: the **sensor** (beams, drop, noise, timing), the **scene** (what objects and clutter exist, and where), and the **scribe** (which objects get a box, how big, where, with which class). The field has worked hard on the sensor and somewhat on the scene. Nobody models the scribe; every simulator emits exact geometric boxes. Our pilot shows the two real datasets label in opposite ways:
- LUMPI keeps boxes on objects the sensor cannot see;
- V2X-Real drops objects with fewer than about 6 points;
- our synthetic labels follow neither.

**S3 models all three factors.** It calibrates each one only from what the rules allow us to see (unlabeled real scans and label statistics), and it measures how much of the sim-to-real gap each factor explains.

**Why a top venue would care.**
1. **A new, general insight:** the sim-to-real gap has a third component that no simulator models. It is measurable and differs between datasets.
2. **A cheap new method:** a scribe changes labels, not renders, so it costs no simulation.
3. **A principled engine:** CTD (likelihood-free, misspecification-aware calibration) makes the twin's parameters inferred, not hand-set.
4. **A quantitative answer to an old question:** where the gap of a LiDAR twin lives, across three real sites.
5. **A reusable framework:** S3-Twin, applicable to any twin.

**The sequence in one line.** Prove the cheapest, most novel effect first (scribe-only label swap). Then add the scene and sensor factors in order of value per cost, put them under one calibration engine, run the decomposition on three sites, and release the framework.

**What we publish when.**

| Venue | Deadline | Content | Condition |
|---|---|---|---|
| CVPR 2027 | Nov 16, 2026 | S3 decomposition and the scribe twin, CTD-lite calibration, 2-3 sites, PointPillars and CenterPoint | gate G3 (Section 5) passes |
| ICCV 2027 | about early March 2027 | the full S3-Twin: joint robust calibration, time-aware sensor, paired consistency, Voxel R-CNN, CARLA to KITTI check | default if G3 fails; otherwise the journal or follow-up version |
| NeurIPS 2027 Evaluations and Datasets | about mid-May 2027 | the S3 benchmark across twins, plus evaluation science (agenda Section 12) | after CVPR |

## 1. Value assessment: which approach carries a top-venue paper

Reviewers at CVPR, ICCV or NeurIPS look for four things:
- **(a) a new insight or problem formulation;**
- **(b) a method that is general and principled;**
- **(c) consistent gains on several benchmarks, with rigorous statistics;**
- **(d) something the community can reuse.**

The table scores each candidate on these against the closest prior work.

| # | Approach | Core idea | Closest prior work | (a) insight | (b) method | (c) evidence so far | (d) reuse | Cost | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Scribe twin** | a parametric labelling policy inside the generator (visibility, persistence, padding, size regime, taxonomy, z, yaw, label time), inferred from label statistics | SN (sizes), Synth It Like KITTI (hand shrink), PCGen (pedestrian loosening), LGPL (2D, learned from target labels) | **high**: a gap no simulator models | medium: simple model, principled inference | **strong**: P0 shows opposite policies, regimes and padding | high: any twin, no re-render | low | **headline** |
| 2 | **S3 decomposition** | a 2^3 factorial over sensor, scene and scribe (naive or calibrated), Shapley shares, error fingerprints across IoU thresholds | content vs appearance gap (Meta-Sim, images); Towards Zero Domain Gap (sensor factors, paired real data) | **high**: first three-factor answer for LiDAR | medium | the pilot shows all three gaps exist | high: a protocol for any twin | high GPU (800-1,000 GPU-hours) | **headline finding** |
| 3 | **CTD engine** (rev. 2) | robust or tempered SBI posterior for global sensor parameters, a source distribution for per-frame scene parameters, misspecification flags | BayesSim, NPDR (control), Meta-Sim (images, MMD), LiDAR-in-the-loop (CMA-ES) | medium alone ("SBI applied to LiDAR") | **high**: principled, uncertainty-aware | none yet | medium | medium CPU, low GPU | **the engine**, not the headline |
| 4 | Calibrated negatives (scene) | unlabeled clutter fitted to the real point mass the twin does not explain | Real-Aug, Sim2SG, our hand-set G2-lite clutter | medium | medium | static structures are 50-77% of unmatched walker detections; clutter halved them | high | low | **scene factor** |
| 5 | Time-aware multi-LiDAR rendering (sensor) | per-sensor phase offsets: each sensor sees moving actors at its own time | CoBEVFlow (feature level), calibration work | medium | medium | LUMPI smear median 0.27 m (90th percentile 0.59 m) | medium (multi-LiDAR sites) | medium | **sensor factor option** |
| 6 | Paired multi-render consistency | same scene, two sensor draws, consistency loss | SESS, LiDAR Distillation, CVGC (segmentation) | low-medium | medium | none | medium | about 2x training | ICCV version |
| 7 | Label-free target-in-the-loop generation | steer the generator by ensemble disagreement on unlabeled real frames, plus persistence-mined false positives | Deliberate Practice, ActGen (images) | medium-high | medium | seed bags give the ensemble | high | rounds of training | **paper 3** |
| 8 | Diversity scaling laws | AP against unique content vs frame count, at two fidelity levels | Fan et al., SOC (images) | medium-high | low (analysis) | none | high | about 800 GPU-hours | **paper 4** |
| 9 | Evaluation science | realism-metric reliability, transfer prediction from small tests | FID Lottery | medium | low | 15 scored versions | high | low | **paper 2** |
| 10 | Generative translation (DRUM-style) | learn real-looking scans | DRUM, RangeLDM | low | medium | | low | high | research-only upper bound |
| 11 | Self-training on real frames | pseudo-labels on real data | ST3D, MS3D | none | none | | | | out of bounds for this line |

**Reading.**
- CTD on its own is a good engine but a weak headline: SBI for simulator calibration exists in robotics, and reviewers will call it an application.
- The scribe is the new idea, and the decomposition is the finding that makes it matter.
- Together, with CTD as the calibration engine, they make one paper with all four of (a)-(d).

## 2. The strategic sequence

The order: cheapest decisive test first, then factors in order of value per cost, then the engine that unifies them, then the study, generality and release.

| Step | What we build | Precise novelty | Pros | Cons / risk | Process (sim -> train -> val) | Complexity | Value | Gate |
|---|---|---|---|---|---|---|---|---|
| **S3-0** Evidence (done) | `pilot_scribe.py`: label and point statistics, real vs synthetic | first measurement of labelling-policy differences between roadside datasets and a twin | cheap, read-only; de-risked the idea | descriptive only | statistics only | 1 day, CPU minutes | P0: opposite visibility policies, regimes, padding, sensor smear | done |
| **S3-1** Scribe v0 and the label swap (E-S0) | `synthtwin.scribe`: rules read directly off the statistics:<br>- V2X minimum points per class;<br>- LUMPI track persistence (0-point boxes);<br>- LUMPI manual-regime sizes;<br>- padding, z and height | the scribe as a generator stage; the first controlled label-only swap on fixed frames | no re-render; isolates the scribe effect; fast | single-factor, hand-read parameters | regenerate labels on the same `g1-v5` frames (min_points 0 plus per-actor hit statistics, then the scribe) -> PointPillars, 3 seeds -> realval-B AP at IoU 0.25, 0.5 and 0.7, static false positives per frame | 2 person-days; CPU minutes; 70-140 GPU-hours | decides whether the scribe leads the paper; possible spill-over to the challenge (V2X pedestrians) | **G1**: effect outside the interval on at least one track |
| **S3-2** Scribe inference | parametric scribe *a*, fitted from label-statistic summaries. Closed form where identifiable (truncation point, persistence rate, regime mixture); SBI for parts coupled with the sensor (visibility depends on drop) | inferring a multi-part labelling policy without target labels; identifiability analysis; label-budget curve | principled; answers "can you infer it?" | coupling with sensor drop; regimes need a regime cue | sim-to-sim: a known scribe applied to synthetic data must be recovered; real: fit on realval-A statistics from k = 10, 50, 200, 1,280 frames | 3 person-days; CPU | the method claim (S2); the "statistics are enough" curve | recovery within 90% intervals |
| **S3-3** Scene twin | calibrated negatives (clutter library parameters fitted to the residual real point mass by height, footprint, points and range histograms) and a per-frame source distribution of content (walker counts and styles, clutter density) | negatives calibrated to unexplained real mass; a fitted, not guessed, randomization distribution | targets the main walker error (static false positives) | the residual is also caused by sensor errors | simulate candidates (minutes) -> match residual summaries -> corpus | 3-4 person-days; about 10 CPU-hours | precision gains, mainly walkers | residual summaries closer than the hand values |
| **S3-4** Sensor twin | per-beam return and drop model (range, incidence), the V2X structured null map, per-sensor time phase for LUMPI (moving actors displaced per sensor; G2-lite casts each sensor separately) | time-aware multi-LiDAR rendering; label-free calibration of an identifiable fixed-sensor model | completes the decomposition | published drop gains are small; timing is secondary | robust SBI (TSNPE ensemble, 2-3 rounds, about 10^4 simulations of 64 frames) on unlabeled-scan summaries | 4-5 person-days; LUMPI about 12 CPU-hours, V2X about 2 | needed for S1; small AP on its own | coverage diagnostics pass |
| **S3-5** Joint engine (CTD) | one calibration over sensor, scene and scribe: robust and tempered posterior, source distribution, misspecification flags that name the wrong factor | joint, factor-structured, misspecification-aware twin calibration with label-statistic summaries | turns S3 from three tricks into one method | complexity; time | summaries -> posterior -> posterior-predictive checks per factor | 2-3 person-days on top of S3-2 to S3-4 | the method's rigor; misspecification-attribution figures | **G2**: diagnostics pass, flags interpretable |
| **S3-6** Decomposition study (E-S1) | 8 factorial cells plus the S6 hand-calibrated twin, uniform randomization and a real-trained oracle; Shapley shares; error fingerprints (AP at IoU 0.25, 0.5 and 0.7, centre-distance AP, mASE, false positives per frame by height) | first quantitative three-factor decomposition of a LiDAR sim-to-real gap; "twin debugging" from error fingerprints | the paper's headline table and figure | GPU-heavy; interactions may blur shares | corpora from posterior draws (equal frame budget) -> 2 detectors x 3 seeds -> realval-B and third site -> bootstrap intervals | 800-1,000 GPU-hours (4-5 days of the machine); 2 person-days of analysis | claim S1 | **G3**: scribe or scene share outside its interval on both tracks |
| **S3-7** Generality | third site TUMTraf-I (two OS1-64, 4,800 labelled frames); optionally CARLA to KITTI | the same pipeline on a new twin without per-site hand work | proves "any twin" | engineering (sensor metadata, class map, licence rules) | adapter -> calibrate -> E-S1 subset | 3-4 person-days; about 300 GPU-hours | the generality claim; a third real target | baseline row on TUMTraf-I |
| **S3-8** Framework release | S3-Twin: adapters, factor modules, summaries, calibrator, decomposer, per-twin specs | a factorized, calibratable twin interface with a gap-decomposition protocol | citations and reuse; anchors the follow-up papers | packaging time; anonymity during review | anonymized code for review; public at camera-ready | 3-5 person-days, mostly after CVPR | impact (d) | |
| Later | paired consistency (C4), target-in-the-loop (paper 3), scaling laws (paper 4), evaluation science (paper 2) | see Section 1 | | | | | | |

## 3. The S3-Twin framework (technical stack)

**Design principle.** A twin is a function of three independent, calibratable factors and one fixed protocol:

    frame, labels = Protocol( Scribe_a( Sensor_phi( Scene_psi( Twin ) ) ) )

Every factor exposes its parameters in a spec file (`twin/theta.yaml`: `sensor:`, `scene:`, `scribe:` blocks). Every factor is calibrated from **summaries** that the same code computes on real and on simulated data, so calibration never needs a real label inside the detector.

```
                      +---------------------------------------------------------------+
  any twin            |  TwinAdapter: UrbanTwin LUMPI / V2X / TUMTraf-I, CARLA, ...      |
  (scenes, rig)       |  -> SceneState: static geometry, actors (id, class, mesh, pose(t)), rig |
                      +---------------------------------------------------------------+
                                  |
                      +-----------v-----------+   psi: content distribution, negatives,
                      |  SceneModel(psi)      |        density prior, placement
                      +-----------+-----------+
                                  |
                      +-----------v-----------+   phi: beam tables, per-beam drop and noise,
                      |  SensorModel(phi)     |        null map, per-sensor time phase
                      |  ray cast per sensor  |   -> points (xyz, sensor, time, beam) + per-actor hit stats
                      +-----------+-----------+
                                  |
                      +-----------v-----------+   a: visibility, persistence, padding, size regime,
                      |  ScribeModel(a)       |      z, rider grouping, taxonomy, yaw, noise, label time
                      +-----------+-----------+   -> boxes, classes (+ regime)
                                  |
                      +-----------v-----------+   the target's protocol (50k resample, range mask)
                      |  Protocol             |
                      +-----------+-----------+
                                  |
     real unlabeled scans  +------v------+  simulated batches
     + label statistics -->|  Summaries  |<-- (same code)
                           +------+------+
                                  |
                      +-----------v-----------+   per factor: closed form / robust SBI / source
                      |  Calibrator (CTD)     |   distribution; SBC, coverage, PPC, misspecification flags
                      +-----------+-----------+
                                  |
                      +-----------v-----------+   theta draws + seeds -> corpus manifest (reproducible)
                      |  CorpusBuilder        |
                      +-----------+-----------+
                                  |
                      +-----------v-----------+   OpenPCDet adapters (PointPillars, CenterPoint, Voxel R-CNN)
                      |  Trainer              |
                      +-----------+-----------+
                                  |
                      +-----------v-----------+   AP at IoU 0.25 / 0.5 / 0.7, centre-distance AP, mASE,
                      |  Evaluator +          |   false positives by height; seeds and bootstrap;
                      |  Decomposer           |   factorial cells, Shapley shares, error fingerprints
                      +-----------------------+
```

**Package layout** (`synth-common/synthtwin/`, replacing the flat plan of `synth-common/README.md` Section 2):

| Module | Role | Built on (imported from `main`, never edited) | New |
|---|---|---|---|
| `adapters/` | `UrbanTwinLumpi`, `UrbanTwinV2X`, `UrbanTwinTumtraf` (later `Carla`): SceneState from organizer frames (UT-LUMPI is a sequence with actor ids, so actor velocities are available) | `data-<track>/prepare_g1.py`, `bdc26.io` | SceneState contract, per-actor history |
| `scene.py` | content sampler, negatives library, density prior, source distribution q_psi | `bdc26.render.g1`, `pedsim`, `g2` (clutter, riders), `bdc26.density` | residual-mass matching, q_psi |
| `sensor.py` | rig, per-sensor ray cast with time phase, return model (drop, noise, nulls) | `bdc26.render.lidar_sim`, `g2.insert_meshes` (already casts per sensor) | time-aware cast, per-beam return model, hit statistics per actor |
| `scribe.py` | labelling policy and regimes | `bdc26.prep` (currently min_points = 1 for every class) | the whole module |
| `protocol.py` | the target's resample and range mask | `bdc26.frames.resample`, `bdc26.boxes` | |
| `summaries.py` | unlabeled-scan and label-statistic summaries (`twin/summaries.yaml`), with the scribe family added | `bdc26.realism`, `pilot_scribe.py` statistics | the label-statistic family |
| `calibrate/` | `closed_form.py`, `sbi_robust.py` (TSNPE ensembles, tempering), `source.py` (Sourcerer-style), `diagnostics.py` | pinned `sbi` in `.venv_ut` | all |
| `corpus.py` | manifests, disk budget, regeneration from manifests | `common/pipeline` queues | |
| `evaluate.py`, `decompose.py` | IoU sweep, centre-distance AP, mASE, false positives by height, factorial and Shapley, fingerprints | `bdc26.evalap`, `bdc26.diagnostics` | decomposition and fingerprints |

**Branch rule in practice.** `synthtwin` imports `bdc26` and wraps it. If a hook inside `common/` is unavoidable (for example, exposing per-actor hit counts before the min_points filter), it is added on `main` as a detector-line change with its own test, then merged into `synth-cv`.

**Per-twin onboarding** (what "any twin" costs):
1. Write the adapter.
2. Write `theta.yaml` and `summaries.yaml`.
3. Point the calibrator at the site's unlabeled scans and label statistics.
4. Run the decomposition.

Everything else is shared.

## 4. Method details

**4.1 The scribe model.** For actor i with true box b_i, class k_i, track id, rendered points P_i (times, sensor ids), hit count n_i, visible fraction v_i (hits over unoccluded rays), range r_i and track history H_i, the scribe outputs a label or none. Parameters per class k and regime m:

| Component | Model | Identified from |
|---|---|---|
| visibility | keep with probability sigmoid(beta_k (log(1 + n_i) - log(1 + n0_k))); V2X-like datasets have a sharp n0 | the truncation point and shape of real points-per-box histograms against the twin's complete population |
| persistence | if unseen now but seen with n >= n0 within the last W frames, keep with rate rho_k (box carried by the track) | the 0-point box rate by range against the twin's occlusion statistics |
| size regime | one size per track (observed on LUMPI); box size = s_{k,m} * true size + pad_{k,m}; mixture weights pi_m per recording | per-regime size histograms; LUMPI's manual flag is an observed regime label |
| padding and z | face margins on sensor-facing faces; bottom at ground contact or at the lowest point | fill and gap statistics on near, well-observed boxes |
| taxonomy | class map per regime (LUMPI automatic class 6 is person-sized) | per-class size mixtures per regime |
| rider grouping, yaw, noise | box includes the rider or not; yaw from motion or from shape; jitter | height bimodality; track statistics |
| label time | the box is placed at the actor's pose at time tau inside the sweep | doubled contours of moving objects (LUMPI; identification still open, P0) |

**4.2 Calibration (CTD engine).**
- Closed-form estimates first (truncation, persistence, regime sizes). Many scribe parameters are directly identifiable as statistics.
- Robust SBI for the coupled and sensor parameters, with misspecification diagnostics (agenda Section 5.2).
- The source distribution for per-frame scene parameters.
- Identifiability is shown sim-to-sim: a known (phi, psi, a) applied to synthetic data must be recovered.
- Confounds are tested by perturbation: change the drop and check that the inferred visibility n0 stays put.

**4.3 Decomposition.**
- Cells: AP(S) for each subset S of {sensor, scene, scribe} calibrated, the rest naive.
- Shapley share of factor f: phi_f = sum over S not containing f of |S|! (2 - |S|)! / 3! x [AP(S + f) - AP(S)].
- Reported per class and per IoU threshold, with interaction terms, against the real-trained oracle (the gap's denominator), with seed and frame bootstrap intervals.

**4.4 Error fingerprints ("twin debugging").** Each factor should leave a distinct signature on a small labelled set:
- scribe errors hurt high IoU (0.7) and mASE more than centre-distance AP;
- sensor errors hurt recall at range at every IoU;
- scene errors add false positives (by height band).

The fingerprint table turns the decomposition into a diagnostic tool: from a detector's errors on a few labelled frames, tell which factor of the twin to fix.

## 5. Experiments that make the paper reviewer-proof

| Experiment | Question | Why reviewers need it |
|---|---|---|
| E-S0 label swap | does the scribe alone move AP and false positives? | isolates the new factor |
| E-S1 factorial | how much does each factor explain, per class and IoU? | the headline |
| **Label budget** | scribe statistics from k = 10, 50, 200, 1,280 labelled frames, against **fine-tuning on the same k frames** (research-only reference row) | "if you have labels, why not fine-tune?": statistics are cheaper, transfer across sensors, and never put real labels into the detector |
| **Scribe from guidelines** | a scribe hand-set from published annotation guidelines, against the inferred one | inference beats reading the manual |
| Output rescaling | SN-style post-hoc size and z correction on the naive model's outputs, against the scribe | rescaling cannot change which objects get a box |
| Sim-to-sim recovery | parameters recovered within intervals; confound perturbations | identifiability |
| Regimes | LUMPI manual against automatic; regime-matched against mixture training | the scribe is a latent variable per recording |
| Third site | TUMTraf-I through the same pipeline | generality |
| Seeds and statistics | 3 seeds per cell (5 for the main rows), 95% bootstrap intervals, paired tests | the seed spread under shift is up to 0.17 AP per class |

## 6. Execution plan

Dates assume the challenge's own duties stay on `main`: development uploads to Oct 30, final phase Nov 1-14 (1 upload a day), report draft by Nov 1, report due Nov 15. GPU budget: 8 A6000 = 192 GPU-hours a day.

| When | Step | Work | Output | Compute | Gate |
|---|---|---|---|---|---|
| Oct 19-20 | S3-1 | `synthtwin.scribe` v0; per-actor hit statistics before the min_points filter (wrapper, or a small hook on `main`); label variants for V2X (minimum points 6 for pedestrians, by class; vehicle height and padding) and LUMPI (manual Person sizes, persistence) | `E-S0/` configs and corpora (labels only) | CPU minutes | |
| Oct 20-22 | S3-1 | E-S0 runs: raw against scribe labels, PointPillars, 3 seeds, 2 tracks | `E-S0/results.json` | 70-140 GPU-hours | **G1 (Oct 23)**: does the scribe lead the paper? |
| Oct 19-23 (parallel) | S3-4 prep | pin `sbi` after a torch 2.1.2 smoke test; summaries v1 (`summaries.py`, label family included); TUMTraf-I download (academic use, nothing derived leaves `$BDC_DATA`) | `E1-summaries/` | CPU | summaries separate S6 from uniform settings |
| Oct 24-28 | S3-2, S3-3, S3-4 | scribe inference and sim-to-sim recovery; label-budget fits; residual-mass negatives; sensor posterior (TSNPE rounds); time-aware LUMPI cast (if cheap); TUMTraf-I adapter and baseline | `E2-posterior/`, `E-S2/` | about 15 CPU-hours, about 100 GPU-hours | |
| Oct 29 | S3-5 | joint engine, posterior-predictive checks, misspecification flags | diagnostics figures | CPU | **G2**: diagnostics pass |
| Oct 30 - Nov 5 | S3-6 | E-S1 factorial on LUMPI and V2X (plus TUMTraf-I rows), label-budget and rescaling baselines | the main table, Shapley figure, fingerprints | 800-1,000 GPU-hours | **G3 (Nov 5)**: go or no-go for CVPR |
| Nov 6-10 | paper | figures, Voxel R-CNN on the main rows if time allows; register the paper by **Nov 10** (OpenReview RahulVishwakarma1) | draft v1 | about 150 GPU-hours | |
| Nov 11-16 | paper | writing, supplementary (anonymized BigData report as concurrent work, synth-paper/README.md Section 3); challenge report on Nov 15 from the Nov 1 draft | CVPR submission Nov 16 AoE | | |
| if G3 fails | ICCV 2027 | the full S3-Twin (S3-3 to S3-8, consistency, CARLA to KITTI), 3 sites, 3 detectors | | | |

**Honest load.** The CVPR scope is about 20-25 person-days of research in 29 days, alongside the challenge's final phase and report. It works only if:
- E-S0 is decisive at G1;
- the BigData report is drafted by Nov 1;
- the factorial runs uninterrupted from Oct 30.

## 7. Risks and kill criteria

| Risk | Signal | Response |
|---|---|---|
| The scribe has no AP effect | E-S0 flat on both tracks at every IoU | the scribe stays a factor; the paper leads with the decomposition (S1) and CTD; or move to ICCV |
| Factors are not separable (sensor drop and visibility) | sim-to-sim recovery fails under perturbation | calibrate jointly; report the interaction term as a finding |
| "It is just label calibration" | review | visibility and persistence cannot be fixed by rescaling (output-rescaling baseline); regimes; the inferred-vs-guidelines result; the decomposition |
| "You use target labels" | review | statistics only, from a small labelled subset; the label-budget curve against fine-tuning; the detector never sees a real label |
| Compute or time | G3 slips | Voxel R-CNN and the third site move to ICCV; CVPR keeps two sites and two detectors |
| Novelty threats | weekly arXiv check (LGPL follow-ups in 3D, HuLiGen, LidarVerse, SPIN) | position on the multi-part inferred scribe and the three-factor decomposition |
