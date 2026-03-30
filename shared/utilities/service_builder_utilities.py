from sqlalchemy.ext.asyncio import AsyncSession

from repositories.route_repository import RouteRepository
from services.route_service import RouteService
from repositories.segment_repository import SegmentRepository
from services.segment_service import SegmentService

def build_route_service(session: AsyncSession) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)

def build_segment_service(session: AsyncSession) -> SegmentService:
    repository = SegmentRepository(session=session)
    return SegmentService(segment_repository=repository)