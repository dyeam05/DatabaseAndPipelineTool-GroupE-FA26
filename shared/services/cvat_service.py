import os
from pathlib import Path
import time
import logging
import zipfile

from cvat_sdk.core.proxies.tasks import ResourceType
from cvat_sdk.models import TaskWriteRequest
import cvat_sdk.auto_annotation as cvataa

from cvat_annotation_functions.i_cvat_detection import ICVATDetection
from db.models.job_segment_run import JobSegmentRun
from db.models.segment import Segment
from utilities.cvat_utilities import create_cvat_client, labels_to_patched_requests
from utilities.file_utilities import does_dir_exist, get_pngs_in_directory

logger = logging.getLogger(__name__)

class CVATService:
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

    def create_new_task_for_img_dir(self, segment_dir: Path, cvat_function: ICVATDetection) -> int:
        """
        Returns the task id of the created task
        """
        images = get_pngs_in_directory(dir=segment_dir)
        # logging.info(f"Creating new task with dir {segment_dir}")
        # logging.info(f"Create new task with images: {images}")
        labels = cvat_function.labels
        patched_labels = labels_to_patched_requests(labels=labels)
        task_spec = TaskWriteRequest(
            name=str(segment_dir),
            labels=patched_labels
        )
        logger.info(f"Creating cvat task with name {str(segment_dir)}")

        task = self.cvat_client.tasks.create_from_data(
            spec=task_spec, # type: ignore
            resource_type=ResourceType.LOCAL,
            resources=images
        )

        logger.info(f"Tak created with id {task.id}")
        return task.id
    
    def annotate_task(self, task_id: int, cvat_function: ICVATDetection) -> None:
        cvataa.annotate_task(
            self.cvat_client,
            task_id,
            cvat_function
        )

    def export_task_coco(
        self,
        task_id: int,
        output_dir: Path
    ) -> Path:
        """
        Args
            - task_id[int]: The task ID
            - output_dir[Path]: The path where data will be downloaded to
        Output
            - output_path[Path]: The file path of the output json file.
        """
        zip_path = output_dir / f"task_{task_id}.zip"
        out_path = output_dir / f"task_{task_id}.json"

        task = self.cvat_client.tasks.retrieve(obj_id=task_id)
        task.export_dataset(
            format_name="COCO 1.0",
            filename=zip_path,
            include_images=False
        )

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            coco_files = [file for file in zip_file.namelist() if file.endswith(".json")]
            if not coco_files:
                raise FileNotFoundError(f"No coco files found in {zip_path} when exporting task {task_id}")

            with zip_file.open(coco_files[0]) as src, open(out_path, "wb") as dst:
                dst.write(src.read())
        os.remove(zip_path)
        return out_path

    def get_detections_for_segment(self, segment_dir: Path, cvat_function: ICVATDetection, output_dir: Path) -> Path:
        """
        Returns the path of the output file
        """
        if not does_dir_exist(dir=segment_dir):
            raise RuntimeError(f"Directory {segment_dir} does not exist.")

        self.wait_for_cvat()
        task_id = self.create_new_task_for_img_dir(
            segment_dir=segment_dir,
            cvat_function=cvat_function
        )
        self.annotate_task(
            task_id=task_id,
            cvat_function=cvat_function
        )
        
        output_file = self.export_task_coco(
            task_id=task_id,
            output_dir=output_dir
        )

        return output_file
