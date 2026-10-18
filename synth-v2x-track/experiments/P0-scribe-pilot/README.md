# P0 scribe pilot: V2X-Real (2026-10-18)

**Question.** As for LUMPI ([`../../../synth-lumpi-track/experiments/P0-scribe-pilot/README.md`](../../../synth-lumpi-track/experiments/P0-scribe-pilot/README.md)): does the real dataset label by rules our synthetic labels do not follow?

**Protocol.** Read-only statistics (`config.yaml`, `results.json`). Real data is realval-A: 688 frames after the guard, prepared labels, 50k points. Synthetic data is 1,280 random frames of `g1-v5`. Range bands and fill are as for LUMPI. There is one sensor, no manual flag and no track ids in the prepared labels, so there is no regime, track or timing analysis.

## Results

**1. Visibility policy: V2X-Real drops objects with fewer than about 6 points; our labels keep them.** This is the opposite of LUMPI.

| Class, band | Boxes with 1-2 points: real | synthetic | 3-5 points: real | synthetic | 6-10 points: real | synthetic |
|---|---|---|---|---|---|---|
| pedestrian, 15-30 m | 0.04% | 3.6% | 0.35% | 4.3% | 12.1% | 9.7% |
| pedestrian, 30-57 m | 0.08% | **8.1%** | 4.8% | **30.9%** | **82.7%** | 48.4% |
| vehicle, 30-57 m | 0 | 1.2% | 0.4% | 1.2% | 14.1% | 3.6% |
| truck, 30-57 m | 0 | 2.5% | 0 | 1.0% | 0 | 2.4% |

The real distribution of far pedestrians is cut off below about 6 points, while the medians are close (7 real, 6 synthetic): a labelling rule, not a density difference. **39% of our far training pedestrians are objects the real annotators would not have labelled.** Pedestrians are 62% of the test objects, and static false positives are the main walker error (docs/02 Section 8.2.1).

**2. Box fit.**
- Vehicle height: synthetic vehicles are 1.53 m tall against 1.64-1.71 m real. At 30-57 m, real tops sit 0.31 m above the highest point (synthetic 0.11 m). This is a size and padding difference.
- Pedestrian: width fill 0.75-0.78 real against 0.64-0.68 synthetic near the sensor. The near-range bottom gap is 0.52 m real against 0.35 m synthetic, where feet sit in the blind zone below the sensor.
- Truck: far real trucks are 5.9 m long against 8.2 m synthetic, so the far "truck" population is smaller vehicles.

## Decision

The scribe hypothesis holds on V2X-Real, with a different visibility policy than LUMPI. That is the strongest argument for a **dataset-specific, inferred** scribe rather than one hand-set rule.

The cheapest decisive test is E-S0: the same `g1-v5` frames with pedestrian labels filtered by the inferred minimum-points rule, against raw labels. Read pedestrian AP and static false positives per frame on realval-B. It needs only training runs (about 6 PointPillars runs, 24-48 GPU-hours).
