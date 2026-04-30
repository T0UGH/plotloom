# Plotloom CLI Technical Design

> 日期：2026-04-30  
> 状态：Draft v0.2
> 目标：定义 Plotloom 自有薄 CLI 层，用于覆盖短剧生产中的确定性执行、素材归档、异步视频任务和成片验收。  
> 相关文档：
> - `docs/design/2026-04-30-plotloom-cli-brainstorm.md`
> - `docs/design/2026-04-30-plotloom-cli-command-surface.md`
> - `docs/design/2026-04-30-plotloom-cli-contract-details.md`
> - `docs/design/cli-design.md`（历史草案，已由本文档取代）
> - `docs/research/2026-04-30-volcengine-seedance-api-spike.md`
> - `docs/prd/plotloom-mvp-prd.zh.md`

## 1. 设计结论

Plotloom CLI 第一版采用 **Python** 实现。

一句话：

```text
Plotloom CLI = 短剧 series repo 的确定性执行层；Python CLI + thin adapters + repo-visible receipts。
```

CLI 不做创作判断，不做 runtime，不做 dashboard，不做隐藏状态机。

核心边界：

```text
image = sync-first
video = async-first
state = visible files in series repo
intelligence = Plotloom skills / agent
```

当前已收敛的产品决策：

- MVP 视频层要把 `dreamina-cli`、`happyhorse-fal`、`volcengine-seedance` 三家都接通，用同一套 submit/poll/receipt 契约做真实对比。
- 先设计稳定命令面，再写实现；执行计划应以本文档的命令和文件契约为准。
- `prompt extract/check` 不是后置增强；只要真实视频 adapter 进入 MVP，`video submit` 就必须先把 `video-prompts-en.md` 编译成 provider-ready prompt。
- image adapter 依赖本机 Codex 安装和内置 `image_generation` 能力；实现可吸收 `codex-imagegen2-api` 的本地 JSON API 模式，但不依赖某个私有 helper 安装路径。
- 本地密钥和 provider 配置集中放在 `~/.plotloom/.env.toml`，不得写入 series repo、receipt、日志或聊天输出。

## 2. 为什么选 Python，不选 JS

### 2.1 Python 更适合当前 MVP

Plotloom MVP 的 CLI 任务主要是本地生产工具链：

- 文件系统操作：初始化 repo、复制候选、备份 selected。
- TOML/Markdown 读写。
- 调 ffmpeg / ffprobe。
- 下载视频 URL。
- 调火山方舟 Python SDK。
- 复用现有 Python 脚本：`init_series.py`、`validate_repo.py`、`select_candidate.py`、`stitch_ffmpeg.py`。
- 与 Codex image generation / Dreamina CLI / fal HappyHorse / VolcEngine Seedance API 做 thin adapter。

这些都更贴近 Python。

### 2.2 JS 的价值暂时不在 runtime

JS/Node 在 Plotloom 里主要价值是：

- `npx skills add ...` 安装 skill pack。
- 未来如果做 Web preview / lightweight UI，可以考虑 JS。
- 如果发布 npm 包给 agent hosts，可另起 packaging layer。

但第一版 CLI 不需要 Web runtime，也不需要 Node 生态能力。

### 2.3 选型风险

Python 风险：

- 分发不如 `npx` 顺手。
- 用户环境 Python 版本/依赖可能不一致。

缓解：

- MVP 先本仓库本地开发安装：`pip install -e .` 或 `uvx --from . plotloom`。
- 后续再考虑 PyPI / `uv tool install`。
- skill 安装仍走 `npx skills`，CLI 安装单独说明。

JS 风险：

- 会重写已有 Python 脚本。
- ffmpeg/media/SDK glue 也仍要调用外部命令或另找包。
- 火山方舟当前验证路径是 Python SDK，JS 先做会增加未知数。

结论：**MVP 用 Python；JS 暂不进入 CLI runtime。**

## 3. CLI 设计原则

### 3.1 Thin CLI, not runtime

CLI 是 agent 的手，不是脑。

CLI 做：

- repo discovery / init / validate
- image generate/import/select
- video submit/poll/download
- media probe / stitch
- delivery summary / handoff text

CLI 不做：

- 剧情生成
- 爽点判断
- 创作性 prompt 改写；provider-aware extract/compile 属于 adapter glue
- 用户交互确认
- 多 agent 编排
- daemon / queue / dashboard
- hidden DB
- persistent package/workflow manifest

