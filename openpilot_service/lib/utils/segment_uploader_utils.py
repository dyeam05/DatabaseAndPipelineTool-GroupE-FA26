import os
from pathlib import Path



def upload_segment(route_id: str, dir_path: Path, minio_url: str):
    # code to upload data to minio and add metadata to postgress
    for file in os.listdir(dir_path):
        print(f"uploading {file}...")


def get_list_of_upload_jobs_for_route(route_id: str, dir_path: str) -> list[SegmentUploadJob]