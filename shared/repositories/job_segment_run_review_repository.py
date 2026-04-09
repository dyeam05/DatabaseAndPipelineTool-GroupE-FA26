import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import JobSegmentRunReviewStatus
from db.models.job_segment_run_review import JobSegmentRunReview

logger = logging.getLogger(__name__)

class JobSegmentRunReviewRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
    ) -> JobSegmentRunReview | None:

        return await self._session.get(
            JobSegmentRunReview,
            {
                "job_run_num":job_run_num, 
                "job_def_id": job_def_id, 
                "route_id": route_id,
                "segment_id": segment_id
            }
        )

    async def list_all(self) -> list[JobSegmentRunReview]:
        stmt = select(JobSegmentRunReview)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_status(self, status: JobSegmentRunReviewStatus) -> list[JobSegmentRunReview]:
        stmt = (
            select(JobSegmentRunReview)
            .where(JobSegmentRunReview.status == status)
            .order_by(JobSegmentRunReview.segment_id.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int
    ) -> JobSegmentRunReview:
        job_segment_run_review = JobSegmentRunReview(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id,
            status=JobSegmentRunReviewStatus.QUEUED_FOR_LOADING
        )

        self._session.add(job_segment_run_review)
        await self._session.flush()
        return job_segment_run_review

    async def save(self, job_segment_run_review: JobSegmentRunReview) -> JobSegmentRunReview:
        self._session.add(job_segment_run_review)
        await self._session.flush()
        return job_segment_run_review

    async def delete(self, job_segment_run_review) -> None:
        await self._session.delete(job_segment_run_review)
        await self._session.flush()

    async def get_next_by_status(self, status: JobSegmentRunReviewStatus) -> JobSegmentRunReview | None:
        stmt = (
            select(JobSegmentRunReview)
            .where(JobSegmentRunReview.status == status)
            .order_by(JobSegmentRunReview.created_at.asc())
            .limit(1)
        )

        result = await self._session.scalars(stmt)
        return result.first()


