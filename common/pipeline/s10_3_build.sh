#!/usr/bin/env bash
# Release 10.3 (record docs/decisions/2026-11-13-s10-10.3-final-system.md): validate, gate and package the 10.3
# systems as soon as their retrained members are tuned. Every card is a scored parent's recipe made by
# common/tools/s10_3_recipe.py, so no step here selects anything; the steps measure, check and package.
#   LUMPI: L3 = routed-c0's recipe on the 14 B1 checkpoints, then L6 = L3 + P (final_adjust of routed-s10-2-l5).
#     bash common/pipeline/launch.sh <run> s103lumpi common/pipeline/s10_3_build.sh <run> lumpi
#   2026-11-13 (record Section 10): N1 stopped; the same flow on the re-cast-only corpus (L3q, then L6q = L3q + P):
#     bash common/pipeline/launch.sh <run> s103qlumpi common/pipeline/s10_3_build.sh <run> lumpi \
#       routed-s10-3-l3q routed-s10-3-l6q pcdet/g1-v6pq
#   V2X: V3 = routed-c1a's recipe (4 checkpoints), then V3x = routed-c2r's (V1, 1050253) recipe (7 checkpoints) if
#   its three extra draws are tuned by the deadline. Runs the members' 12-view jobs on the first half that stops training.
#     bash common/pipeline/launch.sh <run> s103v2x common/pipeline/s10_3_build.sh <run> v2x ["<hand-over event>"]
# Events: "S10-3 <track> <system>: ..." in <run>/events.txt; logs <run>/s103_<system>_<step>.log.
RUN=$1; T=$2
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
E=$RUN/events.txt
MAXBOX=38466                       # LUMPI: the box count of a zip the server has scored in time (S9 rule 1(b))
SYS=""
st() { ev "S10-3 $T $SYS: $*"; }
lg() { echo "$RUN/s103_${SYS}_$1.log"; }
run() { local N=$1; shift; if "$@" > "$(lg "$N")" 2>&1; then st "$N done"; else st "$N FAILED (log $(lg "$N"))"; return 1; fi; }

# the checkpoint models a card needs: "tuned <model>" for every model, "t12 <model>" for the 12-view ones
needs() {
  python - "model-$T-track/$1" <<'PY'
import sys, yaml
from pathlib import Path
sys.path.insert(0, "common/tools")
from route_predictions import used_members
d = Path(sys.argv[1]); card = yaml.safe_load((d / "model.yaml").read_text())
out = set()
for n in used_members(card):
    m = card["members"][n]
    mc = yaml.safe_load((d.parent / m["model"] / "model.yaml").read_text())
    seeds = mc["members"] if mc.get("type") == "bag" else [m["model"]]
    for s in seeds:
        out.add(f"tuned {s}")
        if m.get("tta_tag") == "tta12":
            out.add(f"t12 {s}")
print("\n".join(sorted(out)))
PY
}
tuned() { grep -qE "POST_DONE $T $1$" "$E"; }
has12() { local O=model-$T-track/$1/validation/output; ls "$O" 2>/dev/null | grep -qx "pcdet_.*_valB_run1_checkpoint_epoch_40_tta12[.]json"; }   # not the raw file (10.5 fix)
utc() { date -u +%s; }

wait_ready() {    # system [deadline epoch]: 0 when every member is tuned (and 12-view where needed), 1 at the deadline
  local S=$1 DL=${2:-0} k=0
  while true; do
    local miss=0 failed=""
    while read -r kind m; do
      if [ "$kind" = tuned ]; then tuned "$m" || { miss=1; grep -qE "POST_FAIL $T $m$" "$E" && failed="$failed $m"; }
      else has12 "$m" || miss=1; fi
    done < <(needs "$S")
    [ $miss = 0 ] && return 0
    if [ -n "$failed" ] && [ $((k % 60)) = 0 ]; then SYS=$S st "waiting: post-processing FAILED for$failed (rerun member_post.sh)"; fi
    [ "$DL" -gt 0 ] && [ "$(utc)" -ge "$DL" ] && return 1
    k=$((k + 1)); sleep 120
  done
}

