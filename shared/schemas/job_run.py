from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from db.enums import JobStatus


class CreateJobRunRequest(BaseModel):
    job_run_id: UUID
    job_def_id: int
    route_id: str
    status: JobStatus = JobStatus.QUEUED


class JobRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_run_id: UUID
    job_def_id: int
    route_id: str
    status: JobStatus
    queued_at: datetime
    started_at: datetime
    finished_at: datetime
    error: str | None
    stats: dict | None