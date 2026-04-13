from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import CameraType, JobSegmentRunStatus
from db.models.job_segment_run import JobSegmentRun

class JobSegmentRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, 
        job_run_num:int, 
        job_def_id:int, 
        route_id:str, 
        segment_id:int,
        camera: CameraType,
    ) -> JobSegmentRun | None:
        return await self._session.get(JobSegmentRun, {
            "job_run_num":job_run_num, 
            "job_def_id": job_def_id, 
            "route_id": route_id,
            "segment_id": segment_id,
            "camera": camera
        })


    async def list_all(self) -> list[JobSegmentRun]:
        stmt = select(JobSegmentRun)
        result = await self._session.scalars(stmt)
        return list(result.all())        

    async def get_by_status(self, status: JobSegmentRunStatus) -> list[JobSegmentRun]:
        stmt = (
            select(JobSegmentRun)
            .where(JobSegmentRun.status == status)
            .order_by(JobSegmentRun.segment_id.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())
        

    async def get_segments_by_job_run(
       self, 
       job_run_num: int, 
       job_def_id: int, 
       route_id: str
    ) -> list[JobSegmentRun]:
        stmt = (
            select(JobSegmentRun)
            .where(
                JobSegmentRun.job_run_num == job_run_num,
                JobSegmentRun.job_def_id == job_def_id,
                JobSegmentRun.route_id == route_id,
            )
        )
        result = await self._session.scalars(stmt)
        return list(result.all())


    async def create(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
        camera: CameraType,
        artifact_id: UUID | None = None,
    ) -> JobSegmentRun:
        job_segment_run = JobSegmentRun(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
            artifact_id=artifact_id,
            camera=camera,
            status=JobSegmentRunStatus.QUEUED,
        )
        self._session.add(job_segment_run)
        await self._session.flush()
        return job_segment_run


    async def save(self, job_segment_run: JobSegmentRun) -> JobSegmentRun:
        self._session.add(job_segment_run)
        await self._session.flush()
        return job_segment_run

    async def delete(self, job_segment_run: JobSegmentRun) -> None:
        await self._session.delete(job_segment_run)
        await self._session.flush()
