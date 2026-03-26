from uuid import UUID

from db.models.frame_artifact import FrameArtifact, ArtifactRole
from repositories.frame_artifact_repository import FrameArtifactRepository
from services.errors import FrameArtifactAlreadyExistsError, FrameArtifactNotFoundError

# This service is responsible for managing frame artifacts, which are associated with frames and have specific roles.


class FrameArtifactService:
    def __init__(self, frame_artifact_repository: FrameArtifactRepository) -> None:
        self._frame_artifact_repository = frame_artifact_repository

    async def list_frame_artifacts(self) -> list[FrameArtifact]:
        return await self._frame_artifact_repository.list_all()

    async def get_frame_artifacts_by_frame(
        self,
        frame_pk: int,
    ) -> list[FrameArtifact]:
        return await self._frame_artifact_repository.get_by_frame(frame_pk)

    async def get_frame_artifact(
        self,
        frame_pk: int,
        role: ArtifactRole,  # role refer to the type of artifact. migh add more later
    ) -> FrameArtifact | None:
        return await self._frame_artifact_repository.get_by_id(
            frame_pk=frame_pk,
            role=role,
        )

    async def create_frame_artifact(
    self,
    frame_pk: int,
    artifact_id: UUID,
    role: ArtifactRole,
    ) -> FrameArtifact:
        existing = await self._frame_artifact_repository.get_by_id(
            frame_pk=frame_pk,
            role=role,
        )
        if existing is not None:
            raise FrameArtifactAlreadyExistsError(frame_pk, role)

        return await self._frame_artifact_repository.create(
            frame_pk=frame_pk,
            artifact_id=artifact_id,
            role=role,
        )

    async def delete_frame_artifact(
        self,
        frame_pk: int,
        role: ArtifactRole,
    ) -> None:
        frame_artifact = await self._frame_artifact_repository.get_by_id(
            frame_pk=frame_pk,
            role=role,
        )
        if frame_artifact is None:
            raise FrameArtifactNotFoundError(frame_pk, role)

        await self._frame_artifact_repository.delete(frame_artifact)
