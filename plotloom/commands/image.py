from __future__ import annotations

from pathlib import Path

import click

from plotloom.adapters.image_codex_app_server import CodexImageAdapter
from plotloom.images import image_output_path
from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd

IMAGE_KINDS = ["cast", "scene", "cover", "reference"]


@click.group("image")
def image_group() -> None:
    """Generate and manage image assets."""


@image_group.command("generate")
@click.option("--kind", required=True, type=click.Choice(IMAGE_KINDS))
@click.option("--character")
@click.option("--scene")
@click.option("--episode")
@click.option("--clip")
@click.option("--prompt-file", required=True, type=click.Path(path_type=str))
@click.option("--image", "images", multiple=True, type=click.Path(path_type=str))
@click.option("--timeout", default=600, show_default=True, type=int)
@click.pass_context
def generate_command(
    ctx: click.Context,
    kind: str,
    character: str | None,
    scene: str | None,
    episode: str | None,
    clip: str | None,
    prompt_file: str,
    images: tuple[str, ...],
    timeout: int,
) -> None:
    repo = _repo_path(ctx)
    try:
        output_path = image_output_path(
            repo,
            kind=kind,
            character=character,
            scene=scene,
            episode=episode,
            clip=clip,
        )
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    result = CodexImageAdapter().generate(
        prompt_file=Path(prompt_file).expanduser(),
        output_dir=output_path.parent,
        filename=output_path.name,
        images=[Path(path).expanduser() for path in images],
        timeout=timeout,
    )
    emit(
        {
            "ok": True,
            "command": "image.generate",
            "kind": kind,
            "image_path": result["image_path"],
            "image_url": result["image_url"],
            "source_image_path": result["source_image_path"],
            "notes": result["notes"],
            "message": f"image generated: {result['image_path']}",
        },
        as_json=ctx.obj.get("as_json"),
    )


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo
