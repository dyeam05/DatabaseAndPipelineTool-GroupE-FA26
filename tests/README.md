# Testing

## End-To-End Tests

### Route Downloading/Uploading to MinIO

Ensure that **ONLY** the following containers are running:

- postgres
- backend 
- open_pilot_download_worker
- open_pilot_upload_worker (for end-to-end testing)
- minio (for end-to-end testing)

Ensure that the database has been reset.

Run the following:

```docker compose run --build --rm tests pytest ./end_to_end```

## Unit Tests

Run unit tests with

```docker compose run --build --rm tests pytest ./unit```
