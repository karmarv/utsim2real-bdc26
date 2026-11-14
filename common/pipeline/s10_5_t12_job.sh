#!/usr/bin/env bash
# Release 10.5 (record docs/decisions/2026-11-14-s10-10.5-final-push.md): one 12-view tuning job for a member trained
# and tuned in an earlier run (so, unlike t12f_job.sh, there is no tuning event to wait for). Run by gpu_queue.sh on its
# fixed GPU, from the repository root. Skips a member that already has 12-view outputs; waits for 46 GB free.
#   bash common/pipeline/s10_5_t12_job.sh <track> <member>
set -uo pipefail
T=$1; M=$2; D=model-$T-track/$M
if ls "$D/validation/output" 2>/dev/null | grep -qx "pcdet_.*_valB_run1_checkpoint_epoch_40_tta12[.]json"; then echo "$T:$M already has 12-view outputs"; exit 0; fi
until [ "$(nvidia-smi -i "$CUDA_VISIBLE_DEVICES" --query-gpu=memory.free --format=csv,noheader,nounits)" -ge 46000 ]; do sleep 30; done
bash "$D/validation/tune_and_eval.sh" "$D/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth" \
  --tta flip4+yaw+z+scale --tta-tag tta12 --reuse-raw
