import json
import os
from pathlib import Path
import logging

from cvat_sdk import make_client
from cvat_sdk.models import PatchedLabelRequest

from models.cvat_models import SegmentJob

logger = logging.getLogger(__name__)

CVAT_EMAIL = os.environ["CVAT_EMAIL"]
CVAT_PASSWORD = os.environ["CVAT_PASSWORD"]
CVAT_HOST = os.environ["CVAT_HOST"]
CVAT_SHARE_ROOT = os.environ["CVAT_SHARE_ROOT"]
CVAT_PUBLIC_URL = os.environ["CVAT_PUBLIC_URL"]


def labels_to_patched_requests(labels: dict[int, str]) -> list[PatchedLabelRequest]:
    return [PatchedLabelRequest(name=name) for name in labels.values()] # type: ignore


def create_cvat_client():
    return make_client(CVAT_HOST, credentials=(CVAT_EMAIL, CVAT_PASSWORD))


def ensure_segment_exists(segment: SegmentJob) -> None:
    if not os.path.isdir(segment.share_dir):
        raise FileNotFoundError(
            f"Segment directory does not exist: {segment.share_dir}"
        )
    pngs = [f for f in os.listdir(segment.share_dir) if f.lower().endswith(".png")]
    if not pngs:
        raise FileNotFoundError(
            f"No .png files found in segment directory: {segment.share_dir}"
        )

def extract_ids_to_labels_for_coco_annotation_file(annotation_file: Path) -> dict[int, str]:
    """
    Returns the dictionary mapping integer IDs to string labels for a CVAT annotation file (in COCO format)
    """
    with annotation_file.open("r") as f:
        data = json.load(f)

    try:
        ids_to_labels: dict[int, str] = {}
        for category in data['categories']:
            ids_to_labels[category['id']] = category['name']
    except KeyError as e:
        raise ValueError(f"JSON schema not in expcted format. File: {annotation_file}. {e}")
    
    return ids_to_labels

def get_task_url(task_id: int, job_id: int) -> str:
    return f"{CVAT_PUBLIC_URL}/tasks/{task_id}/jobs/{job_id}"
