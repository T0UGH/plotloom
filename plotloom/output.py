from __future__ import annotations

import json
from typing import Any


def emit(data: dict[str, Any], *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    message = data.get("message")
    if message:
        print(message)
    for key in ("path", "repo", "receipt_path", "candidate_path", "selected_path", "final_path"):
        if data.get(key):
            print(f"{key}: {data[key]}")
