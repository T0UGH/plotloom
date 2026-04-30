from __future__ import annotations

import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from plotloom.toml_io import toml_str

SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
TEXT_EXTS = {".md", ".toml", ".txt"}


@dataclass(frozen=True)
class RepoValidation:
    ok: bool
    missing: list[Path]


class RegistryError(ValueError):
    pass


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def template_root() -> Path:
    source_template = project_root() / "templates" / "series-repo"
    if source_template.exists():
        return source_template
    package_template = Path(__file__).resolve().parent / "templates" / "series-repo"
    if package_template.exists():
        return package_template
    raise FileNotFoundError("series repo template not found")


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
    if not validate_registry_append(registry, slug=slug, path=path):
        return

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
    if text and not text.endswith("\n"):
        text += "\n"
    try:
        registry.write_text(text + entry, encoding="utf-8")
    except OSError as error:
        raise RegistryError(f"could not write registry: {registry}") from error


def read_registry(registry: Path) -> list[dict[str, Any]]:
    if not registry.exists():
        return []
    try:
        data = tomllib.loads(registry.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise RegistryError(f"could not parse registry TOML: {registry}") from error
    except OSError as error:
        raise RegistryError(f"could not read registry: {registry}") from error
    repos = data.get("repos", [])
    if not isinstance(repos, list):
        raise RegistryError("registry repos must be an array")
    return [repo for repo in repos if isinstance(repo, dict)]


def init_repo(target: Path, *, slug: str, title: str, registry: Path | None = None) -> Path:
    if not SAFE_SLUG.match(slug):
        raise ValueError("invalid slug")
    if "\n" in title or "\r" in title:
        raise ValueError("invalid title")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(str(target))
    if registry:
        validate_registry_append(registry, slug=slug, path=target)

    target_existed = target.exists()
    staging = target.parent / f".{target.name}.plotloom-tmp"
    if staging.exists():
        shutil.rmtree(staging)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_template(template_root(), staging, slug=slug, title=title)
        if registry:
            append_registry(registry, slug=slug, title=title, path=target)
        if target_existed:
            target.rmdir()
        staging.rename(target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if not target_existed and target.exists():
            shutil.rmtree(target)
        raise
    return target


def validate_registry_append(registry: Path, *, slug: str, path: Path) -> bool:
    try:
        registry.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RegistryError(f"could not create registry parent: {registry.parent}") from error
    repos = read_registry(registry)
    for repo in repos:
        if repo.get("slug") != slug:
            continue
        existing_path = Path(str(repo.get("path", ""))).expanduser()
        if existing_path == path:
            return False
        raise ValueError(f"registry slug conflict: {slug}")
    return True


def validate_segment(kind: str, value: str) -> str:
    if not SAFE_SEGMENT.match(value):
        raise ValueError(f"invalid {kind}: {value}")
    return value


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
        episode = validate_segment("episode", episode)
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
