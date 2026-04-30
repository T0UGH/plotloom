from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "image_path": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": ["image_path", "notes"],
    "additionalProperties": True,
}


def codex_bin(binary: str = "codex") -> str:
    resolved = shutil.which(binary)
    if not resolved:
        raise RuntimeError(f"codex binary not found: {binary}")
    return resolved


class CodexImageAdapter:
    def __init__(self, codex_binary: str = "codex") -> None:
        self.codex_binary = codex_binary

    def generate(
        self,
        *,
        prompt_file: Path,
        output_dir: Path,
        filename: str,
        images: list[Path],
        timeout: int = 600,
    ) -> dict[str, Any]:
        prompt_path = Path(prompt_file).expanduser()
        prompt = prompt_path.read_text(encoding="utf-8")
        input_images = [_validate_image(path) for path in images]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as result_file:
            result_path = Path(result_file.name)
        try:
            args = [
                codex_bin(self.codex_binary),
                "exec",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--enable",
                "image_generation",
                "--output-schema",
                json.dumps(OUTPUT_SCHEMA),
                "--output-last-message",
                str(result_path),
                _build_prompt(prompt, input_images),
            ]
            completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
            payload = _load_result(result_path, completed.stdout)
            source = _source_image(payload) or _newest_generated_image()
            if source is None:
                raise RuntimeError("codex image generation did not return an image path")
            shutil.copy2(source, output_path)
            return {
                "ok": True,
                "image_path": str(output_path),
                "image_url": output_path.resolve().as_uri(),
                "source_image_path": str(source),
                "notes": str(payload.get("notes", "")),
                "input_images": [str(path) for path in input_images],
                "codex_exit_code": completed.returncode,
            }
        finally:
            result_path.unlink(missing_ok=True)


def _validate_image(path: Path) -> Path:
    image = Path(path).expanduser()
    if not image.exists():
        raise FileNotFoundError(f"image not found: {image}")
    if not image.is_file():
        raise ValueError(f"image is not a file: {image}")
    return image


def _build_prompt(prompt: str, images: list[Path]) -> str:
    if not images:
        return prompt
    image_lines = "\n".join(f"- {path}" for path in images)
    return f"{prompt}\n\nInput images:\n{image_lines}"


def _load_result(path: Path, stdout: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    if not text and stdout.strip():
        text = stdout.strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        data = json.loads(text[start : end + 1]) if start >= 0 and end > start else {}
    return data if isinstance(data, dict) else {}


def _source_image(payload: dict[str, Any]) -> Path | None:
    value = payload.get("image_path")
    if not value:
        return None
    path = Path(str(value).removeprefix("file://")).expanduser()
    return path if path.exists() else None


def _newest_generated_image() -> Path | None:
    generated = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser() / "generated_images"
    if not generated.exists():
        return None
    candidates = [path for path in generated.iterdir() if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)
