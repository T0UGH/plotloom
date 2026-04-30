from __future__ import annotations

from pathlib import Path

import click

from plotloom.assets import asset_candidate_dir, asset_info, import_asset, list_assets
from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd

ASSET_KINDS = ["cast", "scene", "cover", "reference", "video"]


@click.group("asset")
def asset_group() -> None:
    """Import and inspect local assets."""


@asset_group.command("import")
@click.option("--kind", required=True, type=click.Choice(ASSET_KINDS))
@click.option("--file", "file_path", required=True, type=click.Path(path_type=str))
@click.option("--episode")
@click.option("--clip")
@click.option("--character")
@click.option("--scene")
@click.option("--adapter")
@click.option("--candidate", is_flag=True)
@click.pass_context
def import_command(
    ctx: click.Context,
    kind: str,
    file_path: str,
    episode: str | None,
    clip: str | None,
    character: str | None,
    scene: str | None,
    adapter: str | None,
    candidate: bool,
) -> None:
    _ = candidate
    repo = _repo_path(ctx)
    try:
        target_dir = asset_candidate_dir(repo, kind, episode=episode, clip=clip, character=character, scene=scene)
        target = import_asset(Path(file_path), target_dir, adapter=adapter)
    except (FileNotFoundError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    emit(
        {
            "ok": True,
            "command": "asset.import",
            "path": str(target),
            "message": f"asset imported: {target}",
        },
        as_json=ctx.obj.get("as_json"),
    )


@asset_group.command("list")
@click.option("--kind", required=True, type=click.Choice(ASSET_KINDS))
@click.option("--episode")
@click.option("--clip")
@click.option("--character")
@click.option("--scene")
@click.pass_context
def list_command(
    ctx: click.Context,
    kind: str,
    episode: str | None,
    clip: str | None,
    character: str | None,
    scene: str | None,
) -> None:
    repo = _repo_path(ctx)
    try:
        target_dir = asset_candidate_dir(repo, kind, episode=episode, clip=clip, character=character, scene=scene)
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    assets = list_assets(target_dir)
    emit(
        {
            "ok": True,
            "command": "asset.list",
            "assets": assets,
            "message": "\n".join(str(asset["path"]) for asset in assets) or "no assets found",
        },
        as_json=ctx.obj.get("as_json"),
    )


@asset_group.command("info")
@click.argument("path", type=click.Path(path_type=str))
@click.pass_context
def info_command(ctx: click.Context, path: str) -> None:
    info = asset_info(Path(path))
    emit(
        {
            "ok": info["exists"],
            "command": "asset.info",
            "asset": info,
            "message": f"{info['path']}: {info['size']} bytes" if info["exists"] else f"asset not found: {info['path']}",
        },
        as_json=ctx.obj.get("as_json"),
    )
    if not info["exists"]:
        ctx.exit(1)


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo
