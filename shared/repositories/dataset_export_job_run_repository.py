from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import CameraType
from db.models.dataset_export_job_run import DatasetExportJobRun


class DatasetExportJobRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_export_id(self, export_id: int) -> list[DatasetExportJobRun]:
        stmt = (
            select(DatasetExportJobRun)
            .where(DatasetExportJobRun.export_id == export_id)
            .order_by(
                DatasetExportJobRun.camera.asc(),
                DatasetExportJobRun.job_def_id.asc(),
                DatasetExportJobRun.job_run_num.asc(),
            )
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        export_id: int,
        route_id: str,
        job_def_id: int,
        job_run_num: int,
        camera: CameraType,
    ) -> DatasetExportJobRun:
        dataset_export_job_run = DatasetExportJobRun(
            export_id=export_id,
            route_id=route_id,
            job_def_id=job_def_id,
            job_run_num=job_run_num,
            camera=camera,
        )
        self._session.add(dataset_export_job_run)
        await self._session.flush()
        return dataset_export_job_run

    async def delete(self, dataset_export_job_run: DatasetExportJobRun) -> None:
        await self._session.delete(dataset_export_job_run)
        await self._session.flush()
