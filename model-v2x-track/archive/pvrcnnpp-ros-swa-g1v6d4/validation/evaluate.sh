#!/usr/bin/env bash
# Predict on a validation split and score it with the challenge-style evaluator; logs a registry row.
#   bash validation/evaluate.sh train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth [DATA] [SPLIT]
# DATA defaults to model.yaml data.realval (real validation set; decisions are made on it), SPLIT to val.
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$MODEL_DIR/../../common/env/activate.sh"      # .venv_ut if set up, else conda bdc-train
CKPT=$(realpath "$1"); DATA=${2:-}; SPLIT=${3:-val}
TRACK=$(python -c "import yaml;print(yaml.safe_load(open('$MODEL_DIR/model.yaml'))['track'])")
NAME=$(python -c "import yaml;print(yaml.safe_load(open('$MODEL_DIR/model.yaml'))['name'])")
[ -n "$DATA" ] || DATA=$(python -c "import yaml;print(yaml.safe_load(open('$MODEL_DIR/model.yaml'))['data']['realval'])")
RUN=$(basename "$(dirname "$(dirname "$CKPT")")")_$(basename "$CKPT" .pth)
OUT="$(echo "$DATA" | tr '/' '_')_${SPLIT}_${RUN}"
cd "$BDC_REPO/common/tools"
python pcdet_predict.py "$MODEL_DIR" --ckpt "$CKPT" --frames "$DATA" --split "$SPLIT" --out "$MODEL_DIR/validation/output/$OUT.json"
python eval_predictions.py --track "$TRACK" --pred "$MODEL_DIR/validation/output/$OUT.json" --data "$DATA" --split "$SPLIT" \
  --out "$MODEL_DIR/validation/results/$OUT.json" --model "$NAME" --run "$RUN"
