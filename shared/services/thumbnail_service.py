
from services.frame_service import FrameService
from repositories.segment_repository import SegmentRepository
from services.minio_service import MinioService
from services.errors import SegmentNotFoundError, FrameNotFoundError, FrameArtifactNotFoundError, ArtifactNotFoundError
from db.enums import ArtifactRole
from db.models.segment import Segment
from services.frame_artifact_service import FrameArtifactService
from services.artifact_service import ArtifactService
class ThumbnailService:
    def __init__(
        self,
        segment_repository: SegmentRepository,
        minio_service: MinioService,
        frame_service: FrameService,
        frame_artifact_service: FrameArtifactService,
        artifact_service: ArtifactService
    ) -> None:
        self._segment_repository = segment_repository
        self._minio_service = minio_service
        self._frame_service = frame_service
        self._frame_artifact_service = frame_artifact_service
        self._artifact_service = artifact_service


    async def get_segment_thumbnail_stream(self, route_id: str, segment_id: int):
        segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if segment is None:
            raise SegmentNotFoundError(route_id, segment_id)

        frames = await self._frame_service.get_frames_by_route_segment(route_id, segment_id)
        if not frames:
            raise FrameNotFoundError(frame_pk=-1)
        middle_frame = frames[len(frames) // 2]

        frame_artifact = await self._frame_artifact_service.get_frame_artifact( 
            frame_pk=middle_frame.frame_pk,
            role=ArtifactRole.FRAME_IMAGE
        )
        if frame_artifact is None:
            raise FrameArtifactNotFoundError(frame_pk=middle_frame.frame_pk, role=ArtifactRole.FRAME_IMAGE)
        
        artifact = await self._artifact_service.get_artifact(frame_artifact.artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id=frame_artifact.artifact_id)

        return self._minio_service.download_artifact_to_stream(artifact=artifact)