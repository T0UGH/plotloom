from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from plotloom.media import probe_media


def discover_selected_clips(repo: Path, episode: str, clips: list[str] | None = None) -> list[Path]:
    videos = Path(repo) / "episodes" / episode / "videos"
    if clips:
        selected = [videos / clip / "selected.mp4" for clip in clips]
    else:
        selected = sorted(videos.glob("clip-*/selected.mp4"), key=lambda path: path.parent.name)
    return [path for path in selected if path.exists()]


def stitch_clips(
    clips: list[Path],
    output: Path,
    *,
    normalize: bool = False,
    resolution: str = "720p",
    fps: int = 24,
) -> Path:
    if not clips:
        raise ValueError("no selected clips found")
    for clip in clips:
        probe_media(clip)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        inputs = _normalize_clips(clips, temp, resolution=resolution, fps=fps) if normalize else clips
        concat = temp / "concat.txt"
        concat.write_text("".join(f"file '{path}'\n" for path in inputs), encoding="utf-8")
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(output)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"ffmpeg exited {result.returncode}")
    probe_media(output)
    return output


def _normalize_clips(clips: list[Path], temp: Path, *, resolution: str, fps: int) -> list[Path]:
    normalized: list[Path] = []
    scale = _scale_filter(resolution)
    for index, clip in enumerate(clips, 1):
        output = temp / f"clip-{index:03d}.mp4"
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(clip),
                "-vf",
                f"{scale},fps={fps}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "44100",
                "-ac",
                "2",
                str(output),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"ffmpeg normalize exited {result.returncode}")
        normalized.append(output)
    return normalized


def _scale_filter(resolution: str) -> str:
    if resolution == "720p":
        return "scale=-2:720"
    if resolution == "1080p":
        return "scale=-2:1080"
    return "scale=trunc(iw/2)*2:trunc(ih/2)*2"
