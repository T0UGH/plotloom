from __future__ import annotations

from pathlib import Path

import click

from plotloom.output import emit
from plotloom.selection import select_candidate


@click.command("select")
@click.argument("candidate", type=click.Path(path_type=str))
@click.pass_context
def select_command(ctx: click.Context, candidate: str) -> None:
    """Copy a candidate media file to its selected sibling."""
    try:
        result = select_candidate(Path(candidate))
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error

    backup_path = str(result.backup_path) if result.backup_path else None
    message = f"selected candidate: {result.selected_path}"
    if backup_path:
        message = f"{message} (backup: {backup_path})"
    emit(
        {
            "ok": True,
            "command": "select",
            "selected_path": str(result.selected_path),
            "backup_path": backup_path,
            "message": message,
        },
        as_json=ctx.obj.get("as_json"),
    )
