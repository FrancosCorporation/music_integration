# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import json
import os

@dataclass
class VideoMeta:
    file_path: Path
    title: str
    description: str = ""
    tags: list = None

class SocialPlatform(ABC):
    platform_name: str = "base"

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir) / self.platform_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / "session.json"
        self.cookies = self._load_session()

    def _load_session(self):
        if self.session_file.exists():
            try:
                return json.loads(self.session_file.read_text())
            except Exception:
                return {}
        return {}

    def _save_session(self, cookies):
        self.session_file.write_text(json.dumps(cookies))

    @abstractmethod
    async def login_interactive(self):
        """Open browser for manual login and save session."""
        pass

    @abstractmethod
    async def post_video(self, video: VideoMeta) -> dict:
        """Post video, return dict with status, message."""
        pass

    def is_logged_in(self) -> bool:
        return bool(self.cookies)
