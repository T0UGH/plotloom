from __future__ import annotations

from pathlib import Path

import click

from plotloom.delivery import delivery_summary, episode_files
from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd


@click.group("delivery")
def delivery_group() -> None:
    """Summarize delivery artifacts."""


@delivery_group.command("files")
@click.option("--episode", required=True)
@click.option("--include-candidates", is_flag=True)
@click.pass_context
def files_command(ctx: click.Context, episode: str, include_candidates: bool) -> None:
    repo = _repo_path(ctx)
    files = episode_files(repo, episode, include_candidates=include_candidates)
    emit(
        {"ok": True, "command": "delivery.files", "files": files, "message": "\n".join(files) or "no delivery files found"},
        as_json=ctx.obj.get("as_json"),
    )


@delivery_group.command("summary")
@click.option("--episode", required=True)
@click.option("--include-candidates", is_flag=True)
@click.option("--output", "output_path", type=click.Path(path_type=str))
@click.pass_context
def summary_command(ctx: click.Context, episode: str, include_candidates: bool, output_path: str | None) -> None:
    repo = _repo_path(ctx)
    text = delivery_summary(repo, episode, include_candidates=include_candidates)
    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    emit(
        {
            "ok": True,
            "command": "delivery.summary",
            "path": str(Path(output_path).expanduser()) if output_path else None,
            "summary": text,
            "message": text,
        },
        as_json=ctx.obj.get("as_json"),
    )


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo
