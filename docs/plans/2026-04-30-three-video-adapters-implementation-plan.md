# Three Video Adapters Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build Plotloom's first real async video adapter layer for `dreamina-cli`, `happyhorse-fal`, and `volcengine-seedance`, including provider-specific prompt/reference compilation, capability validation, task receipts, polling, downloads, and same-prompt comparison support.

**Architecture:** Keep Plotloom repo-first and runtime-light. Add a small Python package/CLI that compiles a normalized `PlotloomVideoRequest` into provider-native requests through adapter `capabilities()`, `validate_request()`, and `compile_native_request()`. Persist only visible TOML receipts and downloaded media under the series repo; no daemon, hidden DB, dashboard, or workflow runtime.

**Tech Stack:** Python 3.11+, argparse or click, stdlib `tomllib` + `tomli-w`, `requests`, optional `fal-client`, optional `volcengine-python-sdk[ark]`, external `dreamina` CLI, ffprobe/ffmpeg.

---

## Source docs and constraints

Read these before implementing:

- Design: `docs/design/2026-04-30-video-adapter-three-provider-integration.md`
- CLI design: `docs/design/cli-design.md`
- Adapter notes:
  - `adapters/dreamina.md`
  - `adapters/happyhorse-fal.md`
  - `adapters/volcengine-seedance.md`
- Downloaded provider references:
  - `docs/references/video-adapters/2026-04-30/dreamina-cli/`
  - `docs/references/video-adapters/2026-04-30/fal-happyhorse/`
  - `docs/references/video-adapters/2026-04-30/volcengine-seedance/`
- Existing deterministic scripts:
  - `scripts/init_series.py`
  - `scripts/validate_repo.py`
  - `scripts/adapters/fake_video.py`
  - `scripts/ffprobe_media.py`
  - `scripts/select_candidate.py`
  - `scripts/stitch_ffmpeg.py`

Important product boundaries:

- Do not implement daemon / runtime DB / dashboard / workflow engine.
- Do not bind Plotloom core to any one provider.
- Do not commit credentials, temporary signed URLs, OAuth links, QR contents, or API keys.
- Do not send the same raw `video-prompts-en.md` to all providers; compile provider-specific prompt text.
- Do not silently downgrade important parameters such as resolution unless the caller explicitly allows it.

---

## Target command surface

MVP commands should be available through Python scripts first; a later plan can wrap them as an installed `plotloom` command.

```bash
python3 scripts/video_submit.py \
  --repo ~/plotloom_repo/<slug> \
  --episode ep001 \
  --clip clip-01 \
  --adapter dreamina-cli \
  --mode text-to-video \
  --prompt-file episodes/ep001/video-prompts-en.md \
  --duration 15 \
  --ratio 9:16 \
  --resolution 720p

python3 scripts/video_poll.py \
  --repo ~/plotloom_repo/<slug> \
  --episode ep001 \
  --clip clip-01 \
  --receipt episodes/ep001/videos/clip-01/tasks/<adapter>-<timestamp>.toml
```

The future `plotloom video submit/poll` can wrap these scripts.

---

## Task 1: Add package skeleton for video adapters

**Objective:** Create a minimal importable Python module for shared video adapter code without changing existing scripts.

**Files:**
- Create: `plotloom/__init__.py`
- Create: `plotloom/video/__init__.py`
- Create: `plotloom/video/types.py`
- Create: `plotloom/video/adapters/__init__.py`
- Test: `tests/test_video_types.py`

**Step 1: Write failing test**

Create `tests/test_video_types.py`:

```python
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_plotloom_video_request_defaults():
    req = PlotloomVideoRequest(
        repo="/tmp/series",
        episode="ep001",
        clip="clip-01",
        adapter="dreamina-cli",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file="episodes/ep001/video-prompts-en.md",
        ratio="9:16",
        resolution="720p",
        duration=15,
    )

    assert req.audio_intent == "native_if_supported"
    assert req.reference_images == []
    assert req.first_frame is None
```

**Step 2: Run test to verify failure**

Run:

```bash
python3 -m pytest tests/test_video_types.py -v
```

Expected: FAIL because `plotloom.video.types` does not exist.

**Step 3: Implement minimal types**

Create `plotloom/__init__.py` and `plotloom/video/__init__.py` as empty files.

Create `plotloom/video/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal


class VideoMode(StrEnum):
    TEXT_TO_VIDEO = "text-to-video"
    IMAGE_TO_VIDEO = "image-to-video"
    REFERENCE_TO_VIDEO = "reference-to-video"
    VIDEO_EDIT = "video-edit"


AudioIntent = Literal["none", "native_if_supported", "require_native"]


@dataclass(frozen=True)
class PlotloomVideoRequest:
    repo: str
    episode: str
    clip: str
    adapter: str
    mode: VideoMode
    prompt_file: str
    ratio: str
    resolution: str
    duration: int
    audio_intent: AudioIntent = "native_if_supported"
    seed: int | None = None
    first_frame: str | None = None
    reference_images: list[str] = field(default_factory=list)
    reference_videos: list[str] = field(default_factory=list)
    reference_audios: list[str] = field(default_factory=list)
    source_video: str | None = None
    allow_downgrade: bool = False
    allow_normalize_duration: bool = False

    @property
    def repo_path(self) -> Path:
        return Path(self.repo).expanduser().resolve()
```

Create `plotloom/video/adapters/__init__.py` as empty.

**Step 4: Run test to verify pass**

Run:

```bash
python3 -m pytest tests/test_video_types.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom tests/test_video_types.py
git commit -m "feat: add video adapter request types"
```

---

## Task 2: Add adapter capability and validation primitives

**Objective:** Define reusable capability/validation contracts for all providers.

**Files:**
- Modify: `plotloom/video/types.py`
- Test: `tests/test_video_types.py`

