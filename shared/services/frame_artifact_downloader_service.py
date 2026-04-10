from pathlib import Path

from db.enums import ArtifactRole
from db.models.frame import Frame
from services.artifact_service import ArtifactService
from services.errors import ArtifactNotFoundError, FrameArtifactNotFoundError
from services.frame_artifact_service import FrameArtifactService
from services.frame_service import FrameService
from services.minio_service import MinioService
from urllib3.response import BaseHTTPResponse

class FrameArtifactDownloaderService:
    """
    Service for downloading frames, that takes care of populating the frames, frame artifacts, and artifacts tables.
    """
    def __init__(self, frame_service: FrameService, frame_artifact_service: FrameArtifactService, artifact_service: ArtifactService, minio_service: MinioService):
        self.minio_service = minio_service
        self.frame_service = frame_service
        self.frame_artifact_service = frame_artifact_service
        self.artifact_service = artifact_service

    async def download_frame(self, frame: Frame, dest_path: Path):
        frame_artifact = await self.frame_artifact_service.get_frame_artifact( 
            frame_pk=frame.frame_pk,
            role=ArtifactRole.FRAME_IMAGE
        )
        if frame_artifact is None:
            raise FrameArtifactNotFoundError(frame_pk=frame.frame_pk, role=ArtifactRole.FRAME_IMAGE)
        artifact = await self.artifact_service.get_artifact(frame_artifact.artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id=frame_artifact.artifact_id)
        self.minio_service.download_artifact(artifact=artifact, dest_path=dest_path)

    async def dowload_frame_to_stream(self, frame: Frame) -> BaseHTTPResponse:
        frame_artifact = await self.frame_artifact_service.get_frame_artifact( 
            frame_pk=frame.frame_pk,
            role=ArtifactRole.FRAME_IMAGE
        )
        if frame_artifact is None:
            raise FrameArtifactNotFoundError(frame_pk=frame.frame_pk, role=ArtifactRole.FRAME_IMAGE)
        artifact = await self.artifact_service.get_artifact(frame_artifact.artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id=frame_artifact.artifact_id)
        
        return self.minio_service.download_artifact_to_stream(artifact=artifact)