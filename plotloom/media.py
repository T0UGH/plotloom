from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from plotloom.errors import MediaValidationError


@dataclass(frozen=True)
class MediaFacts:
    path: Path
    duration: float | None
    width: int | None
    height: int | None
    fps: float | None
    has_audio: bool
    video_codec: str | None
    audio_codec: str | None
    format_name: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "has_audio": self.has_audio,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "format_name": self.format_name,
        }


def probe_media(path: Path) -> MediaFacts:
    target = path.expanduser().resolve()
    if not target.exists():
        raise MediaValidationError(f"media path not found: {target}", next_step="Check the media path and retry.")

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(target),
    ]
    try:
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as error:
        raise MediaValidationError(
            "ffprobe executable not found",
            next_step="Install ffmpeg/ffprobe and retry.",
        ) from error

    if result.returncode != 0:
        detail = (result.stderr or "").strip() or f"exit code {result.returncode}"
        raise MediaValidationError(f"ffprobe failed for {target}: {detail}")

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as error:
        raise MediaValidationError(f"ffprobe returned invalid JSON for {target}: {error}") from error

    streams = payload.get("streams", [])
    if not isinstance(streams, list):
        streams = []
    video_stream = _first_stream(streams, "video")
    audio_stream = _first_stream(streams, "audio")
    format_data = payload.get("format", {})
    if not isinstance(format_data, dict):
        format_data = {}

    return MediaFacts(
        path=target,
        duration=_first_float(format_data.get("duration"), video_stream.get("duration"), audio_stream.get("duration")),
        width=_parse_int(video_stream.get("width")),
        height=_parse_int(video_stream.get("height")),
        fps=_first_fps(video_stream.get("avg_frame_rate"), video_stream.get("r_frame_rate")),
        has_audio=bool(audio_stream),
        video_codec=_parse_str(video_stream.get("codec_name")),
        audio_codec=_parse_str(audio_stream.get("codec_name")),
        format_name=_parse_str(format_data.get("format_name")),
    )


def _first_stream(streams: list[Any], codec_type: str) -> dict[str, Any]:
    for stream in streams:
        if isinstance(stream, dict) and stream.get("codec_type") == codec_type:
            return stream
    return {}


def _parse_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _first_float(*values: Any) -> float | None:
    for value in values:
        parsed = _parse_float(value)
        if parsed is not None:
            return parsed
    return None


def _parse_fps(value: Any) -> float | None:
    text = _parse_str(value)
    if text is None:
        return None
    if "/" in text:
        try:
            ratio = Fraction(text)
        except (ValueError, ZeroDivisionError):
            return None
        if ratio.denominator == 0 or ratio.numerator == 0:
            return None
        return float(ratio)
    return _parse_float(text)


def _first_fps(*values: Any) -> float | None:
    for value in values:
        parsed = _parse_fps(value)
        if parsed is not None:
            return parsed
    return None
