from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, String, DateTime, func, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

# this tell job status, like queued, running, succeeded, failed or cancelled
class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRun(Base):
    __tablename__ = "job_runs"

    job_run_id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    # job def link to job run, one job def can have many job runs, but one job run only link to one job def
    job_def_id: Mapped[int] = mapped_column(
        ForeignKey("job_definitions.job_def_id"),
        nullable=False,
    )
    route_id: Mapped[str] = mapped_column(
        ForeignKey("routes.route_id"),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    stats: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    def __repr__(self):
        return f"{self.job_run_id}, {self.job_def_id}, {self.route_id}, {self.status}"