### 3.2 Repo-visible state

所有生产状态都应该落在 series repo 的可见文件里。

允许：

```text
episodes/ep001/videos/clip-01/tasks/volcengine-seedance-cgt-20260430120000.toml
episodes/ep001/videos/clip-01/latest-task.toml
episodes/ep001/videos/clip-01/candidates/v001.volcengine-seedance.mp4
episodes/ep001/videos/clip-01/selected.mp4
```

不允许：

```text
~/.plotloom/tasks.db
.plotloom/state.sqlite
hidden queue worker state
```

`tasks/*.toml` 是任务收据，不是 workflow runtime。它只描述一次 provider submit/poll 的可见证据，不能变成隐藏调度状态。

### 3.3 Sync image, async video

图片生成：同步。

```text
plotloom image generate -> returns local file/candidate path
```

视频生成：异步优先。

```text
plotloom video submit -> task receipt
plotloom video poll -> status / download candidate
```

原因：图片通常较快，失败重试成本低；视频排队和生成慢，必须与 chat turn 解耦。

### 3.4 Adapter-thin

Adapter 只处理工具差异，不承载 Plotloom 产品逻辑。

例如：

- `codex-app-server`：通过本机 Codex `image_generation` 能力生成图片，复制输出图。
- `dreamina-cli`：调用 Dreamina CLI，记录 submit_id，query/download。
- `happyhorse-fal`：调用 fal queue API，记录 request_id，poll/download。
- `volcengine-seedance`：调用火山方舟 API，记录 task_id，poll/download。
- `mock`：生成本地假视频，保障 E2E。

## 4. 推荐目录结构

在 Plotloom repo 中新增 Python package：

```text
plotloom/
  __init__.py
  cli.py
  config.py
  registry.py
  repo.py
  paths.py
  toml_io.py
  media.py
  prompts.py
  assets.py
  images.py
  videos.py
  adapters/
    __init__.py
    image_codex_app_server.py
    video_mock.py
    video_dreamina_cli.py
    video_happyhorse_fal.py
    video_volcengine_seedance.py
  commands/
    __init__.py
    config.py
    repos.py
    init.py
    validate.py
    doctor.py
    image.py
    asset.py
    prompt.py
    video.py
    select.py
    stitch.py
    media.py
    delivery.py
scripts/
  ... existing deterministic helpers, gradually migrated or wrapped ...
```

不强制一次性迁移现有 `scripts/`。第一阶段可以让 CLI 调用现有脚本，稳定后再内聚到 package。

## 5. Python package / entrypoint

建议使用 `pyproject.toml`：

```toml
[project]
name = "plotloom"
version = "0.1.0"
description = "Short-drama-native production CLI for Plotloom series repos"
requires-python = ">=3.11"
dependencies = [
  "click>=8.1",
  "tomli-w>=1.0",
  "requests>=2.31",
]

[project.optional-dependencies]
happyhorse = ["fal-client>=0.7.0"]
volcengine = ["volcengine-python-sdk[ark]>=5.0.0"]
dev = ["pytest>=8", "ruff>=0.5"]

[project.scripts]
plotloom = "plotloom.cli:main"
```

说明：

- Python 3.11+：标准库有 `tomllib` 读 TOML；写 TOML 用 `tomli-w` 或自写小函数。
- `click`：简单稳定，videoclaw 也用 click；不用 Typer 避免额外复杂度。
- `requests`：下载视频 URL。
- `fal-client` 作为 optional dependency，只有 `happyhorse-fal` adapter 需要。
- `volcengine-python-sdk[ark]` 作为 optional dependency，避免没有 key 时污染基础安装。

### 5.1 Local config / secret config

Plotloom 增加一个 user-level config 文件：

```text
~/.plotloom/.env.toml
```

用途：

- 存放 provider API key、本机 binary 路径、默认模型和默认参数。
- 只服务 CLI adapter preflight/submit/poll，不承载 series repo 生产状态。
- 不写入 Git，不复制进 series repo，不出现在 receipt、日志或聊天输出中。

文件权限：

- `plotloom config init` 创建 `~/.plotloom/` 和 `.env.toml` 时应设置为 `0600`。
- `plotloom config doctor` 如果发现权限过宽，应返回清晰告警。

读取优先级：

