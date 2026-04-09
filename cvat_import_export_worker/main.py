import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path
import shutil
import signal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.enums import JobSegmentRunReviewStatus
from db.models.job_segment_run_review import JobSegmentRunReview
from db.url import build_database_url
from repositories.artifact_repository import ArtifactRepository
from repositories.frame_artifact_repository import FrameArtifactRepository
from repositories.frame_repository import FrameRepository
from repositories.job_segment_run_repository import JobSegmentRunRepository
from repositories.job_segment_run_review_repository import JobSegmentRunReviewRepository
from repositories.segment_repository import SegmentRepository
from services.artifact_service import ArtifactService
from services.cvat_service import CVATService
from services.errors import JobSegmentRunNotFoundError
from services.frame_artifact_downloader_service import FrameArtifactDownloaderService
from services.frame_artifact_service import FrameArtifactService
from services.frame_service import FrameService
from services.job_segment_artifiact_downloader_service import JobSegmentArtifactDownloaderService
from services.job_segment_run_review_service import JobSegmentRunReviewService
from services.job_segment_run_service import JobSegmentRunService
from services.minio_service import MinioService
from services.segment_artifact_download_service import SegmentArtifactDownloadService
from services.segment_service import SegmentService


POLL_INTERVAL_SECONDS = 1.0
DATA_DIR = Path("/app/cvat_share")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

async def _mark_stale_running_jobs_as_failed(job_segment_run_review_service: JobSegmentRunReviewService):
    logging.info("Marking stale running jobs as failed")
    stale_jobs = await job_segment_run_review_service.get_by_status(status=JobSegmentRunReviewStatus.LOADING)
    for job in stale_jobs:
        logger.warning(f"Stale job: {job} marked as FAILED")
        await job_segment_run_review_service.set_status(
            job_def_id=job.job_def_id,
            job_run_num=job.job_run_num,
            route_id=job.route_id,
            segment_id=job.segment_id,
            status=JobSegmentRunReviewStatus.FAILED
        )

    stale_jobs = await job_segment_run_review_service.get_by_status(status=JobSegmentRunReviewStatus.REMOVING)
    for job in stale_jobs:
        logger.warning(f"Stale job: {job} marked as FAILED")
        await job_segment_run_review_service.set_status(
            job_def_id=job.job_def_id,
            job_run_num=job.job_run_num,
            route_id=job.route_id,
            segment_id=job.segment_id,
            status=JobSegmentRunReviewStatus.FAILED
        )

    logger.info("Completed marking stale running jobs as failed.")


async def _process_loading_job(
    job_segment_run_review:JobSegmentRunReview,
    job_segment_run_review_service:JobSegmentRunReviewService,
    cvat_service:CVATService,
    job_segment_run_service: JobSegmentRunService,
    job_segment_artifact_downloader_service: JobSegmentArtifactDownloaderService,
    session: AsyncSession
):
    logging.info(f"Processing loading job {job_segment_run_review}")
    await job_segment_run_review_service.set_status(
        job_run_num=job_segment_run_review.job_def_id,
        job_def_id=job_segment_run_review.job_def_id,
        route_id=job_segment_run_review.route_id,
        segment_id=job_segment_run_review.segment_id,
        status=JobSegmentRunReviewStatus.LOADING
    )
    await session.commit()


    try:
        # Download job run info from minio
        job_segment_run = await job_segment_run_service.get_job_segment_run(
            job_run_num=job_segment_run_review.job_def_id,
            job_def_id=job_segment_run_review.job_def_id,
            route_id=job_segment_run_review.route_id,
            segment_id=job_segment_run_review.segment_id,
        )
        if not job_segment_run:
            raise JobSegmentRunNotFoundError(
                job_run_num=job_segment_run_review.job_def_id,
                job_def_id=job_segment_run_review.job_def_id,
                route_id=job_segment_run_review.route_id,
                segment_id=job_segment_run_review.segment_id,
            )

        unique_folder_name = str(uuid4())
        dest_path = DATA_DIR / unique_folder_name
        job_segment_run_dir = await job_segment_artifact_downloader_service.download_job_segment_run_artifacts(
            job_segment_run=job_segment_run,
            dest_path=dest_path
        )

        # Create task in cvat
        task_name = f"{job_segment_run_review.route_id}-{job_segment_run_review.segment_id}-{job_segment_run_review.job_def_id}-{job_segment_run_review.job_run_num}-export"
        task_id = cvat_service.create_new_annotated_task_for_job_segment_run_dir(
            job_segment_run_dir=job_segment_run_dir,
            task_name=task_name
        )

        job_segment_run_review.task_id = task_id


        # Remove files
        shutil.rmtree(dest_path)


        await job_segment_run_review_service.set_status(
            job_run_num=job_segment_run_review.job_def_id,
            job_def_id=job_segment_run_review.job_def_id,
            route_id=job_segment_run_review.route_id,
            segment_id=job_segment_run_review.segment_id,
            status=JobSegmentRunReviewStatus.LOADED
        )
        await session.commit()
    except Exception as e:
        logging.error(f"Job loading failed: {job_segment_run_review}", e)
        await job_segment_run_review_service.set_status(
            job_run_num=job_segment_run_review.job_def_id,
            job_def_id=job_segment_run_review.job_def_id,
            route_id=job_segment_run_review.route_id,
            segment_id=job_segment_run_review.segment_id,
            status=JobSegmentRunReviewStatus.FAILED
        )
        await session.commit()

