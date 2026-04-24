from datetime import datetime

from pydantic import BaseModel, ConfigDict

from db.enums import CameraType, JobStatus


class CreateJobRunRequest(BaseModel):
    job_def_id: int
    route_id: str
    camera: CameraType

class JobRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_run_num: int
    job_def_id: int
    route_id: str
    camera: CameraType
    status: JobStatus
    queued_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    stats: dict | None
