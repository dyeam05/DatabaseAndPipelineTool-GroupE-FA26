from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.artifact import Artifact, ArtifactKind
# repo for managing Artifact entities in the database


class ArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, artifact_id) -> Artifact | None:
        return await self._session.get(Artifact, artifact_id)

    async def list_all(self) -> list[Artifact]:
        stmt = select(Artifact).order_by(Artifact.created_at.desc())
        # order by created_at desc to get the most recent artifacts first
        # then session.scalars() is used to execute the query and extract the Artifact
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_kind(self, kind: ArtifactKind) -> list[Artifact]:
        stmt = (
            select(Artifact)
            .where(Artifact.kind == kind)
            .order_by(Artifact.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        artifact_id: UUID,
        bucket: str,
        object_key: str,
        kind: ArtifactKind,
    ) -> Artifact:
        artifact = Artifact(
            artifact_id=artifact_id,
            bucket=bucket,
            object_key=object_key,
            kind=kind,
            meta=None,
        )
        self._session.add(artifact)
        await self._session.flush()
        return artifact

    async def save(self, artifact: Artifact) -> Artifact:
        self._session.add(artifact)
        await self._session.flush()
        return artifact

    async def delete(self, artifact: Artifact) -> None:
        await self._session.delete(artifact)
        await self._session.flush()
