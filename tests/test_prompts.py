import hashlib
import json

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.prompts import compile_prompt, extract_clip_prompt, lint_provider_prompt, list_clips


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


def test_extract_supports_cli_prompt_marker_with_code_span():
    text = """
## clip-01
- Prompt string for `--prompt`:
  ```text
  Keep this prompt from the skill template.
  ```
- Ending frame / handoff point: stop here.
"""

    prompt = extract_clip_prompt(text, "clip-01")

    assert "Keep this prompt from the skill template." in prompt
    assert "```" not in prompt
    assert "Continuity rules" not in prompt
    assert "Ending frame" not in prompt


def test_extract_template_prompt_stops_before_following_template_fields():
    text = """
## clip-01
- Prompt string for `--prompt`:
  ```text
  Keep only the provider prompt.
  ```
- Continuity rules:
- Camera motion:
- Dialogue / audio window:
- Ending frame / handoff point:
- Adapter-specific notes:
"""

    assert extract_clip_prompt(text, "clip-01") == "Keep only the provider prompt."


def test_compile_volcengine_reference_prompt_adds_image_role_instruction():
    compiled = compile_prompt(PROMPTS, "clip-01", adapter="volcengine-seedance", mode="image-to-video")

    assert compiled.prompt_text.startswith("Use attached images by their request roles")
    assert "rainy lobby" in compiled.prompt_text


def test_compile_text_to_video_does_not_add_image_instruction():
    compiled = compile_prompt(PROMPTS, "clip-01", adapter="dreamina-cli", mode="text-to-video")

    assert compiled.prompt_text.startswith("A vertical short-drama")
    assert compiled.prompt_chars == len(compiled.prompt_text)
    assert compiled.prompt_sha256 == hashlib.sha256(compiled.prompt_text.encode("utf-8")).hexdigest()
    assert compiled.sha256 == compiled.prompt_sha256
    assert compiled.to_dict()["sha256"] == compiled.prompt_sha256
    assert compiled.warnings == []


def test_compile_empty_prompt_fails_clearly():
    text = """
## Clip 01
Prompt string:

Reference images:
- ref.png
"""

    try:
        compile_prompt(text, "clip-01", adapter="dreamina-cli", mode="text-to-video")
    except ValueError as error:
        assert "compiled prompt is empty" in str(error)
    else:
        raise AssertionError("empty prompt should fail")


def test_lint_provider_prompt_reports_reference_and_shot_list_risks():
    warnings = lint_provider_prompt("Shot 1: Image 2 enters.\nShot 2: 中文对白 appears.", reference_count=1)

    assert "Image 2" in warnings[0]
    assert any("CJK" in warning for warning in warnings)
    assert any("shot list" in warning for warning in warnings)


def test_prompt_check_lint_uses_reference_map(tmp_path):
    repo = _repo_with_prompts(
        tmp_path,
        """
## Clip 01
Prompt string:
Shot 1: Image 2 walks into frame.
Shot 2: 中文对白 appears on screen.
""",
    )
    reference = repo / "assets" / "cast" / "ethan" / "safe-face.png"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"png")
    plan = CliRunner().invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "plan-references",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--reference",
            "character:ethan=assets/cast/ethan/safe-face.png",
            "--write",
        ],
    )
    assert plan.exit_code == 0

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "prompt",
            "check",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--reference-map",
            "episodes/ep001/videos/clip-01/reference-map.toml",
        ],
    )

    assert result.exit_code == 0
    warnings = json.loads(result.output)["checks"]["clip-01"]["warnings"]
    assert any("Image 2" in warning for warning in warnings)
    assert any("CJK" in warning for warning in warnings)
    assert any("shot list" in warning for warning in warnings)


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
            "volcengine-seedance",
            "--mode",
            "reference-to-video",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "prompt.compile"
    assert payload["adapter"] == "volcengine-seedance"
    assert payload["prompt_chars"] == len(payload["prompt_text"])
    assert payload["sha256"] == payload["prompt_sha256"]
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
