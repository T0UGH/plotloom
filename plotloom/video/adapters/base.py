from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from plotloom.video.types import PlotloomVideoRequest, ValidationResult, VideoAdapterCapabilities


@dataclass(frozen=True)
class VideoSubmitResult:
    adapter: str
    provider: str
    provider_task_id: str
    status: str
    local_path: Path | None = None
    failure_category: str | None = None
    failure_stage: str | None = None
    retryable: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoTaskStatus:
    adapter: str
    provider_task_id: str
    status: str
    video_url: str | None = None
    local_path: Path | None = None
    error_code: str | None = None
    error_message: str | None = None
    failure_category: str | None = None
    failure_stage: str | None = None
    retryable: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class VideoAdapter(Protocol):
    name: str
    provider: str

    def capabilities(self) -> VideoAdapterCapabilities: ...

    def validate_request(self, request: PlotloomVideoRequest) -> ValidationResult: ...

    def compile_native_request(self, request: PlotloomVideoRequest) -> dict[str, Any]: ...

    def submit(self, request: PlotloomVideoRequest, *, candidate_path: Path) -> VideoSubmitResult: ...

    def poll(self, provider_task_id: str, *, download_dir: Path) -> VideoTaskStatus: ...
