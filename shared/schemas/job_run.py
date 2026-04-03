from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from db.enums import JobStatus


class CreateJobRunRequest(BaseModel):
    job_def_id: int
    route_id: str

class JobRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_run_id: UUID
    job_def_id: int
    route_id: str
    status: JobStatus
    queued_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    stats: dict | None