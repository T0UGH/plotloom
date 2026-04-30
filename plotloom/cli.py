from __future__ import annotations

import json
import re
import sys

import click

from plotloom import __version__
from plotloom.errors import PlotloomError


def _error_code(error: click.ClickException) -> str:
    name = error.__class__.__name__
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()


def _wants_json(args: list[str]) -> bool:
    return "--json" in args


def _normalize_json_args(args: list[str]) -> list[str]:
    if "--json" not in args or "--help" in args or "-h" in args or "--version" in args:
        return args
    normalized = [arg for arg in args if arg != "--json"]
    return ["--json", *normalized]


def _attempted_command(args: list[str]) -> str:
    options_with_values = {"--repo", "--config"}
    flag_options = {"--json", "--quiet", "--dry-run", "-h", "--help"}
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg in options_with_values:
            skip_next = True
            continue
        if arg in flag_options:
            continue
        if arg.startswith("-"):
            continue
        return arg
    return "unknown"


def _exit_code(error: click.ClickException) -> int:
    if isinstance(error, click.UsageError):
        return 1
    return error.exit_code


class PlotloomGroup(click.Group):
    def main(
        self,
        args: list[str] | tuple[str, ...] | None = None,
        prog_name: str | None = None,
        complete_var: str | None = None,
        standalone_mode: bool = True,
        windows_expand_args: bool = True,
        **extra: object,
    ) -> object:
        args_list = list(sys.argv[1:] if args is None else args)
        normalized_args = _normalize_json_args(args_list)
        try:
            return super().main(
                args=normalized_args,
                prog_name=prog_name,
                complete_var=complete_var,
                standalone_mode=False,
                windows_expand_args=windows_expand_args,
                **extra,
            )
        except PlotloomError as error:
            if _wants_json(args_list):
                payload = {
                    "ok": False,
                    "command": _attempted_command(normalized_args),
                    "error": {
                        "code": error.code,
                        "message": error.message,
                    },
                }
                if error.next_step:
                    payload["error"]["next_step"] = error.next_step
                click.echo(json.dumps(payload, ensure_ascii=False))
            else:
                click.echo(f"Error: {error.message}", err=True)
                if error.next_step:
                    click.echo(f"Next step: {error.next_step}", err=True)
            if standalone_mode:
                sys.exit(error.exit_code)
            raise
        except click.ClickException as error:
            if _wants_json(args_list):
                click.echo(
                    json.dumps(
                        {
                            "ok": False,
                            "command": _attempted_command(args_list),
                            "error": {
                                "code": _error_code(error),
                                "message": error.format_message(),
                            },
                        },
                        ensure_ascii=False,
                    )
                )
            else:
                error.show()
            if standalone_mode:
                sys.exit(_exit_code(error))
            raise
        except click.exceptions.Exit as error:
            if standalone_mode:
                sys.exit(error.exit_code)
            raise


@click.group(cls=PlotloomGroup, context_settings={"help_option_names": ["-h", "--help"]})
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


from plotloom.commands.config import config_group  # noqa: E402

main.add_command(config_group)
