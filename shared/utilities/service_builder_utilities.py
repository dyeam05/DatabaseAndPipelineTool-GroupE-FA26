from sqlalchemy.ext.asyncio import AsyncSession

from repositories.route_repository import RouteRepository
from services.route_service import RouteService
from repositories.segment_repository import SegmentRepository
from services.segment_service import SegmentService
from repositories.job_run_repository import JobRunRepository
from services.job_run_service import JobRunService
from repositories.job_definition_repository import JobDefinitionRepository
from services.job_definition_service import JobDefinitionService
from repositories.frame_repository import FrameRepository
from services.frame_service import FrameService
from repositories.frame_artifact_repository import FrameArtifactRepository
from services.frame_artifact_service import FrameArtifactService
from repositories.artifact_repository import ArtifactRepository
from services.artifact_service import ArtifactService
from services.minio_service import MinioService
from services.thumbnail_service import ThumbnailService

def build_route_service(session: AsyncSession) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)

def build_segment_service(session: AsyncSession) -> SegmentService:
    segment_repository = SegmentRepository(session=session)

    frame_repository = FrameRepository(session=session)
    frame_service = FrameService(frame_repository=frame_repository)

    frame_artifact_repository = FrameArtifactRepository(session=session)
    frame_artifact_service = FrameArtifactService(
        frame_artifact_repository=frame_artifact_repository
    )

    artifact_repository = ArtifactRepository(session=session)
    artifact_service = ArtifactService(
        artifact_repository=artifact_repository
    )

    minio_service = MinioService()

    thumbnail_service = ThumbnailService(
        segment_repository=segment_repository,
        minio_service=minio_service,
        frame_service=frame_service,
        frame_artifact_service=frame_artifact_service,
        artifact_service=artifact_service,
    )

    return SegmentService(
        segment_repository=segment_repository,
        thumbnail_service=thumbnail_service,
    )

def build_job_run_service(session: AsyncSession) -> JobRunService:
    repository = JobRunRepository(session=session)
    return JobRunService(job_run_repository=repository)

def build_job_definition_service(session: AsyncSession) -> JobDefinitionService:
    repository = JobDefinitionRepository(session=session)
    return JobDefinitionService(job_definition_repository=repository)