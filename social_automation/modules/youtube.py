"""YouTube Data API client and locally stored OAuth credentials."""

import json
import mimetypes
import os
from pathlib import Path
import tempfile

from .base import VideoMeta


class YouTubePlatform:
    platform_name = "youtube"
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    PRIVACY_OPTIONS = {"private", "unlisted", "public"}

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir).expanduser().resolve() / self.platform_name
        self.session_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.session_dir, 0o700)
        except OSError:
            pass
        self.token_file = self.session_dir / "token.json"
        self.client_secret_file = self.session_dir / "client_secret.json"
        self.credentials = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        if not self.token_file.is_file():
            return
        try:
            from google.oauth2.credentials import Credentials

            self.credentials = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)
        except (OSError, ValueError, json.JSONDecodeError):
            self.credentials = None

    def save_credentials(self) -> None:
        if self.credentials is None:
            raise RuntimeError("Não há credenciais OAuth para salvar.")
        self.session_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.session_dir, prefix=".token-", delete=False
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                os.chmod(temporary_path, 0o600)
                temporary_file.write(self.credentials.to_json())
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            temporary_path.replace(self.token_file)
            os.chmod(self.token_file, 0o600)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def is_logged_in(self) -> bool:
        return bool(
            self.credentials
            and (self.credentials.valid or (self.credentials.expired and self.credentials.refresh_token))
        )

    def _get_service(self):
        if self.credentials is None:
            raise RuntimeError("Conta do YouTube não conectada.")
        if self.credentials.expired:
            if not self.credentials.refresh_token:
                raise RuntimeError("A credencial expirou. Conecte novamente a conta do YouTube.")
            from google.auth.transport.requests import Request

            self.credentials.refresh(Request())
            self.save_credentials()
        if not self.credentials.valid:
            raise RuntimeError("Credencial do YouTube inválida. Conecte novamente a conta.")
        from googleapiclient.discovery import build

        return build("youtube", "v3", credentials=self.credentials, cache_discovery=False)

    async def post_video(self, video_meta: VideoMeta, privacy: str = "private") -> dict:
        if privacy not in self.PRIVACY_OPTIONS:
            raise ValueError("Opção de privacidade do YouTube inválida.")
        file_path = Path(video_meta.file_path).expanduser().resolve()
        if not file_path.is_file() or file_path.stat().st_size == 0:
            raise ValueError("Arquivo de vídeo não encontrado ou vazio.")
        title = video_meta.title.strip()
        description = video_meta.description.strip()
        if not title or len(title) > 100:
            raise ValueError("O título deve ter entre 1 e 100 caracteres.")
        if len(description) > 5000:
            raise ValueError("A descrição ultrapassa 5.000 caracteres.")
        tags = [tag.strip() for tag in (video_meta.tags or []) if tag.strip()]
        if any(len(tag) > 500 for tag in tags):
            raise ValueError("Uma tag ultrapassa 500 caracteres.")

        from googleapiclient.http import MediaFileUpload

        mime_type = mimetypes.guess_type(file_path.name)[0] or "video/*"
        service = self._get_service()
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22",
            },
            "status": {"privacyStatus": privacy},
        }
        media = MediaFileUpload(str(file_path), chunksize=8 * 1024 * 1024, resumable=True, mimetype=mime_type)
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        video_id = response.get("id")
        if not video_id:
            raise RuntimeError("A API do YouTube não retornou o identificador do vídeo.")
        return {"status": "posted", "video_id": video_id}
