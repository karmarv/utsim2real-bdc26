# Releases

Each release tag fixes the code, the documentation and the submission files of the leaderboard entries at that point. The zip of every leaderboard entry is committed next to its manifest, byte for byte the file that was scored (md5 below and in the folder's `manifest.json`): in 1.0 as `submission_<track>.zip`; from S2 on under its upload name `<track>_<strategy>_submission.zip`, written by the packager (upload copies are git-ignored until they become leaderboard entries; then `git add -f` the file). The full submission register, with the gate result of every version, is [`docs/decisions/README.md` Section 2](docs/decisions/README.md#2-submission-register).

## 2.0 (pre-release, 2026-10-09)

**Leaderboard entries:** unchanged from 1.0 (LUMPI 965614, S1, combined 0.4728, rank 2 of 18; V2X 972563, S1+C1, combined 0.7855, rank 1 of 19). Their files are the 1.0 files above. No S2 version passed the upload gate, so 2.0 adds no entry file; the checked LUMPI S2 candidate `model-lumpi-track/routed-g2/submissions/2026-10-09_s2/lumpi_s2_submission.zip` stays local (git-ignored) until it becomes an entry.

**What 2.0 contains**
- Strategy S2, *Center-Routed Small Objects* ([`docs/02-STRATEGY.md` Section 8.2.1](docs/02-STRATEGY.md#821-results-2026-10-09); [decision record](docs/decisions/2026-10-09-s2-center-routed.md)): CenterPoint members at stride 8 and 4 on both tracks (`centerpoint-g1v3`, `centerpoint-s4-g1v3`), routed models `routed-g2`. Gates: LUMPI Bicycle moves to CenterPoint (realval-B 0.102 -> 0.128) but the combined estimate gains +0.003, below the +0.005 upload gate; V2X keeps S1+C1.
- A runtime fix for OpenPCDet's `CenterHead.assign_targets`, which relabeled classes across head groups (V2X pedestrians trained the vehicle head): `common/bdc26/detect/pcdet_patches.py`, applied by `register()`, with a regression test.
- Diagnosis that static structures cause 72-77% (V2X) and 50-69% (LUMPI) of the unmatched walker detections (oracle bound: V2X pedestrian realval-B 0.252 -> 0.346), which promotes static hard negatives (R3) in the plan.
- Tools: `pcdet_smoke.py` (measured training cost), `route_predictions.py validate` and `select --rule joint --calibrated`, `scorecard.py --realism-from`, track-prefixed upload copies `<track>_<strategy>_submission.zip` from the packager.
- R track: legal late-A realism proxies; the frame re-selection (R2) failed its gate, S1 frames kept.
- Tests: 47 (`python -m pytest -q common/tests`).

## 1.0 (pre-release, 2026-10-09)

**Leaderboard entries** (development phase; public leaderboards checked 2026-10-09):

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S1 | 965614 | 2026-10-06 21:37 | 0.4728 | 0.1357 | 0.8912 | 2 of 18 (1 until Oct 7) | [`submission_lumpi.zip`](model-lumpi-track/routed-g1/submissions/2026-10-02_first/submission_lumpi.zip) (`ea2c76393d6f8868762d6bac1ac03fa8`) | [s1 first submission](docs/decisions/2026-10-06-s1-first-submission.md) |
| 2 V2X-Real (16685) | S1+C1 | 972563 | 2026-10-09 15:17 | **0.7855** | 0.4869 | 0.9203 | **1 of 19** | [`submission_v2x.zip`](model-v2x-track/routed-g1z/submissions/2026-10-09_zcal/submission_v2x.zip) (`7fbb973e2c1715dea66d7850b8bde11f`) | [s1 close-out](docs/decisions/2026-10-09-s1-closeout-z-calibration.md) |

Per-class AP, realism terms and the scoring logs: [`codabench_965614.json`](model-lumpi-track/routed-g1/submissions/2026-10-02_first/codabench_965614.json), [`codabench_972563.json`](model-v2x-track/routed-g1z/submissions/2026-10-09_zcal/codabench_972563.json). The LUMPI file was uploaded as `submission_lumpi_karmarv.zip` (same bytes; also a release-0.1 asset). Field on 2026-10-09: LUMPI leader 0.4784 (mAP 0.1185, realism R 0.942); V2X runner-up 0.6616.

**What 1.0 contains**
- Strategy S1, *Calibrated Twin, Routed Pillars* ([`docs/02-STRATEGY.md` Section 8.1](docs/02-STRATEGY.md#81-s1-calibrated-twin-routed-pillars)): engine G1 synthetic data, PointPillars members, per-class post-processing and routing; models `model-<track>/routed-g1`.
- S1 close-out: joint routing with the class gate, `scorecard.py` with a paired frame bootstrap, the `strategy` registry column, evaluation subsets and error breakdowns, and the range-dependent z calibration C1, which gives the V2X version S1+C1 (`model-v2x-track/routed-g1z`, +0.019 combined on the leaderboard).
- Documentation: the strategy routes S2-S6 with steps and gates, the decisions folder (submission register, evaluation protocol and gates, progression tracker, calendar, dated records), named references R1-R42.
- Tests: 44 (`python -m pytest -q common/tests`).

## Earlier tags

0.1 (S1 first submission, 2026-10-06; zips as release assets), 0.2 (documentation of the strategy routes). 1.0 and 2.0 are described above.
