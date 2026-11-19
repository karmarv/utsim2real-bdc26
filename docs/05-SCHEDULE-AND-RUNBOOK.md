# 05. Schedule and runbook (Sep 30 to Nov 15, 2026)

> Day 0 is Wed Sep 30. Dev phase closes **Fri Oct 30, 17:00 PDT / 19:00 CDT**. The final phase runs Nov 1-14 with **1 submission per day** and closes **Sat Nov 14, 16:00 PST / 18:00 CST**. Module IDs refer to `04-IMPLEMENTATION-GUIDE.md`; gates refer to `02-STRATEGY.md` Section 4.
> Both tracks run in parallel on shared code. Where a day lists two tracks, do V2X first (smaller data, faster loop), then port to LUMPI.

---

## 1. Calendar

**Status 2026-10-27:** S7 is the entry on both tracks, rank 1 on both, and the latest uploads are the S7.6 packages (LUMPI 1014495, 0.5228; V2X 1014682, 0.8982, identical to 1001919); they are F1 for the final phase. Status 2026-10-17: S6 was the entry on both tracks (LUMPI 995869, 0.5228; V2X 995877, 0.8931; before: R5 990245 0.5198 and 990255 0.8852); the register of every upload is [`decisions/README.md` Section 2](decisions/README.md#2-submission-register). Status 2026-10-09: S1 on LUMPI (965614, 0.4728, rank 2 since Oct 7) and S1+C1 on V2X (972563, 0.7855, rank 1). **The calendar of record from Oct 9 to Nov 14, with status, is [`decisions/README.md` Section 5](decisions/README.md#5-calendar-and-compute-plan)** (S2-S5 with one gate and one upload each, LUMPI realism in parallel, freeze Oct 25); the Week 2-4 tables below are the original plan, kept for reference.

**Status 2026-10-02 (D2): ahead of the calendar below.** Done: kits ingested and the scorers matched bit-for-bit to the official `scoring_program` (M3); real data and both real validation sets (M5.1); LUMPI class report, sensor metadata, V2X OS1-64 beam table and walker prior (M5.2-M5.3); realism proxies (M5.4); procedural walkers and engine G1 on both tracks (M7.1, M8; Gate C passed locally: LUMPI Person 0 -> 0.34 on realval-A); LUMPI density calibration (realism 0.59 -> 0.90); per-class post-processing and routing (M11 partial); both submissions packaged and dry-run tested. Not yet done: the first development uploads (Gate A on the leaderboard: the entrant uploads), the organizer email, M6 ray-drop model, G2 (M9), the architecture sweep (M10), TTA/WBF. Re-plan from D3: development uploads and confirmation of the local estimates (D3-D4), then Week 3's M10 sweep and G2 move forward by one week, leaving Week 4 for ensembles and the final-phase plan.

### Week 1: close the loop (Sep 30 - Oct 6)

| Day | Date | Work | Output |
|---|---|---|---|
| D0 | Wed Sep 30 | **Done:** repo restructured (`common/`, `data-<track>/`, `model-<track>/`); `bdc-train` built; UT-LUMPI and UT-V2X downloaded and verified; baseline `pointpillars-ut` configured and smoke-tested on both tracks. **Still to do today:** download both starting kits; email the organizer questions (`01` S10); ask legal about the real-data licences; ask the other GPU user / admin for a reservation | Kits on disk, email sent |
| D1 | Thu Oct 1 | `ingest_kit.py` (both tracks); read `local_eval.py`, record its details in `01` S4; **M3** parity test; `prepare_ut.py --name ut-v1` (both tracks); start V2X `pointpillars-ut` training (GPUs 4-7) | `kit_report.json`; parity confirmed; V2X training running |
| D2 | Fri Oct 2 | **M2** frame and density checks against `kit_report.json`; start LUMPI `pointpillars-ut` (GPUs 0-3); if licences are cleared: `fetch_real.py` (LUMPI `--meta --labels --lidar`; V2X `--points`) and `resolve_test_ids.py` | LUMPI training running; guard mapping |
| D3 | Sat Oct 3 | V2X: evaluate, `test/predict.sh`, `package_submission.py`, upload, `--record` | **Gate A** (V2X) |
| D4 | Sun Oct 4 | LUMPI: same (0.78x actor fix is in `ut-v1`); V2X `fetch_real.py --labels`; **M5.1** `prepare_realval.py` (both tracks) | Gate A (LUMPI); two real val sets |
| D5 | Mon Oct 5 | **M5.2** label statistics + **M5.3** beam tables and pose fits (V2X first) | Stats report, fitted sensor YAMLs |
| D6 | Tue Oct 6 | **M5.4** realism proxy + real-vs-real floor; score UT frames on the proxy; baselines evaluated on real val | Proxy and floor numbers |

### Week 2: missing classes and the sensor model (Oct 7 - Oct 13)

| Day | Date | Work | Output |
|---|---|---|---|
| D7 | Wed Oct 7 | **M7.1** procedural pedestrians and cyclists; **M7.3** label conventions fitted to real stats | **Gate B** (real val live) |
| D8 | Thu Oct 8 | **M6** sensor model + raycaster (beam table, pose, noise, blind zone); unit tests against real ring geometry | Raycaster passes tests |
| D9 | Fri Oct 9 | **M8** engine G1: range-image insertion of VRUs into UT-V2X; corpus G1-v2x-v1 (10k frames) | G1 V2X corpus |
| D10 | Sat Oct 10 | Train on UT + G1-v2x-v1; evaluate on real val; submit V2X. Start G1 for LUMPI (per-sensor insertion) | V2X pedestrian AP measured |
| D11 | Sun Oct 11 | G1-lumpi-v1; train; evaluate; submit LUMPI | LUMPI Person/Bicycle AP measured |
| D12 | Mon Oct 12 | Iterate conventions and VRU placement on real val | **Gate C** (VRUs work) |
| D13 | Tue Oct 13 | **M6.4** ray-drop model fitted to real (per beam x range x incidence); **M9.1** static scene from UT accumulation | Drop model, scene meshes |

### Week 3: engine G2 and detector v2 (Oct 14 - Oct 20)

| Day | Date | Work | Output |
|---|---|---|---|
| D14 | Wed Oct 14 | **M9** G2 generation for V2X (exact OS1 model, fitted pose, VRUs + vehicles, placement sampler) | G2-v2x-v1 |
| D15 | Thu Oct 15 | G2 for LUMPI (5 sensors, merged) | G2-lumpi-v1 |
| D16 | Fri Oct 16 | **M10** training sweep: data mix (UT : G1 : G2), architectures (CenterPoint / VoxelNeXt / Voxel R-CNN), DG aug | Sweep results on real val |
| D17 | Sat Oct 17 | Sweep continued; realism frames from G2 vs UT on the proxy | |
| D18 | Sun Oct 18 | Decide G2's role; submit both tracks with the best single model | **Gate D** |
| D19 | Mon Oct 19 | LUMPI class policy (Unknown, Motorcycle, Bus) per organizer answer and real-val results | Policy locked |
| D20 | Tue Oct 20 | Gated branches only if approved (background prior, self-training) | Ablation rows |

### Week 4: ensemble, select, freeze (Oct 21 - Oct 30)

| Day | Date | Work | Output |
|---|---|---|---|
| D21-D23 | Oct 21-23 | Train final model zoo: 3 seeds x 2-3 architectures per track on the chosen corpus | Model zoo |
| D24 | Sat Oct 24 | **M11** TTA + 3D WBF; select the ensemble on real val with bootstrap CIs | Ensemble config |
| D25 | Sun Oct 25 | **M12** realism frame selection; final packaging dry run | **Gate E** (feature freeze) |
| D26-D29 | Oct 26-29 | Submit the best 2-3 variants per track (confirm only); archive every artifact; start the report outline | Leaderboard confirmations |
| D30 | Fri Oct 30 | Last dev submissions before 17:00 PDT; freeze tags `final-v2x-A/B`, `final-lumpi-A/B` | **Gate F** |

### Final phase (Oct 31 - Nov 15)

| Date (US) | V2X | LUMPI | Notes |
|---|---|---|---|
| Sat Oct 31 evening (after 17:00 PDT) | Final #1: best ensemble | Final #1: best ensemble | The phase opens Nov 1 00:00 UTC |
| Sun Nov 1 | Final #2: best single model (safety) | Final #2: best single model | |
| Mon Nov 2 - Wed Nov 4 | #3: variant with the second-best realism frames or ensemble | #3 | Only pre-validated variants |
| Thu Nov 5 - Tue Nov 10 | #4 if a vetted improvement exists | #4 | |
| Thu Nov 12 | #5 (last planned) | #5 | Keep Nov 13-14 as a reserve for packaging errors |
| Nov 3 - Nov 14 | Write the 4-8 page report from the ablation registry | | Due Nov 15 (confirm channel) |

CodaBench ranks the final phase with `Force_Best` on the leaderboard key, so the best of your final submissions counts. Spend the first two on your strongest, safest systems.

## 2. The daily loop

```
morning   : read overnight training logs -> validation/evaluate.sh on real val -> registry row appended automatically
midday    : one change per experiment; launch training / generation jobs for the night
afternoon : package and submit only hypotheses already confirmed on real val (<= 3 per track per day)
evening   : package_submission.py --record <id> <leaderboard.json>; update the track doc's experiment table
```

Rules of thumb:
- A submission must never be the first time a model's output is scored. Always score locally first.
- Record `(git sha, config hash, data version, seed, real-val AP per class, proxy R, submission id, leaderboard score)` for every submission.
- If local and server scores disagree by more than 1e-4 on realism, stop and find out why.

## 3. Compute plan (shared server)

Topology: NVLink pairs (0-1, 2-3, 4-5, 6-7) and NUMA nodes {GPU 0-3, CPU 0-63,128-191} and {GPU 4-7, CPU 64-127,192-254}.

| Workload | Preferred placement | Notes |
|---|---|---|
| V2X training | GPUs 4-7 (NUMA 1), 4-way DDP | Pin CPU workers with `numactl --cpunodebind=1` |
| LUMPI training | GPUs 0-3 (NUMA 0), 4-way DDP | LUMPI frames are larger; use 2-GPU jobs if contended |
| Generation (G1/G2) | CPU (Embree), 64-128 threads | Does not need GPUs; runs alongside training |
| Ablations | Single-GPU jobs on whichever GPU is free | `CUDA_VISIBLE_DEVICES` pinning |
| Realism proxy / EMD | CPU | Exact EMD on 10k x 10k takes seconds to minutes (see M3) |

**Action on D0:** another user is running jobs on all eight GPUs at 100% utilization. Ask for a reservation (for example GPUs 4-7 for the whole of October, all 8 for Oct 21-30). If none is possible, plan for 2-GPU jobs and prefer the faster architectures.

## 4. Storage plan

One data root, `$BDC_DATA` (default `<repo>/../bdc26-data` on the workspace drive `/`; 1.3 TB free after the downloads on Sep 30), set by `common/env/bdc26.env`; `/data` only for archives. Layout and dataset versions: `DEVELOPMENT.md` Section 3 and `data-<track>/README.md` Sections 3 and 9. Free space on `/` is shared and has swung by more than 1 TB in a day: check `df -h /` before large jobs.

| Item | Size | Status |
|---|---|---|
| UT-LUMPI (pcd, lbl, sem_seg, ins_seg) | 49 GB | Downloaded, zip parts deleted |
| UT-V2X-Real-IC (same folders) | 20 GB | Downloaded, zip parts deleted |
| OpenPCDet clone and build | about 1 GB | `$BDC_DATA/third_party/OpenPCDet` |
| Real LUMPI working set (M4 < 6400 every 5th frame, M5/M6 strided, labels, meta) | about 25 GB | After licence clearance |
| Real V2X-Real agent -1 (train, val, test bins; allowed labels) | about 7 GB | After licence clearance |
| Each `pcdet/<version>` of 10k frames | about 6 GB (LUMPI 50k points) / 4 GB (V2X 35k) plus infos and GT database | Build per version; never rebuild a version in place |
| Checkpoints | 0.1-0.5 GB each | In `model-<track>/<model>/train/output/` (git-ignored); keep the best 3 per config |
| Submissions | about 25 MB per zip | In `model-<track>/<model>/submissions/<date>_<tag>/` (zip git-ignored, manifest tracked) |

Do not store coordinates as float16 (3 cm quantization at 32-64 m).

## 5. Submission budget

| Phase | Allowance | Plan |
|---|---|---|
| Dev | 5/day, 100 total per track | Days 3-30: about 2-3 per day per track, all pre-validated. Target at most 70 used, leaving slack |
| Final | 1/day, 5 total per track | Section 1 final-phase table |

## 6. Communication checklist

- D0: organizer email (questions in `01` S10). Record the reply verbatim in `docs/decisions/` and flip the gated flags.
- D0: GPU reservation request.
- D25: check the CodaBench pages for any rule or date updates.
- Nov 14: confirm the report submission channel and format.
