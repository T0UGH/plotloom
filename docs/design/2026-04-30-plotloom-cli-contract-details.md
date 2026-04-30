# Plotloom CLI Contract Details

> 日期：2026-04-30  
> 状态：Draft v0.1  
> 目的：补充 CLI command surface 落地前必须稳定的细节：真实 provider 手动 E2E、命令输入输出契约、config/secret 规则、receipt/filesystem contract。  
> Source of truth:
> - `docs/design/2026-04-30-plotloom-cli-technical-design.md`
> - `docs/design/2026-04-30-plotloom-cli-command-surface.md`

## 1. Provider Manual E2E

真实 provider 调用不进入默认自动化测试。第一版只提供 `doctor` + 手动 smoke 命令，避免自动测试误烧钱、误卡队列、误依赖登录态。

手动 E2E 共用原则：

- 先跑 `plotloom config doctor --adapter <adapter>`。
- 只用 720p、短时长、单 clip smoke。
- submit 后立即检查 receipt 是否写入。
- poll 是 one-shot；`--watch` 必须显式且有 `--max-wait`。
- 成功后必须下载到本地 candidate，并跑 `ffprobe`。
- 不把 provider 临时 URL 当长期产物。
- 不在 stdout、receipt、日志里打印 API key、OAuth code、QR 内容或 credential 文件路径。

### 1.1 Dreamina CLI

Prerequisites:

```text
dreamina binary exists
Dreamina account is logged in
user_credit passes
vip_level is sufficient
ffmpeg/ffprobe available for downstream media validation
```

Doctor:

```bash
plotloom config doctor --adapter dreamina-cli
plotloom doctor --adapter dreamina-cli --deep
```

Text-to-video smoke:

```bash
plotloom video submit \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter dreamina-cli \
  --mode text-to-video \
  --duration 15 \
  --ratio 9:16 \
  --resolution 720p

plotloom video poll \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter dreamina-cli \
  --latest
```

Expected artifacts:

```text
episodes/ep001/videos/clip-01/tasks/dreamina-cli-<submit-id>.toml
episodes/ep001/videos/clip-01/latest-task.toml
episodes/ep001/videos/clip-01/candidates/vNNN.dreamina-cli.mp4
```

Success criteria:

- receipt contains `adapter = "dreamina-cli"` and `provider_task_id`.
- poll records terminal status or clear queue/running status.
- succeeded poll downloads a playable candidate.
- `plotloom media probe <candidate>` succeeds.

Stop conditions:

- login or membership invalid.
- Dreamina queue is too long for the current manual check.
- prompt compile produces an empty or full-Markdown prompt.

### 1.2 HappyHorse / fal

Prerequisites:

```text
FAL_KEY present through env or ~/.plotloom/.env.toml
fal-client import succeeds
fal account has funds
local reference assets are uploadable when using image/reference/video modes
```

Doctor:

```bash
plotloom config doctor --adapter happyhorse-fal
plotloom doctor --adapter happyhorse-fal --deep
```

Text-to-video smoke:

```bash
plotloom video submit \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter happyhorse-fal \
  --mode text-to-video \
  --duration 5 \
  --ratio 9:16 \
  --resolution 720p

plotloom video poll \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter happyhorse-fal \
  --latest
```

Reference-to-video smoke:

```bash
plotloom video submit \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter happyhorse-fal \
  --mode reference-to-video \
  --reference-image assets/cast/lin-qiao/character-grid.png \
  --duration 5 \
  --ratio 9:16 \
  --resolution 720p
```

Expected artifacts:

```text
episodes/ep001/videos/clip-01/tasks/happyhorse-fal-<request-id>.toml
episodes/ep001/videos/clip-01/latest-task.toml
episodes/ep001/videos/clip-01/candidates/vNNN.happyhorse-fal.mp4
```

Success criteria:

- receipt records endpoint, mode, request id, duration, ratio, resolution, prompt hash.
- local media inputs are uploaded before submit; receipt may record uploaded URL host/type but not credential values.
- poll downloads `result.video.url` immediately.
- media probe records duration, resolution, fps, audio presence.

Cost controls:

- default smoke duration should be 5s for HappyHorse unless user explicitly requests longer.
- default smoke resolution is 720p.
- no automatic multi-candidate batch generation.

### 1.3 VolcEngine Seedance

Prerequisites:

```text
ARK_API_KEY present through env or ~/.plotloom/.env.toml
volcengine-python-sdk[ark] import succeeds
model access enabled
account balance/resource package sufficient
```