async def _process_removal_job(
    job_segment_run_review:JobSegmentRunReview,
    job_segment_run_review_service:JobSegmentRunReviewService,
    cvat_service:CVATService,
    session: AsyncSession
):
    logging.info(f"Processing loading job {job_segment_run_review}")
    await job_segment_run_review_service.set_status(
        job_run_num=job_segment_run_review.job_def_id,
        job_def_id=job_segment_run_review.job_def_id,
        route_id=job_segment_run_review.route_id,
        segment_id=job_segment_run_review.segment_id,
        status=JobSegmentRunReviewStatus.REMOVING
    )
    await session.commit()


    try:
        # Try to remove job from CVAT
        if not job_segment_run_review.task_id:
            raise ValueError(f"Job segment run review does not have a task id: {job_segment_run_review}")

        cvat_service.delete_task(
            task_id=job_segment_run_review.task_id
        )

        await job_segment_run_review_service.set_status(
            job_run_num=job_segment_run_review.job_def_id,
            job_def_id=job_segment_run_review.job_def_id,
            route_id=job_segment_run_review.route_id,
            segment_id=job_segment_run_review.segment_id,
            status=JobSegmentRunReviewStatus.REMOVED
        )
        await session.commit()
    except Exception as e:
        logging.error(f"Job loading failed: {job_segment_run_review}", e)
        await job_segment_run_review_service.set_status(
            job_run_num=job_segment_run_review.job_def_id,
            job_def_id=job_segment_run_review.job_def_id,
            route_id=job_segment_run_review.route_id,
            segment_id=job_segment_run_review.segment_id,
            status=JobSegmentRunReviewStatus.FAILED
        )
        await session.commit()

async def _process_job(
    job_segment_run_review:JobSegmentRunReview,
    job_segment_run_review_service:JobSegmentRunReviewService,
    job_segment_run_service:JobSegmentRunService,
    job_segment_artifact_downloader_service: JobSegmentArtifactDownloaderService,
    cvat_service:CVATService,
    session: AsyncSession
):
    logging.info(f"Processing {job_segment_run_review}")
    if job_segment_run_review.status == JobSegmentRunReviewStatus.QUEUED_FOR_LOADING:
        await _process_loading_job(
            job_segment_run_review=job_segment_run_review,
            job_segment_run_review_service=job_segment_run_review_service,
            job_segment_run_service=job_segment_run_service,
            job_segment_artifact_downloader_service=job_segment_artifact_downloader_service,
            cvat_service=cvat_service,
            session=session
        )
    elif job_segment_run_review.status == JobSegmentRunReviewStatus.QUEUED_FOR_REMOVAL:
        await _process_removal_job(
            job_segment_run_review=job_segment_run_review,
            job_segment_run_review_service=job_segment_run_review_service,
            cvat_service=cvat_service,
            session=session
        )
    else:
        raise ValueError(f"Invalid status on {job_segment_run_review}")

async def main():
    logger.info("Starting worker")
    
    engine = create_async_engine(
        url=build_database_url(),
        pool_pre_ping=True
    )
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    stop_event = asyncio.Event()
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig=sig, callback=stop_event.set)

    try:
        async with SessionLocal() as session:
            job_segment_run_review_repository = JobSegmentRunReviewRepository(session=session)
            job_segment_run_review_service = JobSegmentRunReviewService(job_segment_run_review_repository)
            frame_repository = FrameRepository(session=session)
            frame_service = FrameService(frame_repository)
            artifact_repository = ArtifactRepository(session=session)
            artifact_service = ArtifactService(artifact_repository)
            cvat_service = CVATService()
            job_segment_run_repository = JobSegmentRunRepository(session=session)
            job_segment_run_service = JobSegmentRunService(job_segment_run_repository)
            minio_service = MinioService()
            segment_repository = SegmentRepository(session)
            segment_service = SegmentService(segment_repository)
            frame_artifact_repository = FrameArtifactRepository(session=session)
            frame_artifact_service = FrameArtifactService(frame_artifact_repository)
            frame_artifact_downloader_service = FrameArtifactDownloaderService(
                frame_service=frame_service,
                frame_artifact_service=frame_artifact_service,
                artifact_service=artifact_service,
                minio_service=minio_service
            )
            segment_artifact_download_service = SegmentArtifactDownloadService(
                frame_service=frame_service,
                frame_artifact_downloader_service=frame_artifact_downloader_service
            )
            job_segment_artifact_downloader_service = JobSegmentArtifactDownloaderService(
                job_segment_run_service=job_segment_run_service,
                artifact_service=artifact_service,
                segment_artifact_download_service=segment_artifact_download_service,
                segment_service=segment_service,
                minio_service=minio_service
            )



            await _mark_stale_running_jobs_as_failed(
                job_segment_run_review_service=job_segment_run_review_service
            )
            await session.commit()

            while not stop_event.is_set():
                logging.info("Checking for queues job segment run reviews")
                job_segment_run_review = await job_segment_run_review_service.get_next_by_statuses(statuses=[JobSegmentRunReviewStatus.QUEUED_FOR_LOADING, JobSegmentRunReviewStatus.QUEUED_FOR_REMOVAL])

                if job_segment_run_review is None:
                    await session.rollback()
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue

                await _process_job(
                    job_segment_run_review=job_segment_run_review,
                    job_segment_run_review_service=job_segment_run_review_service,
                    job_segment_run_service=job_segment_run_service,
                    job_segment_artifact_downloader_service=job_segment_artifact_downloader_service,
                    cvat_service=cvat_service,
                    session=session,
                )






    finally:
        executor.shutdown(wait=False)
        await engine.dispose()
        logger.info("Worker Shutdown Complete")


if __name__ == "__main__":
    asyncio.run(main())
