"""Tests for YouTube Shorts upload adapter and CLI commands."""
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Inject stub google/googleapiclient modules so tests run without the SDK
# ---------------------------------------------------------------------------

def _inject_google_stubs() -> None:
    google = ModuleType("google")
    google.oauth2 = ModuleType("google.oauth2")  # type: ignore[attr-defined]
    google.oauth2.credentials = ModuleType("google.oauth2.credentials")  # type: ignore[attr-defined]
    google.auth = ModuleType("google.auth")  # type: ignore[attr-defined]
    google.auth.transport = ModuleType("google.auth.transport")  # type: ignore[attr-defined]
    google.auth.transport.requests = ModuleType("google.auth.transport.requests")  # type: ignore[attr-defined]

    # Credentials class stub
    class _Creds:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.expired = False

        def refresh(self, request):
            pass

    google.oauth2.credentials.Credentials = _Creds  # type: ignore[attr-defined]
    google.auth.transport.requests.Request = object  # type: ignore[attr-defined]

    sys.modules.setdefault("google", google)
    sys.modules.setdefault("google.oauth2", google.oauth2)
    sys.modules.setdefault("google.oauth2.credentials", google.oauth2.credentials)
    sys.modules.setdefault("google.auth", google.auth)
    sys.modules.setdefault("google.auth.transport", google.auth.transport)
    sys.modules.setdefault("google.auth.transport.requests", google.auth.transport.requests)

    googleapiclient = ModuleType("googleapiclient")
    googleapiclient.discovery = ModuleType("googleapiclient.discovery")  # type: ignore[attr-defined]
    googleapiclient.http = ModuleType("googleapiclient.http")  # type: ignore[attr-defined]
    googleapiclient.errors = ModuleType("googleapiclient.errors")  # type: ignore[attr-defined]

    class _HttpError(Exception):
        def __init__(self, status_code=400, reason="bad request"):
            self.status_code = status_code
            self.reason = reason

    googleapiclient.errors.HttpError = _HttpError  # type: ignore[attr-defined]
    googleapiclient.http.MediaFileUpload = MagicMock()  # type: ignore[attr-defined]
    googleapiclient.discovery.build = MagicMock()  # type: ignore[attr-defined]

    sys.modules.setdefault("googleapiclient", googleapiclient)
    sys.modules.setdefault("googleapiclient.discovery", googleapiclient.discovery)
    sys.modules.setdefault("googleapiclient.http", googleapiclient.http)
    sys.modules.setdefault("googleapiclient.errors", googleapiclient.errors)

    google_auth_oauthlib = ModuleType("google_auth_oauthlib")
    google_auth_oauthlib.flow = ModuleType("google_auth_oauthlib.flow")  # type: ignore[attr-defined]
    sys.modules.setdefault("google_auth_oauthlib", google_auth_oauthlib)
    sys.modules.setdefault("google_auth_oauthlib.flow", google_auth_oauthlib.flow)


_inject_google_stubs()

from plotloom.adapters.youtube_shorts import YouTubeShortsAdapter, YouTubeShortsUploadResult  # noqa: E402
from plotloom.errors import ConfigError  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_adapter(tmp_path: Path, *, creds: bool = True) -> YouTubeShortsAdapter:
    secrets = tmp_path / "secrets.json"
    secrets.write_text(json.dumps({"installed": {}}), encoding="utf-8")
    creds_file = tmp_path / "creds.json"
    if creds:
        creds_file.write_text(
            json.dumps({
                "token": "tok",
                "refresh_token": "ref",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "cid",
                "client_secret": "csec",
                "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
            }),
            encoding="utf-8",
        )
    return YouTubeShortsAdapter(secrets, creds_file)


def _mock_youtube_client(video_id: str = "abc123") -> MagicMock:
    client = MagicMock()
    client.videos.return_value.insert.return_value.execute.return_value = {"id": video_id}
    return client


# ---------------------------------------------------------------------------
# Adapter unit tests
# ---------------------------------------------------------------------------

def test_upload_appends_shorts_tag(tmp_path):
    adapter = _make_adapter(tmp_path)
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")

    with patch.object(adapter, "_build_client", return_value=_mock_youtube_client("xyz")):
        result = adapter.upload(video, title="我的短剧第一集")

    assert "#Shorts" in result.title
    assert result.video_id == "xyz"
    assert result.url == "https://www.youtube.com/shorts/xyz"


def test_upload_does_not_duplicate_shorts_tag(tmp_path):
    adapter = _make_adapter(tmp_path)
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")

    with patch.object(adapter, "_build_client", return_value=_mock_youtube_client()):
        result = adapter.upload(video, title="Episode 1 #Shorts")

    assert result.title.count("#Shorts") == 1
    assert result.title.count("#shorts") == 0  # no duplicate in any case


