# Openpilot Data Pipeline

## Authors

- Noah Pursell
- Trevor Bean
- Vinh Khang Huynh
- Thomas Petersen
- Roman Beames

## Background

This repository contains code for the data pipeline for the [Comma AI](https://comma.ai/) Platform. It is organized as a containerized mono-repo.

## Dependencies (Do These First)

### Docker

1. Install [docker](https://www.docker.com/get-started/) for your operating system.

### Comma AI JWT

1. Get a new jwt on [comma.ai's website](https://jwt.comma.ai)
1. Save this for future steps

### ENV File

1. Create a `.env` file at the root directory, copied from the `.example_env` file
1. Fill out the marked spots

### Minio License

1. Go to the [minio download page](https://www.min.io/download)
1. Download a **FREE** license
1. Create a folder in the root director called `minio`
1. Move the license into the folder. It should be called `minio/minio.license`

## Running the Code

1. Start the databases with ```docker compose up --build -d postgres minio```.
1. Create a database migration with ```docker compose run --build --rm alembic_worker alembic -c /app/alembic_worker/alembic.ini revision --autogenerate -m "first migration"```
1. Push the migration with ```docker compose up --build alembic_worker minio_initializer```
1. Start the backend and open pilot download worker with ```docker compose up --build -d backend open_pilot_download_worker open_pilot_upload_worker```.
1. Start the cvat workers with ```docker compose up --build cvat_worker cvat_import_export_worker```

## Contributing

### Code Organization

#### Backend

The backend code is stored in the `/backend/` folder. This is the primary orchestrator for the pipeline. It acts as an API that is interacted with through the front-end that allows for controlling route downloads, processing, and retrieval. It is a FastAPI deployment. When editing the backend, most code should actually be written in the `/shared/` folder. Keep `/backend/main.py` as minimal as possible.

#### Open Pilot Download Worker

The Open Pilot Download Worker, located in `/open_pilot_download_worker/` is a worker that can download videos and logs from OpenPilot. It does this by watching the `Routes` table in the database for any routes that are ready to be downloaded. When it sees a new route ready to download, it begins to download the route and save it in a folder under `/data/`.

#### Postgres

SQL storage for the project.

#### Alembic Worker

Alembic Worker, located in `/alembic_worker/` is the tool we use for Postgres SQL migrations. It looks at the models defined in the `/shared/db/` code, and updates the SQL database to reflect the schema. Look at `/alembic_worker/readme.md` for information on how to use it.

#### Minio

S3 Bucket storage for the project.

### Shared

This is where the majority of code lives, in the `/shared/` directory. This code is copied into the other containers, such as the backend or the worker containers.

### Data

Do not put any code here. This folder `/data/` is used as a shared volume between workers.

### Ruff

Before commiting any code, run the `ruff` linter and fix any issues found.

`ruff check .`

### Pyright

Before commiting any code, run the `pyright` static type checker and fix any issues found.

`pyright`

## Testing

Testing code is inside the `./tests/` folder. See `./tests/README.md` for more information.

## CVAT Job Extension Notes

CVAT detection implementations live in `shared/cvat_annotation_functions/`. Built-in implementations register themselves through `cvat_detection_registry.py`, and `cvat_worker/main.py` loads them at startup and resolves a job by `implementation_key` plus `config`.

You do not need a new plugin to make a new job definition if an existing implementation already does what you want. Example `POST /job-definitions` payload reusing the built-in `detr_detection` plugin with a different config:

```json
{
  "type": "object_detection",
  "implementation_key": "detr_detection",
  "name": "RT-DETR small threshold test",
  "description": "Reuse existing detector with different config",
  "config": {
    "model_name": "PekingU/rtdetr_v2_r50vd"
  }
}
```

Only add a new plugin when you need a new implementation key or different detection code path.

## TODO

Check out the [course Kanban board](https://cscapstone.cs.ou.edu/pages/account/) for TODOs.

## Important link

- [Comma Connect](https://connect.comma.ai/)

## Comma Routes

- 16 Segments: db478799b6f9f210/00000098--ce43889a70
- 4 Segments: db478799b6f9f210/0000000e--9ecd39f6bc
- 2 Segments: db478799b6f9f210/00000081--23c1159034


## front end

run command 

```docker compose up --build -d frontend```