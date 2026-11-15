#!/usr/bin/env bash
# Release 10.5 (record docs/decisions/2026-11-14-s10-10.5-final-push.md): build, gate and package the 10.5 systems. The
# functions of s10_3_build.sh are reused (sourced with S10_3_LIB=1); no step here selects anything.
#   V2X retrained line: V3, V3p = V3 + PV, V3x, V3xp = V3x + PV (Section 3; rules of Section 5):
#     bash common/pipeline/launch.sh <run> s105v2x common/pipeline/s10_5_build.sh <run> v2x
#   View-set swap (L9 on L8, V5 on V4): probe, validate, the class rule (common/tools/s10_5_view_swap.py), then the build;
#   optional members get 12-view tuning jobs first, on the second trainer half to finish (deadline 14:30 UTC):
#     bash common/pipeline/launch.sh <run> s105l9 common/pipeline/s10_5_build.sh <run> swap lumpi routed-s10-4-l8 routed-s10-5-l9 L9 <L8 zip> \
#       pointpillars-ros-g1v6 pointpillars-ros-g1v6d2 voxelnext-rosf-g1v6d2
#     bash common/pipeline/launch.sh <run> s105v5 common/pipeline/s10_5_build.sh <run> swap v2x routed-s10-4-v4 routed-s10-5-v5 V5 <V4 zip>
# Events: "S10-5 <track> <system>: ..." in <run>/events.txt; logs <run>/s105_<system>_<step>.log.
RUN=$1; MODE=$2
TT=v2x; { [ "$MODE" = swap ] || [ "$MODE" = addmember ] || [ "$MODE" = p ]; } && TT=$3
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
export S10_3_LIB=1
source "$REPO/common/pipeline/s10_3_build.sh" "$RUN" "$TT"
st() { ev "S10-5 $T $SYS: $*"; }
lg() { echo "$RUN/s105_${SYS}_$1.log"; }
REC=docs/decisions/2026-11-14-s10-10.5-final-push.md

