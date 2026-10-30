#!/usr/bin/env bash
# S8 last day, LUMPI (rules in docs/decisions/2026-10-29-s8-last-day-strategy.md Section 6, rule 8 for the late go;
# written before this ran; runs detached, never uploads or commits):
#   bash common/pipeline/launch.sh <run> s8_u1 common/pipeline/s8_portfolio.sh <run> u1
#   bash common/pipeline/launch.sh <run> s8_u1pkg common/pipeline/s8_portfolio.sh <run> u1pkg   # after the kit-time fallback
#   bash common/pipeline/launch.sh <run> s8_u2 common/pipeline/s8_portfolio.sh <run> u2
#   bash common/pipeline/launch.sh <run> s8_v2x common/pipeline/s8_portfolio.sh <run> v2x
#   bash common/pipeline/launch.sh <run> s8_u3 common/pipeline/s8_portfolio.sh <run> u3       # S8.2 LUMPI s8c
#   bash common/pipeline/launch.sh <run> s8_v2x2 common/pipeline/s8_portfolio.sh <run> v2x2   # S8.2 V2X s8w
#   bash common/pipeline/launch.sh <run> s8_u4 common/pipeline/s8_portfolio.sh <run> u4 <spec.json>     # S8.3 LUMPI s8d
#   bash common/pipeline/launch.sh <run> s8_v2x3 common/pipeline/s8_portfolio.sh <run> v2x3 <spec.json> # S8.3 V2X s8x
# u1: routed-g11 = the entry routed-g10 plus the non-negative completion (floors above 0.01 lowered to 0.01, Person
#     tail copies of the boxes scored >= t); package s8a, official kit check, scorecard, reproduction scripts
# u2: routed-g11b = routed-g11 plus the _tta12 siblings of the 7 TTA members in the unfrozen classes' fusions
#     (validation/tune_and_eval.sh --tta flip4+yaw+z+scale --tta-tag tta12 --reuse-raw, run before this); fuse
#     --swap-variant: one candidate per class through the 6.0 pooled rule (Person ranked on late-A); U1's floors and
#     copies; final check against routed-g11 (common/tools/s7_check.py), failing classes frozen at routed-g11; package
#     s8b, kit check, scorecard, reproduction scripts, projections against routed-g11 and the entry
# v2x: V2X U2, model-v2x-track/routed-g13 = the entry routed-g12 with the _tta12 siblings of its 4 non-bag TTA members
#     swapped in as above, budget --pooled, tail copies and the sparse stage re-derived (as S7.6), final check against
#     the entry, failing classes frozen at the entry; package s8v
# Events: <run>/events.txt (S8 <stage>: ...); logs <run>/s8_<stage>_*.log
RUN=$1; STAGE=$2
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
L=model-lumpi-track
ENTRY=$L/routed-g10; U1=$L/routed-g11; U2=$L/routed-g11b
st() { ev "S8 $STAGE: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/s8_${STAGE}_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }

package() {                                             # model folder, tag, reference for the scorecard [, track]
  local M=$1 TAG=$2 REF=$3 T=${4:-lumpi} G="" SCX=(--judge Van) E=$ENTRY
  [ "$T" = v2x ] && { SCX=(); E=$REF; }
  until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
  CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh $TAG > "$RUN/s8_${STAGE}_package.log" 2>&1 || { st "package FAILED"; exit 1; }
  local Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
  st "packaged $Z"
  python common/tools/check_submission.py --track $T $Z --official > "$RUN/s8_${STAGE}_check.log" 2>&1 \
    && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/s8_${STAGE}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
  python common/tools/scorecard.py $M --vs $REF --bootstrap 200 --realism-from $E "${SCX[@]}" > "$RUN/s8_${STAGE}_scorecard.log" 2>&1 \
    && st "scorecard done" || st "scorecard FAILED"
  python common/tools/reproduce_submission.py $M --tag $TAG --write-script > "$RUN/s8_${STAGE}_reproduce.log" 2>&1 || true
  python common/tools/reproduce_validation.py $M --tag $TAG --write-script > "$RUN/s8_${STAGE}_reproduce_val.log" 2>&1 || true
  st "projection vs $(basename $E): $(python common/tools/s7_check.py projection $T $M $E)"
}

if [ "$STAGE" = u1 ]; then
  mkdir -p $U1/test $U1/validation/results $U1/train $U1/submissions
  cp $ENTRY/test/make_submission.sh $ENTRY/test/synthetic_ids.txt $U1/test/
  cp $ENTRY/validation/results/route_table.json $ENTRY/validation/results/fusion_table.json $U1/validation/results/
  python - "$ENTRY" "$U1" > "$RUN/s8_u1_card.log" 2>&1 <<'PY' || { st "card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
src, m = sys.argv[1:3]
d = yaml.safe_load(Path(src, "model.yaml").read_text())
d["name"] = Path(m).name
d["strategy"] = "S8"
d["status"] = ("S8 U1: the entry routed-g10 plus the non-negative completion, floors above 0.01 lowered to 0.01 and Person "
               "tail copies of the boxes scored >= 0.0508 (docs/decisions/2026-10-29-s8-last-day-strategy.md)")
d["notes"] = "S8 U1 (docs/decisions/2026-10-29-s8-last-day-strategy.md, rules 2 and 8).\n"
for c, f in d["budget"].items():                        # rule 2: every floor above 0.01 to 0.01; Unknown has no test GT
    if c != "Unknown" and f > 0.01:
        d["budget"][c] = 0.01
d["tail_copies"] = {"Person": {"r": 0.2, "n": 4, "min_score": 0.0508}}   # t: median Person score of routed-g10 on realval-A
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: budget {d['budget']}, tail copies {d['tail_copies']}")
PY
  st "$(basename $U1) created ($(tr '\n' ';' < "$RUN/s8_u1_card.log"))"
  run validate python common/tools/route_predictions.py validate $U1
  python common/tools/s7_check.py check lumpi $U1 $ENTRY > "$RUN/s8_u1_final_check.log" 2>&1 \
    && st "check vs entry (report only, rule 2 exempts the completion): $(grep -vh '^FROZEN' "$RUN/s8_u1_final_check.log" | cut -c1-160 | tr '\n' ';')"
  package $U1 s8a $ENTRY
  st "DONE"
  exit 0
fi

if [ "$STAGE" = u1pkg ]; then                           # rule 2 kit-time fallback applied to the U1 card: package again
  package $U1 s8a $ENTRY
  st "DONE"
  exit 0
fi

if [ "$STAGE" = u2 ]; then
  mkdir -p $U2/test $U2/validation/results $U2/train $U2/submissions
  cp $U1/test/make_submission.sh $U1/test/synthetic_ids.txt $U2/test/
  cp $U1/validation/results/route_table.json $U2/validation/results/
  python - "$U1" "$U2" > "$RUN/s8_u2_card.log" 2>&1 <<'PY' || { st "card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
src, m = sys.argv[1:3]
d = yaml.safe_load(Path(src, "model.yaml").read_text())
d["name"] = Path(m).name
d["status"] = ("S8 U2: routed-g11 with the 12-view (flip4+yaw+z+scale) siblings swapped into the unfrozen classes' "
               "fusions, gated per class (docs/decisions/2026-10-29-s8-last-day-strategy.md)")
d["notes"] = "S8 U2 (docs/decisions/2026-10-29-s8-last-day-strategy.md, rules 3, 4 and 8).\n"
for k in ("pp4_tta", "vrros4s2_tta", "pvros_tta", "pvros4d2_tta", "ppros_tta", "vrros4_tta", "g1_tta"):
    m0 = d["members"][k]
    d["members"][k + "12"] = {"model": m0["model"], "ckpt": m0["ckpt"], "tta": "flip4+yaw+z+scale", "tta_tag": "tta12",
                              "postprocess": "test/postprocess_tta12.yaml"}
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: {len(d['members'])} members")
PY
  st "$(basename $U2) created ($(tr '\n' ';' < "$RUN/s8_u2_card.log"))"
  run fuse python common/tools/route_predictions.py fuse $U2 --pooled-rule --swap-variant tta12 \
    --classes Person Car Truck Van --late-rank Person --gate-top 3
  st "swap: $(grep -h 'swap candidates' "$RUN/s8_u2_fuse.log" | sed 's/^ *//')"
  st "fuse: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$RUN/s8_u2_fuse.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"
  python - "$U1" "$U2" > "$RUN/s8_u2_completion.log" 2>&1 <<'PY' || { st "completion FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
src, m = sys.argv[1:3]
u1 = yaml.safe_load(Path(src, "model.yaml").read_text())
d = yaml.safe_load(Path(m, "model.yaml").read_text())
d["budget"], d["tail_copies"] = u1["budget"], u1["tail_copies"]      # rule 8: U1's floors and copies (fuse rewrites the tail)
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print("budget", d["budget"], "tail copies", d["tail_copies"])
PY
  run freeze_rare python common/tools/freeze_classes.py $U2 --from $U1 Bicycle Motorcycle Bus
  run validate python common/tools/route_predictions.py validate $U2
  python common/tools/s7_check.py check lumpi $U2 $U1 > "$RUN/s8_u2_final_check.log" 2>&1 || { st "final check FAILED"; exit 1; }
  FROZEN=$(grep -h '^FROZEN' "$RUN/s8_u2_final_check.log" | cut -d' ' -f2-)
  st "final check vs $(basename $U1): $(grep -vh '^FROZEN' "$RUN/s8_u2_final_check.log" | cut -c1-200 | tr '\n' ';')"
  run freeze python common/tools/freeze_classes.py $U2 --from $U1 $FROZEN
  run validate_final python common/tools/route_predictions.py validate $U2
  NC=$(python -c "import sys;sys.path.insert(0,'common');from bdc26.config import load_track;print(len(load_track('lumpi')['classes_with_test_gt']))")
  if [ "$(echo $FROZEN | wc -w)" -ge "$NC" ]; then st "every class frozen: $(basename $U2) equals U1; U2 is not built"; st "DONE"; exit 0; fi
  package $U2 s8b $U1
  st "projection vs $(basename $U1): $(python common/tools/s7_check.py projection lumpi $U2 $U1)"
  st "DONE"
  exit 0
fi
if [ "$STAGE" = v2x ]; then
  V=model-v2x-track; REF=$V/routed-g12; M=$V/routed-g13
  mkdir -p $M/test $M/validation/results $M/train $M/submissions
  cp $REF/test/make_submission.sh $REF/test/synthetic_ids.txt $M/test/
  cp $REF/validation/results/route_table.json $M/validation/results/
  python - "$REF" "$M" > "$RUN/s8_v2x_card.log" 2>&1 <<'PY' || { st "card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
src, m = sys.argv[1:3]
d = yaml.safe_load(Path(src, "model.yaml").read_text())
d["name"] = Path(m).name
d["strategy"] = "S8"
d["status"] = ("S8 V2X U2: the entry routed-g12 with the 12-view (flip4+yaw+z+scale) siblings swapped into its fusions, "
               "gated per class (docs/decisions/2026-10-29-s8-last-day-strategy.md)")
d["notes"] = "S8 V2X U2 (docs/decisions/2026-10-29-s8-last-day-strategy.md, rules 3, 4 and 8).\n"
for k in ("vrros_tta", "vrros4_tta", "pvros4s2_tta", "pp5_tta"):
    m0 = d["members"][k]
    d["members"][k + "12"] = {"model": m0["model"], "ckpt": m0["ckpt"], "tta": "flip4+yaw+z+scale", "tta_tag": "tta12",
                              "postprocess": "test/postprocess_tta12.yaml"}
d.pop("tail_copies", None); d.pop("sparse_demotion", None)       # re-derived after the swap, as in S7.6
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: {len(d['members'])} members")
PY
  st "$(basename $M) created ($(tr '\n' ';' < "$RUN/s8_v2x_card.log"))"
  run fuse python common/tools/route_predictions.py fuse $M --pooled-rule --swap-variant tta12
  st "swap: $(grep -h 'swap candidates' "$RUN/s8_v2x_fuse.log" | sed 's/^ *//')"
  st "fuse: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$RUN/s8_v2x_fuse.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"
  run budget python common/tools/route_predictions.py budget $M --pooled
  run tail python common/tools/route_predictions.py tail $M
  run sparse python common/tools/route_predictions.py sparse $M
  python common/tools/s7_check.py check v2x $M $REF > "$RUN/s8_v2x_final_check.log" 2>&1 || { st "final check FAILED"; exit 1; }
  FROZEN=$(grep -h '^FROZEN' "$RUN/s8_v2x_final_check.log" | cut -d' ' -f2-)
  st "final check vs $(basename $REF): $(grep -vh '^FROZEN' "$RUN/s8_v2x_final_check.log" | cut -c1-200 | tr '\n' ';')"
  if [ -n "$FROZEN" ]; then
    run freeze python common/tools/freeze_classes.py $M --from $REF $FROZEN
    run validate python common/tools/route_predictions.py validate $M
  fi
  NC=$(python -c "import sys;sys.path.insert(0,'common');from bdc26.config import load_track;print(len(load_track('v2x')['classes_with_test_gt']))")
  if [ "$(echo $FROZEN | wc -w)" -ge "$NC" ]; then st "every class frozen: $(basename $M) equals the entry; V2X U2 is not built"; st "DONE"; exit 0; fi
  package $M s8v $REF v2x
  st "DONE"
  exit 0
fi
# S8.2 (record Section 9): the 12-view bags and seeds, rule 4 in full (extend the route table, fuse up to 3 members),
# final check against the latest built version of the track; LUMPI routed-g11c (s8c) from routed-g11b, V2X routed-g14
# (s8w) from routed-g13. Needs the seeds' _tta12 variants (tune_and_eval.sh ... --tta-tag tta12 --reuse-raw).
if [ "$STAGE" = u3 ] || [ "$STAGE" = v2x2 ]; then
  if [ "$STAGE" = u3 ]; then
    T=lumpi; V=$L; REF=$U2; M=$L/routed-g11c; TAG=s8c
    BAGS="bag-voxelrcnn-ros-g1v4 bag-voxelrcnn-ros-g1v4x bag-pvrcnnpp-ros-g1v4 bag-pvrcnnpp-ros-g1v4x"
    FUSEX=(--classes Person Car Truck Van --late-rank Person --gate-top 3)
  else
    T=v2x; V=model-v2x-track; REF=$V/routed-g13; M=$V/routed-g14; TAG=s8w
    BAGS="bag-voxelrcnn-ros-g1v5 bag-voxelrcnn-ros-g1v5x bag-pvrcnnpp-ros-g1v5 bag-pvrcnnpp-ros-g1v5x"
    FUSEX=()
  fi
  for B in $BAGS; do run "bag_$B" python common/tools/bag_predictions.py $V/$B --tags _tta12 & done   # bags in parallel
  wait
  for B in $BAGS; do grep -q "_tta12: A" "$RUN/s8_${STAGE}_bag_$B.log" || { st "bag $B FAILED"; exit 1; }; done
  st "bags: $(cat "$RUN"/s8_${STAGE}_bag_*.log | grep -E '_tta12: A' | tr '\n' ';')"
  mkdir -p $M/test $M/validation/results $M/train $M/submissions
  cp $REF/test/make_submission.sh $REF/test/synthetic_ids.txt $M/test/
  cp $REF/validation/results/route_table.json $M/validation/results/
  python - "$REF" "$M" "$T" "$BAGS" > "$RUN/s8_${STAGE}_card.log" 2>&1 <<'PY' || { st "card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
src, m, t, bags = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split()
d = yaml.safe_load(Path(src, "model.yaml").read_text())
seeds = set()
for b in bags:
    seeds |= set(yaml.safe_load(Path(src).parent.joinpath(b, "model.yaml").read_text())["members"])
done = {(v["model"], v["ckpt"]) for v in d["members"].values() if v.get("tta_tag") == "tta12"}
for k, v in list(d["members"].items()):                  # every 8-view member whose 12-view variant now exists
    if v.get("tta") and not v.get("tta_tag") and (v["model"] in seeds or v["model"] in bags) and (v["model"], v["ckpt"]) not in done:
        d["members"][k + "12"] = {"model": v["model"], "ckpt": v["ckpt"], "tta": "flip4+yaw+z+scale", "tta_tag": "tta12",
                                  "postprocess": "test/postprocess_tta12.yaml"}
d["name"] = Path(m).name
d["status"] = (f"S8.2: {Path(src).name} with the 12-view seed bags and seeds as members, rule 4 in full (fuse up to 3), "
               "gated per class (docs/decisions/2026-10-29-s8-last-day-strategy.md Section 9)")
d["notes"] = "S8.2 (docs/decisions/2026-10-29-s8-last-day-strategy.md, Section 9).\n"
if t == "v2x":
    d.pop("tail_copies", None); d.pop("sparse_demotion", None)       # re-derived after fuse, as in s8v
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: {len(d['members'])} members, {sum(1 for v in d['members'].values() if v.get('tta_tag'))} at 12 views")
PY
  st "$(basename $M) created ($(tr '\n' ';' < "$RUN/s8_${STAGE}_card.log"))"
  run extend python common/tools/route_predictions.py extend $M
  run fuse python common/tools/route_predictions.py fuse $M --max-members 3 --pooled-rule "${FUSEX[@]}"
  st "fuse: $(grep -hoE '^[A-Za-z]+ .*"decision": "[^"]*"' "$RUN/s8_${STAGE}_fuse.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"
  st "fused sets: $(python -c "import yaml;d=yaml.safe_load(open('$M/model.yaml'));print('; '.join(f\"{c} {'+'.join(f['members'])}@{f['iou']}\" for c, f in d['fusion'].items()))")"
  if [ "$T" = lumpi ]; then
    python - "$U1" "$M" > "$RUN/s8_${STAGE}_completion.log" 2>&1 <<'PY' || { st "completion FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
src, m = sys.argv[1:3]
u1 = yaml.safe_load(Path(src, "model.yaml").read_text())
d = yaml.safe_load(Path(m, "model.yaml").read_text())
d["budget"], d["tail_copies"] = u1["budget"], u1["tail_copies"]      # U1's floors and copies (fuse rewrites the tail)
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
  python common/tools/s7_check.py check $T $M $REF > "$RUN/s8_${STAGE}_final_check.log" 2>&1 || { st "final check FAILED"; exit 1; }
  FROZEN=$(grep -h '^FROZEN' "$RUN/s8_${STAGE}_final_check.log" | cut -d' ' -f2-)
  st "final check vs $(basename $REF): $(grep -vh '^FROZEN' "$RUN/s8_${STAGE}_final_check.log" | cut -c1-200 | tr '\n' ';')"
  if [ -n "$FROZEN" ]; then
    cp $M/model.yaml "$RUN/s8_${STAGE}_card_before_freeze.yaml"
    run freeze python common/tools/freeze_classes.py $M --from $REF $FROZEN
    python -c "import sys,yaml;a,b=(yaml.safe_load(open(f)) for f in sys.argv[1:]);sys.exit(0 if a==b else 1)" \
      "$RUN/s8_${STAGE}_card_before_freeze.yaml" $M/model.yaml && st "freeze changed nothing: validation kept" \
      || run validate_final python common/tools/route_predictions.py validate $M
  fi
  NC=$(python -c "import sys;sys.path.insert(0,'common');from bdc26.config import load_track;print(len(load_track('$T')['classes_with_test_gt']))")
  if [ "$(echo $FROZEN | wc -w)" -ge "$NC" ]; then st "every class frozen: $(basename $M) equals $(basename $REF); $TAG is not built"; st "DONE"; exit 0; fi
  package $M $TAG $REF $T
  st "projection vs $(basename $REF): $(python common/tools/s7_check.py projection $T $M $REF)"
  st "DONE"
  exit 0
fi
# S8.3 (record Section 10): the completion up to the kit budget, no GPU. u4: LUMPI routed-g11d (s8d) from routed-g11c;
# v2x3: V2X routed-g13x (s8x) from routed-g13. $3 = a JSON file {"tail_copies": {...}} (LUMPI) or {"final_copies": {...}}
# (V2X) chosen by the probe; the test predictions are the reference's verified member predictions, merged again.
if [ "$STAGE" = u4 ] || [ "$STAGE" = v2x3 ]; then
  SPEC=$3
  if [ "$STAGE" = u4 ]; then T=lumpi; REF=$L/routed-g11c; M=$L/routed-g11d; TAG=s8d; RTAG=s8c
  else T=v2x; REF=model-v2x-track/routed-g13; M=model-v2x-track/routed-g13x; TAG=s8x; RTAG=s8v; fi
  mkdir -p $M/test/output $M/validation/results $M/train $M/submissions
  cp $REF/test/make_submission.sh $REF/test/synthetic_ids.txt $M/test/
  cp $REF/validation/results/route_table.json $M/validation/results/
  python - "$REF" "$M" "$SPEC" > "$RUN/s8_${STAGE}_card.log" 2>&1 <<'PY' || { st "card FAILED"; exit 1; }
import json, sys
from pathlib import Path
import yaml
src, m, spec = sys.argv[1:4]
d = yaml.safe_load(Path(src, "model.yaml").read_text())
d.update(json.loads(Path(spec).read_text()))
d["name"] = Path(m).name
d["status"] = (f"S8.3: {Path(src).name} with the completion up to the kit budget ({json.loads(Path(spec).read_text())}) "
               "(docs/decisions/2026-10-29-s8-last-day-strategy.md Section 10)")
d["notes"] = "S8.3 (docs/decisions/2026-10-29-s8-last-day-strategy.md, Section 10).\n"
Path(m, "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{Path(m).name}: " + json.dumps(json.loads(Path(spec).read_text())))
PY
  st "$(basename $M) created ($(tr '\n' ';' < "$RUN/s8_${STAGE}_card.log"))"
  run validate python common/tools/route_predictions.py validate $M &
  USED=$(python -c "import sys,yaml;sys.path.insert(0,'common/tools');from route_predictions import used_members;print(' '.join(used_members(yaml.safe_load(open('$M/model.yaml')))))")
  PRED=(); for N in $USED; do PRED+=(--pred "$N=$REF/test/output/predictions_$N.json"); done
  run merge python common/tools/route_predictions.py merge $M "${PRED[@]}" --out $M/test/output/predictions.json
  wait                                                  # validation first: the manifest records its local scores
  grep -q "S8 $STAGE: validate done" "$RUN/events.txt" || { st "validate FAILED"; exit 1; }
  SYN=$(python -c "import yaml;print(yaml.safe_load(open('$M/model.yaml'))['realism_frames'])")
  run package python common/tools/package_submission.py $M --tag $TAG --pred $M/test/output/predictions.json --synthetic "$SYN" \
    --syn-split val --syn-list $M/test/synthetic_ids.txt --ckpt "S8.3: $(basename $REF) members, merged again" --team "${BDC_TEAM:-KarmaRV}" \
    --local-scores $M/validation/results/local_scores.json
  Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
  st "packaged $Z"
  python common/tools/check_submission.py --track $T $Z --official > "$RUN/s8_${STAGE}_check.log" 2>&1 \
    && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/s8_${STAGE}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
  SCX=(); [ "$T" = lumpi ] && SCX=(--judge Van)
  python common/tools/scorecard.py $M --vs $REF --bootstrap 200 --realism-from $REF "${SCX[@]}" > "$RUN/s8_${STAGE}_scorecard.log" 2>&1 \
    && st "scorecard done" || st "scorecard FAILED"
  python common/tools/reproduce_submission.py $M --tag $TAG --write-script > "$RUN/s8_${STAGE}_reproduce.log" 2>&1 || true
  python common/tools/reproduce_validation.py $M --tag $TAG --write-script > "$RUN/s8_${STAGE}_reproduce_val.log" 2>&1 || true
  st "projection vs $(basename $REF): $(python common/tools/s7_check.py projection $T $M $REF)"
  st "DONE"
  exit 0
fi
echo "unknown stage $STAGE" >&2; exit 2
