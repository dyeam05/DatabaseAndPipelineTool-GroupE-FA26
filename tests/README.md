# Testing

## End-To-End Tests

### Route Downloading

Ensure that **ONLY** the following containers are running:

- postgres
- backend
- open_pilot_download_worker

Ensure that the database has been reset.

Run the following:

```pytest end_to_end/route_download.py```
