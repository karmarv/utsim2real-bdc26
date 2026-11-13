# Releases

Each release tag fixes the code, the documentation and the submission files of the leaderboard entries at that point. The zip of every leaderboard entry is committed next to its manifest, byte for byte the file that was scored (md5 below and in the folder's `manifest.json`): in 1.0 as `submission_<track>.zip`; from S2 on under its upload name `<track>_<strategy>_submission.zip`, written by the packager (the upload copies of leaderboard entries are committed; the ignore rule for upload copies was lifted on 2026-10-10). The full submission register, with the gate result of every version, is [`docs/decisions/README.md` Section 2](docs/decisions/README.md#2-submission-register).

From 6.0 on, a release also carries **the weights of its leaderboard entries** as GitHub release assets (checkpoints are not in git), listed with their repository paths and md5 in `releases/<tag>/weights.json`, so the entries can be rebuilt from a fresh clone (root README Section 6.11). `releases/<tag>/github.json` records the published release as GitHub shows it: URL, commit, label, upload times and the sha256 of every asset, checked against the local files. Real data is never a release asset: the assets are checkpoints trained on synthetic data only and the scored zips (synthetic frames, predictions, declaration).

**Making a release.** Steps 1-4 run on the server; steps 5-8 need the entrant's GitHub credentials and run in the entrant's terminal (the tool reads `$GITHUB_TOKEN` or `$GH_TOKEN`, or asks for a token at a hidden prompt).
1. Record every upload of the release: `package_submission.py <model> --tag <tag> --record <id> <codabench json>` (manifest and registry row), the server record `codabench_<id>.json`, the register row (`docs/decisions/README.md` Section 2), the track README Section 9, the root README Section 9.
2. Dry-run the reproduction scripts of every version on idle GPUs, one job per GPU (`common/pipeline/gpu_queue.sh`): `test/reproduce_<tag>.sh` must report IDENTICAL, `test/reproduce_<tag>_validation.sh` IDENTICAL or EQUIVALENT. Write the result into the release section below.
3. `python common/tools/release_weights.py collect --tag <tag> <model folder>:<submission tag> ...` writes `releases/<tag>/weights.json`; add the release section and its row in the release map below.
4. Commit on main and create the annotated tag: `git tag -a <tag> -m "<summary with the CodaBench ids>"`.
5. `git push origin main && git push origin <tag>`.
6. `python common/tools/release_weights.py publish --tag <tag>`: creates the GitHub pre-release of the tag (with `--final`, a full release; an existing release is updated) (notes: its section of this file, links pointing at the tag) and uploads every asset; it ends with "all assets uploaded and sizes match".
7. In a fresh clone at the tag: `release_weights.py fetch --tag <tag> --version <track>:<submission tag>` (md5-verified), then the version's `test/reproduce_<tag>.sh`.
8. Record the outcome in the release section and in `releases/<tag>/github.json` (release URL, label, the sha256 GitHub shows for each asset compared with the local files, fresh-clone check), commit and push; the tag stays on its commit.

The workflow from a scored upload to a release that anyone with read access can rebuild:

```mermaid
flowchart LR
  UP["the entrant's upload<br/>of the unchanged zip"] --> REC["record: codabench_ID.json,<br/>manifest, registry, register"]
  REC --> RS["reproduce_TAG.sh and<br/>reproduce_TAG_validation.sh"]
  RS --> DRY["dry run on idle GPUs:<br/>IDENTICAL or EQUIVALENT"]
  DRY --> COL["release_weights.py collect:<br/>releases/TAG/weights.json"]
  COL --> GIT["commit, annotated tag,<br/>push main and the tag"]
  GIT --> PUB["release_weights.py publish:<br/>pre-release, notes from this file,<br/>checkpoints and zips as assets"]
  PUB --> FET["fresh clone at the tag:<br/>fetch --version, md5 check"]
  FET --> RS2["reproduce scripts against<br/>the scored zip"]
```

## Release map (tags, leaderboard submissions, weights)

Every tag fixes the code, the documentation and the scored zips of the leaderboard versions of that point. A submission is identified by its CodaBench id, its zip (md5 in the folder's `manifest.json` and the server record `codabench_<id>.json`) and its model folder. Weights are GitHub release assets from 6.0 on; earlier versions are rebuilt by retraining from their configs.

| Tag | Date | Strategy | LUMPI (16684) id: combined | V2X (16685) id: combined | Weights in the release | Reproduction script (in the tree from 6.0 on) |
|---|---|---|---|---|---|---|
| 0.1 | 2026-10-06 | S1 | 965614: 0.4728 | 965633: 0.7665 | no (zips as assets) | `routed-g1/test/reproduce_first.sh` |
| 1.0 | 2026-10-09 | S1, S1+C1 | 965614: 0.4728 | 972563: 0.7855 | no | `reproduce_first.sh`, `routed-g1z/test/reproduce_zcal.sh` |
| 2.0 | 2026-10-09 | S2 (no upload) | 965614 | 972563 | no | |
| 3.0 | 2026-10-10 | S3 | 974348: 0.5015 (log; never listed) | 974400: 0.8381 | no | `routed-g3/test/reproduce_s3.sh` |
| 4.0 | 2026-10-11 | S4 | 975871: 0.5040 | 975938: 0.8485 | no | `routed-g4/test/reproduce_s4.sh` |
| 5.0 | 2026-10-11 | S5 | 978931: 0.5039 (not listed) | 978945: 0.8730 | no | `routed-g5/test/reproduce_s5.sh` |
| 5.1 | 2026-10-13 | R3 | 986489: 0.5169 | 986496: 0.8789 | no | `routed-g6/test/reproduce_r3.sh` |
| 5.2 | 2026-10-15 | R5 | 990245: 0.5198 | 990255: 0.8852 | no | `routed-g7/test/reproduce_r5.sh` |
| 6.0 | 2026-10-17 | S6 | 995869: 0.5228 (0.522754) | 995877: 0.8931 | **yes**: 21 checkpoints + 2 zips ([`releases/6.0/weights.json`](releases/6.0/weights.json)), published 2026-10-18 ([`github.json`](releases/6.0/github.json)) | `routed-g8/test/reproduce_s6.sh` (LUMPI), `routed-g8b/test/reproduce_s6b.sh` (V2X) |
| 7.0 | 2026-10-27 | S7 (the entries until S8; the F1 fallback) | **1014495: 0.5228** (0.522846, S7.6) | **1014682: 0.8982** (0.898172, S7.6) = 1001919 (S7 step 1) | **yes**: 25 checkpoints + 3 zips ([`releases/7.0/weights.json`](releases/7.0/weights.json)), published 2026-10-28 ([`github.json`](releases/7.0/github.json)) | `routed-g10/test/reproduce_s7s.sh` (LUMPI), `routed-g12/test/reproduce_s7s.sh` and `routed-g9/test/reproduce_s7.sh` (V2X) |
| 8.0 | 2026-10-30 | S8 (V2X entry and F1; LUMPI until 8.1) | **1022250: 0.5239** (0.523901, S8 U2) | **1022246: 0.9022** (0.902153, S8 V2X U2) | **yes**: 25 checkpoints + 2 zips ([`releases/8.0/weights.json`](releases/8.0/weights.json)), every checkpoint byte-identical to its 7.0 asset | `routed-g11b/test/reproduce_s8b.sh` (LUMPI), `routed-g13/test/reproduce_s8v.sh` (V2X) |
| 8.1 | 2026-10-30 | S8.2, S8.3 (LUMPI entry until 9.1; V2X unchanged) | 1022492: 0.5257 (0.525688, S8.3); 1022399: 0.5254 (S8.2) | 1022246: 0.9022 (as 8.0) | **yes**: 25 checkpoints + 3 zips ([`releases/8.1/weights.json`](releases/8.1/weights.json)), every checkpoint byte-identical to its 8.0 asset | `routed-g11d/test/reproduce_s8d.sh`, `routed-g11c/test/reproduce_s8c.sh` (LUMPI), `routed-g13/test/reproduce_s8v.sh` (V2X) |
| **9.2** | 2026-11-07 | **S9 close-out** (the entries on both tracks, final phase; LUMPI development entry `s9d`) | **1038963: 0.5428** (0.542809, `s9j`, final phase); 1031132: 0.5425 (0.542490, `s9d`, development) | **1038966: 0.9038** (0.903777, `s9f`, final phase) | **yes**: 23 checkpoints + 3 zips ([`releases/9.2/weights.json`](releases/9.2/weights.json)); 2 checkpoints new since 9.1 | `routed-g22/test/reproduce_s9j.sh`, `routed-g15/test/reproduce_s9d.sh` (LUMPI), `routed-g19/test/reproduce_s9f.sh` (V2X) |
| 9.1 | 2026-11-02 | S9 (the entries until the close-out) | **1028541: 0.5357** (0.535667, `s9a2`) | **1028491: 0.9030** (0.902971, `s9a`) | **yes**: 27 checkpoints + 2 zips ([`releases/9.1/weights.json`](releases/9.1/weights.json)); 4 checkpoints new since 8.1 | `routed-g12/test/reproduce_s9a2.sh` (LUMPI), `routed-g15/test/reproduce_s9a.sh` (V2X) |
| **10.0** | 2026-11-06 (tag set on 2026-11-11 on `e6c34d9`, the 9.2 commit) | S9 close-out, **removed from the boards** by the organizers (walkers placed at real label positions; their ruling of 2026-11-09) | 1038963: 0.5428 (`s9j`; removed) | 1038966: 0.9038 (`s9f`; removed) | **yes**: 23 checkpoints + 2 zips ([`releases/10.0/weights.json`](releases/10.0/weights.json)), byte-identical to the 9.2 assets | `routed-g22/test/reproduce_s9j.sh` (LUMPI), `routed-g19/test/reproduce_s9f.sh` (V2X) |
| **10.1** | 2026-11-11 | **S10 Clean Final**: no real label in training; the organizers rank KarmaRV from 1042287 / 1042294 on | 1047231: 0.5413 (0.541329, `c0pq`; frames do not qualify under the 2026-11-12 answer); **1042287: 0.5408** (`C0`, the best qualifying LUMPI entry); 1047204: 0.5396 (`c1pq`; frames as `c0pq`) | **1046758: 0.8889** (0.888864, `c1av5`, the best clean V2X entry); 1042294: 0.8885 (`C0`) | **yes**: 23 checkpoints + 5 zips ([`releases/10.1/weights.json`](releases/10.1/weights.json)); frozen 2026-11-12 (no dry runs) | `routed-c0/test/reproduce_c0.sh` (both tracks), `routed-c0/test/reproduce_c0pq.sh`, `routed-c1/test/reproduce_c1pq.sh` (LUMPI), `routed-c1a/test/reproduce_c1av5.sh` (V2X) |
| **10.2** | 2026-11-12 to 2026-11-13 | **S10 final week**, after the organizers' frame answer: new members and bags, packages whose frames come from the detectors' training data | 1050208: 0.5400 (0.540045, `s10-2-l1`, qualifies; below 1042287, so **1042287: 0.5408** stays the best qualifying LUMPI entry) | **1050253: 0.8913** (0.891305, `s10-2-v1`, qualifies; rank 1 on the final board) | **manifest ready**: 27 checkpoints + 2 zips, 4.03 GB ([`releases/10.2/weights.json`](releases/10.2/weights.json)); the GitHub release is published with the entrant's credentials | `routed-c2r/test/reproduce_s10-2-l1.sh` (LUMPI), `routed-c2r/test/reproduce_s10-2-v1.sh` (V2X) |
| **10.3** | in progress (from 2026-11-13) | **S10 final system**: one complete system per track, every member retrained on the calibrated generator, all planned improvements, uploaded together once every check passes | L6 (`routed-s10-3-l6`), building | V3x (`routed-s10-3-v3x`; fallback V3), building | with the uploads ([`releases/10.3/`](releases/)) | written at packaging |

The scripts sit in `model-<track>-track/<model>/test/`; every version's row in [`docs/decisions/README.md` Section 6.1](docs/decisions/README.md#61-reproducing-a-submission) names its release. Uploads that never scored (957399, 957439) are in the register, not in a release. GitHub release pages exist for 0.1, 6.0, 7.0, 8.0, 8.1 and 9.1; 10.1 is frozen (2026-11-12; its tag is pushed, the release-page work stopped); 10.0 is a pre-release to publish (on the 9.2 commit) ([releases](https://github.com/karmarv/utsim2real-bdc26/releases)); the other tags are git tags only, with their zips in the tree.

## 10.3 (in progress, from 2026-11-13): S10 final system

**In one line.** The entrant's decision of 2026-11-13: no further upload until one complete system per track carries every planned improvement, built from the generator up as the organizers' answers allow, with its weights published. Plan and gates: [`docs/decisions/2026-11-13-s10-10.3-final-system.md`](docs/decisions/2026-11-13-s10-10.3-final-system.md).

| Track | System | What it is | Frames | Status |
|---|---|---|---|---|
| LUMPI | **L6** `routed-s10-3-l6` | `C0`'s recipe (1042287) with all 14 checkpoints retrained on the calibrated generator (PandarQT re-cast + N1 density prior), plus P | 1042287's 50 ids from `g1-v6n1` | B1 training; builds automatically (`s10_3_build.sh`) |
| V2X | **V3x** `routed-s10-3-v3x` | V1's recipe (1050253) with all 7 checkpoints retrained on the calibrated generator (`aw_mid`, no-returns stored in the corpora) | V1's 50 ids from `g1-v6aw`, as stored | trains after B1; V3 (`c1a`'s recipe, 4 checkpoints) is the fallback |

## 10.2 (2026-11-12 to 2026-11-13): S10 final week, after the organizers' frame answer

**In one line.** Everything built after the 10.1 uploads, kept apart from 10.1 at the entrant's request (2026-11-12): new detector members and bags, packages whose 50 frames come from the corpora the detectors were trained on, and the plan to the close. Closed on 2026-11-13 with its weights manifest; the final uploads are release 10.3.

**Uploads** (both meet every ruling; audited byte by byte with `common/tools/s10_2_audit_upload.py` and re-merged exactly with `reproduce_submission.py`; [record Section 11.2](docs/decisions/2026-11-12-s10-10.2-clean-final-push.md)):

| Track | Upload | System | Frames | md5 | Projected | Scored |
|---|---|---|---|---|---|---|
| LUMPI | **1050208** (`s10-2-l1`, L1) | `routed-c2r` (`c2rv6`): `C0` plus the late-A Person route | byte-identical to 1042287's (`g1-v6`) | `4a1fd4b242c5fd44ce1c0f5bfcbeb004` | 0.5413 / 0.5419 / 0.5422 | **0.540045** (mAP 0.194093, R 0.9342); -0.000755 against `C0`: Person 0.3058 -> 0.2994, all else and realism equal |
| V2X | **1050253** (`s10-2-v1`, V1) | `routed-c2r`: the V2X `C2` rehearsal (rule 14b against `c1a`) | `g1-v6`, 31% no-return points, equal to 1046758's | `9f836506b943141b4cdce78648e143c7` | 0.8893 | **0.891305** (mAP 0.600907, R 0.940605); +0.002441 against `c1av5`: truck +0.0073, pedestrian +0.0012 |

**Ready, not uploaded; folded into 10.3** (the entrant, 2026-11-13: P goes into the 10.3 LUMPI system; all checks of record Section 11.6 pass: rules 1 and 1b, rule 14 GO against `C0`, kit check valid, audit 6 of 6, re-merge identical):

| Track | Package | System | Frames | md5 | Projected | Validation against `C0` |
|---|---|---|---|---|---|---|
| LUMPI | `s10-2-l5` (L5) | `routed-s10-2-l5`: `C0` unchanged plus P (`final_adjust`: Person height and Bicycle footprint moved toward the train-split median real box, Person copies) | byte-identical to 1042287's (`g1-v6`) | `eca9d91051f50a16efa6c50d03778a0b` | 0.5414 / 0.5422 / 0.5428 | A +0.0015, B +0.0023, late-A +0.0009 |

**Built, not uploaded:** V2X `s10-2-v2` (V2): NO-GO against V1, equal on validation once the class gate reverted every class (record Section 11.6).

**Withdrawn, never uploaded** (frames-only calibrations, not allowed under the answer): the LUMPI `c2r` package of 2026-11-11 (`g1-v6pq` frames; kept out of git), and the held LUMPI N1 and V2X `aw_mid` packages (git-ignored).

**New members and bags** (all rule 1 clean; tuning and 12-view runs in progress): PV-RCNN++ draws `d4`, `d5`, GBlobs `d2`, `d3` and their averaged (epochs 31-40) versions; Voxel R-CNN R1 draws `d2r1m`, `d3r1m` (both tracks) and GBlobs averaged members; V2X VoxelNeXt `d6`; the bags `pvrcnnpp-ros-g1v6x5`, `voxelrcnn-rosn-gblobs-g1v6x3`, the GBlobs `pqx3`/`pqx5` bags, the R1 bags `r1s5`/`r1x6`/`r1x8` and V2X `voxelnext-ros-g1v6x6` (each also averaged). Measurements: [S10 record, Sections 15.16-15.17](docs/decisions/2026-11-08-s10-clean-final-plan.md).

**The organizers' rulings, resolved in 10.2** (all of them, against every upload: [S10 record, Section 15.18](docs/decisions/2026-11-08-s10-clean-final-plan.md)).
- **Rule 1b in code.** The 2026-11-12 rule ("a calibration may change the submitted frames only if it also changed the data your detector was trained on") is now checked by `common/tools/clean_check.py`, and `package_submission.py` refuses frames that fail it. It passes 1042287, 1042294, 1046758 and both 10.2 packages; it fails the `c1pq`/`c0pq` frames and refuses to rebuild them as an upload.
- **The board.** Under the 2026-11-09 ruling (d) the LUMPI board shows our highest score, 1047231, and we cannot choose another. The remedy is the disclosure (record Appendix C, which the entrant sends) and a qualifying upload above 0.5413.
- **The plan to the close:** [`docs/decisions/2026-11-12-s10-10.2-clean-final-push.md`](docs/decisions/2026-11-12-s10-10.2-clean-final-push.md). Candidates L1-L4 (LUMPI) and V1-V3 (V2X); gates fixed before any result; every upload before 2026-11-15 18:00 UTC. Revised after the L1 result and the board of 2026-11-12 (record Sections 11.4-11.5, adopted 2026-11-13): LUMPI L5, L3 and L6 (L2 stopped, L4 dropped); V2X V3 in any case.

## 10.1 (release, 2026-11-12; pre-release 2026-11-11): S10 Clean Final, the clean uploads of Nov 8 and Nov 10

**In one line.** Every system the organizers rank for KarmaRV: five final-phase uploads (LUMPI 1042287, 1047204 and 1047231; V2X 1042294 and 1046758). Every detector is trained only on synthetic corpora that contain no real label row. The best scores are LUMPI 1047231 (0.541329) and V2X **1046758 (0.888864)**; under the organizers' frame answer of 2026-11-12 the best qualifying LUMPI entry is **1042287 (0.540800)** (see below).

**Why 10.1 is separate from 10.0.**
- The organizers' clarification of 2026-11-07 says that real labels, and object points cut out with real boxes, must not enter the training set.
- Our generator had placed walkers at the positions, headings and sizes of real label rows until Nov 2. We reported this and stopped it.
- Their ruling of 2026-11-09: KarmaRV is ranked only by LUMPI 1042287 and V2X 1042294 onward. The earlier final-phase uploads (release 10.0) are removed from the boards but still count toward the submission limit. Each team's best entry counts, and the report must describe the change.
- [S10 record Section 15.14](docs/decisions/2026-11-08-s10-clean-final-plan.md).

**Rule 1 (`common/tools/clean_check.py`), run on 2026-11-11 on each upload's routed model.** A member is clean when no corpus it trained on names a real label row.

| Release | Track | Upload | Model | Members | Realism frames | Rule 1 |
|---|---|---|---|---|---|---|
| 10.1 | LUMPI | 1042287 (`C0`) and 1047231 (`c0pq`) | `routed-c0` | 13, all clean | `pcdet/g1-v6` (`C0`), `pcdet/g1-v6pq` (`c0pq`), both clean | **PASS** |
| 10.1 | LUMPI | 1047204 (`c1pq`) | `routed-c1` | 12, all clean | `pcdet/g1-v6pq`, clean | **PASS** |
| 10.1 | V2X | 1042294 (`C0`) | `routed-c0` | 5, all clean | `pcdet/g1-v6`, clean | **PASS** |
| 10.1 | V2X | 1046758 (`c1av5`) | `routed-c1a` | 5, all clean | `pcdet/g1-v6`, clean | **PASS** |
| 10.0 | LUMPI | 1038963 (`s9j`) | `routed-g22` | 12, 10 trained on `g1-v2`..`g1-v4d2` (real M4 Person label rows) | `pcdet/g1-v6`, clean | FAIL |
| 10.0 | V2X | 1038966 (`s9f`) | `routed-g19` | 6, all trained on `g1-v3`..`g1-v5` (real walker label rows) | `pcdet/g1-v5`, label rows | FAIL |

**Leaderboard.** All five are final-phase uploads made by the entrant, with the scores taken from the scoring outputs the entrant shared. The public leaderboard API shows a bot check, and it is not bypassed.

| Track | Version | CodaBench id | Combined | 3D mAP@0.5 | Realism R (EMD) | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | `C0`: the first clean system | 1042287 (2026-11-08) | 0.5408 | 0.1950 | 0.9342 (1.2720) | [`lumpi_s10_submission.zip`](model-lumpi-track/routed-c0/submissions/2026-11-07_c0/lumpi_s10_submission.zip) (`1de9f12c1f18d045e5b0c05e08a2f793`) | [S10 record, Section 13](docs/decisions/2026-11-08-s10-clean-final-plan.md) |
| 1 LUMPI (16684) | `c1pq`: `C0` plus one Person route; frames with the PandarQT near-field re-cast | 1047204 (2026-11-11) | 0.5396 (0.539575) | 0.1929 | 0.9355 (1.2464) | [`lumpi_s10_submission.zip`](model-lumpi-track/routed-c1/submissions/2026-11-10_c1pq/lumpi_s10_submission.zip) (`6c2da31f4146a174caba4923709f87c4`) | [S10 record, Sections 15.15.7-15.15.8](docs/decisions/2026-11-08-s10-clean-final-plan.md) |
| 1 LUMPI (16684) | `c0pq`: `C0`'s detections with the `c1pq` frames (the best LUMPI score; its frames do not qualify under the 2026-11-12 answer) | 1047231 (2026-11-11) | **0.5413** (0.541329) | 0.1950 | 0.9355 (1.2464) | [`lumpi_s10_submission.zip`](model-lumpi-track/routed-c0/submissions/2026-11-10_c0pq/lumpi_s10_submission.zip) (`aa167c395f3d8c4549b063d9e269a863`) | [S10 record, Sections 15.15.9-15.15.10](docs/decisions/2026-11-08-s10-clean-final-plan.md) |
| 2 V2X-Real (16685) | `C0`: the first clean system | 1042294 (2026-11-08) | 0.8885 (0.888471) | 0.5976 | 0.9406 (1.1097) | [`v2x_s10_submission.zip`](model-v2x-track/routed-c0/submissions/2026-11-07_c0/v2x_s10_submission.zip) (`c70e8a341b7647d8ae7712a09ba1baf6`) | [S10 record, Section 13](docs/decisions/2026-11-08-s10-clean-final-plan.md) |
| 2 V2X-Real (16685) | `c1av5`: `C0` plus the V5 overhead demotion of pedestrian boxes (**the best clean V2X entry**) | 1046758 (2026-11-10) | **0.8889** (0.888864) | 0.5981 | 0.9406 (1.1097) | [`v2x_s10_submission.zip`](model-v2x-track/routed-c1a/submissions/2026-11-09_c1av5/v2x_s10_submission.zip) (`2f3d80cbfed8c0f4064a8ba77aa5ecb5`) | [S10 record, Sections 15.14.6-15.14.7](docs/decisions/2026-11-08-s10-clean-final-plan.md) |

Server records: `codabench_<id>.json` in each submission folder.

**What each version is**, for the report:

| Version | Change against the previous version | Members (checkpoints) | Training corpora | Test-time stages | Realism frames | Kit boxes |
|---|---|---|---|---|---|---|
| LUMPI `C0` (1042287) | every member retrained on the clean `g1-v6` corpus family; route, fusion and calibrations re-selected from scratch on realval A/B (S10 rules 1-3) | 13 (14) | `g1-v6`, `g1-v6d2`, `g1-v6j` | 8- and 12-view TTA; fusion of up to 3 members (Bicycle, Car, Motorcycle, Person, Truck); score floors (budget); Person and Bus low-score copies; anchored box-size calibration (Car, Person) | 50 `g1-v6` val frames chosen on fit proxies (S9 rule 4) | 24,088 |
| LUMPI `c1pq` (1047204) | Person route `bvrrosfswa6x4_tta12` (an averaged 4-draw Voxel R-CNN bag); Unknown route; realism frames with the PandarQT re-cast | 12 (17) | adds `g1-v6d3`, `g1-v6d4` | as `C0`; Person not fused; size calibration Car only | the same 50 ids from `g1-v6pq` | 24,481 |
| LUMPI `c0pq` (1047231) | `C0`'s detections (byte-identical predictions) with `c1pq`'s frames (byte-identical) | 13 (14) | as `C0` | as `C0` | as `c1pq` | 24,088 |
| V2X `C0` (1042294) | every member retrained on `g1-v6`; route, fusion and calibrations re-selected | 5 (4) | `g1-v6`, `g1-v6d2` | 8- and 12-view TTA; fusion (all three classes); budget; pedestrian copies; sparse-point demotion; size calibration (vehicle) | 50 `g1-v6` frames with 31% null returns added at packaging | 41,225 |
| V2X `c1av5` (1046758) | adds the V5 overhead demotion of pedestrian boxes with points above them (rule 11) | 5 (4) | as `C0` | as `C0`, plus V5 | as `C0` | 41,232 |

**How the scores decompose.**
- `c1pq` against `C0`: realism +0.001324 (EMD -0.026, the PandarQT re-cast) and mAP -0.002047 (the Person route; it lost on late-A locally, record 15.15.8).
- `c0pq` against `C0`: exactly the realism gain, +0.000529 combined.
- `c1av5` against V2X `C0`: +0.000393 (pedestrian AP +0.0014; realism identical).

**The frames under the organizers' answer of 2026-11-12** (received after all five uploads; the rule row in [docs/01 Section 3.1](docs/01-CHALLENGE-FACTS.md#31-our-operating-interpretation); the full account is in the S10 record, Section 15.17, from release 10.2 on).
- The answer: the 50 frames "are meant to represent the synthetic data your detector was trained on"; a calibration applied only to the 50 frames, with the training data unchanged, is not allowed. The same calibration inside the generator, with the detector retrained on it, is allowed.
- **LUMPI 1042287 (`C0`), V2X 1042294 and 1046758:** the frames come from the corpus family every member trained on. The V2X frames store 31% (0,0,0) no-return points, as the real sensor does; the detector's loader removes them in training and inference.
- **LUMPI 1047204 (`c1pq`) and 1047231 (`c0pq`):** the PandarQT near-field re-cast (`pcdet/g1-v6pq`) reached the 50 frames but not the training data of any member. Under the answer they do not qualify; **the best qualifying LUMPI entry is 1042287 (0.5408)**. Both stay in this release as the record of what was uploaded.

**Real data in 10.1, for the report.** The organizers allowed every use below on 2026-11-09, as long as none of the 100 forbidden frames is involved (`common/tools/clean_check.py` reads each corpus card's `real_data_use`).
- Validation and model selection on non-forbidden real frames: LUMPI realval A/B; V2X infrastructure frames, including the public val and test splits.
- Label statistics as scalars, in the generator and at test time:
  - size quantiles of the legal realval labels;
  - the walker box mixture and the 10-bin walker distance histogram;
  - four vehicle size thresholds (the LUMPI class convention);
  - the anchored test-time box-size calibration.
- Realism calibration from unlabelled real clouds: the background density prior, and the proxies that choose the 50 submitted frames.
- Sensor metadata:
  - the LUMPI Measurement4 rig and beam tables, including the PandarQT near-field re-cast of `pcdet/g1-v6pq` (`common/tools/s10_beamfix.py`, used by `c1pq` and `c0pq`);
  - the V2X beam elevation table.
- Test-time post-processing of our detectors' outputs: augmentation, box fusion, score floors, low-score duplicate boxes, point-count rescoring and the V5 overhead demotion.
- **R1** (synthetic static blocks placed where unlabelled real frames show structures the twin lacks; allowed on 2026-11-09) is in no 10.1 upload.

**Release assets.**
- 23 checkpoints and the 5 scored zips, 3.47 GB, listed with md5, size and users in [`releases/10.1/weights.json`](releases/10.1/weights.json).
- Each version shares one upload name (`<track>_s10_submission.zip`). So the zip assets are named `<track>.<model folder>.<submission tag>.<file name>`, for example `lumpi.routed-c0.c0pq.lumpi_s10_submission.zip`; `fetch` places each at its repository path.
- Checkpoints are named `<track>.<model folder>.epoch40.pth`.

```bash
python common/tools/release_weights.py fetch --tag 10.1 --version lumpi:c0pq      # or lumpi:c0, lumpi:c1pq, v2x:c0, v2x:c1av5
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-c0/test/reproduce_c0pq.sh
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-c1a/test/reproduce_c1av5.sh
```

**Reproduction.**
- The five test-frame scripts re-merge to identical boxes from the cached member predictions (CPU check, 2026-11-11): LUMPI 24,088 / 24,088 / 24,481; V2X 41,225 / 41,232.
- The GPU dry runs (test-frame inference with the released weights, then the comparison with the scored zip) are **not run**: 10.1 was frozen on 2026-11-12 (below).
- The validation scripts (`reproduce_<tag>_validation.sh`) sit beside the test scripts.

**Frozen (the entrant, 2026-11-12, after the push of `512a976`).** 10.1's LUMPI uploads 1047204 and 1047231 are invalid under the frame rule, and the entrant asks the organizers to drop them. No more work goes into 10.1: no dry runs and no further release-page work. The tag stays the record of what was uploaded. Every clean submission from here on is release 10.2.

**Not yet in 10.1.**
- The GPU dry-run results.
- Every later model, package and upload of the final week is **release 10.2** (the entrant's choice, 2026-11-12), so that each increment stays separate.

## 10.0 (pre-release, tag on `e6c34d9`, set 2026-11-11): the removed first final-phase uploads

- **What it marks.** The first final-phase uploads, LUMPI 1038963 (`s9j`, 0.542809) and V2X 1038966 (`s9f`, 0.903777). The tag sits on the commit of release 9.2 (`e6c34d9`), which holds their code, records and zips byte for byte.
- **Why they were removed.** Their members trained on corpora whose walkers were placed at the positions, headings and sizes of real label rows. The organizers removed both uploads from the boards on 2026-11-09, and both still count toward the limit. The rule 1 table under 10.1 shows the failing members: LUMPI `routed-g22`, 10 of 12 on `g1-v2`..`g1-v4d2`; V2X `routed-g19`, 6 of 6 on `g1-v3`..`g1-v5`, and its frames.
- **What they were.** The S9 close-out: the anchored box-size calibration on the development entries `s9d` (LUMPI) and `s9a` (V2X). See 9.2 below for the change, the scores and the dry run (EQUIVALENT on 2026-11-07).
- **Release assets.**
  - 23 checkpoints and the 2 scored zips (4.01 GB) in [`releases/10.0/weights.json`](https://github.com/karmarv/utsim2real-bdc26/blob/main/releases/10.0/weights.json), all byte-identical by md5 to their 9.2 assets.
  - The manifest is on `main` (it was written after the tag's commit), so fetch from a `main` checkout, then reproduce at the tag (checkpoints are git-ignored, so they stay in place across the checkout):

    ```bash
    git checkout main && python common/tools/release_weights.py fetch --tag 10.0 --version lumpi:s9j     # or v2x:s9f
    git checkout 10.0 && CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g22/test/reproduce_s9j.sh
    ```
- **The report** describes the change and lists both ids as removed.

## 9.2 (pre-release, 2026-11-07)

**Leaderboard.** The S9 close-out on both tracks. The entrant uploaded both zips unchanged in the final phase (the F2 uploads, after the development close at 2026-11-06 04:59 UTC). The final leaderboard hides ranks until the close, but each scoring output shows its score. The public leaderboard API returned a bot-check page on 2026-11-07 at 03:31 UTC, so the scores below come from the scoring outputs the entrant shared.

| Track | Version | CodaBench id | Phase | Combined | 3D mAP@0.5 | Realism R | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S9 close-out `s9j` | 1038963 | final (F2) | **0.5428** (0.542809) | 0.1973 | 0.9342 | [`lumpi_s9j_submission.zip`](model-lumpi-track/routed-g22/submissions/2026-11-05_s9j/lumpi_s9j_submission.zip) (`60d6d37a1dc4de5dc5bd28490e4a4b60`) | [s9 clean twin, Sections 15.31-15.32](docs/decisions/2026-11-02-s9-clean-twin-plan.md#1532-final-phase-s9j-and-s9f-score-above-the-development-entries-release-92-2026-11-07-0345-utc) |
| 2 V2X-Real (16685) | S9 close-out `s9f` | 1038966 | final (F2) | **0.9038** (0.903777) | 0.6189 | 0.9332 | [`v2x_s9f_submission.zip`](model-v2x-track/routed-g19/submissions/2026-11-05_s9f/v2x_s9f_submission.zip) (`ae8ceb825b0eb04e64cfd9ab3e54d8ec`) | same |
| 1 LUMPI (16684) | S9 `s9d` | 1031132 | development (rank 1 of 25 at the close) | 0.5425 (0.542490) | 0.1969 | 0.9342 | [`lumpi_s9d_submission.zip`](model-lumpi-track/routed-g15/submissions/2026-11-03_s9d/lumpi_s9d_submission.zip) (`20d2d5fac2408a2fb91d03985645b70d`) | [s9 clean twin, Sections 15.6-15.7](docs/decisions/2026-11-02-s9-clean-twin-plan.md) |

Server records: [`codabench_1038963.json`](model-lumpi-track/routed-g22/submissions/2026-11-05_s9j/codabench_1038963.json), [`codabench_1038966.json`](model-v2x-track/routed-g19/submissions/2026-11-05_s9f/codabench_1038966.json), [`codabench_1031132.json`](model-lumpi-track/routed-g15/submissions/2026-11-03_s9d/codabench_1031132.json).
- **What changed.** One new last stage of the merge: an anchored box-size calibration (`size_calibration` in `model.yaml`, `route_predictions.apply_size_calibration`). It keeps the box end nearest a sensor, moves the far end, and keeps the box bottom. The constants were selected on realval A and B with a pre-registered grid and the 6.0 pooled rule (`common/tools/size_calibration.py`). Each zip was packaged from its development entry's cached member predictions, so only the calibrated classes' box geometry differs from the scored entries.
- **LUMPI `s9j` against `s9d`: +0.00032** (projected +0.0004). Person +0.0036, Car -0.0010, 3D mAP@0.7 +0.0070; every other class and the realism are identical.
- **V2X `s9f` against `s9a` (1028491, 0.902971): +0.00081** (projected +0.0015). Vehicle +0.0078, pedestrian -0.0050, truck identical, 3D mAP@0.7 +0.0338; the realism is identical.
- **`s9d`** is in the release as the development entry at the close (rank 1 of 25), and its members are the same as `s9j`'s. LUMPI `s9b` (1030540, 0.5415), `s9c` (1030511, 0.5412) and the diagnostic `s9iu` (1035970, 0.5400) have their zips and scripts in the tree but no weights in a release.

**Release assets.** The three zips and the 23 checkpoints they use (4.03 GB; LUMPI 12, V2X 11), in [`releases/9.2/weights.json`](releases/9.2/weights.json). 21 checkpoints are 9.1 assets, byte-identical by md5. New: LUMPI `pvrcnnpp-ros-g1v6` and `voxelrcnn-rosf-g1v6`, the `g1-v6` members of the `s9d` Person and Car routes. New in the tree since 9.1:
- the size-calibration stage and its selection tool;
- the S9 portfolio folders `routed-g13`, `routed-g14` and `routed-g15` (LUMPI `s9b`, `s9c`, `s9d`), `routed-g16`-`routed-g21`, `routed-g22` (`s9j`) and V2X `routed-g16`-`routed-g19` (`s9f`);
- the S9 members trained after 9.1, and the fuse fix (16 workers and `gc.freeze`).
```bash
python common/tools/release_weights.py fetch --tag 9.2 --version lumpi:s9j                 # or v2x:s9f, lumpi:s9d
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g22/test/reproduce_s9j.sh
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g19/test/reproduce_s9f.sh
```
Dry run on 2026-11-07 (`$BDC_DATA/logs/s9/r920`, each test-frame script alone on an idle GPU). Both test-frame scripts come back **EQUIVALENT**, the same result as 9.1 and `s9d` (record Section 15.26):
- **LUMPI `reproduce_s9j.sh`:** 24,870 against 24,874 boxes. 24,868 are matched, with centres within 0.0006 m at the 99th percentile. All 8 unmatched boxes score below 0.3. Kit check valid in 209 s.
- **V2X `reproduce_s9f.sh`:** 38,809 against 38,824 boxes. 38,794 are matched (centres within 0.002 m at the 99th percentile). All 45 unmatched boxes score below 0.3. Kit check valid in 230 s.
- **Both:** the 50 realism frames are byte-identical. The calibration stage is deterministic, so the variation is the members' GPU inference, as in 9.1: the cached member predictions behind the scored zips came from shared-GPU runs that no fresh run repeats bit for bit.
The validation scripts were dry-run the same day: the realval-A/B inference was spread over the 8 idle GPUs (47 jobs, none failed), then each script scored on its own GPU. Both pass:
- **LUMPI `reproduce_s9j_validation.sh`: EQUIVALENT.** A 0.4078 (recorded 0.4079), B 0.2370, late-A 0.3746. Every class is within 6.2e-4 AP. 19 of 28 member files are bit-identical; the other 9 differ in the last digits.
- **V2X `reproduce_s9f_validation.sh`: IDENTICAL** (within 1e-4 per class). A 0.7427, B 0.7261, both as recorded. Every class is within 4.0e-5 AP. 17 of 28 member files are bit-identical; the other 11 differ in the last digits.

## 9.1 (pre-release, 2026-11-02)

**Leaderboard** (development phase, extended to 2026-11-06 04:59 UTC; public leaderboards checked 2026-11-02, 19:20 UTC): S9 on both tracks, rank 1 on both. These two zips are the F1 candidates for the final phase, unless a later S9 version scores higher before the development phase closes.

| Track | Version | CodaBench id | Uploaded (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S9 `s9a2` | 1028541 | 2026-11-02 19:11 | **0.5357** (0.535667) | 0.1890 | 0.9342 | **1 of 24** (next 0.5132) | [`lumpi_s9a2_submission.zip`](model-lumpi-track/routed-g12/submissions/2026-11-02_s9a2/lumpi_s9a2_submission.zip) (`45e4eda799949770cece154a990eb979`) | [s9 clean twin, Section 14.9](docs/decisions/2026-11-02-s9-clean-twin-plan.md#149-leaderboard-s9a2-and-s9a-release-91) |
| 2 V2X-Real (16685) | S9 `s9a` | 1028491 | 2026-11-02 18:24 | **0.9030** (0.902971) | 0.6180 | 0.9332 | **1 of 28** (next 0.8112) | [`v2x_s9a_submission.zip`](model-v2x-track/routed-g15/submissions/2026-11-02_s9a/v2x_s9a_submission.zip) (`3e59e5b3c76b440bd11aeba0304cc75e`) | same |

Server records: [`codabench_1028541.json`](model-lumpi-track/routed-g12/submissions/2026-11-02_s9a2/codabench_1028541.json), [`codabench_1028491.json`](model-v2x-track/routed-g15/submissions/2026-11-02_s9a/codabench_1028491.json).
- **LUMPI against S8.3 (1022492): +0.00998.** Person 0.188 -> 0.262 (+0.0745) from two members trained on the label-free corpus `g1-v6`. Realism 0.9323 -> 0.9342 from the `g1-v6` frames (EMD 1.302 -> 1.272). Every other class is within 0.0008.
- **V2X against S8 (1022246): +0.00082.** Pedestrian 0.443 -> 0.446, from a re-fusion of existing members; everything else is identical.
- Both projections had the right sign. LUMPI +0.0049 detection plus about +0.002 realism was projected, +0.0100 scored. V2X +0.0007 was projected, +0.0008 scored.

**Release assets.** The two zips and the 27 checkpoints they use (4.70 GB; LUMPI 16, V2X 11), in [`releases/9.1/weights.json`](releases/9.1/weights.json). New since 8.1: LUMPI `voxelrcnn-ros-g1v6` and `voxelnext-ros-g1v6` (trained on `g1-v6`), and V2X `pvrcnnpp-ros-g1v5d2` and `pvrcnnpp-ros-g1v5d3` (the seeds of `bag-pvrcnnpp-ros-g1v5x`, which the V2X pedestrian fusion now uses). The other checkpoints are 8.1 assets. New in the tree:
- engine v6: `common/bdc26/render/scene_map.py` (static scene map from the twin's own semantic tags, label-free walker sampler, map ground), `common/bdc26/render/v6.py` (size quantiles, the LUMPI vehicle size convention), map-placed structures in `render/g2.py`, and the v6 flags of both `prepare_g1.py`;
- `common/tools/s9_calibrate.py` and `s9_member_check.py`, `common/pipeline/s9_portfolio.sh` (with seed and draw bags), the `bdc_world_tilt` augmentor and the VoxelNeXt head fix in `pcdet_patches.py`;
- the S9 member folders (VoxelNeXt, Voxel R-CNN and PV-RCNN++ on `g1-v6` and `g1-v6d2`), the draw bags `bag-*-g1v6x`, and `routed-g12` (LUMPI) and `routed-g15` (V2X).
```bash
python common/tools/release_weights.py fetch --tag 9.1 --version lumpi:s9a2                # or v2x:s9a
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g12/test/reproduce_s9a2.sh
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g15/test/reproduce_s9a.sh
```
Dry run on 2026-11-02 (`$BDC_DATA/logs/s9/r91`), each script on its own GPU, but **next to the S9 training jobs** (no GPU is idle until training ends on Nov 5). Both test-frame scripts come back **EQUIVALENT** (GPU nondeterminism), not IDENTICAL:
- **LUMPI `reproduce_s9a2.sh`:** 38,471 against 38,466 boxes. 38,427 boxes are matched, with centres within 0.010 m at the 99th percentile (median 1.5e-8 m) and scores within 0.0003. All 83 unmatched boxes score below 0.3.
- **V2X `reproduce_s9a.sh`:** 38,794 against 38,824 boxes. 38,779 are matched (centres within 0.003 m at the 99th percentile). All 60 unmatched boxes score below 0.3.
- **Both:** the 50 realism frames are byte-identical and the kit check is valid (LUMPI 400.5 s and V2X 236.2 s on the loaded machine).
- **The reported maximum difference of about 78** comes from comparing boxes by position in each frame's list once the counts differ. It is not a box offset.
- **The same pattern** was seen in 8.0, where the shared-GPU attempts were EQUIVALENT and the idle-GPU runs IDENTICAL.

**Idle-GPU run on 2026-11-05** (`$BDC_DATA/logs/s9/r92`, each script alone on its GPU, twice; record [`docs/decisions/2026-11-02-s9-clean-twin-plan.md` Section 15.26](docs/decisions/2026-11-02-s9-clean-twin-plan.md)). Both scripts are again **EQUIVALENT**, and this is final:
- **LUMPI:** 58 unmatched boxes, centres within 0.015 m at the 99th percentile.
- **V2X:** 45 unmatched boxes, centres within 0.002 m at the 99th percentile.
- **Both:** no unmatched box scores above 0.3, the realism frames are byte-identical, and the kit check is valid.
- **Why not IDENTICAL.** The members that differ were inferred by the package step on GPUs shared with training (no GPU was idle on Nov 2). Inference on an idle GPU is deterministic for most of them: the two V2X runs agree in every file, but the scored zip's files carry the shared-GPU variation. VoxelNeXt `vn6_tta` also varies between idle runs. So no fresh run can rebuild these zips bit for bit.

**Published** by the entrant on 2026-11-02 ([`releases/9.1/github.json`](releases/9.1/github.json)): [release 9.1](https://github.com/karmarv/utsim2real-bdc26/releases/tag/9.1) on commit `009b1db`. `main` (e520d6c..009b1db) and the tag were pushed from the entrant's terminal, and `release_weights.py publish` uploaded the 29 assets, ending with "all assets uploaded and sizes match". The 23 asset names shared with 8.1 are byte-identical to their 8.1 assets by sha256. New: the checkpoints of LUMPI `voxelrcnn-ros-g1v6` and `voxelnext-ros-g1v6`, and of V2X `pvrcnnpp-ros-g1v5d2` and `pvrcnnpp-ros-g1v5d3`, plus the two zips. Not done yet, as for 8.0 and 8.1: the GitHub-side sha256 and the label, read from the release page in the entrant's browser, and the fresh-clone fetch check, which needs a token on this server.

## 8.1 (pre-release, 2026-10-30)

**Leaderboard** (development phase, its last day; LUMPI checked 2026-10-30, 23:13 UTC): S8.3 on LUMPI, rank 1 of 22 (next 0.5118), after S8.2. V2X is unchanged from 8.0: S8.2 and S8.3 change no V2X class, so no V2X version was built. F1: `lumpi_s8d_submission.zip` and `v2x_s8v_submission.zip`.

| Track | Version | CodaBench id | Uploaded (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S8.3 | 1022492 | 2026-10-30 23:09 | **0.5257** (0.525688) | 0.1782 | 0.9323 | **1 of 22** | [`lumpi_s8d_submission.zip`](model-lumpi-track/routed-g11d/submissions/2026-10-30_s8d/lumpi_s8d_submission.zip) (`d5bd41769788c902b6e49095236aafd6`) | [s8 last day, Section 10](docs/decisions/2026-10-29-s8-last-day-strategy.md) |
| 1 LUMPI (16684) | S8.2 | 1022399 | 2026-10-30 21:37 | **0.5254** (0.525439) | 0.1779 | 0.9323 | **1 of 22** | [`lumpi_s8c_submission.zip`](model-lumpi-track/routed-g11c/submissions/2026-10-30_s8c/lumpi_s8c_submission.zip) (`ead9da5ec4eb683e526efe4b72483dfc`) | [s8 last day, Section 9](docs/decisions/2026-10-29-s8-last-day-strategy.md) |
| 2 V2X-Real (16685) | S8 V2X U2 (as 8.0) | 1022246 | 2026-10-30 19:52 | **0.9022** (0.902153) | 0.6170 | 0.9332 | **1 of 25** | [`v2x_s8v_submission.zip`](model-v2x-track/routed-g13/submissions/2026-10-30_s8v/v2x_s8v_submission.zip) (`b9c82e3de0c37babf146549eeedabbf6`) | same |

Server records: [`codabench_1022492.json`](model-lumpi-track/routed-g11d/submissions/2026-10-30_s8d/codabench_1022492.json), [`codabench_1022399.json`](model-lumpi-track/routed-g11c/submissions/2026-10-30_s8c/codabench_1022399.json).
- **LUMPI S8.3 against S8.2 (1022399): +0.00025, as projected (+0.0002).** Person 0.1865 -> 0.1876 and Bus 0.0028 -> 0.0037, from the copies (which cannot lower AP); every other class and the realism are identical.
- **LUMPI against S8 U2 (1022250): +0.00154.** Car 0.6482 -> 0.6608 (+0.0126); every other class and the realism are identical.
- The local evidence was a pooled +0.0007 (A +0.0018, B -0.0010) and a projection of +0.00003. LUMPI Car's local splits did not predict the test result, here upward; in S7.6 they missed downward.

**Release assets.** The three zips (`s8d`, `s8c`, `s8v`) and the same 25 checkpoints as 8.0 (4.44 GB, byte-identical; S8.2 adds no checkpoint, only 12-view variants of existing ones), in [`releases/8.1/weights.json`](releases/8.1/weights.json). New in the tree:
- the `_tta12` post-processing and validation files of the 19 bag seeds;
- the 12-view bag outputs (`bag_predictions.py --tags _tta12`);
- `routed-g11c` (`s8c`), `routed-g11d` (`s8d`; S8.3, the merge only) and `routed-g14` (V2X, not built);
- `route_predictions.py` `final_copies` (copies after the sparse stage) and the `u4`/`v2x3` stages of `s8_portfolio.sh`.
```bash
python common/tools/release_weights.py fetch --tag 8.1 --version lumpi:s8d                 # or lumpi:s8c, v2x:s8v
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g11d/test/reproduce_s8d.sh
```
Verified on 2026-10-30 on an idle GPU (`$BDC_DATA/logs/s8/r80`): `reproduce_s8c.sh` rebuilds the scored zip **IDENTICAL** from these weights, with predictions at maximum difference 0.0 and the 50 realism frames byte-identical. The 12-view bag is recomputed from its six seeds (`--refresh`). `reproduce_s8v.sh` is the 8.0 dry-run (IDENTICAL). `reproduce_s8d.sh` (the same members as `s8c`, merged with the S8.3 copies) also rebuilds its scored zip **IDENTICAL**: 37,396 boxes, maximum difference 0.0, kit scorer valid in 368 s.

**Published** by the entrant on 2026-10-30 ([`releases/8.1/github.json`](releases/8.1/github.json)): [release 8.1](https://github.com/karmarv/utsim2real-bdc26/releases/tag/8.1) on commit `e5b090f`. `main` and the tag were pushed from the entrant's terminal, and `release_weights.py publish` uploaded the 28 assets, ending with "all assets uploaded and sizes match". Every checkpoint and the V2X zip equal their 8.0 assets by sha256 (26 of 26 shared names); the two LUMPI zips are new. Not done yet, as for 8.0: the GitHub-side sha256 and the label, read from the release page in the entrant's browser, and the fresh-clone fetch.

## 8.0 (pre-release, 2026-10-30)

**Leaderboard** (development phase, its last day; public leaderboards checked 2026-10-30, 20:09 UTC): S8 on both tracks, rank 1 on both. These two zips are F1 for the final phase, unless an S8.2 version (8.1) scores higher before the phase closes.

| Track | Version | CodaBench id | Uploaded (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S8 U2 | 1022250 | 2026-10-30 19:57 | **0.5239** (0.523901) | 0.1762 | 0.9323 | **1 of 22** (next 0.5118) | [`lumpi_s8b_submission.zip`](model-lumpi-track/routed-g11b/submissions/2026-10-30_s8b/lumpi_s8b_submission.zip) (`c85189b48795db4647119189f7a5a2d3`) | [s8 last day](docs/decisions/2026-10-29-s8-last-day-strategy.md) |
| 2 V2X-Real (16685) | S8 V2X U2 | 1022246 | 2026-10-30 19:52 | **0.9022** (0.902153) | 0.6170 | 0.9332 | **1 of 25** (next 0.8112) | [`v2x_s8v_submission.zip`](model-v2x-track/routed-g13/submissions/2026-10-30_s8v/v2x_s8v_submission.zip) (`b9c82e3de0c37babf146549eeedabbf6`) | same |

Server records: [`codabench_1022250.json`](model-lumpi-track/routed-g11b/submissions/2026-10-30_s8b/codabench_1022250.json), [`codabench_1022246.json`](model-v2x-track/routed-g13/submissions/2026-10-30_s8v/codabench_1022246.json) (scores from the scoring output, ranks and times from the public API).
- **LUMPI against S7.6 (1014495): +0.00106.** Person 0.1802 -> 0.1865 (+0.0063), Truck 0.0632 -> 0.0653 (+0.0021), Motorcycle +0.0003. Car, Bicycle, Bus, Van and the realism are identical.
- **V2X against S7.6 (1014682): +0.00398.** Pedestrian 0.4288 -> 0.4428 (+0.0139); vehicle, truck and the realism are identical.
- Both projections had the right sign: LUMPI +0.0011 projected, +0.00106 scored; V2X +0.0015 projected, +0.0040 scored. `s8a` (LUMPI U1, the completion alone) was built and not uploaded; `s8b` contains it.

**Release assets: everything needed to replicate the two versions.** The two submission zips and the 25 checkpoints they use (4.44 GB; LUMPI 15, V2X 10), named and mapped as in 7.0 in [`releases/8.0/weights.json`](releases/8.0/weights.json). **All 25 checkpoints are byte-identical to 7.0 assets** (same md5): S8 changes only test-time views (`flip4+yaw+z+scale`), post-processing (`test/postprocess_tta12.yaml` of the 12-view members) and the merge (floors, copies, fusions), all in git. From a fresh clone at this tag:
```bash
python common/tools/release_weights.py fetch --tag 8.0 --version lumpi:s8b                 # or v2x:s8v; md5-verified, placed under train/output/
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g11b/test/reproduce_s8b.sh             # test frames: predictions and frames against the scored zip
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g13/test/reproduce_s8v.sh                # V2X entry
```
Verified on 2026-10-30 on an idle GPU (`$BDC_DATA/logs/s8/r80`): both test-frame scripts reproduce their scored zips **IDENTICAL** from these weights. Predictions match with maximum difference 0.0 and 0 frames differing, and all 50 realism frames are byte-identical. The kit scorer is valid: LUMPI `s8b` 329 s and 32,038 boxes, V2X `s8v` 131 s and 21,354 boxes. The first attempts ran next to the S8.2 GPU jobs and came back EQUIVALENT: LUMPI differed in 9 Car boxes, from one seed of the 6-seed PV-RCNN++ bag, and V2X in all 50 frames. As in 6.0 and 7.0, bit-identity needs an idle GPU. The validation scripts (`reproduce_s8b_validation.sh`, `reproduce_s8v_validation.sh`) were not dry-run for 8.0: they repeat every member's inference on realval-A and B, several GPU-hours that S8.2 used on the last day. Their checkpoints are the ones 7.0's validation dry-run checked (EQUIVALENT), and the 12-view members' validation files are in the tree.

**Published** by the entrant on 2026-10-30 ([`releases/8.0/github.json`](releases/8.0/github.json)): [release 8.0](https://github.com/karmarv/utsim2real-bdc26/releases/tag/8.0) on commit `0441b31`. `main` and the tag were pushed from the entrant's terminal, and `release_weights.py publish` uploaded the 27 assets, ending with "all assets uploaded and sizes match". Every checkpoint's sha256 equals the sha256 GitHub showed for the same 7.0 asset (25 of 25). Not done yet: the GitHub-side sha256 of the 8.0 assets and the label, which are read from the release page in the entrant's browser, and the fresh-clone fetch (step 7).

**What 8.0 contains**
- Strategy S8 ([record](docs/decisions/2026-10-29-s8-last-day-strategy.md), [`docs/02-STRATEGY.md` Section 8.13](docs/02-STRATEGY.md#813-s8-last-day-tta-and-completion-2026-10-30)):
  - the 12-view view set (`bdc26.detect.tta`, part `scale`);
  - views in chunks of 8 and `--from-raw` in `pcdet_predict.py`;
  - a second TTA variant per member: `tune_and_eval.sh --tta-tag tta12 --reuse-raw` and `member_tag` `tta_tag`;
  - tail copies with `min_score`, and `fuse --swap-variant`;
  - `common/pipeline/s8_portfolio.sh`;
  - LUMPI `routed-g11` (U1, `s8a`, not uploaded) and `routed-g11b` (U2, `s8b`, 1022250), V2X `routed-g13` (`s8v`, 1022246);
  - the kit-time fallback that moved the Person copies to boxes scored >= 0.274.
- S8.2 (record Section 9): the pre-registered rules and their tooling are in 8.0:
  - `bag_predictions.py --tags/--variant tta12`;
  - `route_predictions.py extend`;
  - the `u3` and `v2x2` stages.

  Its runs (the 12-view seed bags) and versions (`routed-g11c`, `routed-g14`) are not, and go to 8.1.

## 7.0 (pre-release, 2026-10-27)

**Leaderboard** (development phase; public leaderboards checked 2026-10-27, 21:41 CDT): S7 on both tracks, rank 1 on both; the latest upload on each track is its S7.6 package, and those two zips are F1 for the final phase.

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S7.6 | 1014495 | 2026-10-28 00:32 | **0.5228** (0.522846) | 0.1749 | 0.9323 | **1 of 22** | [`lumpi_s7s_submission.zip`](model-lumpi-track/routed-g10/submissions/2026-10-27_s7s/lumpi_s7s_submission.zip) (`19122be039da416d98ccdf852d67532b`) | [s7 final revisions](docs/decisions/2026-10-26-s7-final-revisions.md) |
| 2 V2X-Real (16685) | S7.6 | 1014682 | 2026-10-28, between 00:53 and 02:41 (not public: a tie does not replace the listed row) | **0.8982** (0.898172) | 0.6124 | 0.9332 | 1 (tie with 1001919) | [`v2x_s7s_submission.zip`](model-v2x-track/routed-g12/submissions/2026-10-27_s7s/v2x_s7s_submission.zip) (`73518975aed78ed70f78437bf62c715b`) | same |
| 2 V2X-Real (16685) | S7 step 1 | 1001919 | 2026-10-19 02:52 | **0.8982** (0.898172) | 0.6124 | 0.9332 | **1 of 24** (the listed row) | [`v2x_s7_submission.zip`](model-v2x-track/routed-g9/submissions/2026-10-18_s7/v2x_s7_submission.zip) (`c1483d590242d4fe6b4eefff96c1619c`) | [s7 visibility rule](docs/decisions/2026-10-18-s7-visibility-rule.md) |

Server records: [`codabench_1014495.json`](model-lumpi-track/routed-g10/submissions/2026-10-27_s7s/codabench_1014495.json), [`codabench_1014682.json`](model-v2x-track/routed-g12/submissions/2026-10-27_s7s/codabench_1014682.json), [`codabench_1001919.json`](model-v2x-track/routed-g9/submissions/2026-10-18_s7/codabench_1001919.json). LUMPI against S6 (995869): Truck 0.058 -> 0.063, Car 0.652 -> 0.648, every other class and the realism identical (+0.00009). V2X: 1014682 equals 1001919 in every metric; 1001919 against S6 variant b (995877): pedestrian 0.413 -> 0.429, vehicle 0.735 -> 0.737, truck and realism identical (+0.0051).

**Release assets: everything needed to replicate the three versions.** The three submission zips and the 25 checkpoints they use (4.46 GB; LUMPI 15, V2X 10, every file exactly as used), named `<track>.<model folder>.epoch40.pth` and mapped to their repository paths and md5 in [`releases/7.0/weights.json`](releases/7.0/weights.json). Twenty checkpoints are byte-identical to 6.0 assets; new are the five LUMPI PV-RCNN++ checkpoints of the extended bag (`pvrcnnpp-ros-g1v4-s2`, `-s3`, `-s4`, `pvrcnnpp-ros-g1v4d2`, `-d3`). From a fresh clone at this tag (root README Section 6.11):
```bash
python common/tools/release_weights.py fetch --tag 7.0 --version lumpi:s7s                 # or v2x:s7s, v2x:s7; md5-verified, placed under train/output/
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g10/test/reproduce_s7s.sh              # test frames: predictions and frames against the scored zip
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g10/test/reproduce_s7s_validation.sh   # realval-A/B against the recorded scorecard (needs the real data)
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g12/test/reproduce_s7s.sh                # V2X entry; routed-g9/test/reproduce_s7.sh for 1001919
```
Verified on 2026-10-27 on idle GPUs, one job per GPU (`$BDC_DATA/logs/r70`): the three test-frame scripts reproduce their scored zips **IDENTICAL** from these weights (predictions, maximum difference 0.0; all 50 frames byte-identical; kit scorer valid: LUMPI `s7s` 284 s and 23,270 boxes, V2X `s7s` 157 s, V2X `s7` 160 s). The two validation scripts reproduce realval-A/B to four decimals: LUMPI `s7s` A 0.3881, B 0.2250, late-A 0.3583, every class within 6.2e-4 AP, 28 of 34 member files bit-identical; V2X `s7s` A 0.7340, B 0.7206, every class within 1.9e-4, 15 of 20 bit-identical (**EQUIVALENT**; the others were recorded on GPUs shared with training, as in 6.0). `v2x:s7` uses the same ten checkpoints and members as `v2x:s7s`.

**Published** by the entrant on 2026-10-28 and checked on GitHub the same day ([`releases/7.0/github.json`](releases/7.0/github.json)): [release 7.0](https://github.com/karmarv/utsim2real-bdc26/releases/tag/7.0) on commit `3eafbaf` (tag created 2026-10-28 04:52 UTC). The 28 assets were uploaded 13:10-13:14 UTC; GitHub lists 30 with its two source archives. The sha256 GitHub shows for every asset equals the sha256 of the file the dry run used (28 of 28), so the published weights and zips are the ones that reproduced. GitHub label: **Latest**, kept by the entrant on 2026-10-28 (a pre-release cannot be Latest; 6.0 carries neither label; both titles say pre-release). The fresh-clone fetch (step 7) is the entrant's: the repository is private and the server has no GitHub token.

**F1 and fallbacks for the final phase** ([`docs/02-STRATEGY.md` Section 8.8](docs/02-STRATEGY.md#88-final-phase-plan-nov-1-14)): F1 = `lumpi_s7s_submission.zip` and `v2x_s7s_submission.zip`. Fallbacks: `v2x_s7_submission.zip` (1001919, equal score, in this release) and `lumpi_s6_submission.zip` (995869, release 6.0).

**What 7.0 contains**
- Strategy S7 ([`docs/02-STRATEGY.md` Sections 8.11-8.12](docs/02-STRATEGY.md#811-s7-visibility-rule-v2x-2026-10-18)):
  - step 1, the V2X sparse-box demotion at the real annotators' visibility cut (`route_predictions.py sparse`, `bdc26.boxes.count_points_per_box`; `routed-g9`, 1001919);
  - step 2, members retrained on visibility-matched labels (`common/tools/filter_labels.py`, corpus `g1-v5m`, `routed-g10`): below the upload gate, so its checkpoints stay out of the release;
  - S7.4-S7.6, fresh generator draws (`prepare_g1.py --seed`; the default reproduces the existing corpora) in extended seed-and-draw bags (`bag-*-g1v5x`, `bag-*-g1v4x`), the bag swap (`route_predictions.py fuse --swap-to`), the pooled bound on score floors (`budget --pooled`), the final check and projection (`common/tools/s7_check.py`); V2X `routed-g11` and `routed-g12` (the entry), LUMPI `routed-g9` and `routed-g10` (the entry). No version passed the +0.003 upload gate; the entrant uploaded both S7.6 packages.
- Pipelines (`common/pipeline/`): `s7_portfolio.sh`, `s7f_portfolio.sh`, `s7g_amend.sh`; `route_predictions.py fuse --pooled-rule` and `merge --frames`.
- Rules and compliance: [`2026-10-18-rules-external-datasets.md`](docs/decisions/2026-10-18-rules-external-datasets.md) (TUMTraf-V2X and other real sets not used), [`2026-10-26-rules-compliance-audit.md`](docs/decisions/2026-10-26-rules-compliance-audit.md) (18 items, the pre-registered rules a-e, the 2026-10-27 forum-FAQ addendum and the disclosure email draft); the V2X corpus card lists every real-derived generator input.
- Documentation: workflow and compliance diagrams as built (root README Sections 2.1, 2.3 and 2.4; `docs/03-ARCHITECTURE.md` Sections 2 and 6.2; `model-lumpi-track/README.md` Section 5); the release map and the release workflow (top of this file); the release of every version in `docs/decisions/README.md` Section 6.1; model READMEs for every `routed-g*` folder.
- Findings: inside portfolios that already fuse architectures, more seeds or draws of one family add little; a score floor can cut an R40 level of the pooled frames that neither split shows; LUMPI Car failed to transfer for the second time (an observation, no rule change before the final); the in-frame order of equal predictions does not change the server score.
- Tests: 106 (`python -m pytest -q common/tests`; `test_s7.py` added; the release-manifest check covers 6.0 and 7.0).

## 6.0 (pre-release, 2026-10-17)

**Leaderboard** (development phase; public leaderboards checked 2026-10-17): both tracks have a new entry, strategy S6.

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | S6 | 995869 | 2026-10-17 14:17 | **0.5228** | 0.1748 | 0.9323 | **1 of 21** | [`lumpi_s6_submission.zip`](model-lumpi-track/routed-g8/submissions/2026-10-16_s6/lumpi_s6_submission.zip) (`02c731ecbd162a84d6eae5537856bc4a`) | [s6 variance-controlled](docs/decisions/2026-10-16-s6-variance-controlled.md) |
| 2 V2X-Real (16685) | S6 variant b | 995877 | 2026-10-17 14:23 | **0.8931** | 0.6065 | 0.9332 | **1 of 23** | [`v2x_s6b_submission.zip`](model-v2x-track/routed-g8b/submissions/2026-10-16_s6b/v2x_s6b_submission.zip) (`00a80bb32c5019b6d9913555efebc6b6`) | same |

Server records: [`codabench_995869.json`](model-lumpi-track/routed-g8/submissions/2026-10-16_s6/codabench_995869.json), [`codabench_995877.json`](model-v2x-track/routed-g8b/submissions/2026-10-16_s6b/codabench_995877.json). LUMPI against R5: Van 0.117 -> 0.141, every other class and the realism identical. V2X against R5: vehicle 0.721 -> 0.735, truck 0.657 -> 0.671, pedestrian and realism identical.

**Release assets: everything needed to replicate the two entries.** The two submission zips and the 21 checkpoints they use (3.5 GB; LUMPI 11, V2X 10, every file exactly as used, md5 as in the decision record), named `<track>.<model folder>.epoch40.pth` and mapped to their repository paths in [`releases/6.0/weights.json`](releases/6.0/weights.json). From a fresh clone at this tag (root README Section 6.11):
```bash
python common/tools/release_weights.py fetch --tag 6.0 --version lumpi:s6      # or v2x:s6b; md5-verified, placed under train/output/
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g8/test/reproduce_s6.sh    # test frames: predictions and frames against the scored zip
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g8/test/reproduce_s6_validation.sh   # realval-A/B against the recorded scorecard (needs the real data)
```
Verified on 2026-10-17 on idle GPUs (`$BDC_DATA/logs/s6close`): the test-frame scripts reproduce both scored zips **IDENTICAL** (predictions, maximum difference 0.0; all 50 frames byte-identical, from the corpus and from the committed zip); the validation scripts reproduce realval-A/B to four decimals on both tracks (every class within 4e-4 AP: EQUIVALENT; 41 of 48 member files bit-identical, the others recorded on GPUs shared with training).

**Published** 2026-10-18 (assets uploaded 14:43-14:46 UTC; [`releases/6.0/github.json`](releases/6.0/github.json)): the sha256 GitHub shows for each of the 23 assets equals the local file (checked 2026-10-28); GitHub label: none.

**Fallback for the first final-phase submission:** the R5 zips of release 5.2.

**What 6.0 contains**
- Strategy S6 ([`docs/02-STRATEGY.md` Sections 8.6-8.6.2](docs/02-STRATEGY.md#86-s6-variance-controlled-final-portfolio-re-planned-2026-10-15)): seed bags (`common/tools/bag_predictions.py`, model folders `bag-*`), the LUMPI Van judge (`route_predictions.py --judge`, `scorecard.py --judge`), class freezing (`freeze_classes.py`), the per-class score blend as a tool (`score_blend.py`), the realism pool from a whole corpus (`select_realism_frames.py --split train+val`, held-out scores in the packaged order).
- Close-out: the pooled rule as the gate from 6.0 on (`docs/decisions/README.md` Section 3.2; `common/tools/pooled_check.py`, the pooled condition on the final predictions); V2X variant b (`routed-g8b`, the entry) and the LUMPI check of the same rule (`routed-g8b`, Car rejected on the pooled frames); `common/pipeline/finish_portfolio.sh`, `s6b_lumpi.sh`, `gpu_queue.sh` (one reproduction job per GPU).
- Background pipeline (`common/pipeline/`, root README Section 6.10): detached queues for training and post-processing, per-track portfolio orchestrators, `status.sh`, events log; TensorBoard with realval learning curves (`tb_realval.py`) for every member since S3.
- Reproduction (root README Section 6.11, `docs/decisions/README.md` Section 6.1): `reproduce_submission.py` (weights inventory with md5 and release-asset names, re-merge check, `test/reproduce_<tag>.sh` per scored version: portable, frames from the corpus or the scored zip, final comparison of predictions and frames, matched-box equivalence check), `reproduce_validation.py` (`test/reproduce_<tag>_validation.sh`: realval-A/B from the weights against the recorded scorecard), `package_submission.py --syn-zip / --reproduction`; `release_weights.py` and `_github.py` (release assets: collect, publish, fetch, verify; GitHub REST, no CLI needed); a Reproduce section in every decision record since S1.
- Members: LUMPI `voxelrcnn-ros-g1v4-s3/-s4`, `pvrcnnpp-ros-g1v4-s3/-s4`; V2X `voxelrcnn-ros-g1v5-s2/-s3`, `pvrcnnpp-ros-g1v5-s2/-s3`; six bags; models `routed-g8` (both tracks) and `routed-g8b` (V2X variant b, the entry; LUMPI close-out).
- Findings: every seed bag at or above its best seed, but on realval-B none above R5's three-architecture fusions by +0.01; on the leaderboard the bag fusions gained +0.014 on V2X vehicle and truck (the +0.01-on-B requirement was too strict; the pooled condition had the signs right); the LUMPI Van judge transferred at 0.45 x its realval-A gain; LUMPI Car fusion gains vanish on the pooled frames for the third time; realism frame changes below about 0.004 are inside the scorer's subsample noise; inference is bit-identical on an idle GPU.
- Environment: `tensorboard==2.17.1` pinned in `requirements.txt` and the lock.
- Tests: 91 (`python -m pytest -q common/tests`; `test_environment.py` included).

## 5.2 (pre-release, 2026-10-15)

**Leaderboard** (development phase; public leaderboards checked 2026-10-15): both tracks have a new entry, strategy R5.

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | R5 | 990245 | 2026-10-15 13:50 | **0.5198** | 0.1714 | 0.9323 | **1 of 21** | [`lumpi_r5_submission.zip`](model-lumpi-track/routed-g7/submissions/2026-10-14_r5/lumpi_r5_submission.zip) (`ae3612bfa0607f3f0773702acd985fd0`) | [r5 realism-led](docs/decisions/2026-10-14-r5-realism-led.md) |
| 2 V2X-Real (16685) | R5 | 990255 | 2026-10-15 13:53 | **0.8852** | 0.5972 | **0.9332** | **1 of 20** | [`v2x_r5_submission.zip`](model-v2x-track/routed-g7/submissions/2026-10-14_r5/v2x_r5_submission.zip) (`0d339f79a21059a8c97211d4d7c15533`) | same |

Server records: [`codabench_990245.json`](model-lumpi-track/routed-g7/submissions/2026-10-14_r5/codabench_990245.json), [`codabench_990255.json`](model-v2x-track/routed-g7/submissions/2026-10-14_r5/codabench_990255.json). LUMPI against R3: Person 0.157 -> 0.180, every other class and the realism identical (uploaded below the upload gate by the entrant's call). V2X against R3: pedestrian +0.011 (walker tail copies), vehicle +0.002, realism +0.0065 (EMD 1.345 -> 1.182, FPD 0.733 -> 1.468).

**Fallback for the first final-phase submission:** the R3 zips of release 5.1, re-verified on 2026-10-14 (re-merged from the saved member predictions with the committed `routed-g6/model.yaml` and repackaged: `predictions.json` and all 50 frames byte-identical on both tracks; only the declaration date differs).

**What 5.2 contains**
- Rules: [`docs/decisions/2026-10-14-rules-compliance-review.md`](docs/decisions/2026-10-14-rules-compliance-review.md) (every method against the Rules, Terms and declaration as published on 2026-10-14) and the updated operating interpretation in `docs/01-CHALLENGE-FACTS.md` Section 3.1.
- Strategy R5 ([`docs/02-STRATEGY.md` Sections 8.9 and 8.9.1](docs/02-STRATEGY.md#89-r5-realism-led-refinement-after-r3-review-and-plan-2026-10-14)): iterative density-prior fitting (`fit_density_prior.py --base`, `density.fit(base=...)`); EMD-targeted frame selection (`select_realism_frames.py --objective fpd+emd`); walker tail copies (`route_predictions.py tail`, `apply_tail_copies`; the final gate treats them as class configuration); the late-A rank for LUMPI Person (`fuse --late-rank Person --gate-top 3`); seeded training (`pcdet_train.py --seed`).
- Data: V2X `gen/density_prior_v1.npz` and corpus `g1-v5`; LUMPI `gen/density_prior_v2.npz` and corpus `g1-v5` (built, not adopted).
- Members: `voxelrcnn-ros-g1v4-s2`, `pvrcnnpp-ros-g1v4-s2` on both tracks; V2X `pointpillars-g1v5`, `voxelrcnn-ros-g1v5`, `pvrcnnpp-ros-g1v5`; models `routed-g7`.
- Findings: residual realism is background (EMD attributed point by point), a density prior must be fitted to the generator it corrects (iteratively when cells saturate), seed variance is as large as many strategy steps, walker tail copies transfer as constructed (V2X pedestrian 1.07 x), the late-A Person rule transferred at 1.6 x, the V2X vehicle fusion of new members at 0.2 x, and V2X realism at 0.58 x (EMD transferred, FPD rose on the server); a test-window-like proxy (class-count reweighting) fails its backtest; LUMPI Measurement4 Person labels drift from manual to automatic boxes toward the test window.
- Files: `lumpi_r5_submission.zip` and `v2x_r5_submission.zip` (the scored upload copies) with `manifest.json`, `synthetic_ids.txt` and `codabench_<id>.json` under `model-<track>/routed-g7/submissions/2026-10-14_r5/`.
- Tests: 74 (`python -m pytest -q common/tests`).

## 5.1 (pre-release, 2026-10-13)

**Leaderboard** (development phase; public leaderboards checked 2026-10-14): both tracks have a new entry, strategy R3.

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 1 LUMPI (16684) | R3 | 986489 | 2026-10-14 05:38 | **0.5169** | 0.1680 | **0.9323** | **1 of 21** | [`lumpi_r3_submission.zip`](model-lumpi-track/routed-g6/submissions/2026-10-12_r3/lumpi_r3_submission.zip) (`8dbce7a9356ae490c5b948218588f86b`) | [r3 g2-lite](docs/decisions/2026-10-12-r3-g2-lite.md) |
| 2 V2X-Real (16685) | R3 | 986496 | 2026-10-14 05:44 | **0.8789** | 0.5929 | 0.9268 | **1 of 19** | [`v2x_r3_submission.zip`](model-v2x-track/routed-g6/submissions/2026-10-12_r3/v2x_r3_submission.zip) (`510eb8f9a775539c87ce323f9b13bc1b`) | same |

Server records: [`codabench_986489.json`](model-lumpi-track/routed-g6/submissions/2026-10-12_r3/codabench_986489.json), [`codabench_986496.json`](model-v2x-track/routed-g6/submissions/2026-10-12_r3/codabench_986496.json). LUMPI against S4: realism 0.891 -> 0.932, Truck +0.025, Bus +0.003, Bicycle -0.056 (mAP -0.004; diagnosed in [`docs/02-STRATEGY.md` 8.7.2](docs/02-STRATEGY.md#872-r3-results-2026-10-11-to-2026-10-13)). V2X against S5: pedestrian +0.012, realism +0.0065.

**What 5.1 contains**
- Strategy R3, *Engine G2-lite* ([`docs/02-STRATEGY.md` Sections 8.7.1 and 8.7.2](docs/02-STRATEGY.md#871-r3-engine-g2-lite-review-and-plan-2026-10-11); [decision record](docs/decisions/2026-10-12-r3-g2-lite.md)): `common/bdc26/render/g2.py` (mesh primitives, hull exemplar bank, two-wheelers with riders, static clutter, ray-consistent Open3D insertion with the candidate-sensor occlusion rule, per-class range-ramped ray dropout, shrink-to-fit real sizes, `G2Pass`), the `post_inserter` hook and the reference sampling rate in `common/bdc26/prep.py` and `common/bdc26/density.py`, `--g2` in both `prepare_g1.py`; corpora `g1-v4` on both tracks.
- Members `pointpillars-g1v4`, `voxelrcnn-ros-g1v4`, `pvrcnnpp-ros-g1v4` on both tracks and `pointpillars-ros-g1v4` on LUMPI (plain and TTA; the uncapped V2X Voxel R-CNN run kept as `run0_rostail`); models `routed-g6` with realism frames from `g1-v4`.
- Protocol and tools: the pooled A+B condition (`scorecard.pooled_gate`, `route_predictions.py --pooled`), the final gate on the final predictions (`route_predictions.py gate --vs <entry>`), the size cap of object scaling (`CLASS_MAX`), the unclipped upload estimate (`combined_estimate(clip=False)`).
- **One environment:** Open3D 0.19.0 moved into `.venv_ut` (no other package changed; the separate conda environment `bdc-sim` and its script are retired); `requirements.txt` pins every directly imported package exactly, the new `requirements-lock.txt` pins the full set, `setup_venv_ut.sh` installs with the lock as constraints, and `common/tests/test_environment.py` fails on any drift. A `g1-v4` rebuild in `.venv_ut` is bit-identical to the corpus built in `bdc-sim` (8 frames per track). Fix: a template `.gitignore` rule (`env/`) had kept `common/env/` (`activate.sh`, `bdc26.env`, `setup_venv_ut.sh`, `setup_bdc_train.sh`) out of git; the folder is now committed.
- Findings: point density compared in the same place (UT Cars 0.44x -> 0.83x real, two-wheelers 0.25-0.52x -> 0.90-1.04x); static walker false positives halve in every LUMPI two-stage member; realism LUMPI 0.891 -> 0.932 on the server (the gap to the hidden reference shrank from 0.015 to 0.002), V2X 0.920 -> 0.927; real sizes need a ceiling and per-class routing; LUMPI Bicycle failed to transfer twice (S5, R3) and is a known exception to the local gates.
- Tests: 70 (`python -m pytest -q common/tests`, all in `.venv_ut`).

## 5.0 (pre-release, 2026-10-11)

**Leaderboard** (development phase; public leaderboards checked 2026-10-11): V2X has a new entry; the LUMPI entry stays the 4.0 one (975871).

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 2 V2X-Real (16685) | S5 | 978945 | 2026-10-11 20:20 | **0.8730** | 0.5890 | 0.9203 | **1 of 19** | [`v2x_s5_submission.zip`](model-v2x-track/routed-g5/submissions/2026-10-11_s5/v2x_s5_submission.zip) (`e5b258652c9aa0f783f3cdfbd614d687`) | [s5 object scaling](docs/decisions/2026-10-11-s5-object-scaling.md) |
| 1 LUMPI (16684) | S5 | 978931 | 2026-10-11 20:12 | 0.5039 | 0.1720 | 0.8912 | not listed (0.00007 below the S4 entry, which stays rank 1 of 18) | [`lumpi_s5_submission.zip`](model-lumpi-track/routed-g5/submissions/2026-10-11_s5/lumpi_s5_submission.zip) (`9f2c925c3976679b5b2038bfde5f7566`) | same |

Server records: [`codabench_978945.json`](model-v2x-track/routed-g5/submissions/2026-10-11_s5/codabench_978945.json), [`codabench_978931.json`](model-lumpi-track/routed-g5/submissions/2026-10-11_s5/codabench_978931.json). V2X against S4: pedestrian +0.046, truck +0.029, vehicle +0.011. LUMPI against S4: Truck +0.038, Bicycle -0.030, Car -0.010 (confirmation failed; diagnosed in [`docs/02-STRATEGY.md` 8.5.1](docs/02-STRATEGY.md#851-results-2026-10-11)).

**What 5.0 contains**
- Strategy S5, *Geometry-Invariant Inputs* ([`docs/02-STRATEGY.md` Sections 8.5 and 8.5.1](docs/02-STRATEGY.md#851-results-2026-10-11); [decision record](docs/decisions/2026-10-11-s5-object-scaling.md)): the review (voxel occupancy: GBlobs as published degenerates at our density; real vs synthetic label sizes: bicycles and trucks are the gap); `common/bdc26/detect/gblobs_vfe.py` (`GBlobsVFE` ported with its BSD-3 notice, `GBlobsCellVFE`) and `common/bdc26/detect/augment.py` (class-wise object scaling `bdc_object_scaling`); runs `voxelrcnn-gblobs-g1v3`, `voxelrcnn-ros-g1v3`, `pvrcnnpp-ros-g1v3`, `pointpillars-ros-g1v3` on both tracks (plain and TTA); models `routed-g5`.
- Findings: object scaling lifts every anchor-free and two-stage member and hurts the anchor-based V2X pillars; GBlobs loses as a member and helps inside fusions; the LUMPI test window answers the size-augmented Bicycle members with false positives no local split shows; from R3 on the class gate also requires a pooled A+B gain (agrees with the leaderboard on 16 of the 17 class changes of S3-S5).
- Tests: 56 (`python -m pytest -q common/tests`).

## 4.0 (pre-release, 2026-10-11)

**Leaderboard entries** (development phase; public leaderboards checked 2026-10-11): **rank 1 on both tracks.**

| Track | Version | CodaBench id | Scored (UTC) | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 2 V2X-Real (16685) | S4 | 975938 | 2026-10-11 00:16 | **0.8485** | 0.5605 | 0.9203 | **1 of 19** | [`v2x_s4_submission.zip`](model-v2x-track/routed-g4/submissions/2026-10-10_s4/v2x_s4_submission.zip) (`29c8f7a9887d1443cd7f23289ecfc8b1`) | [s4 two-stage](docs/decisions/2026-10-10-s4-two-stage.md) |
| 1 LUMPI (16684) | S4 | 975871 | 2026-10-10 23:50 | **0.5040** | 0.1721 | 0.8912 | **1 of 18** | [`lumpi_s4_submission.zip`](model-lumpi-track/routed-g4/submissions/2026-10-10_s4/lumpi_s4_submission.zip) (`ce3dc93c3f7defd7e0ca74bd0efc702a`) | same |

Per-class AP, realism terms and the scoring logs: [`codabench_975938.json`](model-v2x-track/routed-g4/submissions/2026-10-10_s4/codabench_975938.json), [`codabench_975871.json`](model-lumpi-track/routed-g4/submissions/2026-10-10_s4/codabench_975871.json). Against the S3 entries: V2X 0.8381 -> 0.8485 (vehicle +0.027, truck +0.010, pedestrian identical); LUMPI 0.5015 (S3 log; 974348 was never listed) -> 0.5040 (Bicycle 0.224 -> 0.244, every other class identical). The LUMPI package was below its upload gate (estimate +0.003) and uploaded by the entrant's call. Field on 2026-10-11: LUMPI second 0.4784, V2X runner-up 0.6616.

**What 4.0 contains**
- Strategy S4, *Two-Stage Refinement* ([`docs/02-STRATEGY.md` Sections 8.4 and 8.4.1](docs/02-STRATEGY.md#841-results-2026-10-10); [decision record](docs/decisions/2026-10-10-s4-two-stage.md)): the review of the S3 losses (AP-loss decomposition and near-miss analysis, `bdc26.diagnostics.ap_loss_decomposition`, now in every scorecard) and the revised plan; members `voxelrcnn-g1v3` and `pvrcnnpp-g1v3` on both tracks (stage 1 = the S2 CenterPoint; plain and TTA variants); a per-class two-stage score blend (`common/bdc26/detect/pcdet_patches.py`, `pcdet_predict.py --score-blend`); `route_predictions.py fuse --max-members 3` with incumbent-aware selection; models `routed-g4`.
- Findings: refinement halves the vehicle localization loss (3D@0.7 on the V2X leaderboard 0.0755 -> 0.1118) but leaves walker localization unchanged; the leaderboard gain had the right sign at all five uploads with a local change but was 0.25-1.9 x any local gain, so projections use 0.6 x the mean of the realval-A and B gains.
- Tests: 54 (`python -m pytest -q common/tests`).

## 3.0 (pre-release, 2026-10-10)

**Leaderboard entries** (development phase; public leaderboards checked 2026-10-10):

| Track | Version | CodaBench id | Scored | Combined | 3D mAP@0.5 | Realism R | Rank | Submission file (md5) | Decision record |
|---|---|---|---|---|---|---|---|---|---|
| 2 V2X-Real (16685) | S3 | 974400 | 2026-10-10 11:18 UTC (06:18 CDT) | **0.8381** | 0.5483 | 0.9203 | **1 of 19** | [`v2x_s3_submission.zip`](model-v2x-track/routed-g3/submissions/2026-10-09_s3/v2x_s3_submission.zip) (`5e46f9450feb7846455c4b8428483641`) | [s3 fused portfolio](docs/decisions/2026-10-09-s3-fused-portfolio.md) |
| 1 LUMPI (16684) | S3 | 974348 | 2026-10-10 05:48 CDT; scorer log DONE, CodaBench status Running afterwards | **0.5015** (log) | 0.1692 | 0.8912 | not listed yet (would lead: 0.4784); listed LUMPI entry 965614 (S1, rank 2) | [`lumpi_s3_submission.zip`](model-lumpi-track/routed-g3/submissions/2026-10-09_s3/lumpi_s3_submission.zip) (`9133dd7d9d8b377ec9228b79b75065a0`) | same |

Per-class AP, realism terms and the scoring logs: [`codabench_974400.json`](model-v2x-track/routed-g3/submissions/2026-10-09_s3/codabench_974400.json), [`codabench_974348.json`](model-lumpi-track/routed-g3/submissions/2026-10-09_s3/codabench_974348.json). Against the previous entries: V2X 0.7855 -> 0.8381 (vehicle +0.076, pedestrian +0.064, truck +0.044); LUMPI 0.4728 -> 0.5015 (Person +0.040, Car +0.019, Bicycle 0.053 -> 0.224). Realism is identical (same 50 frames): every change is detection. Field on 2026-10-10: LUMPI leader 0.4784, V2X runner-up 0.6616.

**What 3.0 contains**
- Strategy S3, *Fused Portfolio with TTA* ([`docs/02-STRATEGY.md` Section 8.3.1](docs/02-STRATEGY.md#831-results-2026-10-09); [decision record](docs/decisions/2026-10-09-s3-fused-portfolio.md)), built on the S2 members without new training: 8-view test-time augmentation (`common/bdc26/detect/tta.py`: flips, yaw +/-5 deg, z +/-0.25 m) and rotated weighted box fusion (`common/bdc26/detect/fusion.py`); `pcdet_predict.py --tta`; `tune_and_eval.sh --tta` in every member folder (each TTA variant tunes its own `test/postprocess_tta.yaml`); `route_predictions.py` with TTA members, `fuse` (per-class pairs of two checkpoints, class gate, A-only selection-bias check) and `budget` (per-class score floors costing at most 0.002 AP, exact from truncated match flags); models `routed-g3` on both tracks.
- Real validation: V2X realval-A / B 0.585 / 0.537 -> 0.661 / 0.664 (BEV-3D gap on B 0.129 -> 0.062); LUMPI 0.272 / 0.170 -> 0.301 / 0.184 (late-A 0.271 -> 0.298). Upload gate passed on both tracks; kit scorer 74 s (10,671 boxes) and 181 s (17,193 boxes).
- Transfer finding: leaderboard levels follow realval-B (0.83-0.92 x B), but the S3 gains were 0.80 (V2X) and 0.81 (LUMPI) x the realval-A gain against 0.48 and 1.89 x the B gain; the scorecard protocol adds a leaderboard projection (previous leaderboard mAP + 0.8 x the A gain), the gates stay on B.
- Scorecard: static false-positive share at a fixed score and ranked above the median true-positive score (fusion cut the ranked static walker boxes 6.2 -> 1.8 per frame on V2X, 9.7 -> 4.1 on LUMPI); registry rows of TTA runs carry strategy S3.
- Submission files: the S3 upload copies above, and the checked S2 candidate [`lumpi_s2_submission.zip`](model-lumpi-track/routed-g2/submissions/2026-10-09_s2/lumpi_s2_submission.zip) (md5 `3d972c963a5949fcdd87d85c5a8e30bc`, never uploaded) for traceability. Upload copies are tracked from this release on.
- Tests: 52 (`python -m pytest -q common/tests`).

## 2.0 (pre-release, 2026-10-09)

**Leaderboard entries:** unchanged from 1.0 (LUMPI 965614, S1, combined 0.4728, rank 2 of 18; V2X 972563, S1+C1, combined 0.7855, rank 1 of 19). Their files are the 1.0 files above. No S2 version passed the upload gate, so 2.0 adds no entry file; the checked LUMPI S2 candidate `model-lumpi-track/routed-g2/submissions/2026-10-09_s2/lumpi_s2_submission.zip` was kept local in 2.0 and is committed in 3.0 for traceability (checked, never uploaded).

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

0.1 (S1 first submission, 2026-10-06; zips as release assets), 0.2 (documentation of the strategy routes). 1.0 to 5.0 are described above.
