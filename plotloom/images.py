from __future__ import annotations

from pathlib import Path

from plotloom.paths import next_candidate_path


def image_output_path(
    repo: Path,
    *,
    kind: str,
    filename: str | None = None,
    character: str | None = None,
    scene: str | None = None,
    episode: str | None = None,
    clip: str | None = None,
) -> Path:
    if kind == "cast":
        if not character:
            raise ValueError("--character is required for cast images")
        return repo / "assets" / "cast" / character / (filename or "character-grid.png")
    if kind == "scene":
        if not scene:
            raise ValueError("--scene is required for scene images")
        return next_candidate_path(repo / "assets" / "scenes" / scene / "candidates", ".png")
    if kind == "cover":
        if not episode:
            raise ValueError("--episode is required for cover images")
        return next_candidate_path(repo / "episodes" / episode / "images" / "covers" / "candidates", ".png")
    if kind == "reference":
        if not episode or not clip:
            raise ValueError("--episode and --clip are required for reference images")
        return next_candidate_path(repo / "episodes" / episode / "images" / "references" / clip / "candidates", ".png")
    raise ValueError(f"unknown image kind: {kind}")
