# synth-common: the synthesized-data research line (shared code)

> Plan of record: [`synth-docs/RESEARCH-AGENDA.md`](../synth-docs/RESEARCH-AGENDA.md). Per-track material: [`synth-lumpi-track/`](../synth-lumpi-track/README.md), [`synth-v2x-track/`](../synth-v2x-track/README.md).

## 1. What this line is, and how it differs from the detector line

The repository has two lines of work:

| Line | Folders | Question | Unit of work | Output |
|---|---|---|---|---|
| **Detector line** (S1-S6, the challenge entries) | `data-<track>/`, `model-<track>/`, `common/` | which detectors, fusions and post-processing win on the leaderboard | a model folder with checkpoints, tuned post-processing, a routed portfolio | CodaBench submissions (release 6.0) |
| **Synth line** (this folder, research) | `synth-common/`, `synth-lumpi-track/`, `synth-v2x-track/` | how to *infer* the digital twin from unlabeled real scans so that synthetic-only training transfers | a twin parameter posterior, a corpus drawn from it, an experiment record | papers (CVPR 2027 target), and candidate corpora the detector line may adopt through its own gates |

The synth line reuses the detector line's code (generator, scorer, detectors) without changing it: it imports `bdc26` (render, density, realism, evalap, scorecard) and calls `data-<track>/prepare_g1.py` and OpenPCDet through new, separate entry points. It never writes into `data-*`, `model-*` or their registries. Corpora and posteriors live under `$BDC_DATA/synth/<track>/` (git-ignored, like all large data); configs, summaries of results and experiment records live in `synth-<track>-track/` (in git).

## 2. Planned layout (built work package by work package, agenda Section 8)

```
synth-common/
├── README.md                this file
├── synthtwin/               Python package (added to PYTHONPATH in common/env/bdc26.env when WP1 lands)
│   ├── theta.py             WP1  parameter spaces (synth-<track>-track/twin/theta.yaml): priors, transforms, sampling
│   ├── simulate.py          WP1  theta -> a batch of frames through the existing generator (prepare_g1 hooks), CPU-parallel
│   ├── summaries.py         WP1  s(x) of synth-<track>-track/twin/summaries.yaml, identical for real and simulated batches
│   ├── scribe.py            WP1b the annotator twin (agenda Section 13.2): labelling policy applied at label generation (visibility,
│   │                             padding, size regime, z, rider grouping, taxonomy, yaw, noise, label time), and its summaries
│   ├── posterior.py         WP2  NPE / robust NPE (pinned sbi), sequential rounds, diagnostics (SBC, coverage, PPC)
│   ├── corpus.py            WP3  posterior-predictive corpora: theta ~ q(theta | s_real) per frame, manifests, disk budget
│   ├── paired.py            WP4  paired multi-render batches (same scene, K sensor draws) for consistency training
│   ├── consistency.py       WP4  OpenPCDet hooks: BEV-feature and heatmap/box consistency losses with an EMA teacher
│   ├── failures.py          WP5  failure statistics of a detector on legal real validation -> generator controls
│   ├── metrics.py           WP6  debiased realism estimators, variance decomposition, transfer predictors
│   └── attribution.py       WP7  Shapley-style attribution over twin factors
├── tools/                   CLIs (synth_summaries.py, synth_posterior.py, synth_corpus.py, synth_train.py, ...)
├── pipeline/                detached jobs reusing common/pipeline (launch.sh, gpu_queue.sh) for simulation and training
└── tests/                   unit tests (synthetic fixtures; run with the main suite)
```

## 3. Conventions

- **Environment:** the one pinned `.venv_ut`. New packages (the `sbi` library first) are pinned in `requirements.txt` and the lock after a compatibility check with torch 2.1.2; `common/tests/test_environment.py` must pass.
- **Rules:** real data enters only as statistics for the generator (unlabeled scans, legal label statistics) and as labelled validation; no detector is trained, fine-tuned or adapted on real frames; no real-scan geometry. Research-only experiments (agenda Section 6.6) are flagged in their experiment record and can never feed a submission.
- **Honest evaluation:** inference sees only the calibration data named in `twin/summaries.yaml`; realval-B, the held-out realism proxies and the hidden test are never used to fit anything.
- **Statistics:** every detection number is a mean over at least 3 seeds (or a bag) with a 90% interval; every realism number is a mean over 10 subsample seeds with its standard deviation.
- **Runs:** detached through `common/pipeline/launch.sh`, logged in `$BDC_DATA/logs/synth-<experiment>/`, TensorBoard as in root README Section 6.10.
- **Records:** one folder per experiment, `synth-<track>-track/experiments/<ID>/` with `config.yaml`, `results.json` and `README.md` (question, protocol, result, decision), indexed in `synth-<track>-track/experiments/README.md`.
