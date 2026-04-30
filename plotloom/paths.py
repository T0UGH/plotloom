from __future__ import annotations

import re
from pathlib import Path


def _normalized_suffix(suffix: str) -> str:
    if not suffix:
        raise ValueError("candidate suffix is required")
    return suffix if suffix.startswith(".") else f".{suffix}"


def next_candidate_path(candidates_dir: Path | str, suffix: str, adapter: str | None = None) -> Path:
    candidates_path = Path(candidates_dir)
    normalized_suffix = _normalized_suffix(suffix)
    pattern = re.compile(rf"^v(?P<number>\d{{3,}})(?:\.[^.]+)?{re.escape(normalized_suffix)}$")
    max_number = 0

    if candidates_path.exists():
        for path in candidates_path.iterdir():
            if not path.is_file():
                continue
            match = pattern.match(path.name)
            if match:
                max_number = max(max_number, int(match.group("number")))

    next_number = max_number + 1
    adapter_part = f".{adapter}" if adapter else ""
    return candidates_path / f"v{next_number:03d}{adapter_part}{normalized_suffix}"


def selected_for_candidate(candidate: Path | str) -> Path:
    candidate_path = Path(candidate)
    if candidate_path.parent.name != "candidates":
        raise ValueError("candidate must be inside a candidates directory")
    return candidate_path.parent.parent / f"selected{candidate_path.suffix}"
