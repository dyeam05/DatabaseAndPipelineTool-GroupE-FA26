import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Response, status, APIRouter

from api.dependencies import get_session, get_transactional_session
from db.enums import JobStatus
from db.models.job_run import JobRun
from schemas.job_run import CreateJobRunRequest, JobRunResponse
from services.errors import JobRunNotFoundError
from services.job_run_service import JobRunService
from utilities.service_builder_utilities import build_job_run_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

job_runs_router = APIRouter(
    prefix="/job-runs",
)

@job_runs_router.get("/", response_model=list[JobRunResponse])
async def list_job_runs(
    session: AsyncSession = Depends(get_session),
) -> list[JobRun]:
    logging.info("get job runs")
    job_run_service = build_job_run_service(session=session)
    return await job_run_service.list_job_runs()


@job_runs_router.get("/{job_run_id}", response_model=JobRunResponse)
async def get_job_run(
    job_run_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> JobRun:
    logging.info(f"Getting job run {job_run_id}")
    job_run_service = build_job_run_service(session=session)
    job_run = await job_run_service.get_job_run(job_run_id=job_run_id)
    if job_run is None:
        raise JobRunNotFoundError(job_run_id)
    return job_run


@job_runs_router.post("/", response_model=JobRunResponse, status_code=status.HTTP_201_CREATED)
async def create_job_run(
    payload: CreateJobRunRequest,
    session: AsyncSession = Depends(get_transactional_session),
) -> JobRun:
    logging.info("create job run")
    job_run_service: JobRunService = build_job_run_service(session=session)
    return await job_run_service.create_job_run(
        job_run_id=payload.job_run_id,
        job_def_id=payload.job_def_id,
        route_id=payload.route_id,
        status=JobStatus.QUEUED,
    )


@job_runs_router.delete("/{job_run_id}")
async def delete_job_run(
    job_run_id: UUID,
    session: AsyncSession = Depends(get_transactional_session),
):
    logging.info("delete job run")
    job_run_service = build_job_run_service(session=session)
    await job_run_service.delete_job_run(job_run_id=job_run_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)