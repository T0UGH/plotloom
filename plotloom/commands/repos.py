from __future__ import annotations

from pathlib import Path

import click

from plotloom.config import load_config
from plotloom.output import emit
from plotloom.repo import RegistryError, append_registry, read_registry, resolve_registry_repo, write_registry


@click.group("repos")
def repos_group() -> None:
    """Manage Plotloom repo registry."""


@repos_group.command("list")
@click.option("--status", "status_filter", default="active", show_default=True)
@click.pass_context
def list_repos(ctx: click.Context, status_filter: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    try:
        repos = read_registry(cfg.registry_path)
    except RegistryError as error:
        raise click.ClickException(str(error)) from error

    if status_filter != "all":
        repos = [repo for repo in repos if repo.get("status", "active") == status_filter]
    if ctx.obj.get("as_json"):
        emit({"ok": True, "command": "repos.list", "repos": repos}, as_json=True)
        return

    for repo in repos:
        click.echo(
            "\t".join(
                [
                    str(repo.get("slug", "")),
                    str(repo.get("status", "active")),
                    str(repo.get("path", "")),
                    str(repo.get("title", "")),
                ]
            )
        )


@repos_group.command("add")
@click.argument("slug")
@click.option("--title", required=True)
@click.option("--path", "path_value", required=True)
@click.option("--status", "status_value", default="active", show_default=True)
@click.pass_context
def add_repo(ctx: click.Context, slug: str, title: str, path_value: str, status_value: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    path = Path(path_value).expanduser().resolve()
    try:
        append_registry(cfg.registry_path, slug=slug, title=title, path=path, status=status_value)
    except (RegistryError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    emit(
        {"ok": True, "command": "repos.add", "repo": str(path), "message": f"repo added: {slug}"},
        as_json=ctx.obj.get("as_json"),
    )


@repos_group.command("set-status")
@click.argument("slug")
@click.argument("status_value")
@click.pass_context
def set_status(ctx: click.Context, slug: str, status_value: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    try:
        repos = read_registry(cfg.registry_path)
        for repo in repos:
            if repo.get("slug") == slug:
                repo["status"] = status_value
                write_registry(cfg.registry_path, repos)
                emit(
                    {"ok": True, "command": "repos.set-status", "message": f"{slug}: {status_value}"},
                    as_json=ctx.obj.get("as_json"),
                )
                return
    except RegistryError as error:
        raise click.ClickException(str(error)) from error
    raise click.ClickException(f"repo not found: {slug}")


@repos_group.command("remove")
@click.argument("slug")
@click.pass_context
def remove_repo(ctx: click.Context, slug: str) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    try:
        repos = read_registry(cfg.registry_path)
        kept = [repo for repo in repos if repo.get("slug") != slug]
        if len(kept) == len(repos):
            raise click.ClickException(f"repo not found: {slug}")
        write_registry(cfg.registry_path, kept)
    except RegistryError as error:
        raise click.ClickException(str(error)) from error
    emit(
        {"ok": True, "command": "repos.remove", "message": f"registry entry removed: {slug}"},
        as_json=ctx.obj.get("as_json"),
    )


@repos_group.command("resolve")
@click.argument("slug", required=False)
@click.pass_context
def resolve_repo(ctx: click.Context, slug: str | None) -> None:
    cfg = load_config(ctx.obj.get("config_path"))
    try:
        path = resolve_registry_repo(cfg.registry_path, slug)
    except (FileNotFoundError, RegistryError, RuntimeError) as error:
        raise click.ClickException(str(error)) from error
    emit(
        {"ok": True, "command": "repos.resolve", "repo": str(path), "message": str(path)},
        as_json=ctx.obj.get("as_json"),
    )
