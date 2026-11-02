#!/usr/bin/env bash
# S9 portfolio of one track (rules 1-3 of docs/decisions/2026-11-02-s9-clean-twin-plan.md Section 8, written before any
# S9 run; runs detached, never uploads or commits):
#   bash common/pipeline/launch.sh <run> pf_lumpi_w1 common/pipeline/s9_portfolio.sh <run> lumpi routed-g12 \
#        model-lumpi-track/routed-g11d s9a vrros6:voxelrcnn-ros-g1v6:voxelrcnn-ros-g1v4 ...
# 1. waits until every listed member has its tuned plain and 8-view validation predictions on realval A and B; a member
#    that is a seed bag (model.yaml type: bag) is fused (common/tools/bag_predictions.py) once all its seeds have them
# 2. rule 3: the member check of each against its family incumbent (common/tools/s9_member_check.py); only members
#    that pass on at least one class enter
# 3. the new routed model = the reference (the entry or the last S9 version) plus the passing members (plain and 8-view);
#    V2X tail copies and the sparse stage are removed and re-derived (as S7.6 and S8)
# 4. extend the route table, fuse up to 3 members (the 6.0 pooled rule; LUMPI: Person ranked on late-A, the Van judge);
#    LUMPI keeps the reference's floors and tail copies and freezes Bicycle, Motorcycle and Bus (rule 2); V2X budget,
#    tail copies and the sparse stage
# 5. final check per class against the reference (common/tools/s7_check.py: pooled P >= 0.9, neither split down by
#    more than 0.005, the train-split condition); failing classes frozen at the reference
# 6. package (the reference's realism frames), official kit check, scorecard, reproduction scripts, projection
# Optional (S9 W2-W4, record Section 15):
#   S9_TTA12="k1 k2": member keys whose 12-view siblings (<k>_tta12, validation/tune_and_eval.sh --tta-tag tta12) are
#     swapped into the fusions after the main fuse (the S8 swap stage, fuse --swap-variant tta12); the waiter also
#     waits for their _tta12 validation outputs
#   S9_MAX_BOXES=N (LUMPI): rule 1(b), after packaging the Person copy threshold is re-derived for this route
#     (common/tools/s9_copies_fit.py: the lowest realval-A quantile in 0.95-0.99 whose kit keeps at most N boxes);
#     if it changes: validate, final check again, package again
# Realism frames: the reference's, unless S9_FRAMES (a corpus, e.g. pcdet/g1-v6) and S9_IDS (its 50 chosen ids, rule 4)
# are set in the environment; then the scorecard scores realism itself instead of reusing the reference's.
# Events: <run>/events.txt (S9 <track> <tag>: ...); logs <run>/s9_<track>_<tag>_*.log
RUN=$1; T=$2; NAME=$3; REF=$4; TAG=$5; shift 5; SPECS="$*"
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
V=model-$T-track; M=$V/$NAME
FUSEX=(); SCX=()
[ "$T" = lumpi ] && { FUSEX=(--late-rank Person --gate-top 3 --judge Van); SCX=(--judge Van); }
st() { ev "S9 $T $TAG: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/s9_${T}_${TAG}_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }
card_get() { python -c "import sys,yaml;d=yaml.safe_load(open(sys.argv[1]+'/model.yaml'));print($2)" $V/$1; }
runof() { card_get $1 "'bag' if d.get('type') == 'bag' else 'run1'"; }
complete() { local m=$1 r; r=$(runof $m); for S in val valB; do for X in "" _tta; do
  [ -s $V/$m/validation/output/pcdet_realval-v1_${S}_${r}_checkpoint_epoch_40${X}.json ] || return 1; done; done; }
tta12_ready() { local m=$1 S; for S in val valB; do
  [ -s $V/$m/validation/output/pcdet_realval-v1_${S}_run1_checkpoint_epoch_40_tta12.json ] || return 1; done; }
all_done() { local ok=0 s k m i sd ready; for s in $SPECS; do IFS=: read -r k m i <<< "$s"
  if [[ " ${S9_TTA12:-} " == *" $k "* ]] && ! tta12_ready $m; then ok=1; continue; fi
  complete $m && continue; ok=1
  if [ "$(runof $m)" = bag ] && [ ! -e "$RUN/s9_${T}_${TAG}_bag_$m.log" ]; then
    ready=1; for sd in $(card_get $m "' '.join(d['members'])"); do complete $sd || ready=0; done
    if [ $ready = 1 ]; then
      python common/tools/bag_predictions.py $V/$m > "$RUN/s9_${T}_${TAG}_bag_$m.log" 2>&1 || { st "bag $m FAILED"; exit 1; }
      st "bag $m built: $(grep -E ': A' "$RUN/s9_${T}_${TAG}_bag_$m.log" | tr '\n' ';' | cut -c1-300)"
    fi
  fi; done; return $ok; }
st "waiting for: $SPECS"
until all_done; do sleep 120; done
sleep 30

PASSED=""
for s in $SPECS; do
  IFS=: read -r k m i <<< "$s"
  python common/tools/s9_member_check.py $T $m $i > "$RUN/s9_${T}_${TAG}_check_$k.log" 2>&1 || { st "member check $k FAILED"; exit 1; }
  R=$(tail -n 1 "$RUN/s9_${T}_${TAG}_check_$k.log")
  st "member check $k ($m vs $i): $R"
  [ "${R%% *}" = PASS ] && PASSED="$PASSED $k:$m"
done
[ -z "$PASSED" ] && { st "no member passed rule 3: $NAME not built"; st "DONE"; exit 0; }

mkdir -p $M/test $M/validation/results $M/train $M/submissions
cp $REF/test/make_submission.sh $REF/test/synthetic_ids.txt $M/test/
cp $REF/validation/results/route_table.json $M/validation/results/
RFROM=(--realism-from $REF)
if [ -n "${S9_FRAMES:-}" ]; then cp "$S9_IDS" $M/test/synthetic_ids.txt; RFROM=(); st "realism frames: $S9_FRAMES ($S9_IDS)"; fi
python - "$REF" "$M" "$T" "$PASSED" "${S9_FRAMES:-}" > "$RUN/s9_${T}_${TAG}_card.log" 2>&1 <<'PY' || { st "card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
ref, m, t, passed, frames = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(), sys.argv[5]
d = yaml.safe_load(Path(ref, "model.yaml").read_text())
if frames:
    d["realism_frames"] = frames
ck = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"
for km in passed:
    k, name = km.split(":")
    bag = yaml.safe_load((Path(m).parent / name / "model.yaml").read_text()).get("type") == "bag"
    c = "train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth" if bag else ck   # a bag's ckpt path only names its files
    d["members"][k] = {"model": name, "ckpt": c}
    d["members"][k + "_tta"] = {"model": name, "ckpt": c, "tta": "flip4+yaw+z", "postprocess": "test/postprocess_tta.yaml"}
d["name"] = Path(m).name
d["strategy"] = "S9"
d["status"] = (f"S9: {Path(ref).name} plus the engine-v6 members that passed rule 3 ({' '.join(passed)}), rule 4 of S8.2 in "
               "full (extend, fuse up to 3), gated per class (docs/decisions/2026-11-02-s9-clean-twin-plan.md)")
d["notes"] = "S9 (docs/decisions/2026-11-02-s9-clean-twin-plan.md, Sections 7-8).\n"
if t == "v2x":
    d.pop("tail_copies", None); d.pop("sparse_demotion", None)       # re-derived after fuse, as in S7.6 and S8
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: {len(d['members'])} members")
PY
st "$NAME created ($(tr '\n' ';' < "$RUN/s9_${T}_${TAG}_card.log"))"
run extend python common/tools/route_predictions.py extend $M
run fuse python common/tools/route_predictions.py fuse $M --max-members 3 --pooled-rule "${FUSEX[@]}"
st "fuse: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$RUN/s9_${T}_${TAG}_fuse.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"
st "fused sets: $(python -c "import yaml;d=yaml.safe_load(open('$M/model.yaml'));print('; '.join(f\"{c} {'+'.join(f['members'])}@{f['iou']}\" for c, f in d['fusion'].items()))")"
if [ -n "${S9_TTA12:-}" ]; then                        # the 12-view siblings of the passing members (S8 swap stage)
  python - "$M" "$S9_TTA12" > "$RUN/s9_${T}_${TAG}_tta12_card.log" 2>&1 <<'PY' || { st "tta12 card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
m, keys = Path(sys.argv[1]), sys.argv[2].split()
d = yaml.safe_load((m / "model.yaml").read_text())
added = []
for k in keys:
    m0 = d["members"].get(k + "_tta")
    if m0 is None:                                     # the member did not pass rule 3
        continue
    d["members"][k + "_tta12"] = {"model": m0["model"], "ckpt": m0["ckpt"], "tta": "flip4+yaw+z+scale", "tta_tag": "tta12",
                                  "postprocess": "test/postprocess_tta12.yaml"}
    added.append(k + "_tta12")
(m / "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print("12-view siblings:", " ".join(added) or "none")
PY
  st "$(cat "$RUN/s9_${T}_${TAG}_tta12_card.log")"
  if ! grep -q "siblings: none" "$RUN/s9_${T}_${TAG}_tta12_card.log"; then
    run fuse_tta12 python common/tools/route_predictions.py fuse $M --max-members 3 --pooled-rule --swap-variant tta12 "${FUSEX[@]}"
    st "fuse tta12: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$RUN/s9_${T}_${TAG}_fuse_tta12.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"
    st "fused sets: $(python -c "import yaml;d=yaml.safe_load(open('$M/model.yaml'));print('; '.join(f\"{c} {'+'.join(f['members'])}@{f['iou']}\" for c, f in d['fusion'].items()))")"
  fi
fi
if [ "$T" = lumpi ]; then
  python - "$REF" "$M" > "$RUN/s9_${T}_${TAG}_completion.log" 2>&1 <<'PY' || { st "completion FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
src, m = sys.argv[1:3]
r = yaml.safe_load(Path(src, "model.yaml").read_text())
d = yaml.safe_load(Path(m, "model.yaml").read_text())
d["budget"], d["tail_copies"] = r["budget"], r["tail_copies"]       # the reference's floors and copies (S8 U1/S8.3)
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print("budget", d["budget"], "tail copies", d["tail_copies"])
PY
  run freeze_rare python common/tools/freeze_classes.py $M --from $REF Bicycle Motorcycle Bus
  run validate python common/tools/route_predictions.py validate $M
else
  run budget python common/tools/route_predictions.py budget $M --pooled
  run tail python common/tools/route_predictions.py tail $M
  run sparse python common/tools/route_predictions.py sparse $M
fi
python common/tools/s7_check.py check $T $M $REF > "$RUN/s9_${T}_${TAG}_final_check.log" 2>&1 || { st "final check FAILED"; exit 1; }
FROZEN=$(grep -h '^FROZEN' "$RUN/s9_${T}_${TAG}_final_check.log" | cut -d' ' -f2-)
st "final check vs $(basename $REF): $(grep -vh '^FROZEN' "$RUN/s9_${T}_${TAG}_final_check.log" | cut -c1-200 | tr '\n' ';')"
if [ -n "$FROZEN" ]; then
  cp $M/model.yaml "$RUN/s9_${T}_${TAG}_card_before_freeze.yaml"
  run freeze python common/tools/freeze_classes.py $M --from $REF $FROZEN
  python -c "import sys,yaml;a,b=(yaml.safe_load(open(f)) for f in sys.argv[1:]);sys.exit(0 if a==b else 1)" \
    "$RUN/s9_${T}_${TAG}_card_before_freeze.yaml" $M/model.yaml && st "freeze changed nothing: validation kept" \
    || run validate_final python common/tools/route_predictions.py validate $M
fi
NC=$(python -c "import sys;sys.path.insert(0,'common');from bdc26.config import load_track;print(len(load_track('$T')['classes_with_test_gt']))")
if [ "$(echo $FROZEN | wc -w)" -ge "$NC" ]; then st "every class frozen: $NAME equals $(basename $REF); $TAG is not built"; st "DONE"; exit 0; fi
if [ -n "${S9_FRAMES:-}" ]; then                       # rule 4, last clause: the frames' generator must train a used member
  if ! python - "$M" "$S9_FRAMES" <<'PY'
import sys, yaml
from pathlib import Path
sys.path.insert(0, "common/tools")
from route_predictions import used_members
m, frames = Path(sys.argv[1]), sys.argv[2]
d = yaml.safe_load((m / "model.yaml").read_text())
gens = {frames, frames + "d2"}                           # the corpus and its second generator draw (same configuration)
corpora = lambda k: {c.strip() for c in str(yaml.safe_load((m.parent / d["members"][k]["model"] / "model.yaml").read_text())["data"]["train"]).split("+")}
used = [k for k in used_members(d) if corpora(k) & gens]   # a draw bag lists both draws (pcdet/g1-v6+pcdet/g1-v6d2)
print("v6-trained members in use:", used)
sys.exit(0 if used else 1)
PY
  then
    cp $REF/test/synthetic_ids.txt $M/test/synthetic_ids.txt; RFROM=(--realism-from $REF)
    python -c "import sys,yaml;p=sys.argv[1]+'/model.yaml';d=yaml.safe_load(open(p));d['realism_frames']=yaml.safe_load(open(sys.argv[2]+'/model.yaml'))['realism_frames'];open(p,'w').write(yaml.safe_dump(d,sort_keys=False))" $M $REF
    st "no member trained on $S9_FRAMES is used: the reference's realism frames are kept (rule 4)"
  fi
fi
G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh $TAG > "$RUN/s9_${T}_${TAG}_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
st "packaged $Z"
if [ "$T" = lumpi ] && [ -n "${S9_MAX_BOXES:-}" ]; then   # rule 1(b): the Person copy threshold of this route
  python common/tools/s9_copies_fit.py lumpi $M --max-boxes $S9_MAX_BOXES --write > "$RUN/s9_${T}_${TAG}_copies_fit.log" 2>&1 \
    || { st "copies fit FAILED"; exit 1; }
  CF=$(tail -n 1 "$RUN/s9_${T}_${TAG}_copies_fit.log"); st "copies fit: $CF"
  if [ "${CF%% *}" = SET ]; then
    run validate_copies python common/tools/route_predictions.py validate $M
    python common/tools/s7_check.py check $T $M $REF > "$RUN/s9_${T}_${TAG}_final_check_copies.log" 2>&1 || { st "final check FAILED"; exit 1; }
    F2=$(grep -h '^FROZEN' "$RUN/s9_${T}_${TAG}_final_check_copies.log" | cut -d' ' -f2-)
    st "final check after the copy fit: $(grep -vh '^FROZEN' "$RUN/s9_${T}_${TAG}_final_check_copies.log" | cut -c1-200 | tr '\n' ';')"
    [ "$F2" = "$FROZEN" ] || { st "the copy fit changed the frozen classes ($FROZEN -> $F2): stopped for review"; exit 1; }
    G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
    CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh $TAG > "$RUN/s9_${T}_${TAG}_package2.log" 2>&1 || { st "package FAILED"; exit 1; }
    Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
    st "packaged again with the fitted copies: $Z"
  fi
fi
python common/tools/check_submission.py --track $T $Z --official > "$RUN/s9_${T}_${TAG}_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/s9_${T}_${TAG}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
python common/tools/scorecard.py $M --vs $REF --bootstrap 200 "${RFROM[@]}" "${SCX[@]}" > "$RUN/s9_${T}_${TAG}_scorecard.log" 2>&1 \
  && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py $M --tag $TAG --write-script > "$RUN/s9_${T}_${TAG}_reproduce.log" 2>&1 || true
python common/tools/reproduce_validation.py $M --tag $TAG --write-script > "$RUN/s9_${T}_${TAG}_reproduce_val.log" 2>&1 || true
st "projection vs $(basename $REF): $(python common/tools/s7_check.py projection $T $M $REF)"
st "DONE"
