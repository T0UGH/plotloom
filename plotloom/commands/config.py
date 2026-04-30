from __future__ import annotations

import importlib.util
import shutil
from typing import Any

import click
import tomli_w

from plotloom.config import DEFAULT_TEMPLATE, load_config, permission_warning, resolve_config_path, write_default_config
from plotloom.output import emit

KNOWN_ADAPTERS = ("codex-app-server", "dreamina-cli", "volcengine-seedance")
ADAPTER_CHOICES = (*KNOWN_ADAPTERS, "all")


@click.group(name="config")
def config_group() -> None:
    """Manage Plotloom local config."""


@config_group.command("path")
@click.pass_context
def config_path(ctx: click.Context) -> None:
    cfg_path = resolve_config_path(ctx.obj.get("config_path"))
    if ctx.obj.get("as_json"):
        emit({"ok": True, "command": "config.path", "config_path": str(cfg_path)}, as_json=True)
        return
    click.echo(str(cfg_path))


@config_group.command("init")
@click.option("--force", is_flag=True)
@click.option("--print-template", "print_template", is_flag=True)
@click.pass_context
def config_init(ctx: click.Context, force: bool, print_template: bool) -> None:
    if print_template:
        click.echo(tomli_w.dumps(DEFAULT_TEMPLATE))
        return

    cfg_path = resolve_config_path(ctx.obj.get("config_path"))
    write_default_config(cfg_path, force=force)
    emit(
        {"ok": True, "command": "config.init", "path": str(cfg_path), "message": f"config: {cfg_path}"},
        as_json=ctx.obj.get("as_json"),
    )


def _dependency_check(module_name: str) -> dict[str, str]:
    return {"status": "available" if importlib.util.find_spec(module_name) else "missing"}


def _binary_check(binary: str | None) -> dict[str, str]:
    if not binary:
        return {"status": "absent"}
    return {"status": "available" if shutil.which(binary) else "missing"}


def _secret_check(source: str) -> dict[str, str]:
    if source == "absent":
        return {"status": "absent"}
    return {"status": "present", "source": source}


def _check_adapter(cfg: Any, adapter: str) -> dict[str, dict[str, str]]:
    if adapter == "codex-app-server":
        return {"codex_binary": _binary_check(cfg.adapter_value(adapter, "codex_binary", "codex"))}
    if adapter == "dreamina-cli":
        return {"binary": _binary_check(cfg.adapter_value(adapter, "binary", "dreamina"))}
    if adapter == "volcengine-seedance":
        return {
            "ark_api_key": _secret_check(cfg.value_source("adapters.volcengine-seedance", "ark_api_key")),
            "volcenginesdkarkruntime": _dependency_check("volcenginesdkarkruntime"),
        }
    raise ValueError(adapter)


def _unknown_adapter_warnings(cfg: Any) -> list[str]:
    adapters = cfg.data.get("adapters", {})
    if not isinstance(adapters, dict):
        return []
    unknown = sorted(name for name in adapters if name not in KNOWN_ADAPTERS)
    return [f"unknown adapter section: {name}" for name in unknown]


def _has_failure(checks: dict[str, Any]) -> bool:
    for value in checks.values():
        if isinstance(value, dict):
            if value.get("status") in {"absent", "missing"}:
                return True
            if _has_failure(value):
                return True
    return False


@config_group.command("doctor")
@click.option("--adapter", type=click.Choice(ADAPTER_CHOICES), default="all")
@click.pass_context
def config_doctor(ctx: click.Context, adapter: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    warning = permission_warning(cfg.path)
    warnings = [warning] if warning else []
    warnings.extend(_unknown_adapter_warnings(cfg))
    if adapter == "all":
        checks = {
            "permission": {"status": "warning" if warning else "ok"},
            **{current: _check_adapter(cfg, current) for current in KNOWN_ADAPTERS},
        }
    else:
        checks = {"permission": {"status": "warning" if warning else "ok"}, **_check_adapter(cfg, adapter)}
    failed = warning is not None or _has_failure(checks)
    data = {
        "ok": not failed,
        "command": "config.doctor",
        "path": str(cfg.path),
        "adapter": adapter,
        "checks": checks,
        "warnings": warnings,
    }
    emit(
        {**data, "message": "config ok" if data["ok"] else "config check failed"},
        as_json=ctx.obj.get("as_json"),
    )
    if failed:
        ctx.exit(2)
