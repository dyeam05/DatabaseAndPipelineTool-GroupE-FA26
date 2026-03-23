from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, Enum, Integer, DateTime, func, ForeignKeyConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class CameraType(StrEnum):
    FRONT_REGULAR = "front_regular"
    FRONT_WIDE = "front_wide"
    DRIVER = "driver"


class Frame(Base):
    __tablename__ = "frames"

    __table_args__ = (
        ForeignKeyConstraint(
            ["route_id", "segment_id"],
            ["segments.route_id", "segments.segment_id"],
            ondelete="CASCADE",
        ),
    )

    frame_pk: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    route_id: Mapped[str] = mapped_column(
        nullable=False,
    )
    segment_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    frame_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    camera: Mapped[CameraType] = mapped_column(
        Enum(
            CameraType,
            name="camera_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    log_mono_time: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    openpilot_features: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    width_px: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    height_px: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"{self.frame_pk}, {self.route_id}, {self.segment_id}, {self.frame_id}"