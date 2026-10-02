# 2026-09-30 Real-data download under the entrant's instruction

**Context.** The plan gated every real-data download behind `--accept-licence` until legal sign-off (LUMPI: CC BY-NC 3.0; V2X-Real: UCLA Academic licence, dataset "All Rights Reserved"). On 2026-09-30 the entrant instructed: "Lets download all the data to a location, prepare it and setup the first model training". The real-data scripts were therefore run with `--accept-licence`, on the entrant's authority.

**What was downloaded** (all under `$BDC_DATA`, outside git):
- LUMPI: `meta.json`, `HD_map/`, Label.csv of Measurements 4-6 (streamed through `ForbiddenGuard`: 75,761 Measurement4 rows of the blocked window 6400-8199 were dropped before writing; nothing of the window is on disk), lidar frames Measurement4 0-6399 every 5th (1,280), Measurement5 every 20th (378), Measurement6 every 25th (489).
- V2X-Real (Lidar-64 release, infrastructure agent -1 only): point clouds of the test and val splits (1,970) and of train1-4 (5,772). **No V2X label file** has been extracted: the V2X guard refuses all real labels until the starting kit's `forbidden_frames.txt` and the scenario-index mapping are resolved (`data-v2x-track/resolve_test_ids.py`).

**How it is used** (every access logged in `<track>/real/access_log.csv`):
- LUMPI realval-A (1,280 Measurement4 frames) and realval-B (867 Measurement5-6 frames) for validation and post-processing selection only; never for training.
- LUMPI sensor metadata (poses, beam tables) and legal Person label statistics for the G1 generator; legal unlabeled frames for the density prior (`2026-09-30-g1-generator.md`).
- V2X (after the kit was ingested on 2026-10-02 and `resolve_test_ids.py` resolved the guard): labels of guard-allowed frames only (4,853 of 7,742 agent -1 frames); realval-v1 A/B (688 / 298 frames) and 5 realism proxies; legal walker rows for the G1 placement prior (`gen/walker_prior_v1.npz`); 23 unlabeled frames for the OS1-64 beam table (`gen/os1_64_calib_v1.npz`).

**Decision.** Keep the download; record it here and in the challenge report. The licence question for a corporate researcher (Hitachi legal, `07-LITERATURE.md` Section 4) remains open and is the entrant's to close; if the answer is negative, delete `$BDC_DATA/*/real/` and every dataset derived from it (realval-*, realism-proxy-*, gen/person_prior_m4.npz, gen/density_prior_*.npz, gen/walker_prior_v1.npz, gen/os1_64_calib_v1.npz, and the G1 corpora built from them) and retrain without them.

**Consequences.** The track data guides (`data-lumpi-track/README.md`, `data-v2x-track/README.md`) list the files and versions. Both starting kits were ingested on 2026-10-02 (forbidden lists, test frames, official scorer; our scorers match it bit-for-bit, `common/tests/test_official_parity.py`).
