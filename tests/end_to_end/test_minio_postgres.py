import os
import time
import warnings
import pytest
import requests
import subprocess
import psycopg2
import shlex
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

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET_NAME", "data") # Updated to match .env [cite: 2]

TARGET_ROUTE_ID = "db478799b6f9f210|00000086--803d0a7844" # Your fresh route ID

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
        if result: return result
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


# ---------------------------------------------------------------------------
# Atomic Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestOpenPilotPipeline:

    def test_01_cleanup_and_creation(self):
        """Clean old data via API and verify route creation."""
        # 1. Attempt standard API cleanup
        _delete_route(TARGET_ROUTE_ID)
        time.sleep(2) # Give the DB a moment to settle
        
        # 2. Attempt creation
        resp = requests.post(
            ROUTES_URL,
            headers={"accept": "application/json", "Content-Type": "application/json"},
            json={"route_id": TARGET_ROUTE_ID, "status": "download queue"},
            timeout=30,
        )
        # Allow 200 (OK), 201 (Created), or 409 (Conflict/Already Exists)
        # This ensures the test doesn't stop just because the cleanup failed.
        assert resp.status_code in {200, 201}, f"POST failed: {resp.text}"
        
        # 3. Verify it exists and is in a valid starting state
        route = wait_for_route(TARGET_ROUTE_ID)
        
        # Allow 'downloading' or 'uploading' in case the worker picked it up instantly
        valid_statuses = {"download queue", "downloading", "uploading"}
        assert route["status"] in valid_statuses, f"Unexpected status: {route['status']}"

    def test_02_download_completion(self):
        """Wait for download worker to finish (status moving past downloading)."""
        def route_finished_downloading():
            route = _get_route(TARGET_ROUTE_ID)
            if not route: return None
            if route["status"] == "failed":
                pytest.fail(f"Route FAILED: {route}")
            # Fix: Accept 'uploading' if the upload worker already started
            return route if route["status"] in ["upload queue", "uploading", "uploaded"] else None

        route = _poll_until(route_finished_downloading, DOWNLOAD_TIMEOUT_SECONDS, "download completion")
        assert route["file_path"] is not None

    def test_03_segment_status(self):
        """Verify segments exist and are ready for upload."""
        segments = _get_segments_for_route(TARGET_ROUTE_ID)
        assert len(segments) > 0
        for seg in segments:
            assert seg["status"] in ["download queue", "downloading", "upload queue", "uploading", "uploaded"]

    def test_04_upload_completion(self):
        """Wait for all segments to be marked uploaded."""
        def all_segments_uploaded():
            segs = _get_segments_for_route(TARGET_ROUTE_ID)
            return all(s["status"] == "uploaded" for s in segs) if segs else False

        _poll_until(all_segments_uploaded, UPLOAD_TIMEOUT_SECONDS, "all segments uploaded")

    def test_05_minio_and_cleanup(self):
        """Verify files in MinIO using the v1 API path and then delete them."""
        minio = _minio_client()
        
        # Adjust the prefix to match your bucket structure: v1/routes/ID
        # Note: We keep the pipe '|' because your pathing shows it's preserved
        route_path = f"v1/routes/{TARGET_ROUTE_ID}"
        
        # List objects in the 'data' bucket under that specific path
        objects = list(minio.list_objects(
            MINIO_BUCKET, 
            prefix=route_path, 
            recursive=True
        ))
        
        assert len(objects) > 0, f"No files found in MinIO under path: {route_path}"
        print(f"Found {len(objects)} segments in MinIO. Starting cleanup...")

        # Cleanup MinIO to keep the test environment pristine
        for obj in objects:
            minio.remove_object(MINIO_BUCKET, obj.object_name)
            
        # Double check cleanup
        remaining = list(minio.list_objects(MINIO_BUCKET, prefix=route_path, recursive=True))
        assert len(remaining) == 0, "MinIO cleanup failed: some objects still remain."