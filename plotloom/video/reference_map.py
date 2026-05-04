from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REFERENCE_KINDS = frozenset({"first_frame", "last_frame", "character", "scene", "style", "generic"})


@dataclass(frozen=True)
class ReferenceIntent:
    slot: int
    kind: str
    path: Path | None = None
    uri: str | None = None
    source: str = "manual"
    character: str | None = None
    scene: str | None = None
    label: str | None = None

    def to_toml_dict(self, repo: Path) -> dict[str, Any]:
        data: dict[str, Any] = {
            "slot": self.slot,
            "kind": self.kind,
            "source": self.source,
        }
        if self.path is not None:
            data["path"] = repo_relative_path(repo, self.path)
        if self.uri is not None:
            data["uri"] = self.uri
        if self.character:
            data["character"] = self.character
        if self.scene:
            data["scene"] = self.scene
        if self.label:
            data["label"] = self.label
        return data


def default_reference_map_path(repo: Path, episode: str, clip: str) -> Path:
    return repo / "episodes" / episode / "videos" / clip / "reference-map.toml"


def build_reference_map(
    repo: Path,
    *,
    first_frame: str | None = None,
    last_frame: str | None = None,
    references: tuple[str, ...] = (),
) -> list[ReferenceIntent]:
    planned: list[ReferenceIntent] = []
    if first_frame:
        planned.append(
            _intent(
                repo,
                slot=len(planned) + 1,
                kind="first_frame",
                raw_path=first_frame,
                source="manual",
            )
        )
    for entry in references:
        kind, label, raw_path = parse_reference_entry(entry)
        planned.append(
            _intent(
                repo,
                slot=len(planned) + 1,
                kind=kind,
                raw_path=raw_path,
                source=_source_for_path(raw_path),
                label=label,
            )
        )
    if last_frame:
        planned.append(
            _intent(
                repo,
                slot=len(planned) + 1,
                kind="last_frame",
                raw_path=last_frame,
                source="manual",
            )
        )
    return planned


def parse_reference_entry(entry: str) -> tuple[str, str | None, str]:
    if "=" not in entry:
        raise ValueError("reference entries must use kind[:name]=path, for example character:ethan=assets/cast/ethan/ref.png")
    left, raw_path = entry.split("=", 1)
    left = left.strip().lower().replace("-", "_")
    raw_path = raw_path.strip()
    if not raw_path:
        raise ValueError("reference path is required")

    kind, label = (left.split(":", 1) + [None])[:2] if ":" in left else (left, None)
    if not kind:
        raise ValueError("reference kind is required")
    if kind not in REFERENCE_KINDS:
        choices = ", ".join(sorted(REFERENCE_KINDS))
        raise ValueError(f"unsupported reference kind {kind!r}; supported: {choices}")
    if label is not None:
        label = label.strip()
        if not label:
            raise ValueError("reference label cannot be empty")
    return kind, label, raw_path


def write_reference_map(path: Path, repo: Path, references: list[ReferenceIntent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    import tomli_w

    path.write_text(tomli_w.dumps({"references": [item.to_toml_dict(repo) for item in references]}), encoding="utf-8")


def read_reference_map(path: Path, repo: Path) -> list[ReferenceIntent]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"could not parse reference map: {path}") from error
    references = data.get("references")
    if not isinstance(references, list):
        raise ValueError("reference map must contain [[references]] entries")

    planned: list[ReferenceIntent] = []
    for index, raw in enumerate(references, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"reference entry {index} must be a table")
        planned.append(_intent_from_dict(repo, raw, fallback_slot=index))
    return planned


def references_to_dicts(repo: Path, references: list[ReferenceIntent]) -> list[dict[str, Any]]:
    return [item.to_toml_dict(repo) for item in references]


def format_reference_map(repo: Path, references: list[ReferenceIntent]) -> str:
    if not references:
        return "reference plan is empty"
    lines = ["reference plan:"]
    for item in references:
        label = ""
        if item.character:
            label = f":{item.character}"
        elif item.scene:
            label = f":{item.scene}"
        elif item.label:
            label = f":{item.label}"
        target = item.uri if item.uri else repo_relative_path(repo, item.path) if item.path is not None else ""
        lines.append(f"{item.slot}\t{item.kind}{label}\t{target}")
    return "\n".join(lines)


def repo_relative_path(repo: Path, path: Path) -> str:
    resolved_repo = repo.resolve()
    resolved_path = path.resolve()
    if not resolved_path.is_relative_to(resolved_repo):
        raise ValueError(f"reference path must be inside repo: {path}")
    return resolved_path.relative_to(resolved_repo).as_posix()


def _intent(
    repo: Path,
    *,
    slot: int,
    kind: str,
    raw_path: str,
    source: str,
    label: str | None = None,
) -> ReferenceIntent:
    uri = _asset_uri(raw_path)
    character = label if kind == "character" else None
    scene = label if kind == "scene" else None
    generic_label = label if kind not in {"character", "scene"} else None
    return ReferenceIntent(
        slot=slot,
        kind=kind,
        path=None if uri else _resolve_existing_repo_path(repo, raw_path),
        uri=uri,
        source=source,
        character=character,
        scene=scene,
        label=generic_label,
    )


def _intent_from_dict(repo: Path, raw: dict[str, Any], *, fallback_slot: int) -> ReferenceIntent:
    kind = str(raw.get("kind") or "").strip().lower().replace("-", "_")
    if kind not in REFERENCE_KINDS:
        choices = ", ".join(sorted(REFERENCE_KINDS))
        raise ValueError(f"unsupported reference kind {kind!r}; supported: {choices}")
    path_value = str(raw.get("path") or "").strip()
    uri = str(raw.get("uri") or "").strip() or None
    if not path_value and not uri:
        raise ValueError("reference path or uri is required")
    if uri:
        _asset_uri(uri)
    slot = int(raw.get("slot") or fallback_slot)
    return ReferenceIntent(
        slot=slot,
        kind=kind,
        path=_resolve_existing_repo_path(repo, path_value) if path_value else None,
        uri=uri,
        source=str(raw.get("source") or "manual"),
        character=str(raw["character"]) if raw.get("character") else None,
        scene=str(raw["scene"]) if raw.get("scene") else None,
        label=str(raw["label"]) if raw.get("label") else None,
    )


def _resolve_existing_repo_path(repo: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo / path
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"reference path not found: {resolved}")
    repo_relative_path(repo, resolved)
    return resolved


def _source_for_path(value: str) -> str:
    if _asset_uri(value):
        return "asset"
    path = Path(value)
    first = path.parts[0] if path.parts else ""
    return "asset" if first == "assets" else "manual"


def _asset_uri(value: str) -> str | None:
    value = value.strip()
    if value.startswith("asset://asset-"):
        return value
    if value.startswith("asset://"):
        raise ValueError("asset uri must use asset://asset-<id>")
    return None
