from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from db.url import build_database_url
from services.errors import (
    RouteAlreadyExistsError,
    RouteNotFoundError,
    RouteNotReadyForJobRunError,
)

from api.routers.routes import routes_router
from api.routers.segments import segments_router
from api.routers.job_runs import job_runs_router
from api.routers.job_definitions import job_definitions_router
from api.routers.job_segment_run import job_segment_run_router

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


@app.exception_handler(RouteNotReadyForJobRunError)
async def handle_route_not_ready_for_job_run_error(
    _: Request,
    exc: RouteNotReadyForJobRunError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


app.include_router(router=routes_router)
app.include_router(router=segments_router)
app.include_router(router=job_runs_router)
app.include_router(router=job_definitions_router)
app.include_router(router=job_segment_run_router)
