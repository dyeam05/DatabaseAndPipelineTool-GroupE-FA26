from sqlalchemy.ext.asyncio import AsyncSession

from repositories.route_repository import RouteRepository
from services.route_service import RouteService


def build_route_service(session: AsyncSession) -> RouteService:
    repository = RouteRepository(session=session)
    return RouteService(route_repository=repository)