#!/usr/bin/env bash
# Release 10.3, L7 (record docs/decisions/2026-11-13-s10-10.3-final-system.md, Section 12): L5 with the re-cast
# VoxelR-CNN members that pass the member rule, built and gated before the machine move (the entrant, 2026-11-13).
#   bash common/pipeline/launch.sh <run> s103l7 common/pipeline/s10_3_l7.sh <run>
# Member rule (fixed before any 12-view result): voxelrcnn-rosf-g1v6pq replaces voxelrcnn-rosf-g1v6 (vrrosf6_tta12, the
# Car route) and voxelrcnn-rosn-g1v6pq replaces voxelrcnn-rosn-g1v6 (vrrosn6_tta12, the Person route) only if its
# 12-view AP on that class is at least its parent's on both realval A and realval B. If none passes, there is no L7.
# L3h = routed-c0's recipe with those swaps: C0's knobs and 50 g1-v6 frames; the other members' kit predictions are
# routed-c0's (byte-identical to L5's); the Person copy threshold re-fit as for every C0 recipe. L7 = L3h + P.
# Upload rule (fixed before any result): rules 1/1b, box budget, kit check and audit pass, rule 14 against L5 says GO
# and the pooled realval mAP delta against L5 is above 0. JUDGEMENT with a positive delta goes to the entrant.
RUN=$1
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
export S10_3_LIB=1
source "$REPO/common/pipeline/s10_3_build.sh" "$RUN" lumpi
T=lumpi; TD=model-lumpi-track; L5=routed-s10-2-l5; L3H=routed-s10-3-l3h; L7=routed-s10-3-l7
C0ZIP=$TD/routed-c0/submissions/2026-11-07_c0/lumpi_s10_submission.zip
SYS=$L7; st "armed: waits for the 12-view tuning of voxelrcnn-rosf-g1v6pq and voxelrcnn-rosn-g1v6pq (t12l7)"
until grep -qE "WORKER_DONE t12l7_1$" "$E" && grep -qE "WORKER_DONE t12l7_3$" "$E"; do sleep 60; done
if grep -qE "JOB_FAIL t12l7_" "$E"; then st "a 12-view job FAILED: no L7"; exit 1; fi

ONLY=$(python - <<'PY'
import json, sys
from pathlib import Path
TD = Path("model-lumpi-track")
keep = []
for parent, cls in (("voxelrcnn-rosf-g1v6", "Car"), ("voxelrcnn-rosn-g1v6", "Person")):
    new, old = (json.loads((TD / m / "validation/results/local_scores_tta12.json").read_text()) for m in (parent + "pq", parent))
    d = {s: new[f"realval_{s}_per_class"][cls] - old[f"realval_{s}_per_class"][cls] for s in ("A", "B")}
    ok = all(v >= 0 for v in d.values())
    print(f"{parent}pq {cls} 12-view: A {d['A']:+.4f}, B {d['B']:+.4f} -> {'swap' if ok else 'keep the parent'}", file=sys.stderr)
    if ok:
        keep.append(parent)
print(",".join(keep))
PY
2> "$RUN/s103_l7_member_rule.log")
st "member rule: $(tr '\n' ' ' < "$RUN/s103_l7_member_rule.log")"
[ -n "$ONLY" ] || { st "no member passes the member rule: no L7; L5 (1051465) stays the LUMPI entry"; exit 0; }

