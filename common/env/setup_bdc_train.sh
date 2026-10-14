#!/usr/bin/env bash
# Training / evaluation environment (OpenPCDet). Recipe compiled and import-tested on bdasl-gpu-server
# (driver 570, system nvcc 12.8): Python 3.10, torch 2.1.2 (cu121 wheel), spconv-cu121 2.3.8, numpy 1.23.5.
# numpy >= 1.24 breaks OpenPCDet (np.int / np.float / np.bool); /usr/local/cuda-11.8 must NOT be used with cu121.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/bdc26.env"
ENV=${1:-bdc-train}
eval "$(conda shell.bash hook)"
conda env list | grep -qE "^$ENV\s" || conda create -n "$ENV" python=3.10 -y
conda activate "$ENV"
export PYTHONNOUSERSITE=1 PIP_NO_CACHE_DIR=1
# torch 2.1's cpp_extension imports pkg_resources, which recent setuptools no longer ships
pip install "setuptools<70" wheel
pip install torch==2.1.2 torchvision==0.16.2
pip install spconv-cu121==2.3.8
pip install numpy==1.23.5 numba==0.58.1 llvmlite==0.41.1 scikit-image==0.21.0 opencv-python-headless==4.8.1.78 \
            tensorboardX easydict pyyaml tqdm SharedArray pyquaternion ninja scipy requests pot pytest open3d==0.19.0
# The reference environment is .venv_ut (common/env/setup_venv_ut.sh, requirements.txt + requirements-lock.txt);
# this conda recipe is the fallback and installs the same direct packages.
mkdir -p "$BDC_THIRD_PARTY"
if [ ! -d "$PCDET_ROOT" ]; then
  git clone https://github.com/open-mmlab/OpenPCDet.git "$PCDET_ROOT"
  git -C "$PCDET_ROOT" checkout 233f849   # tested commit
fi
cd "$PCDET_ROOT"
# `import pcdet` fails without av2 because of an unconditional Argo2 import: make it optional.
if grep -q "^from .argo2.argo2_dataset import Argo2Dataset" pcdet/datasets/__init__.py; then
  sed -i 's/^from .argo2.argo2_dataset import Argo2Dataset/try:\n    from .argo2.argo2_dataset import Argo2Dataset\nexcept ImportError:\n    Argo2Dataset = None/' pcdet/datasets/__init__.py
fi
export PATH="$CUDA_HOME/bin:$PATH" MAX_JOBS=${MAX_JOBS:-48}
python setup.py develop
pip install -e "$BDC_REPO/common"
python -c "import torch, spconv, pcdet, bdc26; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'gpus', torch.cuda.device_count(), 'pcdet', pcdet.__version__)"
