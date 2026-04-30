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
    try:
        repo = init_repo(target.resolve(), slug=slug, title=title, registry=None if no_registry else cfg.registry_path)
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    except FileExistsError as error:
        raise click.ClickException(f"target repo is not empty: {error}") from error

    emit(
        {"ok": True, "command": "repo.init", "repo": str(repo), "message": f"created series repo: {repo}"},
        as_json=ctx.obj.get("as_json"),
    )


@click.command("validate")
@click.option("--episode")
@click.option("--require-prompts", is_flag=True)
@click.option("--require-media", is_flag=True)
@click.pass_context
def validate_command(ctx: click.Context, episode: str | None, require_prompts: bool, require_media: bool) -> None:
    repo_arg = ctx.obj.get("repo")
    if not repo_arg:
        raise click.ClickException("--repo is required until discovery is implemented")

    repo = Path(repo_arg).expanduser().resolve()
    result = validate_repo(repo, episode=episode, require_prompts=require_prompts, require_media=require_media)
    if not result.ok:
        raise click.ClickException("missing required Plotloom paths:\n" + "\n".join(str(path) for path in result.missing))

    emit(
        {"ok": True, "command": "repo.validate", "repo": str(repo), "message": "repo ok"},
        as_json=ctx.obj.get("as_json"),
    )
