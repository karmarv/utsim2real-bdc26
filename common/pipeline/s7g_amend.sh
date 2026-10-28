#!/usr/bin/env bash
# S7.6 amendment, one track (rules in docs/decisions/2026-10-26-s7-final-revisions.md, written before this ran; runs
# detached, never uploads or commits):
#   bash common/pipeline/launch.sh <run> amend_<track> common/pipeline/s7g_amend.sh <run> <track>
# 1. the amendment portfolio from the S7.4/S7.5 portfolio as it stood before its final-check freeze (V2X routed-g12
#    from routed-g11, LUMPI routed-g10 from routed-g9 with its fused classes restored); V2X tail copies and sparse
#    stage removed
# 2. fuse --swap-to: one candidate per class, the incumbent fusion with the extended bags in place of their seeds or
#    3-seed bag, through the 6.0 pooled rule (LUMPI Person ranked on late-A as in S7.5)
# 3. budget --pooled (floor loss also bounded on the pooled A+B frames); V2X tail copies and sparse stage re-derived;
#    LUMPI Bicycle, Motorcycle and Bus frozen at the entry
# 4. final check against the entry (common/tools/s7_check.py, rule 5), failing classes frozen at the entry, package,
#    official kit check, scorecard, reproduction scripts, projection (rule 6)
# Events: <run>/events.txt (AMEND <track>: ...); logs <run>/am_<track>_*.log
RUN=$1; T=$2
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
if [ "$T" = v2x ]; then
  SRC=model-v2x-track/routed-g11; M=model-v2x-track/routed-g12; REF=model-v2x-track/routed-g9
  BAGS="bagvr5x bagpv5x"; FUSEX=(); SCX=()
else
  SRC=model-lumpi-track/routed-g9; M=model-lumpi-track/routed-g10; REF=model-lumpi-track/routed-g8
  BAGS="bagvr4x bagpv4x"; FUSEX=(--classes Person Car Truck Van --late-rank Person --gate-top 3); SCX=(--judge Van)
fi
TAG=s7s; N=$(basename $M)
st() { ev "AMEND $T: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/am_${T}_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }

mkdir -p $M/test $M/validation/results $M/train $M/submissions
cp $REF/test/make_submission.sh $REF/test/synthetic_ids.txt $M/test/
cp $SRC/validation/results/route_table.json $M/validation/results/
python - "$T" "$SRC" "$M" > "$RUN/am_${T}_card.log" 2>&1 <<'PY' || { st "portfolio card FAILED"; exit 1; }
import json, sys
from pathlib import Path
import yaml
t, src, m = sys.argv[1:4]
d = yaml.safe_load(Path(src, "model.yaml").read_text())
d["name"] = Path(m).name
d["status"] = (f"S7.6 amendment: {Path(src).name} before its final-check freeze, the extended bags swapped into the "
               "incumbent fusions, the pooled budget (docs/decisions/2026-10-26-s7-final-revisions.md)")
d["notes"] = "S7.6 amendment (docs/decisions/2026-10-26-s7-final-revisions.md).\n"
ft = json.loads(Path(src, "validation", "results", "fusion_table.json").read_text())
rt = json.loads(Path(src, "validation", "results", "route_table.json").read_text())
rare = {"Bicycle", "Motorcycle", "Bus"} if t == "lumpi" else set()
for c, r in ft.items():                                 # the fused classes as S7.4/S7.5 fused them (rare classes stay frozen)
    if r["decision"].startswith("fused") and c not in rare:
        mem, ms = rt[c]["members"], r["best"]["members"]
        d["fusion"][c] = {"members": ms, "weights": [1.0] * len(ms), "iou": r["best"]["iou"],
                          "calibration": {n: mem[n]["calibration"] for n in ms if mem[n]["calibration"]}}
        print(f"restored {c}: {'+'.join(ms)}@{r['best']['iou']}")
d.pop("tail_copies", None); d.pop("sparse_demotion", None)
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: {len(d['members'])} members")
PY
st "$N created ($(tr '\n' ';' < "$RUN/am_${T}_card.log"))"

run fuse python common/tools/route_predictions.py fuse $M --pooled-rule --swap-to $BAGS "${FUSEX[@]}"
st "swap: $(grep -h 'swap candidates' "$RUN/am_${T}_fuse.log" | sed 's/^ *//')"
st "fuse: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$RUN/am_${T}_fuse.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"
run budget python common/tools/route_predictions.py budget $M --pooled
if [ "$T" = v2x ]; then
  run tail python common/tools/route_predictions.py tail $M
  run sparse python common/tools/route_predictions.py sparse $M
else
  run freeze_rare python common/tools/freeze_classes.py $M --from $REF Bicycle Motorcycle Bus
  run validate_rare python common/tools/route_predictions.py validate $M
fi

python common/tools/s7_check.py check "$T" "$M" "$REF" > "$RUN/am_${T}_final_check.log" 2>&1 || { st "final check FAILED"; exit 1; }
FROZEN=$(grep -h '^FROZEN' "$RUN/am_${T}_final_check.log" | cut -d' ' -f2-)
st "final check: $(grep -vh '^FROZEN' "$RUN/am_${T}_final_check.log" | cut -c1-200 | tr '\n' ';')"
if [ -n "$FROZEN" ]; then
  run freeze python common/tools/freeze_classes.py $M --from $REF $FROZEN
  run validate python common/tools/route_predictions.py validate $M
fi
NC=$(python -c "import sys;sys.path.insert(0,'common');from bdc26.config import load_track;print(len(load_track('$T')['classes_with_test_gt']))")
if [ "$(echo $FROZEN | wc -w)" -ge "$NC" ]; then st "every class frozen: $N equals the entry; submission-ready version = the entry"; st "DONE"; exit 0; fi

G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh $TAG > "$RUN/am_${T}_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
st "packaged $Z"
python common/tools/check_submission.py --track $T $Z --official > "$RUN/am_${T}_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/am_${T}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
python common/tools/scorecard.py $M --vs $REF --bootstrap 200 --realism-from $REF "${SCX[@]}" > "$RUN/am_${T}_scorecard.log" 2>&1 \
  && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py $M --tag $TAG --write-script > "$RUN/am_${T}_reproduce.log" 2>&1 || true
python common/tools/reproduce_validation.py $M --tag $TAG --write-script > "$RUN/am_${T}_reproduce_val.log" 2>&1 || true
st "projection: $(python common/tools/s7_check.py projection "$T" "$M" "$REF")"
st "DONE"
