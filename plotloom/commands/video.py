from __future__ import annotations

import tomllib
import uuid
from dataclasses import replace
from hashlib import sha256
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
from plotloom.video.adapters.base import VideoTaskStatus
from plotloom.video.compare import compare_receipts
from plotloom.video.downloads import download_url
from plotloom.video.face_policy import validate_reference_intent_face_policies
from plotloom.video.failures import classify_failure, is_retryable_code_or_message
from plotloom.video.reference_map import (
    build_reference_map,
    default_reference_map_path,
    format_reference_map,
    read_reference_map,
    references_to_dicts,
    repo_relative_path,
    write_reference_map,
)
from plotloom.video.receipts import Receipt, receipt_path, write_latest_pointer, write_receipt
from plotloom.video.types import PlotloomVideoRequest, VideoMode

VIDEO_PROMPTS = "video-prompts-en.md"
VIDEO_MODES = ["text-to-video", "image-to-video", "reference-to-video"]


@click.group("video")
def video_group() -> None:
    """Submit and poll video generation tasks."""


@video_group.command("plan-references")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--first-frame", type=click.Path(path_type=str), help="Planned first-frame image path.")
@click.option("--last-frame", type=click.Path(path_type=str), help="Planned last-frame image path.")
@click.option(
    "--reference",
    "references",
    multiple=True,
    help='Reference intent, repeatable. Example: --reference "character:ethan=assets/cast/ethan/ref.png"',
)
@click.option("--write", is_flag=True, help="Write episodes/<episode>/videos/<clip>/reference-map.toml.")
@click.pass_context
def plan_references_command(
    ctx: click.Context,
    episode: str,
    clip: str,
    first_frame: str | None,
    last_frame: str | None,
    references: tuple[str, ...],
    write: bool,
) -> None:
    repo = _repo_path(ctx)
    try:
        planned = build_reference_map(repo, first_frame=first_frame, last_frame=last_frame, references=references)
        map_path = default_reference_map_path(repo, episode, clip)
        if write:
            write_reference_map(map_path, repo, planned)
        message = format_reference_map(repo, planned)
    except (FileNotFoundError, ValueError, OSError) as error:
        raise click.ClickException(str(error)) from error
    emit(
        {
            "ok": True,
            "command": "video.plan-references",
            "episode": episode,
            "clip": clip,
            "written": write,
            "path": str(map_path) if write else None,
            "reference_map_path": str(map_path),
            "references": references_to_dicts(repo, planned),
            "message": message,
        },
        as_json=ctx.obj.get("as_json"),
    )


