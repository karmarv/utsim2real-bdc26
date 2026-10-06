# 2026-10-06 First CodaBench uploads did not score; team name set in the packaged zips

**Context.** On 2026-10-02 the entrant downloaded both packaged zips (`model-<track>/routed-g1/submissions/2026-10-02_first/submission.zip`, team line left blank), typed the team name into `declaration.txt` by hand, compressed the files again and uploaded them:

| Track | CodaBench id | Uploaded file | Outcome |
|---|---|---|---|
| 1 LUMPI (16684) | 957399 | `submission.zip` (hand-edited copy) | Failed after a few hours, no score and no visible message; not counted (0 of 100 used) |
| 2 V2X-Real (16685) | 957439 | `submission_v2x_20261002.zip` (hand-edited copy) | Running for 4 days, the panel only ever showed "Preparing submission... this may take a few moments.."; cancelled 2026-10-06; counted (1 of 100 used) |

Other teams were scored in the same period (for example Equinox3D on Track 2, 2026-10-06 08:14), so the queue was not down for everyone.

**Evidence.**
- Server settings (public API, 2026-10-06): shared default queue (`queue: null`), image `codalab/codalab-legacy:py312`, `execution_time_limit` 1,200 s in both phases. `run.sh` pip-installs numpy, scipy, shapely and POT at every run, with `set -euo pipefail`.
- The packaged zips (not the uploaded copies) pass our validator and the kit's own scorer: `check_submission.py --official`, with realism-proxy-4 as the realism reference and realval-v1 labels under the 50 test IDs as a stand-in detection GT (3,652 and 1,134 boxes): Track 1 valid, 134 s, 5.9 GB peak, realism 0.9057; Track 2 valid, 95 s, 5.9 GB peak, realism 0.9188.
- Peak memory does not depend on the submission: the realism metrics subsample 10,000 points per side, and the dense 10k x 10k MMD matrices dominate. Detection time grows with the number of predicted boxes (Track 1 17,095, Track 2 18,728); the box cap ablation costs mAP (cap 100: -0.0005 LUMPI, -0.0013 V2X), so time is a fallback lever only.
- Simulated hand re-zips through the kit's scorer: a zip of the unzipped folder (everything under `submission/`) fails in 2.5 s with "Honor declaration is missing or invalid"; a zip of the folder's contents plus `__MACOSX/` entries is accepted.
- On a validation error `score.py` writes `scores.json` with `Infinity` for CD, MMD, EMD and FPD and exits 0. EMD is a leaderboard column on both tracks; if the site cannot store an infinite value, the submission ends as Failed and the scorer's message never reaches the leaderboard. This is a hypothesis to check against the submission's logs.

**Diagnosis (ranked; to be confirmed with the logs and the exact uploaded files).**
1. Track 1: the hand-made zip did not have the three entries at its root (nested folder), or `declaration.txt` lost the required sentence or was saved under another name or format. The scorer then rejects it within seconds of starting; the few hours were queue time.
2. Track 2: the job was never run or was lost on a worker (no log line at all, not even `[scoring] installing dependencies...`). A platform problem; the cure is to cancel and upload once more, and to tell the organizers if it repeats.
3. Unlikely: the 1,200 s limit (the server would have to be about 9x slower than our machine) and memory (the same 6 GB for every participant, and others score).

**Decision.**
1. The team name comes from `BDC_TEAM=KarmaRV` (`common/env/bdc26.env`) in the packager and every `make_submission.sh`; `submit.validate` fails on an empty team or on any zip entry other than `synthetic/*.bin`, `predictions.json` and `declaration.*` at the root.
2. `common/tools/check_submission.py` checks a zip as the server sees it, can rewrite only the team line (`--set-team`), and runs the kit's scorer locally with a legal stand-in reference (`--official`).
3. Both 2026-10-02 zips were rewritten with `--set-team KarmaRV`: only `declaration.txt` changed (the `predictions.json` checksums are unchanged: a8f3daa97b55... Track 1, a6cee1807d13... Track 2); `manifest.json` carries the new `zip_md5` and the two failed attempts under `codabench_attempts`.
4. Upload the packaged zip files unchanged; never unzip, edit and re-zip by hand. Root README Section 8.7 has the symptom table and the debug data to collect.

**Outcome (2026-10-06, same day).** The two checked zips, uploaded unchanged (renamed `submission_lumpi_karmarv.zip` and `submission_v2x_karmarv.zip`), scored at the first try: 965614 (Track 1, combined 0.4728) and 965633 (Track 2, combined 0.7665), both rank 1. The scoring logs begin with `[scoring] installing dependencies...`, the line that never appeared for 957439, which confirms that the earlier failures came from the uploaded copies or the platform, not from the packaged zips. Server records: `model-<track>/routed-g1/submissions/2026-10-02_first/codabench_<id>.json`; results in the root README Section 12.

**Consequences.** Every later upload is the checked zip, unchanged. If one fails, collect the status tooltip, the scoring stdout and stderr, the detailed results and the exact uploaded file (root README Section 8.7), and add the submission ids to the organizer email (`01-CHALLENGE-FACTS.md` Section 10, question 7).
