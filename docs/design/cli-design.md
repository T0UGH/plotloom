# Plotloom CLI Design

> Status: Draft v0.1  
> Date: 2026-04-30  
> Owner: 贵平  
> Agent: Nova  
> Source: PRD discussion + Superpowers-style brainstorm + existing Plotloom MVP skill pack

## 1. Design Hypothesis

Plotloom should grow its own CLI layer.

But the CLI must stay thin:

```text
Plotloom CLI = deterministic hands for short-drama production
Plotloom skills / agent = creative brain and director judgment
```

The CLI exists to make short-drama production reliable:

- find or initialize a series repo
- generate and archive image assets
- submit and poll video generation jobs
- copy accepted candidates to `selected.*`
- stitch selected clips into `final.mp4`
- validate media before delivery

It must not become:

- a workflow runtime
- a dashboard
- a task board
- a daemon / queue worker
- a hidden database
- a generic video creation platform

Plotloom may grow into a short-drama-native `videoclaw-v2`, but not a generic videoclaw clone.

## 2. Superpowers-style Mental Model

Plotloom is a skill graph, not a fixed pipeline.

Each capability should behave like a Superpowers skill:

```text
trigger condition
-> read existing context
-> create or update the minimum necessary artifact
-> verify output
-> hand off to the next likely capability
```

The CLI should support those skills with stable commands.

Example:

```text
plotloom-series-bible skill
  -> needs repo structure
  -> calls plotloom init / validate

plotloom-shot-prompts skill
  -> needs model-ready prompt string
  -> calls plotloom prompt extract/check

plotloom-video-adapter skill
  -> needs submit/poll/download
  -> calls plotloom video submit / poll

plotloom-stitch-deliver skill
  -> needs final.mp4
  -> calls plotloom stitch / media probe
```

CLI commands should be small, composable, and safe to call from different agents.

## 3. Core Principles

### 3.1 Image is sync-first

MVP image generation should be synchronous.

```text
plotloom image generate -> local image candidate path
```

Reason:

- image generation is usually much faster than video
- Codex imagegen2 helper is sync-like
- image reroll cost is low
- no need to introduce image task receipts in MVP

If future image providers become slow/async, `plotloom image submit/poll` can be added later.

### 3.2 Video is async-first

MVP video generation should be asynchronous.

```text
plotloom video submit -> task receipt or local candidate
plotloom video poll   -> status / download candidate
```

Reason:

- Dreamina / 即梦 queue can be long
- VolcEngine Seedance API is task-based
- HappyHorse / fal uses queue-style API for long-running video generation
- chat turns should not block on long video jobs
- videos are costlier, so one candidate at a time is safer

### 3.3 Repo-visible state only

Plotloom state lives in the series repo.

Allowed:

```text
episodes/ep001/videos/clip-01/task.volcengine.toml
episodes/ep001/videos/clip-01/candidates/v001.mp4
episodes/ep001/videos/clip-01/selected.mp4
```

Not allowed:

```text
hidden sqlite DB
background workflow state
central runtime queue
```

A task TOML is a visible receipt, not a workflow engine.

### 3.4 Python CLI

MVP CLI should use Python.

Reason:

- existing Plotloom deterministic scripts are Python
- ffmpeg / ffprobe wrapping is straightforward
- VolcEngine Ark SDK path is already Python
- local file and TOML handling are simple
- JS adds little for this local execution layer

JS remains useful for `npx skills` distribution and possible future web preview, not for MVP CLI runtime.

### 3.5 SD2.0 handles voice in MVP

No separate MVP voice/subtitle CLI is required.

For MVP, voice/audio is handled by the video adapter where supported:

```text
Seedance 2.0 / VolcEngine API -> generate_audio=true
Dreamina / Seedance family    -> adapter-specific audio option if available
```

So MVP does not include:

```bash
plotloom voice generate
plotloom subtitle generate
plotloom subtitle burn
```

Those can be future capabilities if Seedance audio is insufficient.

## 4. Product Flow Coverage

The CLI should cover the short-drama MVP flow end to end:

```text
new / existing short drama repo
  -> repo init / discovery / validation
  -> image assets: cast, scene, cover, reference still
  -> video prompt extraction
  -> video generation submit / poll / download
  -> candidate selection
  -> ffmpeg stitch
  -> ffprobe validation
  -> delivery by agent / Feishu adapter
```

