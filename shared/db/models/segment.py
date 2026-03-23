from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Enum, Integer, String, DateTime, func, ForeignKey, JSON 
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
# this role tell segment for which stage belong to, like downloading or uploading
class SegmenStatus(StrEnum):
    DOWNLOAD_QUEUE = "download queue"
    DOWNLOADING = "downloading"
    UPLOAD_QUEUE = "upload queue"
    UPLOADING = "uploading"
    FAILED = "failed"


class Segment(Base):
    __tablename__ = "segments"
# this check constraint is used to ensure segment_id is non-negative
#  it should start from 0
    __table_args__ = (
        CheckConstraint("segment_id >= 0", name="ck_segments_segment_id_non_negative"),
    )

    route_id: Mapped[str] = mapped_column(
        ForeignKey("routes.route_id", ondelete="CASCADE"),
        primary_key=True,
    )
    segment_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[SegmenStatus] = mapped_column(
        Enum(
            SegmenStatus,
            name="segment_status",
            native_enum=True,
            validate_strings=True,
        ),
        #nullable=False means every segment must have a status, it cannot be nulls
        nullable=False,
    )
    segment_meta: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"{self.route_id}, {self.segment_id}, {self.status}"