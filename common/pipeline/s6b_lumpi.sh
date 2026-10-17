#!/usr/bin/env bash
# S6 close-out, LUMPI variant b (docs/02-STRATEGY.md Section 8.6.2): routed-g8 plus the Car candidate of the S6 fuse step,
# kept only if the pooled condition also holds on the final predictions (the check that reverted LUMPI Car in S5 and R5).
#   bash common/pipeline/launch.sh <run> s6b_lumpi common/pipeline/s6b_lumpi.sh <run>
RUN=$1
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=4
M=model-lumpi-track/routed-g8b; REF=model-lumpi-track/routed-g8
st() { ev "S6B lumpi: $*"; }
run() { local S=$1; shift; ( time "$@" ) > "$RUN/s6b_lumpi_$S.log" 2>&1 || { st "$S FAILED"; exit 1; }; st "$S done"; }
run budget python common/tools/route_predictions.py budget $M
run pin python common/tools/freeze_classes.py $M --from $REF Person Bicycle Motorcycle Bus Truck Van Unknown
run validate python common/tools/route_predictions.py validate $M
run pooled python common/tools/pooled_check.py $M --vs $REF --classes Car
st "Car on the final predictions: $(grep -h '^Car' "$RUN/s6b_lumpi_pooled.log")"
grep -q "^Car .* passes" "$RUN/s6b_lumpi_pooled.log" || { st "Car fails the pooled check on the final predictions: variant b = S6, nothing to package"; st "DONE"; exit 0; }
# packaging waits for the reproduction workers of this run (a GPU shared with another job can change the last digits)
until [ "$(grep -c "WORKER_DONE gpu" "$RUN/events.txt")" -ge 8 ]; do sleep 120; done
G=""; until G=$(free_gpu 24000); [ -n "$G" ]; do sleep 60; done
CUDA_VISIBLE_DEVICES=$G bash $M/test/make_submission.sh s6b > "$RUN/s6b_lumpi_package.log" 2>&1 || { st "package FAILED"; exit 1; }
Z=$(ls -d $M/submissions/*_s6b | tail -n 1)/submission.zip; st "packaged $Z"
python common/tools/check_submission.py --track lumpi $Z --official > "$RUN/s6b_lumpi_check.log" 2>&1 \
  && st "kit check: $(grep -E '"wall_s"|"n_boxes"|"valid"' "$RUN/s6b_lumpi_check.log" | tr -s ' ' | tr '\n' ' ')" || st "kit check FAILED"
python common/tools/scorecard.py $M --vs $REF --bootstrap 200 --realism-from $REF --judge Van > "$RUN/s6b_lumpi_scorecard.log" 2>&1 && st "scorecard done" || st "scorecard FAILED"
python common/tools/reproduce_submission.py $M --tag s6b --write-script > "$RUN/s6b_lumpi_reproduce.log" 2>&1 || true
python common/tools/reproduce_validation.py $M --tag s6b --write-script >> "$RUN/s6b_lumpi_reproduce.log" 2>&1 || true
st "DONE"
