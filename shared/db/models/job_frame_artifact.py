from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

# this role tell job_frame_artifact for which 
# artifact belong to, like detection json, segmentation mask, segmentation map, depth map, coco export etc.
from db.models.artifact_role import ArtifactRole


class JobFrameArtifact(Base):
    __tablename__ = "job_frame_artifacts"

    job_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_runs.job_run_id", ondelete="CASCADE"),
        primary_key=True,
    )
    frame_pk: Mapped[int] = mapped_column(
        ForeignKey("frames.frame_pk", ondelete="CASCADE"),
        primary_key=True,
    )
    artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("artifacts.artifact_id"),
        primary_key=True,
    )
    role: Mapped[ArtifactRole] = mapped_column(
        Enum(
            ArtifactRole,
            name="artifact_role",
            native_enum=True,
            validate_strings=True,
        ),
        primary_key=True,
    )

    def __repr__(self):
        return f"{self.job_run_id}, {self.frame_pk}, {self.artifact_id}, {self.role}"