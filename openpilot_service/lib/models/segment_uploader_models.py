from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import time

@dataclass
class SegmentUploaderJob:
    id: str
    segment_path: Path 
    created_at: float = field(default_factory=time.time)