# Plotloom CLI Technical Design

> 日期：2026-04-30  
> 状态：Draft v0.1  
> 目标：定义 Plotloom 自有薄 CLI 层，用于覆盖短剧生产中的确定性执行、素材归档、异步视频任务和成片验收。  
> 相关文档：
> - `docs/design/2026-04-30-plotloom-cli-brainstorm.md`
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

## 2. 为什么选 Python，不选 JS

### 2.1 Python 更适合当前 MVP

Plotloom MVP 的 CLI 任务主要是本地生产工具链：

- 文件系统操作：初始化 repo、复制候选、备份 selected。
- TOML/Markdown 读写。
- 调 ffmpeg / ffprobe。
- 下载视频 URL。
- 调火山方舟 Python SDK。
- 复用现有 Python 脚本：`init_series.py`、`validate_repo.py`、`select_candidate.py`、`stitch_ffmpeg.py`。
- 与 Codex imagegen2 helper / Dreamina CLI / VolcEngine API 做 thin adapter。

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
- package manifest

CLI 不做：

- 剧情生成
- 爽点判断
- prompt 改写
- 用户交互确认
- 多 agent 编排
- daemon / queue / dashboard
- hidden DB

### 3.2 Repo-visible state

所有生产状态都应该落在 series repo 的可见文件里。

允许：

```text
episodes/ep001/videos/clip-01/task.volcengine.toml
episodes/ep001/videos/clip-01/candidates/v001.mp4
episodes/ep001/videos/clip-01/selected.mp4
```

不允许：

```text
~/.plotloom/tasks.db
.plotloom/state.sqlite
hidden queue worker state
```

`task.*.toml` 是任务收据，不是 workflow runtime。

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

- `codex-imagegen`：调用 Codex imagegen2 helper，复制输出图。
- `dreamina`：调用 Dreamina CLI，记录 submit_id，query/download。
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
    image_codex.py
    video_mock.py
    video_dreamina.py
    video_volcengine.py
  commands/
    __init__.py
    repos.py
    init.py
    validate.py
    doctor.py
    image.py
    asset.py
    video.py
    select.py
    stitch.py
    media.py
    package.py
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
volcengine = ["volcengine-python-sdk[ark]>=5.0.0"]
dev = ["pytest>=8", "ruff>=0.5"]

[project.scripts]
plotloom = "plotloom.cli:main"
```

说明：

- Python 3.11+：标准库有 `tomllib` 读 TOML；写 TOML 用 `tomli-w` 或自写小函数。
- `click`：简单稳定，videoclaw 也用 click；不用 Typer 避免额外复杂度。
- `requests`：下载视频 URL。
- `volcengine-python-sdk[ark]` 作为 optional dependency，避免没有 key 时污染基础安装。

## 6. 命令设计

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
plotloom init
plotloom repos list
plotloom validate
plotloom doctor
```

Repo discovery：

1. 如果 `--repo PATH` 存在，使用它。
2. 否则从当前目录向上找 `series.md`。
3. 否则读 `~/plotloom.toml`。
4. 如果多个 active repo，不交互选择，只输出候选并返回非零或提示 agent 选择。

### 6.2 Image commands

MVP 图片同步。

```bash
plotloom image generate --kind cast --character lin-qiao --adapter codex-imagegen
plotloom image generate --kind scene --scene boardroom --adapter codex-imagegen
plotloom image generate --kind cover --episode ep001 --adapter codex-imagegen
plotloom image generate --kind reference --episode ep001 --clip clip-01 --adapter codex-imagegen
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

MVP 可选，但建议尽早做。

原因：之前已经踩过坑，Markdown artifact 不能原样喂给 Dreamina CLI / API。

`prompt extract` 应从 `video-prompts-en.md` 中提取纯 prompt string，避免 adapter 收到：

```text
clip-01
Duration hint
Reference images
Ending frame
```

这类内部 artifact。

### 6.5 Video commands

视频异步优先。

```bash
plotloom video submit --episode ep001 --clip clip-01 --adapter mock
plotloom video submit --episode ep001 --clip clip-01 --adapter dreamina
plotloom video submit --episode ep001 --clip clip-01 --adapter volcengine-seedance

