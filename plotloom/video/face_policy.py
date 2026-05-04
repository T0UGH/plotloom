from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from plotloom.video.reference_map import ReferenceIntent, repo_relative_path

FACE_STRATEGIES = frozenset({"safe-face-reference", "text-only", "cloud-face-asset"})
FACE_POLICY_FILE = "face-policy.toml"


@dataclass(frozen=True)
class FacePolicyIssue:
    character: str
    path: Path
    message: str


@dataclass(frozen=True)
class FacePolicy:
    character: str
    strategy: str
    path: Path | None = None
    description: str | None = None
    provider: str | None = None
    cloud_asset: str | None = None
    body_reference: Path | None = None


@dataclass(frozen=True)
class FacePolicyValidation:
    issues: list[FacePolicyIssue]
    checked: int

    @property
    def ok(self) -> bool:
        return not self.issues


def load_face_policy(repo: Path, character: str) -> tuple[FacePolicy | None, list[FacePolicyIssue], Path]:
    policy_path = repo / "assets" / "cast" / character / FACE_POLICY_FILE
    if not policy_path.exists():
        return None, [FacePolicyIssue(character=character, path=policy_path, message="missing face-policy.toml")], policy_path
    policy, issues = _load_face_policy(repo, character=character, path=policy_path)
    return policy, issues, policy_path


def face_policy_to_dict(repo: Path, policy: FacePolicy) -> dict[str, Any]:
    data: dict[str, Any] = {
        "character": policy.character,
        "strategy": policy.strategy,
    }
    if policy.path:
        data["path"] = repo_relative_path(repo, policy.path)
    if policy.description:
        data["description"] = policy.description
    if policy.provider:
        data["provider"] = policy.provider
    if policy.cloud_asset:
        data["cloud_asset"] = policy.cloud_asset
        data["cloud_asset_redacted"] = redact_cloud_asset(policy.cloud_asset)
    if policy.body_reference:
        data["body_reference"] = repo_relative_path(repo, policy.body_reference)
    return data


