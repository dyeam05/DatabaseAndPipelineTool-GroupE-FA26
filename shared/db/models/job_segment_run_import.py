from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, String, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
from db.enums import JobSegmentRunImportStatus

class JobSegmentRunImport(Base):
    __tablename__ = "job_segment_run_review"
    __table_args__ = (
        ForeignKeyConstraint(
            ["job_run_num", "route_id", "job_def_id", "segment_id"],
            ["job_segment_run.job_run_num", "job_segment_run.route_id", "job_segment_run.job_def_id", "job_segment_run.segment_id"],
            ondelete="CASCADE",
        ),
    )

    # primary keys
    job_run_num: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    route_id: Mapped[str] = mapped_column(
        primary_key=True,
    )

    job_def_id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    segment_id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    status: Mapped[JobSegmentRunImportStatus] = mapped_column(
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    task_id: Mapped[int | None] = mapped_column(
        nullable=True
    )

    task_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    def __repr__(self):
        return f"JobSegmentRunReview({self.job_run_num=}, {self.route_id=}, {self.job_def_id=}, {self.segment_id=}, {self.status=}, {self.task_id=})"

