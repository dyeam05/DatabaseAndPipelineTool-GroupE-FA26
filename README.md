# Openpilot Data Pipeline

## Authors

- Noah Pursell
- Trevor Bean
- Vin Khu Yhn
- Thomas Petersen

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
1. Push the migration with ```docker compose up --build alembic_worker```
1. Start the backend and open pilot download worker with ```docker compose up --build backend open_pilot_download_worker```.

## Contributing

### Code Organization

#### Backend

###
