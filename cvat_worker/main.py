import asyncio
import logging
import signal
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.job_run import JobRun
from db.enums import JobStatus
from db.url import build_database_url
from repositories.job_run_repository import JobRunRepository
from repositories.job_definition_repository import JobDefinitionRepository
from services.job_run_service import JobRunService
from services.job_definition_service import JobDefinitionService
from services.errors import JobRunNotFoundError

from cvat_client.cvat_client import SegmentJob, run_pipeline_for_segment


POLL_INTERVAL_SECONDS = 1.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


async def _mark_stale_running_jobs_as_failed(job_run_service: JobRunService) -> None:
    stale_jobs = await job_run_service.get_job_runs_by_status(status=JobStatus.RUNNING)
    if not stale_jobs:
        return

    for job_run in stale_jobs:
        await job_run_service.set_error(
            job_run.job_run_id, "Marked failed on worker startup (was still RUNNING)"
        )
        await job_run_service.set_status(job_run.job_run_id, JobStatus.FAILED)
        logger.warning(
            "Marked stale job run as failed on startup: job_run_id=%s", job_run.job_run_id
        )


async def _process_job_run(
    job_run: JobRun,
    job_run_service: JobRunService,
    job_def_service: JobDefinitionService,
    session: AsyncSession,
    executor: ThreadPoolExecutor,
) -> None:
    logger.info("Picked job_run=%s route=%s", job_run.job_run_id, job_run.route_id)

    try:
        await job_run_service.set_status(job_run.job_run_id, JobStatus.RUNNING)
        await session.commit()
        logger.info("Committed status RUNNING for job_run=%s", job_run.job_run_id)
    except JobRunNotFoundError:
        await session.rollback()
        logger.warning(
            "Job run disappeared before processing start: job_run_id=%s", job_run.job_run_id
        )
        return

    try:
        job_def = await job_def_service.get_job_definition(job_run.job_def_id)
        if job_def is None:
            raise RuntimeError(f"Job definition not found: job_def_id={job_run.job_def_id}")

        config = job_def.config
        segment = SegmentJob(
            segment_id=str(config["segment_id"]),
            local_image_dir=config["local_image_dir"],
            share_subdir=config.get("share_subdir"),
            task_title_prefix=config.get("task_title_prefix", "segment"),
            resource_type=config.get("resource_type", "SHARE"),
            conf_threshold=float(config.get("conf_threshold", 0.5)),
        )
        logger.info(
            "Built SegmentJob for job_run=%s segment_id=%s dir=%s",
            job_run.job_run_id,
            segment.segment_id,
            segment.local_image_dir,
        )

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, run_pipeline_for_segment, segment)

        if result.success:
            stats = {
                "task_ids": [tr.task_id for tr in result.task_results],
                "export_paths": [tr.export_path for tr in result.task_results if tr.export_path],
                "duration_seconds": result.duration_seconds,
            }
            await job_run_service.set_stats(job_run.job_run_id, stats)
            await job_run_service.set_status(job_run.job_run_id, JobStatus.SUCCEEDED)
            await session.commit()
            logger.info(
                "Job run succeeded: job_run_id=%s duration=%.1fs",
                job_run.job_run_id,
                result.duration_seconds,
            )
        else:
            await job_run_service.set_error(job_run.job_run_id, result.message)
            await job_run_service.set_status(job_run.job_run_id, JobStatus.FAILED)
            await session.commit()
            logger.error(
                "Job run pipeline failed: job_run_id=%s error=%s",
                job_run.job_run_id,
                result.message,
            )

    except JobRunNotFoundError:
        await session.rollback()
        logger.warning("Job run missing during finalize: job_run_id=%s", job_run.job_run_id)
    except Exception as exc:
        logger.exception(
            "Job run failed with exception: job_run_id=%s error=%s", job_run.job_run_id, exc
        )
        try:
            await job_run_service.set_error(job_run.job_run_id, str(exc))
            await job_run_service.set_status(job_run.job_run_id, JobStatus.FAILED)
            await session.commit()
        except JobRunNotFoundError:
            await session.rollback()
            logger.warning(
                "Job run removed before FAILED update: job_run_id=%s", job_run.job_run_id
            )


async def main():
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

            await _mark_stale_running_jobs_as_failed(job_run_service)
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
