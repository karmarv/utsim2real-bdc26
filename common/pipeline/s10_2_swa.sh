#!/usr/bin/env bash
# S10-2 (release 10.2): the weight-averaged members of B2's recipe (record Section 4, L4 = c2r's recipe). When a base
# member's training is done, average its epochs 31-40 (common/tools/swa_ckpt.py), mark the card S10-2 L4, check rule 1
# and queue the averaged member for post-processing (8-view and TTA tuning), as for every S10 averaged member.
#   bash common/pipeline/launch.sh <run> s102swa common/pipeline/s10_2_swa.sh <run>
RUN=$1
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh
BASES=(lumpi:voxelrcnn-rosf-g1v6n1 lumpi:voxelrcnn-rosf-g1v6d2n1 lumpi:voxelrcnn-rosf-g1v6d3n1 lumpi:voxelrcnn-rosf-g1v6d4n1
       lumpi:voxelrcnn-rosf-gblobs-g1v6n1 lumpi:voxelrcnn-rosf-gblobs-g1v6d2n1 lumpi:voxelrcnn-rosf-gblobs-g1v6d3n1
       lumpi:pointpillars-rosf-g1v6n1)
declare -A DONE=()
while [ ${#DONE[@]} -lt ${#BASES[@]} ]; do
  for b in "${BASES[@]}"; do
    [ -n "${DONE[$b]:-}" ] && continue
    T=${b%%:*}; M=${b#*:}
    grep -qE "TRAIN_FAIL $T $M " "$RUN/events.txt" && { DONE[$b]=fail; ev "S10-2 swa: $T $M failed training, no average"; continue; }
    grep -qE "TRAIN_DONE $T $M " "$RUN/events.txt" || continue
    S=$(python common/tools/swa_ckpt.py "model-$T-track/$M" --first 31 --last 40 2>&1 | tail -n 1)
    A=${M%-*}-swa-${M##*-}
    if [ -d "model-$T-track/$A" ]; then
      python - "$T" "$A" "$M" <<'PY'
import sys
from pathlib import Path
import yaml
t, a, m = sys.argv[1:]
f = Path(f"model-{t}-track/{a}/model.yaml")
d = yaml.safe_load(f.read_text())
d.update({"strategy": "S10-2", "candidate": "L4",
          "status": f"S10-2 L4: weight average of {m} epochs 31-40 (no training)",
          "realism_frames": "pcdet/g1-v6n1"})
f.write_text(yaml.safe_dump(d, sort_keys=False))
PY
      if python common/tools/clean_check.py "model-$T-track/$A" > /dev/null; then
        qpush "$RUN/post_queue.txt" "$T:$A"; ev "S10-2 swa: $T $A averaged, clean, queued for post-processing"
      else ev "S10-2 swa: $T $A is not clean (rule 1); not queued"; fi
    else ev "S10-2 swa: $T $M averaging gave no folder ($S)"; fi
    DONE[$b]=1
  done
  [ ${#DONE[@]} -lt ${#BASES[@]} ] && sleep 120
done
ev "S10-2 swa: all ${#BASES[@]} averaged members handled"
