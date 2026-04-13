import os
import time
import warnings
from uuid import uuid4

import psycopg2
import pytest
import requests


POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "db")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "adp_user")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "adp_password")

BASE_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
ROUTES_URL = f"{BASE_URL}/routes/"
JOB_DEFS_URL = f"{BASE_URL}/job-definitions/"
JOB_RUNS_URL = f"{BASE_URL}/job-runs/"

TARGET_ROUTE_ID = "db478799b6f9f210|00000081--23c1159034"
TARGET_CAMERA = "front_regular"

POLL_INTERVAL_SECONDS = 5
ROUTE_UPLOAD_TIMEOUT_SECONDS = 20 * 60
JOB_RUN_TIMEOUT_SECONDS = 20 * 60


def _db_connect():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def _get(url: str) -> requests.Response:
    resp = requests.get(url, headers={"accept": "application/json"}, timeout=30)
    resp.raise_for_status()
    return resp


def _post(url: str, payload: dict, timeout: int = 30) -> requests.Response:
    return requests.post(
        url,
        headers={"accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )


def _delete(url: str, params: dict, timeout: int = 30) -> requests.Response:
    return requests.delete(url, params=params, timeout=timeout)


def _poll_until(condition_fn, timeout: float, description: str):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = condition_fn()
        if result:
            return result
        time.sleep(POLL_INTERVAL_SECONDS)
    pytest.fail(f"Timed out after {timeout}s waiting for: {description}")


def _get_route(route_id: str) -> dict | None:
    routes = _get(ROUTES_URL).json()
    return next((route for route in routes if route["route_id"] == route_id), None)


def _get_job_run(job_def_id: int, job_run_num: int, route_id: str) -> dict | None:
    runs = _get(JOB_RUNS_URL).json()
    return next(
        (
            run for run in runs
            if run["job_def_id"] == job_def_id
            and run["job_run_num"] == job_run_num
            and run["route_id"] == route_id
        ),
        None,
    )


def _fetch_job_segment_runs(job_def_id: int, job_run_num: int, route_id: str) -> list[dict]:
    with _db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT segment_id, status, artifact_id
            FROM job_segment_run
            WHERE job_def_id = %s AND job_run_num = %s AND route_id = %s
            ORDER BY segment_id ASC
            """,
            (job_def_id, job_run_num, route_id),
        )
        rows = cur.fetchall()

    return [
        {
            "segment_id": row[0],
            "status": row[1],
            "artifact_id": row[2],
        }
        for row in rows
    ]


def _delete_route(route_id: str) -> None:
    if not route_id:
        warnings.warn("No route_id provided. _delete_route skipped.")
        return

    try:
        with _db_connect() as conn, conn.cursor() as cur:
            conn.autocommit = True
            cur.execute("DELETE FROM segments WHERE route_id = %s;", (route_id,))
            cur.execute("DELETE FROM routes WHERE route_id = %s;", (route_id,))
    except Exception as exc:
        warnings.warn(f"Failed to delete route '{route_id}': {exc}")


def _cleanup_job_artifacts(job_def_id: int | None, job_run_num: int | None, route_id: str) -> None:
    if job_def_id is not None and job_run_num is not None:
        resp = _delete(
            JOB_RUNS_URL,
            {
                "job_def_id": job_def_id,
                "job_run_num": job_run_num,
                "route_id": route_id,
                "camera": TARGET_CAMERA,
            },
            timeout=10,
        )
        if resp.status_code not in (204, 404):
            warnings.warn(f"Failed to delete job run: {resp.status_code} {resp.text}")

    if job_def_id is not None:
        resp = requests.delete(f"{JOB_DEFS_URL}{job_def_id}", timeout=10)
        if resp.status_code not in (204, 404):
            warnings.warn(f"Failed to delete job definition: {resp.status_code} {resp.text}")


def _wait_for_route_uploaded(route_id: str) -> dict:
    def route_uploaded():
        route = _get_route(route_id)
        if route is None:
            return None
        if route["status"] == "failed":
            pytest.fail(f"Route failed before upload completed: {route}")
        return route if route["status"] == "uploaded" else None

    return _poll_until(route_uploaded, ROUTE_UPLOAD_TIMEOUT_SECONDS, "route upload completion")


def _wait_for_job_run_terminal(job_def_id: int, job_run_num: int, route_id: str) -> dict:
    def job_finished():
        job_run = _get_job_run(job_def_id=job_def_id, job_run_num=job_run_num, route_id=route_id)
        if job_run is None:
            return None
        if job_run["status"] == "failed":
            pytest.fail(f"Job run failed: {job_run}")
        return job_run if job_run["status"] == "succeeded" else None

    return _poll_until(job_finished, JOB_RUN_TIMEOUT_SECONDS, "job run completion")


def _wait_for_job_segment_runs_succeeded(job_def_id: int, job_run_num: int, route_id: str) -> list[dict]:
    def segment_runs_finished():
        segment_runs = _fetch_job_segment_runs(
            job_def_id=job_def_id,
            job_run_num=job_run_num,
            route_id=route_id,
        )
        if not segment_runs:
            return None

        failed_runs = [segment_run for segment_run in segment_runs if segment_run["status"] == "failed"]
        if failed_runs:
            pytest.fail(f"Job segment runs failed: {failed_runs}")

        all_succeeded = all(segment_run["status"] == "succeeded" for segment_run in segment_runs)
        all_have_artifacts = all(segment_run["artifact_id"] is not None for segment_run in segment_runs)
        return segment_runs if all_succeeded and all_have_artifacts else None

    return _poll_until(
        segment_runs_finished,
        JOB_RUN_TIMEOUT_SECONDS,
        "job segment run completion",
    )


@pytest.mark.integration
def test_route_upload_and_job_run_end_to_end():
    job_def_id: int | None = None
    job_run_num: int | None = None
    job_name = f"Integration Route Job {uuid4()}"

    try:
        _delete_route(TARGET_ROUTE_ID)
        time.sleep(2)

        route_create_resp = _post(
            ROUTES_URL,
            {"route_id": TARGET_ROUTE_ID, "status": "download queue"},
        )
        assert route_create_resp.status_code in {200, 201}, (
            f"Route creation failed: {route_create_resp.status_code} {route_create_resp.text}"
        )

        route = _wait_for_route_uploaded(TARGET_ROUTE_ID)
        assert route["file_path"] is not None
        assert route["status"] == "uploaded"

        job_def_resp = _post(
            JOB_DEFS_URL,
            {
                "type": "object_detection",
                "implementation_key": "detr_detection",
                "name": job_name,
                "description": "End-to-end DETR job test",
                "config": {
                    "model_name": "PekingU/rtdetr_v2_r50vd",
                },
            },
            timeout=10,
        )
        assert job_def_resp.status_code == 201, (
            f"Job definition creation failed: {job_def_resp.status_code} {job_def_resp.text}"
        )
        job_def_id = job_def_resp.json()["job_def_id"]

        job_run_resp = _post(
            JOB_RUNS_URL,
            {
                "job_def_id": job_def_id,
                "route_id": TARGET_ROUTE_ID,
                "camera": TARGET_CAMERA,
            },
            timeout=10,
        )
        assert job_run_resp.status_code == 201, (
            f"Job run creation failed: {job_run_resp.status_code} {job_run_resp.text}"
        )
        job_run_data = job_run_resp.json()
        job_run_num = job_run_data["job_run_num"]

        completed_job_run = _wait_for_job_run_terminal(
            job_def_id=job_def_id,
            job_run_num=job_run_num,
            route_id=TARGET_ROUTE_ID,
        )
        assert completed_job_run["status"] == "succeeded"

        segment_runs = _wait_for_job_segment_runs_succeeded(
            job_def_id=job_def_id,
            job_run_num=job_run_num,
            route_id=TARGET_ROUTE_ID,
        )
        assert len(segment_runs) > 0

    finally:
        _cleanup_job_artifacts(
            job_def_id=job_def_id,
            job_run_num=job_run_num,
            route_id=TARGET_ROUTE_ID,
        )
