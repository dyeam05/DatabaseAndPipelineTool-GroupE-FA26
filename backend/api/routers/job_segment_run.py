import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_transactional_session
from db.enums import JobSegmentRunImportStatus
from utilities.service_builder_utilities import build_job_segment_run_import_service

logger = logging.getLogger(__name__)

job_segment_run_router = APIRouter(
    prefix="/job_segment_run",
)

@job_segment_run_router.post("/export_to_cvat")
async def export_job_segment_run_to_cvat(
    route_id: str,
    job_def_id: int,
    job_run_num: int,
    segment_id: int,
    session: AsyncSession = Depends(get_transactional_session)
):
    logging.info("Exporting job segment run to cvat")
    job_segment_run_review_service = build_job_segment_run_import_service(session=session)
    job_segment_run_review = await job_segment_run_review_service.create(
        job_run_num=job_run_num,
        job_def_id=job_def_id,
        route_id=route_id,
        segment_id=segment_id
    )

    return job_segment_run_review

@job_segment_run_router.delete("/export_to_cvat")
async def delete_job_segment_run_in_cvat(
    route_id: str,
    job_def_id: int,
    job_run_num: int,
    segment_id: int,
    session: AsyncSession = Depends(get_transactional_session)
):
    logging.info("Removing job segment run from cvat")
    job_segment_run_review_service = build_job_segment_run_import_service(session=session)
    await job_segment_run_review_service.set_status(
        job_run_num=job_run_num,
        job_def_id=job_def_id,
        route_id=route_id,
        segment_id=segment_id,
        status=JobSegmentRunImportStatus.QUEUED_FOR_REMOVAL
    )



