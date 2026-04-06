from pathlib import Path

from db.models.segment import Segment
from services.frame_artifact_downloader_service import FrameArtifactDownloaderService
from services.frame_service import FrameService


class SegmentArtifactDownloadService:
    def __init__(
        self, 
        frame_service: FrameService,
        frame_artifact_downloader_service: FrameArtifactDownloaderService
    ):
        self.frame_artifact_downloader_service = frame_artifact_downloader_service
        self.frame_service = frame_service

    async def download_segment_frames(self, segment: Segment, dest_path: Path):
        """
        dest_path is a relative folder path for the segment
        """
        frames = await self.frame_service.get_frames_by_route_segment(
            route_id=segment.route_id, segment_id=segment.segment_id
        )
        for frame in frames:
            await self.frame_artifact_downloader_service.download_frame(
                frame=frame, 
                dest_path=dest_path / f"{str(frame.frame_id)}.png"
            )
