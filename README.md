# Custom Openpilot

This repo contains the tools needed to get OpenPilot up and running.

## Background

OpenPilot is a tool for interfacing/developing with the [Comma AI](https://comma.ai/) Platform. More concretly, it is a code repository.

Setting up the OpenPilot repository can be troublesome. The documentation is poor and different version have poor compaitibility/things break. The purpose of this  repository is to create a system that allows for the easy installation of OpenPilot.

## Version Information

This script builds OpenPilot `v0.9.8`. It will likely not work with any other version.

## Dependencies

## Dependencies Before Running Script

- [cuda 13](https://developer.nvidia.com/cuda-13-0-0-download-archive)
- [nvidia container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### Dependences (Inside Docker, Automatically Installed)

This script requires the following things:

- Ubuntu OS (may work with WSL)
- [Git](https://git-scm.com/install/linux). If you get errors like `error: unknown option also-filter-submodules`, you might need to update your git version.
- [Git LFS](https://git-lfs.com/). Usually can be installed with ```sudo apt-get install git-lfs```.
- conda (can be either [Anaconda Distribution](https://www.anaconda.com/docs/getting-started/anaconda/install#macos-linux-installation) or [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install#macos-linux-installation))

#### Model Dependencies

The OpenPilot models run using [OpenCL](https://en.wikipedia.org/wiki/OpenCL), a GPU-computing framework. As such, in order to run these models, you need to have a device and drivers compatible with OpoenCL. This script has been setup to allow the installation of [pocl-opencl-icd](https://portablecl.org/), which allows your CPU to be used via the OpenCL interface, meaning you do not have a graphics card. Support for using graphics cards will hopefully be added in the future.

## What The Script Does

The main script does the following:

1. If you have specified to use CPU graphics, it installs `pocl-opencl-icd`.
2. Clones the OpenPilot repo.
3. Checks out `v0.9.8`.
4. Pulls any git lfs files.****
5. Copies over `./cereal/services/py` into the OpenPilot repo. This allows us to use the GPS Kalman Service, which is deprecated by default in this version. It is important this is done **before** compiling openpilot, as done in this scriopt.
6. Creates a new conda environment with `python=3.12`.
7. Installs ``uv`` package and does a refresh on the uv lock. This is important because some of the hashes in the OpenPilot repo are not up-to-date, and would result in package download errors if not refreshed.
8. Runs OpenPilot setup script.
9. Compiles OpenPilot

## Usage

### Running the Script

1. Clone the repo: ```git clone https://github.com/CS-4273-Spring2026-GroupI/custom_openpilot.git```.
1. Run ```docker compose up -d```
1. Run ```docker exec -it custom_openpilot-dev-1 ./scripts/setup-openpilot.sh```

### Using OpenPilot Repo

#### Register your JWT

1. Get a new jwt on [comma.ai's website](https://jwt.comma.ai)
2. Apply the jwt with ```docker exec -it custom_openpilot-dev-1 ./scripts/register_jwt_docker.sh <jwt>```

#### Run Replay

Run replay with ```docker exec -it custom_openpilot-dev-1 ./scripts/start_replay_in_docker.sh db478799b6f9f210/00000040--8afe968813```

#### Run Modeld

After the script has run, you can navigate inside the openpilot repo with ```cd ./openpilot```.

### Working inside the container

When you want to run code inside this repo, you **must** do the following in order:

1. Activate your conda environemnt: ```conda activate openpilot```.
2. Activate your venv: ```source ./.venv/bin/activate```.

Then, you can run various code files. For example, ```./tools/replay/replay db478799b6f9f210/00000040--8afe968813/23 --all --ecam```
