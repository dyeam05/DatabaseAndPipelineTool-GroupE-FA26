import os
from pathlib import Path

from lib.models.segment_uploader_models import UploadJob




def upload_segment(route_id: str, dir_path: Path, minio_url: str):
    # TODO
    # code to upload data to minio and add metadata to postgress
    for file in os.listdir(dir_path):
        print(f"uploading {file}...")


def get_list_of_upload_jobs_for_route(route_id: str, dir_path: str) -> list[UploadJob]:
    # TODO
    return []