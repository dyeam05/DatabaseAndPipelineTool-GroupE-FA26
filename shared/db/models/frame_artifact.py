from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import ArtifactRole, artifact_role_enum

# this role tell job_frame_artifact for which
# enforece one artifact role per frame
class FrameArtifact(Base):
    __tablename__ = "frame_artifacts"

    frame_pk: Mapped[int] = mapped_column(
        ForeignKey("frames.frame_pk", ondelete="CASCADE"),
        primary_key=True,
    )
    artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("artifacts.artifact_id"),
         nullable=False,
    )
    role: Mapped[ArtifactRole] = mapped_column(
        artifact_role_enum,
        primary_key=True,
    )

    def __repr__(self):
        return f"FrameArtifact({self.frame_pk}, {self.artifact_id}, {self.role})"
