from __future__ import annotations

import json


def toml_str(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)
