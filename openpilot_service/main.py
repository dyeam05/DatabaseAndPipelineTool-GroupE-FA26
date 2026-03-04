from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from lib.models.pipeline_job_models import PipelineJob
from lib.services.pipeline_job_service import PipelineJobService


@dataclass
class Services:
    pipeline_job_service: PipelineJobService | None = None


services = Services()


@asynccontextmanager
async def lifespan(app: FastAPI):
    services.pipeline_job_service = PipelineJobService()
    await services.pipeline_job_service.start()
    try:
        yield
    finally:
        if services.pipeline_job_service is not None:
            await services.pipeline_job_service.stop()

app = FastAPI(lifespan=lifespan)


@app.post("/pipeline-jobs")
async def create_pipeline_job(route_id: str) -> PipelineJob:
    assert services.pipeline_job_service is not None
    job = await services.pipeline_job_service.enqueue(route_id)
    return job


@app.get("/pipeline-jobs/{job_id}")
async def get_pipeline_job(job_id: str) -> PipelineJob:
    assert services.pipeline_job_service is not None
    try:
        job = await services.pipeline_job_service.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    return job


@app.get("/pipeline-jobs")
async def get_pipeline_jobs() -> list[PipelineJob]:
    assert services.pipeline_job_service is not None
    jobs = await services.pipeline_job_service.get_jobs()
    return jobs


@app.post("/pipeline-jobs/{job_id}/cancel")
async def cancel_pipeline_job(job_id: str):
    assert services.pipeline_job_service is not None
    try:
        await services.pipeline_job_service.cancel(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    return {"ok": True}


@app.delete("/pipeline-jobs/{job_id}")
async def delete_pipeline_job(job_id: str):
    assert services.pipeline_job_service is not None
    try:
        await services.pipeline_job_service.remove_job(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"ok": True}
