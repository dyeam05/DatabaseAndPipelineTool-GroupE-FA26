FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/shared

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir sqlalchemy alembic psycopg[binary]

COPY alembic_worker/alembic.ini /app/alembic_worker/alembic.ini
COPY alembic_worker/alembic /app/alembic_worker/alembic
COPY shared /app/shared

CMD ["alembic", "-c", "/app/alembic_worker/alembic.ini", "upgrade", "head"]