from __future__ import annotations

import shutil
from pathlib import Path

from plotloom.paths import next_candidate_path


def asset_candidate_dir(
    repo: Path,
    kind: str,
    *,
    episode: str | None = None,
    clip: str | None = None,
    character: str | None = None,
    scene: str | None = None,
) -> Path:
    if kind == "cast":
        if not character:
            raise ValueError("--character is required for cast assets")
        return repo / "assets" / "cast" / character / "candidates"
    if kind == "scene":
        if not scene:
            raise ValueError("--scene is required for scene assets")
        return repo / "assets" / "scenes" / scene / "candidates"
    if kind == "cover":
        if not episode:
            raise ValueError("--episode is required for cover assets")
        return repo / "episodes" / episode / "images" / "covers" / "candidates"
    if kind == "reference":
        if not episode or not clip:
            raise ValueError("--episode and --clip are required for reference assets")
        return repo / "episodes" / episode / "images" / "references" / clip / "candidates"
    if kind == "video":
        if not episode or not clip:
            raise ValueError("--episode and --clip are required for video assets")
        return repo / "episodes" / episode / "videos" / clip / "candidates"
    raise ValueError(f"unknown asset kind: {kind}")


def import_asset(file: Path, target_dir: Path, adapter: str | None = None) -> Path:
    source = Path(file).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"asset file not found: {source}")
    if not source.is_file():
        raise ValueError(f"asset path is not a file: {source}")
    target = next_candidate_path(target_dir, source.suffix or ".bin", adapter=adapter)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def asset_info(path: Path) -> dict[str, object]:
    target = Path(path).expanduser()
    return {
        "path": str(target),
        "suffix": target.suffix,
        "size": target.stat().st_size if target.exists() else None,
        "exists": target.exists(),
    }


def list_assets(target_dir: Path) -> list[dict[str, object]]:
    if not target_dir.exists():
        return []
    return [asset_info(path) for path in sorted(target_dir.iterdir()) if path.is_file()]
