from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

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


@dataclass(frozen=True)
class CanonicalAssetIssue:
    character: str
    path: Path
    message: str


def canonical_cast_info(repo: Path, character: str) -> dict[str, Any]:
    root = repo / "assets" / "cast" / character
    selected = root / "selected.png"
    selected_face_blocked = root / "selected-face-blocked.png"
    metadata_path = root / "metadata.toml"
    metadata: dict[str, Any] = {}
    metadata_error = None
    if metadata_path.exists():
        try:
            metadata = tomllib.loads(metadata_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as error:
            metadata_error = str(error)
    return {
        "character": character,
        "root": str(root),
        "selected": str(selected),
        "selected_exists": selected.exists(),
        "selected_face_blocked": str(selected_face_blocked),
        "selected_face_blocked_exists": selected_face_blocked.exists(),
        "metadata": str(metadata_path),
        "metadata_exists": metadata_path.exists(),
        "metadata_error": metadata_error,
        "metadata_data": metadata,
    }


def select_cast_asset(
    repo: Path,
    *,
    character: str,
    candidate: Path,
    face_blocked: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    source = _resolve_repo_file(repo, candidate)
    blocked_source = _resolve_repo_file(repo, face_blocked) if face_blocked else None
    root = repo / "assets" / "cast" / character
    root.mkdir(parents=True, exist_ok=True)
    selected = root / "selected.png"
    selected_face_blocked = root / "selected-face-blocked.png"
    metadata_path = root / "metadata.toml"
    for target in (selected, selected_face_blocked if blocked_source else None, metadata_path):
        if target and target.exists() and not force:
            raise FileExistsError(f"canonical asset already exists: {target}")
    shutil.copy2(source, selected)
    if blocked_source:
        shutil.copy2(blocked_source, selected_face_blocked)
    data: dict[str, Any] = {
        "character": character,
        "selected_candidate": _repo_relative(repo, source),
        "selected": _repo_relative(repo, selected),
        "selected_at": datetime.now().isoformat(timespec="seconds"),
        "selected_by": "manual",
        "notes": "Canonical cast asset selected by plotloom asset select.",
    }
    if blocked_source:
        data["selected_face_blocked_candidate"] = _repo_relative(repo, blocked_source)
        data["selected_face_blocked"] = _repo_relative(repo, selected_face_blocked)
    import tomli_w

    metadata_path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return canonical_cast_info(repo, character)


def validate_canonical_cast_assets(repo: Path) -> list[CanonicalAssetIssue]:
    cast_root = repo / "assets" / "cast"
    if not cast_root.exists():
        return []
    issues: list[CanonicalAssetIssue] = []
    for character_dir in sorted(path for path in cast_root.iterdir() if path.is_dir()):
        character = character_dir.name
        for name in ("selected.png", "metadata.toml"):
            path = character_dir / name
            if not path.exists():
                issues.append(CanonicalAssetIssue(character=character, path=path, message=f"missing canonical {name}"))
    return issues


def _resolve_repo_file(repo: Path, path: Path | None) -> Path:
    if path is None:
        raise ValueError("path is required")
    target = path.expanduser()
    if not target.is_absolute():
        target = repo / target
    resolved = target.resolve()
    if not resolved.is_relative_to(repo.resolve()):
        raise ValueError(f"asset must be inside repo: {path}")
    if not resolved.exists():
        raise FileNotFoundError(f"asset file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"asset path is not a file: {resolved}")
    return resolved


def _repo_relative(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()
