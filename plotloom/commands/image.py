from __future__ import annotations

import tomllib
from datetime import datetime
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
@click.option("--filename", help="Optional output filename/path relative to the image kind folder, e.g. reference-sheet/selected.png for cast images.")
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
    filename: str | None,
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
            filename=filename,
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


@image_group.command("batch")
@click.option("--manifest", required=True, type=click.Path(path_type=str))
@click.option("--resume", is_flag=True, help="Keep succeeded/skipped manifest items unchanged.")
@click.option("--skip-existing", is_flag=True, help="Mark items skipped when their output already exists.")
@click.option("--write-status/--no-write-status", default=True, show_default=True, help="Write updated status back to the manifest.")
@click.pass_context
def batch_command(ctx: click.Context, manifest: str, resume: bool, skip_existing: bool, write_status: bool) -> None:
    repo = _repo_path(ctx)
    manifest_path = Path(manifest).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = repo / manifest_path
    try:
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as error:
        raise click.ClickException(f"could not read image batch manifest: {manifest_path}") from error
    items = data.get("items")
    if not isinstance(items, list):
        raise click.ClickException("image batch manifest must contain [[items]] entries")

    updated_items = []
    rows = []
    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            raise click.ClickException(f"manifest item {index} must be a table")
        item = dict(raw)
        output = str(item.get("output") or "").strip()
        status = str(item.get("status") or "pending")
        if resume and status in {"succeeded", "skipped"}:
            action = "kept"
        elif not output:
            status = "failed"
            item["error"] = "output is required"
            action = "failed"
            _stamp(item, "finished_at")
        else:
            output_path = Path(output).expanduser()
            if not output_path.is_absolute():
                output_path = repo / output_path
            if skip_existing and output_path.exists():
                status = "skipped"
                action = "skipped-existing"
                _stamp(item, "finished_at")
            else:
                status = "pending"
                action = "pending-local-only"
        item["status"] = status
        item.setdefault("retry_count", 0)
        updated_items.append(item)
        rows.append({"index": index, "status": status, "action": action, "output": output})

    if write_status and not ctx.obj.get("dry_run"):
        import tomli_w

        manifest_path.write_text(tomli_w.dumps({"items": updated_items}), encoding="utf-8")

    emit(
        {
            "ok": True,
            "command": "image.batch",
            "manifest": str(manifest_path),
            "written": bool(write_status and not ctx.obj.get("dry_run")),
            "items": rows,
            "message": "\n".join(f"{row['index']}\t{row['status']}\t{row['action']}\t{row['output']}" for row in rows),
        },
        as_json=ctx.obj.get("as_json"),
    )


def _stamp(item: dict[str, object], field: str) -> None:
    item.setdefault(field, datetime.now().isoformat(timespec="seconds"))


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo
