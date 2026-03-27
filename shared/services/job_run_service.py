from uuid import UUID
from datetime import datetime, timezone
from db.models.job_run import JobRun, JobStatus
from repositories.job_run_repository import JobRunRepository
from services.errors import JobRunAlreadyExistsError, JobRunNotFoundError
datetime.now(timezone.utc)
# This service is responsible for managing job runs.
class JobRunService:
    def __init__(self, job_run_repository: JobRunRepository) -> None:
        self._job_run_repository = job_run_repository

    async def list_job_runs(self) -> list[JobRun]:
        return await self._job_run_repository.list_all()

    async def get_job_runs_by_status(self, status: JobStatus) -> list[JobRun]:
        return await self._job_run_repository.get_by_status(status)

    async def get_next_job_run_by_status(self, status: JobStatus) -> JobRun | None:
        return await self._job_run_repository.get_next_by_status(status)

    async def get_job_run(self, job_run_num: int, job_def_id: int, route_id: str) -> JobRun | None:
        return await self._job_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id
        )

    async def create_job_run(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
    ) -> JobRun:
        existing = await self._job_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id
        )
        if existing is not None:
            raise JobRunAlreadyExistsError(
                job_run_num=job_run_num, 
                job_def_id=job_def_id,
                route_id=route_id
            )

        return await self._job_run_repository.create(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id
        )

    async def set_status(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        status: JobStatus,
    ) -> JobRun:
        job_run = await self._job_run_repository.get_by_id(
            job_run_num=job_run_num, 
            job_def_id=job_def_id,
            route_id=route_id
        )
        if job_run is None:
            raise JobRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id
            )
        # When the status of a job run is updated,
        #  we also want to update
        job_run.status = status
        # THIS IS NEEDED
        if status == JobStatus.RUNNING:
            job_run.started_at = datetime.now(timezone.utc) # Set started_at when the job run starts running
        # if the job run is either succeeded, failed, or cancelled
        if status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
            job_run.finished_at = datetime.now(timezone.utc)

        return await self._job_run_repository.save(job_run)

    async def set_error(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        error: str | None, #error is a string that describes the error that may have during job exec.
    ) -> JobRun:
        job_run = await self._job_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id
        )
        if job_run is None:
            raise JobRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id
            )

        job_run.error = error
        return await self._job_run_repository.save(job_run)

    async def set_stats(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        stats: dict | None,
    ) -> JobRun:
        job_run = await self._job_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id
        )
        if job_run is None:
            raise JobRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id
            )

        job_run.stats = stats
        return await self._job_run_repository.save(job_run)

    async def delete_job_run(
        self, 
        job_run_num: int,
        job_def_id: int,
        route_id: str
    ) -> None:
        job_run = await self._job_run_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id
        )
        if job_run is None:
            raise JobRunNotFoundError(
                job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id
            )

        await self._job_run_repository.delete(job_run)
