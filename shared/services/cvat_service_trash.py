import os
import logging
import zipfile
import time

import torch
from PIL import Image as PIL
from transformers import AutoImageProcessor, AutoModelForObjectDetection

from cvat_sdk.core.proxies.tasks import ResourceType
from cvat_sdk.models import TaskWriteRequest
import cvat_sdk.models as models
import cvat_sdk.auto_annotation as cvataa

from models.cvat_models import PipelineResult, SegmentJob, TaskResult
from utilities.cvat_utilities import (
    CVAT_SHARE_ROOT,
    create_cvat_client,
    ensure_segment_exists,
    labels_to_patched_requests,
    wait_for_cvat,
)


logger = logging.getLogger(__name__)


class CVATService:
    def create_task_from_folder(
        self,
        task_name: str,
        share_dir: str,
        labels: dict[int, str] | None = None,
        resource_type: ResourceType = ResourceType.SHARE,
    ) -> int:
        # handle path for segment and extracting annotations.json
        png_files = sorted(
            f for f in os.listdir(share_dir) if f.lower().endswith(".png")
        )
        if not png_files:
            raise ValueError(f"No PNG files found in {share_dir}")

        json_files = [f for f in os.listdir(share_dir) if f.lower().endswith(".json")]
        annotations_path = (
            os.path.join(share_dir, json_files[0]) if json_files else None
        )

        if resource_type == ResourceType.LOCAL:
            file_paths = [os.path.join(share_dir, f) for f in png_files]
        else:
            rel_dir = os.path.relpath(share_dir, CVAT_SHARE_ROOT).replace("\\", "/")
            file_paths = [f"{rel_dir}/{f}" for f in png_files]

        with create_cvat_client() as client:
            task_spec = TaskWriteRequest(
                name=task_name,
                labels=labels_to_patched_requests(labels) if labels else [],
            )
            logger.info(
                "Creating task '%s' with %d images from %s",
                task_name,
                len(file_paths),
                share_dir,
            )
            task = client.tasks.create_from_data(
                spec=task_spec,
                resource_type=resource_type,
                resources=file_paths,
            )
            logger.info("Task created: %s", task.id)

            if annotations_path:
                logger.info(
                    "Importing annotations from %s into task %s",
                    annotations_path,
                    task.id,
                )
                task.import_annotations(
                    format_name="COCO 1.0", filename=annotations_path
                )
                logger.info("Annotations imported into task %s", task.id)

        return task.id

        logger.info("Created task for segment %s: %s", segment.segment_id, task_id)
        return task_id

    def annotate_task(
        self, task_id: int, model_name: str, labels: dict[int, str]
    ) -> None:
        with create_cvat_client() as client:
            func = AVDetectionFunction(model_name=model_name, labels=labels)
            cvataa.annotate_task(client, task_id, func)

    def export_task_coco(
        self, task_id: int, output_dir: str = ANNOTATION_OUTPUT_DIR
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        zip_path = os.path.join(output_dir, f"task_{task_id}.zip")
        out_path = os.path.join(output_dir, f"task_{task_id}.json")

        with create_cvat_client() as client:
            task = client.tasks.retrieve(task_id)
            task.export_dataset(
                format_name=COCO_FORMAT,
                filename=zip_path,
                include_images=False,
            )

        with zipfile.ZipFile(zip_path, "r") as zf:
            coco_files = [f for f in zf.namelist() if f.endswith(".json")]
            if not coco_files:
                raise FileNotFoundError(
                    f"No JSON found in export zip for task {task_id}"
                )
            with zf.open(coco_files[0]) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

        os.remove(zip_path)
        logger.info("Saved COCO annotations to %s", out_path)
        return out_path

    def run_pipeline_for_segment(self, segment: SegmentJob) -> PipelineResult:
        started_at = time.time()
        task_result = TaskResult(task_id=-1)

        try:
            ensure_segment_exists(segment)
            wait_for_cvat()

            task_id = self.create_segment_task(segment)
            task_result = TaskResult(task_id=task_id, status="created")

            export_path = self.export_task_coco(
                task_id, output_dir=ANNOTATION_OUTPUT_DIR
            )
            task_result.export_path = export_path
            task_result.status = "exported"

            finished_at = time.time()
            return PipelineResult(
                segment_id=segment.segment_id,
                success=True,
                task_results=[task_result],
                message="Pipeline completed successfully",
                started_at=started_at,
                finished_at=finished_at,
            )

        except Exception as e:
            logger.exception("Pipeline failed for segment %s", segment.segment_id)
            finished_at = time.time()
            return PipelineResult(
                segment_id=segment.segment_id,
                success=False,
                task_results=[task_result],
                message=str(e),
                started_at=started_at,
                finished_at=finished_at,
            )
