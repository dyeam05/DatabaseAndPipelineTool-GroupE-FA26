import logging
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

        for obj in objects:
            if obj.object_name is None:
                continue

            self._minio_service.delete_object(
                bucket_name=self._minio_service.bucket_name,
                object_key=obj.object_name,
            )

        await self._segment_repository.delete(segment)

    async def delete_route(self, route_id: str) -> None:
        # delete frame artifacts
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
          
        # delete artifacts from minio
        for obj in artifacts :
            if obj.object_key:
                self._minio_service.delete_object(
                    bucket_name=self._minio_service.bucket_name,
                    object_key=obj.object_key,
                )
        
        route = await self._route_repository.get_by_id(route_id)
        if route:
            await self._route_repository.delete(route)
      
        for artifact in artifacts:
            await self._artifact_repository.delete(artifact)