"""
Unit tests for Postgres DB connection and repository CRUD.

Requires a live postgres container to be running.
Run with: docker compose run --build --rm tests pytest ./unit
"""

import warnings
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from db.enums import SegmentStatus
from db.models.route import Route
from db.models.segment import Segment
from db.url import build_database_url
from repositories.route_repository import RouteRepository
from repositories.segment_repository import SegmentRepository

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_segment(route_id: str, segment_id: int = 0, status: SegmentStatus = SegmentStatus.UPLOAD_QUEUE) -> Segment:
    """Create a Segment with required start_time and end_time fields populated."""
    return Segment(
        route_id=route_id,
        segment_id=segment_id,
        status=status,
        start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(build_database_url(), pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with SessionLocal() as s:
        async with s.begin():
            yield s
            await s.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def route_repository(session):
    return RouteRepository(session=session)


@pytest_asyncio.fixture
async def segment_repository(session):
    return SegmentRepository(session=session)


# ---------------------------------------------------------------------------
# DB connection / session
# ---------------------------------------------------------------------------

async def test_postgres_connection_is_live(session: AsyncSession):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1


async def test_postgres_session_rollback(session: AsyncSession):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    await session.execute(text("SELECT 1"))
    await session.rollback()


# ---------------------------------------------------------------------------
# RouteRepository CRUD
# ---------------------------------------------------------------------------

async def test_route_repository_add_and_fetch_route(route_repository: RouteRepository, session: AsyncSession):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    route_id = f"db478799b6f9f210/unit-test-route-{uuid4().hex}"
    route = Route(route_id=route_id, status="download queue", file_path=None)
    session.add(route)
    await session.flush()

    fetched = await route_repository.get_by_id(route_id=route_id)  # was: get_route
    assert fetched is not None
    assert fetched.route_id == route_id


async def test_route_repository_get_route_returns_none_when_missing(route_repository: RouteRepository):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    result = await route_repository.get_by_id(route_id="does/not/exist")  # was: get_route
    assert result is None


async def test_route_repository_status_update(route_repository: RouteRepository, session: AsyncSession):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    route_id = f"db478799b6f9f210/unit-test-route-{uuid4().hex}"
    route = Route(route_id=route_id, status="download queue", file_path=None)
    session.add(route)
    await session.flush()

    route.status = "uploading"
    await session.flush()

    fetched = await route_repository.get_by_id(route_id=route_id)  # was: get_route
    assert fetched.status == "uploading"


# ---------------------------------------------------------------------------
# SegmentRepository CRUD
# ---------------------------------------------------------------------------

async def test_segment_repository_add_and_fetch_segment(
    route_repository: RouteRepository,
    segment_repository: SegmentRepository,
    session: AsyncSession,
):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    route_id = f"db478799b6f9f210/unit-test-route-{uuid4().hex}"
    session.add(Route(route_id=route_id, status="download queue", file_path=None))
    await session.flush()

    session.add(_make_segment(route_id=route_id, segment_id=0, status=SegmentStatus.UPLOAD_QUEUE))
    await session.flush()

    segments = await segment_repository.get_by_route(route_id=route_id)  # was: get_segments_by_route
    assert len(segments) == 1
    assert segments[0].status == SegmentStatus.UPLOAD_QUEUE


async def test_segment_repository_get_next_upload_queue_segment(
    segment_repository: SegmentRepository,
    session: AsyncSession,
):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    route_id = f"db478799b6f9f210/unit-test-route-{uuid4().hex}"
    session.add(Route(route_id=route_id, status="download queue", file_path=None))
    await session.flush()

    session.add(_make_segment(route_id=route_id, segment_id=0, status=SegmentStatus.UPLOAD_QUEUE))
    await session.flush()

    segment = await segment_repository.get_next_by_status(status=SegmentStatus.UPLOAD_QUEUE)  # was: get_next_segment_by_status
    assert segment is not None
    assert segment.status == SegmentStatus.UPLOAD_QUEUE


async def test_segment_repository_returns_none_when_queue_empty(segment_repository: SegmentRepository):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    segment = await segment_repository.get_next_by_status(status=SegmentStatus.UPLOAD_QUEUE)  # was: get_next_segment_by_status
    assert segment is None


async def test_segment_status_update(
    segment_repository: SegmentRepository,
    session: AsyncSession,
):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    route_id = f"db478799b6f9f210/unit-test-route-{uuid4().hex}"
    session.add(Route(route_id=route_id, status="download queue", file_path=None))
    await session.flush()

    segment = _make_segment(route_id=route_id, segment_id=0, status=SegmentStatus.UPLOAD_QUEUE)
    session.add(segment)
    await session.flush()

    segment.status = SegmentStatus.FAILED
    await session.flush()

    segments = await segment_repository.get_by_route(route_id=route_id)  # was: get_segments_by_route
    assert segments[0].status == SegmentStatus.FAILED


async def test_stale_uploading_segments_can_be_marked_failed(
    segment_repository: SegmentRepository,
    session: AsyncSession,
):
    warnings.warn(
        "This test requires the postgres container to be running.",
        RuntimeWarning,
    )
    route_id = f"db478799b6f9f210/unit-test-route-{uuid4().hex}"
    session.add(Route(route_id=route_id, status="uploading", file_path=None))
    await session.flush()

    session.add(_make_segment(route_id=route_id, segment_id=0, status=SegmentStatus.UPLOADING))
    await session.flush()

    stale = await segment_repository.get_by_status(status=SegmentStatus.UPLOADING)  # was: get_segments_by_status
    assert any(s.route_id == route_id for s in stale)

    for s in stale:
        if s.route_id == route_id:
            s.status = SegmentStatus.FAILED
    await session.flush()

    updated = await segment_repository.get_by_route(route_id=route_id)  # was: get_segments_by_route
    assert all(s.status == SegmentStatus.FAILED for s in updated)
