# Plotloom CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-usable Plotloom Python CLI covering config, repo discovery/init/validate, prompt compile, image generation through local Codex image generation, mock media E2E, and real Dreamina / Aliyun Bailian Wan / VolcEngine submit-poll adapters with visible receipts.

**Architecture:** Implement a small Python package under `plotloom/` with Click commands that orchestrate deterministic helpers, adapter interfaces, TOML config/receipt files, and local media validation. Keep all production state visible in the series repo except user-level secrets in `~/.plotloom/.env.toml`; do not introduce a daemon, database, dashboard, hidden queue, or persistent JSON/YAML workflow artifact.

**Tech Stack:** Python 3.11+, Click, stdlib `tomllib`, `tomli-w`, `requests`, optional `dashscope`, optional `volcengine-python-sdk[ark]`, local `codex exec --enable image_generation`, external `dreamina`, `ffmpeg`, `ffprobe`, pytest.

---

## Source Documents

Read these before starting:

- Provider pivot: older design docs may still mention `happyhorse-fal`; for implementation, replace that provider with `aliyun-bailian-wan` and use `adapters/aliyun-bailian-wan.md`.
- `docs/design/2026-04-30-plotloom-cli-technical-design.md`
- `docs/design/2026-04-30-plotloom-cli-command-surface.md`
- `docs/design/2026-04-30-plotloom-cli-contract-details.md`
- `adapters/codex.md`
- `adapters/dreamina.md`
- `adapters/aliyun-bailian-wan.md`
- `adapters/volcengine-seedance.md`
- Existing helper scripts: `scripts/init_series.py`, `scripts/validate_repo.py`, `scripts/select_candidate.py`, `scripts/ffprobe_media.py`, `scripts/stitch_ffmpeg.py`, `scripts/adapters/fake_video.py`

## Non-Negotiable Boundaries

- Current checkpoint: Tasks 1-3 were implemented before the provider pivot. Do not redo them. Before the first provider/capability task, migrate any implemented `happyhorse-fal` config defaults/tests to `aliyun-bailian-wan`.
- Default automated tests must not call Dreamina, Aliyun Bailian, VolcEngine, or real Codex image generation.
- Real provider E2E is manual only through `doctor` and smoke commands.
- `video submit` must run provider-aware prompt compile/check before submit.
- Do not print or persist secrets. Show only `present/absent` and `credential_source`.
- Use TOML for first-party structured artifacts. Do not write persistent JSON/YAML repo artifacts.
- Store receipts under `episodes/<ep>/videos/<clip>/tasks/*.toml`; `latest-task.toml` is only a pointer.
- Keep `scripts/` working as compatibility helpers; CLI can share code but should live in `plotloom/`.

## Task 1: Python Package Skeleton And Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `plotloom/__init__.py`
- Create: `plotloom/cli.py`
- Create: `plotloom/errors.py`
- Create: `plotloom/output.py`
- Create: `tests/test_cli_basic.py`

**Step 1: Write the failing CLI smoke test**

Create `tests/test_cli_basic.py`:

```python
from click.testing import CliRunner

from plotloom.cli import main


def test_cli_version_runs():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert "plotloom" in result.output.lower()


def test_cli_json_error_shape_for_missing_command():
    result = CliRunner().invoke(main, ["--json", "missing-command"])

    assert result.exit_code != 0
    assert "No such command" in result.output
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_cli_basic.py -v
```

Expected: FAIL because `plotloom.cli` does not exist.

**Step 3: Add package metadata**

Create `pyproject.toml`:

```toml
[project]
name = "plotloom"
version = "0.1.0"
description = "Short-drama-native production CLI for Plotloom series repos"
requires-python = ">=3.11"
dependencies = [
  "click>=8.1",
  "requests>=2.31",
  "tomli-w>=1.0",
]

[project.optional-dependencies]
aliyun = ["dashscope>=1.25.8"]
volcengine = ["volcengine-python-sdk[ark]>=5.0.0"]
dev = ["pytest>=8", "ruff>=0.5"]

[project.scripts]
plotloom = "plotloom.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Create `plotloom/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `plotloom/errors.py`:

```python
class PlotloomError(Exception):
    exit_code = 1
    code = "PLOTLOOM_ERROR"

    def __init__(self, message: str, *, next_step: str | None = None):
        super().__init__(message)
        self.message = message
        self.next_step = next_step


class ConfigError(PlotloomError):
    exit_code = 2
    code = "CONFIG_ERROR"


class ProviderError(PlotloomError):
    exit_code = 3
    code = "PROVIDER_ERROR"


class MediaValidationError(PlotloomError):
    exit_code = 4
    code = "MEDIA_VALIDATION_ERROR"
```

Create `plotloom/output.py`:

```python
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
```

Create `plotloom/cli.py`:

```python
from __future__ import annotations

import click

from plotloom import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="plotloom")
@click.option("--repo", type=click.Path(path_type=str), help="Series repo path.")
@click.option("--config", "config_path", type=click.Path(path_type=str), help="Config file path.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON to stdout.")
@click.option("--quiet", is_flag=True, help="Only print critical paths/status.")
@click.option("--dry-run", is_flag=True, help="Show planned actions without provider calls.")
@click.pass_context
def main(ctx: click.Context, repo: str | None, config_path: str | None, as_json: bool, quiet: bool, dry_run: bool) -> None:
    """Plotloom short-drama production CLI."""
    ctx.ensure_object(dict)
    ctx.obj.update({"repo": repo, "config_path": config_path, "as_json": as_json, "quiet": quiet, "dry_run": dry_run})
```

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_cli_basic.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml plotloom tests/test_cli_basic.py
git commit -m "feat: add plotloom cli skeleton"
```

## Task 2: Config Model And `plotloom config`

**Files:**
- Create: `plotloom/config.py`
- Create: `plotloom/commands/__init__.py`
- Create: `plotloom/commands/config.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_config.py`

**Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.config import load_config


def test_config_init_writes_template_with_private_permissions(tmp_path):
    cfg = tmp_path / ".plotloom" / ".env.toml"
    result = CliRunner().invoke(main, ["--config", str(cfg), "config", "init"])

    assert result.exit_code == 0
    assert cfg.exists()
    assert cfg.stat().st_mode & 0o777 == 0o600
    assert "default_video_adapters" in cfg.read_text()


def test_config_env_overrides_toml(tmp_path, monkeypatch):
    cfg = tmp_path / ".env.toml"
    cfg.write_text('[adapters.aliyun-bailian-wan]\ndashscope_api_key = "from-file"\n', encoding="utf-8")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "from-env")

    loaded = load_config(cfg)

    assert loaded.adapter_value("aliyun-bailian-wan", "dashscope_api_key") == "from-env"
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_config.py -v
```

Expected: FAIL because `plotloom.config` and `config` command do not exist.

**Step 3: Implement config loader and command**

Create `plotloom/config.py`:

```python
from __future__ import annotations

import os
import stat
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli_w

DEFAULT_CONFIG_PATH = Path("~/.plotloom/.env.toml")

ENV_MAP = {
    ("plotloom", "repos_root"): "PLOTLOOM_REPOS_ROOT",
    ("plotloom", "registry_path"): "PLOTLOOM_REGISTRY_PATH",
    ("adapters.codex-app-server", "codex_binary"): "CODEX_BINARY",
    ("adapters.codex-app-server", "app_server_url"): "CODEX_APP_SERVER_URL",
    ("adapters.dreamina-cli", "binary"): "DREAMINA_BINARY",
    ("adapters.dreamina-cli", "home"): "DREAMINA_HOME",
    ("adapters.aliyun-bailian-wan", "dashscope_api_key"): "DASHSCOPE_API_KEY",
    ("adapters.aliyun-bailian-wan", "base_url"): "PLOTLOOM_ALIYUN_BAILIAN_BASE_URL",
    ("adapters.aliyun-bailian-wan", "model"): "PLOTLOOM_ALIYUN_BAILIAN_MODEL",
    ("adapters.volcengine-seedance", "ark_api_key"): "ARK_API_KEY",
    ("adapters.volcengine-seedance", "base_url"): "PLOTLOOM_VOLCENGINE_BASE_URL",
    ("adapters.volcengine-seedance", "model"): "PLOTLOOM_VOLCENGINE_MODEL",
}

DEFAULT_TEMPLATE = {
    "plotloom": {
        "repos_root": "~/plotloom_repo",
        "registry_path": "~/plotloom.toml",
        "default_image_adapter": "codex-app-server",
        "default_video_adapters": ["dreamina-cli", "aliyun-bailian-wan", "volcengine-seedance"],
    },
    "adapters": {
        "codex-app-server": {"enabled": True, "codex_binary": "codex", "app_server_url": ""},
        "dreamina-cli": {"enabled": True, "binary": "dreamina", "home": "~"},
        "aliyun-bailian-wan": {
            "enabled": True,
            "dashscope_api_key": "",
            "base_url": "https://dashscope.aliyuncs.com/api/v1",
            "model": "wan2.6-t2v",
            "default_resolution": "720p",
        },
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

    @property
    def repos_root(self) -> Path:
        return Path(self.section_value("plotloom", "repos_root", "~/plotloom_repo")).expanduser()

    @property
    def registry_path(self) -> Path:
        return Path(self.section_value("plotloom", "registry_path", "~/plotloom.toml")).expanduser()


def default_config_path() -> Path:
    return Path(os.environ.get("PLOTLOOM_CONFIG", str(DEFAULT_CONFIG_PATH))).expanduser()


def load_config(path: str | Path | None = None) -> PlotloomConfig:
    cfg_path = Path(path).expanduser() if path else default_config_path()
    data: dict[str, Any] = {}
    if cfg_path.exists():
        data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    return PlotloomConfig(path=cfg_path, data=data)


def write_default_config(path: Path, *, force: bool = False) -> None:
    if path.exists() and not force:
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
```

