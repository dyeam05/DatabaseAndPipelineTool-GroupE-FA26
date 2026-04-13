import os
import time
import warnings

import pytest
import psycopg2
import requests
from minio import Minio

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Postgres connection info (from your environment or defaults)
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")  # 'postgres' if running inside docker network
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "db")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "adp_user")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "adp_password")

BASE_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
# Updated to ensure trailing slash matches FastAPI expectations
ROUTES_URL = f"{BASE_URL}/routes/" 
SEGMENTS_URL = f"{BASE_URL}/segments/"

JOB_DEFS_URL = f"{BASE_URL}/job-definitions/"
JOB_RUNS_URL = f"{BASE_URL}/job-runs/"

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET_NAME", "data") # Updated to match .env [cite: 2]

TARGET_ROUTE_ID = "db478799b6f9f210|00000081--23c1159034" # Your fresh route ID
TARGET_CAMERA = "front_regular"

POLL_INTERVAL_SECONDS = 5
DOWNLOAD_TIMEOUT_SECONDS = 10 * 60 
UPLOAD_TIMEOUT_SECONDS = 10 * 60 

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _get_route(route_id: str) -> dict | None:
    routes = _get(ROUTES_URL).json()
    return next((r for r in routes if r["route_id"] == route_id), None)

def _get_segments_for_route(route_id: str) -> list[dict]:
    segments = _get(SEGMENTS_URL).json()
    return [s for s in segments if s["route_id"] == route_id]

def _poll_until(condition_fn, timeout: float, description: str = "condition"):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = condition_fn()
        if result:
            return result
        time.sleep(POLL_INTERVAL_SECONDS)
    pytest.fail(f"Timed out after {timeout}s waiting for: {description}")



def _delete_route(route_id: str) -> None:
    """
    Delete a specific route and its related segments from the DB.
    Only affects the route/segments for this test; does NOT truncate other data.
    """
    if not route_id:
        warnings.warn("No route_id provided. _delete_route skipped.")
        return

    try:
        # Connect to Postgres
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
        conn.autocommit = True  # Ensure DELETE commits immediately
        cur = conn.cursor()

        # Delete segments for this route
        cur.execute("DELETE FROM segments WHERE route_id = %s;", (route_id,))
        # Delete the route itself
        cur.execute("DELETE FROM routes WHERE route_id = %s;", (route_id,))

        print(f"Deleted route '{route_id}' and its segments from DB.")

        cur.close()
        conn.close()

    except Exception as e:
        warnings.warn(f"Failed to delete route '{route_id}': {e}")

