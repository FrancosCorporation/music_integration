# base.py
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class VideoMeta:
    file_path: Path
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
