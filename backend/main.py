from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.route import Route
from db.url import build_database_url
from repositories.route_repository import RouteRepository
from schemas.route import CreateRouteRequest, RouteResponse
from services.errors import RouteAlreadyExistsError, RouteNotFoundError
from services.route_service import RouteService


engine = create_async_engine(build_database_url(), pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

app = FastAPI()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_transactional_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_route_service(session: AsyncSession = Depends(get_session)) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)


def get_transactional_route_service(
    session: AsyncSession = Depends(get_transactional_session),
) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)


@app.get("/health-check")
async def health_check() -> dict[str, str]:
    return {"status": "alive"}


@app.exception_handler(RouteAlreadyExistsError)
async def handle_route_exists_error(
    _: Request,
    exc: RouteAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(RouteNotFoundError)
async def handle_route_not_found_error(
    _: Request,
    exc: RouteNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.post("/routes", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    payload: CreateRouteRequest,
    route_service: RouteService = Depends(get_transactional_route_service),
) -> Route:
    return await route_service.create_route(
        route_id=payload.route_id,
        status=payload.status,
    )


@app.get("/routes", response_model=list[RouteResponse])
async def list_routes(
    route_service: RouteService = Depends(get_route_service),
) -> list[Route]:
    return await route_service.list_routes()


@app.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: str,
    route_service: RouteService = Depends(get_route_service),
) -> Route:
    route = await route_service.get_route(route_id=route_id)
    if route is None:
        raise RouteNotFoundError(route_id)

    return route
