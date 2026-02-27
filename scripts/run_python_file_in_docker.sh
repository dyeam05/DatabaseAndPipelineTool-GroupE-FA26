#!/usr/bin/env bash
set -euo pipefail
set -x


if [ "$#" -lt 1 ]; then
	echo "Usage: $0 <python_file>"
	exit 1
fi

python_file="$1"

source ~/miniconda3/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME
cd /workspace/openpilot/
source ./.venv/bin/activate

python "$python_file"