def test_upload_scheduled_sets_private_status(tmp_path):
    adapter = _make_adapter(tmp_path)
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")

    captured_body: dict = {}

    def fake_insert(**kwargs):
        captured_body.update(kwargs.get("body", {}))
        m = MagicMock()
        m.execute.return_value = {"id": "sched1"}
        return m

    client = MagicMock()
    client.videos.return_value.insert.side_effect = fake_insert

    with patch.object(adapter, "_build_client", return_value=client):
        result = adapter.upload(
            video,
            title="Episode",
            privacy_status="public",
            publish_at="2026-05-10T09:00:00Z",
        )

    assert result.privacy_status == "private"
    assert captured_body["status"]["publishAt"] == "2026-05-10T09:00:00Z"
    assert captured_body["status"]["privacyStatus"] == "private"


def test_upload_raises_config_error_when_no_credentials(tmp_path):
    adapter = _make_adapter(tmp_path, creds=False)
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")

    with pytest.raises(ConfigError, match="YouTube credentials not found"):
        adapter.upload(video, title="Test")


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------

from click.testing import CliRunner  # noqa: E402

from plotloom.cli import main  # noqa: E402


def _make_repo(tmp_path: Path, episode: str = "ep001") -> Path:
    repo = tmp_path / "myshow"
    (repo / "episodes" / episode).mkdir(parents=True)
    (repo / "episodes" / episode / "final.mp4").write_bytes(b"fake video")
    (repo / "plotloom.toml").write_text("", encoding="utf-8")
    return repo


def _fake_adapter_upload(video_path, title, description="", privacy_status="public", publish_at=None):
    from datetime import datetime, timezone
    if "#Shorts" not in title and "#shorts" not in title.lower():
        title = f"{title} #Shorts"
    return YouTubeShortsUploadResult(
        video_id="testvid1",
        url="https://www.youtube.com/shorts/testvid1",
        title=title,
        privacy_status=privacy_status,
        uploaded_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def test_youtube_upload_writes_receipt(tmp_path):
    repo = _make_repo(tmp_path)
    runner = CliRunner()

    with patch("plotloom.commands.youtube._adapter") as mock_adapter_factory:
        mock_adapter = MagicMock()
        mock_adapter.upload.side_effect = _fake_adapter_upload
        mock_adapter_factory.return_value = mock_adapter

        result = runner.invoke(
            main,
            ["--repo", str(repo), "--json", "youtube", "upload",
             "--episode", "ep001", "--title", "我的短剧"],
        )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["video_id"] == "testvid1"
    assert "receipt" in data

    receipt_path = Path(data["receipt"])
    assert receipt_path.exists()
    receipt = tomllib.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["video_id"] == "testvid1"
    assert receipt["source_file"] == "episodes/ep001/final.mp4"


def test_youtube_upload_json_includes_url(tmp_path):
    repo = _make_repo(tmp_path)
    runner = CliRunner()

    with patch("plotloom.commands.youtube._adapter") as mock_adapter_factory:
        mock_adapter = MagicMock()
        mock_adapter.upload.side_effect = _fake_adapter_upload
        mock_adapter_factory.return_value = mock_adapter

        result = runner.invoke(
            main,
            ["--repo", str(repo), "--json", "youtube", "upload",
             "--episode", "ep001", "--title", "Test Short"],
        )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["url"].startswith("https://www.youtube.com/shorts/")


def test_youtube_upload_dry_run_skips_adapter(tmp_path):
    repo = _make_repo(tmp_path)
    runner = CliRunner()

    with patch("plotloom.commands.youtube._adapter") as mock_adapter_factory:
        mock_adapter = MagicMock()
        mock_adapter_factory.return_value = mock_adapter

        result = runner.invoke(
            main,
            ["--repo", str(repo), "--dry-run", "--json", "youtube", "upload",
             "--episode", "ep001", "--title", "Test"],
        )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["dry_run"] is True
    mock_adapter.upload.assert_not_called()


def test_youtube_upload_missing_video_raises_error(tmp_path):
    repo = tmp_path / "myshow"
    (repo / "episodes" / "ep001").mkdir(parents=True)
    (repo / "plotloom.toml").write_text("", encoding="utf-8")
    runner = CliRunner()

    with patch("plotloom.commands.youtube._adapter"):
        result = runner.invoke(
            main,
            ["--repo", str(repo), "--json", "youtube", "upload",
             "--episode", "ep001", "--title", "Test"],
        )

    assert result.exit_code != 0
    data = json.loads(result.output)
    assert data["ok"] is False


def test_youtube_upload_help(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["youtube", "upload", "--help"])
    assert result.exit_code == 0
    assert "--episode" in result.output
    assert "--title" in result.output
    assert "--publish-at" in result.output
