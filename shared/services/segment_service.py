from datetime import datetime

from db.models.segment import Segment, SegmentStatus
from repositories.segment_repository import SegmentRepository
from services.errors import SegmentAlreadyExistsError, SegmentNotFoundError
from services.minio_service import MinioService
from services.thumbnail_service import ThumbnailService


# Service layer for managing segments
class SegmentService:
    def __init__(self, segment_repository: SegmentRepository, thumbnail_service: ThumbnailService | None = None) -> None:
        self._segment_repository = segment_repository
        self._thumbnail_service = thumbnail_service


    async def list_segments(self) -> list[Segment]:
        return await self._segment_repository.list_all()

    async def get_segments_by_status(self, status: SegmentStatus) -> list[Segment]:
        return await self._segment_repository.get_by_status(status)

    async def get_segments_by_route(self, route_id: str) -> list[Segment]:
        return await self._segment_repository.get_by_route(route_id)

    async def get_next_segment_by_status(self, status: SegmentStatus) -> Segment | None:
        return await self._segment_repository.get_next_by_status(status)

    async def get_segment(self, route_id: str, segment_id: int) -> Segment | None:
        return await self._segment_repository.get_by_id(route_id, segment_id)
    
    async def get_segment_thumbnail_stream(self, route_id: str, segment_id: int):
        return await self._thumbnail_service.get_segment_thumbnail_stream(
            route_id=route_id,
            segment_id=segment_id,
        )

    async def create_segment(
        self,
        route_id: str,
        segment_id: int,
        start_time: datetime,
        end_time: datetime,
        status: SegmentStatus = SegmentStatus.DOWNLOAD_QUEUE,  # default status when creating a segment
    ) -> Segment:
        # Check if a segment with the same route_id and segment_id  alive
        existing_segment = await self._segment_repository.get_by_id(
            route_id, segment_id
        )
        if existing_segment is not None:
            raise SegmentAlreadyExistsError(route_id, segment_id)

        return await self._segment_repository.create(
            route_id=route_id,
            segment_id=segment_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )

    # Update the status of a segment
    async def set_status(
        self,
        route_id: str,
        segment_id: int,
        status: SegmentStatus,
    ) -> Segment:
        segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if segment is None:
            raise SegmentNotFoundError(route_id, segment_id)

        segment.status = status
        return await self._segment_repository.save(segment)

    # Update the segment_meta of a segment
    async def set_segment_meta(
        self,
        route_id: str,
        segment_id: int,
        segment_meta: dict | None,
    ) -> Segment:
        segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if segment is None:
            raise SegmentNotFoundError(route_id, segment_id)

        segment.segment_meta = segment_meta
        return await self._segment_repository.save(segment)

    async def delete_segment(self, route_id: str, segment_id: int) -> None:
        segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if segment is None:
            raise SegmentNotFoundError(route_id, segment_id)

        await self._segment_repository.delete(segment)

# TODO: query base on object id from postgress
# instead of list object from minio and sort it to get the middle frame as thumbnail, 
# we can directly query the object id from postgress and get the object from minio. This will be more efficient and faster.
# fget the object from minio and return the file path to the caller, then the caller can read the file and return the stream to the client.
# dont want to fget. fget - saves as file. we just need transient store file on backend, and return that
