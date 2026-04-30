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
