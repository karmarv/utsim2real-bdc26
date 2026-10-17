#!/usr/bin/env bash
# Finish a routed model whose route and fusions are already set (for example a variant of a portfolio): score floors,
# tail copies (V2X), packaging, the official kit check, the scorecard against a reference and the reproduction script.
# No gate is applied here: the caller states why the configuration is what it is (decision record). Never uploads.
#   bash common/pipeline/launch.sh <run> finish_<name> common/pipeline/finish_portfolio.sh <run> <track> <model> <tag> <ref>
# Example (S6 V2X variant b): ... <run> v2x model-v2x-track/routed-g8b s6b model-v2x-track/routed-g7
RUN=$1; T=$2; M=$3; TAG=$4; REF=$5
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
N=$(basename "$M")
st() { ev "FINISH $N: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/fin_${N}_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }
# floors are chosen on the original boxes and tail copies are derived afterwards (the order of the S6 portfolio and R5):
# copies sit below every original box, so a floor search that sees them would always pick no floor
python -c "import yaml,sys; p=sys.argv[1]; d=yaml.safe_load(open(p)); d.pop('tail_copies', None); open(p, 'w').write(yaml.safe_dump(d, sort_keys=False))" "$M/model.yaml"
run budget python common/tools/route_predictions.py budget "$M"
[ "$T" = v2x ] && run tail python common/tools/route_predictions.py tail "$M"
G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash "$M/test/make_submission.sh" "$TAG" > "$RUN/fin_${N}_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d "$M"/submissions/*_"$TAG" | tail -n 1)/submission.zip
st "packaged $Z"
python common/tools/check_submission.py --track "$T" "$Z" --official > "$RUN/fin_${N}_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/fin_${N}_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
SCX=(); [ "$T" = lumpi ] && SCX=(--judge Van)
python common/tools/scorecard.py "$M" --vs "$REF" --bootstrap 200 --realism-from "$REF" "${SCX[@]}" > "$RUN/fin_${N}_scorecard.log" 2>&1 \
  && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py "$M" --tag "$TAG" --write-script > "$RUN/fin_${N}_reproduce.log" 2>&1 || true
st "DONE"
