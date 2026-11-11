#!/usr/bin/env bash
# S10 clean portfolio, the steps after the card (common/pipeline/s10_clean_portfolio.sh steps 3-8; record
# docs/decisions/2026-11-08-s10-clean-final-plan.md Section 8). s10_clean_portfolio.sh runs it from `select`; alone it
# resumes a build whose route and fusion are set (FROM = calibrate, the default) or whose card has members only
# (FROM = select), or whose select is done (FROM = fuse):
#   bash common/pipeline/launch.sh <run> c0_lumpi_tail common/pipeline/s10_portfolio_tail.sh <run> lumpi routed-c0 \
#        model-lumpi-track/routed-g22 c0 [calibrate|select]
# z calibration covers the classes that are not fused: merge_card applies the class-level `calibration` to routed
# classes only (a fused class takes its members' own calibrations, none in an uncalibrated select), and `calibrate`
# reads the route-only merge, which has no predictions of a fused class whose routed member is not in its fusion set
# (C0 LUMPI Bicycle, 2026-11-08: "need at least one array to concatenate"). The scorecard computes realism on the zip
# (--realism): the S9 references' scorecards hold none to reuse (C0 LUMPI, 2026-11-08).
# S10 rule 14b (C2, package A, record 15.15.7): S10_ROUTE_BAR=0 S10_GO_P=0.8 drop R3's +0.01 B bar on route changes
# and raise rule 14's grouped P to 0.8 (default: R3 and rule 14 as in C1).
# S10_INCUMBENT=<model dir> (C1, C2): after size calibration, `gate --vs` reverts every changed class that fails R3 to
# the incumbent's whole class configuration (size entry included), then validates and runs the rule 14 grouped gate.
RUN=$1; T=$2; NAME=$3; REF=$4; TAG=$5; FROM=${6:-calibrate}
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
V=model-$T-track; M=$V/$NAME
FUSEX=(); SCX=()
[ "$T" = lumpi ] && { FUSEX=(--late-rank Person --gate-top 3 --judge Van); SCX=(--judge Van); }
st() { ev "S10 $T $TAG: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/s10_${T}_${TAG}_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }
[ -e $M/model.yaml ] || { st "$M has no card: stopped"; exit 1; }
if [ "$FROM" = select ] || [ "$FROM" = fuse ]; then      # fuse: resume a build whose select is done (S10 C1, 2026-11-10)
  if [ "$FROM" = select ]; then
    run select python common/tools/route_predictions.py select $M --rule joint --pooled
    st "route: $(python -c "import yaml;d=yaml.safe_load(open('$M/model.yaml'));print(d['route'])")"
  fi
  run fuse python common/tools/route_predictions.py fuse $M --max-members 3 --pooled-rule "${FUSEX[@]}"
  st "fused sets: $(python -c "import yaml;d=yaml.safe_load(open('$M/model.yaml'));print('; '.join(f\"{c} {'+'.join(f['members'])}@{f['iou']}\" for c, f in (d.get('fusion') or {}).items()))")"
elif [ "$FROM" != calibrate ]; then
  st "unknown start step $FROM: stopped"; exit 1
fi
NF=$(python -c "import sys; sys.path[:0]=['common','common/tools']; from _common import model_info; m,d,t=model_info(sys.argv[1]); f=d.get('fusion') or {}; print(' '.join(c for c in t['classes_with_test_gt'] if c not in f))" $M) \
  || { st "class list FAILED"; exit 1; }
if [ -n "$NF" ]; then
  run calibrate python common/tools/route_predictions.py calibrate $M --pooled --classes $NF
  st "z calibration ($NF; fused classes keep their members' outputs): $(grep '^calibration:' "$RUN/s10_${T}_${TAG}_calibrate.log" | cut -c1-200)"
else
  st "z calibration: every class is fused, none tried"
fi
if [ "$T" = lumpi ]; then
  run validate python common/tools/route_predictions.py validate $M
  run pointscore python common/tools/route_predictions.py pointscore $M --classes Person   # S10 D2 (record 15.13), gated
  st "point rescore: $(grep -E '^Person' "$RUN/s10_${T}_${TAG}_pointscore.log" | cut -c1-200)"
else
  run budget python common/tools/route_predictions.py budget $M --pooled
  run tail python common/tools/route_predictions.py tail $M
  run sparse python common/tools/route_predictions.py sparse $M
  run overhead python common/tools/route_predictions.py overhead $M --classes pedestrian   # S10 V5, rule 11
  st "overhead demotion: $(grep -E '^pedestrian' "$RUN/s10_${T}_${TAG}_overhead.log" | cut -c1-200)"
fi
run size_select python common/tools/size_calibration.py $M --write
st "size calibration: $(grep -E '^[A-Za-z]+: best' "$RUN/s10_${T}_${TAG}_size_select.log" | tr '\n' ';' | cut -c1-300)"
run validate_size python common/tools/route_predictions.py validate $M
if [ -n "${S10_INCUMBENT:-}" ]; then   # S10 C1 (record 15.13.7): each changed class passes R3 against the incumbent or reverts to it
  run gate python common/tools/route_predictions.py gate $M --vs "$S10_INCUMBENT" --route-bar "${S10_ROUTE_BAR:-0.01}" "${SCX[@]}"
  st "class gate vs $(basename "$S10_INCUMBENT"): $(grep '^reverted' "$RUN/s10_${T}_${TAG}_gate.log" | cut -c1-200)"
  run validate_gated python common/tools/route_predictions.py validate $M
  python common/tools/s10_grouped_gate.py $M "$S10_INCUMBENT" --go-p "${S10_GO_P:-0.75}" > "$RUN/s10_${T}_${TAG}_grouped.log" 2>&1 || { st "rule 14 gate FAILED"; exit 1; }
  st "rule 14 vs $(basename "$S10_INCUMBENT"): $(head -n 2 "$RUN/s10_${T}_${TAG}_grouped.log" | tr -s ' ' | tr '\n' ' ' | cut -c1-300)"
fi
python common/tools/clean_check.py $M > "$RUN/s10_${T}_${TAG}_clean.log" 2>&1 || { st "rule 1 FAILED: $(tail -n 1 "$RUN/s10_${T}_${TAG}_clean.log")"; exit 1; }
st "rule 1: $(tail -n 1 "$RUN/s10_${T}_${TAG}_clean.log")"
G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh $TAG > "$RUN/s10_${T}_${TAG}_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
st "packaged $Z"
if [ "$T" = lumpi ]; then                               # rule 7: the Person copy threshold of this route
  python common/tools/s9_copies_fit.py lumpi $M --max-boxes 38466 --write > "$RUN/s10_${T}_${TAG}_copies_fit.log" 2>&1 \
    || { st "copies fit FAILED"; exit 1; }
  CF=$(tail -n 1 "$RUN/s10_${T}_${TAG}_copies_fit.log"); st "copies fit: $CF"
  if [ "${CF%% *}" = SET ]; then
    run validate_copies python common/tools/route_predictions.py validate $M
    G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
    CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh $TAG > "$RUN/s10_${T}_${TAG}_package2.log" 2>&1 || { st "package FAILED"; exit 1; }
    Z=$(ls -d $M/submissions/*_$TAG | tail -n 1)/submission.zip
    st "packaged again with the fitted copies: $Z"
  fi
fi
python common/tools/check_submission.py --track $T $Z --official > "$RUN/s10_${T}_${TAG}_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/s10_${T}_${TAG}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
python common/tools/scorecard.py $M --vs $REF --bootstrap 200 --realism "${SCX[@]}" > "$RUN/s10_${T}_${TAG}_scorecard.log" 2>&1 \
  && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py $M --tag $TAG --write-script > "$RUN/s10_${T}_${TAG}_reproduce.log" 2>&1 || true
python common/tools/reproduce_validation.py $M --tag $TAG --write-script > "$RUN/s10_${T}_${TAG}_reproduce_val.log" 2>&1 || true
st "projection vs $(basename $REF) (information; the reference is not clean): $(python common/tools/s7_check.py projection $T $M $REF)"
st "DONE"
