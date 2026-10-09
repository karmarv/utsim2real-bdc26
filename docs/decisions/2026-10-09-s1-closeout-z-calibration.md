# 2026-10-09 S1 close-out: range-dependent z calibration (C1), version S1+C1 for V2X; none for LUMPI

**Version.** `model-v2x-track/routed-g1z/submissions/2026-10-09_zcal/` (strategy S1+C1: S1's members, route and realism frames plus a z calibration after routing). LUMPI: no new version.

**Context.** The S1 close-out ([`02-STRATEGY.md` Section 8.1.2](../02-STRATEGY.md#812-close-out-steps-before-s2)) found that V2X loses 0.103 (realval-A) and 0.146 (realval-B) mAP between BEV@0.5 and 3D@0.5, as on the leaderboard (0.570 vs 0.465). V2X pedestrian centre z error by range 0-10 / 10-20 / 20-30 / 30+ m: +0.16 / +0.08 / +0.03 / -0.11 m on A, the same on B; vehicles +0.02 / +0.09 / +0.09 / -0.12 m. One per-class `z_offset` (already tuned in S1) cannot remove a bias that changes sign with distance. LUMPI's gap is 0.025 (84-91% of BEV-matched Persons already reach 3D IoU 0.5).

**Evidence.** `z_new = z + z0 + z_per_m * hypot(x, y)` per class ([`zcalib.py`](../../common/bdc26/detect/zcalib.py)), selected on realval-A by the official AP over z0 in [-0.30, 0.30] m and z_per_m in [-0.015, 0.015]:

| Track / class | (z0, z_per_m) | realval-A | realval-B (bootstrap 90% interval, P(gain)) | Class gate |
|---|---|---|---|---|
| V2X vehicle | (-0.15, +0.005) | 0.627 -> 0.641 | 0.662 -> 0.685 (+0.017 to +0.036, 1.00) | kept |
| V2X pedestrian | (-0.175, +0.0075) | 0.266 -> 0.290 | 0.226 -> 0.252 (+0.022 to +0.033, 1.00) | kept |
| V2X truck | (-0.025, +0.0025) | +0.002 | +0.002 (0.93) | dropped: gain below 0.01 |
| LUMPI, all classes | various | at most +0.005 | at most +0.004 (Truck -0.004) | dropped |

**Gate.** Upload gate ([README](README.md#3-evaluation-protocol-and-gates) Section 3): V2X combined estimate (B) 0.814 -> 0.828 (+0.014 >= 0.005); realval-B mAP 0.520 -> 0.537 (90% interval of the gain +0.014 to +0.021); same 50 frames as S1 byte for byte, every box equals S1's plus the calibration; kit scorer valid in 86 s. **Passed.** LUMPI: no class passed, joint routing reproduces S1: no LUMPI version.

**Classification.** Two post-processing scalars per class selected on labeled legal real frames, the same category as S1's `z_offset` and size scales (hyperparameter selection on the real train split; `01-CHALLENGE-FACTS.md` Section 10, question 3). No test frame involved. Disclose in the report.

**Decision.** Upload `routed-g1z` once on Track 2; no Track 1 upload.

**Outcome (2026-10-09).** **972563: V2X combined 0.7855** (965633: 0.7665), mAP 0.4869 (+0.022), vehicle 0.605 (+0.020), pedestrian 0.281 (+0.046), truck 0.574 (unchanged), BEV@0.5 0.5696 (unchanged, as expected for a z-only change), so the leaderboard BEV-3D gap fell from 0.105 to 0.083; realism identical (R 0.9203). Leaderboard / realval-B mAP 0.91 (S1: 0.89). Rank 1 (runner-up 0.6616). **Confirmation rule passed**; the calibration stays in every later V2X routed model.

**Consequences.** S2 and later re-select the calibration after routing (`route_predictions.py calibrate`); the V2X upload bar is now the S1+C1 estimate (B) 0.828; the remaining BEV-3D gap (0.129 on realval-B) is the S2-S4 height target.