bags() {          # the card's new bags, each fused for the view tags its members use
  python - "model-$T-track/$1" <<'PY'
import sys, yaml
from pathlib import Path
sys.path.insert(0, "common/tools")
from route_predictions import used_members
d = Path(sys.argv[1]); card = yaml.safe_load((d / "model.yaml").read_text())
tags = {}
for n in used_members(card):
    m = card["members"][n]
    if yaml.safe_load((d.parent / m["model"] / "model.yaml").read_text()).get("type") == "bag":
        tags.setdefault(m["model"], set()).add("_" + (m.get("tta_tag") or "tta") if m.get("tta") else "")
for b, t in sorted(tags.items()):
    print(b, " ".join(sorted(t)))
PY
}

kit_member() {    # one used member's kit predictions (as test/make_submission.sh does), on the GPU with most free memory
  local MD=$1 N=$2
  python - "$MD" "$N" <<'PY'
import sys, yaml, shlex
from pathlib import Path
md, n = Path(sys.argv[1]), sys.argv[2]
card = yaml.safe_load((md / "model.yaml").read_text()); m = card["members"][n]
mm = md.parent / m["model"]; out = md / "test" / "output" / f"predictions_{n}.json"
if yaml.safe_load((mm / "model.yaml").read_text()).get("type") == "bag":
    var = (m.get("tta_tag") or "tta") if m.get("tta") else "plain"
    cmd = ["python", "common/tools/bag_predictions.py", str(mm), "--kit", "--variant", var, "--out", str(out)]
else:
    cmd = ["python", "common/tools/pcdet_predict.py", str(mm), "--ckpt", str(mm / m["ckpt"]), "--frames", "kit", "--out", str(out)]
    if m.get("tta"):
        cmd += ["--tta", m["tta"], "--postprocess", str(mm / m.get("postprocess", "test/postprocess_tta.yaml"))]
print(shlex.join(cmd))
PY
}

predict_kit() {   # every used member's kit predictions, one at a time (a shared GPU can change inference digits)
  local S=$1 MD=model-$T-track/$1
  for n in $(python -c "import sys,yaml;sys.path.insert(0,'common/tools');from route_predictions import used_members;print(' '.join(used_members(yaml.safe_load(open('$MD/model.yaml')))))"); do
    local C; C=$(kit_member "$MD" "$n")
    local G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
    CUDA_VISIBLE_DEVICES=$G bash -c "$C" > "$(lg "kit_$n")" 2>&1 || { st "kit predictions of $n FAILED (log $(lg "kit_$n"))"; return 1; }
  done
  st "kit predictions done"
}

merge_kit() {     # merge the members' kit predictions with the card
  local MD=model-$T-track/$1 P=()
  for f in "$MD"/test/output/predictions_*.json; do n=$(basename "$f" .json); P+=(--pred "${n#predictions_}=$f"); done
  python common/tools/route_predictions.py merge "$MD" "${P[@]}" --out "$MD/test/output/predictions.json"
}

