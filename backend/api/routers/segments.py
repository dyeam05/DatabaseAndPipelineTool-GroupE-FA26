import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Response, status, APIRouter
import os
from minio import Minio
from fastapi.responses import RedirectResponse
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

@segments_router.get("/{route_id}/{segment_id}/thumbnail")
async def get_segment_thumbnail(route_id: str, segment_id: int):

    # ✅ extract last part after "--"
    try:
        route_suffix = route_id.split("--")[-1]
    except Exception:
        return Response(status_code=400)

    # ✅ correct MinIO path
    prefix = f"{route_suffix}/segment/{segment_id}/front_regular/frames/"

    objects = list(
        minio_client.list_objects(
            MINIO_BUCKET,
            prefix=prefix,
            recursive=True,
        )
    )

    if not objects:
        return Response(status_code=404)

    # pick a frame (middle frame looks nicer than first)
    obj = sorted(objects, key=lambda o: o.object_name)[len(objects)//2]

    url = minio_client.presigned_get_object(
        MINIO_BUCKET,
        obj.object_name,
    )

    return RedirectResponse(url)