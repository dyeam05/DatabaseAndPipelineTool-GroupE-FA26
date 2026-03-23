from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.job_frame_artifact import JobFrameArtifact, ArtifactRole


class JobFrameArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        job_run_id,
        frame_pk: int,
        role: ArtifactRole,
    ) -> JobFrameArtifact | None: # get a specific job frame artifact 
        return await self._session.get(
            JobFrameArtifact,
            {
                "job_run_id": job_run_id,
                "frame_pk": frame_pk,
                "role": role,
            },
        )

    async def list_all(self) -> list[JobFrameArtifact]:
        stmt = select(JobFrameArtifact)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_job_run(
        self,
        job_run_id,
    ) -> list[JobFrameArtifact]: # get all frame artifacts associated with a specific job run ID
        stmt = (
            select(JobFrameArtifact)
            .where(JobFrameArtifact.job_run_id == job_run_id)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        job_run_id,
        frame_pk: int,
        artifact_id,
        role: ArtifactRole,
    ) -> JobFrameArtifact:
        job_frame_artifact = JobFrameArtifact(
            job_run_id=job_run_id,
            frame_pk=frame_pk,
            artifact_id=artifact_id,
            role=role,
        )
        self._session.add(job_frame_artifact)
        await self._session.flush()
        return job_frame_artifact

    async def save(self, job_frame_artifact: JobFrameArtifact) -> JobFrameArtifact:
        self._session.add(job_frame_artifact)
        await self._session.flush()
        return job_frame_artifact

    async def delete(self, job_frame_artifact: JobFrameArtifact) -> None:
        await self._session.delete(job_frame_artifact)
        await self._session.flush()
