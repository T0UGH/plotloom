from __future__ import annotations

from pathlib import Path

import click

from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd
from plotloom.stitch import discover_selected_clips, stitch_clips


@click.group("stitch", invoke_without_command=True)
@click.option("--episode")
@click.option("--output", "output_path", type=click.Path(path_type=str))
@click.option("--clips")
@click.option("--normalize", is_flag=True)
@click.option("--resolution", default="720p", show_default=True)
@click.option("--fps", default=24, show_default=True, type=int)
@click.pass_context
def stitch_group(
    ctx: click.Context,
    episode: str | None,
    output_path: str | None,
    clips: str | None,
    normalize: bool,
    resolution: str,
    fps: int,
) -> None:
    """Stitch selected clips into a final video."""
    if ctx.invoked_subcommand is not None:
        return
    if not episode:
        raise click.ClickException("--episode is required")
    repo = _repo_path(ctx)
    selected = discover_selected_clips(repo, episode, _split_clips(clips))
    output = Path(output_path).expanduser() if output_path else repo / "episodes" / episode / "videos" / "final.mp4"
    try:
        final = stitch_clips(selected, output, normalize=normalize, resolution=resolution, fps=fps)
    except (RuntimeError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    emit(
        {
            "ok": True,
            "command": "stitch",
            "final_path": str(final),
            "clips": [str(path) for path in selected],
            "message": f"final: {final}",
        },
        as_json=ctx.obj.get("as_json"),
    )


@stitch_group.command("plan")
@click.option("--episode", required=True)
@click.option("--clips")
@click.pass_context
def plan_command(ctx: click.Context, episode: str, clips: str | None) -> None:
    repo = _repo_path(ctx)
    selected = discover_selected_clips(repo, episode, _split_clips(clips))
    emit(
        {
            "ok": bool(selected),
            "command": "stitch.plan",
            "clips": [str(path) for path in selected],
            "message": "\n".join(str(path) for path in selected) or "no selected clips found",
        },
        as_json=ctx.obj.get("as_json"),
    )
    if not selected:
        ctx.exit(1)


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo


def _split_clips(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]