```text
explicit CLI flag
  -> environment variable
  -> ~/.plotloom/.env.toml
  -> built-in default
```

环境变量保留为 CI/临时覆盖入口；`.env.toml` 是本机长期配置入口。

建议结构：

```toml
[plotloom]
repos_root = "~/plotloom_repo"
registry_path = "~/plotloom.toml"
default_image_adapter = "codex-app-server"
default_video_adapters = ["dreamina-cli", "happyhorse-fal", "volcengine-seedance"]

[adapters.codex-app-server]
enabled = true
codex_binary = "codex"
# Optional. Direct app-server endpoint can be used if available; MVP may use codex exec.
app_server_url = ""

[adapters.dreamina-cli]
enabled = true
binary = "dreamina"
home = "~"

[adapters.happyhorse-fal]
enabled = true
fal_key = ""
default_resolution = "720p"

[adapters.volcengine-seedance]
enabled = true
ark_api_key = ""
base_url = "https://ark.cn-beijing.volces.com/api/v3"
model = "doubao-seedance-2-0-260128"
default_resolution = "720p"
```

等价环境变量：

```text
PLOTLOOM_CONFIG
PLOTLOOM_REPOS_ROOT
PLOTLOOM_REGISTRY_PATH
FAL_KEY
ARK_API_KEY
DREAMINA_BINARY
DREAMINA_HOME
CODEX_BINARY
CODEX_APP_SERVER_URL
```

安全规则：

- CLI 可以显示 key 是否存在，但只能显示 `present/absent`，不能显示明文或前后缀。
- receipt 中只能记录 `credential_source = "env"` 或 `credential_source = "config"` 这类来源，不记录值。
- `config set` 如果未来实现，避免把 secret 放进 shell history；MVP 可以只提供 `config init/path/doctor`，让用户手动编辑 TOML。

## 6. 命令设计

命令面先按 v0.2 固定，后续执行计划不要再重新发明语法。

通用参数：

```bash
plotloom --config ~/.plotloom/.env.toml <command>
plotloom <command> --repo PATH
```

Repo 解析顺序：

1. 显式 `--repo PATH`。
2. 从当前目录向上找 `series.md`。
3. 读取 `registry_path`，默认 `~/plotloom.toml`。
4. 多个 active repo 或无法唯一匹配时，列出候选并返回非零，让 agent/用户选择。
5. registry 中路径失效时，不自动重建目录。

### 6.0 Config commands

```bash
plotloom config path
plotloom config init
plotloom config doctor
```

MVP 只需要这三个命令：

- `config path`：打印当前会读取的 config 路径。
- `config init`：创建 `~/.plotloom/.env.toml` 模板，文件权限 `0600`，已存在则不覆盖。
- `config doctor`：检查 TOML 可解析、权限合理、关键 adapter 配置是否 present，不打印 secret。

### 6.1 Repo commands

```bash
plotloom init <slug> --title "Fake Heiress Reboot" [--path ~/plotloom_repo/<slug>]
plotloom repos list
plotloom repos add <slug> --title "..." --path PATH --status active
plotloom repos set-status <slug> active|paused|archived
plotloom repos resolve <slug>
plotloom validate [--repo PATH]
plotloom doctor [--repo PATH]
```

MVP 必须：

```bash
plotloom init <slug> --title "..."
plotloom repos list
plotloom validate
plotloom doctor
```

`init` 不做交互式题材生成；slug/title 是命令输入。`--path` 省略时使用 `repos_root/<slug>`，默认 `~/plotloom_repo/<slug>`。

### 6.2 Image commands

MVP 图片同步。

```bash
plotloom image generate --kind cast --character lin-qiao --adapter codex-app-server --prompt-file PATH
plotloom image generate --kind scene --scene boardroom --adapter codex-app-server --prompt-file PATH
plotloom image generate --kind cover --episode ep001 --adapter codex-app-server --prompt-file PATH
plotloom image generate --kind reference --episode ep001 --clip clip-01 --adapter codex-app-server --prompt-file PATH
plotloom image list --kind cover --episode ep001
plotloom image info PATH
```

输出位置：

```text
assets/cast/<character>/character-grid.png
assets/scenes/<scene>/candidates/vNNN.png
episodes/ep001/images/covers/candidates/vNNN.png
episodes/ep001/images/references/clip-01/candidates/vNNN.png
```