CLI does not write `series.md`, `characters.md`, `episode-card.md`, or `video-prompts.md` creatively. Skills/agents write those files.

## 5. Series Repo Contract touched by CLI

```text
~/plotloom.toml

plotloom_repo/<slug>/
  series.md
  characters.md

  assets/
    cast/
      <character-slug>/
        character-grid.png
        notes.md
    scenes/
      <scene-slug>/
        candidates/
          v001.png
        selected.png
        notes.md

  episodes/
    ep001/
      episode-card.md
      video-prompts.md
      video-prompts-en.md

      images/
        covers/
          candidates/
            v001.png
          selected.png
        references/
          clip-01/
            candidates/
              v001.png
            selected.png

      videos/
        clip-01/
          task.volcengine.toml
          candidates/
            v001.mp4
          selected.mp4
        clip-02/
          candidates/
            v001.mp4
          selected.mp4
        final.mp4
```

Notes:

- `character-grid.png` is the current effective character reference; it is not a selected candidate grid.
- images can have 3 candidates by default; video should generate one candidate at a time.
- generated media may remain local and does not have to be committed to Git.

## 6. MVP Command Set

### 6.1 Repo commands

```bash
plotloom init <slug> --title "..." [--path PATH]
plotloom repos list
plotloom repos add <slug> --title "..." --path PATH --status active
plotloom repos set-status <slug> active|paused|archived
plotloom validate [--repo PATH]
plotloom doctor [--repo PATH]
```

MVP required:

```bash
plotloom init
plotloom repos list
plotloom validate
plotloom doctor
```

Repo discovery rule:

1. `--repo PATH` wins.
2. Else search current directory and parents for `series.md`.
3. Else read `~/plotloom.toml`.
4. If multiple active repos exist, list candidates and let agent/user choose.
5. If a registered path is missing, fail clearly; do not recreate silently.

### 6.2 Image commands

MVP image generation is synchronous.

```bash
plotloom image generate --kind cast --character <slug> --adapter codex-imagegen --prompt-file PATH
plotloom image generate --kind scene --scene <slug> --adapter codex-imagegen --prompt-file PATH
plotloom image generate --kind cover --episode ep001 --adapter codex-imagegen --prompt-file PATH
plotloom image generate --kind reference --episode ep001 --clip clip-01 --adapter codex-imagegen --prompt-file PATH

plotloom image list --kind cover --episode ep001
plotloom image info PATH
```

Kinds:

```text
cast       -> assets/cast/<character>/character-grid.png
scene      -> assets/scenes/<scene>/candidates/vNNN.png
cover      -> episodes/ep001/images/covers/candidates/vNNN.png
reference  -> episodes/ep001/images/references/clip-01/candidates/vNNN.png
```

Rules:

- `cast` generation writes or replaces `character-grid.png`, backing up the old grid when needed.
- `scene`, `cover`, and `reference` generation write numbered candidates.
- CLI does not decide which candidate is best.
- Candidate selection is explicit through `plotloom select`.

MVP should not include:

```bash
plotloom image submit
plotloom image poll
```

### 6.3 Asset / selection commands

```bash
plotloom asset import --kind cast --character <slug> --file /tmp/x.png --as character-grid
plotloom asset import --kind scene --scene <slug> --file /tmp/x.png --candidate
plotloom select PATH/TO/candidates/v001.png
plotloom select PATH/TO/candidates/v001.mp4
```

`plotloom select` behavior:

- copy candidate to sibling `selected.*`
- keep original candidate
- back up previous selected as `selected-prev-YYYYMMDD-HHMMSSffffff.*`
- never use symlink by default

### 6.4 Prompt commands

```bash
plotloom prompt check --episode ep001
plotloom prompt extract --episode ep001 --clip clip-01 --field prompt-string
```

Purpose:

- avoid passing Markdown artifact directly to model CLIs/APIs
- extract only the model-ready prompt string
- verify clip duration / ratio / reference hints when present

This exists because Dreamina CLI and VolcEngine API expect a plain prompt string, not the whole Plotloom prompt document.

### 6.5 Video commands

Video generation is async-first.

