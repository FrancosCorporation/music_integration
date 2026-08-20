# linkedin.py
from .base import SocialPlatform, VideoMeta
from pathlib import Path

class LinkedInPlatform:
    platform_name = "linkedin"

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir) / "linkedin"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.session_dir / "token.json"
        self._load_token()

    def _load_token(self):
        if self.token_file.exists():
            import json
            self.access_token = json.loads(self.token_file.read_text()).get("access_token")
        else:
            self.access_token = None

    def _save_token(self, token):
        import json
        self.token_file.write_text(json.dumps({"access_token": token}))
        self.access_token = token

    def is_logged_in(self) -> bool:
        return bool(self.access_token)

    async def login_interactive(self):
        raise NotImplementedError("Implement OAuth for LinkedIn")

    async def post_video(self, video: VideoMeta) -> dict:
        raise NotImplementedError("Implement LinkedIn video upload")
