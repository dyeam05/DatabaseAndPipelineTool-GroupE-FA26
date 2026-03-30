from datetime import datetime

from pydantic import BaseModel, ConfigDict

from db.enums import SegmentStatus


class CreateSegmentRequest(BaseModel):
    route_id: str
    segment_id: int
    start_time: datetime
    end_time: datetime
    status: SegmentStatus = SegmentStatus.DOWNLOAD_QUEUE


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    segment_id: int
    start_time: datetime
    end_time: datetime
    status: SegmentStatus
    created_at: datetime