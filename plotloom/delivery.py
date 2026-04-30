from __future__ import annotations

from pathlib import Path


def episode_files(repo: Path, episode: str, *, include_candidates: bool = False) -> list[str]:
    ep = Path(repo) / "episodes" / episode
    files: list[str] = []
    final = ep / "videos" / "final.mp4"
    if final.exists():
        files.append(str(final.relative_to(repo)))
    for selected in sorted((ep / "videos").glob("clip-*/selected.mp4")):
        files.append(str(selected.relative_to(repo)))
    if include_candidates:
        for candidate in sorted((ep / "videos").glob("clip-*/candidates/*")):
            if candidate.is_file():
                files.append(str(candidate.relative_to(repo)))
    return files


def delivery_summary(repo: Path, episode: str, *, include_candidates: bool = False) -> str:
    files = episode_files(repo, episode, include_candidates=include_candidates)
    lines = [f"# Delivery Summary: {episode}", ""]
    lines.extend(f"- `{path}`" for path in files)
    if not files:
        lines.append("- No delivery files found.")
    return "\n".join(lines) + "\n"
