"""Clear placeholder for social integrations that are not implemented."""

from pathlib import Path

from .base import VideoMeta


class UnavailablePlatform:
    platform_name = "unavailable"
    display_name = "Esta plataforma"

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir) / self.platform_name

    def is_logged_in(self) -> bool:
        return False

    async def login_interactive(self) -> None:
        raise NotImplementedError(f"{self.display_name} ainda não tem integração disponível.")

    async def post_video(self, video: VideoMeta) -> dict:
        raise NotImplementedError(f"{self.display_name} ainda não tem integração disponível.")
