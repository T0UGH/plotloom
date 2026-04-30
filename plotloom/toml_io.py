from __future__ import annotations


def toml_str(value: object) -> str:
    s = str(value)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'
