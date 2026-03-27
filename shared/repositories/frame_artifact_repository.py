
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.frame_artifact import FrameArtifact, ArtifactRole
# repo for managing Frame Artifact entities in the database


class FrameArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        frame_pk: int,
        role: ArtifactRole,
    ) -> FrameArtifact | None:  # composite primary key of frame_pk and role
        return await self._session.get(
            FrameArtifact,
            {
                "frame_pk": frame_pk,
                "role": role,
            },
        )

    async def list_all(self) -> list[FrameArtifact]:
        stmt = select(FrameArtifact)
        result = await self._session.scalars(stmt)  # scalars() is used to extract the FrameArtifact objects from the result set
        return list(result.all())

    async def get_by_frame(
        self,
        frame_pk: int,
    ) -> list[FrameArtifact]:
        stmt = (
            select(FrameArtifact)
            .where(FrameArtifact.frame_pk == frame_pk)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        frame_pk: int,
        artifact_id,
        role: ArtifactRole,
    ) -> FrameArtifact:
        frame_artifact = FrameArtifact(
            frame_pk=frame_pk,
            artifact_id=artifact_id,
            role=role,
        )
        self._session.add(frame_artifact)
        await self._session.flush()
        return frame_artifact

    async def save(self, frame_artifact: FrameArtifact) -> FrameArtifact:
        self._session.add(frame_artifact)  # add the frame artifact to the session.
        await self._session.flush()
        return frame_artifact

    async def delete(self, frame_artifact: FrameArtifact) -> None:
        await self._session.delete(frame_artifact)
        await self._session.flush()
