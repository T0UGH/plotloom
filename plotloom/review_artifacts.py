from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from plotloom.media import probe_media


@dataclass(frozen=True)
class ReviewArtifactResult:
    candidate_path: Path
    output_dir: Path
    artifacts: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def create_media_review_artifacts(
    candidate_path: Path,
    output_dir: Path,
    *,
    repo: Path | None = None,
    extract_first_frame: bool = True,
    extract_last_frame: bool = True,
    reviewer: str = "manual",
) -> ReviewArtifactResult:
    candidate = candidate_path.expanduser().resolve()
    if not candidate.is_file():
        raise ValueError(f"candidate is missing or not a file: {candidate}")
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}
    warnings: list[str] = []

    ffprobe_raw = output_dir / "ffprobe-raw.json"
    raw_result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(candidate),
        ]
    )
    if raw_result.returncode == 0:
        ffprobe_raw.write_text(raw_result.stdout or "{}", encoding="utf-8")
        artifacts["ffprobe_raw"] = str(ffprobe_raw)
    else:
        warnings.append(f"ffprobe raw failed: {_command_error(raw_result)}")

    try:
        facts = probe_media(candidate).to_dict()
        ffprobe_summary = output_dir / "ffprobe-summary.json"
        ffprobe_summary.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts["ffprobe_summary"] = str(ffprobe_summary)
    except Exception as error:
        facts = {"path": str(candidate), "probe_error": str(error)}
        warnings.append(f"ffprobe summary failed: {error}")

    volumedetect = output_dir / "volumedetect.txt"
    volume_result = _run(["ffmpeg", "-hide_banner", "-i", str(candidate), "-af", "volumedetect", "-f", "null", "-"])
    if volume_result.returncode == 0:
        volumedetect.write_text(volume_result.stderr or volume_result.stdout or "", encoding="utf-8")
        artifacts["volumedetect"] = str(volumedetect)
    else:
        warnings.append(f"volumedetect failed: {_command_error(volume_result)}")

    frames_dir = output_dir / "frames"
    if extract_first_frame:
        first = frames_dir / "first-frame.jpg"
        if _extract_frame(candidate, first, position="start"):
            artifacts["first_frame"] = str(first)
        else:
            warnings.append("first frame extraction failed")
    if extract_last_frame:
        last = frames_dir / "last-frame.jpg"
        duration = facts.get("duration") if isinstance(facts, dict) else None
        if _extract_frame(candidate, last, position="end", duration=duration):
            artifacts["last_frame"] = str(last)
        else:
            warnings.append("last frame extraction failed")

    review_md = output_dir / "REVIEW.md"
    review_md.write_text(_review_note(candidate, repo=repo, facts=facts, artifacts=artifacts, warnings=warnings, reviewer=reviewer), encoding="utf-8")
    artifacts["review"] = str(review_md)
    return ReviewArtifactResult(candidate_path=candidate, output_dir=output_dir, artifacts=artifacts, warnings=warnings)


def write_selected_note(
    selected_path: Path,
    note_path: Path,
    *,
    repo: Path | None,
    artifacts: dict[str, str],
    reason: str | None = None,
) -> None:
    note_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Selected Media Note",
        "",
        f"- selected: `{_display_path(selected_path, repo)}`",
        f"- selected_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- reason: {reason or 'manual selection'}",
        "",
        "## Continuity artifacts",
        "",
    ]
    for key in ("first_frame", "last_frame"):
        value = artifacts.get(key)
        lines.append(f"- {key}: `{_display_path(Path(value), repo)}`" if value else f"- {key}: not generated")
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError as error:
        return subprocess.CompletedProcess(command, 127, "", str(error))


def _extract_frame(candidate: Path, output: Path, *, position: str, duration: object | None = None) -> bool:
    output.parent.mkdir(parents=True, exist_ok=True)
    if position == "end":
        seconds = _last_frame_second(duration)
        command = ["ffmpeg", "-y", "-hide_banner", "-ss", f"{seconds:.3f}", "-i", str(candidate), "-frames:v", "1", str(output)]
    else:
        command = ["ffmpeg", "-y", "-hide_banner", "-i", str(candidate), "-frames:v", "1", str(output)]
    result = _run(command)
    return result.returncode == 0 and output.exists()


def _last_frame_second(duration: object | None) -> float:
    try:
        value = float(duration)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, value - 0.05)


def _command_error(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout or f"exit {result.returncode}").strip()


def _review_note(
    candidate: Path,
    *,
    repo: Path | None,
    facts: dict[str, Any],
    artifacts: dict[str, str],
    warnings: list[str],
    reviewer: str,
) -> str:
    lines = [
        "# Media Review",
        "",
        f"- candidate: `{_display_path(candidate, repo)}`",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- reviewer: {reviewer}",
        "",
        "## Media facts",
        "",
    ]
    for key in ("duration", "width", "height", "fps", "has_audio", "video_codec", "audio_codec", "format_name"):
        lines.append(f"- {key}: {facts.get(key)}")
    lines.extend(["", "## Artifacts", ""])
    for key, path in sorted(artifacts.items()):
        lines.append(f"- {key}: `{_display_path(Path(path), repo)}`")
    lines.extend(
        [
            "",
            "## QA checklist",
            "",
            "- refs used: pending",
            "- identity consistency: pending",
            "- face visible: pending",
            "- story beat clear: pending",
            "- subtitle/watermark/text artifacts: pending",
            "- aspect ratio / crop / black frames: pending",
            "- decision: selected/reroll/revise_prompt/ask_user",
        ]
    )
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines) + "\n"


def _display_path(path: Path, repo: Path | None) -> str:
    resolved = path.expanduser().resolve()
    if repo is not None and resolved.is_relative_to(repo.resolve()):
        return resolved.relative_to(repo.resolve()).as_posix()
    return str(resolved)