```bash
plotloom video submit --episode ep001 --clip clip-01 --adapter mock
plotloom video submit --episode ep001 --clip clip-01 --adapter volcengine-seedance
plotloom video submit --episode ep001 --clip clip-01 --adapter happyhorse-fal --mode reference-to-video
plotloom video submit --episode ep001 --clip clip-01 --adapter dreamina

plotloom video poll --episode ep001 --clip clip-01
plotloom video poll --task-id cgt-... --adapter volcengine-seedance --download-dir PATH
plotloom video poll --task-id req_... --adapter happyhorse-fal --download-dir PATH
plotloom video list --adapter volcengine-seedance --status queued
plotloom video cancel --task-id cgt-... --adapter volcengine-seedance
```

MVP required:

```bash
plotloom video submit --adapter mock
plotloom video submit --adapter dreamina-cli
plotloom video submit --adapter happyhorse-fal
plotloom video submit --adapter volcengine-seedance
plotloom video poll
```

This phase intentionally integrates three real backends in parallel so Plotloom can compare actual short-drama output instead of choosing a winner upfront. Detailed integration design: `docs/design/2026-04-30-video-adapter-three-provider-integration.md`.

Important boundary: the command surface is normalized, but provider parameters are not identical. `plotloom video submit` must compile a normalized `PlotloomVideoRequest` into each provider's native request through `adapter.capabilities()`, `adapter.validate_request()`, and `adapter.compile_native_request()`. Do not silently pass the same `duration/resolution/ratio/reference/audio` flags to all providers.

Examples:

- HappyHorse/fal supports 3s; Dreamina/VolcEngine Seedance 2.0 usually start at 4s.
- HappyHorse/fal supports 1080p; Dreamina Seedance 2.0 family is usually 720p; VolcEngine support depends on model/version.
- Dreamina `image2video` infers ratio from the input image; Plotloom must crop/validate the image rather than pretending `--ratio` applies.
- HappyHorse Ref2V is an endpoint; VolcEngine references are `content[]` roles; Dreamina needs a CLI-specific command mapping.

Adapter priority:

1. `mock`: local fake video for E2E and tests.
2. `dreamina-cli`: immediate baseline because local CLI/login path is already known; useful to start comparing output quickly.
3. `happyhorse-fal`: high-value audio-native API adapter; official fal API partner path, supports T2V/I2V/Ref2V/Edit with native synchronized audio.
4. `volcengine-seedance`: best API-shaped first-party async candidate; likely long-term native adapter if key/queue/quality validate.
5. `videoclaw`: optional legacy execution adapter later.

HappyHorse mode mapping:

```text
text-to-video      -> no image/reference asset; prompt-only clip
image-to-video     -> one selected image/reference still as first frame
reference-to-video -> 1-9 character/scene/style references; prompt uses character1..character9
video-edit         -> reroll/edit existing clip; optional 0-5 reference images; audio_setting=auto|origin
```

HappyHorse constraints to validate before submit:

- provider/auth: `FAL_KEY`; use `fal.ai`, not browser wrappers.
- endpoint family: `alibaba/happy-horse/{text-to-video|image-to-video|reference-to-video|video-edit}`.
- duration: 3-15 seconds.
- resolution: `720p` or `1080p`.
- aspect ratio: `16:9`, `9:16`, `1:1`, `4:3`, `3:4`.
- prompt: max 2500 chars; pass extracted prompt text, not full Markdown.
- local images/videos must be uploaded first because the API expects URLs.

Research note: `docs/research/2026-04-30-happyhorse-adapter-spike.md`.

Task receipt example:

```toml
adapter = "volcengine-seedance"
task_id = "cgt-..."
status = "queued"
submitted_at = "2026-04-30T12:00:00+08:00"
model = "doubao-seedance-2-0-260128"
ratio = "9:16"
resolution = "720p"
duration = 15
generate_audio = true
prompt_file = "episodes/ep001/video-prompts-en.md"
clip = "clip-01"
```

Poll behavior:

1. read task receipt or task id
2. query adapter status
3. update receipt
4. if succeeded, download `video_url` or copy returned file to `candidates/vNNN.mp4`
5. run `ffprobe`
6. store media facts in receipt or adjacent note

### 6.6 Stitch / media commands

