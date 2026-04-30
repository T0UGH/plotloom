from __future__ import annotations

import tomllib
from pathlib import Path

import click

from plotloom.config import load_config
from plotloom.errors import MediaValidationError
from plotloom.media import probe_media
from plotloom.output import emit
from plotloom.paths import next_candidate_path
from plotloom.prompts import compile_prompt
from plotloom.repo import find_repo_from_cwd
from plotloom.video.adapters.dreamina_cli import DreaminaCliAdapter
from plotloom.video.adapters.mock import MockVideoAdapter
from plotloom.video.adapters.volcengine_seedance import VolcEngineSeedanceAdapter
from plotloom.video.compare import compare_receipts
from plotloom.video.downloads import download_url
from plotloom.video.receipts import Receipt, receipt_path, write_latest_pointer, write_receipt
from plotloom.video.types import PlotloomVideoRequest, VideoMode

VIDEO_PROMPTS = "video-prompts-en.md"
VIDEO_MODES = ["text-to-video", "image-to-video", "reference-to-video"]


@click.group("video")
def video_group() -> None:
    """Submit and poll video generation tasks."""


@video_group.command("submit")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--adapter", default="mock", show_default=True)
@click.option("--mode", default="text-to-video", show_default=True, type=click.Choice(VIDEO_MODES))
@click.option("--duration", default=5, show_default=True, type=int)
@click.option("--ratio", default="9:16", show_default=True)
@click.option("--resolution", default="720p", show_default=True)
@click.pass_context
def submit_command(
    ctx: click.Context,
    episode: str,
    clip: str,
    adapter: str,
    mode: str,
    duration: int,
    ratio: str,
    resolution: str,
) -> None:
    repo = _repo_path(ctx)
    prompt_file = repo / "episodes" / episode / VIDEO_PROMPTS
    prompt_text = prompt_file.read_text(encoding="utf-8")
    compiled = compile_prompt(prompt_text, clip, adapter=adapter, mode=mode)
    video_adapter = _adapter(ctx, adapter)
    request = PlotloomVideoRequest(
        repo=repo,
        episode=episode,
        clip=clip,
        adapter=adapter,
        mode=VideoMode(mode),
        prompt_file=prompt_file.relative_to(repo),
        prompt_text=compiled.prompt_text,
        ratio=ratio,
        resolution=resolution,
        duration=duration,
    )
    validation = video_adapter.validate_request(request)
    if not validation.ok:
        messages = "; ".join(issue.message for issue in validation.issues if issue.level == "error")
        raise click.ClickException(messages)

    clip_dir = repo / "episodes" / episode / "videos" / clip
    candidate_path = next_candidate_path(clip_dir / "candidates", ".mp4", adapter=adapter)
    result = video_adapter.submit(request, candidate_path=candidate_path)
    task_path = receipt_path(repo, episode, clip, adapter, result.provider_task_id)
    receipt = Receipt(
        adapter=adapter,
        provider=result.provider,
        provider_task_id=result.provider_task_id,
        status=result.status,
        repo=str(repo),
        episode=episode,
        clip=clip,
        mode=mode,
        prompt_file=str(request.prompt_file),
        compiled_prompt_sha256=compiled.prompt_sha256,
        prompt_chars=compiled.prompt_chars,
        duration=duration,
        ratio=ratio,
        resolution=resolution,
        audio_intent=request.audio_intent,
        credential_source="mock" if adapter == "mock" else "config",
        candidate_path=str(candidate_path.relative_to(repo)) if result.local_path else None,
        provider_data=result.raw,
    )
    write_receipt(task_path, receipt)
    write_latest_pointer(task_path, receipt)
    emit(
        {
            "ok": True,
            "command": "video.submit",
            "adapter": adapter,
            "provider_task_id": result.provider_task_id,
            "receipt_path": str(task_path),
            "candidate_path": str(candidate_path),
            "message": f"video task submitted: {result.provider_task_id}",
        },
        as_json=ctx.obj.get("as_json"),
    )


@video_group.command("poll")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--adapter")
@click.option("--task-id")
@click.pass_context
def poll_command(ctx: click.Context, episode: str, clip: str, adapter: str | None, task_id: str | None) -> None:
    repo = _repo_path(ctx)
    clip_dir = repo / "episodes" / episode / "videos" / clip
    latest = clip_dir / "latest-task.toml"
    latest_data = _read_latest(latest) if latest.exists() else {}
    current_adapter = adapter or latest_data.get("adapter")
    provider_task_id = task_id or latest_data.get("provider_task_id")
    if not current_adapter or not provider_task_id:
        raise click.ClickException("--adapter and --task-id are required when latest-task.toml is missing")

    task_path = _task_path(repo, clip_dir, latest_data, current_adapter, provider_task_id)
    receipt_data = _read_toml(task_path) if task_path.exists() else {}
    status = _adapter(ctx, current_adapter).poll(provider_task_id, download_dir=clip_dir)
    candidate_path = _candidate_from_receipt(repo, receipt_data)
    media: dict[str, object] = {}
    if status.video_url:
        candidate_path = next_candidate_path(clip_dir / "candidates", ".mp4", adapter=current_adapter)
        download_url(status.video_url, candidate_path)
    if candidate_path and candidate_path.exists():
        try:
            media = probe_media(candidate_path).to_dict()
        except MediaValidationError as error:
            media = {"probe_error": error.message}
    updated = _updated_receipt(
        repo=repo,
        episode=episode,
        clip=clip,
        adapter=current_adapter,
        provider_task_id=provider_task_id,
        status=status.status,
        receipt_data=receipt_data,
        candidate_path=candidate_path,
        media=media,
        provider_data=status.raw,
        error_code=status.error_code,
        error_message=status.error_message,
    )
    write_receipt(task_path, updated)
    write_latest_pointer(task_path, updated)
    emit(
        {
            "ok": status.status not in {"failed", "error"},
            "command": "video.poll",
            "adapter": current_adapter,
            "provider_task_id": provider_task_id,
            "status": status.status,
            "receipt_path": str(task_path),
            "candidate_path": str(candidate_path) if candidate_path else None,
            "message": f"video task {provider_task_id}: {status.status}",
        },
        as_json=ctx.obj.get("as_json"),
    )


