from enum import Enum
from dataclasses import dataclass, field
from typing import Any
import time

class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


@dataclass
class RouteLoggerJob:
    id: str
    route_id: str
    created_at: float = field(default_factory=time.time)
    status: JobStatus = JobStatus.queued
    result: Any | None = None
    error: str | None = None