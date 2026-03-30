import os
import time
import logging

from cvat_sdk import make_client
from cvat_sdk.models import PatchedLabelRequest

from models.cvat_models import SegmentJob

logger = logging.getLogger(__name__)

CVAT_EMAIL = os.environ["CVAT_EMAIL"]
CVAT_PASSWORD = os.environ["CVAT_PASSWORD"]
CVAT_HOST = os.environ["CVAT_HOST"]
CVAT_SHARE_ROOT = os.environ["CVAT_SHARE_ROOT"]


def labels_to_patched_requests(labels: dict[int, str]) -> list[PatchedLabelRequest]:
    return [PatchedLabelRequest(name=name) for name in labels.values()]


def create_cvat_client():
    return make_client(CVAT_HOST, credentials=(CVAT_EMAIL, CVAT_PASSWORD))


def check_cvat_connection() -> None:
    logger.info("Checking CVAT connectivity/authentication at %s", CVAT_HOST)
    try:
        with create_cvat_client() as client:
            _ = client.tasks.list(return_json=False)
    except Exception as e:
        raise RuntimeError(f"Failed to connect/authenticate to CVAT: {e}") from e
    logger.info("CVAT connection/authentication successful")


def wait_for_cvat(max_wait_seconds: int = 60, poll_interval: int = 3) -> None:
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

