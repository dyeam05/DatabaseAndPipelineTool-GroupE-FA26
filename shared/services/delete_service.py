import logging

from db.models.segment import Segment
from repositories.segment_repository import SegmentRepository
from services.minio_service import MinioService
from utilities.minio_utilities import get_segment_object_name


logger = logging.getLogger(__name__)


class DeleteService:
    def __init__(
        self,
        segment_repository: SegmentRepository,
        minio_service: MinioService,
    ) -> None:
        self._segment_repository = segment_repository
        self._minio_service = minio_service

    async def delete_segment(self, route_id: str, segment_id: int) -> None:
        segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if segment is None:
            return

        prefix = get_segment_object_name(segment)

        objects = self._minio_service.minio_client.list_objects(
            bucket_name=self._minio_service.bucket_name,
            prefix=prefix,
            recursive=True,
        )

        for obj in objects:
            if obj.object_name is None:
                continue

            self._minio_service.delete_object(
                bucket_name=self._minio_service.bucket_name,
                object_key=obj.object_name,
            )

        await self._segment_repository.delete(segment)