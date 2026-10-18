# 08 Research agenda: the synth line (rev. 3, 2026-10-18)

> **What this is.** The plan of record for the research line that starts after the challenge entries (release 6.0): infer the digital twin from unlabeled real scans so that synthetic-only LiDAR detection transfers, written to the standard of a CVPR paper. Rev. 2 (2026-10-17) set the method (Sections 1-12); **rev. 3 (2026-10-18, Section 13) refines the CVPR paper** around the three gaps of a twin (sensor, scene, scribe) after three more literature passes on the generation side.
> **Where things live.** On branch **`synth-cv`** only, under `synth-*` paths (branch rules: [`README.md`](README.md)); branch `main` holds the challenge line. The research line has its own folders, separate from the detector line (`data-<track>/`, `model-<track>/`):
> - [`synth-common/`](../synth-common/README.md): shared code of the line (package `synthtwin`, tools, pipeline, tests), built work package by work package (Section 8);
> - [`synth-lumpi-track/`](../synth-lumpi-track/README.md) and [`synth-v2x-track/`](../synth-v2x-track/README.md): per-track twin parameter spaces (`twin/theta.yaml`), summary statistics and data protocol (`twin/summaries.yaml`), experiment records (`experiments/`);
> - this document (`synth-docs/`, moved from `docs/08` on 2026-10-18): thesis, approaches reviewed, method, experiments, compute, plan, publication strategy; references in [`LITERATURE.md`](LITERATURE.md).
>
> References R45-R124 (R97 unused) are in [`LITERATURE.md`](LITERATURE.md); their status (confirmed, corrected, unverified) was checked on 2026-10-17 (R45-R105) and 2026-10-18 (R106-R124).

