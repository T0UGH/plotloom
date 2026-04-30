import hashlib
import json

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.prompts import compile_prompt, extract_clip_prompt, list_clips


PROMPTS = """
# EP001 Video Prompts EN

## Clip 01

Duration hint: 5 seconds
Ratio: 9:16

Prompt string:
A vertical short-drama shot in a rainy lobby. Dialogue: "You are the heir." No subtitles.

Reference images:
- assets/cast/lin-qiao/character-grid.png

## clip-02

Prompt string:
A second clip.
Ending frame:
She turns away.
"""


def test_list_clips_normalizes_headings():
    assert list_clips(PROMPTS) == ["clip-01", "clip-02"]


def test_extract_clip_prompt_string():
    prompt = extract_clip_prompt(PROMPTS, "clip-01")

    assert prompt.startswith("A vertical short-drama")
    assert "Reference images" not in prompt


def test_extract_clip_prompt_stops_at_ending_frame_marker():
    prompt = extract_clip_prompt(PROMPTS, "clip-02")

    assert prompt == "A second clip."


def test_extract_supports_inline_prompt_marker():
    text = """
## clip-01
- Duration hint: 15-20s
- Prompt: Keep the story text.
- Ending frame / handoff point: stop here.
"""

    assert extract_clip_prompt(text, "Clip 1") == "Keep the story text."


def test_compile_aliyun_reference_prompt_preserves_story_text():
    compiled = compile_prompt(PROMPTS, "clip-01", adapter="aliyun-bailian-wan", mode="reference-to-video")

    assert "Use provided images only as visual references." in compiled.prompt_text
    assert "rainy lobby" in compiled.prompt_text
    assert compiled.prompt_chars == len(compiled.prompt_text)
    assert compiled.prompt_sha256 == hashlib.sha256(compiled.prompt_text.encode("utf-8")).hexdigest()
    assert compiled.warnings == []


def test_compile_volcengine_reference_prompt_adds_image_role_instruction():
    compiled = compile_prompt(PROMPTS, "clip-01", adapter="volcengine-seedance", mode="image-to-video")

    assert compiled.prompt_text.startswith("Use attached images by their request roles")
    assert "rainy lobby" in compiled.prompt_text


def test_compile_text_to_video_does_not_add_image_instruction():
    compiled = compile_prompt(PROMPTS, "clip-01", adapter="aliyun-bailian-wan", mode="text-to-video")

    assert compiled.prompt_text.startswith("A vertical short-drama")


def test_compile_empty_prompt_fails_clearly():
    text = """
## Clip 01
Prompt string:

Reference images:
- ref.png
"""

    try:
        compile_prompt(text, "clip-01", adapter="aliyun-bailian-wan", mode="text-to-video")
    except ValueError as error:
        assert "compiled prompt is empty" in str(error)
    else:
        raise AssertionError("empty prompt should fail")


def test_prompt_list_command_json(tmp_path):
    repo = _repo_with_prompts(tmp_path, PROMPTS)

    result = CliRunner().invoke(main, ["--json", "--repo", str(repo), "prompt", "list", "--episode", "ep001"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "prompt.list"
    assert payload["clips"] == ["clip-01", "clip-02"]


def test_prompt_extract_command_outputs_plain_prompt(tmp_path):
    repo = _repo_with_prompts(tmp_path, PROMPTS)

    result = CliRunner().invoke(main, ["--repo", str(repo), "prompt", "extract", "--episode", "ep001", "--clip", "clip-01"])

    assert result.exit_code == 0
    assert "rainy lobby" in result.output
    assert "Reference images" not in result.output


def test_prompt_compile_command_json(tmp_path):
    repo = _repo_with_prompts(tmp_path, PROMPTS)

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "prompt",
            "compile",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--adapter",
            "aliyun-bailian-wan",
            "--mode",
            "reference-to-video",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "prompt.compile"
    assert payload["adapter"] == "aliyun-bailian-wan"
    assert payload["prompt_chars"] == len(payload["prompt_text"])
    assert "rainy lobby" in payload["prompt_text"]


def test_prompt_check_reports_empty_prompt_failure(tmp_path):
    repo = _repo_with_prompts(tmp_path, "## Clip 01\n\nPrompt string:\n\nReference images:\n- ref.png\n")

    result = CliRunner().invoke(
        main,
        ["--json", "--repo", str(repo), "prompt", "check", "--episode", "ep001", "--clip", "clip-01"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["command"] == "prompt.check"
    assert "compiled prompt is empty" in payload["checks"]["clip-01"]["error"]


def _repo_with_prompts(tmp_path, text):
    repo = tmp_path / "series"
    ep = repo / "episodes" / "ep001"
    ep.mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    (ep / "video-prompts-en.md").write_text(text, encoding="utf-8")
    return repo
