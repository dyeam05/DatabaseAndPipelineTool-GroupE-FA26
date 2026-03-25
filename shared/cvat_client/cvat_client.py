import os
import time
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional

from dotenv import load_dotenv
from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import ResourceType

from cvat_share.create_tasks import create_tasks_from_folder
from shared.cvat_client.export_annotations import export_task_coco
from shared.cvat_client.auto_annotate import annotate_task

load_dotenv()

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

CVAT_HOST = os.environ.get("CVAT_HOST", "http://localhost:8080")
CVAT_EMAIL = os.environ["CVAT_EMAIL"]
CVAT_PASSWORD = os.environ["CVAT_PASSWORD"]

# Docker-mounted share folder on the host machine
CVAT_SHARE_ROOT = os.environ.get("CVAT_SHARE_ROOT", "share")

# Where exported COCO json files should go
ANNOTATION_OUTPUT_DIR = os.environ.get("ANNOTATION_OUTPUT_DIR", "annotations")

# -----------------------------------------------------------------------------
# Data models
# -----------------------------------------------------------------------------

# TODO: clarify whether this structure works with our db, or if these will need to be updated 
@dataclass
class SegmentJob:
    """
    Represents one queued segment from the DB.

    Assumptions:
    - segment_id is the DB / pipeline identifier
    - local_image_dir is the host path containing the images
    - share_subdir is the relative path inside Docker share that CVAT will use
      Example:
          local_image_dir = "share/segment_001"
          share_subdir    = "segment_001"
    """
    segment_id: str
    local_image_dir: str
    share_subdir: Optional[str] = None
    task_title_prefix: str = "segment"
    resource_type: str = "SHARE"     # "SHARE" or "LOCAL"
    conf_threshold: float = 0.5


@dataclass
class TaskResult:
    task_id: int
    export_path: Optional[str] = None
    status: str = "created"


@dataclass
class PipelineResult:
    segment_id: str
    success: bool
    task_results: List[TaskResult]
    message: str
    started_at: float
    finished_at: float

    @property
    def duration_seconds(self) -> float:
        return self.finished_at - self.started_at


# -----------------------------------------------------------------------------
# Validation / connectivity helpers
# -----------------------------------------------------------------------------

