import logging
from collections import defaultdict
from itertools import chain

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.segment import Segment
from repositories.segment_repository import SegmentRepository
from services.minio_service import MinioService
from utilities.minio_utilities import get_segment_object_name
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
        session: AsyncSession,
    ) -> None:
        self._segment_repository = segment_repository
        self._minio_service = minio_service
        self._route_repository = route_repository
        self._artifact_repository = artifact_repository
        self._session = session


    async def delete_segment(self, route_id: str, segment_id: int) -> None:
        segment = await self._segment_repository.get_by_id(route_id, segment_id)
        if segment is None:
            return

        prefix = get_segment_object_name(segment)

        objects = self._minio_service.minio_client.list_objects(
            bucket_name=self._minio_service.bucket_name,
            prefix=prefix,
            recursive=True,
        )

        object_keys: list[str] = []
        for obj in objects:
            if obj.object_name is None:
                continue
            object_keys.append(obj.object_name)

        if object_keys:
            self._minio_service.delete_objects(
                bucket_name=self._minio_service.bucket_name,
                object_keys=object_keys,
            )

        await self._segment_repository.delete(segment)

    async def delete_route(self, route_id: str) -> None:
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
