#!/usr/bin/env bash
# Release 10.5 record Section 11 (the 8-hour iteration): new members -> a system. Waits until every listed member is
# tuned (POST_DONE), runs the S9 member check of each against its incumbent (common/tools/s9_member_check.py: a class
# with pooled P(gain) >= 0.9 and neither split down > 0.005), then builds <name> = <parent> + the passing members with
# `s10_5_build.sh addmember` (extend, fuse, rare classes frozen, final check, build; upload rule against <upv>).
#   bash common/pipeline/launch.sh <run> l12 common/pipeline/s10_5_iter.sh <run> <parent> <name> <cand> <parent zip> <upv> \
#        key:member:incumbent ...
RUN=$1; PARENT=$2; NAME=$3; CAND=$4; PZ=$5; UPV=$6; shift 6; SPECS=("$@")
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh
E=$RUN/events.txt; P=$REPO/common/pipeline
st() { ev "S10-5 lumpi $NAME: $*"; }
st "armed: member checks of ${SPECS[*]} when tuned, then $NAME = $PARENT + the passing members"
isbag() { python -c "import sys,yaml;sys.exit(0 if yaml.safe_load(open('model-lumpi-track/$1/model.yaml')).get('type')=='bag' else 1)"; }
wait_tuned() { until grep -qE "POST_DONE lumpi $1\$" "$E"; do grep -qE "(TRAIN_FAIL|POST_FAIL) lumpi $1\$" "$E" && break; sleep 120; done; }
for s in "${SPECS[@]}"; do IFS=: read -r k m i <<< "$s"
  if isbag "$m"; then        # a seed bag: its seeds tuned, then its fused predictions (plain and 4-view)
    for sd in $(python -c "import yaml;print(' '.join(yaml.safe_load(open('model-lumpi-track/$m/model.yaml'))['members']))"); do wait_tuned "$sd"; done
    python common/tools/bag_predictions.py "model-lumpi-track/$m" > "$RUN/s105_${NAME}_bag_$k.log" 2>&1 || { st "bag $m FAILED"; st "DONE"; exit 1; }
    st "bag $m built: $(grep -E ': A' "$RUN/s105_${NAME}_bag_$k.log" | tr '\n' ';' | cut -c1-300)"
  else wait_tuned "$m"; fi
done
PASSED=()
for s in "${SPECS[@]}"; do IFS=: read -r k m i <<< "$s"
  python common/tools/s9_member_check.py lumpi "$m" "$i" > "$RUN/s105_${NAME}_check_$k.log" 2>&1
  R=$(tail -n 1 "$RUN/s105_${NAME}_check_$k.log")
  st "member check $k ($m vs $i): $(grep -vE '^(PASS|FAIL)' "$RUN/s105_${NAME}_check_$k.log" | grep -E 'P\(gain\)|P ' | tr -s ' ' | tr '\n' ';' | cut -c1-500) => $R"
  [ "${R%% *}" = PASS ] && PASSED+=("$k:$m")
done
if [ ${#PASSED[@]} = 0 ]; then st "no member passed its check: no $CAND"; st "DONE"; exit 0; fi
st "passing members: ${PASSED[*]}; building $NAME"
bash "$P/s10_5_build.sh" "$RUN" addmember lumpi "$PARENT" "$NAME" "$CAND" "$PZ" "$UPV" "${PASSED[@]}"
st "DONE"