@video_group.command("submit")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--adapter", default="mock", show_default=True)
@click.option("--mode", default="text-to-video", show_default=True, type=click.Choice(VIDEO_MODES))
@click.option("--duration", default=5, show_default=True, type=int)
@click.option("--ratio", default="9:16", show_default=True)
@click.option("--resolution", default="720p", show_default=True)
@click.option("--first-frame", type=click.Path(path_type=str), help="Intent-only first-frame reference path.")
@click.option("--last-frame", type=click.Path(path_type=str), help="Intent-only last-frame reference path.")
@click.option(
    "--reference-image",
    "reference_images",
    multiple=True,
    help='Intent-only reference image, repeatable. Example: --reference-image "character:ethan=assets/cast/ethan/body.png"',
)
@click.option("--reference-map", type=click.Path(path_type=str), help="Read reference intent from a reference-map.toml file.")
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
    first_frame: str | None,
    last_frame: str | None,
    reference_images: tuple[str, ...],
    reference_map: str | None,
) -> None:
    repo = _repo_path(ctx)
    try:
        reference_map_path, reference_intent = _read_reference_intent(
            repo,
            reference_map,
            first_frame=first_frame,
            last_frame=last_frame,
            reference_images=reference_images,
        )
    except (FileNotFoundError, ValueError, OSError) as error:
        raise click.ClickException(str(error)) from error
    prompt_file = repo / "episodes" / episode / VIDEO_PROMPTS
    prompt_text = prompt_file.read_text(encoding="utf-8")
    compiled = compile_prompt(prompt_text, clip, adapter=adapter, mode=mode)
    video_adapter = _adapter(ctx, adapter)
    first_frame_uri, last_frame_uri, reference_image_uris = _reference_uris(reference_intent)
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
        first_frame_uri=first_frame_uri,
        last_frame_uri=last_frame_uri,
        reference_image_uris=reference_image_uris,
    )
    validation = video_adapter.validate_request(request)
    if not validation.ok:
        messages = "; ".join(issue.message for issue in validation.issues if issue.level == "error")
        raise click.ClickException(messages)
    provider_request = _provider_request_with_reference_summary(repo, video_adapter.compile_native_request(request), reference_intent)

    clip_dir = repo / "episodes" / episode / "videos" / clip
    candidate_path = next_candidate_path(clip_dir / "candidates", ".mp4", adapter=adapter)
    try:
        result = video_adapter.submit(request, candidate_path=candidate_path)
    except Exception as error:
        failed_receipt = _failed_submit_receipt(
            repo=repo,
            episode=episode,
            clip=clip,
            adapter=adapter,
            provider=video_adapter.provider,
            mode=mode,
            request=request,
            compiled=compiled,
            duration=duration,
            ratio=ratio,
            resolution=resolution,
            candidate_path=candidate_path,
            reference_map_path=reference_map_path,
            reference_intent=reference_intent,
            provider_request=provider_request,
            error=error,
        )
        task_path = receipt_path(repo, episode, clip, adapter, failed_receipt.provider_task_id)
        write_receipt(task_path, failed_receipt)
        write_latest_pointer(task_path, failed_receipt)
        raise click.ClickException(f"video submit failed: {error}") from error
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
        reference_map_path=repo_relative_path(repo, reference_map_path) if reference_map_path else None,
        reference_intent=references_to_dicts(repo, reference_intent),
        provider_request=provider_request,
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
    try:
        status = _adapter(ctx, current_adapter).poll(provider_task_id, download_dir=clip_dir)
    except Exception as error:
        failure = classify_failure("poll", str(error))
        status = VideoTaskStatus(
            adapter=current_adapter,
            provider_task_id=provider_task_id,
            status="failed",
            error_code=failure.code,
            error_message=str(error),
            failure_category=failure.category,
            failure_stage="poll",
            retryable=failure.retryable,
            raw={"error": str(error)},
        )
    if status.failure_category is None and status.error_message:
        failure = classify_failure("poll", status.error_message)
        status = replace(
            status,
            failure_category=failure.category,
            failure_stage=status.failure_stage or "poll",
            retryable=status.retryable if status.retryable is not None else failure.retryable,
            error_code=status.error_code or failure.code,
        )
    if status.retryable is None and status.error_code is not None:
        status = replace(status, retryable=is_retryable_code_or_message(status.error_code, status.error_message))
    candidate_path = _candidate_from_receipt(repo, receipt_data)
    media: dict[str, object] = {}
    if status.video_url:
        candidate_path = next_candidate_path(clip_dir / "candidates", ".mp4", adapter=current_adapter)
        try:
            download_url(status.video_url, candidate_path)
        except Exception as error:
            failure = classify_failure("download", str(error))
            status = replace(
                status,
                status="failed",
                error_code=failure.code,
                error_message=str(error),
                failure_category=failure.category,
                failure_stage="download",
                retryable=failure.retryable,
            )
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
        failure_category=status.failure_category,
        failure_stage=status.failure_stage,
        retryable=status.retryable,
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
    failure_category: str | None,
    failure_stage: str | None,
    retryable: bool | None,
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
        reference_map_path=str(receipt_data.get("reference_map_path")) if receipt_data.get("reference_map_path") else None,
        reference_intent=list(receipt_data.get("reference_intent") or []),
        provider_request=dict(receipt_data.get("provider_request") or {}),
        error_code=error_code,
        error_message=error_message,
        failure_category=failure_category,
        failure_stage=failure_stage,
        retryable=retryable,
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


def _failed_submit_receipt(
    *,
    repo: Path,
    episode: str,
    clip: str,
    adapter: str,
    provider: str,
    mode: str,
    request: PlotloomVideoRequest,
    compiled,
    duration: int,
    ratio: str,
    resolution: str,
    candidate_path: Path,
    reference_map_path: Path | None,
    reference_intent: list,
    provider_request: dict[str, object],
    error: Exception,
) -> Receipt:
    failure = classify_failure("submit", str(error))
    return Receipt(
        adapter=adapter,
        provider=provider,
        provider_task_id=f"{adapter}-submit-failed-{uuid.uuid4().hex[:8]}",
        status="failed",
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
        candidate_path=str(candidate_path.relative_to(repo)),
        reference_map_path=repo_relative_path(repo, reference_map_path) if reference_map_path else None,
        reference_intent=references_to_dicts(repo, reference_intent),
        provider_request=provider_request,
        error_code=failure.code,
        error_message=str(error),
        failure_category=failure.category,
        failure_stage="submit",
        retryable=failure.retryable,
        provider_data={"error": str(error)},
    )


def _read_reference_intent(
    repo: Path,
    reference_map: str | None,
    *,
    first_frame: str | None = None,
    last_frame: str | None = None,
    reference_images: tuple[str, ...] = (),
):
    has_explicit_refs = bool(first_frame or last_frame or reference_images)
    if reference_map and has_explicit_refs:
        raise ValueError("use either --reference-map or explicit --first-frame/--last-frame/--reference-image options, not both")
    if not reference_map and not has_explicit_refs:
        return None, []
    if has_explicit_refs:
        references = build_reference_map(repo, first_frame=first_frame, last_frame=last_frame, references=reference_images)
        issues = validate_reference_intent_face_policies(repo, references)
        if issues:
            messages = "\n".join(f"{issue.character}: {issue.message} ({issue.path})" for issue in issues)
            raise ValueError("reference intent / face policy validation failed:\n" + messages)
        return None, references
    path = Path(reference_map).expanduser()
    if not path.is_absolute():
        path = repo / path
    resolved = path.resolve()
    references = read_reference_map(resolved, repo)
    issues = validate_reference_intent_face_policies(repo, references)
    if issues:
        messages = "\n".join(f"{issue.character}: {issue.message} ({issue.path})" for issue in issues)
        raise ValueError("reference map / face policy validation failed:\n" + messages)
    return resolved, references


def _provider_request_with_reference_summary(repo: Path, provider_request: dict[str, object], references: list) -> dict[str, object]:
    if not references:
        return provider_request
    data = dict(provider_request)
    data["reference_intent_status"] = _reference_intent_status(provider_request, references)
    data["reference_assets"] = [_reference_asset_summary(repo, reference) for reference in references]
    return data


def _reference_asset_summary(repo: Path, reference) -> dict[str, object]:
    data = {
        "slot": reference.slot,
        "kind": reference.kind,
        "provider_role": _provider_role_for_reference(reference.kind),
        "source": reference.source,
        "character": reference.character,
        "scene": reference.scene,
        "label": reference.label,
    }
    if reference.uri:
        data["uri"] = reference.uri
        return data
    stat = reference.path.stat()
    data["path"] = repo_relative_path(repo, reference.path)
    data["sha256"] = _file_sha256(reference.path)
    data["mtime_ns"] = stat.st_mtime_ns
    return data


def _provider_role_for_reference(kind: str) -> str:
    if kind in {"first_frame", "last_frame"}:
        return kind
    return "reference_image"


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reference_uris(references: list) -> tuple[str | None, str | None, list[str]]:
    first_frame_uri = None
    last_frame_uri = None
    reference_image_uris: list[str] = []
    for reference in references:
        if not reference.uri:
            continue
        if reference.kind == "first_frame":
            first_frame_uri = reference.uri
        elif reference.kind == "last_frame":
            last_frame_uri = reference.uri
        else:
            reference_image_uris.append(reference.uri)
    return first_frame_uri, last_frame_uri, reference_image_uris


def _reference_intent_status(provider_request: dict[str, object], references: list) -> str:
    requested = {reference.uri for reference in references if reference.uri}
    if not requested:
        return "intent_only_not_sent"
    sent = _provider_request_image_urls(provider_request)
    if requested <= sent:
        return "sent_asset_uris"
    if requested & sent:
        return "partially_sent_asset_uris"
    return "intent_only_not_sent"


def _provider_request_image_urls(provider_request: dict[str, object]) -> set[str]:
    payload = provider_request.get("payload")
    if not isinstance(payload, dict):
        return set()
    content = payload.get("content")
    if not isinstance(content, list):
        return set()
    urls: set[str] = set()
    for item in content:
        if not isinstance(item, dict):
            continue
        image_url = item.get("image_url")
        if isinstance(image_url, dict) and image_url.get("url"):
            urls.add(str(image_url["url"]))
    return urls
