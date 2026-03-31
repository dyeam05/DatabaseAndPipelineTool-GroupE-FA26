from pathlib import Path
import time

from cvat_sdk.models import TaskWriteRequest

from db.models.job_segment_run import JobSegmentRun
from db.models.segment import Segment
from utilities.cvat_utilities import create_cvat_client
from utilities.file_utilities import does_dir_exist, get_pngs_in_directory


class CVAT_Service:
    def __init__(self):
        self.cvat_client = create_cvat_client()

    def check_cvat_connection(self):
        try:
            self.cvat_client.tasks.list(return_json=False)
        except Exception as e:
            raise RuntimeError(f"Failed to connect/authenticate to CVAT: {e}") from e

    def wait_for_cvat(self, max_wait_seconds: int = 60, poll_interval: int = 3) -> None:
        deadline = time.time() + max_wait_seconds
        last_error = None
        while time.time() < deadline:
            try:
                self.check_cvat_connection()
                return
            except Exception as e:
                last_error = e
                time.sleep(poll_interval)

        raise RuntimeError(f"CVAT did not become ready within {max_wait_seconds}s: {last_error}")

    def create_segment_task(self, job_segment_run: JobSegmentRun, segment_dir: Path):
        images = get_pngs_in_directory(dir=segment_dir)
        labels = ?? #TODO
        task_spec = TaskWriteRequest(

        )



    def get_detections_for_segment(self, job_segment_run: JobSegmentRun, segment_dir: Path) -> Any:
        #TODO
        if not does_dir_exist(dir=segment_dir):
            raise RuntimeError(f"Directory {segment_dir} does not exist.")

        self.wait_for_cvat()

        pass
