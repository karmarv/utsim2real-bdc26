#!/usr/bin/env bash
# Generic GPU worker: pops shell command lines from a queue file and runs each on one fixed GPU, one at a time (a GPU
# shared by two jobs can change the last digits of inference, so reproduction runs never share one).
#   bash common/pipeline/launch.sh <run> gpu3 common/pipeline/gpu_queue.sh <run> gpu3 <run>/jobs.txt 3
# Every command runs from the repository root with the project environment; log <run>/job_<name>_<k>.log;
# events JOB_START / JOB_DONE / JOB_FAIL <name> <k>, and WORKER_DONE <name> when the queue is empty.
RUN=$1; NAME=$2; Q=$3; GPU=$4
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
cd "$REPO"; source common/env/activate.sh
k=0
while true; do
  J=$(qpop "$Q"); [ -z "$J" ] && break
  k=$((k + 1)); L="$RUN/job_${NAME}_$k.log"
  ev "JOB_START $NAME $k (GPU $GPU): ${J:0:160}"
  if CUDA_VISIBLE_DEVICES=$GPU bash -c "$J" > "$L" 2>&1; then ev "JOB_DONE $NAME $k"; else ev "JOB_FAIL $NAME $k (log $L)"; fi
done
ev "WORKER_DONE $NAME"
