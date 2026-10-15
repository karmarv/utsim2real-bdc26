# 2026-10-14 R5 Realism-led refinement: uploaded and confirmed on both tracks (V2X 0.8852, LUMPI 0.5198, rank 1 on both); LUMPI Person +0.024 through the late-A rule

**Version.** `model-<track>/routed-g7` (strategy R5): the confirmed R3 portfolios (`routed-g6`) plus seeds `voxelrcnn-ros-g1v4-s2` and `pvrcnnpp-ros-g1v4-s2` on both tracks and, on V2X, the R3 member set retrained on corpus `g1-v5` (`pointpillars-g1v5`, `voxelrcnn-ros-g1v5`, `pvrcnnpp-ros-g1v5`), plain and TTA. Packages `routed-g7/submissions/2026-10-14_r5/` with the upload copies `lumpi_r5_submission.zip` (md5 `ae3612bfa0607f3f0773702acd985fd0`) and `v2x_r5_submission.zip` (md5 `0d339f79a21059a8c97211d4d7c15533`). Plan, review and pre-registered rules: [`02-STRATEGY.md` Section 8.9](../02-STRATEGY.md#89-r5-realism-led-refinement-after-r3-review-and-plan-2026-10-14); results 8.9.1; rules review [`2026-10-14-rules-compliance-review.md`](2026-10-14-rules-compliance-review.md).

**Context.** After R3 the residual realism was in the background (exact EMD attributed point by point: 43-44% of the excess at ground level on both tracks, tall structure a minor share), V2X had never had a background density prior, LUMPI Person labels drift from manual to automatic boxes toward the test window, and seed variance had never been measured.

**Evidence** (official 3D AP@0.5 R40, realval-A / realval-B; every change through the class gate with the pooled condition, then the final gate against `routed-g6` on the final predictions):

| Item | Result |
|---|---|
| Density prior (random 50-frame draws) | V2X first prior 0.912 -> 0.934 (fit proxies); LUMPI v1 refined once by iterative fitting 0.918 -> 0.929 (fit), 0.912 -> 0.920 (held-out); a one-step refit on the G2-lite output was worse (0.892: cells saturate) |
| Realism gate (held-out proxies, pre-registered +0.003) | **V2X passed**: `g1-v5` frames 0.9336 against 0.9254 (as packaged 0.9366); **LUMPI failed**: 0.9360 against 0.9332 (+0.0028), so the R3 frames and no LUMPI `g1-v5` retrain |
| Seeds (seed 1666 against 666, TTA) | V2X Voxel R-CNN B 0.619 against 0.670 (truck 0.636 against 0.803), PV-RCNN++ 0.671 against 0.666; LUMPI Voxel R-CNN 0.188 against 0.178, PV-RCNN++ 0.196 against 0.191; **LUMPI Person B 0.104 -> 0.137 and 0.101 -> 0.124** |
| V2X `g1-v5` members (TTA, B) | pillars 0.567 -> 0.589 (truck 0.758 -> 0.827), Voxel R-CNN 0.639 (pedestrian 0.384), PV-RCNN++ 0.669 (A 0.684) |

| Track / class | R3 entry | R5 (`routed-g7`) | Source | dB (P), pooled (P) |
|---|---|---|---|---|
| LUMPI Person | 0.396 / 0.145 | **0.465 / 0.160** | `pp4_tta` + `vrros4s2_tta` (IoU 0.5); the third candidate by late-A (rule 3) | +0.015 (1.00), +0.053 (1.00) |
| LUMPI Car | 0.898 / 0.792 | R3 kept | new triple passed `fuse` (+0.011) but **not the final gate** (pooled -0.0003, P 0.39), the S5 pattern | reverted |
| LUMPI Bicycle, Motorcycle, Bus | R3 | R3 (frozen, rule 4) | | 0 |
| LUMPI Person tail copies | | dropped | B +0.008, but 34,793 boxes and 443 s in the kit scorer (rule: under 400 s) | |
| V2X vehicle | 0.828 / 0.852 | **0.857 / 0.864** | `pvros4s2_tta` + `vrros4s2_tta` + `vrros5_tta` (IoU 0.7), all new members | +0.012 (0.99), +0.024 (1.00) |
| V2X pedestrian | 0.370 / 0.408 | **0.381 / 0.418** | R3 fusion + tail copies (r 0.15 m, 4 copies; rule 5) | +0.010 (1.00), +0.010 (1.00) |
| V2X truck | 0.905 / 0.848 | R3 kept | best fusion +0.008 on B (under the bar); a floor change reverted by the final gate | 0 |

**Gate.** Upload gate (unclipped estimate (B) at least 0.005 above the R3 uploads; kit scorer under 400 s; LUMPI late-A not lower):

| Track | A-mAP | B-mAP (90% interval of the gain) | late-A | R (as packaged) | Estimate (B) | Bar | Kit scorer | Gate |
|---|---|---|---|---|---|---|---|---|
| LUMPI | 0.367 -> 0.377 | 0.221 -> 0.223 (+0.0014 to +0.0028) | 0.341 -> 0.351 | 0.934 (R3 frames) | 0.5631 -> **0.5649** | 0.568 | 157 s, 15,009 boxes | **not met** (+0.0018) |
| V2X | 0.701 -> 0.714 | 0.703 -> 0.710 (+0.0056 to +0.0104) | | 0.925 -> **0.937** | 0.9726 -> **0.9833** | 0.978 | 132 s, 24,759 boxes | **passed** (+0.0107) |

**Decision.** V2X: upload `v2x_r5_submission.zip` unchanged (16685). LUMPI: decision-ready but below the upload gate (uploaded by the entrant's call), as S4 LUMPI was (+0.003, uploaded by the entrant's call, confirmed +0.0025); it changes only Person, the LUMPI class whose leaderboard AP has followed realval-B (0.157 against 0.145), and the leaderboard keeps the best submission, so an upload cannot lower the entry: the entrant decides. Projection (previous leaderboard mAP + 0.6 x the mean of the A and B gains; realism at 1.0-1.5 x the packaged gain): **V2X 0.889-0.891** against 0.8789; **LUMPI 0.519-0.520** against 0.5169.

**Outcome** (2026-10-15 UTC). Both packages uploaded unchanged (LUMPI by the entrant's call, below the upload gate).

| | V2X 990255 | LUMPI 990245 |
|---|---|---|
| Combined (mAP, R) | **0.8852** (0.5972, 0.9332); was 0.8789 (0.5929, 0.9268) | **0.5198** (0.1714, 0.9323); was 0.5169 (0.1680, 0.9323) |
| Per class (vs the entry) | vehicle 0.719 -> 0.721 (+0.002), **pedestrian 0.403 -> 0.413 (+0.011)**, truck 0.657 identical | **Person 0.157 -> 0.180 (+0.024)**; every other class identical (same configuration) |
| Realism terms (CD, MMD, EMD, FPD) | 1.986, 0.00063, **1.182**, 1.468 (was 2.181, 0.00146, 1.345, 0.733) | identical (the R3 frames) |
| Rank | **1 of 20** (linyongchun 0.6616; Raj Patil entered V2X at 0.6261) | **1 of 21** (Raj Patil 0.4914) |
| Confirmation | **passed** (+0.0063; projected 0.889-0.891) | **passed** (+0.0029; projected 0.519-0.520) |

**Transfer.** The walker tail copies transferred as their construction predicts (V2X pedestrian +0.0105 on the leaderboard against +0.0098 on B). The LUMPI Person fusion chosen by the late-A rule transferred at 1.6 x B (+0.024 against +0.015), the largest LUMPI detection gain since S3's Bicycle. The V2X vehicle fusion of new members transferred at only 0.2 x B (+0.002 against +0.012), and 3D mAP@0.7 fell 0.198 -> 0.187 as it did locally (0.180 -> 0.170). V2X realism gained 0.58 x the packaged local gain: the EMD gain transferred (1.345 -> 1.182, about 0.9 x), but the FPD doubled on the server (0.733 -> 1.468) while it fell on the local proxies, so the proxies do not represent the hidden reference's mean and covariance. mAP against the projection rule (0.6 x the mean of the A and B gains): V2X 0.69 x, LUMPI 0.94 x.

**Consequences.**
1. **Seeds matter as much as many strategy steps:** the same config with another seed moved V2X truck by 0.17 and LUMPI Person by 0.03 on B; single-run member comparisons carry this noise, and fusions of seeds are the cheap way to average it out.
2. **The density prior is the V2X realism lever** (+0.011 R as packaged) and also helps its detector (pillars truck +0.07 on B); on LUMPI, frame selection from `g1-v4` already reached the refit's level.
3. **The final gate caught a second Car false gain** (S5, R5): fusion-level gains on LUMPI Car must survive the pooled check on the final predictions.
4. **Tail copies are a server-cost decision on LUMPI** (Person boxes x5), not an accuracy one.
5. The pre-registered late-A rule for LUMPI Person gave the first Person change since S3; its first two candidates failed the B gate, which is the intended protection.
6. **Tail copies and the late-A rule are the R5 levers that transferred** (1.07 x and 1.6 x B); fusions of seed members for V2X vehicle did not (0.2 x).
7. **V2X realism proxies miss the reference's moments:** the next V2X frame change should be judged on EMD and FPD separately, and an FPD rise on the server is a known risk of a density prior.
