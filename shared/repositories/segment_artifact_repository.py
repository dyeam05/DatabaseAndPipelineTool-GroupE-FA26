from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.segment_artifact import SegmentArtifact, ArtifactRole


class SegmentArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        route_id: str,
        segment_id: int,
        role: ArtifactRole,
    ) -> SegmentArtifact | None:
        return await self._session.get(
            SegmentArtifact,
            {
                "route_id": route_id,
                "segment_id": segment_id,
                "role": role,
            },
        )

    async def list_all(self) -> list[SegmentArtifact]:
        stmt = select(SegmentArtifact)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_route_segment(
        self,
        route_id: str,
        segment_id: int,
    ) -> list[SegmentArtifact]:
        stmt = (
            select(SegmentArtifact)
            .where(SegmentArtifact.route_id == route_id)
            .where(SegmentArtifact.segment_id == segment_id)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        route_id: str,
        segment_id: int,
        artifact_id,
        role: ArtifactRole,
    ) -> SegmentArtifact:
        segment_artifact = SegmentArtifact(
            route_id=route_id,
            segment_id=segment_id,
            artifact_id=artifact_id,
            role=role,
        )
        self._session.add(segment_artifact)
        await self._session.flush()
        return segment_artifact

    async def save(self, segment_artifact: SegmentArtifact) -> SegmentArtifact:
        self._session.add(segment_artifact)
        await self._session.flush()
        return segment_artifact

    async def delete(self, segment_artifact: SegmentArtifact) -> None:
        await self._session.delete(segment_artifact)
        await self._session.flush()