角色图规则：

- `character-grid.png` 是当前有效角色设定图。
- 不做 `selected.png`。
- 重画时可备份为 `character-grid-prev-YYYYMMDD-HHMMSS.png` 或生成 `character-grid-vN.png`，但当前有效文件仍是 `character-grid.png`。

MVP 不做：

```bash
plotloom image submit
plotloom image poll
```

未来如果图片 provider 异步，再加。

### 6.3 Asset commands

```bash
plotloom asset import --kind cast --character lin-qiao --file /tmp/x.png --as character-grid
plotloom asset import --kind scene --scene boardroom --file /tmp/x.png --candidate
plotloom asset select PATH/TO/candidates/v001.png
plotloom asset info PATH
```

`asset select` 行为：

- candidate copy 到 `selected.*`
- 旧 selected 备份为 `selected-prev-YYYYMMDD-HHMMSS.*`
- 不用 symlink
- 保留原 candidate

### 6.4 Prompt commands

```bash
plotloom prompt check --episode ep001
plotloom prompt extract --episode ep001 --clip clip-01 --field prompt-string
```

MVP 必须具备 prompt 编译能力，但不一定先暴露成复杂命令。

原因：之前已经踩过坑，Markdown artifact 不能原样喂给 Dreamina CLI / API。

`video submit` 内部必须执行 provider-aware prompt compile，从 `video-prompts-en.md` 中提取纯 prompt string，避免 adapter 收到：

```text
clip-01
Duration hint
Reference images
Ending frame
```

这类内部 artifact。

`prompt check/extract` 保留为调试命令，用于在 submit 前人工确认最终会提交给 provider 的 prompt。

### 6.5 Video commands

视频异步优先。

```bash
plotloom video submit --episode ep001 --clip clip-01 --adapter mock
plotloom video submit --episode ep001 --clip clip-01 --adapter dreamina-cli --mode text-to-video
plotloom video submit --episode ep001 --clip clip-01 --adapter happyhorse-fal --mode reference-to-video
plotloom video submit --episode ep001 --clip clip-01 --adapter volcengine-seedance --mode text-to-video

plotloom video poll --episode ep001 --clip clip-01
plotloom video poll --receipt episodes/ep001/videos/clip-01/tasks/happyhorse-fal-req_xxx.toml
plotloom video poll --task-id cgt-... --adapter volcengine-seedance --download-dir PATH
plotloom video list --adapter volcengine-seedance --status queued
plotloom video cancel --task-id cgt-... --adapter volcengine-seedance
```

MVP 必须：

```bash
plotloom video submit --adapter mock
plotloom video submit --adapter dreamina-cli
plotloom video submit --adapter happyhorse-fal
plotloom video submit --adapter volcengine-seedance
plotloom video poll
```

三家真实 adapter 都进入 MVP。当前不预设默认赢家；先接通并用同题 clip 实测速度、成本、音频、画面质量、角色一致性和失败模式。

Task receipt 示例：

```toml
receipt_version = 1
adapter = "volcengine-seedance"
task_id = "cgt-20260430120000-xxxxx"
status = "queued"
submitted_at = "2026-04-30T12:00:00+08:00"
model = "doubao-seedance-2-0-260128"
mode = "text-to-video"
ratio = "9:16"
resolution = "720p"
duration = 15
prompt_file = "episodes/ep001/video-prompts-en.md"
compiled_prompt_sha256 = "..."
clip = "clip-01"
credential_source = "config"
```

`poll` 成功后：

1. 下载 `video_url` 或复制本地结果到 `candidates/vNNN.<adapter>.mp4`。
2. 跑 `ffprobe`。
3. 更新 receipt：`status=succeeded`、`candidate_path=...`、`duration`、`resolution`、`fps`。
4. 不长期依赖 24h 临时 URL。

### 6.6 Select commands

可以统一 image/video selection：

```bash
plotloom select episodes/ep001/videos/clip-01/candidates/v001.mp4
plotloom select episodes/ep001/images/covers/candidates/v001.png
```

行为：copy to sibling `selected.*`，旧 selected 备份。

也可以保留 `asset select` 作为 alias。

### 6.7 Media / stitch commands

```bash
plotloom media probe PATH
plotloom video check-clip episodes/ep001/videos/clip-01/selected.mp4
plotloom stitch --episode ep001
plotloom stitch --episode ep001 --normalize
```

