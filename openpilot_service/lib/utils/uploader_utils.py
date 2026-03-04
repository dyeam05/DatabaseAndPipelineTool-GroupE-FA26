from pathlib import Path
from typing import Any

from lib.models.segment_uploader_models import UploadJob


def list_segments_for_upload(dir_path: str | Path) -> list[Path]:
    path = Path(dir_path)
    if not path.exists():
        return []
    return sorted([entry for entry in path.rglob("*") if entry.is_file()])


def upload_segment(route_id: str, dir_path: Path, minio_url: str = ""):
    # TODO
    print("Uploading segment")
    # code to upload data to minio and add metadata to postgress
    # Placeholder behavior to support orchestration and retry paths.
    if "fail" in dir_path.name.lower():
        raise RuntimeError(f"simulated upload failure for segment {dir_path.name}")
    return {
        "route_id": route_id,
        "segment": dir_path.name,
        "minio_url": minio_url,
    }


def pre_route_upload_init(route_id: str, output_dir: str | Path) -> dict[str, Any]:
    # TODO
    # initialize route-level upload metadata in remote storage/db
    print("pre route upload")
    return {
        "route_id": route_id,
        "output_dir": str(output_dir),
        "initialized": True,
    }


def post_route_upload_finalize(
    route_id: str,
    output_dir: str | Path,
    segment_summary: dict[str, int],
) -> dict[str, Any]:
    # TODO
    print("post route upload")
    # finalize route-level upload metadata in remote storage/db
    return {
        "route_id": route_id,
        "output_dir": str(output_dir),
        "segment_summary": segment_summary,
        "finalized": True,
    }
