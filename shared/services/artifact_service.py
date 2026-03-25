from uuid import UUID
import uuid

from db.models.artifact import Artifact, ArtifactKind
from repositories.artifact_repository import ArtifactRepository
from services.errors import ArtifactAlreadyExistsError, ArtifactNotFoundError
# This service is responsible for managing artifacts, which are the outputs of jobs. 
class ArtifactService:
    def __init__(self, artifact_repository: ArtifactRepository) -> None:
        self._artifact_repository = artifact_repository

    async def list_artifacts(self) -> list[Artifact]:
        return await self._artifact_repository.list_all()

    async def get_artifacts_by_kind(self, kind: ArtifactKind) -> list[Artifact]:
        return await self._artifact_repository.get_by_kind(kind)

    async def get_artifact(self, artifact_id: UUID) -> Artifact | None:
        return await self._artifact_repository.get_by_id(artifact_id)

    async def create_artifact(
        self,
        bucket: str,
        object_key: str,
        kind: ArtifactKind,
    ) -> Artifact:
        return await self._artifact_repository.create(
            artifact_id=uuid.uuid4(),
            bucket=bucket,
            object_key=object_key,
            kind=kind,
        )

    # this method is used to set the meta field of an artifact, which is a JSON field that can store any additional information
    async def set_meta(
        self,
        artifact_id: UUID,
        meta: dict | None, # for now do dict
    ) -> Artifact:
        artifact = await self._artifact_repository.get_by_id(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)

        artifact.meta = meta
        return await self._artifact_repository.save(artifact)

    async def delete_artifact(self, artifact_id: UUID) -> None:
        artifact = await self._artifact_repository.get_by_id(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)

        await self._artifact_repository.delete(artifact)