`stitch` 检查：

- selected clips 是否存在。
- aspect ratio 是否一致。
- resolution 是否一致。
- fps 是否一致。
- codec 是否可拼。
- audio stream 是否一致；必要时补静音。

MVP 策略：默认严格；`--normalize` 作为显式开关。

### 6.8 Delivery summary

```bash
plotloom delivery summary --episode ep001
plotloom delivery summary --episode ep001 --output /tmp/plotloom-delivery-ep001.toml
```

MVP 不创建 first-party persistent manifest，不写 `manifest.json` / `workflow-state.json` / `media-info.json` 这类状态文件。

默认行为是把交付摘要输出到 stdout，供 agent 或 Feishu adapter 读取；只有用户显式传 `--output` 时，才写一个临时交付摘要文件。若写文件，建议放在 `/tmp` 或用户指定路径，不默认落在 series repo 内。

Feishu 发送仍由 Hermes / nova-lark 完成。

## 7. Adapter design

### 7.1 Image adapter interface

同步接口：

```python
class ImageAdapter(Protocol):
    name: str

    def generate(self, request: ImageGenerateRequest) -> ImageGenerateResult:
        ...
```

`ImageGenerateRequest`：

```python
@dataclass
class ImageGenerateRequest:
    repo: Path
    kind: Literal["cast", "scene", "cover", "reference"]
    prompt: str
    output_dir: Path
    filename_hint: str | None = None
    reference_images: list[Path] = field(default_factory=list)
```

`ImageGenerateResult`：

```python
@dataclass
class ImageGenerateResult:
    path: Path
    adapter: str
    metadata: dict[str, Any]
```

### 7.2 Video adapter interface

异步接口：

```python
class VideoAdapter(Protocol):
    name: str

    def capabilities(self) -> VideoAdapterCapabilities:
        ...

    def validate_request(self, request: VideoSubmitRequest) -> ValidationResult:
        ...

    def compile_native_request(self, request: VideoSubmitRequest) -> NativeVideoRequest:
        ...

    def submit(self, request: VideoSubmitRequest) -> VideoSubmitResult:
        ...

    def poll(self, task_id: str) -> VideoTaskStatus:
        ...

    def cancel(self, task_id: str) -> None:
        ...
```

所有真实 adapter 都必须先声明 capability，再校验 normalized request，最后编译 provider-native request。不要把同一份 `duration/resolution/ratio/reference/audio` 参数无差别传给三家。

`mock` adapter 可以同步生成文件，但仍通过 `VideoSubmitResult` 返回 `local_path`。

`VideoSubmitRequest` 至少包含：

```python
@dataclass
class VideoSubmitRequest:
    repo: Path
    episode: str
    clip: str
    adapter: str
    mode: Literal["text-to-video", "image-to-video", "reference-to-video", "video-edit"]
    prompt_file: Path
    prompt_text: str
    ratio: str
    resolution: str
    duration: int
    audio_intent: Literal["none", "native_if_supported", "require_native"] = "native_if_supported"
    seed: int | None = None
    first_frame: Path | None = None
    reference_images: list[Path] = field(default_factory=list)
    reference_videos: list[Path] = field(default_factory=list)
    source_video: Path | None = None
    allow_downgrade: bool = False
    allow_normalize_duration: bool = False
```

```python
@dataclass
class VideoSubmitResult:
    adapter: str
    task_id: str | None = None
    local_path: Path | None = None
    status: str = "submitted"
    raw: dict[str, Any] = field(default_factory=dict)
```

```python
@dataclass
class VideoTaskStatus:
    adapter: str
    task_id: str
    status: Literal["queued", "running", "succeeded", "failed", "expired", "cancelled"]
    video_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
```

## 8. Filesystem contracts

### 8.1 Candidate numbering

下一个候选路径：

```text
candidates/v001.ext
candidates/v002.ext
candidates/v003.ext
```

算法：扫描现有 `vNNN.*`，取最大 + 1。

### 8.2 Selected backup

如果 `selected.ext` 已存在：

```text
selected-prev-YYYYMMDD-HHMMSSffffff.ext
```

使用微秒，避免同秒多次选择冲突。

### 8.3 TOML writing

MVP 使用 TOML 作为结构化可见状态：