Create `plotloom/commands/__init__.py`:

```python
"""Click command modules for Plotloom."""
```

Create `plotloom/commands/config.py`:

```python
from __future__ import annotations

import click
import tomli_w

from plotloom.config import DEFAULT_TEMPLATE, load_config, permission_warning, write_default_config
from plotloom.output import emit


@click.group(name="config")
def config_group() -> None:
    """Manage Plotloom local config."""


@config_group.command("path")
@click.pass_context
def config_path(ctx: click.Context) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    emit({"ok": True, "command": "config.path", "path": str(cfg.path), "message": str(cfg.path)}, as_json=ctx.obj.get("as_json"))


@config_group.command("init")
@click.option("--force", is_flag=True)
@click.option("--print-template", "print_template", is_flag=True)
@click.pass_context
def config_init(ctx: click.Context, force: bool, print_template: bool) -> None:
    if print_template:
        click.echo(tomli_w.dumps(DEFAULT_TEMPLATE))
        return
    cfg = load_config(ctx.obj.get("config_path"))
    write_default_config(cfg.path, force=force)
    emit({"ok": True, "command": "config.init", "path": str(cfg.path), "message": f"config: {cfg.path}"}, as_json=ctx.obj.get("as_json"))


@config_group.command("doctor")
@click.option("--adapter", default="all")
@click.pass_context
def config_doctor(ctx: click.Context, adapter: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    warning = permission_warning(cfg.path)
    data = {"ok": warning is None, "command": "config.doctor", "path": str(cfg.path), "adapter": adapter, "warnings": [warning] if warning else []}
    emit({**data, "message": "config ok" if data["ok"] else warning}, as_json=ctx.obj.get("as_json"))
```

Modify `plotloom/cli.py`:

```python
from plotloom.commands.config import config_group

main.add_command(config_group)
```

Place the import and `add_command` after `main` is defined.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_config.py tests/test_cli_basic.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml plotloom tests/test_config.py
git commit -m "feat: add plotloom config commands"
```

## Task 3: Repo Registry, Discovery, Init, And Validate

**Files:**
- Create: `plotloom/repo.py`
- Create: `plotloom/toml_io.py`
- Create: `plotloom/commands/repo.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_repo_commands.py`

**Step 1: Write failing repo command tests**

Create `tests/test_repo_commands.py`:

```python
from pathlib import Path

from click.testing import CliRunner

from plotloom.cli import main


def test_init_creates_series_repo_and_registry(tmp_path):
    config = tmp_path / ".plotloom" / ".env.toml"
    repos_root = tmp_path / "repos"
    registry = tmp_path / "plotloom.toml"
    config.parent.mkdir()
    config.write_text(
        f'[plotloom]\nrepos_root = "{repos_root}"\nregistry_path = "{registry}"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--config", str(config), "init", "fake-heiress", "--title", "Fake Heiress"])

    assert result.exit_code == 0
    repo = repos_root / "fake-heiress"
    assert (repo / "series.md").exists()
    assert (repo / "characters.md").exists()
    assert 'slug = "fake-heiress"' in registry.read_text(encoding="utf-8")


def test_validate_requires_prompts(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes" / "ep001").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--repo", str(repo), "validate", "--episode", "ep001", "--require-prompts"])

    assert result.exit_code == 1
    assert "video-prompts" in result.output
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_repo_commands.py -v
```

Expected: FAIL because repo commands do not exist.

**Step 3: Implement registry/repo helpers**

Create `plotloom/toml_io.py`:

```python
def toml_str(value: object) -> str:
    s = str(value)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'
```

Create `plotloom/repo.py`:

```python
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from plotloom.toml_io import toml_str

SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TEXT_EXTS = {".md", ".toml", ".txt"}


@dataclass(frozen=True)
class RepoValidation:
    ok: bool
    missing: list[Path]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_template(src: Path, dst: Path, *, slug: str, title: str) -> None:
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.suffix in TEXT_EXTS:
            text = item.read_text(encoding="utf-8").replace("{{slug}}", slug).replace("{{title}}", title)
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(item, target)


def append_registry(registry: Path, *, slug: str, title: str, path: Path) -> None:
    registry.parent.mkdir(parents=True, exist_ok=True)
    entry = "\n".join([
        "[[repos]]",
        f"slug = {toml_str(slug)}",
        f"title = {toml_str(title)}",
        f"path = {toml_str(path)}",
        'status = "active"',
        "",
    ])
    text = registry.read_text(encoding="utf-8") if registry.exists() else "# Plotloom home repo registry\n\n"
    if f"slug = {toml_str(slug)}" in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    registry.write_text(text + entry, encoding="utf-8")


def init_repo(target: Path, *, slug: str, title: str, registry: Path | None = None) -> Path:
    if not SAFE_SLUG.match(slug):
        raise ValueError("invalid slug")
    if "\n" in title or "\r" in title:
        raise ValueError("invalid title")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(str(target))
    template = project_root() / "templates" / "series-repo"
    target.mkdir(parents=True, exist_ok=True)
    copy_template(template, target, slug=slug, title=title)
    if registry:
        append_registry(registry, slug=slug, title=title, path=target)
    return target


def validate_repo(repo: Path, *, episode: str | None = None, require_prompts: bool = False, require_media: bool = False) -> RepoValidation:
    missing: list[Path] = []
    for rel in ("series.md", "characters.md", "episodes"):
        path = repo / rel
        if not path.exists():
            missing.append(path)
    if episode:
        ep_dir = repo / "episodes" / episode
        if not ep_dir.exists():
            missing.append(ep_dir)
        if require_prompts:
            for name in ("video-prompts.md", "video-prompts-en.md"):
                if not (ep_dir / name).exists():
                    missing.append(ep_dir / name)
        if require_media and not (ep_dir / "videos").exists():
            missing.append(ep_dir / "videos")
    return RepoValidation(ok=not missing, missing=missing)