# L3h: C0's recipe with the swaps
SYS=$L3H; PARENT_DIR=$TD/routed-c0; MD=$TD/$L3H
[ -d "$MD" ] || run recipe python common/tools/s10_3_recipe.py lumpi routed-c0 "$L3H" --suffix pq --only "$ONLY" --candidate L3h || exit 1
run validate python common/tools/route_predictions.py validate "$MD" || exit 1
run clean python common/tools/clean_check.py "$MD" || { st "rules 1/1b FAILED: $(tail -n 2 "$(lg clean)" | tr '\n' ' ')"; exit 1; }
st "rules 1 and 1b: $(grep -E '^(FRAMES|PASS)' "$(lg clean)" | tr '\n' ' ' | cut -c1-300)"
gates "$SYS" routed-c0
NEWK=()
for n in $(python -c "import sys,yaml;sys.path.insert(0,'common/tools');from route_predictions import used_members;print(' '.join(used_members(yaml.safe_load(open('$MD/model.yaml')))))"); do
  if [ "$(python -c "import yaml;a=yaml.safe_load(open('$MD/model.yaml'))['members']['$n'];b=yaml.safe_load(open('$PARENT_DIR/model.yaml'))['members']['$n'];print(int(a==b))")" = 1 ]; then
    cp -p "$PARENT_DIR/test/output/predictions_$n.json" "$MD/test/output/"
  else NEWK+=("$n"); fi
done
st "kit predictions: $(( $(ls "$MD"/test/output/predictions_*.json | wc -l) )) members reused from routed-c0; new: ${NEWK[*]}"
GPUS=(1 3); i=0
for n in "${NEWK[@]}"; do      # each new member alone on its own GPU (a shared GPU can change inference digits)
  G=${GPUS[$((i % 2))]}; i=$((i + 1)); C=$(kit_member "$MD" "$n")
  ( until [ "$(nvidia-smi -i "$G" --query-gpu=memory.used --format=csv,noheader,nounits)" -le 1000 ]; do sleep 30; done
    CUDA_VISIBLE_DEVICES=$G bash -c "$C" > "$(lg "kit_$n")" 2>&1; echo $? > "$RUN/s103_${SYS}_kit_$n.rc" ) &
done
wait
for n in "${NEWK[@]}"; do [ "$(cat "$RUN/s103_${SYS}_kit_$n.rc")" = 0 ] || { st "kit predictions of $n FAILED (log $(lg "kit_$n"))"; exit 1; }; done
st "kit predictions done"
run merge merge_kit "$SYS" || exit 1
python common/tools/s9_copies_fit.py lumpi "$MD" --max-boxes $MAXBOX --write > "$(lg copies_fit)" 2>&1 || { st "copies fit FAILED"; exit 1; }
CF=$(tail -n 1 "$(lg copies_fit)"); st "copies fit: $CF"
if [ "${CF%% *}" = SET ]; then
  run validate_copies python common/tools/route_predictions.py validate "$MD" || exit 1
  run merge_copies merge_kit "$SYS" || exit 1
  gates "$SYS" routed-c0
fi
package "$SYS" s10-3-l3h pcdet/g1-v6 "$C0ZIP" || { st "L3h packaging FAILED"; exit 1; }

# L7 = L3h + P
SYS=$L7
[ -d "$TD/$L7" ] || run recipe python common/tools/s10_3_recipe.py lumpi "$L3H" "$L7" --same-members --candidate L7 --final-adjust-from "$L5" || exit 1
build_p "$L3H" "$L7" s10-3-l7 pcdet/g1-v6 "$L5" || { st "L7 STOPPED"; exit 1; }

# the upload rule
G=$(lg "grouped_vs_$L5"); LEVEL=$(head -n 1 "$G" | sed 's/^[^:]*: //' | awk '{print $1}')
DELTA=$(grep -oE "pooled mAP delta [+-][0-9.]+" "$G" | head -n 1 | awk '{print $4}')
if [ "$LEVEL" = GO ] && python -c "import sys; sys.exit(0 if float('$DELTA') > 0 else 1)"; then
  st "UPLOAD RULE: GO (rule 14 vs L5 $LEVEL, pooled mAP delta $DELTA): L7 is the 10.3 LUMPI upload"
elif [ "$LEVEL" = JUDGEMENT ] && python -c "import sys; sys.exit(0 if float('$DELTA') > 0 else 1)"; then
  st "UPLOAD RULE: JUDGEMENT (rule 14 vs L5 $LEVEL, pooled mAP delta $DELTA): the entrant decides"
else
  st "UPLOAD RULE: NO-GO (rule 14 vs L5 $LEVEL, pooled mAP delta $DELTA): L5 (1051465) stays the LUMPI entry"
fi
st "DONE"
