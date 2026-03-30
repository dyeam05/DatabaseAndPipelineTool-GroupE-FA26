import asyncio
import logging
import signal
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from db.enums import JobSegmentRunStatus, JobStatus
from db.url import build_database_url
from repositories.job_run_repository import JobRunRepository
from repositories.job_segment_run_repository import JobSegmentRunRepository
from repositories.job_definition_repository import JobDefinitionRepository
from services.job_run_service import JobRunService
from services.job_definition_service import JobDefinitionService
from services.job_segment_run_service import JobSegmentRunService



POLL_INTERVAL_SECONDS = 1.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


# Helpers
async def _mark_stale_running_jobs_as_failed(job_run_service:JobRunService, job_segment_run_service:JobSegmentRunService):
    stale_jobs = await job_run_service.get_job_runs_by_status(status=JobStatus.RUNNING)
    if not stale_jobs:
        return
    
    # for all of the stale jobs mark both the job_run and job_segment_run as failed
    for job in stale_jobs:
        await job_run_service.set_status(
            job_run_num=job.job_run_num, 
            job_def_id=job.job_def_id, 
            route_id=job.route_id, 
            status=JobStatus.FAILED
        )
        
        segments = await job_segment_run_service.get_segments_by_job_run(
            job_run_num=job.job_run_num,
            job_def_id=job.job_def_id,
            route_id=job.route_id,
        )
        for segment in segments:
            # only stale if it was actively queued or running, if a segment was completed don't set it to failed
            if segment.status in (JobSegmentRunStatus.RUNNING, JobSegmentRunStatus.QUEUED):
                await job_segment_run_service.set_status(
                    job_run_num=segment.job_run_num,
                    job_def_id=segment.job_def_id,
                    route_id=segment.route_id,
                    segment_id=segment.segment_id,
                    status=JobSegmentRunStatus.FAILED,
                )




async def main():
    # create session to access database
    engine = create_async_engine(build_database_url(), pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    stop_event = asyncio.Event()
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        async with SessionLocal() as session:
            job_run_repository = JobRunRepository(session=session)
            job_run_service = JobRunService(job_run_repository=job_run_repository)
            job_def_repository = JobDefinitionRepository(session=session)
            job_def_service = JobDefinitionService(job_definition_repository=job_def_repository)
            job_segment_run_repository = JobSegmentRunRepository(session=session)
            job_segment_run_service = JobSegmentRunService(job_segment_run_repository=job_segment_run_repository)

            await _mark_stale_running_jobs_as_failed(job_run_service, job_segment_run_service)
            await session.commit()

            while not stop_event.is_set():
                job_run = await job_run_service.get_next_job_run_by_status(
                    status=JobStatus.QUEUED
                )
                if job_run is None:
                    await session.rollback()
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue

                await _process_job_run(
                    job_run, job_run_service, job_def_service, session, executor
                )

            logger.info("Stop event received, shutting down worker")
    finally:
        executor.shutdown(wait=False)
        await engine.dispose()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