def find_repo_from_cwd(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for path in [current, *current.parents]:
        if (path / "series.md").exists():
            return path
    return None
```

**Step 4: Implement repo Click commands**

Create `plotloom/commands/repo.py`:

```python
from __future__ import annotations

from pathlib import Path

import click

from plotloom.config import load_config
from plotloom.output import emit
from plotloom.repo import init_repo, validate_repo


@click.command("init")
@click.argument("slug")
@click.option("--title", required=True)
@click.option("--path", "path_value")
@click.option("--no-registry", is_flag=True)
@click.pass_context
def init_command(ctx: click.Context, slug: str, title: str, path_value: str | None, no_registry: bool) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    target = Path(path_value).expanduser() if path_value else cfg.repos_root / slug
    repo = init_repo(target.resolve(), slug=slug, title=title, registry=None if no_registry else cfg.registry_path)
    emit({"ok": True, "command": "repo.init", "repo": str(repo), "message": f"created series repo: {repo}"}, as_json=ctx.obj.get("as_json"))


@click.command("validate")
@click.option("--episode")
@click.option("--require-prompts", is_flag=True)
@click.option("--require-media", is_flag=True)
@click.pass_context
def validate_command(ctx: click.Context, episode: str | None, require_prompts: bool, require_media: bool) -> None:
    repo_arg = ctx.obj.get("repo")
    if not repo_arg:
        raise click.ClickException("--repo is required until discovery is implemented")
    result = validate_repo(Path(repo_arg).expanduser().resolve(), episode=episode, require_prompts=require_prompts, require_media=require_media)
    if not result.ok:
        raise click.ClickException("missing required Plotloom paths:\n" + "\n".join(str(p) for p in result.missing))
    emit({"ok": True, "command": "repo.validate", "repo": str(Path(repo_arg).expanduser().resolve()), "message": "repo ok"}, as_json=ctx.obj.get("as_json"))
```

Modify `plotloom/cli.py`:

```python
from plotloom.commands.repo import init_command, validate_command

main.add_command(init_command)
main.add_command(validate_command)
```

**Step 5: Run tests**

Run:

```bash
python3 -m pytest tests/test_repo_commands.py tests/test_config.py tests/test_cli_basic.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add plotloom tests/test_repo_commands.py
git commit -m "feat: add repo init and validation commands"
```

## Task 4: Repo Discovery And `repos` Registry Commands

**Files:**
- Modify: `plotloom/repo.py`
- Create: `plotloom/commands/repos.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_repos_commands.py`

**Step 1: Write failing registry tests**

Create `tests/test_repos_commands.py`:

```python
from click.testing import CliRunner

from plotloom.cli import main


def test_repos_list_reads_registry(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    repo = tmp_path / "series"
    repo.mkdir()
    config.write_text(f'[plotloom]\nregistry_path = "{registry}"\n', encoding="utf-8")
    registry.write_text(
        f'[[repos]]\nslug = "demo"\ntitle = "Demo"\npath = "{repo}"\nstatus = "active"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--config", str(config), "repos", "list"])

    assert result.exit_code == 0
    assert "demo" in result.output


def test_repos_resolve_fails_for_missing_path(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    config.write_text(f'[plotloom]\nregistry_path = "{registry}"\n', encoding="utf-8")
    registry.write_text('[[repos]]\nslug = "demo"\ntitle = "Demo"\npath = "/no/such/path"\nstatus = "active"\n', encoding="utf-8")

    result = CliRunner().invoke(main, ["--config", str(config), "repos", "resolve", "demo"])

    assert result.exit_code == 1
    assert "missing" in result.output.lower()
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_repos_commands.py -v
```

Expected: FAIL because `repos` command does not exist.

**Step 3: Add registry helpers**

Modify `plotloom/repo.py`:

```python
import tomllib
from typing import Any


def read_registry(registry: Path) -> list[dict[str, Any]]:
    if not registry.exists():
        return []
    data = tomllib.loads(registry.read_text(encoding="utf-8"))
    return list(data.get("repos", []))


def write_registry(registry: Path, repos: list[dict[str, Any]]) -> None:
    import tomli_w

    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(tomli_w.dumps({"repos": repos}), encoding="utf-8")


def resolve_registry_repo(registry: Path, slug: str | None = None) -> Path:
    repos = [r for r in read_registry(registry) if r.get("status", "active") == "active"]
    if slug:
        repos = [r for r in read_registry(registry) if r.get("slug") == slug]
    if not repos:
        raise FileNotFoundError("no matching active repo")
    if len(repos) > 1:
        raise RuntimeError("multiple active repos")
    path = Path(str(repos[0]["path"])).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"registered repo path is missing: {path}")
    return path.resolve()
```

**Step 4: Add `repos` commands**

Create `plotloom/commands/repos.py`:

```python
from __future__ import annotations

from pathlib import Path

import click

from plotloom.config import load_config
from plotloom.output import emit
from plotloom.repo import append_registry, read_registry, resolve_registry_repo, write_registry


@click.group("repos")
def repos_group() -> None:
    """Manage Plotloom repo registry."""


@repos_group.command("list")
@click.option("--status", "status_filter", default="active")
@click.pass_context
def list_repos(ctx: click.Context, status_filter: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    repos = read_registry(cfg.registry_path)
    if status_filter != "all":
        repos = [r for r in repos if r.get("status", "active") == status_filter]
    if ctx.obj.get("as_json"):
        emit({"ok": True, "command": "repos.list", "repos": repos}, as_json=True)
        return
    for repo in repos:
        click.echo(f"{repo.get('slug')}\t{repo.get('status', 'active')}\t{repo.get('path')}\t{repo.get('title')}")


@repos_group.command("add")
@click.argument("slug")
@click.option("--title", required=True)
@click.option("--path", "path_value", required=True)
@click.option("--status", "status_value", default="active")
@click.pass_context
def add_repo(ctx: click.Context, slug: str, title: str, path_value: str, status_value: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    append_registry(cfg.registry_path, slug=slug, title=title, path=Path(path_value).expanduser().resolve())
    repos = read_registry(cfg.registry_path)
    for repo in repos:
        if repo.get("slug") == slug:
            repo["status"] = status_value
    write_registry(cfg.registry_path, repos)
    emit({"ok": True, "command": "repos.add", "message": f"repo added: {slug}"}, as_json=ctx.obj.get("as_json"))


@repos_group.command("set-status")
@click.argument("slug")
@click.argument("status_value")
@click.pass_context
def set_status(ctx: click.Context, slug: str, status_value: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    repos = read_registry(cfg.registry_path)
    for repo in repos:
        if repo.get("slug") == slug:
            repo["status"] = status_value
            write_registry(cfg.registry_path, repos)
            emit({"ok": True, "command": "repos.set-status", "message": f"{slug}: {status_value}"}, as_json=ctx.obj.get("as_json"))
            return
    raise click.ClickException(f"repo not found: {slug}")


@repos_group.command("remove")
@click.argument("slug")
@click.pass_context
def remove_repo(ctx: click.Context, slug: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    repos = [r for r in read_registry(cfg.registry_path) if r.get("slug") != slug]
    write_registry(cfg.registry_path, repos)
    emit({"ok": True, "command": "repos.remove", "message": f"registry entry removed: {slug}"}, as_json=ctx.obj.get("as_json"))


@repos_group.command("resolve")
@click.argument("slug", required=False)
@click.pass_context
def resolve_repo(ctx: click.Context, slug: str | None) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    try:
        path = resolve_registry_repo(cfg.registry_path, slug)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    emit({"ok": True, "command": "repos.resolve", "repo": str(path), "message": str(path)}, as_json=ctx.obj.get("as_json"))
```

Modify `plotloom/cli.py`:

```python
from plotloom.commands.repos import repos_group

main.add_command(repos_group)
```

**Step 5: Run tests**

Run:

```bash
python3 -m pytest tests/test_repos_commands.py tests/test_repo_commands.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add plotloom tests/test_repos_commands.py
git commit -m "feat: add repo registry commands"
```

## Task 5: Filesystem Paths, Candidate Numbering, And Selection

**Files:**
- Create: `plotloom/paths.py`
- Create: `plotloom/selection.py`
- Create: `plotloom/commands/select.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_selection.py`

**Step 1: Write failing selection tests**

Create `tests/test_selection.py`:

```python
from click.testing import CliRunner

from plotloom.cli import main
from plotloom.paths import next_candidate_path


def test_next_candidate_path_skips_adapter_suffixes(tmp_path):
    candidates = tmp_path / "candidates"
    candidates.mkdir()
    (candidates / "v001.dreamina-cli.mp4").write_text("x")
    (candidates / "v002.aliyun-bailian-wan.mp4").write_text("x")

    assert next_candidate_path(candidates, ".mp4", adapter="volcengine-seedance").name == "v003.volcengine-seedance.mp4"


def test_select_copies_and_backs_up(tmp_path):
    candidate = tmp_path / "candidates" / "v001.mp4"
    candidate.parent.mkdir()
    candidate.write_text("new")
    selected = tmp_path / "selected.mp4"
    selected.write_text("old")

    result = CliRunner().invoke(main, ["select", str(candidate)])

    assert result.exit_code == 0
    assert selected.read_text() == "new"
    assert list(tmp_path.glob("selected-prev-*.mp4"))
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_selection.py -v
```

Expected: FAIL because selection helpers do not exist.

**Step 3: Implement paths and selection**

Create `plotloom/paths.py`:

```python
from __future__ import annotations

import re
from pathlib import Path

VERSION_RE = re.compile(r"^v(\d{3})(?:\..+)?$")


def next_candidate_path(candidates_dir: Path, suffix: str, *, adapter: str | None = None) -> Path:
    candidates_dir.mkdir(parents=True, exist_ok=True)
    max_n = 0
    for path in candidates_dir.iterdir():
        match = VERSION_RE.match(path.name)
        if match:
            max_n = max(max_n, int(match.group(1)))
    stem = f"v{max_n + 1:03d}"
    if adapter:
        stem = f"{stem}.{adapter}"
    return candidates_dir / f"{stem}{suffix}"


def selected_for_candidate(candidate: Path) -> Path:
    if candidate.parent.name != "candidates":
        raise ValueError("candidate must live under a candidates directory")
    return candidate.parent.parent / f"selected{candidate.suffix}"
```

Create `plotloom/selection.py`:

```python
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from plotloom.paths import selected_for_candidate


def backup_path(selected: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return selected.with_name(f"{selected.stem}-prev-{ts}{selected.suffix}")


def select_candidate(candidate: Path) -> tuple[Path, Path | None]:
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(str(candidate))
    selected = selected_for_candidate(candidate)
    selected.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if selected.exists():
        backup = backup_path(selected)
        shutil.copy2(selected, backup)
    shutil.copy2(candidate, selected)
    return selected, backup
```

Create `plotloom/commands/select.py`:

```python
from __future__ import annotations

from pathlib import Path

import click

from plotloom.output import emit
from plotloom.selection import select_candidate


@click.command("select")
@click.argument("candidate")
@click.pass_context
def select_command(ctx: click.Context, candidate: str) -> None:
    try:
        selected, backup = select_candidate(Path(candidate).expanduser().resolve())
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    emit(
        {
            "ok": True,
            "command": "select",
            "selected_path": str(selected),
            "backup_path": str(backup) if backup else None,
            "message": f"selected: {selected}",
        },
        as_json=ctx.obj.get("as_json"),
    )
```

Modify `plotloom/cli.py`:

```python
from plotloom.commands.select import select_command

main.add_command(select_command)
```

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_selection.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_selection.py
git commit -m "feat: add candidate selection helpers"
```

## Task 6: Media Probe, Check, Normalize Command Shell

**Files:**
- Create: `plotloom/media.py`
- Create: `plotloom/commands/media.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_media.py`

**Step 1: Write failing media tests using monkeypatch**

Create `tests/test_media.py`:

```python
import json
import subprocess

from plotloom.media import probe_media


def test_probe_media_parses_ffprobe_json(monkeypatch, tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"x")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=json.dumps({
                "streams": [
                    {"codec_type": "video", "codec_name": "h264", "width": 720, "height": 1280, "avg_frame_rate": "24/1"},
                    {"codec_type": "audio", "codec_name": "aac"},
                ],
                "format": {"duration": "5.000000", "format_name": "mov,mp4,m4a,3gp,3g2,mj2"},
            }),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    facts = probe_media(video)

    assert facts.duration == 5.0
    assert facts.width == 720
    assert facts.height == 1280
    assert facts.has_audio is True
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_media.py -v
```

Expected: FAIL because `plotloom.media` does not exist.

**Step 3: Implement probe helper and CLI**

Create `plotloom/media.py`:

```python
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaFacts:
    path: str
    duration: float | None
    width: int | None
    height: int | None
    fps: float | None
    has_audio: bool
    video_codec: str | None
    audio_codec: str | None
    format_name: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _fps(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" in value:
        num, den = value.split("/", 1)
        return float(num) / float(den)
    return float(value)


def probe_media(path: Path) -> MediaFacts:
    if not path.exists():
        raise FileNotFoundError(str(path))
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    data = json.loads(proc.stdout or "{}")
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    return MediaFacts(
        path=str(path),
        duration=float(data.get("format", {}).get("duration")) if data.get("format", {}).get("duration") else None,
        width=video.get("width"),
        height=video.get("height"),
        fps=_fps(video.get("avg_frame_rate")),
        has_audio=bool(audio),
        video_codec=video.get("codec_name"),
        audio_codec=audio.get("codec_name"),
        format_name=data.get("format", {}).get("format_name"),
    )
```

Create `plotloom/commands/media.py`:

```python
from __future__ import annotations

from pathlib import Path

import click

from plotloom.media import probe_media
from plotloom.output import emit


@click.group("media")
def media_group() -> None:
    """Probe and validate media."""


@media_group.command("probe")
@click.argument("path")
@click.pass_context
def probe_command(ctx: click.Context, path: str) -> None:
    facts = probe_media(Path(path).expanduser().resolve())
    emit({"ok": True, "command": "media.probe", **facts.to_dict(), "message": f"media: {facts.path}"}, as_json=ctx.obj.get("as_json"))
```

Modify `plotloom/cli.py`:

```python
from plotloom.commands.media import media_group

main.add_command(media_group)
```

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_media.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_media.py
git commit -m "feat: add media probe helper"
```

## Task 7: Prompt Parsing, Extract, Check, Compile

**Files:**
- Create: `plotloom/prompts.py`
- Create: `plotloom/commands/prompt.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_prompts.py`

**Step 1: Write failing prompt tests**

Create `tests/test_prompts.py`:

```python
from plotloom.prompts import compile_prompt, extract_clip_prompt, list_clips


PROMPTS = """
# EP001 Video Prompts EN

## Clip 01

Duration hint: 5 seconds
Ratio: 9:16

Prompt string:
A vertical short-drama shot in a rainy lobby. Dialogue: "You are the heir." No subtitles.

Reference images:
- assets/cast/lin-qiao/character-grid.png

## Clip 02

Prompt string:
A second clip.
"""


def test_list_clips():
    assert list_clips(PROMPTS) == ["clip-01", "clip-02"]


def test_extract_clip_prompt_string():
    prompt = extract_clip_prompt(PROMPTS, "clip-01")

    assert prompt.startswith("A vertical short-drama")
    assert "Reference images" not in prompt


def test_compile_aliyun_reference_prompt_preserves_story_text():
    compiled = compile_prompt(PROMPTS, "clip-01", adapter="aliyun-bailian-wan", mode="reference-to-video")

    assert "rainy lobby" in compiled.prompt_text
    assert compiled.prompt_chars == len(compiled.prompt_text)
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_prompts.py -v
```

Expected: FAIL because `plotloom.prompts` does not exist.

**Step 3: Implement minimal parser/compiler**

Create `plotloom/prompts.py`:

```python
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

CLIP_HEADING = re.compile(r"^##\s+(Clip\s+\d+|clip-\d+)\s*$", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class CompiledPrompt:
    prompt_text: str
    prompt_sha256: str
    prompt_chars: int
    warnings: list[str]


def _slug_clip(value: str) -> str:
    value = value.strip().lower().replace("clip ", "clip-")
    if re.fullmatch(r"clip-\d+", value):
        head, num = value.split("-", 1)
        return f"{head}-{int(num):02d}"
    return value


def _sections(text: str) -> dict[str, str]:
    matches = list(CLIP_HEADING.finditer(text))
    result: dict[str, str] = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[_slug_clip(match.group(1))] = text[start:end].strip()
    return result


def list_clips(text: str) -> list[str]:
    return list(_sections(text).keys())


def extract_clip_prompt(text: str, clip: str) -> str:
    section = _sections(text).get(clip)
    if not section:
        raise KeyError(clip)
    marker = re.search(r"^Prompt string:\s*$", section, re.IGNORECASE | re.MULTILINE)
    if marker:
        body = section[marker.end():].strip()
        stop = re.search(r"^(Reference images:|Duration hint:|Ratio:|Ending frame:)", body, re.IGNORECASE | re.MULTILINE)
        return body[: stop.start()].strip() if stop else body.strip()
    paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
    return paragraphs[-1]


def compile_prompt(text: str, clip: str, *, adapter: str, mode: str) -> CompiledPrompt:
    prompt = extract_clip_prompt(text, clip)
    warnings: list[str] = []
    if adapter == "aliyun-bailian-wan" and mode in {"image-to-video", "reference-to-video"}:
        prompt = "Use the provided image URLs as first-frame or character-reference intent according to request metadata.\n" + prompt
    if adapter == "volcengine-seedance" and mode in {"image-to-video", "reference-to-video"}:
        prompt = "Use attached image roles according to the request metadata.\n" + prompt
    if not prompt:
        raise ValueError("compiled prompt is empty")
    return CompiledPrompt(
        prompt_text=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        prompt_chars=len(prompt),
        warnings=warnings,
    )
```

Create `plotloom/commands/prompt.py` with `list`, `extract`, `compile`, and `check` wrappers calling these functions.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_prompts.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_prompts.py
git commit -m "feat: add prompt extraction and compile helpers"
```

## Task 8: Video Types, Capabilities, And Validation

**Files:**
- Create: `plotloom/video/__init__.py`
- Create: `plotloom/video/types.py`
- Create: `plotloom/video/capabilities.py`
- Test: `tests/test_video_types.py`

**Step 1: Write failing type tests**

Create `tests/test_video_types.py`:

```python
from pathlib import Path

from plotloom.video.capabilities import capabilities_for, validate_request
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_video_request_defaults():
    req = PlotloomVideoRequest(
        repo=Path("/tmp/series"),
        episode="ep001",
        clip="clip-01",
        adapter="dreamina-cli",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file=Path("episodes/ep001/video-prompts-en.md"),
        prompt_text="prompt",
        ratio="9:16",
        resolution="720p",
        duration=5,
    )

    assert req.audio_intent == "native_if_supported"
    assert req.reference_images == []


def test_aliyun_bailian_rejects_too_long_prompt():
    req = PlotloomVideoRequest(
        repo=Path("/tmp/series"),
        episode="ep001",
        clip="clip-01",
        adapter="aliyun-bailian-wan",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file=Path("p.md"),
        prompt_text="x" * 5001,
        ratio="9:16",
        resolution="720p",
        duration=5,
    )

    result = validate_request(req, capabilities_for("aliyun-bailian-wan"))

    assert not result.ok
    assert result.issues[0].code == "PROMPT_TOO_LONG"
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_video_types.py -v
```

Expected: FAIL because video types do not exist.

**Step 3: Implement video contracts**

Create `plotloom/video/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal


class VideoMode(StrEnum):
    TEXT_TO_VIDEO = "text-to-video"
    IMAGE_TO_VIDEO = "image-to-video"
    REFERENCE_TO_VIDEO = "reference-to-video"
    VIDEO_EDIT = "video-edit"


AudioIntent = Literal["none", "native_if_supported", "require_native"]


@dataclass(frozen=True)
class PlotloomVideoRequest:
    repo: Path
    episode: str
    clip: str
    adapter: str
    mode: VideoMode
    prompt_file: Path
    prompt_text: str
    ratio: str
    resolution: str
    duration: int
    audio_intent: AudioIntent = "native_if_supported"
    seed: int | None = None
    first_frame: Path | None = None
    reference_images: list[Path] = field(default_factory=list)
    reference_videos: list[Path] = field(default_factory=list)
    source_video: Path | None = None
    allow_downgrade: bool = False
    allow_normalize_duration: bool = False


@dataclass(frozen=True)
class VideoAdapterCapabilities:
    adapter: str
    modes: set[str]
    min_duration: int
    max_duration: int
    ratios: set[str]
    resolutions: set[str]
    max_prompt_chars: int | None
    supports_native_audio: bool
    supports_seed: bool
    supports_first_frame: bool
    supports_reference_images: bool
    supports_video_edit: bool


@dataclass(frozen=True)
class ValidationIssue:
    level: Literal["error", "warning"]
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)
```

Create `plotloom/video/capabilities.py` with hardcoded MVP capabilities and validation for mode, duration, ratio, resolution, prompt length, first frame, reference images, and downgrade flags.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_video_types.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video tests/test_video_types.py
git commit -m "feat: add video request validation contracts"
```

## Task 9: TOML Receipts And Latest Pointer

**Files:**
- Create: `plotloom/video/receipts.py`
- Test: `tests/test_video_receipts.py`

**Step 1: Write failing receipt tests**

Create `tests/test_video_receipts.py`:

```python
from pathlib import Path

from plotloom.video.receipts import Receipt, receipt_path, write_latest_pointer, write_receipt


def test_write_receipt_and_latest_pointer(tmp_path):
    path = receipt_path(tmp_path, "ep001", "clip-01", "volcengine-seedance", "cgt-123")
    receipt = Receipt(
        adapter="volcengine-seedance",
        provider="volcengine",
        provider_task_id="cgt-123",
        status="queued",
        repo=str(tmp_path),
        episode="ep001",
        clip="clip-01",
        mode="text-to-video",
        prompt_file="episodes/ep001/video-prompts-en.md",
        compiled_prompt_sha256="abc",
        prompt_chars=10,
        duration=5,
        ratio="9:16",
        resolution="720p",
        audio_intent="native_if_supported",
        credential_source="config",
    )

    write_receipt(path, receipt)
    write_latest_pointer(path, receipt)

    assert path.exists()
    latest = tmp_path / "episodes" / "ep001" / "videos" / "clip-01" / "latest-task.toml"
    assert latest.exists()
    assert "tasks/volcengine-seedance-cgt-123.toml" in latest.read_text()
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_video_receipts.py -v
```

Expected: FAIL because receipts do not exist.

**Step 3: Implement receipt helpers**

Create `plotloom/video/receipts.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tomli_w


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class Receipt:
    adapter: str
    provider: str
    provider_task_id: str
    status: str
    repo: str
    episode: str
    clip: str
    mode: str
    prompt_file: str
    compiled_prompt_sha256: str
    prompt_chars: int
    duration: int
    ratio: str
    resolution: str
    audio_intent: str
    credential_source: str
    receipt_version: int = 1
    submitted_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    candidate_path: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    next_step: str | None = None
    provider_data: dict[str, Any] = field(default_factory=dict)
    media: dict[str, Any] = field(default_factory=dict)

    def to_toml(self) -> dict[str, Any]:
        data = {k: v for k, v in asdict(self).items() if v is not None}
        if "provider_data" in data:
            data["provider"] = data.pop("provider_data")
        return data


def receipt_path(repo: Path, episode: str, clip: str, adapter: str, provider_task_id: str) -> Path:
    safe_id = provider_task_id.replace("/", "-").replace(":", "-")
    return repo / "episodes" / episode / "videos" / clip / "tasks" / f"{adapter}-{safe_id}.toml"


def write_receipt(path: Path, receipt: Receipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps(receipt.to_toml()), encoding="utf-8")


def write_latest_pointer(path: Path, receipt: Receipt) -> None:
    latest = path.parent.parent / "latest-task.toml"
    relative = path.relative_to(latest.parent)
    latest.write_text(
        tomli_w.dumps({
            "receipt": str(relative),
            "adapter": receipt.adapter,
            "provider_task_id": receipt.provider_task_id,
            "status": receipt.status,
            "updated_at": receipt.updated_at,
        }),
        encoding="utf-8",
    )
```

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_video_receipts.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/receipts.py tests/test_video_receipts.py
git commit -m "feat: add video task receipts"
```

## Task 10: Mock Video Adapter And Video Submit/Poll Shell

**Files:**
- Create: `plotloom/video/adapters/__init__.py`
- Create: `plotloom/video/adapters/base.py`
- Create: `plotloom/video/adapters/mock.py`
- Create: `plotloom/commands/video.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_video_mock.py`

**Step 1: Write failing mock video CLI test**

Create `tests/test_video_mock.py`:

```python
from click.testing import CliRunner

from plotloom.cli import main


def test_video_submit_mock_writes_receipt_and_candidate(tmp_path):
    repo = tmp_path / "series"
    ep = repo / "episodes" / "ep001"
    ep.mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n")
    (repo / "characters.md").write_text("# Characters\n")
    (ep / "video-prompts-en.md").write_text("## Clip 01\n\nPrompt string:\nA fake clip.\n")

    result = CliRunner().invoke(
        main,
        ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"],
    )

    assert result.exit_code == 0
    assert list((ep / "videos" / "clip-01" / "tasks").glob("mock-*.toml"))
    assert list((ep / "videos" / "clip-01" / "candidates").glob("v001.mock.mp4"))
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_video_mock.py -v
```

Expected: FAIL because video command and mock adapter do not exist.

**Step 3: Implement adapter base and mock**

Create `plotloom/video/adapters/base.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from plotloom.video.types import PlotloomVideoRequest, ValidationResult, VideoAdapterCapabilities


@dataclass(frozen=True)
class VideoSubmitResult:
    adapter: str
    provider: str
    provider_task_id: str
    status: str
    local_path: Path | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoTaskStatus:
    adapter: str
    provider_task_id: str
    status: str
    video_url: str | None = None
    local_path: Path | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class VideoAdapter(Protocol):
    name: str
    provider: str

    def capabilities(self) -> VideoAdapterCapabilities: ...
    def validate_request(self, request: PlotloomVideoRequest) -> ValidationResult: ...
    def submit(self, request: PlotloomVideoRequest, *, candidate_path: Path) -> VideoSubmitResult: ...
    def poll(self, provider_task_id: str, *, download_dir: Path) -> VideoTaskStatus: ...
```

Create `plotloom/video/adapters/mock.py`:

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from plotloom.video.adapters.base import VideoSubmitResult, VideoTaskStatus
from plotloom.video.capabilities import capabilities_for, validate_request
from plotloom.video.types import PlotloomVideoRequest


class MockVideoAdapter:
    name = "mock"
    provider = "local"

    def capabilities(self):
        return capabilities_for("mock")

    def validate_request(self, request: PlotloomVideoRequest):
        return validate_request(request, self.capabilities())

    def submit(self, request: PlotloomVideoRequest, *, candidate_path: Path) -> VideoSubmitResult:
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        fixture = Path(__file__).resolve().parents[3] / "examples" / "fixtures" / "fake-video.mp4"
        if fixture.exists():
            shutil.copy2(fixture, candidate_path)
        else:
            candidate_path.write_bytes(b"mock video placeholder")
        return VideoSubmitResult(adapter=self.name, provider=self.provider, provider_task_id="local", status="local", local_path=candidate_path)

    def poll(self, provider_task_id: str, *, download_dir: Path) -> VideoTaskStatus:
        return VideoTaskStatus(adapter=self.name, provider_task_id=provider_task_id, status="local")
```

**Step 4: Implement `video submit` skeleton**

Create `plotloom/commands/video.py` with `video submit` that:

1. resolves `--repo`;
2. reads `episodes/<ep>/video-prompts-en.md`;
3. compiles prompt;
4. builds `PlotloomVideoRequest`;
5. chooses adapter from a registry containing `mock`;
6. writes candidate to `candidates/vNNN.mock.mp4`;
7. writes receipt and latest pointer.

Use `plotloom.paths.next_candidate_path`, `plotloom.video.receipts`, and `plotloom.prompts.compile_prompt`.

**Step 5: Run tests**

Run:

```bash
python3 -m pytest tests/test_video_mock.py tests/test_video_receipts.py tests/test_prompts.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add plotloom tests/test_video_mock.py
git commit -m "feat: add mock video submit flow"
```

## Task 11: Codex Image Adapter From `codex-imagegen2-api`

**Files:**
- Create: `plotloom/images.py`
- Create: `plotloom/adapters/__init__.py`
- Create: `plotloom/adapters/image_codex_app_server.py`
- Create: `plotloom/commands/image.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_image_codex_adapter.py`

**Step 1: Write failing image adapter tests with monkeypatch**

Create `tests/test_image_codex_adapter.py`:

```python
import subprocess

from plotloom.adapters.image_codex_app_server import CodexImageAdapter


def test_codex_image_adapter_copies_result(monkeypatch, tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"png")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("make an image")
    out_dir = tmp_path / "out"

    def fake_run(*args, **kwargs):
        result_path = [str(x) for x in args[0]][args[0].index("--output-last-message") + 1]
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(f'{{"image_path": "{source}", "notes": "ok"}}')
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/codex")

    result = CodexImageAdapter().generate(prompt_file=prompt, output_dir=out_dir, filename="cover.png", images=[], timeout=10)

    assert result["ok"] is True
    assert (out_dir / "cover.png").exists()
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_image_codex_adapter.py -v
```

Expected: FAIL because image adapter does not exist.

**Step 3: Port the local JSON API pattern**

Implement `plotloom/adapters/image_codex_app_server.py` by porting the safe parts of `T0UGH/agent-skills/codex-imagegen2-api/scripts/codex_imagegen2.py`:

- `codex_bin()`
- prompt loading from `--prompt-file`
- optional `--image` validation
- JSON schema requiring `image_path` and `notes`
- `codex exec --skip-git-repo-check --sandbox read-only --enable image_generation --output-schema ... --output-last-message ...`
- JSON extraction from result file/stdout
- fallback to newest `$CODEX_HOME/generated_images` only if JSON is missing
- copy into target output dir
- return `ok`, `image_path`, `image_url`, `source_image_path`, `notes`, `input_images`, `codex_exit_code`

**Step 4: Add `image generate` command**

Implement `plotloom/commands/image.py`:

```bash
plotloom image generate --kind cast --character SLUG --prompt-file PATH [--image PATH ...]
plotloom image generate --kind cover --episode ep001 --prompt-file PATH [--image PATH ...]
```

Path mapping:

- cast -> `assets/cast/<character>/character-grid.png`
- scene -> `assets/scenes/<scene>/candidates/vNNN.png`
- cover -> `episodes/<ep>/images/covers/candidates/vNNN.png`
- reference -> `episodes/<ep>/images/references/<clip>/candidates/vNNN.png`

**Step 5: Run tests**

Run:

```bash
python3 -m pytest tests/test_image_codex_adapter.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add plotloom tests/test_image_codex_adapter.py
git commit -m "feat: add codex image generation adapter"
```

## Task 12: Dreamina CLI Adapter

**Files:**
- Create: `plotloom/video/adapters/dreamina_cli.py`
- Modify: `plotloom/commands/video.py`
- Test: `tests/test_dreamina_adapter.py`

**Step 1: Write failing Dreamina adapter tests**

Create `tests/test_dreamina_adapter.py`:

```python
import subprocess

from plotloom.video.adapters.dreamina_cli import DreaminaCliAdapter
from plotloom.video.types import PlotloomVideoRequest, VideoMode
from pathlib import Path


def test_dreamina_submit_parses_submit_id(monkeypatch, tmp_path):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout='{"submit_id":"sub_123"}', stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    req = PlotloomVideoRequest(
        repo=tmp_path,
        episode="ep001",
        clip="clip-01",
        adapter="dreamina-cli",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file=Path("p.md"),
        prompt_text="prompt",
        ratio="9:16",
        resolution="720p",
        duration=5,
    )

    result = DreaminaCliAdapter(binary="dreamina", home="~").submit(req, candidate_path=tmp_path / "v001.mp4")

    assert result.provider_task_id == "sub_123"
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_dreamina_adapter.py -v
```

Expected: FAIL because Dreamina adapter does not exist.

**Step 3: Implement Dreamina submit/poll**

Implement:

- `text-to-video` -> `dreamina text2video --prompt ... --duration ... --ratio ... --video_resolution ... --model_version seedance2.0fast --poll=0`
- `image-to-video` -> `dreamina image2video --image ... --prompt ... --duration ... --video_resolution ... --model_version seedance2.0fast --poll=0`
- parse `submit_id` from JSON or regex fallback.
- `poll` -> `dreamina query_result --submit_id ... --download_dir <candidate-dir>`.
- Normalize downloaded file name to `vNNN.dreamina-cli.mp4` in `video poll`.

Do not auto-login. `doctor` reports login/credit issues only.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_dreamina_adapter.py tests/test_video_mock.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/adapters/dreamina_cli.py tests/test_dreamina_adapter.py
git commit -m "feat: add dreamina video adapter"
```

## Task 13: Aliyun Bailian Wan Adapter

**Files:**
- Create: `plotloom/video/adapters/aliyun_bailian_wan.py`
- Modify: `plotloom/commands/video.py`
- Test: `tests/test_aliyun_bailian_wan_adapter.py`

**Step 1: Write failing Bailian tests using fake HTTP client**

Create `tests/test_aliyun_bailian_wan_adapter.py`:

```python
from pathlib import Path

from plotloom.video.adapters.aliyun_bailian_wan import AliyunBailianWanAdapter
from plotloom.video.types import PlotloomVideoRequest, VideoMode


class FakeHTTP:
    def post(self, url, headers, json, timeout):
        self.url = url
        self.headers = headers
        self.json = json
        return type("Resp", (), {"status_code": 200, "json": lambda self: {"output": {"task_id": "task_123"}}})()


def test_aliyun_bailian_submit_returns_task_id(tmp_path):
    fake = FakeHTTP()
    adapter = AliyunBailianWanAdapter(http=fake, dashscope_api_key="secret")
    req = PlotloomVideoRequest(
        repo=tmp_path,
        episode="ep001",
        clip="clip-01",
        adapter="aliyun-bailian-wan",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file=Path("p.md"),
        prompt_text="prompt",
        ratio="9:16",
        resolution="720p",
        duration=5,
    )

    result = adapter.submit(req, candidate_path=tmp_path / "v001.mp4")

    assert result.provider_task_id == "task_123"
    assert fake.url.endswith("/services/aigc/video-generation/video-synthesis")
    assert fake.headers["X-DashScope-Async"] == "enable"
    assert fake.headers["Authorization"] == "Bearer secret"
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_aliyun_bailian_wan_adapter.py -v
```

Expected: FAIL because adapter does not exist.

**Step 3: Implement Aliyun Bailian Wan adapter**

Implement HTTP task submit against DashScope Model Studio:

- default `base_url`: `https://dashscope.aliyuncs.com/api/v1`
- `text-to-video`: `POST /services/aigc/video-generation/video-synthesis`
- header `X-DashScope-Async: enable`
- header `Authorization: Bearer <DASHSCOPE_API_KEY>`
- default model: `wan2.6-t2v` unless config overrides it.
- payload: `{"model": model, "input": {"prompt": req.prompt_text}, "parameters": {"size": size_for(req), "prompt_extend": true, "watermark": false}}`

Implement local input handling:

- Bailian video APIs prefer HTTP URLs for image/video inputs. In this phase, reject local-only `first_frame`, `reference_images`, and `source_video` unless they have already been imported to a reachable URL or a later asset upload step provides one.
- Map `image-to-video` only after confirming the exact Bailian Wan endpoint/body in the referenced docs; do not reuse fal/Horse parameter names.
- Treat `reference-to-video` as provider-specific VACE/reference mode only after a small docs/API spike confirms the endpoint and body shape.

Implement poll:

- `GET /tasks/{task_id}` with `Authorization: Bearer <DASHSCOPE_API_KEY>`.
- normalize DashScope task statuses into Plotloom receipt statuses.
- return the temporary output video URL and download it immediately during `video poll`.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_aliyun_bailian_wan_adapter.py tests/test_video_types.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/adapters/aliyun_bailian_wan.py tests/test_aliyun_bailian_wan_adapter.py
git commit -m "feat: add aliyun bailian wan video adapter"
```

## Task 14: VolcEngine Seedance Adapter

**Files:**
- Create: `plotloom/video/adapters/volcengine_seedance.py`
- Modify: `plotloom/commands/video.py`
- Test: `tests/test_volcengine_adapter.py`

**Step 1: Write failing VolcEngine adapter test**

Create `tests/test_volcengine_adapter.py`:

```python
from pathlib import Path

from plotloom.video.adapters.volcengine_seedance import VolcEngineSeedanceAdapter
from plotloom.video.types import PlotloomVideoRequest, VideoMode


class FakeTasks:
    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Task", (), {"id": "cgt_123"})()


class FakeContentGeneration:
    def __init__(self):
        self.tasks = FakeTasks()


class FakeClient:
    def __init__(self):
        self.content_generation = FakeContentGeneration()


def test_volcengine_submit_returns_task_id(tmp_path):
    client = FakeClient()
    adapter = VolcEngineSeedanceAdapter(client=client, model="doubao-seedance-2-0-260128")
    req = PlotloomVideoRequest(
        repo=tmp_path,
        episode="ep001",
        clip="clip-01",
        adapter="volcengine-seedance",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file=Path("p.md"),
        prompt_text="prompt",
        ratio="9:16",
        resolution="720p",
        duration=5,
    )

    result = adapter.submit(req, candidate_path=tmp_path / "v001.mp4")

    assert result.provider_task_id == "cgt_123"
    assert client.content_generation.tasks.kwargs["watermark"] is False
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_volcengine_adapter.py -v
```

Expected: FAIL because adapter does not exist.

**Step 3: Implement VolcEngine adapter**

Implement:

- client constructor from `volcenginesdkarkruntime import Ark`.
- submit via `client.content_generation.tasks.create(...)`.
- `content=[{"type":"text","text": prompt}]` for T2V.
- add image URL content roles for image/reference modes when URLs are provided.
- parameters: model, ratio, resolution, duration, `generate_audio`, `watermark=False`, `return_last_frame=True`.
- poll via `client.content_generation.tasks.get(task_id=...)`.
- normalize statuses and return `video_url`.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_volcengine_adapter.py tests/test_video_types.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/adapters/volcengine_seedance.py tests/test_volcengine_adapter.py
git commit -m "feat: add volcengine seedance video adapter"
```

## Task 15: Video Poll Download, Media Probe, And Compare

**Files:**
- Modify: `plotloom/commands/video.py`
- Create: `plotloom/video/downloads.py`
- Create: `plotloom/video/compare.py`
- Test: `tests/test_video_poll_compare.py`

**Step 1: Write failing poll/compare tests**

Create `tests/test_video_poll_compare.py`:

```python
from plotloom.video.compare import compare_receipts


def test_compare_receipts_keeps_adapter_status(tmp_path):
    receipt = tmp_path / "r.toml"
    receipt.write_text(
        'adapter = "mock"\nstatus = "succeeded"\ncandidate_path = "episodes/ep001/videos/clip-01/candidates/v001.mock.mp4"\n',
        encoding="utf-8",
    )

    rows = compare_receipts([receipt])

    assert rows[0]["adapter"] == "mock"
    assert rows[0]["status"] == "succeeded"
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_video_poll_compare.py -v
```

Expected: FAIL because compare helper does not exist.

**Step 3: Implement download and compare helpers**

Create `plotloom/video/downloads.py`:

```python
from __future__ import annotations

from pathlib import Path

import requests


def download_url(url: str, dest: Path, *, timeout: int = 600) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with dest.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return dest
```

Create `plotloom/video/compare.py`:

```python
from __future__ import annotations

import tomllib
from pathlib import Path


def compare_receipts(receipts: list[Path]) -> list[dict[str, object]]:
    rows = []
    for path in receipts:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        rows.append({
            "adapter": data.get("adapter"),
            "mode": data.get("mode"),
            "status": data.get("status"),
            "candidate_path": data.get("candidate_path"),
            "duration": data.get("media", {}).get("duration") if isinstance(data.get("media"), dict) else None,
            "has_audio": data.get("media", {}).get("has_audio") if isinstance(data.get("media"), dict) else None,
            "failure_mode": data.get("error_code"),
        })
    return rows
```

Update `video poll`:

- read receipt or latest pointer;
- call adapter `poll`;
- if `video_url` exists, download to next candidate path;
- run `probe_media`;
- update receipt `status`, `candidate_path`, `media`;
- update latest pointer.

Add `video compare`.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_video_poll_compare.py tests/test_video_mock.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video plotloom/commands/video.py tests/test_video_poll_compare.py
git commit -m "feat: add video polling and comparison"
```

## Task 16: Asset Import And Image/Asset List Info Commands

**Files:**
- Create: `plotloom/assets.py`
- Create: `plotloom/commands/asset.py`
- Modify: `plotloom/commands/image.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_assets.py`

**Step 1: Write failing asset import tests**

Create `tests/test_assets.py`:

```python
from click.testing import CliRunner

from plotloom.cli import main


def test_asset_import_cover_candidate(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes" / "ep001").mkdir(parents=True)
    image = tmp_path / "cover.png"
    image.write_bytes(b"png")

    result = CliRunner().invoke(
        main,
        ["--repo", str(repo), "asset", "import", "--kind", "cover", "--episode", "ep001", "--file", str(image), "--candidate"],
    )

    assert result.exit_code == 0
    assert (repo / "episodes" / "ep001" / "images" / "covers" / "candidates" / "v001.png").exists()
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_assets.py -v
```

Expected: FAIL because asset commands do not exist.

**Step 3: Implement asset path mapping and import**

Create `plotloom/assets.py` with functions:

- `asset_candidate_dir(repo, kind, episode=None, clip=None, character=None, scene=None)`
- `import_asset(file, target_dir, adapter=None)`
- `info(path)` returning path, suffix, size.

Create `plotloom/commands/asset.py` with `asset import`, `asset list`, `asset info`.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_assets.py tests/test_selection.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_assets.py
git commit -m "feat: add asset import commands"
```

## Task 17: Stitch Command

**Files:**
- Create: `plotloom/stitch.py`
- Create: `plotloom/commands/stitch.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_stitch.py`

**Step 1: Write failing stitch planning test**

Create `tests/test_stitch.py`:

```python
from plotloom.stitch import discover_selected_clips


def test_discover_selected_clips_in_lexical_order(tmp_path):
    videos = tmp_path / "episodes" / "ep001" / "videos"
    (videos / "clip-02").mkdir(parents=True)
    (videos / "clip-01").mkdir(parents=True)
    (videos / "clip-02" / "selected.mp4").write_bytes(b"2")
    (videos / "clip-01" / "selected.mp4").write_bytes(b"1")

    clips = discover_selected_clips(tmp_path, "ep001")

    assert [p.parent.name for p in clips] == ["clip-01", "clip-02"]
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_stitch.py -v
```

Expected: FAIL because stitch helper does not exist.

**Step 3: Implement stitch helper and command**

Create `plotloom/stitch.py`:

- `discover_selected_clips(repo, episode)`;
- `stitch_clips(clips, output, normalize=False, resolution="720p", fps=24)` based on existing `scripts/stitch_ffmpeg.py`;
- use `ffprobe` before and after.

Create `plotloom/commands/stitch.py`:

```bash
plotloom stitch --episode ep001 [--output PATH] [--clips clip-01,clip-02] [--normalize]
plotloom stitch plan --episode ep001
```

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_stitch.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_stitch.py
git commit -m "feat: add stitch command"
```

## Task 18: Doctor Commands

**Files:**
- Create: `plotloom/doctor.py`
- Create: `plotloom/commands/doctor.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_doctor.py`

**Step 1: Write failing doctor tests**

Create `tests/test_doctor.py`:

```python
from plotloom.doctor import redact_present


def test_redact_present_never_returns_secret():
    assert redact_present("abc123", source="env") == "present via env"
    assert "abc" not in redact_present("abc123", source="env")
    assert redact_present("", source="config") == "absent"
```

**Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_doctor.py -v
```

Expected: FAIL because doctor helper does not exist.

**Step 3: Implement doctor helpers**

Create `plotloom/doctor.py`:

```python
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
```

Create `plotloom/commands/doctor.py` with:

```bash
plotloom doctor --adapter all|codex-app-server|dreamina-cli|aliyun-bailian-wan|volcengine-seedance --deep
```

Checks:

- config parse and permissions;
- `codex`, `dreamina`, `ffmpeg`, `ffprobe` binaries;
- `dashscope` and `volcenginesdkarkruntime` imports;
- secret presence only as present/absent.

No paid provider submit in doctor.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_doctor.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_doctor.py
git commit -m "feat: add doctor checks"
```

## Task 19: Delivery Summary

**Files:**
- Create: `plotloom/delivery.py`
- Create: `plotloom/commands/delivery.py`
- Modify: `plotloom/cli.py`
- Test: `tests/test_delivery.py`

**Step 1: Write failing delivery test**

Create `tests/test_delivery.py`:

```python
from plotloom.delivery import episode_files


def test_episode_files_lists_final_and_selected(tmp_path):
    videos = tmp_path / "episodes" / "ep001" / "videos"
    (videos / "clip-01").mkdir(parents=True)
    (videos / "clip-01" / "selected.mp4").write_bytes(b"x")
    (videos / "final.mp4").write_bytes(b"x")

    files = episode_files(tmp_path, "ep001")

    assert "episodes/ep001/videos/final.mp4" in files
    assert "episodes/ep001/videos/clip-01/selected.mp4" in files
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_delivery.py -v
```

Expected: FAIL because delivery helper does not exist.

**Step 3: Implement delivery summary**

Create `plotloom/delivery.py`:

```python
from __future__ import annotations

from pathlib import Path


def episode_files(repo: Path, episode: str) -> list[str]:
    ep = repo / "episodes" / episode
    files = []
    for rel in [
        Path("videos/final.mp4"),
    ]:
        path = ep / rel
        if path.exists():
            files.append(str(path.relative_to(repo)))
    for selected in sorted((ep / "videos").glob("clip-*/selected.mp4")):
        files.append(str(selected.relative_to(repo)))
    return files
```

Create `plotloom/commands/delivery.py`:

```bash
plotloom delivery summary --episode ep001 [--include-candidates] [--output PATH]
plotloom delivery files --episode ep001
```

Default writes stdout only. If `--output` is passed, write to the explicit path.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_delivery.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_delivery.py
git commit -m "feat: add delivery summary commands"
```

## Task 20: Compatibility Wrappers For Existing Scripts

**Files:**
- Modify: `scripts/init_series.py`
- Modify: `scripts/validate_repo.py`
- Modify: `scripts/select_candidate.py`
- Modify: `scripts/ffprobe_media.py`
- Modify: `scripts/stitch_ffmpeg.py`
- Test: `tests/test_script_compat.py`

**Step 1: Write compatibility tests**

Create `tests/test_script_compat.py`:

```python
import subprocess
import sys


def test_validate_repo_script_still_runs(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n")
    (repo / "characters.md").write_text("# Characters\n")

    result = subprocess.run(
        [sys.executable, "scripts/validate_repo.py", "--repo", str(repo)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0
```

**Step 2: Run tests**

Run:

```bash
python3 -m pytest tests/test_script_compat.py -v
```

Expected: PASS before and after wrapper changes.

**Step 3: Refactor scripts carefully**

Keep public script arguments stable. Internally call package helpers where low risk:

- `validate_repo.py` -> `plotloom.repo.validate_repo`
- `select_candidate.py` -> `plotloom.selection.select_candidate`
- `ffprobe_media.py` -> `plotloom.media.probe_media`

Do not refactor `fake_video.py` or `stitch_ffmpeg.py` unless tests cover equivalent behavior.

**Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_script_compat.py tests/test_selection.py tests/test_media.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts tests/test_script_compat.py
git commit -m "refactor: share cli helpers with scripts"
```

## Task 21: Manual Provider Smoke Documentation

**Files:**
- Create: `docs/runbooks/plotloom-provider-smoke.md`
- Modify: `README.md`

**Step 1: Write the runbook**

Create `docs/runbooks/plotloom-provider-smoke.md` with:

- prerequisite checklist for `dreamina-cli`, `aliyun-bailian-wan`, `volcengine-seedance`;
- exact `plotloom config doctor` commands;
- exact text-to-video smoke commands;
- exact poll commands;
- expected receipt/candidate paths;
- cost guardrails for Aliyun Bailian and VolcEngine;
- failure stop conditions;
- reminder that provider smoke is manual, not default pytest.

Use commands from `docs/design/2026-04-30-plotloom-cli-contract-details.md`.

**Step 2: Link from README**

Modify `README.md` Real Adapters section:

```markdown
Manual provider smoke tests are documented in `docs/runbooks/plotloom-provider-smoke.md`.
```

**Step 3: Verify links**

Run:

```bash
test -f docs/runbooks/plotloom-provider-smoke.md
rg -n "plotloom-provider-smoke" README.md
```

Expected: both commands succeed.

**Step 4: Commit**

```bash
git add README.md docs/runbooks/plotloom-provider-smoke.md
git commit -m "docs: add provider smoke runbook"
```

## Task 22: Full Local E2E With Mock

**Files:**
- Create: `tests/test_cli_e2e_mock.py`

**Step 1: Write E2E test**

Create `tests/test_cli_e2e_mock.py`:

```python
from click.testing import CliRunner

from plotloom.cli import main


def test_cli_mock_e2e_without_real_providers(tmp_path):
    config = tmp_path / ".plotloom" / ".env.toml"
    config.parent.mkdir()
    repos_root = tmp_path / "repos"
    registry = tmp_path / "plotloom.toml"
    config.write_text(f'[plotloom]\nrepos_root = "{repos_root}"\nregistry_path = "{registry}"\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config), "init", "fake-heiress", "--title", "Fake Heiress"])
    assert result.exit_code == 0

    repo = repos_root / "fake-heiress"
    ep = repo / "episodes" / "ep001"
    (ep / "video-prompts-en.md").write_text("## Clip 01\n\nPrompt string:\nA mock clip.\n", encoding="utf-8")

    result = runner.invoke(main, ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"])
    assert result.exit_code == 0

    candidate = next((ep / "videos" / "clip-01" / "candidates").glob("v001.mock.mp4"))
    result = runner.invoke(main, ["select", str(candidate)])
    assert result.exit_code == 0
    assert (ep / "videos" / "clip-01" / "selected.mp4").exists()
```

**Step 2: Run E2E test**

Run:

```bash
python3 -m pytest tests/test_cli_e2e_mock.py -v
```

Expected: PASS without calling real providers.

**Step 3: Run full unit test suite**

Run:

```bash
python3 -m pytest -v
```

Expected: PASS.

**Step 4: Commit**

```bash
git add tests/test_cli_e2e_mock.py
git commit -m "test: add mock cli e2e"
```

## Task 23: Final Verification And Cleanup

**Files:**
- Modify only if verification reveals issues.

**Step 1: Run repository validation**

Run:

```bash
python scripts/validate_repo.py --repo examples/tiny-series --require-video-prompts
```

Expected: `ok: .../examples/tiny-series`.

**Step 2: Run full tests**

Run:

```bash
python3 -m pytest -v
```

Expected: PASS.

**Step 3: Run CLI help checks**

Run:

```bash
python3 -m plotloom.cli --help
python3 -m plotloom.cli config --help
python3 -m plotloom.cli video --help
```

Expected: each command exits 0 and prints help.

If `python3 -m plotloom.cli` does not work because Click entrypoint is only exposed through `plotloom`, add:

```python
if __name__ == "__main__":
    main()
```

to `plotloom/cli.py`, then rerun.

**Step 4: Run manual smoke only if user explicitly provides credentials/login**

Manual commands:

```bash
plotloom doctor --adapter dreamina-cli --deep
plotloom doctor --adapter aliyun-bailian-wan --deep
plotloom doctor --adapter volcengine-seedance --deep
```

Do not run paid submit/poll unless the user explicitly asks.

**Step 5: Commit final fixes**

```bash
git status --short
git add <only files changed for final fixes>
git commit -m "chore: finalize plotloom cli implementation"
```

## Execution Notes

- Keep each task commit small. If a task reveals a design mismatch, update the relevant design doc in a separate docs commit before continuing.
- Do not commit local `~/.plotloom/.env.toml`, generated videos, generated images, provider URLs, or credentials.
- Do not run real provider smoke in pytest.
- For real provider smoke, use the runbook and ask the user before submitting paid jobs.
