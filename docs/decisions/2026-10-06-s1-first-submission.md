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

**Reproduce (weights and test run).** Generated on 2026-10-15 by `common/tools/reproduce_submission.py`, which also wrote each `test/reproduce_<tag>.sh`. The script runs the test-frame inference of every used member from the checkpoint listed (checkpoints are not in git; their md5s are in `validation/results/reproduce_<tag>.json`), merges with the committed `model.yaml`, compares with the scored zip, repackages the same 50 frames and runs the official kit scorer. It uses the members' current post-processing files: for the exact files of the time, check out release tag 1.0 (the S1 code is also at 0.1) first; the compare step reports any difference. Checked on 2026-10-15: the saved member predictions re-merge to the scored predictions exactly for every upload, and S1 LUMPI re-run from its checkpoints gives identical boxes and frames.

**Reproduce (LUMPI, `model-lumpi-track/routed-g1`, tag `first`).** Scored zip `model-lumpi-track/routed-g1/submissions/2026-10-02_first/submission_lumpi.zip` (md5 `ea2c76393d6f8868762d6bac1ac03fa8`, CodaBench 965614); realism frames `pcdet/g1-v2` listed in `model-lumpi-track/routed-g1/submissions/2026-10-02_first/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (17095 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `g1` | `model-lumpi-track/pointpillars-g1` | `model-lumpi-track/pointpillars-g1/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `16e68b8b9142` | 6.0: `lumpi.pointpillars-g1.epoch40.pth` | - | `model-lumpi-track/pointpillars-g1/test/postprocess.yaml` |
| `g1v3` | `model-lumpi-track/pointpillars-g1v3` | `model-lumpi-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `e403acdc3ae3` | 6.0: `lumpi.pointpillars-g1v3.epoch40.pth` | - | `model-lumpi-track/pointpillars-g1v3/test/postprocess.yaml` |

```bash
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g1/test/reproduce_first.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-lumpi-track/routed-g1/test/reproduce_first_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-lumpi-track/routed-g1 --tag first   # quick check: re-merge the saved member predictions
```

**Reproduce (V2X, `model-v2x-track/routed-g1`, tag `first`).** Scored zip `model-v2x-track/routed-g1/submissions/2026-10-02_first/submission.zip` (md5 `5343da990d5cdd1f34df379433479e2a`, CodaBench 965633); realism frames `pcdet/g1-v3` listed in `model-v2x-track/routed-g1/submissions/2026-10-02_first/synthetic_ids.txt`. Re-merge of the saved member predictions: identical (18728 boxes).

| Member | Model folder | Weights (epoch 40) | md5 | Release asset | TTA | Post-processing |
|---|---|---|---|---|---|---|
| `g1v2` | `model-v2x-track/pointpillars-g1v2` | `model-v2x-track/pointpillars-g1v2/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `7c3e9a1c074a` | - | - | `model-v2x-track/pointpillars-g1v2/test/postprocess.yaml` |
| `g1v3` | `model-v2x-track/pointpillars-g1v3` | `model-v2x-track/pointpillars-g1v3/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `b330667c2981` | - | - | `model-v2x-track/pointpillars-g1v3/test/postprocess.yaml` |
| `ut` | `model-v2x-track/pointpillars-ut` | `model-v2x-track/pointpillars-ut/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth` | `2081ca05e332` | - | - | `model-v2x-track/pointpillars-ut/test/postprocess.yaml` |

```bash
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g1/test/reproduce_first.sh     # inference with these weights, merge, compare, repackage, kit check
CUDA_VISIBLE_DEVICES=0 bash model-v2x-track/routed-g1/test/reproduce_first_validation.sh   # realval-A/B from the weights against the recorded scorecard
python common/tools/reproduce_submission.py model-v2x-track/routed-g1 --tag first   # quick check: re-merge the saved member predictions
```
