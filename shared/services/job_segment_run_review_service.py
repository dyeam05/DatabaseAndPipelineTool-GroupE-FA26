import logging

from db.enums import JobSegmentRunReviewStatus
from db.models.job_segment_run_review import JobSegmentRunReview
from repositories.job_segment_run_review_repository import JobSegmentRunReviewRepository
from services.errors import JobSegmentRunNotFoundError

logger = logging.getLogger(__name__)

class JobSegmentRunReviewService:
    def __init__(self, job_segment_run_review_repository: JobSegmentRunReviewRepository):
        self._job_segment_run_review_repository = job_segment_run_review_repository

    async def get_by_id(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
    ) -> JobSegmentRunReview | None:
        return await self._job_segment_run_review_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id
        )

    async def list_all(self) -> list[JobSegmentRunReview]:
        return await self._job_segment_run_review_repository.list_all()

    async def get_by_status(self, status: JobSegmentRunReviewStatus) -> list[JobSegmentRunReview]:
        return await self._job_segment_run_review_repository.get_by_status(status=status)

    async def create(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int
    ) -> JobSegmentRunReview:
        return await self._job_segment_run_review_repository.create(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id
        )

    async def set_status(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
        status: JobSegmentRunReviewStatus
    ) -> JobSegmentRunReview:
        job_segment_run_review = await self._job_segment_run_review_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id
        )

        if not job_segment_run_review:
            raise JobSegmentRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id,
                segment_id=segment_id
            )

        job_segment_run_review.status = status
        return await self._job_segment_run_review_repository.save(job_segment_run_review)

    async def get_next_by_status(
        self,
        status: JobSegmentRunReviewStatus
    ) -> JobSegmentRunReview | None:
        return await self._job_segment_run_review_repository.get_next_by_status(
            status=status
        )

    async def get_next_by_statuses(self, statuses: list[JobSegmentRunReviewStatus]) -> JobSegmentRunReview | None:
        return await self._job_segment_run_review_repository.get_next_by_statuses(statuses=statuses)