def redact_cloud_asset(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if len(value) <= 18:
        return "[REDACTED]"
    return f"{value[:14]}[REDACTED]{value[-6:]}"


def validate_face_policies(repo: Path) -> FacePolicyValidation:
    cast_root = repo / "assets" / "cast"
    if not cast_root.exists():
        return FacePolicyValidation(issues=[], checked=0)

    issues: list[FacePolicyIssue] = []
    checked = 0
    for character_dir in sorted(path for path in cast_root.iterdir() if path.is_dir()):
        policy_path = character_dir / FACE_POLICY_FILE
        character = character_dir.name
        if not policy_path.exists():
            issues.append(FacePolicyIssue(character=character, path=policy_path, message="missing face-policy.toml"))
            continue
        checked += 1
        _policy, policy_issues = _load_face_policy(repo, character=character, path=policy_path)
        issues.extend(policy_issues)
    return FacePolicyValidation(issues=issues, checked=checked)


def validate_reference_intent_face_policies(repo: Path, references: list[ReferenceIntent]) -> list[FacePolicyIssue]:
    issues: list[FacePolicyIssue] = []
    for reference in references:
        if reference.kind != "character" or not reference.character:
            continue
        policy_path = repo / "assets" / "cast" / reference.character / FACE_POLICY_FILE
        if not policy_path.exists():
            issues.append(FacePolicyIssue(character=reference.character, path=policy_path, message="missing face-policy.toml for character reference"))
            continue
        policy, policy_issues = _load_face_policy(repo, character=reference.character, path=policy_path)
        issues.extend(policy_issues)
        if policy is None:
            continue
        issues.extend(_validate_character_reference(repo, reference=reference, policy=policy, policy_path=policy_path))
    return issues


def _load_face_policy(repo: Path, *, character: str, path: Path) -> tuple[FacePolicy | None, list[FacePolicyIssue]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        return None, [FacePolicyIssue(character=character, path=path, message=f"could not parse TOML: {error}")]
    except OSError as error:
        return None, [FacePolicyIssue(character=character, path=path, message=f"could not read policy: {error}")]

    issues: list[FacePolicyIssue] = []
    declared_character = str(data.get("character") or "").strip()
    if declared_character and declared_character != character:
        issues.append(
            FacePolicyIssue(
                character=character,
                path=path,
                message=f"character field {declared_character!r} does not match directory {character!r}",
            )
        )

    face = data.get("face")
    if not isinstance(face, dict):
        return None, [*issues, FacePolicyIssue(character=character, path=path, message="missing [face] table")]

    strategy = str(face.get("strategy") or "").strip()
    if strategy not in FACE_STRATEGIES:
        choices = ", ".join(sorted(FACE_STRATEGIES))
        issues.append(FacePolicyIssue(character=character, path=path, message=f"unsupported face strategy {strategy!r}; supported: {choices}"))
        return None, issues

    policy = FacePolicy(character=character, strategy=strategy)
    if strategy == "safe-face-reference":
        face_path, file_issues = _repo_file(repo, character=character, policy_path=path, face=face, field="path")
        issues.extend(file_issues)
        policy = FacePolicy(character=character, strategy=strategy, path=face_path)
    elif strategy == "text-only":
        description = str(face.get("description") or "").strip()
        if not description:
            issues.append(FacePolicyIssue(character=character, path=path, message="text-only strategy requires face.description"))
        policy = FacePolicy(character=character, strategy=strategy, description=description or None)
    elif strategy == "cloud-face-asset":
        provider = str(face.get("provider") or "").strip()
        cloud_asset = str(face.get("cloud_asset") or "").strip()
        if not provider:
            issues.append(FacePolicyIssue(character=character, path=path, message="cloud-face-asset strategy requires face.provider"))
        if not cloud_asset:
            issues.append(FacePolicyIssue(character=character, path=path, message="cloud-face-asset strategy requires face.cloud_asset"))
        elif not cloud_asset.startswith("asset://asset-"):
            issues.append(FacePolicyIssue(character=character, path=path, message="face.cloud_asset must use asset://asset-<id>"))
        body_reference, file_issues = _repo_file(repo, character=character, policy_path=path, face=face, field="body_reference")
        issues.extend(file_issues)
        policy = FacePolicy(
            character=character,
            strategy=strategy,
            provider=provider or None,
            cloud_asset=cloud_asset or None,
            body_reference=body_reference,
        )
    return policy, issues


def _validate_character_reference(
    repo: Path,
    *,
    reference: ReferenceIntent,
    policy: FacePolicy,
    policy_path: Path,
) -> list[FacePolicyIssue]:
    if policy.strategy == "text-only":
        return [
            FacePolicyIssue(
                character=policy.character,
                path=policy_path,
                message=f"reference-map uses character:{policy.character}, but face strategy is text-only",
            )
        ]
    if reference.uri:
        if policy.strategy == "cloud-face-asset" and policy.cloud_asset == reference.uri:
            return []
        expected = policy.cloud_asset if policy.strategy == "cloud-face-asset" else "local face.path"
        return [
            FacePolicyIssue(
                character=policy.character,
                path=policy_path,
                message=f"character reference uri must match {expected}",
            )
        ]
    if reference.path is None:
        return [
            FacePolicyIssue(
                character=policy.character,
                path=policy_path,
                message=f"reference-map character:{policy.character} must use path or matching cloud asset uri",
            )
        ]
    if policy.strategy == "safe-face-reference" and policy.path and not _same_file(reference.path, policy.path):
        return [
            FacePolicyIssue(
                character=policy.character,
                path=policy_path,
                message=(
                    "character reference path must match face.path for safe-face-reference: "
                    f"{repo_relative_path(repo, policy.path)}"
                ),
            )
        ]
    if policy.strategy == "cloud-face-asset" and policy.body_reference and not _same_file(reference.path, policy.body_reference):
        return [
            FacePolicyIssue(
                character=policy.character,
                path=policy_path,
                message=(
                    "character reference path must match face.body_reference for cloud-face-asset: "
                    f"{repo_relative_path(repo, policy.body_reference)}"
                ),
            )
        ]
    return []


def _repo_file(
    repo: Path,
    *,
    character: str,
    policy_path: Path,
    face: dict[str, Any],
    field: str,
) -> tuple[Path | None, list[FacePolicyIssue]]:
    value = str(face.get(field) or "").strip()
    if not value:
        return None, [FacePolicyIssue(character=character, path=policy_path, message=f"{field} is required")]

    target = Path(value).expanduser()
    if not target.is_absolute():
        target = repo / target
    resolved = target.resolve()
    if not resolved.is_relative_to(repo.resolve()):
        return None, [FacePolicyIssue(character=character, path=policy_path, message=f"{field} must be inside repo: {value}")]
    if not resolved.exists():
        return None, [FacePolicyIssue(character=character, path=policy_path, message=f"{field} not found: {value}")]
    if not resolved.is_file():
        return None, [FacePolicyIssue(character=character, path=policy_path, message=f"{field} is not a file: {value}")]
    return resolved, []


def _same_file(left: Path, right: Path) -> bool:
    return left.resolve() == right.resolve()
