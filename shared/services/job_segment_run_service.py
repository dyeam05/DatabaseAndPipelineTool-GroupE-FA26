from uuid import UUID

from db.enums import JobSegmentRunStatus
from db.models.job_segment_run import JobSegmentRun
from repositories.job_segment_run_repository import JobSegmentRunRepository
from services.errors import JobSegmentRunAlreadyExistsError, JobSegmentRunNotFoundError


class JobSegmentRunService:
    def __init__(self, job_segment_run_repository: JobSegmentRunRepository) -> None:
        self._job_segment_run_repository = job_segment_run_repository

    async def list_job_segment_runs(self) -> list[JobSegmentRun]:
        return await self._job_segment_run_repository.list_all()

    async def get_job_segment_run(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
    ) -> JobSegmentRun | None:
        return await self._job_segment_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
        )

    async def get_segments_by_job_run(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
    ) -> list[JobSegmentRun]:
        return await self._job_segment_run_repository.get_segments_by_job_run(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
        )

    async def get_segments_by_status(self, status: JobSegmentRunStatus) -> list[JobSegmentRun]:
        return await self._job_segment_run_repository.get_by_status(status)

    async def create_job_segment_run(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
    ) -> JobSegmentRun:
        existing = await self._job_segment_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
        )
        if existing is not None:
            raise JobSegmentRunAlreadyExistsError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id,
                segment_id=segment_id,
            )
        return await self._job_segment_run_repository.create(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
        )

    async def set_status(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
        status: JobSegmentRunStatus,
    ) -> JobSegmentRun:
        segment_run = await self._job_segment_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
        )
        if segment_run is None:
            raise JobSegmentRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id,
                segment_id=segment_id,
            )
        segment_run.status = status
        return await self._job_segment_run_repository.save(segment_run)

    async def set_artifact(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
        artifact_id: UUID,
    ) -> JobSegmentRun:
        segment_run = await self._job_segment_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
        )
        if segment_run is None:
            raise JobSegmentRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id,
                segment_id=segment_id,
            )
        segment_run.artifact_id = artifact_id
        return await self._job_segment_run_repository.save(segment_run)

    async def delete_job_segment_run(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
    ) -> None:
        segment_run = await self._job_segment_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
        )
        if segment_run is None:
            raise JobSegmentRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id,
                segment_id=segment_id,
            )
        await self._job_segment_run_repository.delete(segment_run)
