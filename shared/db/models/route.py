from enum import StrEnum
from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class RouteStatus(StrEnum):
    PENDING = "pending"
    INGESTING = "ingesting"
    COMPLETE = "complete"
    FAILED = "failed"


class Route(Base):
    __tablename__ = "routes"

    __table_args__ = (
        CheckConstraint("route_id <> ''", name="ck_routes_route_id_not_empty"),
    )

    route_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )
    file_path: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"{self.route_id}, {self.file_path}, {self.status}"
