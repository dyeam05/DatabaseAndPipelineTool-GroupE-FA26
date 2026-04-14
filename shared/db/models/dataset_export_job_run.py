from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.enums import CameraType, camera_type_enum


class DatasetExportJobRun(Base):
    __tablename__ = "dataset_export_job_runs"

    __table_args__ = (
        ForeignKeyConstraint(
            ["job_run_num", "route_id", "job_def_id", "camera"],
            ["job_runs.job_run_num", "job_runs.route_id", "job_runs.job_def_id", "job_runs.camera"],
            ondelete="CASCADE",
        ),
    )

    export_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_exports.export_id", ondelete="CASCADE"),
        primary_key=True,
    )
    route_id: Mapped[str] = mapped_column(
        primary_key=True,
    )
    job_def_id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    job_run_num: Mapped[int] = mapped_column(
        primary_key=True,
    )
    camera: Mapped[CameraType] = mapped_column(
        camera_type_enum,
        primary_key=True,
    )

    def __repr__(self):
        return (
            f"DatasetExportJobRun({self.export_id=}, {self.route_id=}, "
            f"{self.job_def_id=}, {self.job_run_num=}, {self.camera=})"
        )
