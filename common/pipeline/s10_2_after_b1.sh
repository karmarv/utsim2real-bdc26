#!/usr/bin/env bash
# S10-2 (release 10.2, record 2026-11-12-s10-10.2-clean-final-push.md Section 6): the hand-over after B1's trainings.
# The 12-view jobs of B1's members need GPUs of their own (45 GB), so the first trainer half to finish B1 runs them,
# then trains again; the other half goes straight on. The next trainings (V3, then B2) are queued the moment the first
# half finishes, so the other half never idles.
# 2026-11-13 (record Section 11.5, adopted): B2 (L4) is dropped, so only V3's trainings are queued; the freed time goes
# to second seeds of L3's highest-weight members if gate G-D asks for them (queued separately).
# 2026-11-13 (release 10.3, record docs/decisions/2026-11-13-s10-10.3-final-system.md): V2X also retrains V1's
# three extra draws (the 5-draw bag of routed-c2r) on the calibrated generator, after c1a's four, so the V2X 10.3
# system can be V1's recipe; c1a's recipe stays the fallback.
#   bash common/pipeline/launch.sh <run> s103after common/pipeline/s10_2_after_b1.sh <run>
RUN=$1
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
E=$RUN/events.txt; N0=$(wc -l < "$E")
NEXT=(v2x:dsvt-ros-g1v6aw v2x:voxelrcnn-ros-g1v6d2aw v2x:voxelrcnn-rosf-g1v6aw v2x:voxelrcnn-ros-g1v6aw
      v2x:voxelrcnn-ros-g1v6d3aw v2x:voxelrcnn-ros-g1v6d4aw v2x:voxelrcnn-ros-g1v6d5aw)
T12=(voxelrcnn-rosf-g1v6jn1 pvrcnnpp-ros-g1v6jn1 dsvt-rosf-g1v6n1 voxelrcnn-rosn-g1v6n1 voxelrcnn-rosf-g1v6n1 voxelnext-rosn-g1v6n1)
declare -A G=([trainA3]=1,3,5,7 [trainB3]=0,2,4,6) P=([trainA3]=29641 [trainB3]=29642)
done_w() { tail -n +"$((N0 + 1))" "$E" | grep -q "TRAIN_WORKER_DONE $1$"; }
ev "S10-2 hand-over armed: waits for the first B1 trainer to finish"
X=""; until [ -n "$X" ]; do for w in trainA3 trainB3; do done_w $w && { X=$w; break; }; done; [ -n "$X" ] || sleep 60; done
Y=trainA3; [ "$X" = trainA3 ] && Y=trainB3
for j in "${NEXT[@]}"; do qpush "$RUN/train_queue.txt" "$j"; done
ev "S10-2 hand-over: $X finished B1 first; queued V3 (${#NEXT[@]} trainings); B1's 12-view jobs run on GPUs ${G[$X]}"
J=$RUN/jobs_tta12_s102b1.txt; : > "$J"
for m in "${T12[@]}"; do qpush "$J" "bash $RUN/bin/t12f_job.sh lumpi $m"; done
for g in ${G[$X]//,/ }; do
  bash "$REPO/common/pipeline/launch.sh" "$RUN" "t12b$g" "$REPO/common/pipeline/gpu_queue.sh" "$RUN" "t12b$g" "$J" "$g"
done
for g in ${G[$X]//,/ }; do until tail -n +"$((N0 + 1))" "$E" | grep -q "WORKER_DONE t12b$g$"; do sleep 60; done; done
ev "S10-2 hand-over: B1's 12-view jobs done on GPUs ${G[$X]}; ${X%3}4 trains on them"
bash "$REPO/common/pipeline/launch.sh" "$RUN" "${X%3}4" "$REPO/common/pipeline/train_queue.sh" "$RUN" "${X%3}4" "${G[$X]}" "${P[$X]}"
if done_w "$Y" && [ -s "$RUN/train_queue.txt" ]; then   # the other half ended before the queue was refilled
  bash "$REPO/common/pipeline/launch.sh" "$RUN" "${Y%3}4" "$REPO/common/pipeline/train_queue.sh" "$RUN" "${Y%3}4" "${G[$Y]}" "$((${P[$Y]} + 10))"
fi
ev "S10-2 hand-over complete"
