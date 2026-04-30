from __future__ import annotations

import tomllib
from pathlib import Path


def compare_receipts(receipts: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in receipts:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        media = data.get("media") if isinstance(data.get("media"), dict) else {}
        rows.append(
            {
                "adapter": data.get("adapter"),
                "mode": data.get("mode"),
                "status": data.get("status"),
                "candidate_path": data.get("candidate_path"),
                "duration": media.get("duration") if isinstance(media, dict) else None,
                "has_audio": media.get("has_audio") if isinstance(media, dict) else None,
                "failure_mode": data.get("error_code"),
                "receipt_path": str(path),
            }
        )
    return rows