def wait_for_route(route_id: str, timeout: float = 5.0) -> dict:
    """
    Polls FastAPI until the route exists or timeout is reached.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        route = _get_route(route_id)
        if route:
            return route
        time.sleep(0.2)  # small sleep to prevent hammering
    pytest.fail(f"Route '{route_id}' not found after {timeout}s")

def _minio_client() -> Minio:
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)


def _job_definition_payload() -> dict:
    return {
        "type": "object_detection",
        "implementation_key": "detr_detection",
        "name": "Integration Test Detector",
        "config": {"model_name": "PekingU/rtdetr_v2_r18vd"},
        "description": "Integration test for object detection",
    }


def _job_run_payload(job_def_id: int) -> dict:
    return {
        "job_def_id": job_def_id,
        "route_id": TARGET_ROUTE_ID,
        "camera": TARGET_CAMERA,
    }


# ---------------------------------------------------------------------------
# Atomic Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestOpenPilotPipeline:

    def test_01_cleanup_and_creation(self):
        """Clean old data via API and verify route creation."""
        _delete_route(TARGET_ROUTE_ID)
        time.sleep(2)

        resp = _post(
            ROUTES_URL,
            {"route_id": TARGET_ROUTE_ID, "status": "download queue"},
        )
        assert resp.status_code in {200, 201}, f"POST failed: {resp.text}"

        route = wait_for_route(TARGET_ROUTE_ID)

        valid_statuses = {"download queue", "downloading", "upload queue", "uploading"}
        assert route["status"] in valid_statuses, f"Unexpected status: {route['status']}"

    def test_02_job_run_rejected_until_route_uploaded(self):
        """Job runs should be rejected until the route is fully uploaded."""
        job_def_resp = _post(JOB_DEFS_URL, _job_definition_payload(), timeout=10)
        assert job_def_resp.status_code == 201, f"Expected 201, got {job_def_resp.status_code}. API said: {job_def_resp.text}"

        job_def_data = job_def_resp.json()
        pytest.shared_job_def_id = job_def_data["job_def_id"]

        resp = _post(JOB_RUNS_URL, _job_run_payload(job_def_data["job_def_id"]), timeout=10)
        assert resp.status_code == 409, f"Expected 409 before route upload, got {resp.status_code}. API said: {resp.text}"
        assert "not ready for job creation" in resp.text

    def test_03_download_completion(self):
        """Wait for download worker to finish (status moving past downloading)."""
        def route_finished_downloading():
            route = _get_route(TARGET_ROUTE_ID)
            if not route:
                return None
            if route["status"] == "failed":
                pytest.fail(f"Route FAILED: {route}")
            return route if route["status"] in ["upload queue", "uploading", "uploaded"] else None

        route = _poll_until(route_finished_downloading, DOWNLOAD_TIMEOUT_SECONDS, "download completion")
        assert route["file_path"] is not None

    def test_04_segment_status(self):
        """Verify segments exist and are ready for upload."""
        segments = _get_segments_for_route(TARGET_ROUTE_ID)
        assert len(segments) > 0
        for seg in segments:
            assert seg["status"] in ["download queue", "downloading", "upload queue", "uploading", "uploaded"]

    def test_05_upload_completion(self):
        """Wait for all segments to be marked uploaded."""
        def all_segments_uploaded():
            segs = _get_segments_for_route(TARGET_ROUTE_ID)
            return all(s["status"] == "uploaded" for s in segs) if segs else False

        _poll_until(all_segments_uploaded, UPLOAD_TIMEOUT_SECONDS, "all segments uploaded")

    def test_06_create_and_list_job_run(self):
        """Create a job run after upload completion and verify it appears in the list."""
        job_def_id = getattr(pytest, "shared_job_def_id", None)
        assert job_def_id is not None, "Skipping: job_def_id not found from previous test."

        resp = _post(JOB_RUNS_URL, _job_run_payload(job_def_id), timeout=10)
        assert resp.status_code == 201, f"Failed to create Job Run: {resp.text}"
        run_data = resp.json()

        assert run_data["route_id"] == TARGET_ROUTE_ID
        assert run_data["job_def_id"] == job_def_id
        assert "job_run_num" in run_data

        pytest.shared_job_run_num = run_data["job_run_num"]

        list_resp = requests.get(JOB_RUNS_URL, timeout=10)
        assert list_resp.status_code == 200

        runs = list_resp.json()
        found_run = next(
            (
                r for r in runs
                if r["job_run_num"] == pytest.shared_job_run_num
                and r["job_def_id"] == job_def_id
            ),
            None,
        )
        assert found_run is not None, "Newly created job run was not found in the GET / list"

    def test_07_minio_and_cleanup(self):
        """Verify files in MinIO using the v1 API path and then delete them."""
        minio = _minio_client()
        route_path = f"v1/routes/{TARGET_ROUTE_ID}"

        objects = list(minio.list_objects(
            MINIO_BUCKET, 
            prefix=route_path, 
            recursive=True
        ))
        
        assert len(objects) > 0, f"No files found in MinIO under path: {route_path}"
        print(f"Found {len(objects)} segments in MinIO. Starting cleanup...")

        for obj in objects:
            minio.remove_object(MINIO_BUCKET, obj.object_name)

        remaining = list(minio.list_objects(MINIO_BUCKET, prefix=route_path, recursive=True))
        assert len(remaining) == 0, "MinIO cleanup failed: some objects still remain."

    def test_08_cleanup_job_data(self):
        """Clean up the job runs and definitions to ensure a pristine DB state."""
        job_def_id = getattr(pytest, "shared_job_def_id", None)
        job_run_num = getattr(pytest, "shared_job_run_num", None)

        if job_run_num is not None and job_def_id is not None:
            params = {
                "job_def_id": job_def_id,
                "job_run_num": job_run_num,
                "route_id": TARGET_ROUTE_ID,
                "camera": TARGET_CAMERA,
            }
            resp_run = requests.delete(JOB_RUNS_URL, params=params, timeout=10)
            assert resp_run.status_code in (204, 404), f"Failed to delete Job Run: {resp_run.text}"

        if job_def_id is not None:
            resp_def = requests.delete(f"{JOB_DEFS_URL}{job_def_id}", timeout=10)
            assert resp_def.status_code in (204, 404), f"Failed to delete Job Def: {resp_def.text}"
