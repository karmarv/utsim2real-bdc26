#!/usr/bin/env bash
# Real-validation loop for one checkpoint (decisions are made here, never on the leaderboard):
#   bash validation/tune_and_eval.sh train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth [--no-size]
#   bash validation/tune_and_eval.sh <ckpt> --eval-only      # steps 3-4 only (keep the current post-processing)
#   bash validation/tune_and_eval.sh <ckpt> --tta flip4+yaw  # the test-time-augmentation variant (strategy S3)
# 1. raw predictions on realval A (select) and B (check)   -> validation/output/raw_<data>_<split>_<run>[_tta].json
# 2. tune_postprocess.py on A, report on B                  -> test/postprocess.yaml (+ .report.json); old kept as .prev
# 3. challenge-style evaluation with the tuned config on A and B (registry rows) -> validation/results/
# 4. validation/results/local_scores.json (mAP A/B; realism added by make_submission.sh)
# --tta VIEWS: predictions are fused over the views (pcdet_predict.py --tta), tuned into test/postprocess_tta.yaml
# from the neutral start test/postprocess.yaml.prev, and every file gets the suffix _tta (local_scores_tta.json);
# a routed model's member with `tta: VIEWS` reads them (common/tools/_common.py member_tag).
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$MODEL_DIR/../../common/env/activate.sh"      # .venv_ut if set up, else conda bdc-train
CKPT=$(realpath "$1"); shift
EVAL_ONLY=0; TTA=""
while [ $# -gt 0 ]; do
  case "$1" in
    --eval-only) EVAL_ONLY=1; shift ;;
    --tta) TTA="$2"; shift 2 ;;
    *) break ;;
  esac
done
card() { python -c "import yaml;d=yaml.safe_load(open('$MODEL_DIR/model.yaml'));print($1)"; }
TRACK=$(card "d['track']"); DATA=$(card "d['data']['realval']"); NAME=$(card "d['name']")
RUN=$(basename "$(dirname "$(dirname "$CKPT")")")_$(basename "$CKPT" .pth)
D=$(echo "$DATA" | tr '/' '_'); OUT="$MODEL_DIR/validation/output"; RES="$MODEL_DIR/validation/results"
SUF=""; PP="$MODEL_DIR/test/postprocess.yaml"; PRED=()
if [ -n "$TTA" ]; then SUF="_tta"; PP="$MODEL_DIR/test/postprocess_tta.yaml"; PRED=(--tta "$TTA"); fi
mkdir -p "$OUT" "$RES"
cd "$BDC_REPO/common/tools"
if [ "$EVAL_ONLY" = 0 ]; then
  for S in val valB; do
    [ -f "$OUT/raw_${D}_${S}_${RUN}${SUF}.json" ] || \
      python pcdet_predict.py "$MODEL_DIR" --ckpt "$CKPT" --frames "$DATA" --split $S --raw "${PRED[@]}" --out "$OUT/raw_${D}_${S}_${RUN}${SUF}.json"
  done
  if [ -n "$TTA" ]; then
    START="$MODEL_DIR/test/postprocess.yaml.prev"; [ -f "$START" ] || START="$MODEL_DIR/test/postprocess.yaml"
  else
    [ -f "$PP.prev" ] || cp "$PP" "$PP.prev"; START="$PP.prev"
  fi
  python tune_postprocess.py "$MODEL_DIR" --raw-a "$OUT/raw_${D}_val_${RUN}${SUF}.json" --raw-b "$OUT/raw_${D}_valB_${RUN}${SUF}.json" \
    --data "$DATA" --start "$START" --out "$PP" "$@"
fi
for S in val valB; do
  python pcdet_predict.py "$MODEL_DIR" --ckpt "$CKPT" --frames "$DATA" --split $S "${PRED[@]}" --postprocess "$PP" --out "$OUT/${D}_${S}_${RUN}${SUF}.json"
  python eval_predictions.py --track "$TRACK" --pred "$OUT/${D}_${S}_${RUN}${SUF}.json" --data "$DATA" --split $S \
    --out "$RES/${D}_${S}_${RUN}${SUF}.json" --model "$NAME" --run "${RUN}${SUF}"
done
python - "$RES" "$D" "${RUN}${SUF}" "$CKPT" "$SUF" <<'PY'
import json, sys
res, d, run, ckpt, suf = sys.argv[1:]
out = {"ckpt": ckpt, "run": run}
for s, k in (("val", "A"), ("valB", "B")):
    r = json.load(open(f"{res}/{d}_{s}_{run}.json"))
    out[f"realval_{k}_mAP_3d_0.5_R40"] = r["mAP_challenge_3d_0.5_R40"]     # classes with test GT only
    out[f"realval_{k}_per_class"] = {c: (v["3d@0.5"]["AP_R40"] if v["3d@0.5"] else None) for c, v in r["per_class"].items()}
json.dump(out, open(f"{res}/local_scores{suf}.json", "w"), indent=2)
print(json.dumps(out, indent=2))
PY