Doctor:

```bash
plotloom config doctor --adapter volcengine-seedance
plotloom doctor --adapter volcengine-seedance --deep
```

Text-to-video smoke:

```bash
plotloom video submit \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter volcengine-seedance \
  --mode text-to-video \
  --duration 5 \
  --ratio 9:16 \
  --resolution 720p \
  --audio native-if-supported

plotloom video poll \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter volcengine-seedance \
  --latest
```

Image-to-video smoke:

```bash
plotloom video submit \
  --repo ~/plotloom_repo/fake-heiress \
  --episode ep001 \
  --clip clip-01 \
  --adapter volcengine-seedance \
  --mode image-to-video \
  --first-frame episodes/ep001/images/references/clip-01/selected.png \
  --duration 5 \
  --ratio 9:16 \
  --resolution 720p
```

Expected artifacts:

```text
episodes/ep001/videos/clip-01/tasks/volcengine-seedance-<task-id>.toml
episodes/ep001/videos/clip-01/latest-task.toml
episodes/ep001/videos/clip-01/candidates/vNNN.volcengine-seedance.mp4
```

Success criteria:

- receipt records Ark task id and model.
- poll records queued/running/succeeded/failed/expired/cancelled.
- succeeded poll downloads temporary video URL immediately.
- media probe succeeds.

Stop conditions:

- model access unavailable.
- provider rejects references due to face/reference policy.
- provider returns resolution/duration incompatibility and user did not pass explicit downgrade/normalize flags.

## 2. Command I/O Contract

All commands follow the same output shape:

```text
human stdout by default
JSON stdout only with --json
diagnostics/errors to stderr
no first-party persistent JSON/YAML artifacts
```

### 2.1 Global Output Fields

When `--json` is set, successful commands should include:

```json
{
  "ok": true,
  "command": "video.submit",
  "repo": "/abs/path/to/series",
  "outputs": {},
  "warnings": []
}
```

Failure JSON:

```json
{
  "ok": false,
  "command": "video.submit",
  "error": {
    "code": "MISSING_CONFIG",
    "message": "FAL_KEY is not configured",
    "next_step": "Run plotloom config doctor --adapter happyhorse-fal"
  }
}
```

Secrets must be redacted before formatting either human or JSON output.

### 2.2 Config Commands

`plotloom config path`

Outputs:

```text
/Users/<user>/.plotloom/.env.toml
```

JSON output:

```json
{
  "ok": true,
  "command": "config.path",
  "config_path": "/Users/<user>/.plotloom/.env.toml"
}
```

`plotloom config init`

Writes:

```text
~/.plotloom/.env.toml
```

Rules:

- create parent dir if missing.
- chmod file to `0600`.
- do not overwrite existing file unless `--force`.

`plotloom config doctor`

Checks:

- TOML parse.
- file permission.
- env/config presence.
- adapter dependency import/binary availability.

Does not call paid provider submit APIs.

### 2.3 Repo Commands

`plotloom init <slug> --title TEXT`

Writes:

```text
<repos_root>/<slug>/
~/plotloom.toml
```

Outputs:

```json
{
  "ok": true,
  "command": "repo.init",
  "repo": "/abs/path/to/repo",
  "registry_path": "/Users/<user>/plotloom.toml"
}
```

`plotloom validate`

Reads:

```text
series.md
characters.md
episodes/
optional episode prompt/media files
```

Does not write files.

### 2.4 Prompt Commands

`plotloom prompt compile`

Reads:

```text
episodes/<ep>/video-prompts-en.md
referenced image/video assets if mode requires them
```

Outputs stdout unless `--output` is set. If `--output` is set, use a user-specified temp path rather than defaulting into the series repo.

JSON output should include:

```json
{
  "ok": true,
  "command": "prompt.compile",
  "episode": "ep001",
  "clip": "clip-01",
  "adapter": "happyhorse-fal",
  "mode": "reference-to-video",
  "prompt_sha256": "...",
  "prompt_chars": 1200,
  "warnings": []
}
```

### 2.5 Image Commands

`plotloom image generate`

Reads:

```text
prompt file
optional input images
series repo context
```

Writes:

```text
assets/cast/<character>/character-grid.png
assets/cast/<character>/character-grid-prev-YYYYMMDD-HHMMSSffffff.png
assets/scenes/<scene>/candidates/vNNN.png
episodes/<ep>/images/covers/candidates/vNNN.png
episodes/<ep>/images/references/<clip>/candidates/vNNN.png
```

JSON output:

```json
{
  "ok": true,
  "command": "image.generate",
  "adapter": "codex-app-server",
  "image_path": "/abs/path/to/image.png",
  "source_image_path": "/abs/path/to/.codex/generated_images/...",
  "image_url": "file:///abs/path/to/image.png"
}
```

### 2.6 Video Commands

`plotloom video submit`

Reads:

```text
episodes/<ep>/video-prompts-en.md
first frame / reference image / source video if mode needs them
~/.plotloom/.env.toml or environment variables
```

Writes:

```text
episodes/<ep>/videos/<clip>/tasks/<adapter>-<provider-id-or-timestamp>.toml
episodes/<ep>/videos/<clip>/latest-task.toml
```

Does not write candidate unless adapter is `mock` or provider returns a local file synchronously.

JSON output:

```json
{
  "ok": true,
  "command": "video.submit",
  "adapter": "volcengine-seedance",
  "episode": "ep001",
  "clip": "clip-01",
  "receipt_path": "/abs/path/to/tasks/volcengine-seedance-cgt-xxx.toml",
  "task_id": "cgt-xxx",
  "status": "queued"
}
```

`plotloom video poll`

Reads:

```text
task receipt
provider API/CLI
```

Writes:

```text
updated receipt
latest-task.toml
candidates/vNNN.<adapter>.mp4 on success
```

JSON output includes `candidate_path` only after a local candidate exists.

### 2.7 Select / Stitch / Delivery Commands

`plotloom select PATH`

Writes:

```text
sibling selected.<ext>
sibling selected-prev-YYYYMMDD-HHMMSSffffff.<ext> when replacing
```

`plotloom stitch`

Reads selected clips, writes:

```text
episodes/<ep>/videos/final.mp4
```

`plotloom delivery summary`

Default writes nothing; stdout only. With explicit `--output`, write to the user-given path.

## 3. Config And Secret Contract

Config file:

```text
~/.plotloom/.env.toml
```

This file is intentionally outside the series repo. It is local machine configuration, not production state.

### 3.1 Precedence

Read values in this order:

```text
explicit CLI flag
environment variable
~/.plotloom/.env.toml
built-in default
```

Examples:

- `--config PATH` overrides `PLOTLOOM_CONFIG`.
- `FAL_KEY` env overrides `[adapters.happyhorse-fal].fal_key`.
- `ARK_API_KEY` env overrides `[adapters.volcengine-seedance].ark_api_key`.

### 3.2 Environment Mapping

```text
PLOTLOOM_CONFIG              -> config file path
PLOTLOOM_REPOS_ROOT          -> [plotloom].repos_root
PLOTLOOM_REGISTRY_PATH       -> [plotloom].registry_path
CODEX_BINARY                 -> [adapters.codex-app-server].codex_binary
CODEX_APP_SERVER_URL         -> [adapters.codex-app-server].app_server_url
DREAMINA_BINARY              -> [adapters.dreamina-cli].binary
DREAMINA_HOME                -> [adapters.dreamina-cli].home
FAL_KEY                      -> [adapters.happyhorse-fal].fal_key
ARK_API_KEY                  -> [adapters.volcengine-seedance].ark_api_key
PLOTLOOM_VOLCENGINE_BASE_URL -> [adapters.volcengine-seedance].base_url
PLOTLOOM_VOLCENGINE_MODEL    -> [adapters.volcengine-seedance].model
```

### 3.3 Secret Safety

Never print:

```text
FAL_KEY
ARK_API_KEY
OAuth code
QR content
credential file contents
temporary signed URLs if they contain sensitive tokens
```

Allowed diagnostic:

```text
FAL_KEY: present via env
ARK_API_KEY: absent
Dreamina login: present
Codex binary: /opt/homebrew/bin/codex
```

Receipt may record:

```toml
credential_source = "env"
```

Receipt must not record:

```toml
fal_key = "..."
ark_api_key = "..."
```

### 3.4 Permission Rules

`plotloom config init`:

- creates `~/.plotloom` if missing.
- writes `.env.toml` with `0600`.
- refuses to overwrite by default.

`plotloom config doctor`:

- warns if file is group/world readable.
- warns if config has unknown adapter sections.
- fails if TOML cannot parse.
- does not mutate file permissions unless a future explicit `--fix-permissions` flag is added.

## 4. Receipt And Filesystem Contract

Receipts are visible TOML records of provider actions. They are not workflow state, not a queue, and not a project-management system.

### 4.1 Paths

