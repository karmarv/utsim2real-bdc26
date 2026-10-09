# 2026-10-06 S1 first submission (both tracks): routed-g1, version `2026-10-02_first`

**Version.** `model-<track>/routed-g1/submissions/2026-10-02_first/` (strategy S1: engine G1 data, PointPillars members, per-class post-processing and routing; [`02-STRATEGY.md` Section 8.1](../02-STRATEGY.md#81-s1-calibrated-twin-routed-pillars)). Team line `KarmaRV` set on 2026-10-06 with `check_submission.py --set-team` (only `declaration.txt` changed).

**Evidence before upload.**

| Track | realval-A mAP | realval-B mAP | R (held-out proxies) | Estimate (A / B) | Kit scorer (`check_submission.py --official`) |
|---|---|---|---|---|---|
| LUMPI | 0.260 | 0.166 | 0.905 | 0.585 / 0.505 | valid, 134 s, 5.9 GB |
| V2X | 0.572 | 0.520 | 0.919 | 0.858 / 0.814 | valid, 95 s, 5.9 GB |

**Gate.** Pre-protocol: the first upload per track was planned as the check that local estimates transfer (Gate A, `02` Section 4); both zips had to pass the kit's own scorer under the 1,200 s server limit.

**Decision.** Upload both packaged zips unchanged, one per track.

**Outcome.**
- 957399 (LUMPI, Failed) and 957439 (V2X, Running 4 days with no log, cancelled) were hand-edited, re-zipped copies, not the packaged zips; a re-compressed folder fails the scorer with "Honor declaration is missing".
- The packaged zips, uploaded unchanged: **965614 LUMPI combined 0.4728** (mAP 0.1357, R 0.8912) and **965633 V2X combined 0.7665** (mAP 0.4648, R 0.9203), rank 1 on both tracks on 2026-10-06.
- Transfer: realism held (V2X +0.001, LUMPI -0.014 vs the proxies); leaderboard mAP was 0.82 (LUMPI) and 0.89 (V2X) of realval-B but only 0.52 of realval-A on LUMPI.

**Consequences.**
- The evaluation protocol ranks on realval-B with a paired bootstrap and a late-A check (decisions [README](README.md#3-evaluation-protocol-and-gates) Section 3).
- Every upload is the packaged zip, unchanged (renaming is fine); `check_submission.py` checks the zip root, the team line and the server cost first. Failure symptoms and the debug data to collect: track model READMEs Section 10.6.
