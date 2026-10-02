#!/usr/bin/env bash
# Real-validation loop for one checkpoint (decisions are made here, never on the leaderboard):
#   bash validation/tune_and_eval.sh train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth [--no-size]
#   bash validation/tune_and_eval.sh <ckpt> --eval-only      # steps 3-4 only (keep the current test/postprocess.yaml)
# 1. raw predictions on realval A (select) and B (check)   -> validation/output/raw_<data>_<split>_<run>.json
# 2. tune_postprocess.py on A, report on B                  -> test/postprocess.yaml (+ .report.json); old kept as .prev
# 3. challenge-style evaluation with the tuned config on A and B (registry rows) -> validation/results/
# 4. validation/results/local_scores.json (mAP A/B; realism added by make_submission.sh)
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$MODEL_DIR/../../common/env/activate.sh"      # .venv_ut if set up, else conda bdc-train
CKPT=$(realpath "$1"); shift
EVAL_ONLY=0
if [ "${1:-}" = "--eval-only" ]; then EVAL_ONLY=1; shift; fi
card() { python -c "import yaml;d=yaml.safe_load(open('$MODEL_DIR/model.yaml'));print($1)"; }
TRACK=$(card "d['track']"); DATA=$(card "d['data']['realval']"); NAME=$(card "d['name']")
RUN=$(basename "$(dirname "$(dirname "$CKPT")")")_$(basename "$CKPT" .pth)
D=$(echo "$DATA" | tr '/' '_'); OUT="$MODEL_DIR/validation/output"; RES="$MODEL_DIR/validation/results"
mkdir -p "$OUT" "$RES"
cd "$BDC_REPO/common/tools"
if [ "$EVAL_ONLY" = 0 ]; then
  for S in val valB; do
    [ -f "$OUT/raw_${D}_${S}_${RUN}.json" ] || \
      python pcdet_predict.py "$MODEL_DIR" --ckpt "$CKPT" --frames "$DATA" --split $S --raw --out "$OUT/raw_${D}_${S}_${RUN}.json"
  done
  PP="$MODEL_DIR/test/postprocess.yaml"
  [ -f "$PP.prev" ] || cp "$PP" "$PP.prev"
  python tune_postprocess.py "$MODEL_DIR" --raw-a "$OUT/raw_${D}_val_${RUN}.json" --raw-b "$OUT/raw_${D}_valB_${RUN}.json" \
    --data "$DATA" --start "$PP.prev" --out "$PP" "$@"
fi
for S in val valB; do
  python pcdet_predict.py "$MODEL_DIR" --ckpt "$CKPT" --frames "$DATA" --split $S --out "$OUT/${D}_${S}_${RUN}.json"
  python eval_predictions.py --track "$TRACK" --pred "$OUT/${D}_${S}_${RUN}.json" --data "$DATA" --split $S \
    --out "$RES/${D}_${S}_${RUN}.json" --model "$NAME" --run "$RUN"
done
python - "$RES" "$D" "$RUN" "$CKPT" <<'PY'
import json, sys
res, d, run, ckpt = sys.argv[1:]
out = {"ckpt": ckpt, "run": run}
for s, k in (("val", "A"), ("valB", "B")):
    r = json.load(open(f"{res}/{d}_{s}_{run}.json"))
    out[f"realval_{k}_mAP_3d_0.5_R40"] = r["mAP_challenge_3d_0.5_R40"]     # classes with test GT only
    out[f"realval_{k}_per_class"] = {c: (v["3d@0.5"]["AP_R40"] if v["3d@0.5"] else None) for c, v in r["per_class"].items()}
json.dump(out, open(f"{res}/local_scores.json", "w"), indent=2)
print(json.dumps(out, indent=2))
PY