**Contents.** [1 Evidence](#1-evidence-from-the-detector-line) · [2 Problem](#2-problem-statement) · [3 Approaches reviewed](#3-approaches-reviewed) · [4 Thesis and claims](#4-thesis-and-novelty-claims) · [5 Method](#5-method-calibrated-twin-distributions) · [6 Experiments](#6-experimental-design) · [7 Compute](#7-feasibility-and-compute) · [8 Work packages](#8-work-packages) · [9 Timeline](#9-timeline-and-decision-gates) · [10 Publication strategy](#10-publication-strategy) · [11 Risks](#11-risks-and-mitigations) · [12 Second paper](#12-second-paper-evaluation-science) · [13 Rev. 3: sensor, scene, scribe](#13-rev-3-2026-10-18-generation-side-novelty-and-the-refined-paper)

## 1. Evidence from the detector line

| Fact (release 6.0, [`02-STRATEGY.md`](../docs/02-STRATEGY.md) 8.6-8.10) | Value | What it implies for the synth line |
|---|---|---|
| Hidden-test results, synthetic-only training | V2X 0.8931, LUMPI 0.5228 combined; above the ECCV 2026 winners on the same test and scorer (0.7457, 0.4793) | a strong system to build on and compare against |
| What moved the score | twin content and conventions (walkers, actor scale 1/0.78, real sizes, static clutter, density prior) > variance control > size distributions > capacity | the gap is in the twin: calibrating it is the lever |
| How the twin was calibrated | by hand: 20-28 settings per track, one value each (`synth-<track>-track/twin/theta.yaml`, "current") | a point estimate with no uncertainty and no diversity |
| Seed variance under the shift | up to 0.17 AP per class for one configuration | every claim needs seeds and intervals |
| Transfer of local gains | 0.25-2.7 x; a pooled two-split bootstrap condition agreed with the hidden-test sign for 16 of 17 class changes (S3-S5) and both S6 V2X changes, not for the rare LUMPI classes | the evaluation protocol of Section 6.4 |
| Realism score noise | sd 0.0012-0.0025 for a fixed frame set; frame order alone moves it by up to 0.006 | realism must be reported as a mean over subsample seeds |
| Generator cost | 10,000 frames in about 11 min (LUMPI, five sensors, G2-lite) and 1.6 min (V2X) on 96 workers | likelihood-free inference with 10^4 simulations is affordable on CPU |

## 2. Problem statement

- **Simulator.** The generator maps parameters theta (sensor and insertion settings, scene content, placement, background density) and a scene sample u (one of the organizers' 10,000 UT frames per site, plus random seeds) to a labelled frame: (x, y) = S(theta, u). It is cheap, stochastic and not differentiable. It is **misspecified**: no theta reproduces the real site exactly (missing static structure, approximate meshes, CARLA traffic).
- **Real data, under the rules.** Unlabeled real scans of the site (calibration split) and legal label *statistics* (sizes, counts, points per box) may adapt the generator; labelled real frames are used only for evaluation; the detector is trained on synthetic frames only, with no real-scan geometry ([`decisions/2026-10-14-rules-compliance-review.md`](../docs/decisions/2026-10-14-rules-compliance-review.md)).
- **Goal.** Find a *training distribution over the twin*, Q(theta), such that a detector trained only on frames from S(theta, u) with theta ~ Q maximizes AP on the real target.
- **Two kinds of parameters.** Global sensor parameters phi (drop field, range noise, extrinsic error) are the same for every real frame: their uncertainty should shrink with data. Scene parameters theta_i (walker counts and styles, clutter density and mix, density-prior strength) vary from frame to frame in reality: their *distribution* q_psi(theta_i) is what training should sample.
- **Why this is hard.** (1) A posterior over one global theta concentrates as real frames accumulate, so sampling it gives almost no diversity (it collapses to a point estimate). (2) Under misspecification, neural posteriors become overconfident and erratic (R81, R82). (3) Matching simulated to real statistics can backfire when the prior is misspecified (R92). (4) The objective that matters (real AP) is not observable during calibration without real labels.

## 3. Approaches reviewed

| Family | Representative work | Optimizes | Real labels? | Misspecification | Diversity | Cost here | Verdict |
|---|---|---|---|---|---|---|---|
| Hand calibration | our S1-S6 (point estimates) | expert judgement on realval | statistics | implicit | none | person-weeks | the baseline to beat |
| Uniform domain randomization | Tobin et al. 2017 (R93) | nothing (wide ranges) | no | ignores | maximal, unfocused | cheapest | baseline |
| Structured / adaptive / automatic DR | Prakash 2019; Mehta 2019; OpenAI ADR (R93) | context priors; agent difficulty | no | ignores | adaptive | high (RL loops) | cite; not our setting |
| Distribution matching (point) | Meta-Sim, Meta-Sim2 (R47, R48); LiDAR-in-the-loop CMA-ES (R49) | feature MMD / detection loss in simulation | no / sim only | point estimate absorbs it | none | moderate | **baseline** (optimized point estimate) |
| Bilevel task optimization | Learning to Simulate, AutoSimulate (R48); BO on validation mAP | real validation AP | **yes** (leaks labels into calibration) | n/a | none | tens of detector trainings | baseline with a labelled split, flagged |
| SBI posterior (global theta) | BayesSim, NPDR (R45, R46); NPE/TSNPE/FMPE/NPE-PFN (R83-R86) | likelihood-free posterior | no | overconfident (R81, R82) | collapses with data | 10^4 simulations | building block, not enough alone |
| Misspecification-robust SBI | RNPE, MMD-regularized summaries, generalized Bayes/ACE, SPIN (R87-R90, R104) | robust or tempered posteriors | no | the topic | tempered width | small extra | **core component** |
| Source / hierarchical distributions | Sourcerer (max-entropy source), HNPE (R91) | a distribution over per-sample parameters whose push-forward matches the data | no | partial | **matched diversity** | surrogate + optimization | **core component** |
| Learned sensor models | LiDARsim, RINet, PCGen, learned ray drop (07 Sec 3.2) | per-ray drop/intensity from real scans | no | n/a | no | moderate | complementary (sensor block of theta) |
| Generative translation | DRUM (diffusion prior on unlabeled real scans), ePointDA, RangeLDM (R95) | real-looking scans | no | strong | no | high | **research-only upper bound**: on a fixed site it learns real geometry |
| Detector-side invariance | SESS, Mean Teacher, LiDAR Distillation, sparsity-invariant features, CVGC (R52, R96, R98, R99, R105) | consistency across views or densities | no | absorbs residual | n/a | about 2 x training | **core component** (paired renders) |
| Failure-driven generation | counterexample-guided augmentation, AdvSim, KING, SHIFT3D (R57-R59) | hard cases | validation failures | n/a | targeted | retrain rounds | extension (Section 5.5) |
| Self-training on real | ST3D, MS3D, MOS (07 Sec 3.6) | pseudo-labels on real | no | n/a | n/a | moderate | **not allowed** for the detector; research-only reference row |

**Choice.** No single family covers the problem: we combine (a) misspecification-robust posterior inference for the global sensor parameters, (b) a matched source distribution for the per-frame scene parameters, (c) detector-side consistency across paired renders for the misspecification that remains, and (d) label-free misspecification attribution to repair the twin.

## 4. Thesis and novelty claims

**Thesis.** *Calibrate the twin as a distribution, not a point, with inference that knows the twin is wrong, and train the detector to be invariant to what calibration cannot pin down.*

**Claims we intend to make** (each tied to an experiment that could refute it, Section 6.6):
1. **First calibrated likelihood-free inference of a LiDAR twin** (sensor and content parameters) from unlabeled real scans, with simulation-based calibration diagnostics, transferring to synthetic-only 3D detection on three real roadside targets. No prior work infers simulator parameters for LiDAR detection (both literature passes; closest: BayesSim and NPDR for control, LiDAR-in-the-loop for in-simulation sensor tuning, Meta-Sim for images).
2. **The misspecification-to-detection link.** Standard neural posteriors become overconfident under twin misspecification and *lower* real AP; robust or tempered posteriors, with the temperature chosen by label-free predictive coverage on held-out real chunks, recover it. Shown in a controlled sim-to-sim study (known ground truth) and on the real targets.
3. **Diversity versus precision.** A matched per-frame source distribution (scene parameters) beats both a global posterior and uniform randomization at equal frame budgets, and the gain is not an ensembling effect (posterior-draw ensembles against seed ensembles of the same size).
4. **Paired multi-render consistency** for 3D detection: physically re-rendered pairs of the same scene beat beam subsampling and the union-of-renders control, reduce seed variance and the A/B transfer spread, and transfer across sensors (LiDAR-CS).
5. **Label-free misspecification attribution as twin repair:** per-summary model criticism identifies which twin component is wrong (static structure, drop field, walker shape), and repairing it improves AP.

**Not claimed (prior art):** training on a posterior or posterior predictive (BayesSim, NPDR); feature-MMD calibration from unlabeled targets (Meta-Sim); robust summaries per se (Huang et al., Schmitt et al.); ensembles; learned ray drop; the expected-risk argument for posterior-predictive training (textbook).

**Rev. 3 (Section 13.2):** for the CVPR version, claims 4-5 give way to the scribe claims S1-S3 (decomposition, scribe identifiability, regimes); claims 1-3 stay as the inference engine over sensor, scene and scribe.

**Threats to watch weekly on arXiv:** HuLiGen (human LiDAR generation, R113), LidarVerse (R120), LGPL follow-ups (R106, R107), SPIN (SBI under misspecification with unlabeled real data, non-LiDAR, R104), CVGC (cross-view consistency, LiDAR segmentation, R105), LiDAR-CS follow-ups, neural LiDAR simulators fitted to unlabeled scans.

## 5. Method: Calibrated Twin Distributions

Working name: **CTD** (Calibrated Twin Distributions). Components C1-C4 carry claims 1-4; C5 is an extension.

### 5.1 C1 Identification and parameter reduction

- Fixed, known from metadata: sensor poses and beam tables (LUMPI five sensors, V2X OS1-64), the UT scene pool, the 50,000-point protocol.
- Estimated deterministically (tight priors afterwards): quantities directly identifiable from real ring geometry (per-beam return-rate profiles, the V2X null-map structure).
- Inferred: 20-28 entangled parameters per track (`twin/theta.yaml`; up to 12 sensor and insertion, 10-12 content, 1-2 placement, 1-2 background), split into global phi and per-frame theta_i.
- New generator hooks (WP1): a scalar density-prior strength (ratio exponent), a range-dependent null profile (V2X), and per-call parameter overrides so one process renders batches under different theta without rebuilding.

### 5.2 C2 Calibrated distribution over the twin

1. **Summaries** (`twin/summaries.yaml`): about 200 handcrafted dimensions per batch of B = 64 frames (ring return rates, range profiles, height-banded BEV occupancy reduced by PCA fitted on prior simulations only, cluster statistics, ground residuals, null maps, label statistics); a learned DeepSets embedding as the comparison (R100).
2. **Global sensor posterior** p_beta(phi | real): truncated sequential NPE (TSNPE, 2-3 rounds, R84) with an ensemble of 5 density estimators; NPE-PFN as a low-budget cross-check (R86); about 10^4 simulations per track.
3. **Per-frame scene distribution** q_psi(theta_i): a maximum-entropy source distribution whose push-forward matches the distribution of per-chunk real summaries (Sourcerer-style, sliced-Wasserstein matching through a learned surrogate of the simulator; R91). This is the domain-randomization distribution, fitted rather than guessed.
4. **Misspecification pipeline** (claims 2 and 5):
   - *Detect:* summary-space MMD and classifier two-sample tests between real and simulated summaries (R89), local C2ST at the real observation (R101), posterior predictive checks per summary block.
   - *Attribute:* per-block error models (RNPE-style, R87) flag which summaries the twin cannot reproduce; each flag maps to a twin component (BEV height bands above 1.5 m: static structure; ring rates: drop field; small clusters: walker shape).
   - *Robustify:* MMD-regularized summaries (R88) or masking of flagged blocks.
   - *Temper:* a power posterior p_beta (beta in [0.05, 1]) or ACE generalized posterior (R90); beta chosen by predictive coverage of held-out real calibration chunks. No labels are used.
5. **Diagnostics reported:** SBC and expected coverage on held-out simulations (R101), TARP (R101), local C2ST at each real target, posterior predictive checks, and **sim-to-sim recovery**: a twin configuration held out as pseudo-real with known theta.

### 5.3 C3 Training on the calibrated distribution

- Frames are drawn as phi ~ p_beta(phi | real), theta_i ~ q_psi, u uniformly from the UT pool; **equal frame budgets** for every condition (10,000 frames, the size of every corpus so far).
- **Distribution ensembles:** K = 4 detectors, each trained on a different draw of phi (and a different stream of theta_i), against K = 4 seed ensembles on one corpus, to separate the distribution effect from ensembling (claim 3).
- Detectors: PointPillars and CenterPoint (fast, one stage), Voxel R-CNN (two stage); PV-RCNN++ for the final system row. Post-processing tuned on realval-A only (the detector line's tooling), reported on realval-B and the third site.

### 5.4 C4 Paired multi-render consistency

- Each training scene is rendered K = 2 times under two independent draws of phi (sensor) with the same actors, so labels are exact for both renders; identical global augmentation for both views; gt-sampling disabled (or the same objects pasted in both).
- Losses: the detection loss on both renders; BEV-feature consistency (1 - cosine on `spatial_features_2d`, weighted by a dilated box mask plus a small background weight) to an EMA teacher (decay 0.999) fed the other render; heatmap KL with temperature (CenterHead) or classification KL and box smooth-L1 on matched anchors (anchor heads); proposal sharing and pooled-feature consistency for two-stage heads; Hungarian-matched post-NMS box consistency in false-positive regions (SESS-style, R96). Consistency weight ramped as in Mean Teacher (R96).
- Controls (claim 4): the union of the K renders without the consistency loss at matched compute; beam-subsampling consistency (R52); LiDAR Distillation (R98).

### 5.5 C5 Extension: failure-driven repair

The detector line found that remaining errors are ranking errors, misses and static false positives. With labelled realval-A failures (by range, height, region, class) mapped to generator controls (clutter type and placement, occluded walkers, long trucks), 2-3 regenerate-retrain rounds; realval-B and the third site are never in the loop. Reported as an extension because it uses labelled validation statistics (allowed for generator adaptation under the rules review, but a reviewer will ask).

### 5.6 Theory notes for the paper

- Under a well-specified simulator, training on the posterior predictive minimizes the posterior expected risk (risk is linear in the data distribution); this is textbook and cited, not claimed.
- Under misspecification, the relevant bound is a domain-divergence bound (Ben-David et al. 2010): tempering trades the divergence term (precision) against coverage of the real variability (diversity). The diversity-versus-precision experiment (claim 3) is the empirical counterpart.

## 6. Experimental design

### 6.1 Targets and data

| Target | Synthetic source | Real evaluation | Role |
|---|---|---|---|
| LUMPI (five mixed sensors, intersection, 7 classes) | UT-LUMPI 10k + our generator | realval-B (Measurement 5-6, 867 frames); hidden test (anonymized) | main |
| V2X-Real IC (OS1-64, campus slope, 31% nulls, 3 classes) | UT-V2X 10k + our generator | realval-B (298 frames, disjoint scenarios); hidden test (anonymized) | main |
| **TUMTraf-I** (A9 intersection) | **UT-TUMTraf-I, 10k frames, Dataverse DOI 10.7910/DVN/D21HNZ** (R102) | real TUMTraf-I labelled frames (about 4.8k); class map from 10 real to 6 twin classes | **generality (third site)**; licence of the real data to be checked before download |
| LiDAR-CS (six simulated sensors, same scenes; R51) | its renders | its other sensors | consistency across sensors (claim 4) |
| CARLA to KITTI, "Synth It Like KITTI" protocol (R103) | CARLA (docker server) | KITTI val, Car | external simulator; **journal extension**, not on the CVPR path |

Calibration data (the only real data inference sees) and held-out data are fixed per track in `twin/summaries.yaml`: unlabeled frames of the realval-A source not sampled into realval-A, plus realval-A label statistics; realval-B, the held-out realism proxies and the hidden test are never used for calibration.

### 6.2 Metrics

Official 3D AP@0.5 (R40) per class and mAP over the classes with test GT; 3D AP@0.7 and BEV AP as secondary; realism R with the debiased estimator of Section 12 (mean over 10 subsample seeds, sd); posterior diagnostics (coverage, C2ST); seed sd and the realval-A / realval-B transfer spread; cost (simulations, CPU-hours, GPU-hours).

### 6.3 Baselines (rows of the main table)

1. UT data as released (organizers' twin, no generator).
2. **S6 hand-calibrated point estimate** (our generator with the `current` values; the challenge corpora `g1-v4` / `g1-v5`).
3. Uniform randomization over the same prior box.
4. **Optimized point estimate**: CMA-ES on summary MMD (Meta-Sim / LiDAR-in-the-loop style), same simulation budget: separates "distribution" from "calibration".
5. Global SBI posterior without robustness (NPE, beta = 1).
6. CTD (robust global posterior + matched scene distribution).
7. CTD + paired consistency.
8. CTD + paired consistency + failure-driven repair (extension).

Reference rows (not competitors): SN and ST3D (use unlabeled real data; ST3D is not allowed in the challenge), real-trained oracle (same detector, real train split), few-label fine-tuning (1%, 10%), ECCV 2026 winner reports, a DRUM-style translation upper bound (research-only).

### 6.4 Statistical protocol

At least 3 seeds per cell (5 for rows 2, 6, 7); mean, sd and 95% bootstrap interval; paired frame-bootstrap tests for differences between rows; equal frame, render and iteration budgets; hidden-test numbers only as anonymized external confirmation; the pooled two-split condition of the detector line as the decision rule when choosing among variants.

### 6.5 Tables and figures (the minimum a CVPR reviewer will expect)

| Item | Content |
|---|---|
| T1 | main results: 3 targets x {PointPillars, CenterPoint, Voxel R-CNN} x rows 1-8, per-class AP and mAP, mean +- sd |
| T2 | inference ablation: summary groups (drop one family), handcrafted vs learned summaries, sensor-only vs content-only parameters, simulation budget (10^3, 3x10^3, 10^4), beta, global posterior vs matched scene distribution, MAP vs posterior draws vs distribution ensemble |
| T3 | consistency ablation: K = 1 (union) vs 2 vs 3; each loss term; EMA vs symmetric teacher; physical re-render vs beam subsampling; LiDAR-CS cross-sensor results |
| T4 | misspecification: overconfident vs robust vs tempered posteriors (real AP, coverage); attribution flags and AP after each repair |
| T5 | generality: TUMTraf-I third site; LiDAR-CS |
| T6 | cost: simulations, CPU-hours, GPU-hours per row |
| F1 | method overview |
| F2 | posterior marginals against the prior and the hand-calibrated values; SBC/coverage curves |
| F3 | posterior predictive checks (real vs simulated summaries, flagged blocks) |
| F4 | AP against simulation budget and against beta |
| F5 | seed distributions with and without consistency |
| F6 | error maps by range and height; qualitative frames |

### 6.6 Expected outcomes and falsification criteria

| Claim | Expected | Refuted if |
|---|---|---|
| 1 | CTD mAP above the S6 point estimate on realval-B of both tracks and on TUMTraf-I | no row-6 gain over row 2 outside the 95% interval on at least two of the three targets |
| 2 | beta = 1 posterior below the tempered one; coverage of real chunks restored by tempering | overconfidence does not change AP (then report the diagnostic, drop the claim) |
| 3 | matched scene distribution above global posterior and uniform; distribution ensembles above seed ensembles | the gains equal those of seed ensembles of the same size |
| 4 | lower seed sd and A/B spread; AP gain mainly on walkers; cross-sensor gain on LiDAR-CS | union-of-renders matches consistency at equal compute |
| 5 | attribution flags static structure (LUMPI) and the null structure (V2X); repairs raise AP | flags do not point at components whose repair changes AP |

## 7. Feasibility and compute

**Machine:** 8 x RTX A6000 (48 GB), 255 CPU threads, 503 GB RAM, **850 GB free disk** (7 TB volume at 88%; large data now 182 GB).

| Work | Unit cost (measured or estimated) | Volume | Total |
|---|---|---|---|
| Simulation for inference | LUMPI about 55k frames/h, V2X about 375k frames/h on 96 workers (measured); summaries in memory, nothing on disk | 10^4 simulations x 64 frames per track, 2-3 rounds (sequential methods win at 10^3-10^4 simulations, R94) | LUMPI about 12 h, V2X about 2 h of CPU (less on 240 workers) |
| Density estimators (NPE ensembles, surrogate, source fit) | minutes to an hour on one GPU | 2 tracks x a few variants | under 20 GPU-hours |
| Corpora | 10k frames: 6-8 GB disk, 2-11 min | about 10 per track (rows 3-8, ablations, paired renders = 2 x) + third site | about 200-250 GB |
| PointPillars run | 1-2 h on 4 GPUs (measured) | T1-T5 | |
| Voxel R-CNN run | about 4.4 h on 4 GPUs (S6, measured) | T1, T5 | |
| T1 | 3 targets x 3 seeds x (PointPillars and CenterPoint on rows 1-8, Voxel R-CNN on rows 2, 6, 7) | about 170 runs | about 1,300 GPU-hours |
| T2-T4 | PointPillars and CenterPoint, 1-3 seeds | about 120 runs | about 700 GPU-hours |
| Total | | | **about 2,000 GPU-hours = 10-11 days of the whole machine** (192 GPU-hours per day) |

Disk rules: keep the last 3 checkpoints of each run (OpenPCDet `max_ckpt_save_num`), delete corpora after their runs end (the generator is deterministic given theta and seeds, so a manifest rebuilds them), keep summaries and results. Environment: pin `sbi` (0.25.0 or 0.26.1: metadata allows torch 2.1.2 and Python 3.10; a smoke test decides) in `.venv_ut` with the lock; BayesFlow 2 is incompatible (Python 3.12 on main) and is not used.

## 8. Work packages

| WP | Deliverable | Where | Acceptance test |
|---|---|---|---|
| WP0 | folders, parameter spaces, summary specs, this plan | `synth-*`, this plan | done 2026-10-17 |
| WP1 | `synthtwin.theta`, `simulate`, `summaries`; new generator hooks (prior strength, null profile, per-call overrides); `sbi` pinned | `synth-common/` | summaries of the S6 point estimate reproduce within noise across seeds; real calibration summaries computed; unit tests |
| WP1b | `synthtwin.scribe` (rev. 3): the labelling policy at label generation, `scribe:` blocks in `theta.yaml`, scribe summaries (margins, visibility ratios, size mixtures per recording and manual flag, rider bimodality); LUMPI per-point time diagnostic | `synth-common/`, `synth-<track>-track/twin/` | sim-to-sim recovery of scribe parameters within 90% intervals; M4 and M5-6 separated beyond seed noise |
| WP2 | `synthtwin.posterior`: TSNPE ensembles, source distribution, misspecification pipeline, diagnostics | `synth-common/`, `synth-<track>-track/experiments/E2-*` | SBC/coverage pass on simulations; sim-to-sim recovery within the 90% interval |
| WP3 | `synthtwin.corpus`: corpora for rows 3-6; detector runs through the existing `common/pipeline` queues | `$BDC_DATA/synth/<track>/`, `experiments/E3-*` | T1 rows 1-6 on two tracks, PointPillars, 3 seeds |
| WP4 | `synthtwin.paired`, `consistency`: OpenPCDet dataset class for K renders, losses, EMA teacher | `synth-common/` | T3 on PointPillars and CenterPoint; LiDAR-CS cross-sensor run |
| WP5 | third site: UT-TUMTraf-I download, sensor metadata, a TUMTraf-I prepare script in the generator's pattern, real TUMTraf-I evaluation split | `synth-tumtraf-track/` (new, same layout), `data-` side untouched | the S6-style baseline row on TUMTraf-I |
| WP6 | `synthtwin.metrics`: debiased realism estimators, variance decomposition, transfer predictors (also for Section 12) | `synth-common/` | estimator unit tests; variance tables reproduce Section 1 |
| WP7 | attribution and repair (claim 5); failure-driven extension (C5) | `synth-common/`, experiments E7 | T4 |
| WP8 | paper: figures, tables, supplementary, code release | `synth-paper/` (git; its README holds the separation policy), anonymized repository for review | camera-ready checklist |

## 9. Timeline and decision gates

The challenge still needs: final-phase submissions (Nov 1-14, F1 = release 6.0) and the challenge report (Nov 15). The CVPR 2027 paper deadline is **Nov 16, 2026 AoE** (registration Nov 10; supplementary Nov 23; OpenReview profiles for every author, which can take two weeks to approve without an institutional e-mail).

| Dates | Work | Gate |
|---|---|---|
| Oct 18-21 | WP1 (generator hooks, summaries, `sbi` pin); WP1b (scribe) to Oct 23; LUMPI per-point time diagnostic; OpenReview profile; TUMTraf-I download (academic use, Section 13.2) | **G1 (Oct 21):** summaries separate S6 from uniform settings and reproduce across seeds; scribe statistics separate M4 from M5-6 and naive from real |
| Oct 22-26 | WP2 on both tracks (posterior, source distribution, diagnostics, sim-to-sim recovery); WP5 download and prepare script | **G2 (Oct 26):** coverage diagnostics pass; misspecification flags are interpretable |
| Oct 27 - Nov 2 | WP3 as experiment E-S1 (Section 13.2): the 2^3 factorial plus S6, uniform and oracle rows, PointPillars and CenterPoint, 3 seeds, two tracks (about 800 GPU-hours) | **G3 (Nov 2), go / no-go for CVPR:** the scribe or the scene share outside its interval on both tracks, and the calibrated corner above S6 |
| Nov 3-10 | if go: Voxel R-CNN rows, T3 (consistency), TUMTraf-I rows, figures; register the paper by Nov 10 | |
| Nov 11-16 | writing; challenge report on Nov 15 (system paper, no shared main results) | CVPR submission |
| if no-go at G3 | ICCV 2027 (deadline not announced; typically early March 2027): full T1-T6, the CARLA to KITTI extension, C5 | |

Honest assessment: CVPR is feasible only for the scoped paper (claims 1-3 on two tracks plus the third site, with consistency if WP4 lands by Nov 3); ICCV 2027 is the safe target for the full version.

## 10. Publication strategy

- **Rev. 3 supersedes the story, titles and contributions below for the CVPR version: see Section 13.2 (Sensor, Scene, Scribe).** The rev. 2 text stays as the ICCV 2027 full version's frame.
- **Story.** Synthetic-only perception lives or dies by how well the twin is calibrated, yet every twin is calibrated by hand. We cast twin calibration as likelihood-free inference under misspecification, show that the naive posterior is overconfident and hurts transfer, and give a calibrated, diverse twin distribution plus a detector that is invariant to what calibration cannot pin down.
- **Title options.** "Calibrated Twin Distributions: Likelihood-Free Inference for Synthetic-Only LiDAR Detection"; "Learning the Twin, Not the Target"; "When the Twin Is Wrong: Misspecification-Aware Simulation for Sim-to-Real LiDAR Detection".
- **Contributions (paper wording):** (1) the CTD formulation (global sensor posterior + per-frame source distribution); (2) a misspecification pipeline with label-free attribution and tempering; (3) paired multi-render consistency; (4) a statistically sound protocol (seeds, intervals, debiased realism); (5) results on three real roadside targets with synthetic-only training, plus code.
- **Positioning.** Against domain randomization (we fit the randomization), Meta-Sim (distribution and uncertainty, not a point; LiDAR; misspecification), BayesSim/NPDR (perception, not control; misspecification; source distributions), translation (no real-scan geometry, labels exact by construction), self-training (no real data enters the detector).
- **Dual submission and anonymity.** CVPR forbids mentioning challenge participation in the submission and treats workshop papers longer than four pages as publications. The challenge report and any BigData proceedings paper describe the S1-S6 *system* only; the CVPR paper uses new experiments (CTD rows, third site) and reports hidden-test numbers, if at all, anonymized as an external check. Ask the organizers whether the challenge report is archival before Nov 10.
- **Reproducibility.** Every row has a manifest (theta draws, seeds, corpus hashes) and a reproduction script, as release 6.0 does for the entries (root README Section 6.11); code released with the camera-ready.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| The global posterior is too narrow to add diversity | the per-frame source distribution (C2.3) is the main object; claim 3 tests it directly |
| Summaries cannot identify content parameters | report posterior widths; T2 drop-one-family ablation; keep the point estimate as a row |
| Misspecification dominates (static structure the twin lacks) | attribution flags it; mask those summaries; consistency absorbs the rest; report it as a finding (claim 5) |
| CVPR timeline (30 days, solo) | gates G1-G3; ICCV 2027 fallback with the full scope |
| TUMTraf-I licence is CC BY-NC-ND 4.0 (R124) | academic use decided (Section 13.2); nothing derived is redistributed; if the download or sensor metadata blocks WP5, two sites plus LUMPI's regimes |
| The scribe is read as "just label calibration" | the visibility policy (which objects get a box) cannot be fixed by rescaling outputs (claim S2 tests it); regimes; joint inference; the decomposition |
| Third site engineering (sensor metadata, class map, licence) | WP5 runs in parallel from Oct 22; if blocked, LiDAR-CS plus the two sites, with the third site in the ICCV version |
| Novelty threats (SPIN, CVGC, new LiDAR SBI work) | weekly arXiv check; differentiate on LiDAR detection, source distributions and the misspecification-to-detection link |
| Disk (850 GB free) | corpus manifests instead of kept corpora; 3 checkpoints per run |
| Rules | real data only as statistics; translation and self-training are research-only rows; the organizer e-mail of the rules review should name the generator-calibration use |

## 12. Second paper: evaluation science

Kept from rev. 1, independent of the CVPR paper; target **NeurIPS 2027 Evaluations & Datasets** (2026 deadlines were May 4-6; expect mid-May 2027).
1. **Realism metric reliability:** variance decomposition of the challenge's realism score (subsample draw, frame order, frame set), the n^(-1/d) bias of subsampled CD and EMD, debiased estimators (self-distance subtraction, unbiased MMD, K-subsample means with intervals), minimum detectable differences for 50-frame submissions (R76-R80; the closest analogue is the FID Lottery, R77).
2. **Predictive validity:** rank correlation of each realism term with downstream AP across generator versions (G1 v1 to G2-lite v5, CTD rows).
3. **Transfer prediction:** from the 15 scored versions (7 LUMPI, 8 V2X) with per-class local and hidden-test numbers: slope, sign accuracy and rank statistics of single-split, pooled-bootstrap, accuracy-on-the-line and agreement-on-the-line predictors (R69, R70), including the pooled rule's failure on rare classes.
4. **A label-free 3D mAP estimator** extending box-stability and consistency estimators (BoS, PCR; R67, R68) to LiDAR, validated on labelled realval.
5. **Seed protocol:** training randomness versus finite-test-set noise (R74); ensembles versus capacity under sim-to-real (R75).

## 13. Rev. 3 (2026-10-18): generation-side novelty and the refined paper

Three further literature passes (sensor physics; scene, assets and curation; annotation conventions) looked for novelty on the *generation* side. References R106-R124 are in [`LITERATURE.md`](LITERATURE.md); the same passes corrected R7 (SN) and R8 (PCGen). **Result: the strongest new direction is the annotator.** A digital twin has three gaps, not one: the sensor, the scene and the *scribe* (how the real dataset was labelled). The field works on the sensor. Our own record says the scribe and the scene moved the score most, and no LiDAR work models the scribe.

### 13.1 Areas reviewed, ranked

| # | Area | Closest prior work | What is open | Our evidence | Verdict |
|---|---|---|---|---|---|
| 1 | **Annotator twin (scribe)**: a parametric labelling policy inside the generator, inferred from label statistics and unlabeled scans | SN (R7: sizes only; it cannot separate real size from convention); Synth It Like KITTI box shrink (R103: hand-set, +25.5 AP@0.7); PCGen (R8: pedestrian loosening + pose filter); LGPL (R106: 2D, Synscapes to Cityscapes +2.42 mAP, transfer model trained on **labelled target** data); per-annotator box-bias models (R109: 2D, several annotators per object) | an explicit annotator in a LiDAR twin; its parameters inferred jointly with sensor and content from legal statistics; annotator regimes per recording; a measured split of the gap into scribe, sensor and scene shares (none found) | actor scale 1/0.78 and UT boxes about 17% too small; UT Van to challenge Van (Van 0.034 -> 0.122); per-class size and z post-processing (LUMPI realval-A 0.210 -> 0.253); V2X range-dependent z (+0.019 combined); class-wise scaling to real sizes (V2X +0.0245); LUMPI Person length 0.77 m (M4) against 0.96-0.99 m (M5-6); realval-B class 6 boxes person- or two-wheeler-sized; LUMPI labels carry a manual flag (manual share 17-100% per class) | **core of the CVPR paper** (13.2) |
| 2 | **Calibrated negatives**: unlabeled clutter fitted to the real point mass the twin does not explain (cluster height, footprint, points, range histograms; no real positions) | Real-Aug, Sim2SG, MetaUrban zoning (R114); our G2-lite clutter (hand-set) | no generator calibrates negatives to residual real mass; learned layout generators are trained on labelled real scenes (real geometry, out of bounds for us) | static structures are 50-77% of unmatched walker detections; G2-lite clutter halved static walker false positives | the **scene factor** of the CVPR paper |
| 3 | **Label-free target-in-the-loop generation**: steer the generator by ensemble disagreement on unlabeled real frames, plus false positives mined by temporal persistence (a "pedestrian" that does not move for minutes is structure) | Deliberate Practice, ActGen, feedback-guided synthesis, uncertainty-aware ControlNet (R116); active DR (R93) | nothing for LiDAR; nothing steers a non-differentiable physical simulator with disagreement on the real target | seed bags give the ensemble for free; real frames are ordered | **paper 3** (ICCV 2027); the label-free replacement for C5 |
| 4 | **Time-aware multi-LiDAR rendering**: per-sensor phase offsets and the label-time convention under asynchrony | CoBEVFlow (feature level, between agents), TrajMatch, UniCal, HDV-Mess (calibration, compensation; R121) | no training-time render of asynchronous roadside fusion; no work asks which time a box refers to | LUMPI merges five sensors and stores per-point time (us); TUMTraf-I merges two OS1-64 by NTP; our renders are synchronous | **diagnostic now** (half a day on LUMPI per-point times); if offsets matter, "label time" joins the scribe |
| 5 | **Diversity scaling laws** for synthetic LiDAR: unique content (assets, scene pool, randomization width) against frame count, at two fidelity levels | Fan et al., SOC, Lin et al., Chen et al. (R115) | no scaling study for synthetic LiDAR detection; none separates diversity axes from fidelity or looks at seed variance | corpora are cheap (minutes) | **paper 4** (analysis; about 135 PointPillars runs, 800 GPU-hours); human assets as one axis (SMPL-X is licensed for non-commercial research only: check for Hitachi) |
| 6 | Identifiable fixed-sensor model (per-beam bias and drop on static background, structured nulls) transferred across sites (V2X OS1-64 to TUMTraf-I OS1-64 gen 2) | LiDARsim, PCGen, DUSty, RINet (R13, R8, R120) | cross-site and cross-sensor transfer of a drop model; object vs background drop | V2X has 31% structured nulls | the **sensor factor** (C2.2); not a headline: published drop gains are small (+2, -1.5, about 0 AP; R119) |
| 7 | Cached-hit differentiable sensor head (gradients through drop, noise, bias after one ray cast) | Heiden et al.; neural re-simulation; in-simulation tuning (R122, R49) | gradient calibration against **unpaired** statistics | | cheap baseline and surrogate inside C2 |
| 8 | Curation by optimal transport to unlabeled real features, fed back as a sampling prior | TAROT, DSIR, DsDm, CARE (R117) | nothing for LiDAR; valuation on labelled validation would leak labels | | baseline row for area 3 |
| 9 | Site-factored leakage audit: subtract the shared static background, then three-sample data-copying tests on actor configurations | Meehan et al., Bhattacharjee et al., Alaa et al. (R118) | nothing for LiDAR twins, where static geometry is shared by design | | **protocol section in every paper** (reviewers will ask whether the twin copies the test site) |
| 10 | Cheap generator checks (not novel) | Synth It Like KITTI (R103): glass the beam passes through +8.8 Car AP@0.7; simulated intensity as input -8.8 | | G2-lite hulls are solid; intensity is not an input | check real Car point profiles by height band against ours; a possible detector-line fix |

### 13.2 The refined paper: Sensor, Scene, Scribe

**Thesis.** *A LiDAR digital twin has three gaps: the sensor, the scene and the scribe. Each can be calibrated without letting real labels into the detector: the sensor from the unlabeled static background, the scene from the unlabeled real point mass the twin does not explain, and the scribe from label statistics. On roadside targets the scribe and the scene carry most of the gap.*

**The scribe** acts at label generation: the twin knows every actor exactly, and the scribe maps (actor, its rendered points, time) to a box or to no box. Changing it needs **no re-render**: the same frames are relabelled. Parameters (a `scribe:` block in `twin/theta.yaml`, WP1b):

| Parameter | Models | Identified from (legal statistics) | Confound and handling |
|---|---|---|---|
| visibility policy P(box given points n, visible fraction v, range r) | which objects get a box | real box counts per (n, r) against the twin's complete actor population; anchored at near range, where P is about 1 | drop and density: infer the sensor first or jointly |
| face padding per class | margin between box faces and the point hull | sensor-facing faces only (back faces mix padding with the guess of hidden extent) | real object size: use within-track variance where track ids exist |
| size mode per regime | tight vs loose conventions, per recording | size mixtures per recording; LUMPI's manual flag separates human from automatic boxes | real size differences between recordings |
| z convention | box bottom against the lowest points, by range | real boxes and their points | sloped ground (V2X): heights relative to the local ground |
| rider grouping | two-wheeler box with or without the rider | height bimodality of two-wheeler boxes | |
| taxonomy per regime | what a class id means per recording (LUMPI id 6: vans in M4, person- or two-wheeler-sized in M5-6) | per-class size mixtures per recording | |
| yaw convention | yaw against motion direction and against the points' principal axis | real boxes over ordered frames | |
| box noise | jitter in centre, size and yaw | within-track variation of rigid objects | |
| label time (if 13.1 area 4 holds) | the sweep time a box refers to | box offset against doubled contours of moving objects | |

**Claims for the CVPR version** (they replace claims 4-5 of Section 4; claims 1-3 stay as the inference engine, now over sensor, scene and scribe):

| Claim | Statement | Test | Refuted if |
|---|---|---|---|
| S1 decomposition | the synthetic-only gap splits into scribe, scene and sensor shares; scribe plus scene exceed sensor on roadside targets; the scribe share grows with the IoU threshold | 2^3 factorial (naive or calibrated per factor), Shapley shares with bootstrap intervals; AP at IoU 0.25, 0.5 and 0.7, centre-distance AP, mASE | the sensor share dominates, or shares are unstable across seeds |
| S2 scribe identifiability and gain | scribe parameters are recoverable from legal statistics, and the calibrated scribe recovers most of the oracle-convention gain; output rescaling (SN-style, our post-processing) recovers less because it cannot change which objects get a box | sim-to-sim recovery within 90% intervals under perturbed drop and size; real margins on realval-B as a check; leave-one-parameter-out | post-hoc rescaling matches the scribe |
| S3 regimes | the convention is a latent variable per recording; a scribe mixture is robust to an unknown test convention | LUMPI M4 vs M5-6 and manual vs automatic boxes; regime-matched vs mixture training | regime-matched and mixture training do not differ |
| S4 engine | joint robust inference over sensor, scene and scribe beats the hand-calibrated S6 point estimate and uniform randomization at equal budgets | Section 6.3 rows 2-6 | (Section 6.6, claims 1-3) |

**Size alone caps the metric** (a reviewer-friendly argument): a centred box scaled by r on k axes has IoU r^k. The UT volume gap of 17% (r = 0.94) caps 3D IoU at 0.83; LUMPI Person length 0.77 against 0.97 m caps it at 0.79. That is 0.29 of headroom above IoU 0.5 but only 0.09 above 0.7, so a convention error turns localization noise into misses at the challenge's threshold.

**Main experiment (E-S1).** Two levels per factor:
- *naive*: sensor from metadata only (beam tables, no drop or noise fit); scene = the UT pool plus walkers, riders and clutter at prior means; scribe = exact geometric boxes of every actor with at least one point (the UrbanTwin convention, R102);
- *calibrated*: the CTD posterior or source distribution for that factor.

Rows:
- the 8 factorial cells;
- the S6 hand-calibrated row;
- uniform randomization;
- a real-trained oracle (research-only; it gives the denominator of the gap shares).

Runs: two tracks (plus TUMTraf-I if cleared), PointPillars and CenterPoint, 3 seeds: about 132 runs, **about 800 GPU-hours (4-5 days of the machine)**. Scribe cells reuse the frames of their sensor-scene cell, so they cost training only.

**What changes in the plan.**
- WP1b (new, Oct 18-23): `synthtwin.scribe`, the `scribe:` block in both `theta.yaml` files, scribe summaries added to `summaries.yaml` (margins on sensor-facing faces, visibility ratios by points and range, size mixtures per recording and per manual flag, rider bimodality), sim-to-sim recovery.
- Half a day on the LUMPI per-point times (area 4).
- G1 adds: scribe statistics separate M4 from M5-6 and naive from real beyond seed noise.
- G3 becomes: the scribe or scene share is outside its interval on both tracks.
- Paired consistency (C4) and the failure-driven extension (C5) move to the ICCV 2027 version, where C5 becomes the label-free loop of area 3.

**Title options.** "Sensor, Scene, Scribe: Decomposing and Closing the Sim-to-Real Gap of LiDAR Digital Twins without Real Labels"; "Who Drew the Box? Annotator Twins for Synthetic-Only LiDAR Detection".

**Positioning.** Against SN and Synth It Like KITTI (one hand-set component, sizes only; we infer a multi-part policy, including which objects get a box), PCGen (pedestrian-specific, fitted by hand), LGPL and its CVPR 2026 follow-up (2D, learned from labelled target data; we use label statistics only and work in 3D), and annotator-noise models (2D, several annotators per object; we have one unknown annotator per recording). The scribe makes CTD's inference concrete and cheap. The decomposition is the finding that generalizes beyond our sites.

**Data and rules.**
- The scribe statistics use realval-A labels and the points inside them (margins). These are statistics, as in Section 2, recorded in the experiment record; never realval-B.
- **Licences (decided 2026-10-18):** all work here is academic, non-commercial research, within LUMPI's CC BY-NC 3.0, V2X-Real's academic terms and TUMTraf-I's **CC BY-NC-ND 4.0** (R124). TUMTraf-I goes ahead as the third site (WP5). NoDerivatives means nothing derived from it (converted labels, modified scans, twin geometry) ever leaves `$BDC_DATA`: not in git, not in a release. Hitachi product use will be built on a separate open-source stack.

**Publications after rev. 3:**
- CVPR 2027: Sensor, Scene, Scribe.
- ICCV 2027 (about March): the full version, with paired consistency and the label-free loop (area 3).
- Paper 2: evaluation science (Section 12).
- Paper 4: diversity scaling laws (area 5).

The separation policy (`synth-paper/README.md`) adds one row: the BigData report describes the convention fixes as engineering (actor scale, size and z post-processing, the Van mapping), never the scribe model, the regimes or the decomposition.
