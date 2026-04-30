from __future__ import annotations

import importlib.util
import shutil


def redact_present(value: str | None, *, source: str) -> str:
    return f"present via {source}" if value else "absent"


def binary_status(name: str) -> dict[str, str | bool]:
    path = shutil.which(name)
    return {"name": name, "ok": bool(path), "path": path or ""}


def import_status(module: str) -> dict[str, str | bool]:
    return {"module": module, "ok": importlib.util.find_spec(module) is not None}
