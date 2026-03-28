from uuid import UUID

from sqlalchemy import Enum, ForeignKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import JobSegmentRunStatus, job_segment_run_enum

class JobSegmentRun(Base):
    __tablename__ = "job_segment_run"

    __table_args__ = (
        ForeignKeyConstraint(
            ["job_run_num", "route_id", "job_def_id"],
            ["job_runs.job_run_num", "job_runs.route_id", "job_runs.job_def_id"],
            ondelete="CASCADE",
        ),
    )

    #primary keys
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
    
    # segment info
    status: Mapped[JobSegmentRunStatus] = mapped_column(
        job_segment_run_enum,
        nullable=False,
    )
    
    artifact_id: Mapped[UUID] | None = mapped_column(
        ForeignKey("artifacts.artifact_id"),
        nullable=True
    )
