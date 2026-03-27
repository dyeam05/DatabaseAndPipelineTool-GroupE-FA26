from db.enums import ArtifactKind, ArtifactRole, CameraType
from db.models.segment import Segment
from services.artifact_service import ArtifactService
from services.frame_artifact_service import FrameArtifactService
from services.frame_service import FrameService
from services.minio_service import MinioService


class FrameUploaderService:
    """
    Service for uploading frames, that takes care of populating the frames, frame artifacts, and artifacts tables.
    """
    def __init__(self, frame_service: FrameService, frame_artifact_service: FrameArtifactService, artifact_service: ArtifactService):
        self.minio_service = MinioService()
        self.frame_service = frame_service
        self.frame_artifact_service = frame_artifact_service
        self.artifact_service = artifact_service


    async def create_frame(self, segment: Segment, camera_view: CameraType, frame_number: int,  frame_path):
        write_result = self.minio_service.put_segment_image(
            segment=segment,
            camera_view=camera_view,
            frame_number=frame_number,
            frame_path=frame_path
        )

        frame = await self.frame_service.create_frame(
            route_id=segment.route_id,
            segment_id=segment.segment_id,
            frame_id=frame_number,
            camera=camera_view
        )

        artifact = await self.artifact_service.create_artifact(
            bucket=write_result.bucket_name,
            object_key=write_result.object_name,
            kind=ArtifactKind.IMAGE,
        )

        self.frame_artifact = await self.frame_artifact_service.create_frame_artifact(
            frame_pk=frame.frame_pk,
            artifact_id=artifact.artifact_id,
            role=ArtifactRole.FRAME_IMAGE
        )
        