@video_group.command("compare")
@click.option("--episode", required=True)
@click.option("--clip")
@click.pass_context
def compare_command(ctx: click.Context, episode: str, clip: str | None) -> None:
    repo = _repo_path(ctx)
    videos_dir = repo / "episodes" / episode / "videos"
    if clip:
        receipts = sorted((videos_dir / clip / "tasks").glob("*.toml"))
    else:
        receipts = sorted(videos_dir.glob("*/tasks/*.toml"))
    rows = compare_receipts(receipts)
    message = "\n".join(f"{row['adapter']}\t{row['status']}\t{row.get('candidate_path') or ''}" for row in rows)
    emit(
        {
            "ok": True,
            "command": "video.compare",
            "episode": episode,
            "clip": clip,
            "rows": rows,
            "message": message or "no receipts found",
        },
        as_json=ctx.obj.get("as_json"),
    )


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo


def _adapter(ctx: click.Context, name: str):
    if name == "mock":
        return MockVideoAdapter()
    if name == "dreamina-cli":
        cfg = load_config(ctx.obj.get("config_path"))
        return DreaminaCliAdapter(
            binary=cfg.adapter_value("dreamina-cli", "binary", "dreamina"),
            home=cfg.adapter_value("dreamina-cli", "home", "~"),
        )
    if name == "volcengine-seedance":
        cfg = load_config(ctx.obj.get("config_path"))
        return VolcEngineSeedanceAdapter(
            ark_api_key=cfg.adapter_value("volcengine-seedance", "ark_api_key", ""),
            base_url=cfg.adapter_value("volcengine-seedance", "base_url", "https://ark.cn-beijing.volces.com/api/v3"),
            model=cfg.adapter_value("volcengine-seedance", "model", "doubao-seedance-2-0-260128"),
        )
    raise click.ClickException(f"unsupported video adapter for submit shell: {name}")


def _read_latest(path: Path) -> dict[str, str]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise click.ClickException(f"could not parse latest task pointer: {path}") from error


def _read_toml(path: Path) -> dict[str, object]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise click.ClickException(f"could not parse receipt: {path}") from error


def _task_path(repo: Path, clip_dir: Path, latest_data: dict[str, str], adapter: str, provider_task_id: str) -> Path:
    receipt_value = latest_data.get("receipt")
    if receipt_value:
        return clip_dir / receipt_value
    return receipt_path(repo, clip_dir.parent.parent.name, clip_dir.name, adapter, provider_task_id)


def _candidate_from_receipt(repo: Path, receipt_data: dict[str, object]) -> Path | None:
    candidate = receipt_data.get("candidate_path")
    if not candidate:
        return None
    path = Path(str(candidate))
    return path if path.is_absolute() else repo / path


def _updated_receipt(
    *,
    repo: Path,
    episode: str,
    clip: str,
    adapter: str,
    provider_task_id: str,
    status: str,
    receipt_data: dict[str, object],
    candidate_path: Path | None,
    media: dict[str, object],
    provider_data: dict[str, object],
    error_code: str | None,
    error_message: str | None,
) -> Receipt:
    return Receipt(
        adapter=adapter,
        provider=str(receipt_data.get("provider") or _provider_for(adapter)),
        provider_task_id=provider_task_id,
        status=status,
        repo=str(receipt_data.get("repo") or repo),
        episode=str(receipt_data.get("episode") or episode),
        clip=str(receipt_data.get("clip") or clip),
        mode=str(receipt_data.get("mode") or "text-to-video"),
        prompt_file=str(receipt_data.get("prompt_file") or ""),
        compiled_prompt_sha256=str(receipt_data.get("compiled_prompt_sha256") or ""),
        prompt_chars=int(receipt_data.get("prompt_chars") or 0),
        duration=int(receipt_data.get("duration") or 0),
        ratio=str(receipt_data.get("ratio") or ""),
        resolution=str(receipt_data.get("resolution") or ""),
        audio_intent=str(receipt_data.get("audio_intent") or "native_if_supported"),
        credential_source=str(receipt_data.get("credential_source") or ("mock" if adapter == "mock" else "config")),
        submitted_at=str(receipt_data.get("submitted_at")) if receipt_data.get("submitted_at") else None,
        candidate_path=str(candidate_path.relative_to(repo)) if candidate_path and candidate_path.is_relative_to(repo) else str(candidate_path) if candidate_path else None,
        error_code=error_code,
        error_message=error_message,
        provider_data=provider_data,
        media=media,
    )


def _provider_for(adapter: str) -> str:
    if adapter == "mock":
        return "local"
    if adapter == "dreamina-cli":
        return "dreamina"
    if adapter == "volcengine-seedance":
        return "volcengine"
    return adapter
