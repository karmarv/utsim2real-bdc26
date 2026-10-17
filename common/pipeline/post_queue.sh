#!/usr/bin/env bash
# Post-processing worker: pops "track:member" from <run>/post_queue.txt and runs member_post.sh; exits when the queue is
# empty and every training worker of the run has finished (TRAIN_WORKER_DONE count >= the number given).
#   bash common/pipeline/launch.sh <run> postA common/pipeline/post_queue.sh <run> postA <n_train_workers>
RUN=$1; NAME=$2; NW=${3:-2}
D="$(dirname "$0")"; source "$D/lib_common.sh" 2>/dev/null || source "$D/common.sh"
POST="$D/lib_member_post.sh"; [ -f "$POST" ] || POST="$D/member_post.sh"
cd "$REPO"
ev "POST_WORKER_START $NAME"
while true; do
  J=$(qpop "$RUN/post_queue.txt")
  if [ -z "$J" ]; then
    [ "$(grep -c TRAIN_WORKER_DONE "$RUN/events.txt")" -ge "$NW" ] && [ ! -s "$RUN/post_queue.txt" ] && break
    sleep 60; continue
  fi
  bash "$POST" "$RUN" "${J%%:*}" "${J#*:}"
done
ev "POST_WORKER_DONE $NAME"
