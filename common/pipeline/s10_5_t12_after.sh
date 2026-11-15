#!/usr/bin/env bash
# Release 10.5 record Section 10.5: a member's 12-view tuning once its plain and 4-view tuning is done (POST_DONE), on the
# GPU gpu_queue.sh gives it.   bash common/pipeline/s10_5_t12_after.sh <run> <track> <member>
RUN=$1; T=$2; M=$3
until grep -qE "POST_DONE $T $M\$" "$RUN/events.txt"; do grep -qE "(TRAIN_FAIL|POST_FAIL) $T $M" "$RUN/events.txt" && exit 1; sleep 60; done
bash "$(dirname "$0")/s10_5_t12_job.sh" "$T" "$M"
