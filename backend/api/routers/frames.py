import logging

from fastapi import Depends, Response, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from services.errors import FrameNotFoundError
from api.dependencies import get_session, get_transactional_session
from db.models.frame import Frame
from db.enums import CameraType
from repositories.frame_repository import FrameRepository
from services.errors import FrameNotFoundError


logger = logging.getLogger(__name__)

frames_router = APIRouter(
    prefix="/frames",
)
@frames_router.get("/{frame_pk}", response_model=Frame)
async def get_frame(
    frame_pk: int,
    session: AsyncSession = Depends(get_session),
) -> Frame:
    logging.info(f"Getting frame {frame_pk}")
    frame_repository = FrameRepository(session=session)
    frame = await frame_repository.get_by_id(frame_pk)
    if frame is None:
        raise FrameNotFoundError(frame_pk=frame_pk)
    return frame

@frames_router.get("/{route_id}/{segment_id}", response_model=list[Frame])
async def get_frames_by_segment(
    route_id: str,
    segment_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[Frame]:
    logging.info(f"Getting frames for route {route_id} segment {segment_id}")
    frame_repository = FrameRepository(session=session)
    frames = await frame_repository.get_by_route_segment(route_id, segment_id)
    if not frames:
        raise FrameNotFoundError(frame_pk=-1) 
    return frames