# AGENTS.md

This file provides guidance to Codex and other coding agents when working with code in this repository.

## Common Commands

Dev environment uses `uv` (Python ≥ 3.11):

```bash
uv sync --extra dev                    # install dev deps (pytest, ruff)
uv sync --extra volcengine             # add VolcEngine SDK
uv run pytest                          # run full test suite
uv run pytest tests/test_cli_basic.py  # single file
uv run pytest -k test_cli_version_runs # single test
uv run ruff check plotloom tests       # lint
```

Build/publish check:

```bash
uv build
uv publish --dry-run --check-url https://pypi.org/simple/ dist/*
```

PyPI does not allow re-publishing the same version — bump `pyproject.toml` `version` before any release.

The CLI is exposed as the `plotloom` console script (`plotloom.cli:main`). Smoke a development build with `uvx plotloom --help` or `pip install -e . && plotloom --help`.

## Architecture

Plotloom is **repo-first, prompt-first, adapter-thin**: every step of short-drama production becomes a reviewable file in a series repo (`series.md`, `characters.md`, `episodes/epXXX/video-prompts.md`, `candidates/`, `selected.*`, `final.mp4`). The CLI never owns hidden state — no DB, no queue worker, no dashboard. When making changes, preserve those boundaries: state belongs in files inside the user's series repo, not in the CLI process.

### Two products in one repo

1. **`plotloom/` Python package** — the CLI. Subcommand groups live in `plotloom/commands/{asset,config,delivery,doctor,image,media,prompt,repo,repos,select,stitch,video}.py`, all wired into the root group in `plotloom/cli.py`. Domain logic (paths, repo template, prompts, media, selection, stitch, output formatting) lives in sibling modules under `plotloom/`.
2. **`skills/`** — agent-neutral Skill packs (`SKILL.md` + templates + references) installed into hosts like Codex and Claude Code via `npx skills add ...`. Skills are **not** Python and have no runtime coupling to the CLI; they describe how an agent should use the CLI and edit repo files. Modifying CLI contracts (file layout, command flags, JSON shapes) usually means a matching skill update.

### Video adapter layer

The video pipeline is the most extension-heavy area. Contracts:

- `plotloom/video/types.py` — `PlotloomVideoRequest`, `VideoMode`, `VideoAdapterCapabilities`, `ValidationResult`. These are the boundary types every adapter speaks.
- `plotloom/video/adapters/base.py` — `VideoAdapter` Protocol with `capabilities() / validate_request() / submit() / poll()`, plus result dataclasses.
- Implementations: `mock.py`, `dreamina_cli.py`, `volcengine_seedance.py`. They are dispatched in `plotloom/commands/video.py::_adapter` based on a string name. To add a new video provider: implement the Protocol, register it in `_adapter`, add capability/validation tests, and update `default_video_adapters` in `plotloom/config.py::DEFAULT_TEMPLATE`.
- Image adapters live in `plotloom/adapters/` (currently `image_codex_app_server.py`).

`plotloom/video/{capabilities,compare,downloads,receipts}.py` are shared video utilities — receipts/`tasks/*.toml` are the on-disk source of truth for any in-flight provider task.

### CLI conventions

- `PlotloomGroup` in `cli.py` normalizes `--json` (which can appear anywhere) and centralizes error rendering. All user-facing failures should raise `PlotloomError` (or one of its subclasses in `plotloom/errors.py`: `ConfigError`, `ProviderError`, `MediaValidationError`) — they carry `code`, `exit_code`, and optional `next_step` and are rendered consistently in both human and `--json` modes.
- Top-level options (`--repo`, `--config`, `--json`, `--quiet`, `--dry-run`) are stashed on the Click context's `obj` dict and read by subcommands. New subcommands should follow the same pattern instead of redefining these flags.
- Tests use `click.testing.CliRunner` — see `tests/test_cli_basic.py` and `tests/test_cli_e2e_mock.py` for the conventional shape (invoke `main`, parse JSON or check exit code).

### Config layering

`plotloom/config.py` resolves values from **env var > `~/.plotloom/.env.toml` > built-in default** in that order. `ENV_MAP` maps `(dotted_section, key)` to env var names; when adding a new adapter setting that should be env-overridable, add an entry to `ENV_MAP`. `doctor` must never print credential values — only their presence.

### Series repo template

`plotloom/templates/series-repo/` is the canonical series repo template. `plotloom.repo.template_root()` resolves this packaged template source; `pyproject.toml` `[tool.setuptools.package-data]` enumerates the files explicitly, so new template files need to be listed there too or they will not ship.

### Documentation layout

All design notes live under `docs/` (adapter specs, host integrations, runbooks, decisions, research). Keep root-level docs limited to `README.md` and packaging metadata; add new adapter or host docs under `docs/adapters/` or `docs/hosts/` and index them from `docs/README.md`.
