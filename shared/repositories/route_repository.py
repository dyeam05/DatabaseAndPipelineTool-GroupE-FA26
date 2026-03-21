from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.route import Route, RouteStatus


class RouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, route_id: str) -> Route | None:
        return await self._session.get(Route, route_id)

    async def list_all(self) -> list[Route]:
        stmt = select(Route).order_by(Route.created_at.desc())
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        route_id: str,
        status: RouteStatus,
    ) -> Route:
        route = Route(route_id=route_id, status=status, file_path=None)
        self._session.add(route)
        await self._session.flush()
        return route

    async def save(self, route: Route) -> Route:
        self._session.add(route)
        await self._session.flush()
        return route

    async def delete(self, route: Route) -> None:
        await self._session.delete(route)
        await self._session.flush()
