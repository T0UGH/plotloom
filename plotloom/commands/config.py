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
    emit(
        {"ok": True, "command": "config.path", "path": str(cfg.path), "message": str(cfg.path)},
        as_json=ctx.obj.get("as_json"),
    )


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
    emit(
        {"ok": True, "command": "config.init", "path": str(cfg.path), "message": f"config: {cfg.path}"},
        as_json=ctx.obj.get("as_json"),
    )


@config_group.command("doctor")
@click.option("--adapter", default="all")
@click.pass_context
def config_doctor(ctx: click.Context, adapter: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    warning = permission_warning(cfg.path)
    data = {
        "ok": warning is None,
        "command": "config.doctor",
        "path": str(cfg.path),
        "adapter": adapter,
        "warnings": [warning] if warning else [],
    }
    emit({**data, "message": "config ok" if data["ok"] else warning}, as_json=ctx.obj.get("as_json"))
