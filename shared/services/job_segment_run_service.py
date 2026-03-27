
from repositories.job_segment_run_repository import JobSegmentRunRepository


class JobRunSegmentService:
    def __init__(self, job_segment_run_repository: JobSegmentRunRepository) -> None:
        self._job_segment_run_repository = job_segment_run_repository
        
    # create segment
    # set status
    # push annotation artifact to minio
    # view annotation labels and counts (low priority) from a JSON