- `~/plotloom.toml`
- `~/.plotloom/.env.toml`
- `episodes/<ep>/videos/<clip>/tasks/<adapter>-<task-id-or-timestamp>.toml`
- `episodes/<ep>/videos/<clip>/latest-task.toml`

不要写 JSON/YAML 作为 first-party repo artifact。

脚本 stdout 可以输出 JSON 供 agent 消费，但不作为持久 artifact。

`latest-task.toml` 只能作为指针或浅拷贝，不应覆盖历史 receipt。推荐内容：

```toml
receipt = "tasks/volcengine-seedance-cgt-20260430120000.toml"
adapter = "volcengine-seedance"
task_id = "cgt-20260430120000-xxxxx"
updated_at = "2026-04-30T12:30:00+08:00"
```

候选文件推荐带 adapter 后缀，方便同题对比：

```text
candidates/v001.dreamina-cli.mp4
candidates/v002.happyhorse-fal.mp4
candidates/v003.volcengine-seedance.mp4
```

## 9. Error handling

CLI 应统一返回：

- exit code `0`：成功。
- exit code `1`：用户/输入错误，例如 repo 不存在、prompt 缺失。
- exit code `2`：外部依赖缺失，例如 ffmpeg、dreamina、ARK_API_KEY。
- exit code `3`：adapter 任务失败。
- exit code `4`：media validation failed。

错误输出原则：

- 不打印 secrets。
- 不打印 API token / OAuth code / credential file。
- 给出下一步可执行修复建议。

## 10. Implementation plan boundary

本文档只定义 CLI 设计、命令契约和文件契约，不再承载执行计划。

后续重新写 implementation plan 时，应以本文档为准，尤其是：

- 三家真实视频 adapter 都进入 MVP：`dreamina-cli`、`happyhorse-fal`、`volcengine-seedance`。
- 命令面先按 Section 6 固定。
- `video submit` 内置 prompt compile/check。
- task receipt 使用 `tasks/*.toml` + `latest-task.toml`，不覆盖历史。
- secrets/config 使用 `~/.plotloom/.env.toml`，不落入 series repo。

## 11. Open questions

1. 封面图是否需要默认 artifact `cover-prompt.md`？当前 PRD 不希望增加默认中间文件。建议由 agent 临时生成 prompt file，CLI 不强制持久化。
2. `plotloom select` 是否接受 remote URL？MVP 不接受，只接受本地 candidate 文件。
3. 三家 adapter 的默认同题比较指标怎么落文档？建议 comparison report 作为显式命令或临时输出，不作为 hidden state。
4. Codex 图片 adapter 的 MVP 实现建议移植 `codex-imagegen2-api` 的 `codex exec --enable image_generation` 模式；直接 app-server API 以后如果更稳定再替换。
5. 是否需要真实 publish？MVP 不做。

## 12. Recommended MVP command set

最终建议第一版只承诺：

```bash
plotloom init <slug> --title "..."
plotloom config init
plotloom config doctor
plotloom repos list
plotloom validate [--repo PATH]
plotloom doctor [--repo PATH]

plotloom image generate --kind cast --character <slug> --adapter codex-app-server --prompt-file PATH
plotloom image generate --kind cover --episode ep001 --adapter codex-app-server --prompt-file PATH
plotloom asset import ...
plotloom select PATH/TO/candidates/v001.png

plotloom prompt check --episode ep001
plotloom prompt extract --episode ep001 --clip clip-01 --field prompt-string

plotloom video submit --episode ep001 --clip clip-01 --adapter mock
plotloom video submit --episode ep001 --clip clip-01 --adapter dreamina-cli
plotloom video submit --episode ep001 --clip clip-01 --adapter happyhorse-fal
plotloom video submit --episode ep001 --clip clip-01 --adapter volcengine-seedance
plotloom video poll --episode ep001 --clip clip-01
plotloom select PATH/TO/candidates/v001.mp4
plotloom stitch --episode ep001
plotloom media probe PATH
```

不在 MVP 承诺：

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

## 13. Summary

Plotloom CLI 第一版应该小，但必须覆盖短剧生产里最容易出错的确定性动作：

```text
repo init/validate
+ sync image generate/import/select
+ async video submit/poll/download
+ selected candidate semantics
+ ffprobe/ffmpeg stitch
```

它是 Plotloom 走向 short-drama-native videoclaw-v2 的执行地基，但不能抢走 skills/agent 的创作判断。
