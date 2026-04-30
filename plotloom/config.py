from __future__ import annotations

import os
import stat
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli_w

from plotloom.errors import ConfigError

DEFAULT_CONFIG_PATH = Path("~/.plotloom/.env.toml")

ENV_MAP = {
    ("plotloom", "repos_root"): "PLOTLOOM_REPOS_ROOT",
    ("plotloom", "registry_path"): "PLOTLOOM_REGISTRY_PATH",
    ("adapters.codex-app-server", "codex_binary"): "CODEX_BINARY",
    ("adapters.codex-app-server", "app_server_url"): "CODEX_APP_SERVER_URL",
    ("adapters.dreamina-cli", "binary"): "DREAMINA_BINARY",
    ("adapters.dreamina-cli", "home"): "DREAMINA_HOME",
    ("adapters.volcengine-seedance", "ark_api_key"): "ARK_API_KEY",
    ("adapters.volcengine-seedance", "base_url"): "PLOTLOOM_VOLCENGINE_BASE_URL",
    ("adapters.volcengine-seedance", "model"): "PLOTLOOM_VOLCENGINE_MODEL",
}

DEFAULT_TEMPLATE = {
    "plotloom": {
        "repos_root": "~/plotloom_repo",
        "registry_path": "~/plotloom.toml",
        "default_image_adapter": "codex-app-server",
        "default_video_adapters": ["dreamina-cli", "volcengine-seedance"],
    },
    "adapters": {
        "codex-app-server": {"enabled": True, "codex_binary": "codex", "app_server_url": ""},
        "dreamina-cli": {"enabled": True, "binary": "dreamina", "home": "~"},
        "volcengine-seedance": {
            "enabled": True,
            "ark_api_key": "",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-seedance-2-0-260128",
            "default_resolution": "720p",
        },
    },
}


@dataclass(frozen=True)
class PlotloomConfig:
    path: Path
    data: dict[str, Any] = field(default_factory=dict)

    def section_value(self, dotted_section: str, key: str, default: Any = None) -> Any:
        env = ENV_MAP.get((dotted_section, key))
        if env and os.environ.get(env):
            return os.environ[env]

        current: Any = self.data
        for part in dotted_section.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(part, {})
        if not isinstance(current, dict):
            return default
        return current.get(key, default)

    def adapter_value(self, adapter: str, key: str, default: Any = None) -> Any:
        return self.section_value(f"adapters.{adapter}", key, default)

    def value_source(self, dotted_section: str, key: str) -> str:
        env = ENV_MAP.get((dotted_section, key))
        if env and os.environ.get(env):
            return "env"

        current: Any = self.data
        for part in dotted_section.split("."):
            if not isinstance(current, dict):
                return "absent"
            current = current.get(part, {})
        if not isinstance(current, dict) or not current.get(key):
            return "absent"
        return "config"

    @property
    def repos_root(self) -> Path:
        return Path(self.section_value("plotloom", "repos_root", "~/plotloom_repo")).expanduser()

    @property
    def registry_path(self) -> Path:
        return Path(self.section_value("plotloom", "registry_path", "~/plotloom.toml")).expanduser()


def default_config_path() -> Path:
    return Path(os.environ.get("PLOTLOOM_CONFIG", str(DEFAULT_CONFIG_PATH))).expanduser()


def resolve_config_path(path: str | Path | None = None) -> Path:
    return Path(path).expanduser() if path else default_config_path()


def load_config(path: str | Path | None = None) -> PlotloomConfig:
    cfg_path = resolve_config_path(path)
    data: dict[str, Any] = {}
    if cfg_path.exists():
        try:
            data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as error:
            raise ConfigError(
                f"Could not parse config TOML at {cfg_path}: {error}",
                next_step="Fix the TOML syntax or run plotloom config init --force to recreate it.",
            ) from error
    return PlotloomConfig(path=cfg_path, data=data)


def write_default_config(path: Path, *, force: bool = False) -> None:
    if path.exists() and not force:
        path.chmod(0o600)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps(DEFAULT_TEMPLATE), encoding="utf-8")
    path.chmod(0o600)


def permission_warning(path: Path) -> str | None:
    if not path.exists():
        return None
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        return f"config file permissions are too broad: {oct(mode)}"
    return None
