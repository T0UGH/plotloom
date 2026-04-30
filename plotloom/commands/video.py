from __future__ import annotations

import tomllib
from pathlib import Path

import click

from plotloom.output import emit
from plotloom.paths import next_candidate_path
from plotloom.prompts import compile_prompt
from plotloom.repo import find_repo_from_cwd
from plotloom.video.adapters.mock import MockVideoAdapter
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
    video_adapter = _adapter(adapter)
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

    status = _adapter(current_adapter).poll(provider_task_id, download_dir=clip_dir)
    emit(
        {
            "ok": status.status not in {"failed", "error"},
            "command": "video.poll",
            "adapter": current_adapter,
            "provider_task_id": provider_task_id,
            "status": status.status,
            "message": f"video task {provider_task_id}: {status.status}",
        },
        as_json=ctx.obj.get("as_json"),
    )


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo


def _adapter(name: str):
    if name == "mock":
        return MockVideoAdapter()
    raise click.ClickException(f"unsupported video adapter for submit shell: {name}")


def _read_latest(path: Path) -> dict[str, str]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise click.ClickException(f"could not parse latest task pointer: {path}") from error
