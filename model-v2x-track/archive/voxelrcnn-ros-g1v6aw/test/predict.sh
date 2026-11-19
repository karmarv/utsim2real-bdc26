#!/usr/bin/env bash
# Predict on the 50 starting-kit test frames (inference only) -> test/output/predictions.json
#   bash test/predict.sh train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$MODEL_DIR/../../common/env/activate.sh"      # .venv_ut if set up, else conda bdc-train
CKPT=$(realpath "$1")
cd "$BDC_REPO/common/tools"
python pcdet_predict.py "$MODEL_DIR" --ckpt "$CKPT" --frames kit --out "$MODEL_DIR/test/output/predictions.json"
