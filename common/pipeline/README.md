# common/pipeline: background jobs

Shell scripts that run the long jobs of a campaign (training queues, post-processing of each trained member, the
portfolio of each track, TensorBoard) detached from the terminal, so they survive an SSH disconnect and can be checked
at any time. Nothing here uploads to CodaBench, commits or tags. Root README Section 6.10 has the short version.

## Files

| Script | Role |
|---|---|
| `launch.sh <run> <name> <script> [args]` | starts `<script>` with `setsid nohup` from a snapshot `<run>/bin/<name>.sh` (sibling scripts as `bin/lib_<file>`, copied once), log `<run>/<name>.log`, PID line in `<run>/pids.txt`, `LAUNCH` event |
| `common.sh` | sourced helpers: `ev` (append to `events.txt`), `qpop`/`qpush` (queue files under `flock`), `ckpt_ok` (load-verify a checkpoint), `free_gpu <MiB>` (GPU with the most free memory) |
| `train_queue.sh <run> <name> <gpus> <port> [wait-event]` | training worker on one 4-GPU half: pops `track:member[:seed]` from `train_queue.txt`, runs `train.sh 4 run1 --fix_random_seed --workers 6 [--seed S]`, verifies the epoch-40 checkpoint, pushes `track:member` to `post_queue.txt` |
| `post_queue.sh <run> <name> <n_train_workers>` | post-processing worker: pops `post_queue.txt`, runs `member_post.sh`; exits once the queue is empty and all training workers are done |
| `member_post.sh <run> <track> <member>` | score blend (two-stage members), plain and TTA tuning on realval-A/B, realval curves into TensorBoard; each step on a GPU with at least `MIN_FREE` MiB free (default 24000), retried 3 times |
| `s6_portfolio.sh <run> <track>` | S6 portfolio of one track (docs/02-STRATEGY.md Section 8.6): waits for the seeds, fuses the seed bags, adds them to `routed-g8`, select, fuse, budget, freeze or tail copies, final gate against `routed-g7`, package, official kit check, scorecard, reproduction script |
| `s6_realism_lumpi.sh <run>` | S6 item 9 (CPU): LUMPI realism frames chosen from the whole `g1-v4` corpus, FPD and FPD + EMD, scored on the held-out proxies against the R5 frames; writes candidate lists only (`routed-g8/validation/results/realism_candidates/`); result 2026-10-15: R5 frames kept |
| `curves_queue.sh <run> <name> <n_train_workers>` | realval curves (`tb_realval.py`) for models trained before the pipeline, from `curves_queue.txt`; starts only after the training workers are done |
| `finish_portfolio.sh <run> <track> <model> <tag> <ref>` | finishes a routed model whose route and fusions are already set (a variant): score floors (tail copies removed first and derived after), tail copies (V2X), packaging, kit check, scorecard, reproduction script; no gate (S6 V2X variant b) |
| `s6b_lumpi.sh <run>` | S6 close-out for LUMPI: `routed-g8b` = the S6 entry plus the fuse step's Car candidate, kept only if the pooled condition holds on the final predictions, then packaged and checked |
| `gpu_queue.sh <run> <name> <queue> <gpu>` | generic worker pinned to one GPU: pops one shell command per line from a queue file and runs it from the repository root (reproduction runs: one job per GPU, never shared) |
| `status.sh <run>` | one screen: `STATUS.md`, queue lengths, last 20 events, epoch of each training run, live processes, GPU memory |
| `tensorboard.sh [port]` | TensorBoard on 127.0.0.1 over every model's `tensorboard/` and `tensorboard_realval/` folders; restarts it when a new run folder appears (checked every 10 minutes) |

Portability: `launch.sh` exports `BDC_REPO` (the repository root, from the launched script's location) to the detached
snapshot; the other scripts use it, or their own location when run directly. Nothing refers to a fixed path.

## Run directory

One per campaign under `$BDC_DATA/logs/` (S6: `$BDC_DATA/logs/s6`):

```
STATUS.md              human log: what was started, decisions taken while running
events.txt             machine log, one line per event (below)
train_queue.txt        jobs still to train: track:member[:seed]
post_queue.txt         trained members waiting for post-processing: track:member
pids.txt               <date> <time> <name> pid <pid> : <script> <args>
bin/                   snapshot copies of the scripts that are running
<name>.log             stdout and stderr of each launched job
train_<track>_<member>.log, post_<track>_<member>_<step>.log, pf_<track>_<step>.log
```

Events: `LAUNCH`, `TRAIN_WORKER_START/DONE`, `TRAIN_START`, `TRAIN_DONE` (checkpoint verified; OpenPCDet's own
evaluation after training races the last save and may exit 1, which is harmless), `TRAIN_FAIL`, `POST_WORKER_START/DONE`,
`POST_START`, `POST_STEP_DONE/FAIL <step>`, `POST_DONE/FAIL`, `BAG_DONE`, `PORTFOLIO <track>: ...` (ends with `DONE` or
`<step> FAILED`), `REALISM lumpi: ...`, `CURVES_WORKER_START/DONE`, `CURVES_DONE/FAIL`.

## Usage

```bash
source common/env/activate.sh; RUN=$BDC_DATA/logs/s6; mkdir -p $RUN
printf '%s\n' lumpi:pvrcnnpp-ros-g1v4-s3:2666 v2x:pvrcnnpp-ros-g1v5-s2:1666 > $RUN/train_queue.txt
bash common/pipeline/launch.sh $RUN trainA common/pipeline/train_queue.sh $RUN trainA 0,1,2,3 29621
bash common/pipeline/launch.sh $RUN trainB common/pipeline/train_queue.sh $RUN trainB 4,5,6,7 29743
bash common/pipeline/launch.sh $RUN postA common/pipeline/post_queue.sh $RUN postA 2
bash common/pipeline/launch.sh $RUN portfolio_lumpi common/pipeline/s6_portfolio.sh $RUN lumpi
bash common/pipeline/status.sh $RUN
tail -f $RUN/events.txt
```

- Add a job while workers run: `echo lumpi:<member>:<seed> >> $RUN/train_queue.txt` (a worker that already found the
  queue empty has exited; launch a new one).
- Re-run one member's post-processing by hand: `bash common/pipeline/launch.sh $RUN repost common/pipeline/member_post.sh $RUN <track> <member>`.
- Stop a job: `kill <pid>` with the PID from `pids.txt` (its children: `pkill -P <pid>`). Never kill by pattern: `pkill -f`
  also matches the shell that runs it.
- Never edit a script in `<run>/bin/` while it runs (bash reads scripts as it goes); edit the repository copy and
  relaunch.

## TensorBoard

```bash
bash common/pipeline/launch.sh $BDC_DATA/logs/tensorboard tensorboard common/pipeline/tensorboard.sh 6006
ssh -N -L 6006:localhost:6006 <user>@<server>     # on your own machine; then open http://localhost:6006
```

Scalars per run `<track>/<model>/<run>`: OpenPCDet training loss terms and learning rate (`train/`, every iteration);
`realval_A/mAP`, `realval_B/mAP` and per class `realval_A/<class>`, `realval_B/<class>` every 5 epochs (official
metric, tuned post-processing, every 8th frame of A and 6th of B; `common/tools/tb_realval.py`, values also in
`validation/results/realval_curves.json`). The curves are for monitoring only: every member uses its epoch-40
checkpoint, so no epoch is chosen on real data.
