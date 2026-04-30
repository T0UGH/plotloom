from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from plotloom.paths import selected_for_candidate


@dataclass(frozen=True)
class SelectionResult:
    selected_path: Path
    backup_path: Path | None = None


def select_candidate(candidate: Path | str) -> SelectionResult:
    candidate_path = Path(candidate).expanduser().resolve()
    if not candidate_path.is_file():
        raise ValueError(f"candidate is missing or not a file: {candidate_path}")

    selected_path = selected_for_candidate(candidate_path)
    backup_path = None
    if selected_path.exists():
        if not selected_path.is_file():
            raise ValueError(f"selected path exists but is not a file: {selected_path}")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = selected_path.with_name(f"selected-prev-{timestamp}{selected_path.suffix}")
        shutil.copy2(selected_path, backup_path)

    selected_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate_path, selected_path)
    return SelectionResult(selected_path=selected_path, backup_path=backup_path)
