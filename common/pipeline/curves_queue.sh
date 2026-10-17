#!/usr/bin/env bash
# Realval learning curves for models trained before the pipeline existed (TensorBoard tensorboard_realval/, monitoring
# only): pops "track:member" from <run>/curves_queue.txt and runs common/tools/tb_realval.py on the GPU with the most
# free memory. Starts only after <n_train_workers> TRAIN_WORKER_DONE events, so it never slows a training job.
#   bash common/pipeline/launch.sh <run> curvesA common/pipeline/curves_queue.sh <run> curvesA 2
RUN=$1; NAME=$2; NW=${3:-2}; MIN_FREE=${MIN_FREE:-24000}
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh
until [ "$(grep -c TRAIN_WORKER_DONE "$RUN/events.txt")" -ge "$NW" ]; do sleep 120; done
sleep $((RANDOM % 60)); ev "CURVES_WORKER_START $NAME"     # staggered so the workers spread over the GPUs
while true; do
  J=$(qpop "$RUN/curves_queue.txt"); [ -z "$J" ] && break
  T=${J%%:*}; M=${J#*:}
  G=""; until G=$(free_gpu "$MIN_FREE"); [ -n "$G" ]; do sleep 60; done
  if CUDA_VISIBLE_DEVICES=$G python common/tools/tb_realval.py "model-$T-track/$M" > "$RUN/curves_${T}_${M}.log" 2>&1; then
    ev "CURVES_DONE $T $M (GPU $G)"; else ev "CURVES_FAIL $T $M (GPU $G)"; fi
  sleep 20                                    # let the GPU memory of the next pick show up in nvidia-smi
done
ev "CURVES_WORKER_DONE $NAME"
