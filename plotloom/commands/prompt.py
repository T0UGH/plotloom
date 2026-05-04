from __future__ import annotations

from pathlib import Path

import click

from plotloom.output import emit
from plotloom.prompts import compile_prompt, extract_clip_prompt, lint_provider_prompt, list_clips
from plotloom.repo import find_repo_from_cwd
from plotloom.video.reference_map import default_reference_map_path, format_reference_map, read_reference_map, references_to_dicts

VIDEO_PROMPTS = "video-prompts-en.md"
MODES = ["text-to-video", "image-to-video", "reference-to-video", "video-edit"]


@click.group("prompt")
def prompt_group() -> None:
    """Inspect and compile episode video prompts."""


@prompt_group.command("list")
@click.option("--episode", required=True)
@click.option("--prompt-file", type=click.Path(path_type=str))
@click.pass_context
def list_command(ctx: click.Context, episode: str, prompt_file: str | None) -> None:
    path = _prompt_path(ctx, episode, prompt_file)
    text = _read_prompt_file(path)
    clips = list_clips(text)
    emit(
        {
            "ok": True,
            "command": "prompt.list",
            "episode": episode,
            "prompt_file": str(path),
            "clips": clips,
            "message": "\n".join(clips) if clips else "no clips found",
        },
        as_json=ctx.obj.get("as_json"),
    )


@prompt_group.command("extract")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--field", default="prompt-string", show_default=True)
@click.option("--prompt-file", type=click.Path(path_type=str))
@click.pass_context
def extract_command(ctx: click.Context, episode: str, clip: str, field: str, prompt_file: str | None) -> None:
    if field != "prompt-string":
        raise click.BadParameter("only prompt-string is supported", param_hint="--field")
    path = _prompt_path(ctx, episode, prompt_file)
    text = _read_prompt_file(path)
    try:
        prompt = extract_clip_prompt(text, clip)
    except KeyError as error:
        raise click.ClickException(str(error)) from error
    if not prompt:
        raise click.ClickException(f"prompt string is empty for {clip}")

    emit(
        {
            "ok": True,
            "command": "prompt.extract",
            "episode": episode,
            "clip": clip,
            "prompt_file": str(path),
            "prompt_text": prompt,
            "message": prompt,
        },
        as_json=ctx.obj.get("as_json"),
    )


@prompt_group.command("refs")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--reference-map", type=click.Path(path_type=str), help="Reference map path; defaults to the clip reference-map.toml.")
@click.pass_context
def refs_command(ctx: click.Context, episode: str, clip: str, reference_map: str | None) -> None:
    repo = _repo_path(ctx)
    path = Path(reference_map).expanduser() if reference_map else default_reference_map_path(repo, episode, clip)
    if not path.is_absolute():
        path = repo / path
    try:
        references = read_reference_map(path.resolve(), repo)
    except (FileNotFoundError, ValueError, OSError) as error:
        raise click.ClickException(str(error)) from error
    emit(
        {
            "ok": True,
            "command": "prompt.refs",
            "episode": episode,
            "clip": clip,
            "reference_map_path": str(path.resolve()),
            "references": references_to_dicts(repo, references),
            "message": format_reference_map(repo, references),
        },
        as_json=ctx.obj.get("as_json"),
    )


