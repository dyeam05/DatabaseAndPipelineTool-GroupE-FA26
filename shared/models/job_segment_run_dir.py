from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class JobSegmentRunDir:
    image_paths: list[Path]
    annotation_path: Path


