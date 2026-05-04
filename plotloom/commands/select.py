from __future__ import annotations

from pathlib import Path

import click

from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd
from plotloom.repo_settings import load_video_continuity_config
from plotloom.review_artifacts import create_media_review_artifacts, write_selected_note
from plotloom.selection import select_candidate


@click.command("select")
@click.argument("candidate", type=click.Path(path_type=str))
@click.option("--reason", help="Optional selection reason written to selected-note.md when continuity artifacts are enabled.")
@click.pass_context
def select_command(ctx: click.Context, candidate: str, reason: str | None) -> None:
    """Copy a candidate media file to its selected sibling."""
    try:
        result = select_candidate(Path(candidate))
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error

    repo = _repo_path(ctx, result.selected_path)
    continuity = load_video_continuity_config(repo)
    continuity_artifacts: dict[str, str] = {}
    continuity_warnings: list[str] = []
    if continuity.enabled and (continuity.extract_first_frame or continuity.extract_last_frame):
        review_dir = result.selected_path.parent / "review" / "selected-continuity"
        try:
            review = create_media_review_artifacts(
                result.selected_path,
                review_dir,
                repo=repo,
                extract_first_frame=continuity.extract_first_frame,
                extract_last_frame=continuity.extract_last_frame,
                reviewer="select",
            )
            continuity_artifacts = review.artifacts
            continuity_warnings = review.warnings
            write_selected_note(
                result.selected_path,
                result.selected_path.with_name("selected-note.md"),
                repo=repo,
                artifacts=continuity_artifacts,
                reason=reason,
            )
        except (OSError, ValueError) as error:
            continuity_warnings = [str(error)]

    backup_path = str(result.backup_path) if result.backup_path else None
    message = f"selected candidate: {result.selected_path}"
    if backup_path:
        message = f"{message} (backup: {backup_path})"
    if continuity.enabled:
        message = f"{message}\ncontinuity artifacts: {'enabled' if continuity_artifacts else 'not generated'}"
    emit(
        {
            "ok": True,
            "command": "select",
            "selected_path": str(result.selected_path),
            "backup_path": backup_path,
            "continuity": {
                "enabled": continuity.enabled,
                "extract_first_frame": continuity.extract_first_frame,
                "extract_last_frame": continuity.extract_last_frame,
                "auto_use_previous_last_frame": continuity.auto_use_previous_last_frame,
                "artifacts": continuity_artifacts,
                "warnings": continuity_warnings,
            },
            "message": message,
        },
        as_json=ctx.obj.get("as_json"),
    )


def _repo_path(ctx: click.Context, selected_path: Path) -> Path | None:
    repo_arg = ctx.obj.get("repo")
    if repo_arg:
        return Path(repo_arg).expanduser().resolve()
    return find_repo_from_cwd(selected_path.parent) or find_repo_from_cwd(Path.cwd())