@prompt_group.command("compile")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--adapter", required=True)
@click.option("--mode", required=True, type=click.Choice(MODES))
@click.option("--prompt-file", type=click.Path(path_type=str))
@click.option("--output", "output_path", type=click.Path(path_type=str))
@click.option("--reference-map", type=click.Path(path_type=str), help="Use reference-map.toml for prompt slot lint.")
@click.option("--lint", "run_lint", is_flag=True, help="Run provider prompt lint checks.")
@click.pass_context
def compile_command(
    ctx: click.Context,
    episode: str,
    clip: str,
    adapter: str,
    mode: str,
    prompt_file: str | None,
    output_path: str | None,
    reference_map: str | None,
    run_lint: bool,
) -> None:
    path = _prompt_path(ctx, episode, prompt_file)
    text = _read_prompt_file(path)
    try:
        compiled = compile_prompt(text, clip, adapter, mode)
    except (KeyError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    lint_warnings = _lint_warnings(ctx, compiled.prompt_text, reference_map=reference_map, run_lint=run_lint)

    if output_path:
        try:
            Path(output_path).expanduser().write_text(compiled.prompt_text, encoding="utf-8")
        except OSError as error:
            raise click.ClickException(f"could not write compiled prompt: {output_path}") from error

    payload = {
        "ok": True,
        "command": "prompt.compile",
        "episode": episode,
        "clip": clip,
        "adapter": adapter,
        "mode": mode,
        "prompt_file": str(path),
        "prompt_text": compiled.prompt_text,
        "sha256": compiled.sha256,
        "prompt_sha256": compiled.prompt_sha256,
        "prompt_chars": compiled.prompt_chars,
        "warnings": [*compiled.warnings, *lint_warnings],
        "message": compiled.prompt_text,
    }
    if output_path:
        payload["path"] = str(Path(output_path).expanduser())
    emit(payload, as_json=ctx.obj.get("as_json"))


@prompt_group.command("check")
@click.option("--episode", required=True)
@click.option("--clip")
@click.option("--adapter", default="dreamina-cli", show_default=True)
@click.option("--mode", default="text-to-video", show_default=True, type=click.Choice(MODES))
@click.option("--prompt-file", type=click.Path(path_type=str))
@click.option("--reference-map", type=click.Path(path_type=str), help="Use reference-map.toml for prompt slot lint.")
@click.option("--lint", "run_lint", is_flag=True, help="Run provider prompt lint checks.")
@click.option("--strict-refs", is_flag=True, help="Fail when prompt image slots do not match the reference map.")
@click.pass_context
def check_command(
    ctx: click.Context,
    episode: str,
    clip: str | None,
    adapter: str,
    mode: str,
    prompt_file: str | None,
    reference_map: str | None,
    run_lint: bool,
    strict_refs: bool,
) -> None:
    path = _prompt_path(ctx, episode, prompt_file)
    text = _read_prompt_file(path)
    clips = [clip] if clip else list_clips(text)
    if not clips:
        raise click.ClickException("no clips found")

    checks: dict[str, dict[str, object]] = {}
    failed: list[str] = []
    for clip_name in clips:
        try:
            compiled = compile_prompt(text, clip_name, adapter, mode)
        except (KeyError, ValueError) as error:
            failed.append(clip_name)
            checks[clip_name] = {"ok": False, "error": str(error)}
            continue
        current_reference_map = reference_map
        if strict_refs and current_reference_map is None:
            current_reference_map = str(default_reference_map_path(_repo_path(ctx), episode, clip_name))
        try:
            lint_warnings = _lint_warnings(ctx, compiled.prompt_text, reference_map=current_reference_map, run_lint=run_lint or strict_refs)
        except click.ClickException as error:
            failed.append(clip_name)
            checks[clip_name] = {
                "ok": False,
                "sha256": compiled.sha256,
                "prompt_sha256": compiled.prompt_sha256,
                "prompt_chars": compiled.prompt_chars,
                "warnings": compiled.warnings,
                "error": error.message,
            }
            continue
        strict_warnings = _strict_ref_warnings(lint_warnings)
        if strict_refs and strict_warnings:
            failed.append(clip_name)
            checks[clip_name] = {
                "ok": False,
                "sha256": compiled.sha256,
                "prompt_sha256": compiled.prompt_sha256,
                "prompt_chars": compiled.prompt_chars,
                "warnings": [*compiled.warnings, *lint_warnings],
                "error": "strict refs failed: " + "; ".join(strict_warnings),
            }
            continue
        checks[clip_name] = {
            "ok": True,
            "sha256": compiled.sha256,
            "prompt_sha256": compiled.prompt_sha256,
            "prompt_chars": compiled.prompt_chars,
            "warnings": [*compiled.warnings, *lint_warnings],
        }

    emit(
        {
            "ok": not failed,
            "command": "prompt.check",
            "episode": episode,
            "adapter": adapter,
            "mode": mode,
            "prompt_file": str(path),
            "checks": checks,
            "message": _check_message(checks, failed),
        },
        as_json=ctx.obj.get("as_json"),
    )
    if failed:
        ctx.exit(1)


def _prompt_path(ctx: click.Context, episode: str, prompt_file: str | None) -> Path:
    if prompt_file:
        return Path(prompt_file).expanduser().resolve()
    repo_arg = ctx.obj.get("repo")
    discovered = find_repo_from_cwd(Path.cwd()) if not repo_arg else None
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else discovered
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo / "episodes" / episode / VIDEO_PROMPTS


def _repo_path(ctx: click.Context) -> Path:
    repo_arg = ctx.obj.get("repo")
    discovered = find_repo_from_cwd(Path.cwd()) if not repo_arg else None
    repo = Path(repo_arg).expanduser().resolve() if repo_arg else discovered
    if repo is None:
        raise click.ClickException("--repo is required outside a Plotloom series repo")
    return repo


def _lint_warnings(ctx: click.Context, prompt: str, *, reference_map: str | None, run_lint: bool) -> list[str]:
    if not run_lint and not reference_map:
        return []
    reference_count = None
    if reference_map:
        path = Path(reference_map).expanduser()
        if not path.is_absolute():
            path = _repo_path(ctx) / path
        try:
            reference_count = len(read_reference_map(path.resolve(), _repo_path(ctx)))
        except (FileNotFoundError, ValueError, OSError) as error:
            raise click.ClickException(str(error)) from error
    return lint_provider_prompt(prompt, reference_count=reference_count)


def _strict_ref_warnings(warnings: list[str]) -> list[str]:
    return [warning for warning in warnings if "reference map" in warning or "Image" in warning]


def _check_message(checks: dict[str, dict[str, object]], failed: list[str]) -> str:
    if not failed:
        return "prompt check ok"
    lines = [f"prompt check failed: {', '.join(failed)}"]
    for clip in failed:
        error = checks.get(clip, {}).get("error")
        if error:
            lines.append(f"{clip}: {error}")
    return "\n".join(lines)


def _read_prompt_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise click.ClickException(f"prompt file not found: {path}") from error
    except OSError as error:
        raise click.ClickException(f"could not read prompt file: {path}") from error
