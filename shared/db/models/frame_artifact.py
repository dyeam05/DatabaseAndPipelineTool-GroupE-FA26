from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

# this role tell job_frame_artifact for which
class ArtifactRole(StrEnum):
    FRAME_IMAGE = "frame_image"

class FrameArtifact(Base):
    __tablename__ = "frame_artifacts"

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
        return f"{self.frame_pk}, {self.artifact_id}, {self.role}"