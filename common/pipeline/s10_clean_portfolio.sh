#!/usr/bin/env bash
# S10 clean portfolio of one track (docs/decisions/2026-11-08-s10-clean-final-plan.md, Section 8 rules 1-3 and 6-8,
# written before any S10 run). Built from scratch on clean members only (rule 1); no class is frozen back to the
# reference, because the reference (the kept zip) is not clean. Runs detached, never uploads or commits:
#   bash common/pipeline/launch.sh <run> c0_lumpi common/pipeline/s10_clean_portfolio.sh <run> lumpi routed-c0 \
#        model-lumpi-track/routed-g22 c0 pcdet/g1-v6 <ids.txt> <member folder> ...
# 1. clean check of every listed member folder (common/tools/clean_check.py); any LABEL stops the build
# 2. card: the reference's card without its route, members, fusion and calibrations (V2X: and budget, tail copies); members = each listed folder with
#    its plain, 8-view and (when tuned) 12-view realval outputs; realism frames = <frames> with the 50 ids of <ids.txt>
#    (chosen by S9 rule 4 on the held-out proxies)
# 3. select --rule joint --pooled (route from scratch: no incumbent; members compared uncalibrated, as S8.2 `extend` does:
#    the per-member z search of --calibrated takes about a minute per member and class, 10 h for 79 LUMPI members)
# 4. fuse --max-members 3 --pooled-rule (LUMPI: Person ranked by late-A, top 3 through the gates, the Van judge), then
#    calibrate --pooled on the classes that are not fused (S1 C1 rule plus the pooled gate; a fused class takes its
#    members' own calibrations in merge_card, none in an uncalibrated select)
# 5. LUMPI: the reference's S8.3 floors and copies, then validate (the Person copy threshold is re-fitted in step 8);
#    V2X: budget --pooled, tail, sparse (S7.6 and S8 order)
# 6. anchored size calibration selected on the uncalibrated routed predictions (size_calibration.py --write), validate
# 7. clean check of the routed model (rule 1), package
# 8. LUMPI: rule 7 copy fit (at most 38,466 kit boxes), re-package if it changes; kit check; scorecard against the
#    reference; reproduction scripts; projection against the reference (information: the reference is not clean)
# Events: <run>/events.txt (S10 <track> <tag>: ...); logs <run>/s10_<track>_<tag>_*.log
RUN=$1; T=$2; NAME=$3; REF=$4; TAG=$5; FRAMES=$6; IDS=$7; shift 7; FOLDERS="$*"
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
V=model-$T-track; M=$V/$NAME
st() { ev "S10 $T $TAG: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/s10_${T}_${TAG}_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }
[ -e $M ] && { st "$M exists: stopped for review"; exit 1; }

BAD=0
for f in $FOLDERS; do python common/tools/clean_check.py $V/$f >> "$RUN/s10_${T}_${TAG}_clean_members.log" 2>&1 || BAD=1; done
[ $BAD = 1 ] && { st "a listed member is not clean (rule 1): $(grep '^LABEL' "$RUN/s10_${T}_${TAG}_clean_members.log" | cut -c1-120 | tr '\n' ';')"; exit 1; }
st "rule 1: all $(echo $FOLDERS | wc -w) member folders clean"

mkdir -p $M/test $M/validation/results $M/train $M/submissions
cp $REF/test/make_submission.sh $M/test/
cp "$IDS" $M/test/synthetic_ids.txt
python - "$REF" "$M" "$T" "$FRAMES" $FOLDERS > "$RUN/s10_${T}_${TAG}_card.log" 2>&1 <<'PY' || { st "card FAILED"; exit 1; }
import sys
from pathlib import Path
import yaml
ref, m, t, frames, folders = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5:]
ABBR = {"voxelrcnn": "vr", "pvrcnnpp": "pv", "voxelnext": "vn", "dsvt": "ds", "pointpillars": "pp", "centerpoint": "cp"}
def key(name):
    bag = name.startswith("bag-")
    parts = (name[4:] if bag else name).split("-")
    return ("b" if bag else "") + ABBR.get(parts[0], parts[0][:3]) + "".join(parts[1:-1]) + parts[-1].replace("g1v", "")
d = yaml.safe_load(Path(ref, "model.yaml").read_text())
for k in ("route", "route_selection", "calibration", "fusion", "size_calibration", "sparse_demotion"):
    d.pop(k, None)
if t == "v2x":                                       # re-derived after fuse (S7.6 and S8); `budget` must go: the
    d.pop("tail_copies", None)                       # budget writer cuts the card at "budget:", so a reference
    d.pop("budget", None)                            # budget above `route` took route and fusion with it (C0 V2X)
d["name"], d["strategy"], d["realism_frames"] = m.name, "S10", frames
d["data"]["train"] = "pcdet/g1-v6"
d["architecture"] = ("per-class routing and box fusion (up to 3 members) of clean members only (S10 rule 1: corpora "
                     "without real label rows, the g1-v6 family and UrbanTwin), with test-time augmentation")
d["status"] = f"S10 clean portfolio {m.name} (docs/decisions/2026-11-08-s10-clean-final-plan.md)"
d["notes"] = "S10 (docs/decisions/2026-11-08-s10-clean-final-plan.md, Sections 7-8): built from scratch on clean members.\n"
mem = {}
for f in folders:
    fd = m.parent / f
    bag = yaml.safe_load((fd / "model.yaml").read_text()).get("type") == "bag"
    run = "bag" if bag else "run1"
    ck = f"train/output/pcdet_model/{run}/ckpt/checkpoint_epoch_40.pth"
    out = fd / "validation" / "output"
    have = lambda x: all((out / f"pcdet_realval-v1_{s}_{run}_checkpoint_epoch_40{x}.json").exists() for s in ("val", "valB"))
    k = key(f)
    if not (have("") and have("_tta")):
        print("skipped (no plain and 8-view realval outputs):", f)
        continue
    mem[k] = {"model": f, "ckpt": ck}
    mem[k + "_tta"] = {"model": f, "ckpt": ck, "tta": "flip4+yaw+z", "postprocess": "test/postprocess_tta.yaml"}
    if have("_tta12"):
        mem[k + "_tta12"] = {"model": f, "ckpt": ck, "tta": "flip4+yaw+z+scale", "tta_tag": "tta12",
                             "postprocess": "test/postprocess_tta12.yaml"}
d["members"] = mem
(m / "model.yaml").write_text(yaml.safe_dump(d, sort_keys=False))
print(f"{m.name}: {len(mem)} members from {len(folders)} folders:", " ".join(mem))
PY
st "$NAME created ($(tail -n 1 "$RUN/s10_${T}_${TAG}_card.log" | cut -c1-200))"
# steps 3-8 (select, fuse, calibrate, budget or validate, size calibration, package, kit, scorecard) from a
# snapshot of s10_portfolio_tail.sh, so that editing the repository never breaks this run
mkdir -p "$RUN/bin"; [ -e "$RUN/bin/lib_common.sh" ] || cp "$REPO/common/pipeline/common.sh" "$RUN/bin/lib_common.sh"
cp "$REPO/common/pipeline/s10_portfolio_tail.sh" "$RUN/bin/s10_tail_${T}_${TAG}.sh"
export BDC_REPO="$REPO"
exec bash "$RUN/bin/s10_tail_${T}_${TAG}.sh" "$RUN" "$T" "$NAME" "$REF" "$TAG" select
