from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import FrozenSet, Literal


class VideoMode(StrEnum):
    TEXT_TO_VIDEO = "text-to-video"
    IMAGE_TO_VIDEO = "image-to-video"
    REFERENCE_TO_VIDEO = "reference-to-video"
    VIDEO_EDIT = "video-edit"


AudioIntent = Literal["none", "native_if_supported", "require_native"]


@dataclass(frozen=True)
class PlotloomVideoRequest:
    repo: Path
    episode: str
    clip: str
    adapter: str
    mode: VideoMode
    prompt_file: Path
    prompt_text: str
    ratio: str
    resolution: str
    duration: int
    audio_intent: AudioIntent = "native_if_supported"
    seed: int | None = None
    first_frame: Path | None = None
    reference_images: list[Path] = field(default_factory=list)
    reference_videos: list[Path] = field(default_factory=list)
    source_video: Path | None = None
    allow_downgrade: bool = False
    allow_normalize_duration: bool = False


@dataclass(frozen=True)
class VideoAdapterCapabilities:
    adapter: str
    modes: FrozenSet[VideoMode]
    min_duration: int
    max_duration: int
    ratios: FrozenSet[str]
    resolutions: FrozenSet[str]
    max_prompt_chars: int | None
    supports_native_audio: bool
    supports_seed: bool
    supports_first_frame: bool
    supports_reference_images: bool
    supports_reference_videos: bool
    supports_video_edit: bool
    extra_durations: FrozenSet[int] = field(default_factory=frozenset)


@dataclass(frozen=True)
class ValidationIssue:
    level: Literal["error", "warning"]
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)
