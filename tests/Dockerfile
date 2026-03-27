FROM python:3.12-slim

ENV PYTHONPATH=/app/shared

WORKDIR /app

# system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip
RUN pip install --no-cache-dir --upgrade pip

# Shared Python Packages
COPY shared/requirements.txt /app/shared_requirements.txt
RUN pip install --no-cache-dir -r /app/shared_requirements.txt

# python packages
COPY tests/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY shared /app/shared
COPY tests /app

WORKDIR /app

CMD ["pytest", "."]
