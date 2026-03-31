import os
from pathlib import Path
import time

from minio.datatypes import Bucket
from minio.helpers import ObjectWriteResult

from db.models.artifact import Artifact
from db.models.segment import Segment
from utilities.minio_utilities import get_minio_client, get_segment_image_object_name, get_segment_log_object_name, is_bucket_in_list_of_buckets

class MinioService:
    def __init__(self):
        self.minio_client = get_minio_client()
        self.bucket_name = os.environ["MINIO_BUCKET_NAME"]

    def put_segment_image(self, segment: Segment, camera_view: str, frame_number: int, frame_path: Path) -> ObjectWriteResult:
        """
        Returns the Minio Object Name 
        """
        result = self.minio_client.fput_object(
            bucket_name=self.bucket_name,
            object_name=get_segment_image_object_name(segment, camera_view, frame_number),
            content_type="image/png",
            file_path=str(frame_path)
        )
        return result

    def put_segment_log(self, segment: Segment, log_path: Path) -> ObjectWriteResult:
        return self.minio_client.fput_object(
            bucket_name=self.bucket_name,
            object_name=get_segment_log_object_name(segment),
            content_type="application/json",
            file_path=str(log_path)
        )

    def wait_for_minio(self, timeout: int = 30) -> None:
        start = time.time()
        while True:
            try:
                self.minio_client.list_buckets()
                return
            except Exception:
                if time.time() - start >  timeout:
                    raise RuntimeError("Minio not ready")
                time.sleep(1)

    def list_buckets(self) -> list[Bucket]:
        return self.minio_client.list_buckets()

    def is_main_bucket_in_created(self):
        return is_bucket_in_list_of_buckets(
            target=self.bucket_name,
            buckets=self.list_buckets()
        )

    def create_bucket(self, bucket_name: str) -> None:
        self.minio_client.make_bucket(
            bucket_name=bucket_name,
        )

    def download_artifact(self, artifact:Artifact,  dest_path:Path):
        self.minio_client.fget_object(
            bucket_name=artifact.bucket, 
            object_name=artifact.object_key, 
            file_path=str(dest_path)
        )