from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import CameraType
from db.models.frame import Frame
# frame repository is responsible for interacting
#  with the database to perform CRUD operations on Frame objects.

class FrameRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, frame_pk: int) -> Frame | None:
        return await self._session.get(Frame, frame_pk)

    async def list_all(self) -> list[Frame]:
        stmt = select(Frame).order_by(Frame.created_at.desc())
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_route_segment(self,route_id: str,segment_id: int, camera: CameraType) -> list[Frame]:
        # make sure in the correct order for a given route and segment
        stmt = (
            select(Frame)
            .where(Frame.route_id == route_id)
            .where(Frame.segment_id == segment_id)
            .where(Frame.camera == camera)
            .order_by(Frame.frame_id.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        route_id: str,
        segment_id: int,
        frame_id: int,
        camera: CameraType,
    ) -> Frame:
        frame = Frame(route_id=route_id,segment_id=segment_id,frame_id=frame_id,camera=camera,
        )
        self._session.add(frame)
        await self._session.flush()
        return frame

    async def save(self, frame: Frame) -> Frame:
        self._session.add(frame)
        await self._session.flush()
        return frame

    async def delete(self, frame: Frame) -> None:
        await self._session.delete(frame)
        await self._session.flush()
