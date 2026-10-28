#!/usr/bin/env bash
# S7 final revisions, one track (S7.4 V2X, S7.5 LUMPI; rules pre-registered in
# docs/decisions/2026-10-26-s7-final-revisions.md; runs detached, never uploads or commits):
#   bash common/pipeline/launch.sh <run> portfolio_<track> common/pipeline/s7f_portfolio.sh <run> <track>
# 1. waits until the four draw runs of the track have their tuned validation files, or the post workers are done
# 2. the two extended bags (existing seeds + both draws)
# 3. the new portfolio from the entry plus the draw runs and the bags (plain and TTA); V2X tail copies and the sparse
#    stage are removed and re-derived
# 4. select (joint, calibrated, pooled), fuse (up to 3, the 6.0 pooled rule; LUMPI also the late-A Person rule and the
#    Van judge), budget; V2X tail copies and sparse stage; LUMPI Bicycle, Motorcycle and Bus frozen at the entry
# 5. final check per class against the entry (rule 5): pooled A+B P(gain) >= 0.9, neither split down by more than
#    0.005, no loss on train-split frames (V2X: V2X-Real train split of A and B pooled; LUMPI: realval-A); LUMPI Van by
#    its judge; failing classes frozen at the entry, then validated again
# 6. package (bag-aware, on a GPU with 24 GB free), official kit check, scorecard, reproduction scripts, projection
# Events: <run>/events.txt (PORTFOLIO <track>: ...); logs <run>/pf_<track>_*.log
RUN=$1; T=$2
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
if [ "$T" = v2x ]; then
  M=model-v2x-track/routed-g11; REF=model-v2x-track/routed-g9; TAG=s7x
  RUNS="vrros5d2:voxelrcnn-ros-g1v5d2 vrros5d3:voxelrcnn-ros-g1v5d3 pvros5d2:pvrcnnpp-ros-g1v5d2 pvros5d3:pvrcnnpp-ros-g1v5d3"
  BAGS="bagvr5x:bag-voxelrcnn-ros-g1v5x bagpv5x:bag-pvrcnnpp-ros-g1v5x"
  FUSEX=(); SCX=()
else
  M=model-lumpi-track/routed-g9; REF=model-lumpi-track/routed-g8; TAG=s7x
  RUNS="vrros4d2:voxelrcnn-ros-g1v4d2 vrros4d3:voxelrcnn-ros-g1v4d3 pvros4d2:pvrcnnpp-ros-g1v4d2 pvros4d3:pvrcnnpp-ros-g1v4d3"
  BAGS="bagvr4x:bag-voxelrcnn-ros-g1v4x bagpv4x:bag-pvrcnnpp-ros-g1v4x"
  FUSEX=(--late-rank Person --gate-top 3 --judge Van); SCX=(--judge Van)
