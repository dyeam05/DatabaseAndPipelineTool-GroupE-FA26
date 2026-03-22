#!/usr/bin/env bash
set -euo pipefail
set -x

if [ "$#" -lt 1 ]; then
	echo "Usage: $0 <replay_id>"
	exit 1
fi

replay_id="$1"

source ~/miniconda3/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME
cd /app/openpilot/
source ./.venv/bin/activate

./tools/replay/replay "$replay_id" --all --ecam