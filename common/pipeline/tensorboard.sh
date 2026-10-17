#!/usr/bin/env bash
# TensorBoard over every model's training outputs (OpenPCDet losses and learning rate in tensorboard/, realval curves
# in tensorboard_realval/), bound to localhost. Run detached and view through SSH port forwarding:
#   bash common/pipeline/launch.sh $BDC_DATA/logs/tensorboard tensorboard common/pipeline/tensorboard.sh [port]
#   ssh -N -L 6006:localhost:6006 <user>@<server>      # on your machine, then open http://localhost:6006
# Run names are <track>/<model>/<run>. A supervisor loop restarts TensorBoard when a new run folder appears (checked
# every 10 minutes), so runs started later show up without a manual restart; killing this script stops TensorBoard.
PORT=${1:-6006}
REPO=${BDC_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}
cd "$REPO"; source common/env/activate.sh
spec() {
  local S="" d t m r
  for d in model-*-track/*/train/output/pcdet_model/*/; do
    [ -d "$d/tensorboard" ] || [ -d "$d/tensorboard_realval" ] || continue
    t=$(echo "$d" | cut -d/ -f1 | sed 's/model-//; s/-track//'); m=$(echo "$d" | cut -d/ -f2); r=$(basename "$d")
    S="${S:+$S,}$t/$m/$r:$REPO/$d"
  done
  echo "$S"
}
TB=""; CUR=""
trap '[ -n "$TB" ] && kill "$TB" 2>/dev/null; exit 0' TERM INT
while true; do
  NEW=$(spec)
  if [ "$NEW" != "$CUR" ] || ! kill -0 "$TB" 2>/dev/null; then
    if [ -n "$TB" ]; then kill "$TB" 2>/dev/null; wait "$TB" 2>/dev/null; sleep 5; fi
    tensorboard --logdir_spec "$NEW" --host 127.0.0.1 --port "$PORT" --reload_interval 120 &
    TB=$!; CUR=$NEW
    echo "$(date '+%F %T') tensorboard pid $TB on 127.0.0.1:$PORT with $(echo "$NEW" | tr ',' '\n' | grep -c .) runs"
  fi
  sleep 600 & wait $!
done
