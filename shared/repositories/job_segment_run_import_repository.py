import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import CameraType, JobSegmentRunImportStatus
from db.models.job_segment_run_import import JobSegmentRunImport

logger = logging.getLogger(__name__)

class JobSegmentRunImportRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
        camera: CameraType,
    ) -> JobSegmentRunImport | None:

        return await self._session.get(
            JobSegmentRunImport,
            {
                "job_run_num":job_run_num, 
                "job_def_id": job_def_id, 
                "route_id": route_id,
                "segment_id": segment_id,
                "camera": camera
            }
        )

    async def list_all(self) -> list[JobSegmentRunImport]:
        stmt = select(JobSegmentRunImport)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_route_id(self, route_id: str) -> list[JobSegmentRunImport]:
        stmt = (
            select(JobSegmentRunImport)
            .where(JobSegmentRunImport.route_id == route_id)
            .order_by(
                JobSegmentRunImport.job_run_num.asc(),
                JobSegmentRunImport.job_def_id.asc(),
                JobSegmentRunImport.segment_id.asc(),
                JobSegmentRunImport.camera.asc(),
            )
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_job(
        self,
        job_def_id: int,
        job_run_num: int,
        route_id: str,
        camera: CameraType,
    ) -> list[JobSegmentRunImport]:
        stmt = (
            select(JobSegmentRunImport)
            .where(
                JobSegmentRunImport.job_def_id == job_def_id,
                JobSegmentRunImport.job_run_num == job_run_num,
                JobSegmentRunImport.route_id == route_id,
                JobSegmentRunImport.camera == camera
            )
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_job_def(self, job_def_id: int) -> list[JobSegmentRunImport]:
        stmt = (
            select(JobSegmentRunImport)
            .where(JobSegmentRunImport.job_def_id == job_def_id)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_status(self, status: JobSegmentRunImportStatus) -> list[JobSegmentRunImport]:
        stmt = (
            select(JobSegmentRunImport)
            .where(JobSegmentRunImport.status == status)
            .order_by(JobSegmentRunImport.segment_id.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        camera: CameraType,
        segment_id: int
    ) -> JobSegmentRunImport:
        job_segment_run_review = JobSegmentRunImport(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
            camera=camera,
            status=JobSegmentRunImportStatus.QUEUED_FOR_LOADING
        )

        self._session.add(job_segment_run_review)
        await self._session.flush()
        return job_segment_run_review
    
    async def set_error(self, job_segment_run_import: JobSegmentRunImport, error_message: str) -> JobSegmentRunImport:
        job_segment_run_import.status = JobSegmentRunImportStatus.FAILED
        job_segment_run_import.error_message = error_message
        await self._session.flush()
        return job_segment_run_import

    async def save(self, job_segment_run_review: JobSegmentRunImport) -> JobSegmentRunImport:
        self._session.add(job_segment_run_review)
        await self._session.flush()
        return job_segment_run_review

    async def delete(self, job_segment_run_review) -> None:
        await self._session.delete(job_segment_run_review)
        await self._session.flush()

    async def get_next_by_status(self, status: JobSegmentRunImportStatus) ->  JobSegmentRunImport| None:
        stmt = (
            select(JobSegmentRunImport)
            .where(JobSegmentRunImport.status == status)
            .order_by(JobSegmentRunImport.created_at.asc())
            .limit(1)
        )

        result = await self._session.scalars(stmt)
        return result.first()

    async def get_next_by_statuses(self, statuses: list[JobSegmentRunImportStatus]) ->  JobSegmentRunImport| None:
        stmt = (
            select(JobSegmentRunImport)
            .where(JobSegmentRunImport.status.in_(statuses))
            .order_by(JobSegmentRunImport.created_at.asc())
            .limit(1)
        )
        result = await self._session.scalars(stmt)
        return result.first()