```text
episodes/<ep>/videos/<clip>/tasks/<adapter>-<provider-id-or-timestamp>.toml
episodes/<ep>/videos/<clip>/latest-task.toml
episodes/<ep>/videos/<clip>/candidates/vNNN.<adapter>.mp4
episodes/<ep>/videos/<clip>/selected.mp4
episodes/<ep>/videos/final.mp4
```

Use provider id when available. Use timestamp only for adapters that produce no id before local output exists.

### 4.2 Status Values

Normalized statuses:

```text
submitted
queued
running
succeeded
failed
expired
cancelled
local
```

Provider-specific statuses should be preserved under `[provider.raw]` or equivalent raw metadata, but command logic should use normalized statuses.

### 4.3 Receipt Schema

Minimal receipt:

```toml
receipt_version = 1
adapter = "volcengine-seedance"
provider = "volcengine"
provider_task_id = "cgt-xxx"
status = "queued"
submitted_at = "2026-04-30T12:00:00+08:00"
updated_at = "2026-04-30T12:00:00+08:00"

repo = "/abs/path/to/series"
episode = "ep001"
clip = "clip-01"

mode = "text-to-video"
prompt_file = "episodes/ep001/video-prompts-en.md"
compiled_prompt_sha256 = "..."
prompt_chars = 1180

duration = 5
ratio = "9:16"
resolution = "720p"
audio_intent = "native_if_supported"
credential_source = "config"
```

On success:

```toml
status = "succeeded"
candidate_path = "episodes/ep001/videos/clip-01/candidates/v001.volcengine-seedance.mp4"
downloaded_at = "2026-04-30T12:08:00+08:00"

[media]
duration = 5.0
width = 720
height = 1280
fps = 24.0
has_audio = true
video_codec = "h264"
audio_codec = "aac"
```

On failure:

```toml
status = "failed"
error_code = "PROVIDER_REJECTED_REFERENCE"
error_message = "Provider rejected the first-frame image."
next_step = "Use an AI-generated character reference or switch to text-to-video."
```

### 4.4 Provider-Specific Fields

Dreamina:

```toml
[provider]
binary = "dreamina"
submit_id = "..."
model_version = "seedance2.0fast"
download_dir = "episodes/ep001/videos/clip-01/candidates"
```

HappyHorse / fal:

```toml
[provider]
endpoint = "alibaba/happy-horse/text-to-video"
request_id = "req_..."
queue_status = "IN_QUEUE"
```

VolcEngine:

```toml
[provider]
base_url = "https://ark.cn-beijing.volces.com/api/v3"
model = "doubao-seedance-2-0-260128"
task_id = "cgt-..."
generate_audio = true
watermark = false
```

Do not put raw provider response into receipt if it contains signed URLs, credentials, or large payloads. Store only safe fields needed for repeatable poll/download/debug.

### 4.5 latest-task.toml

`latest-task.toml` is a pointer, not history:

```toml
receipt = "tasks/volcengine-seedance-cgt-xxx.toml"
adapter = "volcengine-seedance"
provider_task_id = "cgt-xxx"
status = "running"
updated_at = "2026-04-30T12:03:00+08:00"
```

It may be overwritten on new submit/poll. Historical task receipts must not be overwritten.

### 4.6 Candidate Numbering

Candidate numbering scans all existing `vNNN.*` in the clip candidate directory, regardless of adapter suffix:

```text
v001.dreamina-cli.mp4
v002.happyhorse-fal.mp4
v003.volcengine-seedance.mp4
```

Next candidate is max `NNN + 1`.

### 4.7 Compare Output

`plotloom video compare` reads receipts and media probes. Default output is stdout.

Fields:

```text
adapter
mode
status
candidate_path
submit_time
downloaded_at
total_elapsed
duration
resolution
fps
has_audio
estimated_cost
failure_mode
human_notes
```

`human_notes` is optional and should be user/agent-authored, not generated as an automatic quality score in MVP.

## 5. Plan Readiness Checklist

Before using `writing-plans`, these design decisions are now stable:

- First implementation plan targets CLI skeleton plus all three real adapters.
- Default automated tests do not call real providers.
- Manual E2E smoke is documented for Dreamina, HappyHorse, and VolcEngine.
- Config/secrets live in `~/.plotloom/.env.toml`.
- `codex-app-server` image adapter should follow the `codex-imagegen2-api` local JSON API pattern.
- Prompt compile/check is mandatory inside `video submit`.
- Receipt history uses `tasks/*.toml`; `latest-task.toml` is only a pointer.
- Delivery summary is stdout by default; no persistent first-party manifest in MVP.
