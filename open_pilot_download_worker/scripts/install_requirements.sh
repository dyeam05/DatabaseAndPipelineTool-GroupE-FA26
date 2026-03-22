#!/usr/bin/env bash
set -euo pipefail
set -x


source ~/miniconda3/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME
cd /app/openpilot/
source ./.venv/bin/activate

cd ..
pwd
pip install -r requirements.txt