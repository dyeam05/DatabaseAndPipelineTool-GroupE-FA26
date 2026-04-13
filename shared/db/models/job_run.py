from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import CameraType, JobStatus, job_status_enum, camera_type_enum

# this tell job status, like queued, running, succeeded, failed or cancelled


class JobRun(Base):
    __tablename__ = "job_runs"

    job_run_num: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    # job def link to job run, one job def can have many job runs, but one job run only link to one job def
    job_def_id: Mapped[int] = mapped_column(
        ForeignKey("job_definitions.job_def_id", ondelete="CASCADE"),
        primary_key=True,
    )
    route_id: Mapped[str] = mapped_column(
        ForeignKey("routes.route_id", ondelete="CASCADE"),
        primary_key=True,
    )

    camera: Mapped[CameraType] = mapped_column(
        camera_type_enum,
        primary_key=True
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
        return f"JobRun({self.job_run_num}, {self.job_def_id}, {self.route_id}, {self.status})"
