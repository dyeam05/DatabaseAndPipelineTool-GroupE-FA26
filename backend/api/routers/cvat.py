import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session
from services.cvat_service import CVATService
from utilities.service_builder_utilities import build_job_run_service, build_job_segment_run_import_service

logger = logging.getLogger(__name__)

cvat_router = APIRouter(
    prefix="/cvat",
)


@cvat_router.get("/active-status")
async def get_cvat_active_status(
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    logger.info("Getting CVAT active status")
    job_run_service = build_job_run_service(session=session)
    import_service = build_job_segment_run_import_service(session=session)
    cvat_service = CVATService()
    return {"active": await cvat_service.is_active(job_run_service, import_service)}


@cvat_router.post("/restart")
async def restart_cvat_server(
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    logger.info("Restarting CVAT server")
    job_run_service = build_job_run_service(session=session)
    import_service = build_job_segment_run_import_service(session=session)
    cvat_service = CVATService()
    elapsed = await cvat_service.restart_server(job_run_service, import_service)
    return {
        "status": "restarted",
        "elapsed_seconds": round(elapsed, 1),
    }