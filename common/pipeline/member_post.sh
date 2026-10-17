#!/usr/bin/env bash
# Post-processing of one trained member, each step on the GPU with the most free memory (waits for >= MIN_FREE MiB,
# so it can run next to a training job), each retried up to 3 times (out of memory next to training):
#   1. per-class score blend (two-stage members only; common/tools/score_blend.py)
#   2. plain tuning and evaluation on realval-A/B (validation/tune_and_eval.sh)
#   3. TTA tuning (--tta flip4+yaw+z)
#   4. realval learning curves into TensorBoard (common/tools/tb_realval.py; monitoring only, never used to pick epochs)
#   bash common/pipeline/member_post.sh <run> <track> <member>
RUN=$1; T=$2; M=$3; MIN_FREE=${MIN_FREE:-24000}
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh
MD=model-$T-track/$M
step() {  # name, command... (GPU chosen at each attempt, exported as CUDA_VISIBLE_DEVICES)
  local N=$1; shift
  for k in 1 2 3; do
    local G=""; until G=$(free_gpu "$MIN_FREE"); [ -n "$G" ]; do sleep 60; done
    if CUDA_VISIBLE_DEVICES=$G "$@" > "$RUN/post_${T}_${M}_${N}.log" 2>&1; then ev "POST_STEP_DONE $N $T $M (GPU $G)"; return 0; fi
    ev "POST_STEP_FAIL $N $T $M (GPU $G, attempt $k)"; sleep 300
  done
  return 1
}
ev "POST_START $T $M"
OK=1
if grep -q "ROI_HEAD" "$MD/train/pcdet_model.yaml"; then step blend python common/tools/score_blend.py "$MD" || OK=0; fi
step plain bash -c "cd $MD && bash validation/tune_and_eval.sh $CK_REL" || OK=0
step tta bash -c "cd $MD && bash validation/tune_and_eval.sh $CK_REL --tta flip4+yaw+z" || OK=0
step curves python common/tools/tb_realval.py "$MD" || true
[ $OK = 1 ] && ev "POST_DONE $T $M" || ev "POST_FAIL $T $M"
