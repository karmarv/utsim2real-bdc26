#!/usr/bin/env bash
# Release 10.5 record Section 10.5: when L10's build ends, the continuation rule of the TransFusion line
# (common/tools/s10_5_tf_continue.py). PASS: the third draw trains on GPUs 4-7, the draws' 12-view tuning is queued
# (GPU 3 after the second draw, GPU 7 after the third) and the L11 driver (L9 + the three-draw bag, plain, 4-view and
# 12 views) is armed. FAIL: an event asks for the second draw to be stopped by PID; no L11.
#   bash common/pipeline/launch.sh <run> tfcont common/pipeline/s10_5_tf_cont.sh <run>
RUN=$1
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh
E=$RUN/events.txt; P=$REPO/common/pipeline
st() { ev "S10-5 lumpi tf-line: $*"; }
st "armed: waits for L10's build to end, then the continuation rule"
until grep -qE "routed-s10-5-l10: (DONE|STOPPED)$" "$E"; do sleep 120; done
python common/tools/s10_5_tf_continue.py "$E" routed-s10-5-l10 > "$RUN/s105_tfcont.log" 2>&1; RC=$?
st "continuation rule: $(tr '\n' '|' < "$RUN/s105_tfcont.log" | cut -c1-700)"
if [ $RC != 0 ]; then st "FAIL: the second draw (tf2) is to be stopped by PID; no L11"; st "DONE"; exit 0; fi
bash "$P/launch.sh" "$RUN" tf3 "$P/s10_5_tf.sh" "$RUN" lumpi transfusion-rosf-g1v6d3 4,5,6,7 29657 3234
for g in 3:transfusion-rosf-g1v6d2 7:transfusion-rosf-g1v6d3; do
  J=$RUN/jobs_tta12_${g#*:}.txt; echo "bash $P/s10_5_t12_after.sh $RUN lumpi ${g#*:}" > "$J"
  bash "$P/launch.sh" "$RUN" "t12tf${g%%:*}" "$P/gpu_queue.sh" "$RUN" "t12tf${g%%:*}" "$J" "${g%%:*}"
done
L9Z=$REPO/model-lumpi-track/routed-s10-5-l9/submissions/2026-11-14_s10-5-l9/lumpi_s10-5-l9_submission.zip
TTA12=1 bash "$P/launch.sh" "$RUN" s105l11 "$P/s10_5_build.sh" "$RUN" addmember lumpi routed-s10-5-l9 routed-s10-5-l11 L11 "$L9Z" \
  routed-s10-4-l8 btf6x:bag-transfusion-rosf-g1v6x
st "PASS: third draw (tf3, GPUs 4-7), 12-view jobs (GPUs 3 and 7) and the L11 driver (s105l11) launched"; st "DONE"
