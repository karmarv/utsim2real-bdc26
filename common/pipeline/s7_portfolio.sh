#!/usr/bin/env bash
# S7 step 2 portfolio, V2X (docs/02-STRATEGY.md Section 8.11; rules pre-registered in
# docs/decisions/2026-10-18-s7-visibility-rule.md; runs detached, never uploads or commits):
#   bash common/pipeline/launch.sh <run> portfolio_s7 common/pipeline/s7_portfolio.sh <run>
# 1. waits until the six S7 runs (visibility labels, corpus g1-v5m) have their tuned validation files, or the post worker is done
# 2. seed bags bag-voxelrcnn-ros-g1v5m and bag-pvrcnnpp-ros-g1v5m; paired comparison with the g1-v5 bags of the same seeds
# 3. routed-g10 = routed-g9 plus the two bags (plain and TTA); its tail copies and sparse stage are removed and re-derived
# 4. select (joint, calibrated, pooled), fuse (up to 3, the 6.0 pooled rule), budget, tail copies, sparse stage (rule 3)
# 5. final check on the final predictions against routed-g9 (pooled A+B P(gain) >= 0.9, neither split down by more than
#    0.005); failing classes are frozen at routed-g9, then validated again
# 6. package (bag-aware, on an idle GPU), official kit check, scorecard against routed-g9, reproduction script, projection
# Events: <run>/events.txt (PORTFOLIO s7: ...); logs <run>/pf_s7_*.log
RUN=$1
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
T=v2x; M=model-v2x-track/routed-g10; REF=model-v2x-track/routed-g9
SEEDS="voxelrcnn-ros-g1v5m voxelrcnn-ros-g1v5m-s2 voxelrcnn-ros-g1v5m-s3 pvrcnnpp-ros-g1v5m pvrcnnpp-ros-g1v5m-s2 pvrcnnpp-ros-g1v5m-s3"
BAGS="bagvr5m:bag-voxelrcnn-ros-g1v5m bagpv5m:bag-pvrcnnpp-ros-g1v5m"
st() { ev "PORTFOLIO s7: $*"; }
run() { local N=$1; shift; ( time "$@" ) > "$RUN/pf_s7_$N.log" 2>&1 || { st "$N FAILED"; exit 1; }; st "$N done"; }
complete() { local m=$1; for S in val valB; do for X in "" _tta; do
  [ -s model-$T-track/$m/validation/output/pcdet_realval-v1_${S}_run1_checkpoint_epoch_40${X}.json ] || return 1; done; done; }
all_done() { for m in $SEEDS; do complete $m || return 1; done; }
posts_over() { grep -q POST_WORKER_DONE "$RUN/events.txt"; }
st "waiting for the S7 runs: $SEEDS"
until all_done || posts_over; do sleep 120; done
sleep 30
all_done || { st "a run is incomplete after the post worker finished: $(for m in $SEEDS; do complete $m || printf '%s ' $m; done); stopping"; exit 1; }

