#!/usr/bin/env bash
# S10-2 (release 10.2, record 2026-11-12-s10-10.2-clean-final-push.md Sections 4 and 6): the final C2 builds V2 and L2.
# 1. waits for the final 12-view wave (workers t12x0-7) to finish;
# 2. builds the 12-view bags whose members all have 12-view outputs (bag_predictions.py --tags _tta12);
# 3. V2 (V2X): s10_clean_portfolio.sh on <run>/s10_2_v2_pool.txt, gates: rule 14b against V1 (routed-c2r), R1 allowed;
# 4. once V2's select step is over (the 78 GB step; never two at once), L2 (LUMPI) on <run>/s10_2_l2_pool.txt, gates:
#    rules 14b and 15 against L1 (routed-c2r). Frames: g1-v6 (C0's and c1a's 50 ids). No pool member was trained on a
#    re-cast corpus (the stricter reading of the 2026-11-12 frame rule); rule 1b is checked at packaging.
#   bash common/pipeline/launch.sh <run> s102c2 common/pipeline/s10_2_c2_builds.sh <run>
RUN=$1
source "$(dirname "$0")/lib_common.sh" 2>/dev/null || source "$(dirname "$0")/common.sh"
cd "$REPO"; source common/env/activate.sh; export OMP_NUM_THREADS=2
E=$RUN/events.txt
ev "S10-2 C2 builds armed: wait for the 12-view wave"
for g in 0 1 2 3 4 5 6 7; do until grep -q "WORKER_DONE t12x$g$" "$E"; do sleep 60; done; done
B=$(python - <<'PY'
from pathlib import Path
import yaml
out = []
for t in ("v2x", "lumpi"):
    for b in sorted(Path(f"model-{t}-track").glob("bag-*g1v6x*")):
        d = yaml.safe_load((b / "model.yaml").read_text())
        if d.get("type") != "bag" or (b / "validation/output/pcdet_realval-v1_valB_bag_checkpoint_epoch_40_tta12.json").exists():
            continue
        if all((Path(f"model-{t}-track/{m}/validation/output") / f"pcdet_realval-v1_{s}_run1_checkpoint_epoch_40_tta12.json").exists()
               for m in d["members"] for s in ("val", "valB")):
            out.append(str(b))
print(" ".join(out))
PY
)
ev "S10-2 C2 builds: the wave is done; $(echo $B | wc -w) 12-view bags to build"
for b in $B; do
  python common/tools/bag_predictions.py $b --tags _tta12 > "$RUN/bag12_$(basename $b).log" 2>&1 || ev "S10-2 12-view bag $(basename $b) did not build"
done
ev "S10-2 C2 builds: 12-view bags done; V2 starts"
export BDC_ALLOW_R1=1 S10_ROUTE_BAR=0 S10_GO_P=0.8
S10_INCUMBENT=model-v2x-track/routed-c2r bash common/pipeline/s10_clean_portfolio.sh "$RUN" v2x routed-s10-2-v2 \
  model-v2x-track/routed-c0 s10-2-v2 pcdet/g1-v6 "$BDC_DATA/logs/s9/realism/v2x_g1v6_ids.txt" $(cat "$RUN/s10_2_v2_pool.txt") \
  > "$RUN/s10_2_v2_build.log" 2>&1 &
until grep -qE "S10 v2x s10-2-v2: (select done|select FAILED|.*stopped|.*not clean)" "$E"; do sleep 60; done
ev "S10-2 C2 builds: V2's select step is over; L2 starts"
S10_INCUMBENT=model-lumpi-track/routed-c2r S10_LATE_GATE=Person bash common/pipeline/s10_clean_portfolio.sh "$RUN" lumpi routed-s10-2-l2 \
  model-lumpi-track/routed-c0 s10-2-l2 pcdet/g1-v6 "$RUN/lumpi_c0_ids.txt" $(cat "$RUN/s10_2_l2_pool.txt") \
  > "$RUN/s10_2_l2_build.log" 2>&1
wait
ev "S10-2 C2 builds: both builds ended (see S10 v2x s10-2-v2 and S10 lumpi s10-2-l2 events)"
