FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV CONDA_ENV_NAME=openpilot
ENV RUN_MODEL_ON_CPU_OR_NOT=true
ENV REPLACE_CEREAL_SERVICE_OR_NOT=true

WORKDIR /app

# Copy over code for initializaation
COPY open_pilot_download_worker/scripts /app/scripts/
COPY open_pilot_download_worker/files /app/files/

# Run initialization scripts
RUN chmod +x ./scripts/setup-openpilot.sh && ./scripts/setup-openpilot.sh

# Copy over code to run
COPY open_pilot_download_worker/src /app/src/

WORKDIR /app/src
# Entrypoint
CMD ["python", "main.py"]




