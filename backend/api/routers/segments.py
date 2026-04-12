import logging
import os

from fastapi import Depends, Response, status, APIRouter
from fastapi.responses import StreamingResponse
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_transactional_session
from db.models.segment import Segment
from schemas.segment import SegmentResponse
from services.errors import SegmentNotFoundError
from utilities.service_builder_utilities import build_segment_service

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ROOT_USER"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
    secure=False,
)
MINIO_BUCKET = os.getenv("MINIO_BUCKET_NAME")

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

@segments_router.get("/{route_id}/{segment_id}/thumbnail")
async def get_segment_thumbnail(route_id: str, segment_id: int):
    prefix = f"v1/routes/{route_id}/segment/{segment_id}/front_wide/frames/"
    objects = sorted(
        minio_client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True),
        key=lambda o: o.object_name,)
    obj = objects[len(objects) // 2]
    minio_response = minio_client.get_object(MINIO_BUCKET, obj.object_name)
    return StreamingResponse(minio_response, media_type="image/png")

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

@segments_router.delete("/{route_id}/{segment_id}")
async def delete_segment(
    route_id: str,
    segment_id: int,
    session: AsyncSession = Depends(get_transactional_session),
):
    logging.info("delete segment")
    segment_service = build_segment_service(session=session)
    await segment_service.delete_segment(route_id=route_id, segment_id=segment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# TODO: query base on object id from postgress
# instead of list object from minio and sort it to get the middle frame as thumbnail, 
# we can directly query the object id from postgress and get the object from minio. This will be more efficient and faster.
# fget the object from minio and return the file path to the caller, then the caller can read the file and return the stream to the client.
# dont want to fget. fget - saves as file. we just need transient store file on backend, and return that