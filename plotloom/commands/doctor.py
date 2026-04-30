from __future__ import annotations

import click

from plotloom.config import load_config, permission_warning
from plotloom.doctor import binary_status, import_status, redact_present
from plotloom.output import emit

ADAPTERS = ("codex-app-server", "dreamina-cli", "volcengine-seedance")


@click.command("doctor")
@click.option("--adapter", type=click.Choice((*ADAPTERS, "all")), default="all", show_default=True)
@click.option("--deep", is_flag=True)
@click.pass_context
def doctor_command(ctx: click.Context, adapter: str, deep: bool) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    warning = permission_warning(cfg.path)
    checks: dict[str, object] = {"config": {"path": str(cfg.path), "permission": "warning" if warning else "ok"}}
    selected = ADAPTERS if adapter == "all" else (adapter,)
    for current in selected:
        checks[current] = _adapter_checks(cfg, current, deep=deep)
    failed = warning is not None or _has_failure(checks)
    emit(
        {
            "ok": not failed,
            "command": "doctor",
            "adapter": adapter,
            "checks": checks,
            "warnings": [warning] if warning else [],
            "message": "doctor ok" if not failed else "doctor found missing prerequisites",
        },
        as_json=ctx.obj.get("as_json"),
    )
    if failed:
        ctx.exit(2)


def _adapter_checks(cfg, adapter: str, *, deep: bool) -> dict[str, object]:
    if adapter == "codex-app-server":
        checks: dict[str, object] = {"codex": binary_status(cfg.adapter_value(adapter, "codex_binary", "codex"))}
    elif adapter == "dreamina-cli":
        checks = {"dreamina": binary_status(cfg.adapter_value(adapter, "binary", "dreamina"))}
    elif adapter == "volcengine-seedance":
        source = cfg.value_source("adapters.volcengine-seedance", "ark_api_key")
        value = cfg.adapter_value("volcengine-seedance", "ark_api_key", "")
        checks = {
            "ark_api_key": {"status": redact_present(value, source=source if source != "absent" else "config")},
            "requests": import_status("requests"),
        }
        if deep:
            checks["volcenginesdkarkruntime"] = import_status("volcenginesdkarkruntime")
    else:
        raise ValueError(adapter)
    if deep:
        checks["ffmpeg"] = binary_status("ffmpeg")
        checks["ffprobe"] = binary_status("ffprobe")
    return checks


def _has_failure(checks: dict[str, object]) -> bool:
    for value in checks.values():
        if isinstance(value, dict):
            if value.get("ok") is False or value.get("status") == "absent":
                return True
            if _has_failure(value):
                return True
    return False