**Step 1: Add failing tests**

Append to `tests/test_video_types.py`:

```python
from plotloom.video.types import ValidationIssue, ValidationResult, VideoAdapterCapabilities


def test_validation_result_blocks_errors():
    result = ValidationResult(
        issues=[ValidationIssue(level="error", code="BAD_DURATION", message="bad")]
    )
    assert not result.ok


def test_capabilities_has_modes_and_limits():
    caps = VideoAdapterCapabilities(
        adapter="happyhorse-fal",
        modes={"text-to-video"},
        min_duration=3,
        max_duration=15,
        ratios={"9:16"},
        resolutions={"720p"},
        supports_native_audio=True,
        supports_seed=True,
        supports_first_frame=True,
        supports_reference_images=True,
        supports_video_edit=True,
        local_file_strategy="fal_upload",
    )
    assert caps.adapter == "happyhorse-fal"
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_video_types.py -v
```

Expected: FAIL for missing classes.

**Step 3: Implement primitives**

Add to `plotloom/video/types.py`:

```python
@dataclass(frozen=True)
class VideoAdapterCapabilities:
    adapter: str
    modes: set[str]
    min_duration: int
    max_duration: int
    ratios: set[str] | str
    resolutions: set[str]
    supports_native_audio: bool
    supports_seed: bool
    supports_first_frame: bool
    supports_reference_images: bool
    supports_video_edit: bool
    local_file_strategy: Literal["cli_upload", "fal_upload", "url_or_base64", "none"]


@dataclass(frozen=True)
class ValidationIssue:
    level: Literal["error", "warning", "downgrade", "rewrite"]
    code: str
    message: str
    suggestion: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)
```

**Step 4: Run test**

```bash
python3 -m pytest tests/test_video_types.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/types.py tests/test_video_types.py
git commit -m "feat: add video adapter capability validation types"
```

---

## Task 3: Add provider capability declarations

**Objective:** Add capability modules for `dreamina-cli`, `happyhorse-fal`, and `volcengine-seedance`.

**Files:**
- Create: `plotloom/video/adapters/dreamina_cli.py`
- Create: `plotloom/video/adapters/happyhorse_fal.py`
- Create: `plotloom/video/adapters/volcengine_seedance.py`
- Test: `tests/test_video_adapter_capabilities.py`

**Step 1: Write failing tests**

Create `tests/test_video_adapter_capabilities.py`:

```python
from plotloom.video.adapters.dreamina_cli import capabilities as dreamina_capabilities
from plotloom.video.adapters.happyhorse_fal import capabilities as fal_capabilities
from plotloom.video.adapters.volcengine_seedance import capabilities as volc_capabilities


def test_dreamina_capabilities_match_cli_constraints():
    caps = dreamina_capabilities()
    assert caps.adapter == "dreamina-cli"
    assert caps.min_duration == 4
    assert caps.max_duration == 15
    assert caps.resolutions == {"720p"}
    assert "text-to-video" in caps.modes
    assert "image-to-video" in caps.modes


def test_happyhorse_capabilities_match_fal_schema():
    caps = fal_capabilities()
    assert caps.adapter == "happyhorse-fal"
    assert caps.min_duration == 3
    assert caps.max_duration == 15
    assert caps.resolutions == {"720p", "1080p"}
    assert "reference-to-video" in caps.modes
    assert caps.supports_video_edit


def test_volcengine_capabilities_match_seedance_constraints():
    caps = volc_capabilities()
    assert caps.adapter == "volcengine-seedance"
    assert caps.min_duration == 4
    assert caps.max_duration == 15
    assert "adaptive" in caps.ratios
    assert caps.local_file_strategy == "url_or_base64"
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_video_adapter_capabilities.py -v
```

Expected: FAIL due missing modules.

**Step 3: Implement modules**

Create `plotloom/video/adapters/dreamina_cli.py`:

```python
from __future__ import annotations

from plotloom.video.types import VideoAdapterCapabilities


def capabilities() -> VideoAdapterCapabilities:
    return VideoAdapterCapabilities(
        adapter="dreamina-cli",
        modes={"text-to-video", "image-to-video", "multimodal-to-video"},
        min_duration=4,
        max_duration=15,
        ratios={"1:1", "3:4", "16:9", "4:3", "9:16", "21:9", "from_input_image"},
        resolutions={"720p"},
        supports_native_audio=False,
        supports_seed=False,
        supports_first_frame=True,
        supports_reference_images=True,
        supports_video_edit=False,
        local_file_strategy="cli_upload",
    )
```

Create `plotloom/video/adapters/happyhorse_fal.py`:

```python
from __future__ import annotations

from plotloom.video.types import VideoAdapterCapabilities


def capabilities() -> VideoAdapterCapabilities:
    return VideoAdapterCapabilities(
        adapter="happyhorse-fal",
        modes={"text-to-video", "image-to-video", "reference-to-video", "video-edit"},
        min_duration=3,
        max_duration=15,
        ratios={"16:9", "9:16", "1:1", "4:3", "3:4"},
        resolutions={"720p", "1080p"},
        supports_native_audio=True,
        supports_seed=True,
        supports_first_frame=True,
        supports_reference_images=True,
        supports_video_edit=True,
        local_file_strategy="fal_upload",
    )
```

Create `plotloom/video/adapters/volcengine_seedance.py`:

```python
from __future__ import annotations

from plotloom.video.types import VideoAdapterCapabilities


def capabilities() -> VideoAdapterCapabilities:
    return VideoAdapterCapabilities(
        adapter="volcengine-seedance",
        modes={"text-to-video", "image-to-video", "reference-to-video"},
        min_duration=4,
        max_duration=15,
        ratios={"16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"},
        resolutions={"480p", "720p", "1080p"},
        supports_native_audio=True,
        supports_seed=False,
        supports_first_frame=True,
        supports_reference_images=True,
        supports_video_edit=False,
        local_file_strategy="url_or_base64",
    )
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_video_adapter_capabilities.py tests/test_video_types.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/adapters tests/test_video_adapter_capabilities.py
git commit -m "feat: declare video adapter capabilities"
```

