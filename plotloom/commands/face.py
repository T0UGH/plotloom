from __future__ import annotations

from pathlib import Path

import click

from plotloom.output import emit
from plotloom.repo import find_repo_from_cwd
from plotloom.video.face_policy import face_policy_to_dict, load_face_policy, redact_cloud_asset


@click.group("face")
def face_group() -> None:
    """Inspect character face policy and smoke-test prompts."""


@face_group.command("policy")
@click.option("--character", required=True)
@click.option("--adapter", required=True)
@click.pass_context
def policy_command(ctx: click.Context, character: str, adapter: str) -> None:
    repo = _repo_path(ctx)
    policy, issues, path = load_face_policy(repo, character)
    if issues or policy is None:
        messages = "\n".join(f"{issue.character}: {issue.message} ({issue.path})" for issue in issues)
        raise click.ClickException(messages or f"missing face policy: {path}")
    policy_data = face_policy_to_dict(repo, policy)
    advice = _policy_advice(policy_data, adapter)
    emit(
        {
            "ok": True,
            "command": "face.policy",
            "character": character,
            "adapter": adapter,
            "policy_path": str(path),
            "policy": policy_data,
            "advice": advice,
            "message": _policy_message(policy_data, advice),
        },
        as_json=ctx.obj.get("as_json"),
    )


@face_group.command("smoke-prompt")
@click.option("--character", required=True)
@click.option("--adapter", required=True)
@click.pass_context
def smoke_prompt_command(ctx: click.Context, character: str, adapter: str) -> None:
    repo = _repo_path(ctx)
    policy, issues, _path = load_face_policy(repo, character)
    if issues or policy is None:
        messages = "\n".join(f"{issue.character}: {issue.message} ({issue.path})" for issue in issues)
        raise click.ClickException(messages)
    prompt = _smoke_prompt(character, adapter, policy.description)
    emit(
        {
            "ok": True,
            "command": "face.smoke-prompt",
            "character": character,
            "adapter": adapter,
            "prompt_text": prompt,
            "message": prompt,
        },
        as_json=ctx.obj.get("as_json"),
    )


def _policy_advice(policy: dict[str, object], adapter: str) -> dict[str, object]:
    strategy = str(policy["strategy"])
    avoid = [
        "full visible-face photoreal character sheet",
        "corpse or morgue face reference",
        "red mesh / topology overlay as privacy bypass",
    ]
    if strategy == "safe-face-reference":
        return {
            "adapter": adapter,
            "send": [policy.get("path")],
            "avoid": avoid,
            "notes": ["Use the safe local face reference only if it is intentionally non-photoreal, masked, or sketch-like."],
        }
    if strategy == "text-only":
        return {
            "adapter": adapter,
            "send": [],
            "avoid": [*avoid, "any local face reference image"],
            "notes": ["Describe the face in prompt text; do not attach face images for this character."],
        }
    if strategy == "cloud-face-asset":
        cloud_asset = str(policy.get("cloud_asset") or "")
        return {
            "adapter": adapter,
            "send": [redact_cloud_asset(cloud_asset), policy.get("body_reference")],
            "avoid": avoid,
            "notes": ["Cloud face asset is face-only; pair it with the local body/wardrobe reference for clothing and silhouette."],
        }
    return {"adapter": adapter, "send": [], "avoid": avoid, "notes": [f"Unknown strategy: {strategy}"]}


def _policy_message(policy: dict[str, object], advice: dict[str, object]) -> str:
    lines = [
        f"character: {policy['character']}",
        f"strategy: {policy['strategy']}",
        "send:",
        *[f"- {item}" for item in advice["send"] if item],
        "avoid:",
        *[f"- {item}" for item in advice["avoid"]],
        "notes:",
        *[f"- {item}" for item in advice["notes"]],
    ]
    return "\n".join(lines)


def _smoke_prompt(character: str, adapter: str, description: str | None) -> str:
    face_description = f" Character face description: {description}" if description else ""
    return (
        f"Face consistency smoke test for {character} on {adapter}. Medium close-up, front-left 3/4 face, "
        "face visible for at least 2 seconds, face occupies 25-35% of frame, no deep hat shadow, no wide canyon shot, "
        "no fast horse riding, minimal action, slight head turn, stable lighting, no subtitles or text overlays."
        f"{face_description}"
    )


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else find_repo_from_cwd(Path.cwd())
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo
