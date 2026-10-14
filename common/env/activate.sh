# Activate the project environment in the current shell (sourced by every script in data-*/ and model-*/):
#   source common/env/activate.sh
# Order: $BDC_PYENV ("venv" or "conda") if set; else the local virtualenv .venv_ut once setup_venv_ut.sh has
# verified it (.venv_ut/.bdc_ready); else the conda environment bdc-train (common/env/setup_bdc_train.sh).
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$_here/bdc26.env"
_venv=${BDC_VENV:-$BDC_REPO/.venv_ut}
_mode=${BDC_PYENV:-}
if [ -z "$_mode" ]; then
  if [ -f "$_venv/.bdc_ready" ]; then _mode=venv; else _mode=conda; fi
fi
if [ "$_mode" = venv ]; then
  # shellcheck disable=SC1091
  source "$_venv/bin/activate"
else
  eval "$(conda shell.bash hook)"
  conda activate "${BDC_CONDA_ENV:-bdc-train}"
fi
unset _here _venv _mode
