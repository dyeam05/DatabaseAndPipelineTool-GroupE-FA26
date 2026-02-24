#!/usr/bin/env bash

set -euo pipefail # this makes the script stop if something fails

# make sure the user passed in an arguement for the conda env name
if [ "$#" -lt 1 ]; then
	echo "Usage: $0 conda_env_name"
	exit 1
fi

echo "Will use ($1) as environment name"
conda_env_name="$1"


# clone openpilot
git clone --filter=blob:none --recurse-submodules --also-filter-submodules https://github.com/commaai/openpilot.git
cd openpilot
# checkout v0.9.8
git checkout v0.9.8
git lfs pull
# create conda env - this way we know our python  will be 3.12
conda create -n "$conda_env_name" python=3.12 -y
conda activate "$conda_env_name"
# refresh this because some of the hashes in the uv lock are old
uv lock --refresh
# Run the dependency installer
tools/op.sh setup # now it works
# Activate the venv python env
source .venv/bin/activate
# Build the project
scons -u -j$(nproc)

