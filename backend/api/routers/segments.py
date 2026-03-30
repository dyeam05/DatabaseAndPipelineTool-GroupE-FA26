import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Response, status, APIRouter

from api.dependencies import get_session, get_transactional_session
from db.enums import SegmentStatus
from db.models.segment import Segment
from schemas.segment import CreateSegmentRequest, SegmentResponse
from services.errors import SegmentNotFoundError
from services.segment_service import SegmentService
from utilities.service_builder_utilities import build_segment_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
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


@segments_router.post("/", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(
    payload: CreateSegmentRequest,
    session: AsyncSession = Depends(get_transactional_session),
) -> Segment:
    logging.info("create segment")
    segment_service: SegmentService = build_segment_service(session=session)
    return await segment_service.create_segment(
        route_id=payload.route_id,
        segment_id=payload.segment_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=SegmentStatus.DOWNLOAD_QUEUE
    )

@segments_router.delete("/{route_id}/{segment_id}")
async def delete_segment(
    route_id: str,
    segment_id: int,
    session: AsyncSession = Depends(get_session),
):
    logging.info("delete segment")
    segment_service = build_segment_service(session=session)
    await segment_service.delete_segment(route_id=route_id, segment_id=segment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)