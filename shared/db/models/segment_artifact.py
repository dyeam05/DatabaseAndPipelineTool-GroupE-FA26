from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class ArtifactRole(StrEnum):
    SEGMENT_LOG = "segment_log"


class SegmentArtifact(Base):
    __tablename__ = "segment_artifacts"

    __table_args__ = (
        ForeignKeyConstraint(
            ["route_id", "segment_id"],
            ["segments.route_id", "segments.segment_id"],
            ondelete="CASCADE",
        ),
    )

    route_id: Mapped[str] = mapped_column(
        primary_key=True,
    )
    segment_id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    artifact_id: Mapped[UUID] = mapped_column(
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
        return f"{self.route_id}, {self.segment_id}, {self.artifact_id}, {self.role}"