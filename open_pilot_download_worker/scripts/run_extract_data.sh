#!/usr/bin/env bash
set -euo pipefail
set -x

if [ "$#" -lt 1 ]; then
	echo "Usage: $0 <output_dir>"
	exit 1
fi

output_dir="$1"

source ~/miniconda3/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME
cd /app/openpilot/
source ./.venv/bin/activate

python ./selfdrive/modeld/extract_data.py --output_dir "$output_dir"