# Instructions For Running Data Generation

This document has instructions for using loading and processing Comma VQ runs. This is done using Comma VQ's openpilot repository.

TLDR:

Setup openpilot. Put the ```save_vipc_frames.py``` inside the correct folder. Run ```save_vipc_fames.py``` with a run name to download and process the run.

## Detailed Instructions

### 1. Install openpilot

Install the [openpilot repo](https://github.com/commaai/openpilot).

You can follow the full [istructions](https://github.com/commaai/openpilot/tree/master/tools) or use the simplified ones below.

1. Run ```https://github.com/commaai/openpilot.git```.
    - NOTE: It was recommended to me to use version ```0.9.8```. However, mine worked with the ```main``` branch.
1. Run the setup script from the root directory: ```tools/op.sh setup```.
1. Activate Python Environment: ```source .venv/bin/activate```.
1. Build openpilot: ```scons -u -j$(nproc)```.

### 2. Install the Custom Script

There is a file in this repository called ```save_vipc_frames.py```. We need to move this inside the ```openpilot``` repository. Specifically, it needs to be placed in ```openpilot/tools/camerastream/save_vipc_frames.py```.

### 3. Run the Script

This script can be run as follows:

```tools/camerastream/save_vipc_frames.py --route d34c14daa88a1e86/0000013e--0859dd3dcc --format png --workers 4 --include-log-signals```

Change the route to prepare data for a different route. There are several other settings available. You can view them by typing ```tools/camerastream/save_vipc_frames.py -h```.
