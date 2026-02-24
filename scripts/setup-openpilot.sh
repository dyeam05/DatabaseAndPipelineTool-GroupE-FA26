#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
	echo "Usage: $0 conda_env_name"
	exit 1
fi

echo "Will use ($1) as environment name"
conda_env_name="$1"


git clone --filter=blob:none --recurse-submodules --also-filter-submodules https://github.com/commaai/openpilot.git
cd openpilot
git checkout v0.9.8
git lfs pull
conda create -n "$conda_env_name" python=3.12 -y
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$conda_env_name"
# tools/op.sh setup # this errors due to a hash mismatch
uv lock --refresh
tools/op.sh setup # now it works
source .venv/bin/activate
scons -u -j$(nproc)
