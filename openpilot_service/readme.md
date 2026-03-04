# Openpilot Service

## Installing Dependencies

1. Install `python3.12`
1. Run ```pip install -r requirements.txt``` from inside the `openpilot_service` directory.

## Running Code

Inside the root directory of this repo, run ```fastapi dev opoenpilot_service/main.py```

## Running Test Cases

Run `python -m pytest `.

## Pipeline Job API

This service now exposes a single orchestration job for route logging + segment uploading.

- `POST /pipeline-jobs?route_id=<route>`
- `GET /pipeline-jobs`
- `GET /pipeline-jobs/{job_id}`
- `POST /pipeline-jobs/{job_id}/cancel`
- `DELETE /pipeline-jobs/{job_id}`

Pipeline job status values:

- `queued`
- `logging`
- `uploading`
- `completed`
- `partial_failed`
- `failed`
- `canceled`