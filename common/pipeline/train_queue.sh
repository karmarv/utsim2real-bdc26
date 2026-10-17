#!/usr/bin/env bash
# Training worker on one 4-GPU half: pops "track:member[:seed]" from <run>/train_queue.txt, trains 40 epochs
# (seed given: --fix_random_seed --seed S), verifies the epoch-40 checkpoint and queues the member for post-processing.
#   bash common/pipeline/launch.sh <run> trainA common/pipeline/train_queue.sh <run> trainA 0,1,2,3 29621 [wait-event]
RUN=$1; NAME=$2; GPUS=$3; PORT=$4; WAIT=${5:-}
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh
[ -n "$WAIT" ] && until grep -q "$WAIT" "$RUN/events.txt" 2>/dev/null; do sleep 60; done
ev "TRAIN_WORKER_START $NAME gpus $GPUS"
while true; do
  J=$(qpop "$RUN/train_queue.txt"); [ -z "$J" ] && break
  IFS=: read -r T M SEED <<< "$J"; MD=model-$T-track/$M
  SA=(); [ -n "$SEED" ] && SA=(--seed "$SEED")
  ev "TRAIN_START $T $M ${SEED:+seed $SEED} ($NAME)"
  CUDA_VISIBLE_DEVICES=$GPUS MASTER_PORT=$PORT bash "$MD/train/train.sh" 4 run1 --fix_random_seed --workers 6 "${SA[@]}" > "$RUN/train_${T}_${M}.log" 2>&1
  RC=$?
  if [ -f "$MD/$CK_REL" ] && ckpt_ok "$MD/$CK_REL"; then
    ev "TRAIN_DONE $T $M (exit $RC, epoch-40 checkpoint verified)"; qpush "$RUN/post_queue.txt" "$T:$M"
  else ev "TRAIN_FAIL $T $M (exit $RC)"; fi
done
ev "TRAIN_WORKER_DONE $NAME"
