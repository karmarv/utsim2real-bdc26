#!/usr/bin/env bash
# Release 10.5 architecture arm (docs/decisions/2026-11-14-s10-10.5-final-push.md Section 10): train one member on all
# eight GPUs (40 epochs, seed 666), verify the epoch-40 checkpoint, then post-process it (member_post.sh: plain and
# 4-view tuning on realval, curves).
#   bash common/pipeline/launch.sh <run> tf1 common/pipeline/s10_5_tf.sh <run> <track> <member> [gpus] [port] [seed] [wait-event]
RUN=$1; T=$2; M=$3; GPUS=${4:-0,1,2,3,4,5,6,7}; PORT=${5:-29655}; SEED=${6:-666}; WAITEV=${7:-}
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh
MD=model-$T-track/$M; NG=$(echo "$GPUS" | tr ',' '\n' | wc -l)
# the wait matches an event at the start of a line (after its 20-character time stamp), never text inside another line
[ -n "$WAITEV" ] && until awk -v w="$WAITEV" 'substr($0, 21, length(w)) == w {f=1} END {exit !f}' "$RUN/events.txt"; do sleep 60; done
ev "TRAIN_START $T $M seed $SEED (s10_5_tf, $NG GPUs)"
CUDA_VISIBLE_DEVICES=$GPUS MASTER_PORT=$PORT bash "$MD/train/train.sh" "$NG" run1 --fix_random_seed --workers 6 --seed "$SEED" > "$RUN/train_${T}_${M}.log" 2>&1
RC=$?
if [ -f "$MD/$CK_REL" ] && ckpt_ok "$MD/$CK_REL"; then ev "TRAIN_DONE $T $M (exit $RC, epoch-40 checkpoint verified)"
else ev "TRAIN_FAIL $T $M (exit $RC)"; exit 1; fi
POST="$(dirname "$0")/lib_member_post.sh"; [ -f "$POST" ] || POST="$(dirname "$0")/member_post.sh"
bash "$POST" "$RUN" "$T" "$M"
