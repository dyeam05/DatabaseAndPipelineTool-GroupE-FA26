import logging
from collections import defaultdict
from itertools import chain

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import JobSegmentRunImportStatus
from db.models.segment import Segment
from repositories.segment_repository import SegmentRepository
from services.cvat_service import CVATService
from services.errors import RouteDeleteError
from services.job_segment_run_import_service import JobSegmentRunImportService
from services.minio_service import MinioService
from repositories.route_repository import RouteRepository
from repositories.artifact_repository import ArtifactRepository
from db.models import JobSegmentRun, SegmentArtifact, DatasetExport, Artifact, FrameArtifact, Frame

logger = logging.getLogger(__name__)

class DeleteService:
    def __init__(
        self,
        segment_repository: SegmentRepository,
        minio_service: MinioService,
        route_repository: RouteRepository,
        artifact_repository: ArtifactRepository,
        cvat_service: CVATService,
        job_segment_run_import_service: JobSegmentRunImportService,
        session: AsyncSession,
    ) -> None:
        self._segment_repository = segment_repository
        self._minio_service = minio_service
        self._route_repository = route_repository
        self._artifact_repository = artifact_repository
        self._cvat_service = cvat_service
        self._job_segment_run_import_service = job_segment_run_import_service
        self._session = session

    async def delete_route(self, route_id: str) -> None:
        # delete cvat imports
        await self.delete_cvat_imports_for_route(route_id=route_id)
        # delete frame artifacts
        logger.info(f"Deleting route {route_id}")
        stmt =(
            select(Artifact)
            .join(FrameArtifact, Artifact.artifact_id == FrameArtifact.artifact_id)
            .join(Frame, Frame.frame_pk == FrameArtifact.frame_pk)
            .where(Frame.route_id == route_id)
        )
        artifacts_from_frame = (await self._session.scalars(stmt)).all()
        # delete segment artifacts
        stmt= (
            select(Artifact)
            .join(SegmentArtifact, Artifact.artifact_id == SegmentArtifact.artifact_id)
            .join(Segment)
            .where(Segment.route_id == route_id)
        )
        artifacts_from_segment = (await self._session.scalars(stmt)).all()
        # delete job segmnent runs
        stmt =(
            select(Artifact)
            .join(JobSegmentRun, Artifact.artifact_id == JobSegmentRun.artifact_id)
            .where(JobSegmentRun.route_id == route_id)
        )
        artifacts_from_job_segment_run = (await self._session.scalars(stmt)).all()
        # delete dataset exports
        stmt =(
            select(Artifact)
            .join(DatasetExport, Artifact.artifact_id == DatasetExport.zip_artifact_id)
            .where(DatasetExport.route_id == route_id)
        )
        artifacts_from_dataset_export = (await self._session.scalars(stmt)).all()

        artifacts =  list(chain(artifacts_from_frame, artifacts_from_segment, artifacts_from_job_segment_run, artifacts_from_dataset_export))
        logger.info(f"Preparing to delete {len(artifacts)} minio artifacts")

        # delete artifacts from minio
        object_keys_by_bucket: dict[str, list[str]] = defaultdict(list)
        for obj in artifacts:
            if obj.object_key:
                object_keys_by_bucket[obj.bucket].append(obj.object_key)

        for bucket_name, object_keys in object_keys_by_bucket.items():
            self._minio_service.delete_objects(
                bucket_name=bucket_name,
                object_keys=object_keys,
            )

        route = await self._route_repository.get_by_id(route_id)
        if route:
            await self._route_repository.delete(route)

        for artifact in artifacts:
            await self._artifact_repository.delete(artifact)

    async def delete_cvat_imports_for_route(self, route_id: str) -> None:
        logger.info(f"Deleting CVAT imports for route {route_id}")
        imports_to_delete = await self._job_segment_run_import_service.get_by_route_id(route_id=route_id)
        logger.info(f"Deleting {len(imports_to_delete)} CVAT imports for route {route_id}")
        for import_to_delete in imports_to_delete:
            # Raise error if trying to delete a route while an import is in-progress, as this could cause race conditions
            if import_to_delete.status not in [JobSegmentRunImportStatus.LOADED, JobSegmentRunImportStatus.REMOVED, JobSegmentRunImportStatus.FAILED]:
                logger.error(f"Can not delete route with job segment run import having status {import_to_delete.status}")
                raise RouteDeleteError(reason=f"Can not delete route with job segment run import having status {import_to_delete.status}")

            if import_to_delete.status == JobSegmentRunImportStatus.LOADED and import_to_delete.task_id is not None:
                self._cvat_service.delete_task(task_id=import_to_delete.task_id)

        return 