package4() {      # system tag frames same-frames-zip nulls: package, kit check, audit, scorecard, reproduction scripts
  local S=$1 TAG=$2 FR=$3 SAME=$4 NULLS=$5 MD=model-$T-track/$1 NUL=()
  [ -n "$NULLS" ] && NUL=(--nulls "$NULLS")
  run package python common/tools/package_submission.py "$MD" --tag "$TAG" --pred "$MD/test/output/predictions.json" \
    --synthetic "$FR" --syn-split val --syn-list "$MD/test/synthetic_ids.txt" "${NUL[@]}" --team KarmaRV \
    --ckpt "S10-5 $S: $(python -c "import yaml;print(yaml.safe_load(open('$MD/model.yaml'))['status'])")" \
    --local-scores "$MD/validation/results/local_scores.json" || return 1
  local SD; SD=$(ls -d "$MD"/submissions/*_"$TAG" | tail -n 1)
  run kitcheck python common/tools/check_submission.py --track "$T" "$SD/submission.zip" --official || return 1
  st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"|"score_realism"' "$(lg kitcheck)" | tr -s ' ' | tr '\n' ' ')"
  run audit python common/tools/s10_2_audit_upload.py "$SD" --same-frames-as "$SAME" || return 1
  st "audit: $(tail -n 1 "$(lg audit)")"
  local JX=(); [ "$T" = lumpi ] && JX=(--judge Van)
  run scorecard python common/tools/scorecard.py "$MD" --vs "$PARENT_DIR" --bootstrap 200 --realism "${JX[@]}" || true
  python common/tools/reproduce_submission.py "$MD" --tag "$TAG" --write-script > "$(lg reproduce)" 2>&1; st "reproduction: $(grep -E 're-merge' "$(lg reproduce)" | cut -c1-200)"
  python common/tools/reproduce_validation.py "$MD" --tag "$TAG" --write-script > "$(lg reproduce_val)" 2>&1 || true
  st "packaged $SD/$(python -c "import json;print(json.load(open('$SD/manifest.json'))['upload_file']['name'])")"
}

rule_line() {     # the rule-14 level and pooled delta of SYS against R
  local G; G=$(lg "grouped_vs_$1")
  echo "$(head -n 1 "$G" | sed 's/^[^:]*: //' | awk '{print $1}') $(grep -oE "pooled mAP delta [+-][0-9.]+" "$G" | head -n 1 | awk '{print $4}')"
}

p_build() {       # system parent tag parent-zip [extra systems to compare]: a P-type system end to end
  SYS=$1; local PARENT=$2 TAG=$3 PZ=$4; shift 4; PARENT_DIR=model-$T-track/$PARENT
  local MD=model-$T-track/$SYS
  run validate python common/tools/route_predictions.py validate "$MD" || return 1
  run clean python common/tools/clean_check.py "$MD" || { st "rules 1/1b FAILED: $(tail -n 2 "$(lg clean)" | tr '\n' ' ')"; return 1; }
  st "rules 1 and 1b: $(grep -E '^(FRAMES|PASS)' "$(lg clean)" | tr '\n' ' ' | cut -c1-300)"
  gates "$SYS" "$PARENT" "$@"
  for f in "$PARENT_DIR"/test/output/predictions_*.json; do cp -p "$f" "$MD/test/output/"; done
  run merge merge_kit "$SYS" || return 1
  local NB; NB=$(python -c "import json;print(sum(len(v) for v in json.load(open('$MD/test/output/predictions.json')).values()))")
  st "test boxes $NB$([ "$T" = lumpi ] && echo " (budget $MAXBOX)")"
  if [ "$T" = lumpi ] && [ "$NB" -gt $MAXBOX ]; then st "over the box budget: not packaged"; return 1; fi
  local FR NULLS=""
  FR=$(python -c "import json;print(json.load(open('$(dirname "$PZ")/manifest.json'))['synthetic_source'])")
  [ "$T" = v2x ] && case $FR in *aw) NULLS=0;; esac      # the calibrated corpus stores the no-returns
  package4 "$SYS" "$TAG" "$FR" "$PZ" "$NULLS" || return 1
  local L; L=$(rule_line "$PARENT"); st "rule 14 vs $PARENT: ${L% *}, pooled mAP delta ${L#* }"
}

pv_card() {       # base system, new system: the base card (as built) plus PV (final_adjust of routed-s10-4-v4)
  local B=model-v2x-track/$1 M=model-v2x-track/$2
  python - "$B" "$M" "$REC" <<'PY' || return 1
import shutil, sys, yaml
from pathlib import Path
b, m, rec = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
card = yaml.safe_load((b / "model.yaml").read_text())
card["final_adjust"] = yaml.safe_load(Path("model-v2x-track/routed-s10-4-v4/model.yaml").read_text())["final_adjust"]
cand = {"routed-s10-5-v3p": "V3p", "routed-s10-5-v3xp": "V3xp"}[m.name]
card.update({"name": m.name, "strategy": "S10-5", "candidate": cand, "derived_from": b.name,
             "status": f"S10-5 {cand}: {b.name} as built plus PV (final_adjust of routed-s10-4-v4) ({rec})",
             "notes": f"S10-5 {cand} ({rec}): {b.name}'s card unchanged plus PV appended as the last stage; its "
                      "members' kit predictions and its 50 frames reused.\n"})
for sub in ("validation/output", "validation/results", "test/output", "train"):
    (m / sub).mkdir(parents=True, exist_ok=True)
for f in ("make_submission.sh", "synthetic_ids.txt"):
    shutil.copy2(b / "test" / f, m / "test" / f)
(m / "model.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
PY
}

HO="S10-4 (release 10.4): V3x's 7 V2X retrainings"     # the event that queued the V2X retraining (trainA4, trainB4)
N0=$(grep -n "$HO" "$E" | tail -n 1 | cut -d: -f1)
ndone() { tail -n +"$N0" "$E" | grep -cE "TRAIN_WORKER_DONE train[AB]4$"; }

claim_gpu() {     # an idle GPU (<= 1000 MiB in use) claimed with a lock directory; prints its index
  local g
  while true; do
    for g in 0 1 2 3 4 5 6 7; do
      if [ "$(nvidia-smi -i "$g" --query-gpu=memory.used --format=csv,noheader,nounits)" -le 1000 ] && mkdir "$RUN/gpulock_$g" 2>/dev/null; then
        echo "$g"; return
      fi
    done
    sleep 30
  done
}
release_gpu() { rmdir "$RUN/gpulock_$1" 2>/dev/null; }
kit_one() {       # system member: one member's kit predictions alone on an idle GPU (a shared GPU changes digits)
  local C G rc; C=$(kit_member "model-$T-track/$1" "$2"); G=$(claim_gpu)
  CUDA_VISIBLE_DEVICES=$G bash -c "$C" > "$(lg "kit_$2")" 2>&1; rc=$?; release_gpu "$G"
  [ $rc = 0 ] || st "kit predictions of $2 FAILED (log $(lg "kit_$2"))"
  return $rc
}
used_of() { python -c "import sys,yaml;sys.path.insert(0,'common/tools');from route_predictions import used_members;print(' '.join(used_members(yaml.safe_load(open('model-$T-track/$1/model.yaml')))))"; }
predict_kit() {   # 10.5 (replaces s10_3_build.sh's): every used member alone on an idle GPU
  local n; for n in $(used_of "$1"); do kit_one "$1" "$n" || return 1; done; st "kit predictions done"
}

swap_build() {    # system parent tag parent-zip: the view-swap card end to end; unchanged members' kit predictions reused
  SYS=$1; local PARENT=$2 TAG=$3 PZ=$4; PARENT_DIR=model-$T-track/$PARENT
  local MD=model-$T-track/$SYS NEWK=() n
  run validate python common/tools/route_predictions.py validate "$MD" || return 1
  run clean python common/tools/clean_check.py "$MD" || { st "rules 1/1b FAILED: $(tail -n 2 "$(lg clean)" | tr '\n' ' ')"; return 1; }
  st "rules 1 and 1b: $(grep -E '^(FRAMES|PASS)' "$(lg clean)" | tr '\n' ' ' | cut -c1-300)"
  gates "$SYS" "$PARENT" ${EXTRA_CMP:-}
  for n in $(used_of "$SYS"); do
    if [ "$(python -c "import yaml;a=yaml.safe_load(open('$MD/model.yaml'))['members']['$n'];b=yaml.safe_load(open('$PARENT_DIR/model.yaml'))['members'].get('$n');print(int(a==b))")" = 1 ] \
       && [ -s "$PARENT_DIR/test/output/predictions_$n.json" ]; then cp -p "$PARENT_DIR/test/output/predictions_$n.json" "$MD/test/output/"
    else NEWK+=("$n"); fi
  done
  st "kit predictions: reused from $PARENT except ${NEWK[*]}"
  for n in "${NEWK[@]}"; do kit_one "$SYS" "$n" || return 1; done
  run merge merge_kit "$SYS" || return 1
  local NB; NB=$(python -c "import json;print(sum(len(v) for v in json.load(open('$MD/test/output/predictions.json')).values()))")
  st "test boxes $NB$([ "$T" = lumpi ] && echo " (budget $MAXBOX)")"
  if [ "$T" = lumpi ] && [ "$NB" -gt $MAXBOX ]; then st "over the box budget: not packaged"; return 1; fi
  local FR; FR=$(python -c "import json;print(json.load(open('$(dirname "$PZ")/manifest.json'))['synthetic_source'])")
  package4 "$SYS" "$TAG" "$FR" "$PZ" "" || return 1
}

if [ "$MODE" = swap ]; then
  PARENT=$4; NAME=$5; CAND=$6; PZ=$7; shift 7; EXTRA=("$@")
  SYS=$NAME; MD=model-$T-track/$NAME
  if [ ${#EXTRA[@]} -gt 0 ]; then
    # T12_GPUS (relaunch of 2026-11-14 13:35 UTC): run the 12-view jobs at once on these idle GPUs, with deadline
    # T12_DEADLINE, instead of waiting for the second trainer half (it would have left them 25 minutes)
    DLS=${T12_DEADLINE:-2026-11-14 14:30}; DL=$(date -u -d "$DLS" +%s)
    if [ -n "${T12_GPUS:-}" ]; then
      st "relaunched: 12-view tuning of ${EXTRA[*]} at once on idle GPUs $T12_GPUS (deadline $DLS UTC), then the class rule"
    else
      st "armed: 12-view tuning of ${EXTRA[*]} on the second trainer half to finish (deadline $DLS UTC), then the class rule"
      until [ "$(ndone)" -ge 2 ] || [ "$(utc)" -ge "$DL" ]; do sleep 120; done
    fi
    if [ -n "${T12_GPUS:-}" ] || [ "$(ndone)" -ge 2 ]; then
      if [ -n "${T12_GPUS:-}" ]; then GP=$T12_GPUS; W="no trainer (idle GPUs)"
      else
        W=$(tail -n +"$N0" "$E" | grep -E "TRAIN_WORKER_DONE train[AB]4$" | tail -n 1 | awk '{print $NF}')
        case $W in trainA*) GP="1 3 5 7";; *) GP="0 2 4 6";; esac
      fi
      cp "$REPO/common/pipeline/s10_5_t12_job.sh" "$RUN/bin/s10_5_t12_job.sh"
      J=$RUN/jobs_tta12_${CAND}.txt; : > "$J"
      for m in "${EXTRA[@]}"; do qpush "$J" "bash $RUN/bin/s10_5_t12_job.sh $T $m"; done
      st "12-view tuning jobs (${#EXTRA[@]}) on GPUs $GP, freed by $W"
      for g in $GP; do bash "$REPO/common/pipeline/launch.sh" "$RUN" "t12$CAND$g" "$REPO/common/pipeline/gpu_queue.sh" "$RUN" "t12$CAND$g" "$J" "$g"; done
      for g in $GP; do until tail -n +"$N0" "$E" | grep -q "WORKER_DONE t12$CAND$g$" || [ "$(utc)" -ge "$DL" ]; do sleep 60; done; done
      st "12-view tuning jobs finished or at the deadline"
    else st "the trainers did not finish by the deadline: the class rule runs on the existing 12-view outputs"; fi
  fi
  run probe python common/tools/s10_5_view_swap.py probe "$T" "$PARENT" "$NAME" --candidate "$CAND" || { st "nothing to swap: no $CAND"; st "DONE"; exit 0; }
  st "probe: $(head -n 2 "$(lg probe)" | tr '\n' ' ' | cut -c1-400)"
  run probe_validate python common/tools/route_predictions.py validate "$MD" || { st "STOPPED"; exit 1; }
  python common/tools/s10_5_view_swap.py decide "$T" "$PARENT" "$NAME" --candidate "$CAND" > "$(lg decide)" 2>&1; RC=$?
  st "class rule: $(tr '\n' '|' < "$(lg decide)" | tr -s ' ' | cut -c1-900)"
  if [ $RC != 0 ]; then st "no class passes the class rule: no $CAND (the probe card stays for the record)"; st "DONE"; exit 0; fi
  if swap_build "$NAME" "$PARENT" "s10-5-$(echo "$CAND" | tr 'A-Z' 'a-z')" "$PZ"; then
    L=$(rule_line "$PARENT"); LEVEL=${L% *}; DELTA=${L#* }
    if { [ "$LEVEL" = GO ] || [ "$LEVEL" = JUDGEMENT ]; } && python -c "import sys; sys.exit(0 if float('$DELTA') > 0 else 1)"; then
      st "UPLOAD RULE: PASS (rule 14 vs $PARENT $LEVEL, pooled mAP delta $DELTA): goes to the entrant"
    else st "UPLOAD RULE: FAIL (rule 14 vs $PARENT $LEVEL, pooled mAP delta $DELTA): not uploaded"; fi
  else st "STOPPED"; fi
  st "DONE"; exit 0
fi

if [ "$MODE" = p ]; then
  # Record Section 11 (attempt C3): a P-type system, the parent's card plus stage changes already written in the card;
  # the parent's member kit predictions and frames; upload rule against the scored entry UPV (rule 14 GO, or JUDGEMENT
  # with a pooled delta above 0).
  #   bash common/pipeline/launch.sh <run> s105l12c common/pipeline/s10_5_build.sh <run> p lumpi routed-s10-5-l12c \
  #     routed-s10-5-l9 s10-5-l12c <L9 zip> routed-s10-4-l8
  SYS=$4; PARENT=$5; TAG=$6; PZ=$7; UPV=$8
  if p_build "$SYS" "$PARENT" "$TAG" "$PZ" "$UPV"; then
    L=$(rule_line "$UPV"); LEVEL=${L% *}; DELTA=${L#* }
    if { [ "$LEVEL" = GO ] || [ "$LEVEL" = JUDGEMENT ]; } && python -c "import sys; sys.exit(0 if float('$DELTA') > 0 else 1)"; then
      st "UPLOAD RULE: PASS (rule 14 vs $UPV $LEVEL, pooled mAP delta $DELTA): goes to the entrant"
    else st "UPLOAD RULE: FAIL (rule 14 vs $UPV $LEVEL, pooled mAP delta $DELTA): not uploaded"; fi
  else st "STOPPED"; fi
  st "DONE"; exit 0
fi

if [ "$MODE" = addmember ]; then
  # Record Section 10 (the architecture arm; rules written before any result): the parent card plus new members (plain
  # and 4-view), `extend`, `fuse` (up to 3 members, the 6.0 pooled rule; LUMPI: Person ranked on late-A, the Van judge),
  # LUMPI Bicycle, Motorcycle and Bus frozen at the parent (S9 rule 2), the per-class final check against the parent
  # (s7_check: failing classes frozen), then the build with the parent's frames; upload rule against the scored entry UPV.
  #   bash common/pipeline/launch.sh <run> s105l10 common/pipeline/s10_5_build.sh <run> addmember lumpi routed-s10-5-l9 \
  #     routed-s10-5-l10 L10 <L9 zip> routed-s10-4-l8 tf6:transfusion-rosf-g1v6
  PARENT=$4; NAME=$5; CAND=$6; PZ=$7; UPV=$8; shift 8; SPECS=("$@")
  SYS=$NAME; MD=model-$T-track/$NAME; PD=model-$T-track/$PARENT
  st "armed: waits for the tuned plain and 4-view outputs of ${SPECS[*]}; parent $PARENT, upload rule against $UPV"
  # A member may be a seed bag (model.yaml type: bag): it is fused (bag_predictions.py, plain, 4-view and, with TTA12=1,
  # 12 views) once every seed has its tuned outputs. TTA12=1 also adds each member's 12-view sibling after the main fuse
  # (S8's swap stage, fuse --swap-variant tta12), as S9_TTA12 did.
  isbag() { python -c "import sys,yaml;sys.exit(0 if yaml.safe_load(open('model-$T-track/$1/model.yaml')).get('type')=='bag' else 1)"; }
  outs() { local m=$1 r=$2 S X; for S in val valB; do for X in "" _tta ${TTA12:+_tta12}; do
      [ -s "model-$T-track/$m/validation/output/pcdet_realval-v1_${S}_${r}_checkpoint_epoch_40${X}.json" ] || return 1; done; done; }
  seed_ok() { grep -qE "POST_DONE $T $1$" "$E" && outs "$1" run1; }
  ready() { local s m sd ok; for s in "${SPECS[@]}"; do m=${s#*:}
      if isbag "$m"; then
        outs "$m" bag && continue
        ok=1; for sd in $(python -c "import yaml;print(' '.join(yaml.safe_load(open('model-$T-track/$m/model.yaml'))['members']))"); do seed_ok "$sd" || ok=0; done
        [ $ok = 1 ] || return 1
        run "bag_$m" python common/tools/bag_predictions.py "model-$T-track/$m" || return 1
        if [ -n "${TTA12:-}" ]; then run "bag12_$m" python common/tools/bag_predictions.py "model-$T-track/$m" --tags _tta12 || return 1; fi
        st "bag $m: $(grep -E ': A' "$(lg "bag_$m")" | tr '\n' ';' | cut -c1-300)"
        outs "$m" bag || return 1
      else seed_ok "$m" || return 1; fi
    done; }
  until ready; do grep -qE "(POST_FAIL|TRAIN_FAIL) $T ${SPECS[0]#*:}" "$E" && { st "member failed: STOPPED"; exit 1; }; sleep 120; done
  mkdir -p "$MD/test/output" "$MD/validation/results" "$MD/validation/output" "$MD/train" "$MD/submissions"
  cp "$PD/test/make_submission.sh" "$PD/test/synthetic_ids.txt" "$MD/test/"
  RT=$PD/validation/results/route_table.json; [ -f "$RT" ] || RT=${RT_FROM:-model-$T-track/routed-c0}/validation/results/route_table.json
  cp "$RT" "$MD/validation/results/route_table.json"; st "route table from $RT (extend adds the members it lacks)"
  python - "$PD" "$MD" "$CAND" "${SPECS[@]}" > "$(lg card)" 2>&1 <<'PY' || { st "card FAILED"; st "STOPPED"; exit 1; }
import sys
from pathlib import Path
import yaml
pd, md, cand, specs = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4:]
d = yaml.safe_load((pd / "model.yaml").read_text())
ck = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"
for s in specs:
    k, m = s.split(":")
    c = ck.replace("/run1/", "/bag/") if yaml.safe_load((md.parent / m / "model.yaml").read_text()).get("type") == "bag" else ck
    d["members"][k] = {"model": m, "ckpt": c}
    d["members"][k + "_tta"] = {"model": m, "ckpt": c, "tta": "flip4+yaw+z", "postprocess": "test/postprocess_tta.yaml"}
d.update({"name": md.name, "strategy": "S10-5", "candidate": cand, "derived_from": pd.name,
          "status": f"S10-5 {cand}: {pd.name} plus {' '.join(specs)} (extend, fuse, rare classes frozen, final check; "
                    "docs/decisions/2026-11-14-s10-10.5-final-push.md Section 10)",
          "notes": f"S10-5 {cand} (record Section 10): the architecture arm; rules fixed before results.\n"})
(md / "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{md.name}: {len(d['members'])} members, added {' '.join(specs)}")
PY
  st "card: $(tr '\n' ';' < "$(lg card)")"
  FUSEX=(); [ "$T" = lumpi ] && FUSEX=(--late-rank Person --gate-top 3 --judge Van)
  run extend python common/tools/route_predictions.py extend "$MD" || { st "STOPPED"; exit 1; }
  run fuse python common/tools/route_predictions.py fuse "$MD" --max-members 3 --pooled-rule "${FUSEX[@]}" || { st "STOPPED"; exit 1; }
  st "fuse: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$(lg fuse)" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';' | cut -c1-600)"
  st "fused sets: $(python -c "import yaml;d=yaml.safe_load(open('$MD/model.yaml'));print('; '.join(f\"{c} {'+'.join(f['members'])}@{f['iou']}\" for c, f in d['fusion'].items()))" | cut -c1-600)"
  if [ -n "${TTA12:-}" ]; then
    python - "$MD" "${SPECS[@]}" > "$(lg tta12_card)" 2>&1 <<'PY' || { st "tta12 card FAILED"; st "STOPPED"; exit 1; }
import sys
from pathlib import Path
import yaml
md = Path(sys.argv[1]); d = yaml.safe_load((md / "model.yaml").read_text()); added = []
for s in sys.argv[2:]:
    k = s.split(":")[0]; m0 = d["members"][k + "_tta"]
    d["members"][k + "_tta12"] = {"model": m0["model"], "ckpt": m0["ckpt"], "tta": "flip4+yaw+z+scale", "tta_tag": "tta12",
                                  "postprocess": "test/postprocess_tta12.yaml"}
    added.append(k + "_tta12")
(md / "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print("12-view siblings:", " ".join(added))
PY
    st "$(cat "$(lg tta12_card)")"
    run fuse_tta12 python common/tools/route_predictions.py fuse "$MD" --max-members 3 --pooled-rule --swap-variant tta12 "${FUSEX[@]}" || { st "STOPPED"; exit 1; }
    st "fuse tta12: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$(lg fuse_tta12)" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';' | cut -c1-600)"
  fi
  if [ "$T" = lumpi ]; then run freeze_rare python common/tools/freeze_classes.py "$MD" --from "$PD" Bicycle Motorcycle Bus || { st "STOPPED"; exit 1; }; fi
  run validate_fused python common/tools/route_predictions.py validate "$MD" || { st "STOPPED"; exit 1; }
  python common/tools/s7_check.py check "$T" "$MD" "$PD" > "$(lg final_check)" 2>&1 || { st "final check FAILED"; st "STOPPED"; exit 1; }
  FROZEN=$(grep -h '^FROZEN' "$(lg final_check)" | cut -d' ' -f2-)
  st "final check vs $PARENT: $(grep -vh '^FROZEN' "$(lg final_check)" | cut -c1-200 | tr '\n' ';' | cut -c1-900)"
  if [ -n "$FROZEN" ]; then run freeze python common/tools/freeze_classes.py "$MD" --from "$PD" $FROZEN || { st "STOPPED"; exit 1; }; fi
  if python -c "import sys,yaml;a,b=(yaml.safe_load(open(f+'/model.yaml')) for f in sys.argv[1:]);k=('route','fusion','calibration','budget','final_adjust','tail_copies');sys.exit(0 if all((a.get(x) or None)==(b.get(x) or None) for x in k) else 1)" "$MD" "$PD"; then
    st "every class at $PARENT after the checks: no $CAND"; st "DONE"; exit 0; fi
  [ -n "${DRY:-}" ] && { st "dry run: stops before the build"; st "DONE"; exit 0; }
  if EXTRA_CMP=$UPV swap_build "$NAME" "$PARENT" "s10-5-$(echo "$CAND" | tr 'A-Z' 'a-z')" "$PZ"; then
    L=$(rule_line "$UPV"); LEVEL=${L% *}; DELTA=${L#* }
    if { [ "$LEVEL" = GO ] || [ "$LEVEL" = JUDGEMENT ]; } && python -c "import sys; sys.exit(0 if float('$DELTA') > 0 else 1)"; then
      st "UPLOAD RULE: PASS (rule 14 vs $UPV $LEVEL, pooled mAP delta $DELTA): goes to the entrant"
    else st "UPLOAD RULE: FAIL (rule 14 vs $UPV $LEVEL, pooled mAP delta $DELTA): not uploaded"; fi
  else st "STOPPED"; fi
  st "DONE"; exit 0
fi

# ---- V2X: V3, V3p, V3x, V3xp ----
SYS=routed-s10-3-v3; st "armed: waits for the first trainer half to finish, then runs V3's 12-view jobs on it"
until [ "$(ndone)" -ge 1 ]; do sleep 120; done
W=$(tail -n +"$N0" "$E" | grep -E "TRAIN_WORKER_DONE train[AB]4$" | head -n 1 | awk '{print $NF}')
case $W in trainA*) GP="1 3 5 7";; *) GP="0 2 4 6";; esac
J=$RUN/jobs_tta12_s105v2x.txt; : > "$J"
while read -r kind m; do [ "$kind" = t12 ] && qpush "$J" "bash $RUN/bin/t12f_job.sh v2x $m"; done < <(needs routed-s10-3-v3)
st "12-view jobs ($(wc -l < "$J")) on GPUs $GP, freed by $W"
for g in $GP; do bash "$REPO/common/pipeline/launch.sh" "$RUN" "t12y$g" "$REPO/common/pipeline/gpu_queue.sh" "$RUN" "t12y$g" "$J" "$g"; done
wait_ready routed-s10-3-v3
INCUMBENT=routed-c2r
if build_recipe routed-s10-3-v3 routed-c1a s10-3-v3 pcdet/g1-v6aw; then
  st "V3 built"; V3Z=$(ls model-v2x-track/routed-s10-3-v3/submissions/*_s10-3-v3/v2x_*_submission.zip | tail -n 1)
  pv_card routed-s10-3-v3 routed-s10-5-v3p && p_build routed-s10-5-v3p routed-s10-3-v3 s10-5-v3p "$V3Z" routed-c2r routed-s10-4-v4 \
    && st "V3p built" || st "V3p STOPPED"
else st "V3 STOPPED"; fi
SYS=routed-s10-3-v3x
DL=$(date -u -d "2026-11-14 22:00" +%s)
if wait_ready routed-s10-3-v3x "$DL"; then
  INCUMBENT=""
  if build_recipe routed-s10-3-v3x routed-c2r s10-3-v3x pcdet/g1-v6aw; then
    L=$(rule_line routed-c2r); DELTA=${L#* }
    st "G-D, V3x against V1: rule 14 ${L% *}, pooled mAP delta $DELTA"
    XZ=$(ls model-v2x-track/routed-s10-3-v3x/submissions/*_s10-3-v3x/v2x_*_submission.zip | tail -n 1)
    if pv_card routed-s10-3-v3x routed-s10-5-v3xp && p_build routed-s10-5-v3xp routed-s10-3-v3x s10-5-v3xp "$XZ" routed-c2r routed-s10-4-v4; then
      SYS=routed-s10-5-v3xp
      if python -c "import sys; sys.exit(0 if float('$DELTA') > -0.0027 else 1)"; then
        st "UPLOAD RULE: PASS (G-D pooled delta of V3x against V1 $DELTA > -0.0027): goes to the entrant"
      else st "UPLOAD RULE: FAIL (G-D pooled delta of V3x against V1 $DELTA <= -0.0027): not uploaded"; fi
    else st "V3xp STOPPED"; fi
  else st "V3x STOPPED"; fi
else st "V3x not tuned by 2026-11-14 22:00 UTC: V3p is the V2X fallback (rule 5)"; fi
SYS=routed-s10-5-v3xp; st "DONE"