fi
N=$(basename $M)
st() { ev "PORTFOLIO $T: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/pf_${T}_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }
complete() { local m=$1; for S in val valB; do for X in "" _tta; do
  [ -s model-$T-track/$m/validation/output/pcdet_realval-v1_${S}_run1_checkpoint_epoch_40${X}.json ] || return 1; done; done; }
all_done() { for km in $RUNS; do complete ${km#*:} || return 1; done; }
posts_over() { [ "$(grep -c POST_WORKER_DONE "$RUN/events.txt")" -ge 2 ]; }
st "waiting for the draw runs: $RUNS"
until all_done || posts_over; do sleep 120; done
sleep 30
all_done || { st "a run is incomplete after the post workers finished: $(for km in $RUNS; do complete ${km#*:} || printf '%s ' ${km#*:}; done); stopping"; exit 1; }

for kb in $BAGS; do run bag_${kb%%:*} python common/tools/bag_predictions.py model-$T-track/${kb#*:}; done

mkdir -p $M/test $M/validation/results $M/train $M/submissions
cp $REF/test/make_submission.sh $REF/test/synthetic_ids.txt $M/test/
python - "$T" "$M" "$REF" "$RUNS" "$BAGS" > "$RUN/pf_${T}_members.log" 2>&1 <<'PY' || { st "portfolio card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
t, m, ref, runs, bags = sys.argv[1:6]
d = yaml.safe_load(Path(ref, "model.yaml").read_text())
d["name"] = Path(m).name
d["strategy"] = "S7"
d["status"] = (f"S7 final revision ({'S7.4' if t == 'v2x' else 'S7.5'}): the entry {Path(ref).name} plus the generator-draw runs and the "
               "extended bags, through the rules of docs/decisions/2026-10-26-s7-final-revisions.md")
d["notes"] = "S7 final revisions (docs/decisions/2026-10-26-s7-final-revisions.md, rule 4).\n"
d.pop("tail_copies", None); d.pop("sparse_demotion", None)
ck, bk = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth", "train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth"
for spec, ckpt in ((runs, ck), (bags, bk)):
    for km in spec.split():
        k, name = km.split(":")
        d["members"][k] = {"model": name, "ckpt": ckpt}
        d["members"][k + "_tta"] = {"model": name, "ckpt": ckpt, "tta": "flip4+yaw+z", "postprocess": "test/postprocess_tta.yaml"}
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: {len(d['members'])} members")
PY
st "$N created ($(tail -n 1 "$RUN/pf_${T}_members.log"))"

run select python common/tools/route_predictions.py select $M --rule joint --calibrated --pooled
run fuse python common/tools/route_predictions.py fuse $M --max-members 3 --pooled-rule "${FUSEX[@]}"
run budget python common/tools/route_predictions.py budget $M
if [ "$T" = v2x ]; then
  run tail python common/tools/route_predictions.py tail $M
  run sparse python common/tools/route_predictions.py sparse $M
else
  run freeze_rare python common/tools/freeze_classes.py $M --from $REF Bicycle Motorcycle Bus
  run validate_rare python common/tools/route_predictions.py validate $M
fi
st "fuse: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$RUN/pf_${T}_fuse.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"

python common/tools/s7_check.py check "$T" "$M" "$REF" > "$RUN/pf_${T}_final_check.log" 2>&1 || { st "final check FAILED"; exit 1; }
FROZEN=$(grep -h '^FROZEN' "$RUN/pf_${T}_final_check.log" | cut -d' ' -f2-)
st "final check: $(grep -vh '^FROZEN' "$RUN/pf_${T}_final_check.log" | sed -E 's/ \{/ {/' | cut -c1-200 | tr '\n' ';')"
if [ -n "$FROZEN" ]; then
  run freeze python common/tools/freeze_classes.py $M --from $REF $FROZEN
  run validate python common/tools/route_predictions.py validate $M
fi
NC=$(python -c "import sys;sys.path.insert(0,'common');from bdc26.config import load_track;print(len(load_track('$T')['classes_with_test_gt']))")
if [ "$(echo $FROZEN | wc -w)" -ge "$NC" ]; then st "every class frozen: $N equals the entry; submission-ready version = the entry"; st "DONE"; exit 0; fi

G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh $TAG > "$RUN/pf_${T}_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
st "packaged $Z"
python common/tools/check_submission.py --track $T $Z --official > "$RUN/pf_${T}_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/pf_${T}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
python common/tools/scorecard.py $M --vs $REF --bootstrap 200 --realism-from $REF "${SCX[@]}" > "$RUN/pf_${T}_scorecard.log" 2>&1 \
  && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py $M --tag $TAG --write-script > "$RUN/pf_${T}_reproduce.log" 2>&1 || true
python common/tools/reproduce_validation.py $M --tag $TAG --write-script > "$RUN/pf_${T}_reproduce_val.log" 2>&1 || true
st "projection: $(python common/tools/s7_check.py projection "$T" "$M" "$REF")"
st "DONE"
