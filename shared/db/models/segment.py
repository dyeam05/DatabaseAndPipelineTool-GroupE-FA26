from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.models.route import RouteStatus

class Segment(Base):
    __tablename__ = "segments"

    __table_args__ = (
        CheckConstraint("segment_id >= 0", name="ck_segments_segment_id_non_negative"),
    )

    route_id: Mapped[str] = mapped_column(
        ForeignKey("routes.route_id"),
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
    status: Mapped[RouteStatus] = mapped_column(
        Enum(
            RouteStatus,
            name="route_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    segment_meta: Mapped[dict | None] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"{self.route_id}, {self.segment_id}, {self.status}"