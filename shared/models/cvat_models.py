from dataclasses import dataclass

@dataclass
class SegmentJob:
    """
    Represents one queued segment from the DB.

    - segment_id: DB / pipeline identifier
    - share_dir: absolute path to the segment folder inside the cvat_share volume
      Example: "/cvat_share/segment_001"
    """
    segment_id: str
    share_dir: str
    task_title_prefix: str = "segment"
    resource_type: str = "SHARE"     # "SHARE" or "LOCAL"
    conf_threshold: float = 0.5


@dataclass
class TaskResult:
    task_id: int
    export_path: str | None = None
    status: str = "created"


@dataclass
class PipelineResult:
    segment_id: str
    success: bool
    task_results: list[TaskResult]
    message: str
    started_at: float
    finished_at: float

    @property
    def duration_seconds(self) -> float:
        return self.finished_at - self.started_at