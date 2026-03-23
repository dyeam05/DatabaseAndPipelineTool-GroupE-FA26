from db.models.segment import Segment, SegmenStatus
from repositories.segment_repository import SegmentRepository
from services.errors import SegmentAlreadyExistsError, SegmentNotFoundError


class SegmentService:
    def __init__(self, segment_repository: SegmentRepository) -> None:
        self._segment_repository = segment_repository

    async def list_segments(self) -> list[Segment]:
        return await self._segment_repository.list_all()

    async def get_segments_by_status(self, status: SegmenStatus) -> list[Segment]:
        return await self._segment_repository.get_by_status(status)

    async def get_next_segment_by_status(self, status: SegmenStatus) -> Segment | None:
        return await self._segment_repository.get_next_by_status(status)

    async def get_segment(self, route_id: str, segment_id: int) -> Segment | None:
        return await self._segment_repository.get_by_id(route_id, segment_id)

    async def create_segment(
        self,
        route_id: str,
        segment_id: int,
        start_time,
        end_time,
        status: SegmenStatus = SegmenStatus.DOWNLOAD_QUEUE,
    ) -> Segment:
        existing_segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if existing_segment is not None:
            raise SegmentAlreadyExistsError(route_id, segment_id)

        return await self._segment_repository.create(
            route_id=route_id,
            segment_id=segment_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )

    async def set_status(
        self,
        route_id: str,
        segment_id: int,
        status: SegmenStatus,
    ) -> Segment:
        segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if segment is None:
            raise SegmentNotFoundError(route_id, segment_id)

        segment.status = status
        return await self._segment_repository.save(segment)

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