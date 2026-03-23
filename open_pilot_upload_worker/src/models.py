from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SegmentDir:
    path: Path
    segment_num: int