---

## Task 4: Add shared validation helper

**Objective:** Validate mode, duration, resolution, ratio, and audio intent before provider submission.

**Files:**
- Create: `plotloom/video/validation.py`
- Test: `tests/test_video_validation.py`

**Step 1: Write failing tests**

Create `tests/test_video_validation.py`:

```python
from plotloom.video.adapters.dreamina_cli import capabilities as dreamina_capabilities
from plotloom.video.adapters.happyhorse_fal import capabilities as fal_capabilities
from plotloom.video.types import PlotloomVideoRequest, VideoMode
from plotloom.video.validation import validate_against_capabilities


def make_req(**overrides):
    data = dict(
        repo="/tmp/series",
        episode="ep001",
        clip="clip-01",
        adapter="dreamina-cli",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file="episodes/ep001/video-prompts-en.md",
        ratio="9:16",
        resolution="720p",
        duration=15,
    )
    data.update(overrides)
    return PlotloomVideoRequest(**data)


def test_rejects_too_short_for_dreamina():
    result = validate_against_capabilities(make_req(duration=3), dreamina_capabilities())
    assert not result.ok
    assert result.issues[0].code == "DURATION_OUT_OF_RANGE"


def test_accepts_3s_for_happyhorse():
    req = make_req(adapter="happyhorse-fal", duration=3)
    result = validate_against_capabilities(req, fal_capabilities())
    assert result.ok


def test_rejects_1080p_for_dreamina_without_downgrade():
    result = validate_against_capabilities(make_req(resolution="1080p"), dreamina_capabilities())
    assert not result.ok
    assert any(issue.code == "UNSUPPORTED_RESOLUTION" for issue in result.issues)
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_video_validation.py -v
```

Expected: FAIL because helper does not exist.

**Step 3: Implement helper**

Create `plotloom/video/validation.py`:

```python
from __future__ import annotations

from plotloom.video.types import PlotloomVideoRequest, ValidationIssue, ValidationResult, VideoAdapterCapabilities


def validate_against_capabilities(req: PlotloomVideoRequest, caps: VideoAdapterCapabilities) -> ValidationResult:
    issues: list[ValidationIssue] = []

    if req.mode.value not in caps.modes:
        issues.append(ValidationIssue(
            level="error",
            code="UNSUPPORTED_MODE",
            message=f"{caps.adapter} does not support mode {req.mode.value}",
        ))

    if req.duration < caps.min_duration or req.duration > caps.max_duration:
        issues.append(ValidationIssue(
            level="error",
            code="DURATION_OUT_OF_RANGE",
            message=f"{caps.adapter} supports duration {caps.min_duration}-{caps.max_duration}s, got {req.duration}s",
            suggestion=f"Use a duration between {caps.min_duration} and {caps.max_duration} seconds.",
        ))

    if req.resolution not in caps.resolutions:
        level = "downgrade" if req.allow_downgrade else "error"
        issues.append(ValidationIssue(
            level=level,
            code="UNSUPPORTED_RESOLUTION",
            message=f"{caps.adapter} does not support resolution {req.resolution}",
            suggestion=f"Supported resolutions: {', '.join(sorted(caps.resolutions))}",
        ))

    if isinstance(caps.ratios, set) and req.ratio not in caps.ratios:
        issues.append(ValidationIssue(
            level="error",
            code="UNSUPPORTED_RATIO",
            message=f"{caps.adapter} does not support ratio {req.ratio}",
            suggestion=f"Supported ratios: {', '.join(sorted(caps.ratios))}",
        ))

    if req.audio_intent == "require_native" and not caps.supports_native_audio:
        issues.append(ValidationIssue(
            level="error",
            code="NATIVE_AUDIO_REQUIRED",
            message=f"{caps.adapter} cannot guarantee native audio",
        ))

    return ValidationResult(issues=issues)
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_video_validation.py tests/test_video_adapter_capabilities.py tests/test_video_types.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/validation.py tests/test_video_validation.py
git commit -m "feat: validate normalized video requests"
```

---

## Task 5: Add provider prompt compiler interface and Dreamina compiler

**Objective:** Compile normalized prompt text into Dreamina-specific prompt text.

**Files:**
- Create: `plotloom/video/prompts.py`
- Modify: `plotloom/video/adapters/dreamina_cli.py`
- Test: `tests/test_prompt_compilers.py`

**Step 1: Write failing test**

Create `tests/test_prompt_compilers.py`:

```python
from pathlib import Path

from plotloom.video.adapters.dreamina_cli import compile_prompt
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_dreamina_i2v_prompt_mentions_first_frame(tmp_path: Path):
    prompt_file = tmp_path / "video-prompts-en.md"
    prompt_file.write_text("A delivery man enters a luxury lobby.")
    req = PlotloomVideoRequest(
        repo=str(tmp_path),
        episode="ep001",
        clip="clip-01",
        adapter="dreamina-cli",
        mode=VideoMode.IMAGE_TO_VIDEO,
        prompt_file=str(prompt_file),
        ratio="9:16",
        resolution="720p",
        duration=15,
        first_frame="first.png",
    )

    compiled = compile_prompt(req)

    assert "Use the input image as the first frame" in compiled
    assert "A delivery man enters a luxury lobby" in compiled
    assert "character1" not in compiled
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_prompt_compilers.py -v
```

Expected: FAIL because `compile_prompt` does not exist.

**Step 3: Implement shared prompt reading and Dreamina compiler**

Create `plotloom/video/prompts.py`:

