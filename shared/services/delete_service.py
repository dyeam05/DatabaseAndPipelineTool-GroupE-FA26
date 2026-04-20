import logging

from repositories.segment_repository import SegmentRepository
from services.minio_service import MinioService
from utilities.minio_utilities import get_segment_object_name
from repositories.route_repository import RouteRepository

logger = logging.getLogger(__name__)

class DeleteService:
    def __init__(
        self,
        segment_repository: SegmentRepository,
        minio_service: MinioService,
        route_repository: RouteRepository,
    ) -> None:
        self._segment_repository = segment_repository
        self._minio_service = minio_service
        self._route_repository = route_repository

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

    async def delete_route(self, route_id: str) -> None:
        prefix = f"v1/routes/{route_id}"

        objects = self._minio_service.minio_client.list_objects(
            bucket_name=self._minio_service.bucket_name,
            prefix=prefix,
            recursive=True,
        )

        for obj in objects:
            if obj.object_name:
                self._minio_service.delete_object(
                    bucket_name=self._minio_service.bucket_name,
                    object_key=obj.object_name,
                )

        route = await self._route_repository.get_by_id(route_id)
        if route:
            await self._route_repository.delete(route)
