# Experiment registry: synth-v2x-track

One row per experiment; each has a folder `<ID>/` with `config.yaml`, `results.json` and a `README.md` (question, protocol, result, decision). Claims and work packages: [`synth-docs/RESEARCH-AGENDA.md`](../../synth-docs/RESEARCH-AGENDA.md) Sections 4 and 8. Statistics: at least 3 seeds per cell, mean, sd and 95% bootstrap interval (agenda Section 6.4).

| ID | Question | Claim | WP | Status |
|---|---|---|---|---|
| E1-summaries | Do the summaries separate the hand-calibrated twin from uniform settings, and reproduce across simulation seeds? (gate G1) | 1 | WP1 | planned |
| E2-posterior | Global sensor posterior (TSNPE ensemble), per-frame scene distribution, misspecification flags, SBC / coverage, sim-to-sim recovery (gate G2) | 1, 2, 5 | WP2 | planned |
| E3-main | Main table rows 1-6 (UT, hand-calibrated, uniform, optimized point, global posterior, CTD) with PointPillars and CenterPoint, then Voxel R-CNN (gate G3) | 1, 3 | WP3 | planned |
| E3-ensembles | Distribution ensembles versus seed ensembles of the same size | 3 | WP3 | planned |
| E4-consistency | Paired multi-render consistency (rows 7) and its ablations | 4 | WP4 | planned |
| E6-realism | Debiased realism estimators and variance decomposition for this site | P2 | WP6 | planned |
| E7-attribution | Misspecification attribution and twin repair; failure-driven extension (row 8) | 5 | WP7 | planned |
