from sqlalchemy.ext.asyncio import AsyncSession

from repositories.job_segment_run_import_repository import JobSegmentRunImportRepository
from repositories.route_repository import RouteRepository
from services.job_segment_run_import_service import JobSegmentRunImportService
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
from repositories.job_segment_run_repository import JobSegmentRunRepository
from services.job_segment_run_service import JobSegmentRunService
from repositories.segment_artifact_repository import SegmentArtifactRepository
from services.segment_artifact_service import SegmentArtifactService
from services.dataset_export_service import DatasetExportService
from repositories.dataset_export_repository import DatasetExportRepository
from repositories.dataset_export_job_run_repository import DatasetExportJobRunRepository


def build_route_service(session: AsyncSession) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)

def build_segment_service(session: AsyncSession) -> SegmentService:
    repository = SegmentRepository(session=session)
    return SegmentService(segment_repository=repository)

def build_frame_service(session: AsyncSession) -> FrameService:
    repository = FrameRepository(session=session)
    return FrameService(frame_repository=repository)

def build_artifact_service(session: AsyncSession) -> ArtifactService:
    repository = ArtifactRepository(session=session)
    return ArtifactService(artifact_repository=repository)

def build_frame_artifact_service(session: AsyncSession) -> FrameArtifactService:
    repository = FrameArtifactRepository(session=session)
    return FrameArtifactService(frame_artifact_repository=repository)

def build_segment_artifact_service(session: AsyncSession) -> SegmentArtifactService:
    repository = SegmentArtifactRepository(session=session)
    return SegmentArtifactService(segment_artifact_repository=repository)

def build_job_run_service(session: AsyncSession) -> JobRunService:
    job_run_repository = JobRunRepository(session=session)
    route_repository = RouteRepository(session=session)
    job_definition_repository = JobDefinitionRepository(session=session)
    return JobRunService(
        job_run_repository=job_run_repository,
        route_repository=route_repository,
        job_definition_repository=job_definition_repository,
    )

def build_job_definition_service(session: AsyncSession) -> JobDefinitionService:
    repository = JobDefinitionRepository(session=session)
    return JobDefinitionService(job_definition_repository=repository)

def build_thumbnail_service(session: AsyncSession) -> ThumbnailService:
    segment_repository = SegmentRepository(session=session)

    frame_repository = FrameRepository(session=session)
    frame_service = FrameService(frame_repository=frame_repository)

    frame_artifact_repository = FrameArtifactRepository(session=session)
    frame_artifact_service = FrameArtifactService(frame_artifact_repository=frame_artifact_repository)
    artifact_repository = ArtifactRepository(session=session)
    artifact_service = ArtifactService(artifact_repository=artifact_repository)

    minio_service = MinioService()

    return ThumbnailService(
        segment_repository=segment_repository,
        minio_service=minio_service,
        frame_service=frame_service,
        frame_artifact_service=frame_artifact_service,
        artifact_service=artifact_service,
    )
def build_job_segment_run_service(session: AsyncSession) -> JobSegmentRunService:
    repository = JobSegmentRunRepository(session=session)
    return JobSegmentRunService(job_segment_run_repository=repository)

def build_dataset_export_service(session: AsyncSession) -> DatasetExportService:
    dataset_export_repository = DatasetExportRepository(session=session)
    dataset_export_job_run_repository = DatasetExportJobRunRepository(session=session)
    route_repository = RouteRepository(session=session)
    job_run_repository = JobRunRepository(session=session)
    frame_service = build_frame_service(session=session)
    artifact_repository = ArtifactRepository(session=session)
    return DatasetExportService(
        dataset_export_repository=dataset_export_repository,
        dataset_export_job_run_repository=dataset_export_job_run_repository,
        route_repository=route_repository,
        job_run_repository=job_run_repository,
        frame_service=frame_service,
        artifact_repository=artifact_repository,
    )

def build_job_segment_run_import_service(session: AsyncSession) -> JobSegmentRunImportService:
    job_segment_run_import_repository = JobSegmentRunImportRepository(session=session)
    return JobSegmentRunImportService(job_segment_run_import_repository=job_segment_run_import_repository)