```python
from __future__ import annotations

from pathlib import Path


def read_prompt_text(prompt_file: str, repo: str | None = None) -> str:
    path = Path(prompt_file).expanduser()
    if not path.is_absolute() and repo:
        path = Path(repo).expanduser().resolve() / path
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Prompt file is empty: {path}")
    return text
```

Modify `plotloom/video/adapters/dreamina_cli.py`:

```python
from plotloom.video.prompts import read_prompt_text
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def compile_prompt(req: PlotloomVideoRequest) -> str:
    base = read_prompt_text(req.prompt_file, req.repo)
    if req.mode == VideoMode.IMAGE_TO_VIDEO:
        return (
            "Use the input image as the first frame. Keep the character's face, outfit, "
            "and environment consistent. " + base
        )
    if req.mode.value == "multimodal-to-video":
        return (
            "Use the provided media references according to their semantic roles. "
            "Do not add subtitles, logos, or watermarks. " + base
        )
    return base
```

Preserve the existing `capabilities()` function.

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_prompt_compilers.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/prompts.py plotloom/video/adapters/dreamina_cli.py tests/test_prompt_compilers.py
git commit -m "feat: compile Dreamina video prompts"
```

---

## Task 6: Add HappyHorse prompt compiler

**Objective:** Compile HappyHorse prompts with `character1..9` / `@Image1..5` reference binding and 2500-char guard.

**Files:**
- Modify: `plotloom/video/adapters/happyhorse_fal.py`
- Modify: `tests/test_prompt_compilers.py`

**Step 1: Add failing tests**

Append to `tests/test_prompt_compilers.py`:

```python
from plotloom.video.adapters.happyhorse_fal import compile_prompt as compile_happyhorse_prompt


def test_happyhorse_ref2v_prompt_binds_character_labels(tmp_path: Path):
    prompt_file = tmp_path / "video-prompts-en.md"
    prompt_file.write_text("The delivery man enters the lobby.")
    req = PlotloomVideoRequest(
        repo=str(tmp_path),
        episode="ep001",
        clip="clip-01",
        adapter="happyhorse-fal",
        mode=VideoMode.REFERENCE_TO_VIDEO,
        prompt_file=str(prompt_file),
        ratio="9:16",
        resolution="720p",
        duration=15,
        reference_images=["hero.png", "heiress.png"],
    )

    compiled = compile_happyhorse_prompt(req)

    assert "character1" in compiled
    assert "character2" in compiled
    assert "The delivery man enters the lobby" in compiled
    assert len(compiled) <= 2500


def test_happyhorse_prompt_too_long_fails(tmp_path: Path):
    prompt_file = tmp_path / "video-prompts-en.md"
    prompt_file.write_text("x" * 2600)
    req = PlotloomVideoRequest(
        repo=str(tmp_path),
        episode="ep001",
        clip="clip-01",
        adapter="happyhorse-fal",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file=str(prompt_file),
        ratio="9:16",
        resolution="720p",
        duration=15,
    )

    try:
        compile_happyhorse_prompt(req)
    except ValueError as exc:
        assert "2500" in str(exc)
    else:
        raise AssertionError("Expected long HappyHorse prompt to fail")
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_prompt_compilers.py -v
```

Expected: FAIL because HappyHorse compiler missing.

**Step 3: Implement compiler**

Modify `plotloom/video/adapters/happyhorse_fal.py`:

```python
from plotloom.video.prompts import read_prompt_text
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def _ensure_2500(text: str) -> str:
    if len(text) > 2500:
        raise ValueError(f"HappyHorse prompt must be <= 2500 chars, got {len(text)}")
    return text


def compile_prompt(req: PlotloomVideoRequest) -> str:
    base = read_prompt_text(req.prompt_file, req.repo)
    if req.mode == VideoMode.REFERENCE_TO_VIDEO:
        bindings = [
            f"character{i} refers to reference image {i}."
            for i, _ in enumerate(req.reference_images, start=1)
        ]
        text = " ".join(bindings + [base])
        return _ensure_2500(text)
    if req.mode == VideoMode.VIDEO_EDIT and req.reference_images:
        bindings = [
            f"@Image{i} is reference image {i}."
            for i, _ in enumerate(req.reference_images[:5], start=1)
        ]
        text = " ".join(bindings + [base])
        return _ensure_2500(text)
    return _ensure_2500(base)
```

Preserve existing `capabilities()`.

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_prompt_compilers.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/adapters/happyhorse_fal.py tests/test_prompt_compilers.py
git commit -m "feat: compile HappyHorse video prompts"
```

---

## Task 7: Add VolcEngine prompt compiler

**Objective:** Compile VolcEngine prompts that use natural-language role descriptions instead of HappyHorse `character1` labels.

**Files:**
- Modify: `plotloom/video/adapters/volcengine_seedance.py`
- Modify: `tests/test_prompt_compilers.py`

**Step 1: Add failing test**

Append to `tests/test_prompt_compilers.py`:

```python
from plotloom.video.adapters.volcengine_seedance import compile_prompt as compile_volc_prompt


def test_volc_prompt_uses_natural_reference_description(tmp_path: Path):
    prompt_file = tmp_path / "video-prompts-en.md"
    prompt_file.write_text("The delivery man enters the lobby.")
    req = PlotloomVideoRequest(
        repo=str(tmp_path),
        episode="ep001",
        clip="clip-01",
        adapter="volcengine-seedance",
        mode=VideoMode.IMAGE_TO_VIDEO,
        prompt_file=str(prompt_file),
        ratio="9:16",
        resolution="720p",
        duration=15,
        first_frame="first.png",
        reference_images=["hero.png"],
    )

    compiled = compile_volc_prompt(req)

    assert "Use the first-frame image as the opening frame" in compiled
    assert "character1" not in compiled
    assert "The delivery man enters the lobby" in compiled
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_prompt_compilers.py -v
```