package() {       # system tag frames [same-frames-as zip]: package, kit check, audit, scorecard, reproduction scripts
  local S=$1 TAG=$2 FR=$3 SAME=${4:-} MD=model-$T-track/$1 NUL=()
  [ "$T" = v2x ] && NUL=(--nulls 0)      # the calibrated V2X corpus stores the no-returns; frames ship as stored
  run package python common/tools/package_submission.py "$MD" --tag "$TAG" --pred "$MD/test/output/predictions.json" \
    --synthetic "$FR" --syn-split val --syn-list "$MD/test/synthetic_ids.txt" "${NUL[@]}" --team KarmaRV \
    --ckpt "S10-3 $S: $(python -c "import yaml;print(yaml.safe_load(open('$MD/model.yaml'))['status'])")" \
    --local-scores "$MD/validation/results/local_scores.json" || return 1
  local SD; SD=$(ls -d "$MD"/submissions/*_"$TAG" | tail -n 1)
  run kitcheck python common/tools/check_submission.py --track "$T" "$SD/submission.zip" --official || return 1
  st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"|"score_realism"' "$(lg kitcheck)" | tr -s ' ' | tr '\n' ' ')"
  local SA=(); [ -n "$SAME" ] && SA=(--same-frames-as "$SAME")
  run audit python common/tools/s10_2_audit_upload.py "$SD" "${SA[@]}" || return 1
  st "audit: $(tail -n 1 "$(lg audit)")"
  local JX=(); [ "$T" = lumpi ] && JX=(--judge Van)
  run scorecard python common/tools/scorecard.py "$MD" --vs "$PARENT_DIR" --bootstrap 200 --realism "${JX[@]}" || true
  python common/tools/reproduce_submission.py "$MD" --tag "$TAG" --write-script > "$(lg reproduce)" 2>&1; st "reproduction: $(grep -E 're-merge' "$(lg reproduce)" | cut -c1-200)"
  python common/tools/reproduce_validation.py "$MD" --tag "$TAG" --write-script > "$(lg reproduce_val)" 2>&1 || true
  st "packaged $SD/$(python -c "import json;print(json.load(open('$SD/manifest.json'))['upload_file']['name'])")"
}

gates() {         # system, then the systems to compare with (the first is the parent)
  local S=$1; shift
  for R in "$@"; do
    python common/tools/s10_grouped_gate.py "model-$T-track/$S" "model-$T-track/$R" --go-p 0.8 > "$(lg "grouped_vs_$R")" 2>&1
    st "rule 14 vs $R: $(head -n 3 "$(lg "grouped_vs_$R")" | tr -s ' ' | tr '\n' ' ' | cut -c1-330)"
    python common/tools/s10_3_compare.py "model-$T-track/$S" "model-$T-track/$R" > "$(lg "compare_vs_$R")" 2>&1
    st "vs $R: $(tr '\n' ' ' < "$(lg "compare_vs_$R")" | cut -c1-400)"
  done
}

build_recipe() {  # system parent tag frames: the recipe system end to end
  SYS=$1; local PARENT=$2 TAG=$3 FR=$4; PARENT_DIR=model-$T-track/$PARENT
  local MD=model-$T-track/$SYS
  while read -r b tags; do
    run "bag_$b" python common/tools/bag_predictions.py "model-$T-track/$b" --tags $tags || return 1
  done < <(bags "$SYS")
  run validate python common/tools/route_predictions.py validate "$MD" || return 1
  run clean python common/tools/clean_check.py "$MD" || { st "rules 1/1b FAILED: $(tail -n 2 "$(lg clean)" | tr '\n' ' ')"; return 1; }
  st "rules 1 and 1b: $(grep -E '^(FRAMES|PASS)' "$(lg clean)" | tr '\n' ' ' | cut -c1-300)"
  gates "$SYS" "$PARENT" ${INCUMBENT:+"$INCUMBENT"}
  predict_kit "$SYS" || return 1
  run merge merge_kit "$SYS" || return 1
  if [ "$T" = lumpi ]; then          # S9 rule 1(b): the Person copy threshold re-derived for this route (C0's recipe)
    python common/tools/s9_copies_fit.py lumpi "$MD" --max-boxes $MAXBOX --write > "$(lg copies_fit)" 2>&1 || { st "copies fit FAILED"; return 1; }
    local CF; CF=$(tail -n 1 "$(lg copies_fit)"); st "copies fit: $CF"
    if [ "${CF%% *}" = SET ]; then
      run validate_copies python common/tools/route_predictions.py validate "$MD" || return 1
      run merge_copies merge_kit "$SYS" || return 1
      gates "$SYS" "$PARENT"
    fi
  fi
  package "$SYS" "$TAG" "$FR"
}

build_p() {       # L6: L3's card (after its copies fit) plus P, the members' kit predictions reused
  local BASE=$1; SYS=$2; local TAG=$3 FR=$4 PFROM=$5; PARENT_DIR=model-$T-track/routed-c0
  local MD=model-$T-track/$SYS BD=model-$T-track/$1
  python - "$BD" "$MD" "model-$T-track/$PFROM" <<'PY' || { st "card FAILED"; return 1; }
import sys, yaml
from pathlib import Path
b, m, p = (Path(x) for x in sys.argv[1:])
card = yaml.safe_load((b / "model.yaml").read_text())
cur = yaml.safe_load((m / "model.yaml").read_text())
card.update({k: cur[k] for k in ("name", "candidate", "derived_from", "status", "notes")})
card["final_adjust"] = yaml.safe_load((p / "model.yaml").read_text())["final_adjust"]
(m / "model.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
PY
  st "card: $BASE's card (copies fit included) plus P from $PFROM"
  run validate python common/tools/route_predictions.py validate "$MD" || return 1
  run clean python common/tools/clean_check.py "$MD" || return 1
  gates "$SYS" routed-c0 "$BASE" routed-s10-2-l5
  for f in "$BD"/test/output/predictions_*.json; do cp -p "$f" "$MD/test/output/"; done
  run merge merge_kit "$SYS" || return 1
  local NB; NB=$(python -c "import json;print(sum(len(v) for v in json.load(open('$MD/test/output/predictions.json')).values()))")
  st "test boxes $NB (budget $MAXBOX)"
  [ "$NB" -le $MAXBOX ] || { st "over the box budget: not packaged"; return 1; }
  local BZ; BZ=$(ls "$BD"/submissions/*/lumpi_*_submission.zip | tail -n 1)
  package "$SYS" "$TAG" "$FR" "$BZ"
}

