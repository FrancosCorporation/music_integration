# youtube.py
from .base import SocialPlatform, VideoMeta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path
import json

class YouTubePlatform:
    platform_name = "youtube"
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir) / "youtube"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.session_dir / "token.json"
        self.client_secret_file = self.session_dir.parent / "client_secret.json"
        self.credentials = None
        self._load_credentials()

    def _load_credentials(self):
        token_file = self.session_dir / "token.json"
        if token_file.exists():
            import google.oauth2.credentials
            self.credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

    def _save_credentials(self):
        token_file = self.session_dir / "token.json"
        token_file.write_text(self.credentials.to_json())

    def is_logged_in(self) -> bool:
        return self.credentials is not None and self.credentials.valid

    async def login_interactive(self):
        if not self.client_secret_file.exists():
            raise FileNotFoundError("client_secret.json not found in sessions/")
        flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secret_file), self.SCOPES)
        self.credentials = flow.run_local_server(port=0)
        self._save_credentials()

    def _get_service(self):
        if not self.credentials or not self.credentials.valid:
            raise RuntimeError("Not authenticated")
        return build("youtube", "v3", credentials=self.credentials)

    async def post_video(self, video_meta) -> dict:
        service = self._get_service()
        body = {
            "snippet": {
                "title": video_meta.title,
                "description": video_meta.description,
                "tags": video_meta.tags or [],
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        }
        media = MediaFileUpload(str(video_meta.file_path), chunksize=-1, resumable=True, mimetype="video/mp4")
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        return {"status": "posted", "video_id": response.get("id")}
