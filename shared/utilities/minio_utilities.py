import os

from minio.datatypes import Bucket
from minio import Minio

from db.models.job_segment_run import JobSegmentRun
from db.models.segment import Segment


def get_minio_client():
    client = Minio(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False
    )
    return client

def get_segment_object_name(segment: Segment):
    return f"v1/routes/{segment.route_id}/segment/{segment.segment_id}"

def get_segment_image_object_name(segment: Segment, camera_view: str, frame_number: int):
    return f"{get_segment_object_name(segment)}/{camera_view}/frames/{frame_number}.png"

def get_segment_log_object_name(segment: Segment):
    return f"{get_segment_object_name(segment)}/log.json"

def get_job_segment_run_object_name(job_segment_run: JobSegmentRun):
    return f"{job_segment_run.route_id}/{job_segment_run.job_def_id}/{job_segment_run.job_run_num}/{job_segment_run.segment_id}/data.json"

def is_bucket_in_list_of_buckets(target: str, buckets: list[Bucket]) -> bool:
    return any(bucket.name == target for bucket in buckets)

