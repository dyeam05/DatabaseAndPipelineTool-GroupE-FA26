FROM python:3.12-slim

ENV PYTHONPATH=/app/shared:/app/backend

WORKDIR /app

# system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	curl \
	&& rm -rf /var/lib/apt/lists/*

# python packages
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
	pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application code
COPY shared /app/shared
COPY backend /app/backend

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


