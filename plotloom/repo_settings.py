from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VideoContinuityConfig:
    enabled: bool = False
    extract_first_frame: bool = False
    extract_last_frame: bool = False
    auto_use_previous_last_frame: bool = False


def load_video_continuity_config(repo: Path | None) -> VideoContinuityConfig:
    if repo is None:
        return VideoContinuityConfig()
    config_path = repo / "plotloom.toml"
    if not config_path.exists():
        return VideoContinuityConfig()
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return VideoContinuityConfig()
    video = data.get("video")
    continuity: Any = video.get("continuity") if isinstance(video, dict) else None
    if not isinstance(continuity, dict):
        return VideoContinuityConfig()
    return VideoContinuityConfig(
        enabled=bool(continuity.get("enabled", False)),
        extract_first_frame=bool(continuity.get("extract_first_frame", False)),
        extract_last_frame=bool(continuity.get("extract_last_frame", False)),
        auto_use_previous_last_frame=bool(continuity.get("auto_use_previous_last_frame", False)),
    )
