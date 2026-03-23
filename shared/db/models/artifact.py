from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, String, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class ArtifactKind(StrEnum):
    IMAGE = "image"
    JSON = "json"
    PARQUET = "parquet"


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
    kind: Mapped[ArtifactKind] = mapped_column(
        Enum(
            ArtifactKind,
            name="artifact_kind",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    meta: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    def __repr__(self):
        return f"{self.artifact_id}, {self.bucket}, {self.object_key}, {self.kind}"