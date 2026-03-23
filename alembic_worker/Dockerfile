FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/shared

WORKDIR /app

# Install pip
RUN pip install --no-cache-dir --upgrade pip

# Shared Python Packages
COPY shared/requirements.txt /app/shared_requirements.txt
RUN pip install --no-cache-dir -r /app/shared_requirements.txt

# Copy over code files
COPY alembic_worker/alembic.ini /app/alembic_worker/alembic.ini
COPY alembic_worker/alembic /app/alembic_worker/alembic
COPY shared /app/shared

CMD ["alembic", "-c", "/app/alembic_worker/alembic.ini", "upgrade", "head"]
