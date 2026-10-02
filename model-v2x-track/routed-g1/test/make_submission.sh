#!/usr/bin/env bash
# Routed model: predict the 50 starting-kit test frames with every member (each with its own
# test/postprocess.yaml), merge per class with model.yaml `route`, package, validate and score realism.
#   bash test/make_submission.sh first [TEAM]
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$MODEL_DIR/../../common/env/activate.sh"      # .venv_ut if set up, else conda bdc-train
TAG=${1:-first}; TEAM=${2:-}
card() { python -c "import yaml;d=yaml.safe_load(open('$MODEL_DIR/model.yaml'));print($1)"; }
TRACK=$(card "d['track']"); SYN=$(card "d['realism_frames']")
cd "$BDC_REPO/common/tools"
PRED=()
for M in $(card "' '.join(d['members'])"); do
  MM=$(card "d['members']['$M']['model']"); CK=$(card "d['members']['$M']['ckpt']")
  python pcdet_predict.py "$MODEL_DIR/../$MM" --ckpt "$MODEL_DIR/../$MM/$CK" --frames kit --out "$MODEL_DIR/test/output/predictions_$M.json"
  PRED+=(--pred "$M=$MODEL_DIR/test/output/predictions_$M.json")
done
python route_predictions.py merge "$MODEL_DIR" "${PRED[@]}" --out "$MODEL_DIR/test/output/predictions.json"
SEL=(); [ -f "$MODEL_DIR/test/synthetic_ids.txt" ] && SEL=(--syn-list "$MODEL_DIR/test/synthetic_ids.txt")
python package_submission.py "$MODEL_DIR" --tag "$TAG" --pred "$MODEL_DIR/test/output/predictions.json" --synthetic "$SYN" \
  --syn-split val "${SEL[@]}" --ckpt "routed: $(card "d['route']")" --team "$TEAM" \
  $([ -f "$MODEL_DIR/validation/results/local_scores.json" ] && echo --local-scores "$MODEL_DIR/validation/results/local_scores.json")
ZIP=$(ls -d "$MODEL_DIR"/submissions/*_"$TAG" | tail -n 1)/submission.zip
MAP=0; [ -f "$MODEL_DIR/validation/results/local_scores.json" ] && MAP=$(python -c "import json;print(json.load(open('$MODEL_DIR/validation/results/local_scores.json'))['realval_A_mAP_3d_0.5_R40'])")
REFS=()
for k in 4 5; do [ -d "$BDC_DATA/$TRACK/pcdet/realism-proxy-$k" ] && REFS+=(--ref "pcdet/realism-proxy-$k"); done
if [ ${#REFS[@]} -gt 0 ]; then python score_realism.py --track "$TRACK" --syn "$ZIP" "${REFS[@]}" --map "$MAP"; fi
echo "upload $ZIP on CodaBench, then: python common/tools/package_submission.py $MODEL_DIR --tag $TAG --record <id> <leaderboard.json>"
