from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import time


class UploadJobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"

    
@dataclass
class UploadJob:
    id: str
    dir_path: str
    status: UploadJobStatus = UploadJobStatus.queued
    result: str | None = None
    error: str | None = None