plotloom video poll --episode ep001 --clip clip-01
plotloom video poll --task-id cgt-... --adapter volcengine-seedance --download-dir PATH
plotloom video list --adapter volcengine-seedance --status queued
plotloom video cancel --task-id cgt-... --adapter volcengine-seedance
```

MVP 必须：

```bash
plotloom video submit --adapter mock
plotloom video submit --adapter volcengine-seedance  # key ready 后
plotloom video poll
```

Dreamina 可保留为 adapter，但鉴于排队慢，优先级低于 VolcEngine 实测。

Task receipt 示例：

```toml
adapter = "volcengine-seedance"
task_id = "cgt-20260430120000-xxxxx"
status = "queued"
submitted_at = "2026-04-30T12:00:00+08:00"
model = "doubao-seedance-2-0-260128"
ratio = "9:16"
resolution = "720p"
duration = 15
prompt_file = "episodes/ep001/video-prompts-en.md"
clip = "clip-01"
```

`poll` 成功后：

1. 下载 `video_url` 到 `candidates/vNNN.mp4`。
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

### 6.8 Package / delivery manifest

```bash
plotloom package --episode ep001
plotloom delivery manifest --episode ep001
```

MVP 只生成本地 manifest，不直接发 Feishu。

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

    def submit(self, request: VideoSubmitRequest) -> VideoSubmitResult:
        ...

    def poll(self, task_id: str) -> VideoTaskStatus:
        ...

    def cancel(self, task_id: str) -> None:
        ...
```

`mock` adapter 可以同步生成文件，但仍通过 `VideoSubmitResult` 返回 `local_path`。

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
- `task.<adapter>.toml`
- optional package manifest TOML

不要写 JSON/YAML 作为 first-party repo artifact。

脚本 stdout 可以输出 JSON 供 agent 消费，但不作为持久 artifact。

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

## 10. MVP implementation plan

### Phase 1: CLI shell + repo E2E

实现：

```bash
plotloom init
plotloom repos list
plotloom validate
plotloom doctor
plotloom video submit --adapter mock
plotloom select
plotloom stitch
plotloom media probe
```

验收：

```bash
plotloom init fake-heiress --title "Fake Heiress"
plotloom validate --repo ~/plotloom_repo/fake-heiress
plotloom video submit --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01 --adapter mock
plotloom select ~/plotloom_repo/fake-heiress/episodes/ep001/videos/clip-01/candidates/v001.mp4
plotloom stitch --repo ~/plotloom_repo/fake-heiress --episode ep001
ffprobe ~/plotloom_repo/fake-heiress/episodes/ep001/videos/final.mp4
```

### Phase 2: sync image generation

实现：

```bash
plotloom image generate --kind cast --character ... --adapter codex-imagegen
plotloom image generate --kind cover --episode ep001 --adapter codex-imagegen
plotloom asset import/select
```

验收：

- `character-grid.png` 正确生成/备份。
- cover candidates 正确编号。
- selected copy 行为正确。

### Phase 3: VolcEngine async video adapter

前提：贵平提供 `ARK_API_KEY` 并确认模型开通。

实现：

```bash
plotloom video submit --adapter volcengine-seedance
plotloom video poll
plotloom video cancel
```

验收：

- 创建 task 成功。
- receipt 写入。
- poll 能看到 queued/running/succeeded。
- 成功后下载 candidate。
- ffprobe 正常。

### Phase 4: Dreamina adapter

实现：

```bash
plotloom video submit --adapter dreamina
plotloom video poll --adapter dreamina
```

验收：

- 能包装 `dreamina text2video/multimodal2video`。
- 能记录 submit_id。
- 能 query/download。

### Phase 5: prompt extract/check

实现：

```bash
plotloom prompt check
plotloom prompt extract
```

验收：

- 不再把 Markdown artifact 原样传给模型。
- 能提取 `Prompt string for --prompt`。

## 11. Open questions

1. `plotloom image generate` 的 prompt 来源是否允许用临时 `--prompt-file`？建议允许，方便 agent 生成 brief 后调用。
2. 封面图是否需要默认 artifact `cover-prompt.md`？当前 PRD 不希望增加默认中间文件。建议由 agent 临时生成 prompt file，CLI 不强制持久化。
3. `task.volcengine.toml` 是单任务覆盖，还是多任务并存？建议 clip 目录下可有 `tasks/<task_id>.toml`，同时 `latest-task.toml` 指向最近任务。MVP 可先单文件。
4. `plotloom select` 是否接受 remote URL？MVP 不接受，只接受本地 candidate 文件。
5. 是否需要真实 publish？MVP 不做。

## 12. Recommended MVP command set

最终建议第一版只承诺：

```bash
plotloom init <slug> --title "..."
plotloom repos list
plotloom validate [--repo PATH]
plotloom doctor [--repo PATH]

plotloom image generate --kind cast --character <slug> --adapter codex-imagegen --prompt-file PATH
plotloom image generate --kind cover --episode ep001 --adapter codex-imagegen --prompt-file PATH
plotloom asset import ...
plotloom select PATH/TO/candidates/v001.png

plotloom video submit --episode ep001 --clip clip-01 --adapter mock|volcengine-seedance
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