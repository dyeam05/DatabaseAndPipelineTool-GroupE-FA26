import asyncio
import logging
import time

import docker
from docker.errors import APIError, NotFound
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session
from db.enums import JobSegmentRunImportStatus, JobStatus
from utilities.service_builder_utilities import build_job_run_service, build_job_segment_run_import_service

logger = logging.getLogger(__name__)

cvat_router = APIRouter(prefix="/cvat")

CVAT_CONTAINER_NAME = "cvat_server"
RESTART_TIMEOUT_SECONDS = 10

ACTIVE_IMPORT_STATUSES: list[JobSegmentRunImportStatus] = [
    JobSegmentRunImportStatus.LOADING,
    JobSegmentRunImportStatus.REMOVING,
]

async def _is_cvat_active(session: AsyncSession) -> bool:
    job_run_service = build_job_run_service(session=session)
    import_service = build_job_segment_run_import_service(session=session)

    if await job_run_service.get_next_job_run_by_status(JobStatus.RUNNING) is not None:
        return True
    if await import_service.get_next_by_statuses(ACTIVE_IMPORT_STATUSES) is not None:
        return True
    return False


def _restart_container() -> None:
    client = docker.from_env()
    container = client.containers.get(CVAT_CONTAINER_NAME)
    container.restart(timeout=RESTART_TIMEOUT_SECONDS)


@cvat_router.get("/active-status")
async def get_cvat_active_status(
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return {"active": await _is_cvat_active(session)}


@cvat_router.post("/restart")
async def restart_cvat_server(
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    if await _is_cvat_active(session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot restart CVAT while job runs or CVAT imports are active.",
        )

    logger.info("Restarting %s container", CVAT_CONTAINER_NAME)
    started = time.monotonic()

    try:
        await asyncio.to_thread(_restart_container)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Container '{CVAT_CONTAINER_NAME}' not found",
        )
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker API error while restarting CVAT: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach Docker daemon: {exc}",
        )

    return {
        "status": "restarted",
        "elapsed_seconds": round(time.monotonic() - started, 1),
    }