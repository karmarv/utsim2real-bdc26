# Shared helpers for the pipeline scripts (sourced). RUN must be set to the run directory.
# the repository root: $BDC_REPO (launch.sh exports it from the launched script's location), else this file's location
REPO=${BDC_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}
CK_REL=train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth
ev() { echo "$(date '+%F %T') $*" >> "$RUN/events.txt"; }
# pop the first line of a queue file under a lock; prints it (empty if the queue is empty)
qpop() {
  local Q=$1 J=""
  exec 9>"$Q.lock"; flock 9
  if [ -s "$Q" ]; then J=$(head -n 1 "$Q"); tail -n +2 "$Q" > "$Q.tmp"; mv "$Q.tmp" "$Q"; fi
  flock -u 9; exec 9>&-
  echo "$J"
}
qpush() { local Q=$1; shift; exec 9>"$Q.lock"; flock 9; echo "$*" >> "$Q"; flock -u 9; exec 9>&-; }
# load-verify an OpenPCDet checkpoint (the after-training evaluation of OpenPCDet races the last save)
ckpt_ok() { python -c "import torch,sys; d=torch.load(sys.argv[1], map_location='cpu'); assert d.get('epoch') is not None and len(d['model_state'])>0" "$1" 2>/dev/null; }
# GPU with the most free memory, if at least $1 MiB are free (empty otherwise)
free_gpu() {
  nvidia-smi --query-gpu=index,memory.total,memory.used --format=csv,noheader,nounits \
    | awk -F', ' -v need="$1" '{f=$2-$3; if (f>=need && f>best) {best=f; g=$1}} END {if (g!="") print g}'
}
