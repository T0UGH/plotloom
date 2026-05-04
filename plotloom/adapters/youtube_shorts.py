from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from plotloom.errors import ConfigError, ProviderError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
_SHORTS_TAG = "#Shorts"
_INSTALL_HINT = "Install YouTube dependencies with: uv sync --extra youtube"


@dataclass(frozen=True)
class YouTubeShortsUploadResult:
    video_id: str
    url: str
    title: str
    privacy_status: str
    uploaded_at: str


class YouTubeShortsAdapter:
    name = "youtube-shorts"
    provider = "youtube"

    def __init__(self, client_secrets_file: str | Path, credentials_file: str | Path) -> None:
        self.client_secrets_file = Path(client_secrets_file).expanduser()
        self.credentials_file = Path(credentials_file).expanduser()

    def authenticate(self) -> Path:
        """Run OAuth2 browser flow and persist credentials. Returns credentials file path."""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise ConfigError(_INSTALL_HINT) from exc

        if not self.client_secrets_file.exists():
            raise ConfigError(
                f"YouTube client secrets file not found: {self.client_secrets_file}",
                next_step=(
                    "Download OAuth 2.0 client credentials from Google Cloud Console "
                    f"and save to {self.client_secrets_file}"
                ),
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secrets_file), SCOPES)
        creds = flow.run_local_server(port=0)

        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
        self.credentials_file.write_text(
            json.dumps({
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes or SCOPES),
            }),
            encoding="utf-8",
        )
        self.credentials_file.chmod(0o600)
        return self.credentials_file

    def _build_client(self):
        try:
            import google.oauth2.credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ConfigError(_INSTALL_HINT) from exc

        if not self.credentials_file.exists():
            raise ConfigError(
                f"YouTube credentials not found: {self.credentials_file}",
                next_step="Run 'plotloom youtube auth' to authenticate with YouTube.",
            )

        raw = json.loads(self.credentials_file.read_text(encoding="utf-8"))
        creds = google.oauth2.credentials.Credentials(
            token=raw.get("token"),
            refresh_token=raw.get("refresh_token"),
            token_uri=raw.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=raw.get("client_id"),
            client_secret=raw.get("client_secret"),
            scopes=raw.get("scopes", SCOPES),
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            raw["token"] = creds.token
            self.credentials_file.write_text(json.dumps(raw), encoding="utf-8")

        return build("youtube", "v3", credentials=creds)

    def upload(
        self,
        video_path: Path,
        title: str,
        description: str = "",
        privacy_status: str = "public",
        publish_at: str | None = None,
    ) -> YouTubeShortsUploadResult:
        try:
            from googleapiclient.errors import HttpError
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise ConfigError(_INSTALL_HINT) from exc

        if _SHORTS_TAG.lower() not in title.lower():
            title = f"{title} {_SHORTS_TAG}"

        status: dict = {"privacyStatus": privacy_status}
        if publish_at:
            status["privacyStatus"] = "private"
            status["publishAt"] = publish_at

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "22",
            },
            "status": status,
        }

        youtube = self._build_client()
        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

        try:
            response = (
                youtube.videos()
                .insert(part="snippet,status", body=body, media_body=media)
                .execute()
            )
        except HttpError as exc:
            raise ProviderError(
                f"YouTube upload failed ({exc.status_code}): {exc.reason}",
                next_step="Check your internet connection and YouTube API quota.",
            ) from exc

        video_id = response["id"]
        uploaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return YouTubeShortsUploadResult(
            video_id=video_id,
            url=f"https://www.youtube.com/shorts/{video_id}",
            title=title,
            privacy_status=status["privacyStatus"],
            uploaded_at=uploaded_at,
        )
