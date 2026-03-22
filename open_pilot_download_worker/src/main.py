import asyncio
import time

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.url import build_database_url
from repositories.route_repository import RouteRepository
from services.route_service import RouteService, RouteStatus


async def main():
    engine = create_async_engine(build_database_url(), pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    route_repository = RouteRepository(session=session)
    route_service = RouteService(route_repository=route_repository)

    while True:
        routes_ready_for_download = await route_service.get_routes_by_status(
            status=RouteStatus.DOWNLOAD_QUEUE
        )
        if len(routes_ready_for_download) < 1:
            time.sleep(2.0)
            continue

        route_to_process = routes_ready_for_download[0]
        print('tet')
        print(route_to_process)


if __name__ == "__main__":
    asyncio.run(main())