```bash
plotloom media probe PATH
plotloom video check-clip episodes/ep001/videos/clip-01/selected.mp4
plotloom stitch --episode ep001
plotloom stitch --episode ep001 --normalize
```

`plotloom stitch` uses ffmpeg.

Before stitching, validate:

- all required `selected.mp4` clips exist
- aspect ratio is compatible
- resolution is compatible
- fps is compatible
- codec is compatible
- audio stream situation is known

MVP behavior:

- default strict mode: fail with clear reason if clips are incompatible
- optional `--normalize`: normalize resolution/fps/audio before stitching
- output: `episodes/ep001/videos/final.mp4`
- verify final with `ffprobe`

### 6.7 Package / delivery manifest

```bash
plotloom package --episode ep001
plotloom delivery manifest --episode ep001
```

MVP can generate a local manifest for agent delivery.

Feishu sending stays outside core CLI:

```text
Hermes / nova-lark reads final.mp4 -> sends MEDIA:/path/to/final.mp4
```

Feishu is a delivery adapter, not the state center.

## 7. Adapter Contracts

### 7.1 Image adapter

MVP image adapter is sync.

```python
class ImageAdapter:
    name: str

    def generate(self, request: ImageGenerateRequest) -> ImageGenerateResult:
        ...
```

Request fields:

```text
repo
kind
prompt_file / prompt
output_dir
filename_hint
reference_images
```

Result fields:

```text
path
adapter
metadata
```

Initial adapter:

```text
codex-imagegen
```

It wraps the existing Codex imagegen2 helper and always writes output into the series repo.

### 7.2 Video adapter

Video adapter is async-capable.

```python
class VideoAdapter:
    name: str

    def submit(self, request: VideoSubmitRequest) -> VideoSubmitResult:
        ...

    def poll(self, task_id: str) -> VideoTaskStatus:
        ...

    def cancel(self, task_id: str) -> None:
        ...
```

`mock` may return a local path immediately.

`volcengine-seedance` returns a task id and later a video URL.

`happyhorse-fal` uses fal queue-style APIs. It supports four modes: `text-to-video`, `image-to-video`, `reference-to-video`, and `video-edit`. It should return a fal request id at submit time, then download `result.video.url` into the clip candidate directory when polling completes. Local image/video inputs must be uploaded to fal first and passed as URLs.

`dreamina` returns a submit id and later downloads via CLI.

## 8. Implementation Shape

Recommended package structure:

```text
plotloom/
  __init__.py
  cli.py
  registry.py
  repo.py
  paths.py
  toml_io.py
  media.py
  prompts.py
  selection.py
  adapters/
    image_codex.py
    video_mock.py
    video_volcengine.py
    video_happyhorse_fal.py
    video_dreamina.py
  commands/
    init.py
    repos.py
    validate.py
    doctor.py
    image.py
    asset.py
    prompt.py
    video.py
    stitch.py
    media.py
    package.py
```

`pyproject.toml` entrypoint:

```toml
[project.scripts]
plotloom = "plotloom.cli:main"
```

Dependencies:

```toml
click>=8.1
requests>=2.31
tomli-w>=1.0
volcengine-python-sdk[ark]>=5.0.0  # optional extra
fal-client>=0.7.0                 # optional extra for happyhorse-fal
```

Keep existing deterministic scripts until CLI wrappers are stable; migrate later if useful.

## 9. MVP Implementation Order

### Phase 1: fake E2E foundation

```text
init
repos list
validate
doctor
video submit --adapter mock
select
stitch
media probe
```

Acceptance:

```bash
plotloom init fake-heiress --title "Fake Heiress"
plotloom validate --repo ~/plotloom_repo/fake-heiress
plotloom video submit --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01 --adapter mock
plotloom select ~/plotloom_repo/fake-heiress/episodes/ep001/videos/clip-01/candidates/v001.mp4
plotloom stitch --repo ~/plotloom_repo/fake-heiress --episode ep001
plotloom media probe ~/plotloom_repo/fake-heiress/episodes/ep001/videos/final.mp4
```

### Phase 2: sync image generation

```text
image generate --kind cast
image generate --kind scene
image generate --kind cover
image generate --kind reference
asset import
select image candidates
```

Acceptance:

- `character-grid.png` generated in cast directory
- cover candidates numbered correctly
- selected copy and backup work

### Phase 3: three real video adapters comparison

This phase integrates all three real backends behind the same submit/poll/receipt contract. Do not choose a single default before the comparison run.

#### Phase 3A: Dreamina CLI baseline

Prerequisite: host is already authenticated and `dreamina user_credit` passes with `vip_level: maestro`.

```text
video submit --adapter dreamina-cli --mode text-to-video
video submit --adapter dreamina-cli --mode image-to-video
video poll --adapter dreamina-cli
```

Acceptance:

- records `submit_id`
- external query loop works through `query_result`
- downloads candidate to `candidates/vNNN.dreamina-cli.mp4`
- ffprobe passes

#### Phase 3B: HappyHorse / fal adapter

Prerequisite: `FAL_KEY`, funded fal account, and `fal-client` available.

```text
video submit --adapter happyhorse-fal --mode text-to-video
video submit --adapter happyhorse-fal --mode image-to-video
video submit --adapter happyhorse-fal --mode reference-to-video
video poll --adapter happyhorse-fal
```

Acceptance:

- returns fal request id
- writes receipt
- uploads local reference assets when needed
- downloads `result.video.url` into `candidates/vNNN.happyhorse-fal.mp4`
- ffprobe confirms duration/resolution/audio facts

#### Phase 3C: VolcEngine Seedance adapter

Prerequisite: `ARK_API_KEY` and model access validated.

```text
video submit --adapter volcengine-seedance
video poll --adapter volcengine-seedance
video cancel --adapter volcengine-seedance
```

Acceptance:

- returns task id
- writes receipt
- observes queued/running/succeeded or clear failure
- downloads candidate video to `candidates/vNNN.volcengine-seedance.mp4`
- ffprobe passes

#### Phase 3D: Same-prompt comparison report

Run the same 720p vertical clip prompt through all three adapters and record:

```text
submit time / queued time / running time / total time / cost / has_audio / visual quality / character consistency / failure mode
```

### Phase 4: prompt check/extract

```text
prompt check
prompt extract
```

Acceptance:

- model adapter receives plain prompt string, not Markdown artifact

## 10. Non-goals for MVP

Do not implement in MVP:

```bash
plotloom run
plotloom daemon
plotloom dashboard
plotloom workflow
plotloom publish
plotloom image poll
plotloom voice generate
plotloom subtitle burn
```

Voice is covered by Seedance 2.0 `generate_audio` for MVP.

Subtitles/publishing can be future modules after first-episode production works.

## 11. Open Questions

1. Should task receipts be single-file `task.<adapter>.toml` or nested `tasks/<task_id>.toml`? MVP can use single-file per clip.
2. Should cover prompt be persisted as a file? Current lean-artifact rule says no; use temporary `--prompt-file` unless needed.
3. Should `plotloom image generate --kind cast` generate 1 grid or 3 grids? Current default: one effective `character-grid.png`; reroll backs up old grid.
4. Should VolcEngine become default video adapter if queue is good? Decide after key-based timing test.
5. Should HappyHorse/fal become the preferred audio-native adapter for clips that need synchronized speech/sound? Decide after `FAL_KEY` probe and cost/timing comparison.

## 12. Final MVP Coverage Check

| Need | Covered by CLI? | Command |
|---|---:|---|
| Discover / create short-drama repo | yes | `init`, `repos list`, `validate` |
| Character image generation | yes | `image generate --kind cast` |
| Scene image generation | yes | `image generate --kind scene` |
| Cover image generation | yes | `image generate --kind cover` |
| Reference still generation | yes | `image generate --kind reference` |
| Prompt safety / extraction | yes | `prompt check/extract` |
| Video generation | yes | `video submit/poll` |
| SD2.0 voice/audio | yes, via adapter | `generate_audio=true` in video adapter |
| Candidate selection | yes | `select` |
| ffmpeg stitching | yes | `stitch` |
| ffprobe validation | yes | `media probe`, stitch post-check |
| Feishu delivery | outside core CLI | Hermes / nova-lark |

Conclusion:

```text
The MVP CLI covers the main short-drama production loop:
repo -> images -> video -> select -> stitch -> validate -> deliver.
```
