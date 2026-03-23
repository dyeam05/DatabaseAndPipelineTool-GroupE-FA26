from uuid import UUID

from db.models.job_frame_artifact import JobFrameArtifact, ArtifactRole
from repositories.job_frame_artifact_repository import JobFrameArtifactRepository
from services.errors import JobFrameArtifactAlreadyExistsError, JobFrameArtifactNotFoundError

# This service is responsible for managing job frame artifacts
#
class JobFrameArtifactService:
    def __init__(self, job_frame_artifact_repository: JobFrameArtifactRepository) -> None:
        self._job_frame_artifact_repository = job_frame_artifact_repository

    async def list_job_frame_artifacts(self) -> list[JobFrameArtifact]:
        return await self._job_frame_artifact_repository.list_all()

    async def get_job_frame_artifacts_by_job_run(
        self,
        job_run_id,
    ) -> list[JobFrameArtifact]:
        return await self._job_frame_artifact_repository.get_by_job_run(job_run_id)

    async def get_job_frame_artifact(
        self,
        job_run_id,
        frame_pk: int,
        role: ArtifactRole,
    ) -> JobFrameArtifact | None:
        return await self._job_frame_artifact_repository.get_by_id(job_run_id, frame_pk, role)

    async def create_job_frame_artifact(
        self,
        job_run_id,
        frame_pk: int,
        artifact_id: UUID,
        role: ArtifactRole, # artifact role is the type of artifact
    ) -> JobFrameArtifact:
        existing = await self._job_frame_artifact_repository.get_by_id(job_run_id, frame_pk, role)
        if existing is not None:
            raise JobFrameArtifactAlreadyExistsError(job_run_id, frame_pk, role)

        return await self._job_frame_artifact_repository.create(
            job_run_id=job_run_id,
            frame_pk=frame_pk,
            artifact_id=artifact_id,
            role=role,
        )

    async def delete_job_frame_artifact(
        self,
        job_run_id,
        frame_pk: int,
        role: ArtifactRole,
    ) -> None:
        job_frame_artifact = await self._job_frame_artifact_repository.get_by_id(job_run_id, frame_pk, role)
        if job_frame_artifact is None:
            raise JobFrameArtifactNotFoundError(job_run_id, frame_pk, role)

        await self._job_frame_artifact_repository.delete(job_frame_artifact)
