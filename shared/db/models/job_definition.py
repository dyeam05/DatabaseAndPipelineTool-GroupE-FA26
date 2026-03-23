from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum, String, DateTime, func, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class JobType(StrEnum):
    OBJECT_DETECTION = "object_detection"
    SEGMENTATION = "segmentation"
    DEPTH = "depth"
    ANNOTATION = "annotation"


class JobDefinition(Base):
    __tablename__ = "job_definitions"

    job_def_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    type: Mapped[JobType] = mapped_column(
        Enum(
            JobType,
            name="job_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"{self.job_def_id}, {self.type}, {self.name}"