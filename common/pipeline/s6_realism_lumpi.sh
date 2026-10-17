#!/usr/bin/env bash
# S6 item 9 (docs/02-STRATEGY.md Section 8.6), CPU only: LUMPI realism frames chosen from the whole g1-v4 corpus
# (train + val, 10,000 frames, the generator of every LUMPI member) instead of its 1,000 validation frames.
#   bash common/pipeline/launch.sh <run> realism_lumpi common/pipeline/s6_realism_lumpi.sh <run>
# Pre-registered (STATUS.md, 2026-10-15): fit proxies 1-3, seed 1234, the S1 FPD selection and the R5 FPD + EMD
# refinement, iterations scaled with the pool (x10: 200,000 swaps, 30,000 refinement swaps); one run each. Gate: mean
# exact R on the held-out proxies 4-5 at least 0.003 above the R5 frames (scored the same way in step 1); the late
# proxies are reported, never used. Writes candidate lists only (routed-g8/validation/results/realism_candidates/); adopting one
# is a separate, recorded step.
RUN=$1
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=8
L=model-lumpi-track; OUT=$L/routed-g8/validation/results/realism_candidates; mkdir -p $OUT
FIT=(--fit-ref pcdet/realism-proxy-1 --fit-ref pcdet/realism-proxy-2 --fit-ref pcdet/realism-proxy-3)
TEST=(--test-ref pcdet/realism-proxy-4 --test-ref pcdet/realism-proxy-5
      --test-ref pcdet/realism-proxy-late-1 --test-ref pcdet/realism-proxy-late-2 --test-ref pcdet/realism-proxy-late-3)
ev "REALISM lumpi: start (g1-v4 train+val pool)"
python common/tools/score_realism.py --track lumpi --syn $L/routed-g7/submissions/2026-10-14_r5/lumpi_r5_submission.zip \
  --ref pcdet/realism-proxy-4 --ref pcdet/realism-proxy-5 > "$RUN/realism_lumpi_baseline.log" 2>&1 \
  && ev "REALISM lumpi: baseline (R5 frames) done" || ev "REALISM lumpi: baseline FAILED"
for O in fpd fpd+emd; do
  N=${O/+/}
  python common/tools/select_realism_frames.py --track lumpi --syn pcdet/g1-v4 --split train+val "${FIT[@]}" "${TEST[@]}" \
    --seed 1234 --iters 200000 --refine-iters 30000 --objective $O --out $OUT/synthetic_ids_s6_$N.txt \
    > "$RUN/realism_lumpi_$N.log" 2>&1 && ev "REALISM lumpi: $O done" || ev "REALISM lumpi: $O FAILED"
done
ev "REALISM lumpi: DONE"
