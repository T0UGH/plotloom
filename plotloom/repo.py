from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from plotloom.toml_io import toml_str

SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TEXT_EXTS = {".md", ".toml", ".txt"}


@dataclass(frozen=True)
class RepoValidation:
    ok: bool
    missing: list[Path]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_template(src: Path, dst: Path, *, slug: str, title: str) -> None:
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        if item.suffix in TEXT_EXTS:
            text = item.read_text(encoding="utf-8").replace("{{slug}}", slug).replace("{{title}}", title)
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(item, target)


def append_registry(registry: Path, *, slug: str, title: str, path: Path) -> None:
    registry.parent.mkdir(parents=True, exist_ok=True)
    entry = "\n".join(
        [
            "[[repos]]",
            f"slug = {toml_str(slug)}",
            f"title = {toml_str(title)}",
            f"path = {toml_str(path)}",
            'status = "active"',
            "",
        ]
    )
    text = registry.read_text(encoding="utf-8") if registry.exists() else "# Plotloom home repo registry\n\n"
    if f"slug = {toml_str(slug)}" in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    registry.write_text(text + entry, encoding="utf-8")


def init_repo(target: Path, *, slug: str, title: str, registry: Path | None = None) -> Path:
    if not SAFE_SLUG.match(slug):
        raise ValueError("invalid slug")
    if "\n" in title or "\r" in title:
        raise ValueError("invalid title")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(str(target))

    template = project_root() / "templates" / "series-repo"
    target.mkdir(parents=True, exist_ok=True)
    copy_template(template, target, slug=slug, title=title)
    if registry:
        append_registry(registry, slug=slug, title=title, path=target)
    return target


def validate_repo(
    repo: Path,
    *,
    episode: str | None = None,
    require_prompts: bool = False,
    require_media: bool = False,
) -> RepoValidation:
    missing: list[Path] = []
    for rel in ("series.md", "characters.md", "episodes"):
        path = repo / rel
        if not path.exists():
            missing.append(path)

    if episode:
        ep_dir = repo / "episodes" / episode
        if not ep_dir.exists():
            missing.append(ep_dir)
        if require_prompts:
            for name in ("video-prompts.md", "video-prompts-en.md"):
                if not (ep_dir / name).exists():
                    missing.append(ep_dir / name)
        if require_media and not (ep_dir / "videos").exists():
            missing.append(ep_dir / "videos")

    return RepoValidation(ok=not missing, missing=missing)


def find_repo_from_cwd(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for path in [current, *current.parents]:
        if (path / "series.md").exists():
            return path
    return None
