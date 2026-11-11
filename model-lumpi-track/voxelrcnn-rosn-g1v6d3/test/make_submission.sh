#!/usr/bin/env bash
# From a checkpoint to a validated CodaBench zip in submissions/<date>_<TAG>/ (needs the starting kit ingested:
# python data-<track>/ingest_kit.py <kit.zip>). Inference only on the 50 test frames; nothing is fitted to them.
#   bash test/make_submission.sh train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth first [TEAM]
# Steps: predictions with test/postprocess.yaml -> 50 synthetic frames from model.yaml realism_frames (val split,
# never trained on; V2X gets (0,0,0) nulls at the real rate) -> zip + manifest + validation -> local realism on
# held-out legal proxies (realism-proxy-4/5 when they exist).
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$MODEL_DIR/../../common/env/activate.sh"      # .venv_ut if set up, else conda bdc-train
CKPT=$(realpath "$1"); TAG=${2:-first}; TEAM=${3:-$BDC_TEAM}
card() { python -c "import yaml;d=yaml.safe_load(open('$MODEL_DIR/model.yaml'));print($1)"; }
TRACK=$(card "d['track']"); SYN=$(card "d['realism_frames']")
cd "$BDC_REPO/common/tools"
python pcdet_predict.py "$MODEL_DIR" --ckpt "$CKPT" --frames kit --out "$MODEL_DIR/test/output/predictions.json"
LOCAL=()
[ -f "$MODEL_DIR/validation/results/local_scores.json" ] && LOCAL=(--local-scores "$MODEL_DIR/validation/results/local_scores.json")
# frames chosen by select_realism_frames.py against legal proxies 1-3, if present; else random from the val split
[ -f "$MODEL_DIR/test/synthetic_ids.txt" ] && LOCAL+=(--syn-list "$MODEL_DIR/test/synthetic_ids.txt")
python package_submission.py "$MODEL_DIR" --tag "$TAG" --pred "$MODEL_DIR/test/output/predictions.json" \
  --synthetic "$SYN" --syn-split val --ckpt "$CKPT" --team "$TEAM" "${LOCAL[@]}"
ZIP=$(ls -d "$MODEL_DIR"/submissions/*_"$TAG" | tail -n 1)/submission.zip
REFS=()
for k in 4 5; do [ -d "$BDC_DATA/$TRACK/pcdet/realism-proxy-$k" ] && REFS+=(--ref "pcdet/realism-proxy-$k"); done
MAP=()
if [ -f "$MODEL_DIR/validation/results/local_scores.json" ]; then
  MAP=(--map "$(python -c "import json;print(json.load(open('$MODEL_DIR/validation/results/local_scores.json'))['realval_A_mAP_3d_0.5_R40'])")")
fi
# combined estimate = 0.6 * clip(mAP / 0.7) + 0.4 * R with mAP from realval-A (classes with test GT)
if [ ${#REFS[@]} -gt 0 ]; then python score_realism.py --track "$TRACK" --syn "$ZIP" "${REFS[@]}" "${MAP[@]}"; fi
echo "upload $ZIP on CodaBench, then: python common/tools/package_submission.py $MODEL_DIR --tag $TAG --record <id> <leaderboard.json>"
