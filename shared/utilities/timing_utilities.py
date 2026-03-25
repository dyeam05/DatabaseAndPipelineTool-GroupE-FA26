from datetime import datetime, timezone

def convert_milliseconds_to_timestamp(milliseconds: int) -> datetime:
    return datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc)