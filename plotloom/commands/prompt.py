from __future__ import annotations

from pathlib import Path

import click

from plotloom.output import emit
from plotloom.prompts import compile_prompt, extract_clip_prompt, list_clips
from plotloom.repo import find_repo_from_cwd

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


@prompt_group.command("compile")
@click.option("--episode", required=True)
@click.option("--clip", required=True)
@click.option("--adapter", required=True)
@click.option("--mode", required=True, type=click.Choice(MODES))
@click.option("--prompt-file", type=click.Path(path_type=str))
@click.option("--output", "output_path", type=click.Path(path_type=str))
@click.pass_context
def compile_command(
    ctx: click.Context,
    episode: str,
    clip: str,
    adapter: str,
    mode: str,
    prompt_file: str | None,
    output_path: str | None,
) -> None:
    path = _prompt_path(ctx, episode, prompt_file)
    text = _read_prompt_file(path)
    try:
        compiled = compile_prompt(text, clip, adapter, mode)
    except (KeyError, ValueError) as error:
        raise click.ClickException(str(error)) from error

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
        "prompt_sha256": compiled.prompt_sha256,
        "prompt_chars": compiled.prompt_chars,
        "warnings": compiled.warnings,
        "message": compiled.prompt_text,
    }
    if output_path:
        payload["path"] = str(Path(output_path).expanduser())
    emit(payload, as_json=ctx.obj.get("as_json"))


@prompt_group.command("check")
@click.option("--episode", required=True)
@click.option("--clip")
@click.option("--adapter", default="aliyun-bailian-wan", show_default=True)
@click.option("--mode", default="text-to-video", show_default=True, type=click.Choice(MODES))
@click.option("--prompt-file", type=click.Path(path_type=str))
@click.pass_context
def check_command(ctx: click.Context, episode: str, clip: str | None, adapter: str, mode: str, prompt_file: str | None) -> None:
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
        checks[clip_name] = {
            "ok": True,
            "prompt_sha256": compiled.prompt_sha256,
            "prompt_chars": compiled.prompt_chars,
            "warnings": compiled.warnings,
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
            "message": "prompt check ok" if not failed else f"prompt check failed: {', '.join(failed)}",
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


def _read_prompt_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise click.ClickException(f"prompt file not found: {path}") from error
    except OSError as error:
        raise click.ClickException(f"could not read prompt file: {path}") from error
