#!/usr/bin/env bash
# S6 portfolio for one track (docs/02-STRATEGY.md Section 8.6; runs detached, never uploads or commits):
#   bash common/pipeline/launch.sh <run> portfolio_<track> common/pipeline/s6_portfolio.sh <run> <track>
# 1. waits until every S6 seed of the track has its four tuned validation files (or the post workers are done)
# 2. seed bags (common/tools/bag_predictions.py) for every bag of the track whose seeds are complete
# 3. new seeds and bags into routed-g8 (plain and TTA)
# 4. select (joint, calibrated, pooled), fuse (up to 3, pooled; LUMPI: late-A Person rule and the Van judge), budget,
#    freeze (LUMPI Bicycle, Motorcycle, Bus at R5), tail copies (V2X pedestrian; LUMPI Person copies exceeded the server
#    budget in R5), final gate against routed-g7 (LUMPI with the Van judge)
# 5. package (bag-aware), official kit check, scorecard against routed-g7 (LUMPI: judged estimate), reproduce script
# Events: <run>/events.txt (PORTFOLIO <track>: ...); logs <run>/pf_<track>_*.log (select, fuse, budget, gate, package, check, scorecard)
RUN=$1; T=$2
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
M=model-$T-track/routed-g8
st() { ev "PORTFOLIO $T: $*"; }
if [ "$T" = lumpi ]; then
  SEEDS="vrros4s3:voxelrcnn-ros-g1v4-s3 vrros4s4:voxelrcnn-ros-g1v4-s4 pvros4s3:pvrcnnpp-ros-g1v4-s3 pvros4s4:pvrcnnpp-ros-g1v4-s4"
  BAGS="bagvr4:bag-voxelrcnn-ros-g1v4 bagpv4:bag-pvrcnnpp-ros-g1v4"
  FUSEX=(--late-rank Person --gate-top 3 --judge Van); GATEX=(--judge Van); SCX=(--judge Van)
else
  SEEDS="vrros5s2:voxelrcnn-ros-g1v5-s2 vrros5s3:voxelrcnn-ros-g1v5-s3 pvros5s2:pvrcnnpp-ros-g1v5-s2 pvros5s3:pvrcnnpp-ros-g1v5-s3"
  BAGS="bagvr5:bag-voxelrcnn-ros-g1v5 bagpv5:bag-pvrcnnpp-ros-g1v5 bagvr4:bag-voxelrcnn-ros-g1v4 bagpv4:bag-pvrcnnpp-ros-g1v4"
  FUSEX=(); GATEX=(); SCX=()
fi
complete() { local m=$1; for S in val valB; do for X in "" _tta; do
  [ -s model-$T-track/$m/validation/output/pcdet_realval-v1_${S}_run1_checkpoint_epoch_40${X}.json ] || return 1; done; done; }
all_done() { for km in $SEEDS; do complete ${km#*:} || return 1; done; }
posts_over() { [ "$(grep -c POST_WORKER_DONE "$RUN/events.txt")" -ge 2 ]; }
st "waiting for the seeds: $SEEDS"
until all_done || posts_over; do sleep 120; done
sleep 30
ADD=""
for km in $SEEDS; do if complete ${km#*:}; then ADD="$ADD $km"; else st "SKIP seed ${km#*:} (incomplete validation outputs)"; fi; done
BADD=""
for kb in $BAGS; do
  B=model-$T-track/${kb#*:}
  ok=1; for m in $(python -c "import yaml;print(' '.join(yaml.safe_load(open('$B/model.yaml'))['members']))"); do complete $m || ok=0; done
  if [ $ok = 1 ]; then
    if [ -s "$B/validation/output/pcdet_realval-v1_valB_bag_checkpoint_epoch_40_tta.json" ] && [ -s "$B/validation/results/local_scores_tta.json" ] \
       && [ "$B/validation/results/local_scores_tta.json" -nt "$B/model.yaml" ]; then st "bag ${kb#*:} already fused"
    else python common/tools/bag_predictions.py "$B" > "$RUN/pf_${T}_bag_${kb#*:}.log" 2>&1 || { st "bag ${kb#*:} FAILED"; continue; }; fi
    st "bag ${kb#*:}: $(tail -n 2 "$RUN/pf_${T}_bag_${kb#*:}.log" 2>/dev/null | tr '\n' ' ')"; BADD="$BADD $kb"
  else st "SKIP bag ${kb#*:} (a seed is incomplete)"; fi
done
python - "$T" "$ADD" "$BADD" <<'PY' >> "$RUN/pf_${T}_members.log" 2>&1
import sys, yaml
from pathlib import Path
t, add, badd = sys.argv[1], sys.argv[2].split(), sys.argv[3].split()
ck = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"; bk = "train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth"
p = Path(f"model-{t}-track/routed-g8/model.yaml"); d = yaml.safe_load(p.read_text())
for km in add:
    k, m = km.split(":")
    d["members"][k] = {"model": m, "ckpt": ck}
    d["members"][k + "_tta"] = {"model": m, "ckpt": ck, "tta": "flip4+yaw+z", "postprocess": "test/postprocess_tta.yaml"}
for kb in badd:
    k, m = kb.split(":")
    d["members"][k] = {"model": m, "ckpt": bk}
    d["members"][k + "_tta"] = {"model": m, "ckpt": bk, "tta": "flip4+yaw+z", "postprocess": "test/postprocess_tta.yaml"}
p.write_text(yaml.safe_dump(d, sort_keys=False)); print(f"routed-g8 {t}: {len(d['members'])} members")
PY
st "members added:$ADD; bags:$BADD ($(tail -n 1 "$RUN/pf_${T}_members.log"))"
run() { local N=$1; shift; ( time "$@" ) > "$RUN/pf_${T}_$N.log" 2>&1 || { st "$N FAILED"; exit 1; }; st "$N done"; }
run select python common/tools/route_predictions.py select $M --rule joint --calibrated --pooled
run fuse python common/tools/route_predictions.py fuse $M --max-members 3 --pooled "${FUSEX[@]}"
run budget python common/tools/route_predictions.py budget $M
if [ "$T" = lumpi ]; then
  python common/tools/freeze_classes.py $M --from model-lumpi-track/routed-g7 Bicycle Motorcycle Bus > "$RUN/pf_${T}_freeze.log" 2>&1 || { st "freeze FAILED"; exit 1; }
  run validate_freeze python common/tools/route_predictions.py validate $M
else
  run tail python common/tools/route_predictions.py tail $M
fi
run gate python common/tools/route_predictions.py gate $M --vs model-$T-track/routed-g7 "${GATEX[@]}"
st "final gate: $(grep -h '^reverted' "$RUN/pf_${T}_gate.log")"
G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh s6 > "$RUN/pf_${T}_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d $M/submissions/*_s6 | tail -n 1)/submission.zip
st "packaged $Z"
python common/tools/check_submission.py --track $T $Z --official > "$RUN/pf_${T}_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/pf_${T}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
python common/tools/scorecard.py $M --vs model-$T-track/routed-g7 --bootstrap 200 --realism-from model-$T-track/routed-g7 "${SCX[@]}" > "$RUN/pf_${T}_scorecard.log" 2>&1 \
  && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py $M --tag s6 --write-script > "$RUN/pf_${T}_reproduce.log" 2>&1 || true
st "DONE"
