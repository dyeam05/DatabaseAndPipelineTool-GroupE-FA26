https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Ubuntu&target_version=24.04&target_type=deb_local

./scripts/setup-openpilot.sh $CONDA_ENV_NAME $RUN_MODEL_ON_CPU_OR_NOT $REPLACE_CEREAL_SERVICE_OR_NOT


1  ls
    2  pwd
    3  cd ~
    4  export DEBIAN_FRONTEND=noninteractive
    5  apt-get update
    6  apt-get install -y --no-install-recommends sudo tzdata locales wget file
    7  sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
    8  export LANG=en_US.UTF-8
    9  export LANGUAGE=en_US:en
   10  export LC_ALL=en_US.UTF-8
   11  export NVIDIA_VISIBLE_DEVICES=all
   12  export NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute
   13  cd ~
   14  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   15  bash ~/Miniconda3-latest-Linux-x86_64.sh -b
   16  source ~/miniconda3/etc/profile.d/conda.sh
   17  conda tos accept
   18  apt-get install -y ca-certificates
   19  update-ca-certificates
   20  cd ~
   21  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   22  bash ~/Miniconda3-latest-Linux-x86_64.sh -b
   23  source ~/miniconda3/etc/profile.d/conda.sh
   24  conda tos accept
   25  cd /workspace/
   26  chmod +x ./scripts/setup-openpilot.sh
   27  ./scripts/setup-openpilot.sh 
   28  ./scripts/setup-openpilot.sh false true
   29  ./scripts/setup-openpilot.sh openpilot false true
   30  apt-get install git git-lfs
   31  ./scripts/setup-openpilot.sh openpilot false true
   32  ls
   33  cd openpilot/
   34  ls
   35  conda activate openpilot
   36  source ./.venv/bin/activate
   37  ./tools/replay/replay db478799b6f9f210/00000040--8afe968813/23 --all --ecam
   38  python tools/lib/auth.py jwt eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk5MzQ0NTgsIm5iZiI6MTc3MjE1ODQ1OCwiaWF0IjoxNzcyMTU4NDU4LCJpZGVudGl0eSI6IjJjMTY4NTM5NTgwZWIyNjYifQ.P8dSyY2CjkDVvFwlc0RYtxkHlwUdoOLT3X_keg8dbBg
   39  ./tools/replay/replay db478799b6f9f210/00000040--8afe968813/23 --all --ecam
   40  history