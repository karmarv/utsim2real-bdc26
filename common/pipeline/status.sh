#!/usr/bin/env bash
# Status of a pipeline run: bash common/pipeline/status.sh <run_dir>
RUN=${1:?run dir}; REPO=${BDC_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}
echo "=== $(basename "$RUN") status $(date '+%F %T')"
[ -f "$RUN/STATUS.md" ] && { echo "--- STATUS.md (last 15 lines)"; tail -n 15 "$RUN/STATUS.md"; }
echo "--- queues: train $(wc -l < "$RUN/train_queue.txt" 2>/dev/null || echo 0) waiting, post $(wc -l < "$RUN/post_queue.txt" 2>/dev/null || echo 0) waiting"
echo "--- events (last 20)"; tail -n 20 "$RUN/events.txt" 2>/dev/null
echo "--- training progress (epoch checkpoints of runs started by this pipeline)"
grep -h "TRAIN_START" "$RUN/events.txt" 2>/dev/null | awk '{print $4" "$5}' | while read -r T M; do
  d=$REPO/model-$T-track/$M/train/output/pcdet_model/run1/ckpt
  n=$(ls "$d"/checkpoint_epoch_*.pth 2>/dev/null | sed 's/.*epoch_//; s/.pth//' | sort -n | tail -n 1)
  echo "  $T $M: epoch ${n:-0}/40"
done
echo "--- live processes"; while read -r d t name _ pid _; do
  if [ "$pid" != "?" ] && ps -p "$pid" >/dev/null 2>&1; then echo "  $name (pid $pid) running"; else echo "  $name (pid $pid) ended"; fi; done < "$RUN/pids.txt" 2>/dev/null
echo "--- GPUs"; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';'; echo
