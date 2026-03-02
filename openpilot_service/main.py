from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from lib.services.route_logger_service import RouteLoggerService
from lib.models.route_logger_models import RouteLoggerJob


@dataclass
class Services:
    route_logging_service: RouteLoggerService | None = None


services = Services()


@asynccontextmanager
async def lifespan(app: FastAPI):
    services.route_logging_service = RouteLoggerService()
    await services.route_logging_service.start()
    try:
        yield
    finally:
        if services.route_logging_service is not None:
            await services.route_logging_service.stop()

app = FastAPI(lifespan=lifespan)


@app.post("/jobs")
async def create_job(route_id: str) -> RouteLoggerJob:
    assert services.route_logging_service is not None
    job = await services.route_logging_service.enqueue(route_id)
    return job


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> RouteLoggerJob:
    assert services.route_logging_service is not None
    try:
        job = await services.route_logging_service.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    return job


@app.get("/jobs")
async def get_jobs() -> list[RouteLoggerJob]:
    assert services.route_logging_service is not None
    jobs = await services.route_logging_service.get_jobs()
    return jobs


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    assert services.route_logging_service is not None
    try:
        await services.route_logging_service.cancel(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    return {"ok": True}


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    assert services.route_logging_service is not None
    try:
        await services.route_logging_service.remove_job(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"ok": True}
