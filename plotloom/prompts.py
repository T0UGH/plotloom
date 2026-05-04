from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

CLIP_HEADING = re.compile(r"^##\s+(?P<clip>clip(?:\s+|-)\d+)\s*$", re.IGNORECASE | re.MULTILINE)
PROMPT_MARKER = re.compile(
    r"^\s*(?:[-*]\s*)?Prompt(?:\s+string)?(?:\s+for\s+`[^`]+`)?\s*:\s*(?P<inline>.*)$",
    re.IGNORECASE | re.MULTILINE,
)
STOP_MARKER = re.compile(
    r"^\s*(?:[-*]\s*)?(?:"
    r"Reference images(?:\s+and\s+purpose)?|"
    r"Duration hint|"
    r"Duration seconds|"
    r"Ratio|"
    r"Continuity rules|"
    r"Camera motion|"
    r"Dialogue\s*/\s*audio window|"
    r"Ending frame(?:\s*/\s*handoff point)?|"
    r"Adapter-specific notes"
    r"):",
    re.IGNORECASE | re.MULTILINE,
)
IMAGE_REFERENCE_MODES = {"image-to-video", "reference-to-video"}
IMAGE_SLOT = re.compile(r"\b(?:Image|image|图片)\s*(?P<slot>\d+)\b")
SHOT_LIST_LINE = re.compile(r"^\s*(?:\d+[.)]|Shot\s+\d+|镜头\s*\d+)", re.IGNORECASE | re.MULTILINE)
CJK_TEXT = re.compile(r"[\u4e00-\u9fff]")


@dataclass(frozen=True)
class CompiledPrompt:
    prompt_text: str
    prompt_sha256: str
    prompt_chars: int
    warnings: list[str]

    @property
    def sha256(self) -> str:
        return self.prompt_sha256

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["sha256"] = self.prompt_sha256
        return data


def _slug_clip(value: str) -> str:
    normalized = re.sub(r"\s+", "-", value.strip().lower())
    if re.fullmatch(r"clip-\d+", normalized):
        prefix, number = normalized.split("-", 1)
        return f"{prefix}-{int(number):02d}"
    return normalized


def _sections(text: str) -> dict[str, str]:
    matches = list(CLIP_HEADING.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[_slug_clip(match.group("clip"))] = text[start:end].strip()
    return sections


def list_clips(text: str) -> list[str]:
    return list(_sections(text).keys())


def extract_clip_prompt(text: str, clip: str) -> str:
    normalized_clip = _slug_clip(clip)
    sections = _sections(text)
    section = sections.get(normalized_clip)
    if section is None:
        raise KeyError(f"clip not found: {normalized_clip}")

    marker = PROMPT_MARKER.search(section)
    if marker is None:
        return ""

    inline = marker.group("inline").strip()
    body_start = marker.end()
    body = section[body_start:].strip()
    if inline:
        body = f"{inline}\n{body}".strip() if body else inline

    stop = STOP_MARKER.search(body)
    if stop:
        body = body[: stop.start()]
    return _strip_code_fence(body.strip())


def compile_prompt(text: str, clip: str, adapter: str, mode: str) -> CompiledPrompt:
    prompt = extract_clip_prompt(text, clip)
    warnings: list[str] = []
    normalized_adapter = adapter.strip().lower()
    normalized_mode = mode.strip().lower()

    if normalized_adapter == "volcengine-seedance" and normalized_mode in IMAGE_REFERENCE_MODES:
        prompt = _prepend_instruction(prompt, "Use attached images by their request roles: first_frame and reference_image.")
    elif not normalized_adapter:
        warnings.append("adapter is empty; compiled provider-neutral prompt")
    elif not normalized_mode:
        warnings.append("mode is empty; compiled provider-neutral prompt")

    if not prompt.strip():
        raise ValueError(f"compiled prompt is empty for {_slug_clip(clip)}")

    return CompiledPrompt(
        prompt_text=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        prompt_chars=len(prompt),
        warnings=warnings,
    )


def lint_provider_prompt(prompt: str, *, reference_count: int | None = None) -> list[str]:
    warnings: list[str] = []
    slots = [int(match.group("slot")) for match in IMAGE_SLOT.finditer(prompt)]
    if slots and reference_count is None:
        warnings.append("prompt references Image slots but no reference map was provided")
    elif slots and reference_count is not None and max(slots) > reference_count:
        warnings.append(f"prompt references Image {max(slots)} but reference map has {reference_count} entries")

    if CJK_TEXT.search(prompt):
        warnings.append("prompt contains CJK text; provider video models may render unwanted subtitles or text")

    shot_lines = SHOT_LIST_LINE.findall(prompt)
    if len(shot_lines) >= 2:
        warnings.append("prompt looks like a shot list; Seedance prompts should read as a continuous cinematic task")
    return warnings


def _prepend_instruction(prompt: str, instruction: str) -> str:
    prompt = prompt.strip()
    return f"{instruction}\n{prompt}" if prompt else prompt


def _strip_code_fence(value: str) -> str:
    lines = value.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(line.strip() for line in lines[1:-1]).strip()
    return value.strip()