Expected: FAIL because Volc compiler missing.

**Step 3: Implement compiler**

Modify `plotloom/video/adapters/volcengine_seedance.py`:

```python
from plotloom.video.prompts import read_prompt_text
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def compile_prompt(req: PlotloomVideoRequest) -> str:
    base = read_prompt_text(req.prompt_file, req.repo)
    prefixes: list[str] = []
    if req.first_frame:
        prefixes.append("Use the first-frame image as the opening frame.")
    if req.reference_images:
        prefixes.append(
            "Use the reference image(s) only for identity, outfit, style, and environment consistency."
        )
    if req.audio_intent != "none":
        prefixes.append("Follow the dialogue, sound, and ambience described in the prompt.")
    return " ".join(prefixes + [base])
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_prompt_compilers.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/adapters/volcengine_seedance.py tests/test_prompt_compilers.py
git commit -m "feat: compile VolcEngine Seedance prompts"
```

---

## Task 8: Add receipt writer/reader

**Objective:** Persist visible TOML task receipts under `episodes/<episode>/videos/<clip>/tasks/`.

**Files:**
- Create: `plotloom/video/receipts.py`
- Test: `tests/test_video_receipts.py`

**Step 1: Write failing tests**

Create `tests/test_video_receipts.py`:

```python
from pathlib import Path

from plotloom.video.receipts import make_receipt_path, write_receipt


def test_make_receipt_path_uses_clip_tasks_dir(tmp_path: Path):
    path = make_receipt_path(tmp_path, "ep001", "clip-01", "happyhorse-fal", now="20260430-120000")
    assert path == tmp_path / "episodes/ep001/videos/clip-01/tasks/happyhorse-fal-20260430-120000.toml"


def test_write_receipt_creates_file(tmp_path: Path):
    path = tmp_path / "receipt.toml"
    write_receipt(path, {"adapter": "dreamina-cli", "status": "submitted"})
    text = path.read_text()
    assert 'adapter = "dreamina-cli"' in text
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_video_receipts.py -v
```

Expected: FAIL because module missing.

**Step 3: Implement receipts**

Create `plotloom/video/receipts.py`:

```python
from __future__ import annotations

from pathlib import Path

try:
    import tomli_w
except ImportError:  # pragma: no cover
    tomli_w = None


def make_receipt_path(repo: str | Path, episode: str, clip: str, adapter: str, now: str) -> Path:
    return Path(repo).expanduser().resolve() / "episodes" / episode / "videos" / clip / "tasks" / f"{adapter}-{now}.toml"


def write_receipt(path: str | Path, data: dict) -> None:
    if tomli_w is None:
        raise RuntimeError("tomli-w is required to write TOML receipts")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(tomli_w.dumps(data), encoding="utf-8")
```

**Step 4: Run test**

```bash
python3 -m pytest tests/test_video_receipts.py -v
```

Expected: PASS, or fail with missing `tomli-w`. If missing, add dependency/install note and use a tiny local TOML writer only for flat strings/numbers/bools in this task.

**Step 5: Commit**

```bash
git add plotloom/video/receipts.py tests/test_video_receipts.py
git commit -m "feat: write visible video task receipts"
```

---

## Task 9: Add media download helper and ffprobe wrapper

**Objective:** Download provider result URLs into numbered candidate files and run ffprobe.

**Files:**
- Create: `plotloom/video/media.py`
- Test: `tests/test_video_media.py`

**Step 1: Write failing tests**

Create `tests/test_video_media.py`:

```python
from pathlib import Path

from plotloom.video.media import next_candidate_path


def test_next_candidate_path_uses_adapter_suffix(tmp_path: Path):
    candidates = tmp_path / "candidates"
    candidates.mkdir()
    (candidates / "v001.dreamina-cli.mp4").write_text("x")

    path = next_candidate_path(candidates, "happyhorse-fal")

    assert path.name == "v002.happyhorse-fal.mp4"
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_video_media.py -v
```

Expected: FAIL because module missing.

**Step 3: Implement helper**

Create `plotloom/video/media.py`:

```python
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import json
import requests


def next_candidate_path(candidates_dir: str | Path, adapter: str) -> Path:
    d = Path(candidates_dir)
    d.mkdir(parents=True, exist_ok=True)
    max_n = 0
    for p in d.glob("v*.mp4"):
        m = re.match(r"v(\d{3})\.", p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return d / f"v{max_n + 1:03d}.{adapter}.mp4"


def download_url(url: str, dest: str | Path, timeout: int = 120) -> Path:
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    p.write_bytes(response.content)
    return p


def ffprobe_json(path: str | Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)
```

**Step 4: Run test**

```bash
python3 -m pytest tests/test_video_media.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add plotloom/video/media.py tests/test_video_media.py
git commit -m "feat: add video candidate media helpers"
```

---

## Task 10: Implement `scripts/video_submit.py` skeleton

**Objective:** Add a provider-agnostic submit script that validates request, compiles prompt, and writes a receipt without calling real providers yet.

**Files:**
- Create: `scripts/video_submit.py`
- Test: `tests/test_video_submit_script.py`

**Step 1: Write failing integration-style test**

Create `tests/test_video_submit_script.py`:

```python
from pathlib import Path
import subprocess
import sys


def test_video_submit_dry_run_writes_receipt(tmp_path: Path):
    repo = tmp_path / "series"
    prompt = repo / "episodes/ep001/video-prompts-en.md"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("A vertical short drama scene.")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/video_submit.py",
            "--repo", str(repo),
            "--episode", "ep001",
            "--clip", "clip-01",
            "--adapter", "happyhorse-fal",
            "--mode", "text-to-video",
            "--prompt-file", "episodes/ep001/video-prompts-en.md",
            "--duration", "3",
            "--ratio", "9:16",
            "--resolution", "720p",
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "receipt" in result.stdout
    receipts = list((repo / "episodes/ep001/videos/clip-01/tasks").glob("happyhorse-fal-*.toml"))
    assert len(receipts) == 1
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_video_submit_script.py -v
```

