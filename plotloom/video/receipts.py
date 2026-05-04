from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def _local_iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_path_part(value: str) -> str:
    return value.replace("/", "-").replace(":", "-")


def _safe_dir_part(value: str, field_name: str) -> str:
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or ".." in path.parts
    ):
        raise ValueError(f"{field_name} must be a safe path part")
    return value


def _toml_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _toml_safe(item) for key, item in value.items() if item is not None}
    if isinstance(value, (list, tuple)):
        return [_toml_safe(item) for item in value if item is not None]
    return value


@dataclass
class Receipt:
    adapter: str
    provider: str
    provider_task_id: str
    status: str
    repo: str
    episode: str
    clip: str
    mode: str
    prompt_file: str
    compiled_prompt_sha256: str
    prompt_chars: int
    duration: int
    ratio: str
    resolution: str
    audio_intent: str
    credential_source: str
    receipt_version: int = 1
    submitted_at: str = field(default_factory=_local_iso_now)
    updated_at: str = field(default_factory=_local_iso_now)
    candidate_path: str | None = None
    reference_map_path: str | None = None
    reference_intent: list[dict[str, Any]] = field(default_factory=list)
    provider_request: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    failure_category: str | None = None
    failure_stage: str | None = None
    retryable: bool | None = None
    next_step: str | None = None
    provider_data: dict[str, Any] = field(default_factory=dict)
    media: dict[str, Any] = field(default_factory=dict)


def receipt_path(repo: str | Path, episode: str, clip: str, adapter: str, provider_task_id: str) -> Path:
    episode = _safe_dir_part(episode, "episode")
    clip = _safe_dir_part(clip, "clip")
    name = f"{_safe_path_part(adapter)}-{_safe_path_part(provider_task_id)}.toml"
    return Path(repo) / "episodes" / episode / "videos" / clip / "tasks" / name


def _receipt_data(receipt: Receipt) -> dict[str, Any]:
    return {key: _toml_safe(value) for key, value in asdict(receipt).items() if value is not None}


def write_receipt(path: str | Path, receipt: Receipt) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    import tomli_w

    path.write_text(tomli_w.dumps(_receipt_data(receipt)), encoding="utf-8")


def write_latest_pointer(path: str | Path, receipt: Receipt) -> None:
    path = Path(path)
    clip_dir = path.parent.parent
    latest = clip_dir / "latest-task.toml"
    latest.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "receipt": path.relative_to(clip_dir).as_posix(),
        "adapter": receipt.adapter,
        "provider_task_id": receipt.provider_task_id,
        "status": receipt.status,
        "updated_at": receipt.updated_at,
    }
    import tomli_w

    latest.write_text(tomli_w.dumps(data), encoding="utf-8")
