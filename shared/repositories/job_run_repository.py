from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.job_run import JobRun, JobStatus


class JobRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, job_run_num:int, job_def_id:int, route_id:str) -> JobRun | None:
        return await self._session.get(JobRun, {
            "job_run_num":job_run_num, 
            "job_def_id": job_def_id, 
            "route_id": route_id
        }) # id refer to job_run_id in JobRun model

    async def list_all(self) -> list[JobRun]:
        stmt = select(JobRun).order_by(JobRun.queued_at.desc()) # order by queued_at in descending order to get the most recent job runs first
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_status(self, status: JobStatus) -> list[JobRun]:
        stmt = (
            select(JobRun)
            .where(JobRun.status == status)
            .order_by(JobRun.queued_at.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_next_by_status(self, status: JobStatus) -> JobRun | None:
        stmt = (
            select(JobRun)
            .where(JobRun.status == status)
            .order_by(JobRun.queued_at.asc())
            .limit(1) # for now just get next job run at for simple stuff
        )
        result = await self._session.scalars(stmt)
        return result.first()

    async def create(
        self,
        job_def_id: int,
        route_id: str,
    ) -> JobRun:
        job_run = JobRun(
            job_def_id=job_def_id,
            route_id=route_id,
            status=JobStatus.QUEUED,
        )
        self._session.add(job_run)
        await self._session.flush()
        return job_run

    async def save(self, job_run: JobRun) -> JobRun:
        self._session.add(job_run)
        await self._session.flush()
        return job_run

    async def delete(self, job_run: JobRun) -> None:
        await self._session.delete(job_run)
        await self._session.flush()