# 2. bags and the paired comparison with the g1-v5 bags (same seeds, raw labels)
for kb in $BAGS; do run bag_${kb#*:} python common/tools/bag_predictions.py model-$T-track/${kb#*:}; done
python - > "$RUN/pf_s7_bag_compare.log" 2>&1 <<'PY' || st "bag comparison FAILED"
import json, sys
from pathlib import Path
sys.path.insert(0, "common/tools")
from _common import data_path, load_track
from bdc26 import scorecard as sc
t = load_track("v2x"); root = data_path(t, "pcdet/realval-v1"); cls = list(t["classes_with_test_gt"])
gts = {s: sc.load_split(root, s) for s in ("val", "valB")}
f = lambda b, s, x: Path(f"model-v2x-track/{b}/validation/output/pcdet_realval-v1_{s}_bag_checkpoint_epoch_40{x}.json")
out = {}
for fam in ("voxelrcnn-ros", "pvrcnnpp-ros"):
    for x in ("", "_tta"):
        old, new = f"bag-{fam}-g1v5", f"bag-{fam}-g1v5m"
        fo = {s: sc.flags_for(f(old, s, x), gts[s], cls) for s in gts}
        fn = {s: sc.flags_for(f(new, s, x), gts[s], cls) for s in gts}
        row = {}
        for c in cls:
            ap = {k: {s: sc.ap_from_flags(F[s][c], "3d@0.5") for s in gts} for k, F in (("old", fo), ("new", fn))}
            pg = sc.pooled_gate({s: fo[s][c] for s in gts}, {s: fn[s][c] for s in gts}, c)
            row[c] = {"g1v5_A": ap["old"]["val"], "g1v5_B": ap["old"]["valB"], "g1v5m_A": ap["new"]["val"], "g1v5m_B": ap["new"]["valB"],
                      "pooled_delta": pg["delta"], "p_gain": pg["p_gain"]}
            print(f"{fam}{x or '_plain'} {c:10s} A {ap['old']['val']:.4f} -> {ap['new']['val']:.4f}  B {ap['old']['valB']:.4f} -> "
                  f"{ap['new']['valB']:.4f}  pooled {pg['delta']:+.4f} P {pg['p_gain']:.2f}")
        out[f"{fam}{x or '_plain'}"] = row
Path("model-v2x-track/bag-voxelrcnn-ros-g1v5m/validation/results").mkdir(parents=True, exist_ok=True)
Path("model-v2x-track/bag-voxelrcnn-ros-g1v5m/validation/results/s7_bag_compare.json").write_text(json.dumps(out, indent=2))
PY
st "bags vs g1-v5 bags (pooled): $(grep -h 'pedestrian' "$RUN/pf_s7_bag_compare.log" | awk '{print $1, "B", $8, "->", $10, "pooled", $12}' | tr '\n' ';')"

# 3. routed-g10 from routed-g9
mkdir -p $M/test $M/validation/results $M/train $M/submissions
cp $REF/test/make_submission.sh $REF/test/synthetic_ids.txt $M/test/
python - <<'PY' > "$RUN/pf_s7_members.log" 2>&1
import yaml
from pathlib import Path
d = yaml.safe_load(Path("model-v2x-track/routed-g9/model.yaml").read_text())
d["name"] = "routed-g10"
d["status"] = "S7 step 2: routed-g9 plus the bags of the visibility-label members (g1-v5m); select, fuse (6.0 pooled rule), budget, tail, sparse, final pooled check against routed-g9"
d["notes"] = "S7 step 2 (docs/02-STRATEGY.md Section 8.11, docs/decisions/2026-10-18-s7-visibility-rule.md rule 5).\n"
d.pop("tail_copies", None); d.pop("sparse_demotion", None)
bk = "train/output/pcdet_model/bag/ckpt/checkpoint_epoch_40.pth"
for k, m in (("bagvr5m", "bag-voxelrcnn-ros-g1v5m"), ("bagpv5m", "bag-pvrcnnpp-ros-g1v5m")):
    d["members"][k] = {"model": m, "ckpt": bk}
    d["members"][k + "_tta"] = {"model": m, "ckpt": bk, "tta": "flip4+yaw+z", "postprocess": "test/postprocess_tta.yaml"}
Path("model-v2x-track/routed-g10/model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"routed-g10: {len(d['members'])} members")
PY
st "routed-g10 created ($(tail -n 1 "$RUN/pf_s7_members.log"))"

# 4. the portfolio steps
run select python common/tools/route_predictions.py select $M --rule joint --calibrated --pooled
run fuse python common/tools/route_predictions.py fuse $M --max-members 3 --pooled-rule
run budget python common/tools/route_predictions.py budget $M
run tail python common/tools/route_predictions.py tail $M
run sparse python common/tools/route_predictions.py sparse $M
st "fuse: $(grep -hoE '^(vehicle|pedestrian|truck) .*"decision": "[^"]*"' "$RUN/pf_s7_fuse.log" | sed -E 's/ \{.*"decision": / /' | tr '\n' ';')"

# 5. final check against routed-g9 on the final predictions
python - > "$RUN/pf_s7_final_check.log" 2>&1 <<'PY' || { st "final check FAILED"; exit 1; }
import json, sys
from pathlib import Path
sys.path.insert(0, "common/tools")
from _common import data_path, load_track
from bdc26 import scorecard as sc
t = load_track("v2x"); root = data_path(t, "pcdet/realval-v1"); cls = list(t["classes_with_test_gt"])
gts = {s: sc.load_split(root, s) for s in ("val", "valB")}
p = lambda m, s: Path(f"model-v2x-track/{m}/validation/output/pcdet_realval-v1_{s}_routed.json")
fl = {(m, s): sc.flags_for(p(m, s), gts[s], cls, cache=False) for m in ("routed-g9", "routed-g10") for s in gts}
res, fail = {}, []
for c in cls:
    ap = {(m, s): sc.ap_from_flags(fl[(m, s)][c], "3d@0.5") for m in ("routed-g9", "routed-g10") for s in gts}
    dA, dB = ap[("routed-g10", "val")] - ap[("routed-g9", "val")], ap[("routed-g10", "valB")] - ap[("routed-g9", "valB")]
    pg = sc.pooled_gate({s: fl[("routed-g9", s)][c] for s in gts}, {s: fl[("routed-g10", s)][c] for s in gts}, c)
    ok = pg["ok"] and dA >= -0.005 and dB >= -0.005
    res[c] = {"dA": dA, "dB": dB, "pooled_delta": pg["delta"], "p_gain": pg["p_gain"], "kept": ok}
    print(f"{c} dA {dA:+.4f} dB {dB:+.4f} pooled {pg['delta']:+.4f} P {pg['p_gain']:.2f} {'kept' if ok else 'frozen at routed-g9'}")
    if not ok:
        fail.append(c)
Path("model-v2x-track/routed-g10/validation/results/final_check.json").write_text(json.dumps({"vs": "routed-g9", "classes": res}, indent=2))
print("FROZEN", " ".join(fail))
PY
FROZEN=$(grep -h '^FROZEN' "$RUN/pf_s7_final_check.log" | cut -d' ' -f2-)
st "final check: $(grep -hE '^(vehicle|pedestrian|truck) ' "$RUN/pf_s7_final_check.log" | tr '\n' ';')"
if [ -n "$FROZEN" ]; then
  run freeze python common/tools/freeze_classes.py $M --from $REF $FROZEN
  run validate python common/tools/route_predictions.py validate $M
fi
if [ "$(echo $FROZEN | wc -w)" -eq 3 ]; then st "every class frozen: routed-g10 equals routed-g9, nothing to package"; st "DONE"; exit 0; fi

# 6. package, kit check, scorecard, reproduction script, projection (6.0 upload gate)
G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh s7m > "$RUN/pf_s7_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d $M/submissions/*_s7m | tail -n 1)/submission.zip
st "packaged $Z"
python common/tools/check_submission.py --track $T $Z --official > "$RUN/pf_s7_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/pf_s7_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
python common/tools/scorecard.py $M --vs $REF --bootstrap 200 --realism-from $REF > "$RUN/pf_s7_scorecard.log" 2>&1 \
  && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py $M --tag s7m --write-script > "$RUN/pf_s7_reproduce.log" 2>&1 || true
st "projection: $(python -c "
import json
n=json.load(open('$M/validation/results/local_scores.json')); r=json.load(open('$REF/validation/results/local_scores.json'))
dA=n['realval_A_mAP_3d_0.5_R40']-r['realval_A_mAP_3d_0.5_R40']; dB=n['realval_B_mAP_3d_0.5_R40']-r['realval_B_mAP_3d_0.5_R40']
p=0.6*(dA+dB)/2*0.6/0.7; print(f'dA {dA:+.4f} dB {dB:+.4f} combined {p:+.4f} (bar +0.003: {\"passed\" if p>=0.003 else \"not met\"})')")"
st "DONE"
