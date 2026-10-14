#!/usr/bin/env bash
# Build the project's Python environment in a local virtualenv (.venv_ut at the repository root).
#
#   python3.10 -m venv .venv_ut            # once (the script creates it if missing)
#   bash common/env/setup_venv_ut.sh       # install, build OpenPCDet, install bdc26, verify
#
# Steps: pip install -r requirements.txt with requirements-lock.txt as constraints (exact versions of every package,
# Open3D included: one environment for generation, training and evaluation); clone OpenPCDet 233f849 into $BDC_THIRD_PARTY (if missing) and make its
# Argo2 import optional; build OpenPCDet's CUDA ops (`setup.py develop`, reuses an up-to-date build); install bdc26
# editable; import and GPU check; write .venv_ut/.bdc_ready, which makes common/env/activate.sh prefer this venv.
# Requires: Python 3.10, git, an NVIDIA driver >= 530 and a CUDA toolkit for nvcc ($CUDA_HOME, default 12.8;
# any 12.x works with the cu121 torch wheel).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/bdc26.env"
VENV=${BDC_VENV:-$BDC_REPO/.venv_ut}
PY=${PYTHON:-python3.10}
[ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"
"$VENV/bin/python" -c 'import sys; assert sys.version_info[:2] == (3, 10), sys.version' \
  || { echo "need Python 3.10 in $VENV"; exit 1; }
export PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONNOUSERSITE=1
"$VENV/bin/pip" install --upgrade "pip<25"
"$VENV/bin/pip" install -r "$BDC_REPO/requirements.txt" -c "$BDC_REPO/requirements-lock.txt"

mkdir -p "$BDC_THIRD_PARTY"
if [ ! -d "$PCDET_ROOT" ]; then
  git clone https://github.com/open-mmlab/OpenPCDet.git "$PCDET_ROOT"
  git -C "$PCDET_ROOT" checkout 233f849                      # tested commit
fi
if grep -q "^from .argo2.argo2_dataset import Argo2Dataset" "$PCDET_ROOT/pcdet/datasets/__init__.py"; then
  # `import pcdet` fails without av2 because of an unconditional Argo2 import: make it optional
  sed -i 's/^from .argo2.argo2_dataset import Argo2Dataset/try:\n    from .argo2.argo2_dataset import Argo2Dataset\nexcept ImportError:\n    Argo2Dataset = None/' \
    "$PCDET_ROOT/pcdet/datasets/__init__.py"
fi
( cd "$PCDET_ROOT" && PATH="$CUDA_HOME/bin:$PATH" MAX_JOBS=${MAX_JOBS:-32} "$VENV/bin/python" setup.py develop )
"$VENV/bin/pip" install -e "$BDC_REPO/common"

"$VENV/bin/python" - <<'EOF'
import torch, spconv, numpy, shapely, ot, pcdet, bdc26, open3d
from pcdet.ops.iou3d_nms import iou3d_nms_utils
import numpy as np
b = torch.tensor([[0, 0, 0, 2.0, 1.0, 1.0, 0.0]])
iou = iou3d_nms_utils.boxes_bev_iou_cpu(b, b)
assert abs(float(iou[0, 0]) - 1.0) < 1e-5, iou
print(f"torch {torch.__version__} cuda={torch.cuda.is_available()} gpus={torch.cuda.device_count()} "
      f"spconv {spconv.__version__} numpy {numpy.__version__} shapely {shapely.__version__} pcdet {pcdet.__version__} "
      f"open3d {open3d.__version__}")
EOF
touch "$VENV/.bdc_ready"
echo "ready: source common/env/activate.sh (or $VENV/bin/activate)"
