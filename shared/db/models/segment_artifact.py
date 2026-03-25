from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import ArtifactRole, artifact_role_enum

# this role tell segment_log for which segment belong to


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
    ForeignKey("artifacts.artifact_id", ondelete="CASCADE"),
    nullable=False,
    )
    # refer to  ArtifactRole. might change based on schema
    role: Mapped[ArtifactRole] = mapped_column(
        artifact_role_enum,
        primary_key=True,
    )

    def __repr__(self):
        return f"{self.route_id}, {self.segment_id}, {self.artifact_id}, {self.role}"
