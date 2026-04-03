"""
Unit tests for MinIO — requires a live MinIO container.

Ensure the following services are running before executing:
  - minio
  - minio_initializer (to pre-create the bucket)

Run with: docker compose run --build --rm tests pytest ./unit
"""

import os
import warnings
from io import BytesIO
from uuid import uuid4

import pytest
from minio import Minio
from minio.error import S3Error

from services.minio_service import MinioService

pytestmark = pytest.mark.asyncio

BUCKET = os.environ.get("MINIO_BUCKET_NAME", "test-bucket")


def _make_client() -> Minio:
    return Minio(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )


# ---------------------------------------------------------------------------
# Connection / bucket
# ---------------------------------------------------------------------------

async def test_minio_connection_is_live():
    warnings.warn(
        "This test requires the minio container to be running.",
        RuntimeWarning,
    )
    client = _make_client()
    assert client.bucket_exists(BUCKET), (
        f"Bucket '{BUCKET}' not found — ensure minio_initializer has run."
    )


async def test_nonexistent_bucket_returns_false():
    warnings.warn(
        "This test requires the minio container to be running.",
        RuntimeWarning,
    )
    client = _make_client()
    assert not client.bucket_exists(f"does-not-exist-{uuid4().hex}")


# ---------------------------------------------------------------------------
# put_object
# ---------------------------------------------------------------------------

async def test_put_object_succeeds():
    warnings.warn(
        "This test requires the minio container to be running.",
        RuntimeWarning,
    )
    client = _make_client()
    key = f"tests/{uuid4().hex}/frame.png"
    data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

    client.put_object(
        bucket_name=BUCKET,
        object_name=key,
        data=BytesIO(data),
        length=len(data),
        content_type="image/png",
    )

    stat = client.stat_object(BUCKET, key)
    assert stat.size == len(data)

    client.remove_object(BUCKET, key)


async def test_put_object_overwrites_existing():
    warnings.warn(
        "This test requires the minio container to be running.",
        RuntimeWarning,
    )
    client = _make_client()
    key = f"tests/{uuid4().hex}/frame.png"

    for payload in (b"first-version", b"second-version"):
        client.put_object(
            bucket_name=BUCKET,
            object_name=key,
            data=BytesIO(payload),
            length=len(payload),
        )

    stat = client.stat_object(BUCKET, key)
    assert stat.size == len(b"second-version")

    client.remove_object(BUCKET, key)


# ---------------------------------------------------------------------------
# get_object
# ---------------------------------------------------------------------------

async def test_get_object_returns_correct_bytes():
    warnings.warn(
        "This test requires the minio container to be running.",
        RuntimeWarning,
    )
    client = _make_client()
    key = f"tests/{uuid4().hex}/frame.png"
    payload = b"hello-openpilot-" + uuid4().bytes

    client.put_object(
        bucket_name=BUCKET,
        object_name=key,
        data=BytesIO(payload),
        length=len(payload),
    )

    response = client.get_object(BUCKET, key)
    try:
        downloaded = response.read()
    finally:
        response.close()
        response.release_conn()

    assert downloaded == payload

    client.remove_object(BUCKET, key)


async def test_get_object_raises_for_missing_key():
    warnings.warn(
        "This test requires the minio container to be running.",
        RuntimeWarning,
    )
    client = _make_client()
    missing_key = f"tests/{uuid4().hex}/does-not-exist.png"

    with pytest.raises(S3Error):
        response = client.get_object(BUCKET, missing_key)
        response.read()


# ---------------------------------------------------------------------------
# MinioService (higher-level wrapper)
# ---------------------------------------------------------------------------

async def test_minio_service_put_segment_log(tmp_path):
    warnings.warn(
        "This test requires the minio container to be running.",
        RuntimeWarning,
    )
    from unittest.mock import MagicMock

    log_file = tmp_path / "logs.json"
    log_file.write_text('{"events": ["start", "end"]}')

    fake_segment = MagicMock()
    fake_segment.route_id = f"db478799b6f9f210/log-test-{uuid4().hex}"
    fake_segment.segment_id = 0

    service = MinioService()
    service.put_segment_log(segment=fake_segment, log_path=log_file)
