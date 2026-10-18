# synth-lumpi-track: the synth research line on LUMPI

> Plan of record: [`synth-docs/RESEARCH-AGENDA.md`](../synth-docs/RESEARCH-AGENDA.md). Shared code: [`synth-common/`](../synth-common/README.md). The detector line for this track (challenge entries, release 6.0) is [`model-lumpi-track/`](../model-lumpi-track/README.md) and is not changed by anything here.

## 1. Site and simulator

- **Site:** the LUMPI intersection in Hannover: five mixed sensors (Pandar64, HDL-64E, PandarQT, two VLP-16) merged into one frame, 7 classes.
- **Simulator:** the detector line's generator (G1 walker insertion and engine G2-lite over the organizers' 10,000 UT frames), driven by the parameters in [`twin/theta.yaml`](twin/theta.yaml): 27 scalars and a 6-way clutter mix (sensor 12, content 11, placement 2, background 2). Cost: 10,000 frames in about 11 min on 96 workers.
- **Point estimate to beat:** the hand-calibrated values ("current" in `theta.yaml`), which produced the corpora behind release 6.0.

## 2. Real data protocol (fixed before any experiment)

| Use | Data | Where defined |
|---|---|---|
| Calibration (the only real data inference may see) | Measurement4 frames 0-6399 not sampled into realval-A (about 5,100 unlabeled frames) and realval-A label statistics | [`twin/summaries.yaml`](twin/summaries.yaml) |
| Held out, never used to fit anything | realval-B (Measurement5-6, 867 frames), held-out realism proxies 4-5, the hidden test | [`twin/summaries.yaml`](twin/summaries.yaml) |
| Post-processing tuning of evaluated detectors | realval-A (as in the detector line) | agenda Section 6.3 |

Summary statistics: 225 handcrafted dimensions per batch of 64 frames (`twin/summaries.yaml`), plus a learned embedding as the comparison.

## 3. Folder layout

```
synth-lumpi-track/
├── README.md              this file
├── twin/
│   ├── theta.yaml         the twin parameter space: hooks, current values, priors, groups
│   └── summaries.yaml     summary statistics, calibration and held-out data
└── experiments/
    ├── README.md          experiment registry (IDs, claims, status)
    └── <ID>/              one folder per experiment: config.yaml, results.json, README.md (question, protocol, result, decision)
```
Large outputs (simulations, posteriors, corpora, checkpoints) live under `$BDC_DATA/synth/lumpi-track/` and are rebuilt from the manifests in the experiment folders.
