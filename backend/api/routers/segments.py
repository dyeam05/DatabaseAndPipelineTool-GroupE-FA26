import logging

from fastapi import Depends, Response, status, APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_transactional_session
from db.models.segment import Segment
from schemas.segment import SegmentResponse
from services.errors import SegmentNotFoundError
from utilities.service_builder_utilities import build_delete_service, build_segment_service
from utilities.service_builder_utilities import build_thumbnail_service
from repositories.segment_repository import SegmentRepository
from services.segment_service import SegmentService

logger = logging.getLogger(__name__)

segments_router = APIRouter(
    prefix="/segments",
)

@segments_router.get("/", response_model=list[SegmentResponse])
async def list_segments(
    session: AsyncSession = Depends(get_session),
) -> list[Segment]:
    logging.info("get segments")
    segment_service = build_segment_service(session=session)
    return await segment_service.list_segments()

@segments_router.get("/by-route/{route_id}", response_model=list[SegmentResponse])
async def list_segments_by_route(
    route_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[Segment]:
    logging.info(f"get segments for route {route_id}")
    segment_service = build_segment_service(session=session)
    return await segment_service.get_segments_by_route(route_id=route_id)

@segments_router.get("/{route_id}/{segment_id}/thumbnail")
async def get_segment_thumbnail(
    route_id: str,
    segment_id: int,
    session: AsyncSession = Depends(get_session),
):
    thumbnail_service = build_thumbnail_service(session=session)
    stream = await thumbnail_service.get_segment_thumbnail_stream(route_id, segment_id)
    return StreamingResponse(stream, media_type="image/png")

@segments_router.get("/{route_id}/{segment_id}/frame-count")
async def get_frame_count(
    route_id: str,
    segment_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    repo = SegmentRepository(session=session)
    service = SegmentService(segment_repository=repo)

    count = await service.get_frame_count(route_id, segment_id)
    return {"count": count}

@segments_router.get("/{route_id}/{segment_id}", response_model=SegmentResponse)
async def get_segment(
    route_id: str,
    segment_id: int,
    session: AsyncSession = Depends(get_session),
) -> Segment:
    logging.info(f"Getting segment {segment_id} for route {route_id}")
    segment_service = build_segment_service(session=session)
    segment = await segment_service.get_segment(route_id=route_id, segment_id=segment_id)
    if segment is None:
        raise SegmentNotFoundError(route_id=route_id, segment_id=segment_id)
    return segment
