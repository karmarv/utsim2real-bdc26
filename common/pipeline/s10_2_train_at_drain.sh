#!/usr/bin/env bash
# S10-2 (release 10.2): start a 4-GPU training worker once the 12-view workers on its GPUs are done and the GPUs are
# idle, so training never shares a GPU with a 12-view job (45 GB). Then runs train_queue.sh on that half.
#   bash common/pipeline/launch.sh <run> trainA3 common/pipeline/s10_2_train_at_drain.sh <run> trainA3 1,3,5,7 29631 t12x
RUN=$1; NAME=$2; GPUS=$3; PORT=$4; PFX=${5:-t12x}
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
N0=$(wc -l < "$RUN/events.txt")
ev "S10-2 $NAME waits for the 12-view workers ${PFX}{${GPUS}} to finish and GPUs $GPUS to be idle"
for g in ${GPUS//,/ }; do
  until grep -q "WORKER_DONE ${PFX}${g}$" "$RUN/events.txt"; do sleep 60; done
done
for g in ${GPUS//,/ }; do
  until [ "$(nvidia-smi -i "$g" --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 2000 ]; do sleep 30; done
done
ev "S10-2 $NAME: GPUs $GPUS free, training starts"
exec bash "$(dirname "$0")/lib_train_queue.sh" "$RUN" "$NAME" "$GPUS" "$PORT"
