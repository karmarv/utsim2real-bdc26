#!/usr/bin/env bash
# Release 10.3 (record docs/decisions/2026-11-13-s10-10.3-final-system.md Section 10): the hand-over after the LUMPI
# re-cast retraining (L3q, `C0`'s 14 checkpoints on g1-v6pq / g1-v6d2pq / g1-v6jpq). Same pattern as the 10.2 B1
# hand-over (s10_2_after_b1.sh): the first trainer half to finish runs the six 12-view jobs of the LUMPI members `C0`
# uses with 12 views (45 GB each, GPUs of their own), then trains again; V2X's trainings are queued the moment that half
# finishes, so the other half goes straight on. LUMPI comes first (the entrant, 2026-11-13); V2X gets V3's four
# trainings (routed-c1a's recipe on g1-v6aw). V3x's three extra draws are not queued: they cannot finish in time.
#   bash common/pipeline/launch.sh <run> s103qafter common/pipeline/s10_3_after_lumpi.sh <run>
RUN=$1
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
E=$RUN/events.txt; N0=$(wc -l < "$E")
NEXT=(v2x:dsvt-ros-g1v6aw v2x:voxelrcnn-ros-g1v6d2aw v2x:voxelrcnn-rosf-g1v6aw v2x:voxelrcnn-ros-g1v6aw)
T12=(voxelrcnn-rosf-g1v6jpq pvrcnnpp-ros-g1v6jpq dsvt-rosf-g1v6pq voxelrcnn-rosn-g1v6pq voxelrcnn-rosf-g1v6pq voxelnext-rosn-g1v6pq)
declare -A G=([trainA3]=1,3,5,7 [trainB3]=0,2,4,6) P=([trainA3]=29641 [trainB3]=29642)
done_w() { tail -n +"$((N0 + 1))" "$E" | grep -q "TRAIN_WORKER_DONE $1$"; }
ev "S10-3 hand-over armed: waits for the first trainer to finish the LUMPI re-cast queue"
X=""; until [ -n "$X" ]; do for w in trainA3 trainB3; do done_w $w && { X=$w; break; }; done; [ -n "$X" ] || sleep 60; done
Y=trainA3; [ "$X" = trainA3 ] && Y=trainB3
for j in "${NEXT[@]}"; do qpush "$RUN/train_queue.txt" "$j"; done
ev "S10-3 hand-over: $X finished the LUMPI queue first; queued V3 (${#NEXT[@]} trainings); LUMPI's 12-view jobs run on GPUs ${G[$X]}"
J=$RUN/jobs_tta12_s103q.txt; : > "$J"
for m in "${T12[@]}"; do qpush "$J" "bash $RUN/bin/t12f_job.sh lumpi $m"; done
for g in ${G[$X]//,/ }; do
  bash "$REPO/common/pipeline/launch.sh" "$RUN" "t12q$g" "$REPO/common/pipeline/gpu_queue.sh" "$RUN" "t12q$g" "$J" "$g"
done
for g in ${G[$X]//,/ }; do until tail -n +"$((N0 + 1))" "$E" | grep -q "WORKER_DONE t12q$g$"; do sleep 60; done; done
ev "S10-3 hand-over: LUMPI's 12-view jobs done on GPUs ${G[$X]}; ${X%3}4 trains on them"
bash "$REPO/common/pipeline/launch.sh" "$RUN" "${X%3}4" "$REPO/common/pipeline/train_queue.sh" "$RUN" "${X%3}4" "${G[$X]}" "${P[$X]}"
if done_w "$Y" && [ -s "$RUN/train_queue.txt" ]; then   # the other half ended before the queue was refilled
  bash "$REPO/common/pipeline/launch.sh" "$RUN" "${Y%3}4" "$REPO/common/pipeline/train_queue.sh" "$RUN" "${Y%3}4" "${G[$Y]}" "$((${P[$Y]} + 10))"
fi
ev "S10-3 hand-over complete"
