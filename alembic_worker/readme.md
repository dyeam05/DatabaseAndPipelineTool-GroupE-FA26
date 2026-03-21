# Alembic Worker

## Generate New Migration

```docker compose run --rm alembic_worker alembic -c /app/alembic_worker/alembic.ini revision --autogenerate -m "<description>"```