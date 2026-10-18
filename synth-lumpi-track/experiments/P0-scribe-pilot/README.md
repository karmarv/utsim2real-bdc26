# P0 scribe pilot: LUMPI (2026-10-18)

**Question.** Before committing the CVPR paper to "Sensor, Scene, Scribe" (agenda Section 13): does the real dataset label objects by rules that our synthetic labels do not follow, and can those rules be told apart from sensor and asset gaps? Do LUMPI's five unsynchronized sensors smear moving objects?

**Protocol.** Read-only statistics (`config.yaml`, `results.json`); nothing is trained. Real data is realval-A only: 1,280 Measurement4 frames, labels read through the guard, the challenge's 50k points. Synthetic data is 1,280 random frames of the corpus `g1-v5` (the R5/S6 corpus). Range bands are 0-15, 15-30 and 30-57 m. Fill is the point extent divided by the box size, for boxes with at least 15 points. Gaps are the distances from the box bottom to the lowest point and from the highest point to the box top. Timing uses 200 raw frames at full density, with per-point time and sensor id.

## Results

**1. Visibility policy: LUMPI keeps boxes the sensor cannot see; our labels never do.**

| Class, 30-57 m | Boxes with 0 points: real | synthetic | 1-2 points: real | synthetic |
|---|---|---|---|---|
| Car | 3.1% | 0 | 2.9% | 9.7% |
| Person | 1.8% | 0 | 3.8% | 2.0% |
| Van | 2.4% | 0 | 2.8% | 2.4% |
| Bus | 9.2% | 0 | 2.3% | 0.1% |

Every class keeps one box size per track: the within-track spread of l, w and h is 0 for Car, Van, Truck, Bus, Person and Bicycle (736 Car tracks; 2-4% of tracks change size once). Boxes are amodal and carried through occlusion by the track, which is how 0-point boxes arise.

**2. Two labelling regimes inside one recording (the manual flag, `score == 4`).**

| Class, band | Manual: median l x w x h (m) | Automatic: median l x w x h (m) | 0-point boxes, manual / auto |
|---|---|---|---|
| Person, 15-30 m | 0.70 x 0.70 x 1.90 | 1.03 x 0.82 x 1.84 | 0.4% / 3.8% |
| Person, 30-57 m | 0.72 x 0.71 x 1.90 | 1.60 x 0.80 x 1.84 | 1.6% / 6.1% |
| Van (id 6), 30-57 m | 4.77 x 2.03 x 1.80 | **1.04 x 0.80 x 1.78** (person-sized) | 1.0% / 12.9% |
| Bus, 30-57 m | | 5.50 x 0.79 x 2.13 (not a bus) | |

The automatic labeller uses other sizes and another taxonomy: its class 6 is person-sized. That explains why realval-B's class 6 is not vans.

**3. Box fit (fill), real against synthetic, at matched density.**
- Vehicles: real boxes are about 5% wider than their points (Car width fill 0.95 against 0.98-0.99 synthetic; Van and Truck the same). Real Van and Truck tops sit 0.12-0.21 m above the highest point (synthetic: 0.02-0.08 m).
- Person: length fill 0.78 real against 0.59-0.66 synthetic, at the same median box size (0.78 m). Our walkers fill less of the box: an asset or scribe difference that a decomposition must separate.

**4. Sensor and asset gaps at range** (not the scribe):
- At 30-57 m, synthetic objects have fewer points than real ones: Car 34 against 49, Truck 65 against 183, Bicycle 9 against 29, Motorcycle 9 against 12.
- 19% of synthetic far bicycles have 1-2 points (real: 1.3%).
- Synthetic far trucks are shorter (6.3 against 8.5 m).

**5. Timing.** The five sensors see the same vehicle a median 41 ms apart, which smears moving vehicles by a median 0.27 m (90th percentile 0.59 m). Our renders are synchronous, so they have no smear. The label's reference time could not be identified: the sensors' viewpoint differences (median 0.6 m between sensors on static objects) swamp the motion signal in this diagnostic.

## Decision

The scribe hypothesis holds on LUMPI, with three measurable components that size rescaling cannot reproduce:
- a track-persistence visibility policy (0-point boxes);
- regime-specific sizes and taxonomy (manual against automatic);
- padding.

Sensor and asset gaps at range are of similar size, so the paper needs the decomposition, not a scribe-only story. Timing is real but secondary: it is a candidate, not a claim. Next: E-S0, scribe-only label swaps on fixed frames (agenda Section 13.3).
