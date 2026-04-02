from sqlalchemy.ext.asyncio import AsyncSession

from repositories.route_repository import RouteRepository
from services.route_service import RouteService
from repositories.segment_repository import SegmentRepository
from services.segment_service import SegmentService
from repositories.job_run_repository import JobRunRepository
from services.job_run_service import JobRunService

def build_route_service(session: AsyncSession) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)

def build_segment_service(session: AsyncSession) -> SegmentService:
    repository = SegmentRepository(session=session)
    return SegmentService(segment_repository=repository)

def build_job_run_service(session: AsyncSession) -> JobRunService:
    repository = JobRunRepository(session=session)
    return JobRunService(job_run_repository=repository)