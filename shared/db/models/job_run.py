from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, String, DateTime, func, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import JobStatus, job_status_enum

# this tell job status, like queued, running, succeeded, failed or cancelled


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
        job_status_enum,
        nullable=False,
    )
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # set time
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # set time when job run is either succeeded, failed, or cancelled
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    # stats stuff. might change later
    stats: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    def __repr__(self):
        return f"{self.job_run_id}, {self.job_def_id}, {self.route_id}, {self.status}"
