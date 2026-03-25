from db.enums import CameraType
from db.models.frame import Frame
from repositories.frame_repository import FrameRepository
from services.errors import FrameNotFoundError
# frame service is responsible for handling all frame related operations frames.
class FrameService:
    def __init__(self, frame_repository: FrameRepository) -> None:
        self._frame_repository = frame_repository

    async def list_frames(self) -> list[Frame]:
        return await self._frame_repository.list_all()

    async def get_frames_by_route_segment(
        self,
        route_id: str,
        segment_id: int,
    ) -> list[Frame]:
        return await self._frame_repository.get_by_route_segment(route_id, segment_id)

    async def get_frame(self, frame_pk: int) -> Frame | None:
        return await self._frame_repository.get_by_id(frame_pk)

    async def create_frame(
        self,
        route_id: str,
        segment_id: int,
        frame_id: int,
        camera: CameraType,
    ) -> Frame:
        return await self._frame_repository.create(
            route_id=route_id,
            segment_id=segment_id,
            frame_id=frame_id,
            camera=camera,
        )

    async def set_features(
        self,
        frame_pk: int,
        openpilot_features: dict | None,
    ) -> Frame:
        frame = await self._frame_repository.get_by_id(frame_pk)
        if frame is None:
            raise FrameNotFoundError(frame_pk)
        # save the openpilot features as json in the frame table for now
        frame.openpilot_features = openpilot_features
        return await self._frame_repository.save(frame)

    async def delete_frame(self, frame_pk: int) -> None:
        frame = await self._frame_repository.get_by_id(frame_pk)
        if frame is None:
            raise FrameNotFoundError(frame_pk)

        await self._frame_repository.delete(frame)
