import asyncio
from pathlib import Path
import logging
from re import sub
import signal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.enums import SegmentStatus
from db.models.route import Route
from db.url import build_database_url
from open_pilot_upload_worker.src.models import SegmentDir
from repositories.route_repository import RouteRepository
from repositories.segment_repository import SegmentRepository
from services.errors import RouteNotFoundError
from services.route_service import RouteService, RouteStatus
from services.segment_service import SegmentService
from utilities.directory_utils import does_directory_have_more_than_n_items, get_subdirectories

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

async def upload_segment(route: Route, segment_dir: SegmentDir, route_service: RouteService, segment_service: SegmentService, session: AsyncSession):
    # TODO: Fix this later
    segment_start_time = datetime.now()
    segment_end_time = datetime.now()

    await segment_service.create_segment(
        route_id=route.route_id,
        segment_id=segment_dir.segment_num,
        start_time=segment_start_time,
        end_time=segment_end_time,
        status=SegmentStatus.UPLOADING
    )
    
    # TODO finish this metho



async def _process_route(route: Route, route_service: RouteService, segment_service: SegmentService, session: AsyncSession):
    await route_service.set_status(route_id=route.route_id, status=RouteStatus.UPLOADING)
    await session.commit()

    if not route.file_path:
        await route_service.set_status(route_id=route.route_id, status=RouteStatus.FAILED)
        await session.commit()
        raise ValueError(f"Route {route.route_id} has no file_path")

    data_path = DATA_ROOT / route.file_path
    segment_dirs = get_list_of_segment_dirs(data_path)

    for segment in segment_dirs:
        upload_segment(route, segment, route_service, segment_service, session)







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
                await _process_route(route_to_process, route_service, segment_service, session)





    finally:
        await engine.dispose()
        logger.info("Worker shutdown complete")



if __name__ == "__main__":
    asyncio.run(main())

