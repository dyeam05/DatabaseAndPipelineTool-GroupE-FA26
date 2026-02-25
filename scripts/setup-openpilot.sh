#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 3 ]; then
	echo "Usage: $0 <conda_env_name> <run_model_on_cpu_or_not (true or false)> <replace_cereal_service_with_gps_compatible_ceral_serivice_or_not (true or false)>"
	exit 1
fi

echo "Will use ($1) as environment name"
conda_env_name="$1"
run_model_on_cpu="$2"
replace_cereal_with_gps_cereal="$3"


if [ "$run_model_on_cpu" = "true" ]; then
	sudo apt update
	sudo apt install -y pocl-opencl-icd
fi


git clone --filter=blob:none --recurse-submodules --also-filter-submodules https://github.com/commaai/openpilot.git
cd openpilot
git checkout v0.9.8
git lfs pull

if [ "$replace_cereal_with_gps_cereal" = "true" ]; then
	cp ../files/cereal_service_with_gps_kalman.py ./cereal/services.py
fi
conda create -n "$conda_env_name" python=3.12 -y
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$conda_env_name"
pip install uv
# tools/op.sh setup # this errors due to a hash mismatch
uv lock --refresh
tools/op.sh setup # now it works
source .venv/bin/activate
scons -u -j$(nproc)
