from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

import click

from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
REVIEW_KINDS = ["scenes", "cast", "covers", "references"]


@click.group("review")
def review_group() -> None:
    """Create local review artifacts."""


@review_group.command("contact-sheet")
@click.option("--episode")
@click.option("--kind", required=True, type=click.Choice(REVIEW_KINDS))
@click.option("--output", "output_path", required=True, type=click.Path(path_type=str))
@click.option("--reviewer", default="manual", show_default=True)
@click.pass_context
def contact_sheet_command(ctx: click.Context, episode: str | None, kind: str, output_path: str, reviewer: str) -> None:
    repo = _repo_path(ctx)
    output = Path(output_path).expanduser()
    if not output.is_absolute():
        output = repo / output
    candidates = _candidate_images(repo, episode=episode, kind=kind)
    try:
        if output.suffix.lower() == ".png":
            _write_png_contact_sheet(output, repo, candidates)
        else:
            _write_svg_contact_sheet(output, repo, candidates)
        note_path = output.parent / "review-note.md"
        _write_review_note(note_path, repo, candidates, episode=episode, kind=kind, reviewer=reviewer)
    except (OSError, RuntimeError) as error:
        raise click.ClickException(str(error)) from error
    emit(
        {
            "ok": True,
            "command": "review.contact-sheet",
            "episode": episode,
            "kind": kind,
            "candidate_count": len(candidates),
            "contact_sheet_path": str(output),
            "review_note_path": str(note_path),
            "message": f"review contact sheet: {output}\nreview note: {note_path}\ncandidates: {len(candidates)}",
        },
        as_json=ctx.obj.get("as_json"),
    )


def _candidate_images(repo: Path, *, episode: str | None, kind: str) -> list[Path]:
    if kind == "scenes":
        root = repo / "assets" / "scenes"
        patterns = ["*/candidates/*"]
    elif kind == "cast":
        root = repo / "assets" / "cast"
        patterns = ["*/candidates/*"]
    elif kind == "covers":
        if not episode:
            raise click.ClickException("--episode is required for cover review")
        root = repo / "episodes" / episode / "images" / "covers"
        patterns = ["candidates/*"]
    elif kind == "references":
        if not episode:
            raise click.ClickException("--episode is required for reference review")
        root = repo / "episodes" / episode / "images" / "references"
        patterns = ["*/candidates/*"]
    else:
        raise click.ClickException(f"unsupported review kind: {kind}")
    if not root.exists():
        return []
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(path for path in root.glob(pattern) if path.is_file() and path.suffix.lower() in IMAGE_EXTS)
    return sorted(paths)


def _write_svg_contact_sheet(output: Path, repo: Path, candidates: list[Path]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    width = 1200
    cell_w = 280
    cell_h = 260
    cols = 4
    rows = max(1, (len(candidates) + cols - 1) // cols)
    height = 80 + rows * cell_h
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f3ea"/>',
        '<text x="32" y="42" font-size="24" font-family="Georgia, serif" fill="#2b241c">Plotloom review contact sheet</text>',
    ]
    for index, path in enumerate(candidates, start=1):
        col = (index - 1) % cols
        row = (index - 1) // cols
        x = 32 + col * cell_w
        y = 72 + row * cell_h
        rel = path.relative_to(repo).as_posix()
        href = html.escape(_relative_href(output.parent, path))
        label = html.escape(f"{index}. {rel}")
        lines.extend(
            [
                f'<rect x="{x}" y="{y}" width="240" height="190" rx="10" fill="#fffaf0" stroke="#d1b98c"/>',
                f'<image href="{href}" x="{x + 10}" y="{y + 10}" width="220" height="150" preserveAspectRatio="xMidYMid meet"/>',
                f'<text x="{x + 10}" y="{y + 180}" font-size="11" font-family="Menlo, monospace" fill="#3a3329">{label}</text>',
            ]
        )
    lines.append("</svg>")
    output.write_text("\n".join(lines), encoding="utf-8")


def _write_png_contact_sheet(output: Path, repo: Path, candidates: list[Path]) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError as error:
        raise RuntimeError("PNG contact sheets require Pillow; use a .svg output path or install pillow") from error
    output.parent.mkdir(parents=True, exist_ok=True)
    cell_w = 320
    cell_h = 260
    cols = 3
    rows = max(1, (len(candidates) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * cell_w, 60 + rows * cell_h), "#f7f3ea")
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 20), "Plotloom review contact sheet", fill="#2b241c")
    for index, path in enumerate(candidates, start=1):
        col = (index - 1) % cols
        row = (index - 1) // cols
        x = col * cell_w + 20
        y = 60 + row * cell_h
        with Image.open(path) as image:
            image.thumbnail((280, 190))
            sheet.paste(image.convert("RGB"), (x, y))
        draw.text((x, y + 200), f"{index}. {path.relative_to(repo).as_posix()}", fill="#3a3329")
    sheet.save(output)


def _write_review_note(note_path: Path, repo: Path, candidates: list[Path], *, episode: str | None, kind: str, reviewer: str) -> None:
    note_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Plotloom Review Note",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- reviewer: {reviewer}",
        f"- episode: {episode or ''}",
        f"- kind: {kind}",
        "",
        "| candidate | pass/fail | character consistency | face visible | refs used | story beat clear | provider artifacts | decision |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for path in candidates:
        rel = path.relative_to(repo).as_posix()
        lines.append(f"| `{rel}` | pending | pending | pending | pending | pending | pending | selected/reroll/revise_prompt/ask_user |")
    if not candidates:
        lines.append("| no candidates found | pending | pending | pending | pending | pending | pending | ask_user |")
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _relative_href(base: Path, target: Path) -> str:
    return target.resolve().relative_to(base.resolve()).as_posix() if target.resolve().is_relative_to(base.resolve()) else target.resolve().as_uri()


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo
