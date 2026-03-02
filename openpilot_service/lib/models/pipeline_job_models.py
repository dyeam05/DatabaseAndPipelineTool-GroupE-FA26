from dataclasses import dataclass, field
from enum import Enum
import time


class PipelineJobStatus(str, Enum):
    queued = "queued"
    logging = "logging"
    uploading = "uploading"
    completed = "completed"
    partial_failed = "partial_failed"
    failed = "failed"
    canceled = "canceled"


class PipelineStage(str, Enum):
    queued = "queued"
    logging = "logging"
    uploading_init = "uploading_init"
    uploading_segments = "uploading_segments"
    uploading_finalize = "uploading_finalize"
    finished = "finished"


class SegmentUploadStatus(str, Enum):
    queued = "queued"
    uploading = "uploading"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


@dataclass
class SegmentUploadRecord:
    segment_id: str
    status: SegmentUploadStatus = SegmentUploadStatus.queued
    attempts: int = 0
    max_attempts: int = 0
    error: str | None = None


@dataclass
class PipelineJob:
    id: str
    route_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: PipelineJobStatus = PipelineJobStatus.queued
    stage: PipelineStage = PipelineStage.queued
    output_dir: str | None = None
    segments: list[SegmentUploadRecord] = field(default_factory=list)
    error: str | None = None
