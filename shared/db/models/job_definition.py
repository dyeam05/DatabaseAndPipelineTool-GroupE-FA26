from datetime import datetime

from sqlalchemy import String, DateTime, func, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import JobType, job_type_enum

# this tell job type, like object detection, segmentation, depth or annotation


class JobDefinition(Base):
    __tablename__ = "job_definitions"

    job_def_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    type: Mapped[JobType] = mapped_column(
        job_type_enum,
        nullable=False,
    )
    implementation_key: Mapped[str] = mapped_column(
        String,
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
    # config is a json field that store the config for the job definition
    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), # set default value to current time when creating a new job definition
        nullable=False,
    )

    def __repr__(self):
        return (
            f"JobDefinition({self.job_def_id}, {self.type}, "
            f"{self.implementation_key}, {self.name})"
        )
