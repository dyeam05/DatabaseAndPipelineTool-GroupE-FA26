import logging

from db.enums import JobSegmentRunImportStatus
from db.models.job_segment_run_import import JobSegmentRunImport
from repositories.job_segment_run_import_repository import JobSegmentRunImportRepository
from services.errors import JobSegmentRunNotFoundError

logger = logging.getLogger(__name__)

class JobSegmentRunImportService:
    def __init__(self, job_segment_run_import_repository: JobSegmentRunImportRepository):
        self._job_segment_run_import_repository = job_segment_run_import_repository

    async def get_by_id(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int,
    ) -> JobSegmentRunImport | None:
        return await self._job_segment_run_import_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id
        )

    async def list_all(self) -> list[JobSegmentRunImport]:
        return await self._job_segment_run_import_repository.list_all()

    async def get_by_status(self, status: JobSegmentRunImportStatus) -> list[JobSegmentRunImport]:
        return await self._job_segment_run_import_repository.get_by_status(status=status)

    async def create(
        self,
        job_run_num: int,
        job_def_id: int,
        route_id: str,
        segment_id: int
    ) -> JobSegmentRunImport:
        return await self._job_segment_run_import_repository.create(
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
        status: JobSegmentRunImportStatus
    ) -> JobSegmentRunImport:
        job_segment_run_import = await self._job_segment_run_import_repository.get_by_id(
            job_run_num=job_run_num,
            job_def_id=job_def_id,
            route_id=route_id,
            segment_id=segment_id
        )

        if not job_segment_run_import:
            raise JobSegmentRunNotFoundError(
                job_run_num=job_run_num,
                job_def_id=job_def_id,
                route_id=route_id,
                segment_id=segment_id
            )

        job_segment_run_import.status = status
        return await self._job_segment_run_import_repository.save(job_segment_run_import)

    async def get_next_by_status(
        self,
        status: JobSegmentRunImportStatus
    ) -> JobSegmentRunImport | None:
        return await self._job_segment_run_import_repository.get_next_by_status(
            status=status
        )

    async def get_next_by_statuses(self, statuses: list[JobSegmentRunImportStatus]) -> JobSegmentRunImport | None:
        return await self._job_segment_run_import_repository.get_next_by_statuses(statuses=statuses)
