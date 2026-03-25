from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import String, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import ArtifactKind, artifact_kind_enum

# this tell artifact kind, like image, json or parquet


class Artifact(Base):
    __tablename__ = "artifacts"

    artifact_id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    bucket: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    object_key: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    # this is the kind of the artifact know how to read the artifact
    kind: Mapped[ArtifactKind] = mapped_column(
        artifact_kind_enum,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    #json field to store some extra information about the artifact
    meta: Mapped[dict[Any, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    def __repr__(self):
        return f"Artifact({self.artifact_id}, {self.bucket}, {self.object_key}, {self.kind})"
