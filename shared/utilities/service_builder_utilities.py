from sqlalchemy.ext.asyncio import AsyncSession

from repositories.job_segment_run_review_repository import JobSegmentRunReviewRepository
from repositories.route_repository import RouteRepository
from services.job_segment_run_review_service import JobSegmentRunReviewService
from services.route_service import RouteService
from repositories.segment_repository import SegmentRepository
from services.segment_service import SegmentService
from repositories.job_run_repository import JobRunRepository
from services.job_run_service import JobRunService
from repositories.job_definition_repository import JobDefinitionRepository
from services.job_definition_service import JobDefinitionService


def build_route_service(session: AsyncSession) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)

def build_segment_service(session: AsyncSession) -> SegmentService:
    repository = SegmentRepository(session=session)
    return SegmentService(segment_repository=repository)

def build_job_run_service(session: AsyncSession) -> JobRunService:
    repository = JobRunRepository(session=session)
    return JobRunService(job_run_repository=repository)

def build_job_definition_service(session: AsyncSession) -> JobDefinitionService:
    repository = JobDefinitionRepository(session=session)
    return JobDefinitionService(job_definition_repository=repository)

def build_job_segment_run_review_service(session: AsyncSession) -> JobSegmentRunReviewService:
    job_segment_run_review_repository = JobSegmentRunReviewRepository(session=session)
    return JobSegmentRunReviewService(job_segment_run_review_repository=job_segment_run_review_repository)
