from __future__ import annotations

from pathlib import Path

import click

from plotloom.config import load_config
from plotloom.errors import ConfigError
from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd


@click.group("youtube")
def youtube_group() -> None:
    """Upload videos to YouTube as Shorts."""


@youtube_group.command("auth")
@click.pass_context
def auth_command(ctx: click.Context) -> None:
    """Authenticate with YouTube via OAuth2 (opens browser)."""
    config = load_config(ctx.obj.get("config_path"))
    adapter = _adapter(config)
    creds_path = adapter.authenticate()
    emit(
        {
            "ok": True,
            "command": "youtube.auth",
            "credentials_file": str(creds_path),
            "message": f"Credentials saved to {creds_path}",
        },
        as_json=ctx.obj.get("as_json"),
    )


@youtube_group.command("upload")
@click.option("--episode", required=True, help="Episode identifier (e.g. ep001).")
@click.option("--title", required=True, help="Video title. #Shorts is appended automatically if absent.")
@click.option("--description", default="", show_default=False, help="Video description.")
@click.option(
    "--privacy",
    default=None,
    type=click.Choice(["public", "private", "unlisted"]),
    help="Privacy status. Defaults to adapter config default_privacy.",
)
@click.option(
    "--publish-at",
    default=None,
    help="Schedule publish time in RFC3339 UTC (e.g. 2026-05-10T09:00:00Z). Sets privacy to private.",
)
@click.option(
    "--file",
    "video_file",
    default="final.mp4",
    show_default=True,
    help="Video filename relative to episodes/{episode}/.",
)
@click.pass_context
def upload_command(
    ctx: click.Context,
    episode: str,
    title: str,
    description: str,
    privacy: str | None,
    publish_at: str | None,
    video_file: str,
) -> None:
    """Upload an episode video to YouTube as a Short."""
    repo = _repo_path(ctx)
    config = load_config(ctx.obj.get("config_path"))

    if privacy is None:
        privacy = config.adapter_value("youtube-shorts", "default_privacy", "public")

    video_path = repo / "episodes" / episode / video_file
    if not video_path.exists():
        raise ConfigError(
            f"Video file not found: {video_path}",
            next_step=f"Run 'plotloom stitch' to produce {video_file} for episode {episode}.",
        )

    if ctx.obj.get("dry_run"):
        emit(
            {
                "ok": True,
                "command": "youtube.upload",
                "dry_run": True,
                "video_path": str(video_path),
                "title": title,
                "privacy": privacy,
                "message": f"[dry-run] would upload {video_path} to YouTube as a Short",
            },
            as_json=ctx.obj.get("as_json"),
        )
        return

    adapter = _adapter(config)
    result = adapter.upload(
        video_path=video_path,
        title=title,
        description=description,
        privacy_status=privacy,
        publish_at=publish_at,
    )

    receipt_path = _write_receipt(repo, episode, video_file, result, publish_at)

    emit(
        {
            "ok": True,
            "command": "youtube.upload",
            "video_id": result.video_id,
            "url": result.url,
            "title": result.title,
            "privacy_status": result.privacy_status,
            "uploaded_at": result.uploaded_at,
            "receipt": str(receipt_path),
            "message": f"Uploaded: {result.url}",
        },
        as_json=ctx.obj.get("as_json"),
    )


def _write_receipt(
    repo: Path,
    episode: str,
    source_file: str,
    result,
    publish_at: str | None,
) -> Path:
    import tomli_w

    receipt_dir = repo / "episodes" / episode / "deliveries" / "youtube"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    safe_ts = result.uploaded_at.replace(":", "-")
    receipt_path = receipt_dir / f"{safe_ts}.toml"

    data = {
        "video_id": result.video_id,
        "url": result.url,
        "title": result.title,
        "privacy_status": result.privacy_status,
        "uploaded_at": result.uploaded_at,
        "publish_at": publish_at or "",
        "source_file": f"episodes/{episode}/{source_file}",
    }
    receipt_path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return receipt_path


def _adapter(config):
    from plotloom.adapters.youtube_shorts import YouTubeShortsAdapter

    client_secrets = config.adapter_value(
        "youtube-shorts",
        "client_secrets_file",
        "~/.plotloom/youtube-client-secrets.json",
    )
    credentials = config.adapter_value(
        "youtube-shorts",
        "credentials_file",
        "~/.plotloom/youtube-credentials.json",
    )
    return YouTubeShortsAdapter(client_secrets, credentials)


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo
