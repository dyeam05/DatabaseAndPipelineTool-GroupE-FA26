from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from db.models.route import Route
from db.url import build_database_url
from schemas.route import CreateRouteRequest, RouteResponse
from services.errors import RouteAlreadyExistsError, RouteNotFoundError
from services.route_service import RouteService


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    engine: AsyncEngine = create_async_engine(build_database_url(), pool_pre_ping=True)
    session_local: async_sessionmaker[AsyncSession] = async_sessionmaker(bind=engine, expire_on_commit=False)

    app.state.engine = engine
    app.state.session_local = session_local 

    try:
        yield
    finally:
        await engine.dispose()

app = FastAPI(lifespan=lifespan)

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


@app.get("/routes/{route_id:path}", response_model=RouteResponse)
async def get_route(
    route_id: str,
    route_service: RouteService = Depends(get_route_service),
) -> Route:
    route = await route_service.get_route(route_id=route_id)
    if route is None:
        raise RouteNotFoundError(route_id)

    return route


@app.delete("/routes/{route_id:path}")
async def delete_route(
    route_id: str,
    route_service: RouteService = Depends(get_transactional_route_service)
):
    await route_service.delete_route(route_id=route_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