def ensure_env() -> None:
    missing = [k for k in ["CVAT_EMAIL", "CVAT_PASSWORD"] if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")


def ensure_segment_exists(segment: SegmentJob) -> None:
    if not os.path.isdir(segment.local_image_dir):
        raise FileNotFoundError(
            f"Segment directory does not exist: {segment.local_image_dir}"
        )

    pngs = [
        f for f in os.listdir(segment.local_image_dir)
        if f.lower().endswith(".png")
    ]
    if not pngs:
        raise FileNotFoundError(
            f"No .png files found in segment directory: {segment.local_image_dir}"
        )


def ensure_share_mapping_valid(segment: SegmentJob) -> None:
    """
    For SHARE mode, CVAT sees files through Docker's mounted /share volume.
    That means:
      local_image_dir should usually live under CVAT_SHARE_ROOT
      share_subdir should be the relative path inside that share
    """
    if segment.resource_type.upper() != "SHARE":
        return

    share_root_abs = os.path.abspath(CVAT_SHARE_ROOT)
    local_dir_abs = os.path.abspath(segment.local_image_dir)

    if not local_dir_abs.startswith(share_root_abs):
        raise RuntimeError(
            "For SHARE mode, segment.local_image_dir must live under CVAT_SHARE_ROOT.\n"
            f"CVAT_SHARE_ROOT={share_root_abs}\n"
            f"local_image_dir={local_dir_abs}"
        )

    if not segment.share_subdir:
        # derive it automatically if not provided
        rel_path = os.path.relpath(local_dir_abs, share_root_abs)
        segment.share_subdir = rel_path.replace("\\", "/")


def check_cvat_connection() -> None:
    """
    Verifies:
    - host is reachable
    - credentials are valid
    - basic task API call works
    """
    logger.info("Checking CVAT connectivity/authentication at %s", CVAT_HOST)

    try:
        with make_client(CVAT_HOST, credentials=(CVAT_EMAIL, CVAT_PASSWORD)) as client:
            # A simple authenticated operation
            _ = client.tasks.list(return_json=False)
    except Exception as e:
        raise RuntimeError(f"Failed to connect/authenticate to CVAT: {e}") from e

    logger.info("CVAT connection/authentication successful")


def wait_for_cvat(max_wait_seconds: int = 60, poll_interval: int = 3) -> None:
    """
    Useful if main.py may start around the same time containers are still coming up
    """
    deadline = time.time() + max_wait_seconds
    last_error = None

    while time.time() < deadline:
        try:
            check_cvat_connection()
            return
        except Exception as e:
            last_error = e
            logger.warning("CVAT not ready yet: %s", e)
            time.sleep(poll_interval)

    raise RuntimeError(f"CVAT did not become ready within {max_wait_seconds}s: {last_error}")


# -----------------------------------------------------------------------------
# Core pipeline steps
# -----------------------------------------------------------------------------

def create_segment_tasks(segment: SegmentJob) -> List[int]:
    logger.info("Creating CVAT tasks for segment %s", segment.segment_id)

    resource_type = (
        ResourceType.SHARE
        if segment.resource_type.upper() == "SHARE"
        else ResourceType.LOCAL
    )

    task_title = f"{segment.task_title_prefix}_{segment.segment_id}"

    task_ids = create_tasks_from_folder(
        local_image_dir=segment.local_image_dir,
        task_title=task_title,
        resource_type=resource_type,
        share_subdir=segment.share_subdir,
    )

    if not task_ids:
        raise RuntimeError(f"No tasks were created for segment {segment.segment_id}")

    logger.info("Created tasks for segment %s: %s", segment.segment_id, task_ids)
    return task_ids


def annotate_segment_tasks(task_ids: List[int], conf_threshold: float = 0.5) -> None:
    for task_id in task_ids:
        logger.info("Auto-annotating task %s", task_id)
        annotate_task(task_id, conf_threshold=conf_threshold)
        logger.info("Finished auto-annotating task %s", task_id)


def export_segment_tasks(task_ids: List[int], output_dir: str = ANNOTATION_OUTPUT_DIR) -> List[TaskResult]:
    results = []

    os.makedirs(output_dir, exist_ok=True)

    for task_id in task_ids:
        logger.info("Exporting task %s", task_id)
        export_path = export_task_coco(task_id, output_dir=output_dir)
        results.append(TaskResult(task_id=task_id, export_path=export_path, status="exported"))
        logger.info("Exported task %s to %s", task_id, export_path)

    return results


# -----------------------------------------------------------------------------
# Public entry point used by main.py
# -----------------------------------------------------------------------------

def run_pipeline_for_segment(segment: SegmentJob) -> PipelineResult:
    started_at = time.time()
    task_results: List[TaskResult] = []

    try:
        ensure_env()
        ensure_segment_exists(segment)
        ensure_share_mapping_valid(segment)
        wait_for_cvat()

        task_ids = create_segment_tasks(segment)
        task_results = [TaskResult(task_id=t, status="created") for t in task_ids]

        annotate_segment_tasks(task_ids, conf_threshold=segment.conf_threshold)

        for tr in task_results:
            tr.status = "annotated"

        exported_results = export_segment_tasks(task_ids, output_dir=ANNOTATION_OUTPUT_DIR)

        # merge export info back into existing task_results
        export_map = {r.task_id: r for r in exported_results}
        for tr in task_results:
            if tr.task_id in export_map:
                tr.export_path = export_map[tr.task_id].export_path
                tr.status = "exported"

        finished_at = time.time()
        return PipelineResult(
            segment_id=segment.segment_id,
            success=True,
            task_results=task_results,
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
            task_results=task_results,
            message=str(e),
            started_at=started_at,
            finished_at=finished_at,
        )


# -----------------------------------------------------------------------------
# CLI/manual test entrypoint
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Example manual run:
    # host dir: share/segment_001
    # CVAT share path inside Docker: segment_001
    segment = SegmentJob(
        segment_id="001",
        local_image_dir=os.path.join(CVAT_SHARE_ROOT, "segment_001"),
        share_subdir="segment_001",
        task_title_prefix="av_segment",
        resource_type="SHARE",
        conf_threshold=0.5,
    )

    result = run_pipeline_for_segment(segment)
    print(json.dumps({
        **asdict(result),
        "duration_seconds": result.duration_seconds
    }, indent=2))