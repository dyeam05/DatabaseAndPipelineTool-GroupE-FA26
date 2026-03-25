import asyncio
from pathlib import Path
import logging
import signal
from datetime import datetime
import shutil

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.segment_dir import SegmentDir
from db.enums import SegmentStatus
from db.models.route import Route
from db.models.segment import Segment
from db.url import build_database_url
from repositories import artifact_repository, frame_artifact_repository
from repositories.frame_repository import FrameRepository
from repositories.route_repository import RouteRepository
from repositories.segment_repository import SegmentRepository
from repositories.frame_artifact_repository import FrameArtifactRepository
from repositories.artifact_repository import ArtifactRepository
from services import frame_uploader_service
from services.frame_artifact_service import FrameArtifactService
from services.frame_service import FrameService
from services.frame_uploader_service import FrameUploaderService
from services.minio_service import MinioService
from services.route_service import RouteService, RouteStatus
from services.segment_service import SegmentService
from services.artifact_service import ArtifactService
from utilities.camera_type_utils import folder_name_to_camera_type
from utilities.directory_utils import does_directory_have_more_than_n_items, get_subdirectories
from utilities.file_utilities import get_pngs_in_directory

POLL_INTERVAL_SECONDS = 2.0
DATA_ROOT = Path("/app/data")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

async def _mark_stale_uploading_routes_as_failed(route_service: RouteService):
    stale_routes = await route_service.get_routes_by_status(status=RouteStatus.UPLOADING)
    if not stale_routes:
        logging.info("No stale routes detected on startup")
        return

    for route in stale_routes:
        await route_service.set_status(route_id=route.route_id, status=RouteStatus.FAILED)
        logger.warning(f"Marked stale route as failed on startupe: route={route.route_id}")


def get_list_of_segment_dirs(route_data_path: Path):
    """
    Assumes that data is in format:
    `route_data_path/segment_number/camera_view/images`
    """

    segment_dirs: list[SegmentDir] = []

    subdirectories = get_subdirectories(route_data_path)
    for subdirectory in subdirectories:
        segment_num = int(subdirectory.name)
        if does_directory_have_more_than_n_items(path=subdirectory, n=20):
            segment_dirs.append(
                SegmentDir(
                    path=subdirectory,
                    segment_num=segment_num
                )
            )

    return segment_dirs

def get_segment_camera_views(segment_dir: SegmentDir) -> list[str]:
    camera_views = [subdirectory.name for subdirectory in get_subdirectories(segment_dir.path)]
    return camera_views


async def upload_segment(route: Route, segment_dir: SegmentDir, segment_service: SegmentService, frame_uploader_service: FrameUploaderService, session: AsyncSession):
    # TODO: Fix this later
    segment_start_time = datetime.now()
    segment_end_time = datetime.now()

    segment = await segment_service.create_segment(
        route_id=route.route_id,
        segment_id=segment_dir.segment_num,
        start_time=segment_start_time,
        end_time=segment_end_time,
        status=SegmentStatus.UPLOADING
    )
    await session.commit()

    # upload images
    minio_service = MinioService()
    for camera_view_folder_name in get_segment_camera_views(segment_dir=segment_dir):
        camera_view = folder_name_to_camera_type(folder_name=camera_view_folder_name)
        for image_path in get_pngs_in_directory(dir=segment_dir.path / camera_view_folder_name):
            frame_number = int(image_path.name.split(".")[0])
            await frame_uploader_service.create_frame(
                segment=segment,
                camera_view=camera_view,
                frame_number=frame_number,
                frame_path=image_path
            )
            
    # upload logs
    log_path = segment_dir.path / "logs.json"
    write_result = minio_service.put_segment_log(
        segment=segment,
        log_path=log_path
    )

    await segment_service.set_status(route_id=segment.route_id, segment_id=segment.segment_id, status=SegmentStatus.UPLOADED)



async def _process_route(route: Route, route_service: RouteService, segment_service: SegmentService, frame_uploader_service: FrameUploaderService, session: AsyncSession):
    await route_service.set_status(route_id=route.route_id, status=RouteStatus.UPLOADING)
    await session.commit()

    if not route.file_path:
        await route_service.set_status(route_id=route.route_id, status=RouteStatus.FAILED)
        await session.commit()
        raise ValueError(f"Route {route.route_id} has no file_path")

    data_path = DATA_ROOT / route.file_path
    segment_dirs = get_list_of_segment_dirs(data_path)


    for segment in segment_dirs:
        logging.info(f"Uploading segment")
        await upload_segment(
            route=route, 
            segment_dir=segment, 
            segment_service=segment_service, 
            session=session,
            frame_uploader_service=frame_uploader_service
        )

    logging.info("Deleting Data Files")
    shutil.rmtree(data_path)

    await route_service.set_status(route_id=route.route_id, status=RouteStatus.UPLOADED)
    await session.commit()


async def main():
    logger.info("Creating DB engine")
    engine = create_async_engine(build_database_url(), pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    logger.info("DB engine created")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        async with SessionLocal() as session:
            route_repository = RouteRepository(session=session)
            route_service = RouteService(route_repository=route_repository)
            segment_repository = SegmentRepository(session=session)
            segment_service = SegmentService(segment_repository=segment_repository)
            frame_repository = FrameRepository(session=session)
            frame_service = FrameService(frame_repository=frame_repository)
            frame_artifact_repository = FrameArtifactRepository(session=session)
            frame_artifact_service = FrameArtifactService(frame_artifact_repository=frame_artifact_repository)
            artifact_repository = ArtifactRepository(session=session)
            artifact_service = ArtifactService(artifact_repository=artifact_repository)
            frame_uploader_service = FrameUploaderService(
                frame_service=frame_service,
                frame_artifact_service=frame_artifact_service,
                artifact_service=artifact_service
            )

            logging.info("Checking for stale routes.")
            await _mark_stale_uploading_routes_as_failed(route_service)
            await session.commit()

            while not stop_event.is_set():
                route_to_process = await route_service.get_next_route_by_status(status=RouteStatus.UPLOAD_QUEUE)

                if route_to_process is None:
                    logging.info("No routes found...")
                    await session.rollback()
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue

                logging.info(f"Route {route_to_process.route_id} found, processing...")
                await _process_route(route=route_to_process, route_service=route_service, segment_service=segment_service, frame_uploader_service=frame_uploader_service, session=session)
                logging.info(f"Route {route_to_process.route_id} uploaded!")





    finally:
        await engine.dispose()
        logger.info("Worker shutdown complete")



if __name__ == "__main__":
    asyncio.run(main())