if [ "${S10_3_LIB:-0}" = 1 ]; then
  :                                  # sourced for its functions (common/pipeline/s10_3_l7.sh)
elif [ "$T" = lumpi ]; then
  L3=${3:-routed-s10-3-l3}; L6=${4:-routed-s10-3-l6}; FRL=${5:-pcdet/g1-v6n1}
  SYS=$L3; st "armed: waits for the 14 checkpoints of $L3 (8-view) and their six 12-view jobs"
  wait_ready "$L3"
  st "every member tuned; $L3 build starts"
  if build_recipe "$L3" routed-c0 "${L3#routed-}" "$FRL"; then
    build_p "$L3" "$L6" "${L6#routed-}" "$FRL" routed-s10-2-l5 && st "DONE" || st "$L6 STOPPED"
  else st "$L3 STOPPED"; fi
else
  HO=${3:-S10-2 hand-over complete}
  SYS=routed-s10-3-v3; st "armed: waits for c1a's 4 checkpoints (8-view), then runs their 12-view jobs on a free half"
  until grep -q "$HO" "$E"; do sleep 120; done
  N0=$(grep -n "$HO" "$E" | tail -n 1 | cut -d: -f1)
  until tail -n +"$N0" "$E" | grep -qE "TRAIN_WORKER_DONE train[AB][34]$"; do sleep 120; done
  W=$(tail -n +"$N0" "$E" | grep -E "TRAIN_WORKER_DONE train[AB][34]$" | head -n 1 | awk '{print $NF}')
  case $W in trainA*) GP="1 3 5 7";; *) GP="0 2 4 6";; esac
  J=$RUN/jobs_tta12_s103v2x.txt; : > "$J"
  while read -r kind m; do [ "$kind" = t12 ] && qpush "$J" "bash $RUN/bin/t12f_job.sh v2x $m"; done < <(needs routed-s10-3-v3)
  st "12-view jobs ($(wc -l < "$J")) on GPUs $GP, freed by $W"
  for g in $GP; do bash "$REPO/common/pipeline/launch.sh" "$RUN" "t12v$g" "$REPO/common/pipeline/gpu_queue.sh" "$RUN" "t12v$g" "$J" "$g"; done
  wait_ready routed-s10-3-v3
  INCUMBENT=routed-c2r
  if build_recipe routed-s10-3-v3 routed-c1a s10-3-v3 pcdet/g1-v6aw; then st "V3 DONE"; else st "V3 STOPPED"; fi
  SYS=routed-s10-3-v3x
  DL=$(date -u -d "2026-11-15 08:00" +%s)
  if wait_ready routed-s10-3-v3x "$DL"; then
    INCUMBENT=""
    if build_recipe routed-s10-3-v3x routed-c2r s10-3-v3x pcdet/g1-v6aw; then st "DONE"; else st "V3x STOPPED"; fi
  else st "not tuned by 2026-11-15 08:00 UTC: V3x dropped, V3 is the V2X 10.3 system"; fi
fi
