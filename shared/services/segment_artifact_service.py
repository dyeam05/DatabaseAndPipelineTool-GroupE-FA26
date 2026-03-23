from uuid import UUID

from db.models.segment_artifact import SegmentArtifact, ArtifactRole
from repositories.segment_artifact_repository import SegmentArtifactRepository
from services.errors import SegmentArtifactAlreadyExistsError, SegmentArtifactNotFoundError

# Service layer for managing segment artifacts,
#
class SegmentArtifactService:
    def __init__(self, segment_artifact_repository: SegmentArtifactRepository) -> None:
        self._segment_artifact_repository = segment_artifact_repository

    async def list_segment_artifacts(self) -> list[SegmentArtifact]:
        return await self._segment_artifact_repository.list_all()

    async def get_segment_artifacts_by_route_segment(
        self,
        route_id: str,
        segment_id: int,
    ) -> list[SegmentArtifact]:
        return await self._segment_artifact_repository.get_by_route_segment(route_id, segment_id)

    async def get_segment_artifact(
        self,
        route_id: str,
        segment_id: int,
        role: ArtifactRole,
    ) -> SegmentArtifact | None:
        return await self._segment_artifact_repository.get_by_id(route_id, segment_id, role)

    async def create_segment_artifact(
        self,
        route_id: str,
        segment_id: int,
        artifact_id: UUID,
        role: ArtifactRole,
    ) -> SegmentArtifact:
        existing = await self._segment_artifact_repository.get_by_id(route_id, segment_id, role)
        if existing is not None:
            raise SegmentArtifactAlreadyExistsError(route_id, segment_id, role)

        return await self._segment_artifact_repository.create(
            route_id=route_id,
            segment_id=segment_id,
            artifact_id=artifact_id,
            role=role,
        )

    async def delete_segment_artifact(
        self,
        route_id: str,
        segment_id: int,
        role: ArtifactRole,
    ) -> None:
        segment_artifact = await self._segment_artifact_repository.get_by_id(route_id, segment_id, role)
        if segment_artifact is None:
            raise SegmentArtifactNotFoundError(route_id, segment_id, role)

        await self._segment_artifact_repository.delete(segment_artifact)