# 2026-10-09 S2 Center-Routed Small Objects: no upload-ready version; CenterPoint members kept for S3

**Version.** `model-<track>/routed-g2` with members `centerpoint-g1v3` (stride 8) and `centerpoint-s4-g1v3` (stride 4) added to the S1 members (LUMPI) and the S1+C1 members (V2X); LUMPI package `routed-g2/submissions/2026-10-09_s2/lumpi_s2_submission.zip` (candidate, below the upload gate). Strategy: [`02-STRATEGY.md` Section 8.2](../02-STRATEGY.md#82-s2-center-routed-small-objects), results in 8.2.1.

**Context.** S2 tested whether anchor-free center heads on 0.25 m z voxels beat the S1 pillars on small classes and on the V2X height loss. While training, an OpenPCDet bug (`CenterHead.assign_targets` relabels classes in place across head groups) turned V2X pedestrians into vehicle targets and LUMPI Motorcycles into Car targets; it was fixed at runtime (`common/bdc26/detect/pcdet_patches.py`, regression test) and the runs were retrained.

**Evidence** (official 3D AP@0.5, realval-A / realval-B; members after their own gated z calibration):

| Track / class | Incumbent | CenterPoint stride 8 | CenterPoint stride 4 | Class gate |
|---|---|---|---|---|
| LUMPI Bicycle | 0.265 / 0.102 | **0.350 / 0.128** | 0.318 / 0.134 | **passed** (B +0.025, P 1.00, A +0.085) |
| LUMPI Motorcycle | 0.008 / 0.015 | 0.069 / 0.022 | 0.057 / 0.023 | failed (B +0.007) |
| LUMPI Person | **0.340 / 0.134** | 0.095 / 0.038 | 0.168 / 0.047 | incumbent best |
| V2X vehicle | 0.641 / 0.685 | 0.650 / 0.675 | **0.685** / 0.681 | failed (B -0.004) |
| V2X pedestrian | **0.290** / 0.252 | 0.252 / **0.279** | 0.256 / 0.277 | incumbent best joint AP |
| V2X truck | **0.822 / 0.673** | 0.750 / 0.520 | 0.611 / 0.502 | incumbent best |

**Gate.** Upload gate ([README](README.md#32-gates)): LUMPI `routed-g2` (Bicycle from CenterPoint) realval-A 0.260 -> 0.272, late-A 0.255 -> 0.271, realval-B 0.1664 -> 0.1700 (bootstrap 90% interval of the gain +0.002 to +0.005), combined estimate (B) 0.5047 -> 0.5078: **+0.0031 < +0.005, failed**. Kit scorer on the package: valid, 156 s, 24,639 boxes. V2X: no class passed, `routed-g2` equals S1+C1: **no version**.

**Decision.** No S2 upload by the protocol; the current entries stay (LUMPI 965614, V2X 972563). The LUMPI package is kept for an optional confirmation upload (the entrant's call: development budget 99 of 100 left, expected gain small). The CenterPoint members go into S3 as fusion members, and the Bicycle route carries over.

**Findings that change the plan.**
- Static false positives dominate walker errors on both tracks: 72-77% (V2X) and 50-69% (LUMPI) of unmatched high-scoring pedestrian boxes repeat at the same 1 m cells across a scene (structures the twin lacks); CenterPoint produces 1.8-2.7x more. Oracle bound: V2X pedestrian 0.252 -> 0.346 on B, LUMPI Person 0.340 -> 0.400 on A. Static hard negatives in the generator (R3) move ahead of further detector changes.
- z voxels cut the V2X pedestrian BEV-3D gap on B from 0.158 to 0.112 at equal BEV AP; CenterPoint localizes better at IoU 0.7 (0.082 vs 0.058).
- R track: late-A realism proxies do not reproduce the leaderboard realism (0.901-0.908 vs 0.891); re-selecting frames on more proxies failed (0.901 vs 0.905). Realism needs generator content.

**Consequences.** S3 starts from `routed-g2` (both tracks) with the CenterPoint members; R3 (static clutter and long trucks as hard negatives) runs in parallel at higher priority; organizer question 2 (static-background prior) now has a measured value.
