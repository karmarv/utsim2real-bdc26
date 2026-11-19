#!/usr/bin/env bash
# Train this model (outputs: train/output/pcdet_model/<TAG>/). Pick GPUs with CUDA_VISIBLE_DEVICES.
#   CUDA_VISIBLE_DEVICES=4,5,6,7 bash train/train.sh 4 run1
#   CUDA_VISIBLE_DEVICES=1 bash train/train.sh 1 smoke --data pcdet/smoke-v2x --epochs 1
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$MODEL_DIR/../../common/env/activate.sh"      # .venv_ut if set up, else conda bdc-train
NGPUS=${1:-4}; TAG=${2:-run1}; shift $(( $# < 2 ? $# : 2 ))
TRACK=$(python -c "import yaml;print(yaml.safe_load(open('$MODEL_DIR/model.yaml'))['track'])")
DATA=$(python -c "import yaml;print(yaml.safe_load(open('$MODEL_DIR/model.yaml'))['data']['train'])")
for ((i=1; i<=$#; i++)); do [ "${!i}" = "--data" ] && j=$((i+1)) && DATA=${!j}; done
cd "$BDC_REPO/common/tools"
[ -f "$BDC_DATA/$TRACK/$DATA/custom_infos_train.pkl" ] || python pcdet_build_infos.py "$MODEL_DIR" --data "$DATA"
if [ "$NGPUS" -gt 1 ]; then
  torchrun --nproc_per_node="$NGPUS" --master_port="${MASTER_PORT:-$((29500 + RANDOM % 2000))}" pcdet_train.py "$MODEL_DIR" --launcher pytorch --extra_tag "$TAG" "$@"
else
  python pcdet_train.py "$MODEL_DIR" --extra_tag "$TAG" "$@"
fi
