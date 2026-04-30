from __future__ import annotations

import math
from pathlib import Path

import click

from plotloom.errors import MediaValidationError
from plotloom.media import MediaFacts, probe_media
from plotloom.output import emit

NON_NEGATIVE_FINITE_FLOAT = click.FloatRange(min=0.0, min_open=False, clamp=False)
POSITIVE_FINITE_FLOAT = click.FloatRange(min=0.0, min_open=True, clamp=False)


@click.group("media")
def media_group() -> None:
    """Inspect and validate local media files."""


@media_group.command("probe")
@click.argument("path", type=click.Path(path_type=str))
@click.pass_context
def probe_command(ctx: click.Context, path: str) -> None:
    facts = probe_media(Path(path))
    emit(
        {
            "ok": True,
            "command": "media.probe",
            "media": facts.to_dict(),
            "message": _facts_message(facts),
        },
        as_json=ctx.obj.get("as_json"),
    )


@media_group.command("check")
@click.argument("path", type=click.Path(path_type=str))
@click.option("--expect-video", is_flag=True)
@click.option("--expect-audio", is_flag=True)
@click.option("--ratio", help="Expected width:height ratio, for example 9:16.")
@click.option("--resolution", help="Expected resolution, for example 1080x1920 or 720p.")
@click.option("--duration", type=NON_NEGATIVE_FINITE_FLOAT, help="Expected duration in seconds.")
@click.option("--duration-tolerance", type=NON_NEGATIVE_FINITE_FLOAT, default=0.1, show_default=True)
@click.pass_context
def check_command(
    ctx: click.Context,
    path: str,
    expect_video: bool,
    expect_audio: bool,
    ratio: str | None,
    resolution: str | None,
    duration: float | None,
    duration_tolerance: float,
) -> None:
    expected_ratio = _parse_ratio(ratio) if ratio is not None else None
    expected_resolution = _parse_resolution(resolution) if resolution is not None else None
    if duration is not None:
        _ensure_finite(duration, "--duration")
    _ensure_finite(duration_tolerance, "--duration-tolerance")

    facts = probe_media(Path(path))
    checks: dict[str, dict[str, object]] = {}

    if expect_video:
        checks["video"] = {
            "ok": facts.video_codec is not None and facts.width is not None and facts.height is not None,
            "actual": facts.video_codec,
        }
    if expect_audio:
        checks["audio"] = {"ok": facts.has_audio, "actual": facts.audio_codec}
    if expected_ratio is not None:
        checks["ratio"] = _ratio_check(facts, ratio or "", expected_ratio)
    if expected_resolution is not None:
        checks["resolution"] = _resolution_check(facts, resolution or "", expected_resolution)
    if duration is not None:
        checks["duration"] = _duration_check(facts, duration, duration_tolerance)

    failed = [name for name, result in checks.items() if not result["ok"]]
    message = "media check ok" if not failed else f"media check failed: {', '.join(failed)}"
    emit(
        {
            "ok": not failed,
            "command": "media.check",
            "media": facts.to_dict(),
            "checks": checks,
            "message": message,
        },
        as_json=ctx.obj.get("as_json"),
    )
    if failed:
        ctx.exit(4)


@media_group.command("normalize")
@click.argument("input_path", type=click.Path(path_type=str))
@click.option("--output", "output_path", required=True, type=click.Path(path_type=str))
@click.option("--ratio", help="Target width:height ratio, for example 9:16.")
@click.option("--resolution", help="Target resolution, for example 1080x1920 or 720p.")
@click.option("--fps", type=POSITIVE_FINITE_FLOAT, help="Target frames per second.")
@click.option("--audio", type=click.Choice(["stereo", "silent"]), help="Target audio behavior.")
def normalize_command(
    input_path: str,
    output_path: str,
    ratio: str | None,
    resolution: str | None,
    fps: float | None,
    audio: str | None,
) -> None:
    _ = (input_path, output_path, ratio, resolution, fps, audio)
    raise MediaValidationError(
        "media normalize is not implemented yet; no files were changed",
        next_step="Use 'plotloom media probe' and 'plotloom media check' until ffmpeg normalize behavior is specified.",
    )


def _facts_message(facts: MediaFacts) -> str:
    resolution = _actual_resolution(facts)
    fps = f"{facts.fps:.3f}" if facts.fps is not None else "unknown"
    duration = f"{facts.duration:.3f}s" if facts.duration is not None else "unknown"
    return "\n".join(
        [
            f"media: {facts.path}",
            f"duration: {duration}",
            f"resolution: {resolution}",
            f"fps: {fps}",
            f"has_audio: {'yes' if facts.has_audio else 'no'}",
            f"video_codec: {facts.video_codec or 'unknown'}",
            f"audio_codec: {facts.audio_codec or 'none'}",
            f"format_name: {facts.format_name or 'unknown'}",
        ]
    )


def _actual_resolution(facts: MediaFacts) -> str:
    if facts.width is None or facts.height is None:
        return "unknown"
    return f"{facts.width}x{facts.height}"


def _parse_ratio(value: str) -> tuple[int, int]:
    separator = ":" if ":" in value else "/"
    parts = value.split(separator, 1)
    if len(parts) != 2:
        raise click.BadParameter("expected WIDTH:HEIGHT, for example 9:16", param_hint="--ratio")
    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError as error:
        raise click.BadParameter("expected integer WIDTH:HEIGHT", param_hint="--ratio") from error
    if width <= 0 or height <= 0:
        raise click.BadParameter("ratio values must be positive", param_hint="--ratio")
    return width, height


def _ratio_check(facts: MediaFacts, expected: str, parsed: tuple[int, int]) -> dict[str, object]:
    expected_width, expected_height = parsed
    ok = (
        facts.width is not None
        and facts.height is not None
        and facts.width * expected_height == facts.height * expected_width
    )
    return {"ok": ok, "expected": expected, "actual": _actual_resolution(facts)}


def _parse_resolution(value: str) -> tuple[int | None, int]:
    if value.endswith("p"):
        try:
            height = int(value[:-1])
        except ValueError as error:
            raise click.BadParameter("expected HEIGHTp, for example 720p", param_hint="--resolution") from error
        if height <= 0:
            raise click.BadParameter("resolution height must be positive", param_hint="--resolution")
        return None, height

    parts = value.lower().split("x", 1)
    if len(parts) != 2:
        raise click.BadParameter("expected WIDTHxHEIGHT or HEIGHTp", param_hint="--resolution")
    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError as error:
        raise click.BadParameter("expected integer WIDTHxHEIGHT", param_hint="--resolution") from error
    if width <= 0 or height <= 0:
        raise click.BadParameter("resolution values must be positive", param_hint="--resolution")
    return width, height


def _resolution_check(facts: MediaFacts, expected: str, parsed: tuple[int | None, int]) -> dict[str, object]:
    expected_width, expected_height = parsed
    ok = facts.height == expected_height and (expected_width is None or facts.width == expected_width)
    return {"ok": ok, "expected": expected, "actual": _actual_resolution(facts)}


def _duration_check(facts: MediaFacts, expected: float, tolerance: float) -> dict[str, object]:
    ok = facts.duration is not None and abs(facts.duration - expected) <= tolerance
    return {"ok": ok, "expected": expected, "actual": facts.duration, "tolerance": tolerance}


def _ensure_finite(value: float, param_hint: str) -> None:
    if not math.isfinite(value):
        raise click.BadParameter("expected a finite number", param_hint=param_hint)
