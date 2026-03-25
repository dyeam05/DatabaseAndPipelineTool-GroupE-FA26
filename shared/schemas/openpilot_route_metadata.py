from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, model_validator


class OpenPilotRouteMetadata(BaseModel):
    """Schema for route metadata returned by the openpilot route endpoint."""

    model_config = ConfigDict(extra="forbid")

    car_id: int
    create_time: int
    distance: float
    dongle_id: str
    end_lat: float
    end_lng: float
    end_time: datetime
    end_time_utc_millis: int
    fullname: str
    git_branch: str
    git_commit: str
    git_commit_date: datetime
    git_dirty: bool
    git_remote: str
    id: int
    is_preserved: bool
    is_public: bool
    make: str
    maxqlog: int
    platform: str
    procqlog: int
    segment_end_times: list[int]
    segment_numbers: list[int]
    segment_start_times: list[int]
    share_exp: str
    share_sig: str
    start_lat: float
    start_lng: float
    start_time: datetime
    start_time_utc_millis: int
    url: HttpUrl
    user_id: str
    version: str
    version_id: int
    vin: str

    @model_validator(mode="after")
    def validate_segment_lengths(self) -> "OpenPilotRouteMetadata":
        # Segment numbers, start times, and end times should map one-to-one.
        if not (
            len(self.segment_numbers)
            == len(self.segment_start_times)
            == len(self.segment_end_times)
        ):
            raise ValueError(
                "segment_numbers, segment_start_times, and segment_end_times must have equal lengths"
            )

        return self