Expected: FAIL because script missing.

**Step 3: Implement dry-run submit**

Create `scripts/video_submit.py` with argparse that:

1. Parses `--repo`, `--episode`, `--clip`, `--adapter`, `--mode`, `--prompt-file`, `--duration`, `--ratio`, `--resolution`, `--dry-run`.
2. Builds `PlotloomVideoRequest`.
3. Loads adapter module by name.
4. Runs validation.
5. Compiles prompt.
6. Writes receipt with `status = "dry_run"` and prompt metadata.
7. Prints receipt path.

Implementation skeleton:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
from datetime import datetime
from pathlib import Path
import sys

from plotloom.video.receipts import make_receipt_path, write_receipt
from plotloom.video.types import PlotloomVideoRequest, VideoMode
from plotloom.video.validation import validate_against_capabilities

ADAPTER_MODULES = {
    "dreamina-cli": "plotloom.video.adapters.dreamina_cli",
    "happyhorse-fal": "plotloom.video.adapters.happyhorse_fal",
    "volcengine-seedance": "plotloom.video.adapters.volcengine_seedance",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--adapter", required=True, choices=sorted(ADAPTER_MODULES))
    parser.add_argument("--mode", required=True, choices=[m.value for m in VideoMode])
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--duration", type=int, required=True)
    parser.add_argument("--ratio", required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    req = PlotloomVideoRequest(
        repo=args.repo,
        episode=args.episode,
        clip=args.clip,
        adapter=args.adapter,
        mode=VideoMode(args.mode),
        prompt_file=args.prompt_file,
        ratio=args.ratio,
        resolution=args.resolution,
        duration=args.duration,
    )

    module = importlib.import_module(ADAPTER_MODULES[args.adapter])
    validation = validate_against_capabilities(req, module.capabilities())
    if not validation.ok:
        for issue in validation.issues:
            print(f"{issue.level.upper()} {issue.code}: {issue.message}", file=sys.stderr)
        return 2

    compiled_prompt = module.compile_prompt(req)
    prompt_hash = hashlib.sha256(compiled_prompt.encode("utf-8")).hexdigest()
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    receipt_path = make_receipt_path(req.repo_path, req.episode, req.clip, req.adapter, now)
    write_receipt(receipt_path, {
        "adapter": req.adapter,
        "status": "dry_run" if args.dry_run else "not_submitted",
        "mode": req.mode.value,
        "episode": req.episode,
        "clip": req.clip,
        "ratio": req.ratio,
        "resolution": req.resolution,
        "duration": req.duration,
        "prompt": {
            "source_file": req.prompt_file,
            "compiled_sha256": prompt_hash,
            "compiled_chars": len(compiled_prompt),
        },
    })
    print(f"receipt={receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run test**

```bash
python3 -m pytest tests/test_video_submit_script.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/video_submit.py tests/test_video_submit_script.py
git commit -m "feat: add dry-run video submit script"
```

---

## Task 11: Implement Dreamina real submit/poll

**Objective:** Add real Dreamina submit and poll execution while keeping credentials outside repo.

**Files:**
- Modify: `plotloom/video/adapters/dreamina_cli.py`
- Modify: `scripts/video_submit.py`
- Create: `scripts/video_poll.py`
- Test: `tests/test_dreamina_command_compile.py`

**Step 1: Write command compile tests**

Create `tests/test_dreamina_command_compile.py`:

```python
from plotloom.video.adapters.dreamina_cli import compile_submit_command
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_dreamina_t2v_command_has_explicit_duration_and_resolution():
    req = PlotloomVideoRequest(
        repo="/tmp/series",
        episode="ep001",
        clip="clip-01",
        adapter="dreamina-cli",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file="prompt.md",
        ratio="9:16",
        resolution="720p",
        duration=15,
    )
    cmd = compile_submit_command(req, "prompt text", dreamina_bin="dreamina")
    assert cmd[:2] == ["dreamina", "text2video"]
    assert "--duration=15" in cmd
    assert "--video_resolution=720p" in cmd
    assert "--poll=0" in cmd
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_dreamina_command_compile.py -v
```

Expected: FAIL.

**Step 3: Implement command compiler**

Add `compile_submit_command()` to `plotloom/video/adapters/dreamina_cli.py`.

Rules:

- T2V -> `dreamina text2video` with `--prompt`, `--duration`, `--ratio`, `--video_resolution`, `--model_version=seedance2.0fast`, `--poll=0`.
- I2V -> `dreamina image2video` with `--image`, `--prompt`, `--duration`, `--video_resolution`, `--model_version=seedance2.0fast`, `--poll=0`; no ratio flag.
- Multimodal -> future; do not implement until test coverage exists.

**Step 4: Integrate script real mode**

Modify `scripts/video_submit.py`:

- If `--dry-run`, keep current behavior.
- If adapter is `dreamina-cli`, run command with `subprocess.run(...)` using `HOME=/Users/wangguiping` only if env var `PLOTLOOM_DREAMINA_HOME` is not set.
- Parse `submit_id` from stdout conservatively.
- Write receipt with `remote_task_id = submit_id`, `status = "submitted"`, raw stdout path or redacted stdout summary.

Create `scripts/video_poll.py` for Dreamina only first:

- Read receipt TOML.
- Run `dreamina query_result --submit_id=<id> --download_dir=<candidate-dir>`.
- On success/download, rename file to `vNNN.dreamina-cli.mp4` and ffprobe.

**Step 5: Manual verification only if account is ready**

Run preflight:

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina user_credit
```

If ready, run a 4s smoke prompt. If not ready, do not attempt login; record blocker.

**Step 6: Commit**

```bash
git add plotloom/video/adapters/dreamina_cli.py scripts/video_submit.py scripts/video_poll.py tests/test_dreamina_command_compile.py
git commit -m "feat: add Dreamina video submit poll adapter"
```

---

## Task 12: Implement HappyHorse/fal real submit/poll

**Objective:** Add fal submit/poll with local upload support and receipt persistence.

**Files:**
- Modify: `plotloom/video/adapters/happyhorse_fal.py`
- Modify: `scripts/video_submit.py`
- Modify: `scripts/video_poll.py`
- Test: `tests/test_happyhorse_native_request.py`

**Step 1: Write native request tests**

Create `tests/test_happyhorse_native_request.py`:

```python
from plotloom.video.adapters.happyhorse_fal import compile_native_arguments, endpoint_for_mode
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_happyhorse_endpoint_for_ref2v():
    assert endpoint_for_mode(VideoMode.REFERENCE_TO_VIDEO) == "alibaba/happy-horse/reference-to-video"


def test_happyhorse_ref2v_arguments_use_image_urls():
    req = PlotloomVideoRequest(
        repo="/tmp/series",
        episode="ep001",
        clip="clip-01",
        adapter="happyhorse-fal",
        mode=VideoMode.REFERENCE_TO_VIDEO,
        prompt_file="prompt.md",
        ratio="9:16",
        resolution="720p",
        duration=15,
        reference_images=["hero.png"],
    )
    args = compile_native_arguments(req, "character1 enters", image_urls=["https://x/hero.png"])
    assert args["image_urls"] == ["https://x/hero.png"]
    assert args["aspect_ratio"] == "9:16"
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_happyhorse_native_request.py -v
```

Expected: FAIL.

**Step 3: Implement native request helpers**

Add to `plotloom/video/adapters/happyhorse_fal.py`:

- `endpoint_for_mode(mode)`
- `compile_native_arguments(req, compiled_prompt, image_url=None, image_urls=None, video_url=None)`
- `upload_local_files(paths)` using `fal_client.upload_file` but make it injectable/testable.

**Step 4: Integrate submit/poll**

Modify `scripts/video_submit.py`:

- Preflight `FAL_KEY` exists for real fal submit.
- Upload local first frame/reference/source video as needed.
- Call `fal_client.submit(endpoint, arguments=args)`.
- Write receipt with endpoint + request_id.

Modify `scripts/video_poll.py`:

- For `happyhorse-fal`, use endpoint + request_id to get status/result.
- On completed, download `result["video"]["url"]` to next candidate path.
- Run ffprobe and update receipt.

**Step 5: Manual verification only with funded key**

```bash
python3 scripts/video_submit.py ... --adapter happyhorse-fal --mode text-to-video --duration 3 --resolution 720p
python3 scripts/video_poll.py ... --receipt <receipt>
```

If `FAL_KEY` missing, skip real call and report blocker.

**Step 6: Commit**

```bash
git add plotloom/video/adapters/happyhorse_fal.py scripts/video_submit.py scripts/video_poll.py tests/test_happyhorse_native_request.py
git commit -m "feat: add HappyHorse fal video adapter"
```

---

## Task 13: Implement VolcEngine Seedance real submit/poll

**Objective:** Add VolcEngine Ark task submit/poll with content role mapping and immediate download.

**Files:**
- Modify: `plotloom/video/adapters/volcengine_seedance.py`
- Modify: `scripts/video_submit.py`
- Modify: `scripts/video_poll.py`
- Test: `tests/test_volcengine_native_request.py`

**Step 1: Write native content tests**

Create `tests/test_volcengine_native_request.py`:

```python
from plotloom.video.adapters.volcengine_seedance import compile_content
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_volc_content_includes_first_frame_role():
    req = PlotloomVideoRequest(
        repo="/tmp/series",
        episode="ep001",
        clip="clip-01",
        adapter="volcengine-seedance",
        mode=VideoMode.IMAGE_TO_VIDEO,
        prompt_file="prompt.md",
        ratio="9:16",
        resolution="720p",
        duration=15,
        first_frame="first.png",
    )
    content = compile_content(req, "prompt", first_frame_url="https://x/first.png")
    assert content[0] == {"type": "text", "text": "prompt"}
    assert content[1]["role"] == "first_frame"
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_volcengine_native_request.py -v
```

Expected: FAIL.

**Step 3: Implement content compiler**

Add to `plotloom/video/adapters/volcengine_seedance.py`:

- `compile_content(req, compiled_prompt, first_frame_url=None, reference_image_urls=None)`.
- Use `role="first_frame"` for first frame.
- Use `role="reference_image"` for reference images.
- Do not use `character1` labels.

**Step 4: Integrate submit/poll**

Modify `scripts/video_submit.py`:

- Preflight `ARK_API_KEY` exists for real VolcEngine submit.
- Support URL inputs first; local upload/base64 can be added after initial T2V smoke.
- Call `client.content_generation.tasks.create(...)`.
- Write receipt with task id and status.

Modify `scripts/video_poll.py`:

- Query `client.content_generation.tasks.get(task_id=...)`.
- On `succeeded`, download `task.content.video_url` immediately to `vNNN.volcengine-seedance.mp4`.
- Record status, timings, media facts.

**Step 5: Manual verification only with key/model enabled**

```bash
python3 scripts/video_submit.py ... --adapter volcengine-seedance --mode text-to-video --duration 4 --resolution 720p
python3 scripts/video_poll.py ... --receipt <receipt>
```

If `ARK_API_KEY` missing or model not enabled, skip real call and report blocker.

**Step 6: Commit**

```bash
git add plotloom/video/adapters/volcengine_seedance.py scripts/video_submit.py scripts/video_poll.py tests/test_volcengine_native_request.py
git commit -m "feat: add VolcEngine Seedance video adapter"
```

---

## Task 14: Add comparison report generator

**Objective:** Generate a markdown comparison table from receipts for the same clip.

**Files:**
- Create: `scripts/video_compare.py`
- Test: `tests/test_video_compare.py`

**Step 1: Write failing test**

Create `tests/test_video_compare.py`:

```python
from pathlib import Path
import subprocess
import sys


def test_video_compare_outputs_adapter_names(tmp_path: Path):
    tasks = tmp_path / "episodes/ep001/videos/clip-01/tasks"
    tasks.mkdir(parents=True)
    (tasks / "dreamina-cli-1.toml").write_text('adapter = "dreamina-cli"\nstatus = "succeeded"\ntotal_elapsed_sec = 10\n')
    (tasks / "happyhorse-fal-1.toml").write_text('adapter = "happyhorse-fal"\nstatus = "succeeded"\ntotal_elapsed_sec = 8\n')

    result = subprocess.run(
        [sys.executable, "scripts/video_compare.py", "--clip-dir", str(tasks.parent)],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "dreamina-cli" in result.stdout
    assert "happyhorse-fal" in result.stdout
```

**Step 2: Run test to verify failure**

```bash
python3 -m pytest tests/test_video_compare.py -v
```

Expected: FAIL.

**Step 3: Implement script**

Create `scripts/video_compare.py`:

- Read `tasks/*.toml`.
- Output markdown table with adapter, status, duration, total elapsed, has audio, candidate path, error.
- Do not require all fields.

**Step 4: Run test**

```bash
python3 -m pytest tests/test_video_compare.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/video_compare.py tests/test_video_compare.py
git commit -m "feat: add video adapter comparison report"
```

---

## Task 15: Final integration verification

**Objective:** Verify the three-adapter implementation is ready for real key-based testing.

**Files:**
- Modify if needed: `docs/design/2026-04-30-video-adapter-three-provider-integration.md`
- Modify if needed: `adapters/*.md`

**Step 1: Run full tests**

```bash
python3 -m pytest tests/ -v
```

Expected: all tests PASS.

**Step 2: Run dry-run commands for all three adapters**

Create a temporary series repo under `/tmp/plotloom-three-adapter-test` and run:

```bash
python3 scripts/video_submit.py --repo /tmp/plotloom-three-adapter-test --episode ep001 --clip clip-01 --adapter dreamina-cli --mode text-to-video --prompt-file episodes/ep001/video-prompts-en.md --duration 4 --ratio 9:16 --resolution 720p --dry-run
python3 scripts/video_submit.py --repo /tmp/plotloom-three-adapter-test --episode ep001 --clip clip-01 --adapter happyhorse-fal --mode text-to-video --prompt-file episodes/ep001/video-prompts-en.md --duration 3 --ratio 9:16 --resolution 720p --dry-run
python3 scripts/video_submit.py --repo /tmp/plotloom-three-adapter-test --episode ep001 --clip clip-01 --adapter volcengine-seedance --mode text-to-video --prompt-file episodes/ep001/video-prompts-en.md --duration 4 --ratio 9:16 --resolution 720p --dry-run
```

Expected: each writes a visible receipt under `episodes/ep001/videos/clip-01/tasks/`.

**Step 3: Run static secret scan on committed docs/references**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys
root = Path('docs/references/video-adapters/2026-04-30')
patterns = [r'AKLT[a-zA-Z0-9]+', r'AKTP[a-zA-Z0-9]+', r'AKIA[0-9A-Z]+', r'X-Tos-Credential=[^\\&"\s]+', r'X-Tos-Signature=[^\\&"\s]+']
for path in root.rglob('*'):
    if path.is_file():
        text = path.read_text(errors='ignore')
        for pat in patterns:
            if re.search(pat, text):
                print(f'possible secret pattern {pat} in {path}')
                sys.exit(1)
print('reference snapshots sanitized')
PY
```

Expected: `reference snapshots sanitized`.

**Step 4: Review docs alignment**

Check that:

- `docs/design/cli-design.md` still says this phase integrates all three providers.
- `adapters/dreamina.md`, `adapters/happyhorse-fal.md`, `adapters/volcengine-seedance.md` match implemented behavior.
- No code path prints API keys or credential files.

**Step 5: Commit final fixes**

If changes were needed:

```bash
git add <changed-files>
git commit -m "chore: verify three video adapter implementation"
```

**Step 6: Push with user HOME if needed**

```bash
git pull --rebase --autostash
HOME=/Users/wangguiping git push
```

Expected: push succeeds and `git rev-parse HEAD` equals `git ls-remote origin main | cut -f1`.

---

## Acceptance criteria

The implementation is complete when:

1. `scripts/video_submit.py --dry-run` works for all three adapters and writes receipts.
2. Each adapter declares capabilities and validates unsupported duration/resolution/mode/ratio/audio intent.
3. Each adapter compiles provider-specific prompt/reference text.
4. Dreamina real submit/poll works when host is logged in and maestro.
5. HappyHorse/fal real submit/poll works when `FAL_KEY` and credits exist.
6. VolcEngine real submit/poll works when `ARK_API_KEY` and model access exist.
7. Successful real polls download local candidate mp4 files and ffprobe them.
8. Comparison report can summarize receipts for a clip.
9. No credentials, signed URLs, or secret-like doc examples are committed.
10. Full tests pass.

## Handoff notes

- If real provider credentials are missing, do not block the code implementation. Mark real-call verification as blocked and keep dry-run + unit tests green.
- If provider API surface differs during real testing, update adapter notes and tests before changing implementation.
- Use subagent-driven-development for implementation: one fresh subagent per task, then spec compliance review, then code quality review.
