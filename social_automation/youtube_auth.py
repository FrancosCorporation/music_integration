"""Run Google's installed-app OAuth flow on a host with a browser."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

from .modules.youtube import YouTubePlatform


def main() -> int:
    root = Path(__file__).parent
    load_dotenv(root.parent / ".env")
    session_dir = Path(os.environ.get("SESSION_DIR", root.parent / "sessions")).expanduser().resolve()
    youtube = YouTubePlatform(session_dir)
    if not youtube.client_secret_file.is_file():
        raise SystemExit(
            "Arquivo OAuth ausente: "
            f"{youtube.client_secret_file}. Baixe o client_secret.json de um OAuth Client ID "
            "do tipo aplicativo para computador no Google Cloud."
        )
    flow = InstalledAppFlow.from_client_secrets_file(
        str(youtube.client_secret_file), YouTubePlatform.SCOPES
    )
    youtube.credentials = flow.run_local_server(host="127.0.0.1", port=0, open_browser=True)
    youtube.save_credentials()
    print(f"Conta conectada. Token salvo em {youtube.token_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
