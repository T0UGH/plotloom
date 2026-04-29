# Plotloom CLI Brainstorm：覆盖短剧生产的薄 CLI 层

> 日期：2026-04-30  
> 背景：Plotloom 可以长成 short-drama-native videoclaw-v2，但不能退化成 generic video CLI。CLI 应覆盖短剧生产里的确定性动作、异步任务、媒体归档和验收，不负责创作判断。

## 1. 当前判断

Plotloom 需要自己的 CLI 层。

但这个 CLI 不是 runtime，不是 dashboard，不是 worker，不是 PM 系统。

```text
Plotloom = skills + series repo spec + thin CLI + async video adapters
Plotloom CLI = 短剧生产里的确定性手脚
Plotloom skills/agent = 短剧生产里的脑和导演判断
```

CLI 的主价值：

1. 降低 agent 操作文件系统和媒体命令的脆弱性。
2. 把 async video generation 从 chat 阻塞里拆出来。
3. 保证候选、选择、拼接、下载、校验这些动作可重复。
4. 为 Dreamina / VolcEngine / videoclaw / mock 统一一层 adapter contract。
5. 让 series repo 成为真实生产包，而不是只是一堆文档。

## 2. CLI 不做什么

明确不做：

- 不写剧情。
- 不判断爽点。
- 不自动改 prompt。
- 不和用户交互确认。
- 不做任务看板。
- 不跑 daemon / worker / queue。
- 不维护隐藏数据库。
- 不接管 agent 的 skill graph。
- 不把视频模型 provider 写死进 core。

如果 CLI 里出现复杂策略，应该先问：这是不是应该留给 skill / agent？

## 3. CLI 应覆盖的短剧生产对象

Plotloom series repo 中，CLI 主要操作这些对象：

```text
~/plotloom.toml                         # home-level repo registry
plotloom_repo/<slug>/
  series.md
  characters.md
  assets/
    cast/<character>/character-grid.png
    scenes/<scene>/selected.png
  episodes/ep001/
    episode-card.md
    video-prompts.md
    video-prompts-en.md
    images/covers/candidates/v001.png
    images/covers/selected.png
    videos/clip-01/candidates/v001.mp4
    videos/clip-01/selected.mp4
    videos/final.mp4
```

CLI 重点处理：repo discovery、结构初始化、prompt/input 读取、adapter submit、task receipt、candidate download、selected copy、ffprobe、ffmpeg stitch、delivery helper。

## 4. 功能分组

### 4.1 Repo / registry

目标：解决 Hermes 常从 home 启动，agent 不知道哪个短剧 repo 在哪里。

候选命令：

```bash
plotloom repos list
plotloom repos add <slug> --title "..." --path ~/plotloom_repo/<slug> --status active
plotloom repos remove <slug>
plotloom repos set-status <slug> active|paused|archived
plotloom repos resolve <slug>
```

更短命令：

```bash
plotloom list
plotloom use <slug>
```

但 `use` 容易暗示 session state。MVP 先不做隐式 current repo，优先显式 `--repo` 或当前目录自动发现。

规则：

1. 当前目录或父目录有 `series.md`，优先当前 series repo。
2. 否则读 `~/plotloom.toml`。
3. 多个 active repo 时，CLI 只列出选择项，不交互选择；由 agent/user 决定。
4. registry 路径不存在时，报错，不自动重建。

### 4.2 Init / validate

目标：创建和验收 series repo 的最小结构。

```bash
plotloom init <slug> --title "..." [--path ~/plotloom_repo/<slug>]
plotloom validate [--repo PATH]
plotloom doctor [--repo PATH]
```

区别：

- `validate`：检查 repo contract，适合 CI / agent 前置验收。
- `doctor`：检查外部依赖，比如 ffmpeg、dreamina、ARK_API_KEY 是否存在、adapter 可用性。

`init` 应做：

- 创建 repo 目录。
- 写 `series.md`、`characters.md` 最小模板。
- 创建 `episodes/ep001/`。
- 更新 `~/plotloom.toml`。
- 不生成剧情内容。

### 4.3 Image / asset generation and asset helpers

目标：覆盖短剧生产里必需的素材图片生成与归档，包括角色设定图、场景图、封面图。CLI 负责调用图片 adapter、落候选文件、选择归档；不负责审美判断。

素材图片类型：

```text
cast character-grid     # 核心角色 turnaround / character sheet
scene selected/candidate # 可复用场景图
cover candidate/selected # 单集封面图
reference still          # 视频生成用的首帧/尾帧/参考图
```

候选命令：

```bash
plotloom image submit --repo PATH --kind cast --character lin-qiao --adapter codex-imagegen
plotloom image submit --repo PATH --kind scene --scene boardroom --adapter codex-imagegen
plotloom image submit --repo PATH --kind cover --episode ep001 --adapter codex-imagegen
plotloom image submit --repo PATH --kind reference --episode ep001 --clip clip-01 --adapter codex-imagegen

plotloom image poll --repo PATH --kind cover --episode ep001
plotloom image list --repo PATH --kind cast --character lin-qiao
plotloom image info assets/cast/lin-qiao/character-grid.png
```

对于同步图片 adapter，例如 Codex imagegen2 helper，`submit` 可以直接生成并复制到目标目录：

```text
assets/cast/<character>/character-grid.png
assets/scenes/<scene>/candidates/vNNN.png
episodes/ep001/images/covers/candidates/vNNN.png
episodes/ep001/images/references/clip-01/candidates/vNNN.png
```

对于异步图片 adapter，沿用 video 的 task receipt 思路：

```toml
adapter = "codex-imagegen"
kind = "cover"
episode = "ep001"
status = "submitted"
prompt_file = "episodes/ep001/cover-prompt.md"
```

资产导入 / 选择命令：

```bash
plotloom asset import --repo PATH --kind cast --character lin-qiao --file /tmp/x.png --as character-grid
plotloom asset import --repo PATH --kind scene --scene boardroom --file /tmp/x.png --candidate
plotloom asset select --candidate assets/scenes/boardroom/candidates/v001.png
plotloom asset select --candidate episodes/ep001/images/covers/candidates/v001.png
plotloom asset info assets/cast/lin-qiao/character-grid.png
```

这类命令可以统一：

- candidate 命名 `vNNN.*`
- selected copy
- selected-prev backup
- 文件存在性和类型检查
- 图片尺寸 / 格式检查
- 角色 `character-grid.png` 的特殊规则：它是当前有效角色设定图，不是 selected candidate

但不要做“哪个图最好”的判断。

### 4.4 Prompt utilities

这里要谨慎。CLI 不应该写 prompt，但可以检查和抽取 prompt。

```bash
plotloom prompt check episodes/ep001/video-prompts-en.md
plotloom prompt extract --file episodes/ep001/video-prompts-en.md --clip clip-01 --field prompt-string
```

价值：避免把 Markdown artifact 原样喂给 Dreamina/Volc API。

MVP 可做最小：

- 检查 `video-prompts-en.md` 是否包含 `Prompt string for --prompt`。
- 抽取某个 clip 的纯 prompt string。
- 检查 duration / ratio / model hints。

但不要自动翻译、重写、优化 prompt。

### 4.5 Video submit / poll / download

这是 CLI 的核心。

```bash
plotloom video submit --repo PATH --episode ep001 --clip clip-01 --adapter mock
plotloom video submit --repo PATH --episode ep001 --clip clip-01 --adapter dreamina
plotloom video submit --repo PATH --episode ep001 --clip clip-01 --adapter volcengine-seedance

plotloom video poll --repo PATH --episode ep001 --clip clip-01
plotloom video poll --task-id cgt-... --adapter volcengine-seedance --download-dir ...
plotloom video list --adapter volcengine-seedance --status queued
plotloom video cancel --task-id cgt-... --adapter volcengine-seedance
```

Submit 行为：

1. 找到 clip prompt。
2. 找到 reference images/videos/audio。
3. 调 adapter。
4. 如果同步返回文件，放入 `candidates/vNNN.mp4`。
5. 如果异步返回 task id，写 task receipt。

Task receipt 示例：

```toml
adapter = "volcengine-seedance"
task_id = "cgt-..."
status = "queued"
submitted_at = "2026-04-30T01:00:00+08:00"
model = "doubao-seedance-2-0-260128"
ratio = "9:16"
resolution = "720p"
duration = 15
prompt_file = "episodes/ep001/video-prompts-en.md"
clip = "clip-01"
```

Receipt 是可见生产收据，不是 hidden runtime state。

Poll 行为：

1. 查询 task。
2. 更新 receipt status。
3. 成功后立即下载 `video_url`。
4. 存入下一个 `candidates/vNNN.mp4`。
5. 保存 response 摘要到 TOML 或 Markdown note，避免依赖 24h 临时 URL。
6. 跑 `ffprobe`。

### 4.6 Candidate selection

目标：把用户/agent 选择落到 repo。

```bash
plotloom select episodes/ep001/videos/clip-01/candidates/v003.mp4
plotloom select episodes/ep001/images/covers/candidates/v002.png
```

行为：

- copy candidate to `selected.*`
- 旧 selected 备份为 `selected-prev-YYYYMMDD-HHMMSS.*`
- 不用 symlink
- 保留原 candidate

可选：

```bash
plotloom candidates list episodes/ep001/videos/clip-01
plotloom candidates info episodes/ep001/videos/clip-01
```

### 4.7 Media probe / normalize / stitch

目标：拼 final.mp4 前做硬验收。

```bash
plotloom media probe FILE
plotloom video check-clip episodes/ep001/videos/clip-01/selected.mp4
plotloom stitch --repo PATH --episode ep001
plotloom stitch --repo PATH --episode ep001 --normalize
```

`stitch` 前检查：

- selected clips 是否存在
- resolution 是否一致
- fps 是否一致
- codec 是否可拼
- audio stream 是否存在 / 是否需要补静音
- aspect ratio 是否符合 9:16

MVP 策略：

- 默认严格检查；不自动做复杂修复。
- 可以提供 `--normalize`，用 ffmpeg 统一 resolution/fps/audio，但输出前要说明做了什么。

### 4.8 Delivery helpers

Feishu 是 delivery adapter，不是产品中心。

CLI 可做本地打包或输出交付清单，但不一定直接发飞书。

```bash
plotloom package --repo PATH --episode ep001
plotloom delivery manifest --repo PATH --episode ep001
```

Feishu 发送仍可由 Hermes/nova-lark 完成：

```text
agent reads manifest -> send MEDIA:/path/to/final.mp4
```

后续如果要做：

```bash
plotloom deliver feishu --episode ep001
```

也应是 thin adapter，不做状态中心。

### 4.9 Publish / platform metadata

这属于 videoclaw 可复用能力，但不是 MVP 必须。

未来命令：

```bash
plotloom publish prepare --platform tiktok --episode ep001
plotloom publish prepare --platform youtube-shorts --episode ep001
plotloom publish douyin --episode ep001
```

MVP 先不做真实发布，最多生成 metadata 草稿：title、description、hashtags、cover path、final video path。

## 5. Adapter 设计

### 5.1 MVP adapters

优先级：

1. `mock`：本地假视频，保障 E2E。
2. `dreamina`：即梦 CLI，已有登录和 maestro 经验，但排队慢。
3. `volcengine-seedance`：火山方舟 API，明天拿 key 验证排队和权限。
4. `videoclaw`：作为历史/兼容执行层，后续再接。

### 5.2 Adapter contract

每个 adapter 至少支持：

```text
submit(input) -> SubmitResult
poll(task_id) -> TaskStatus
cancel(task_id) -> optional
list(status) -> optional
```

`SubmitResult`：

```text
sync file path | async task_id | failed error
```

`TaskStatus`：

```text
queued | running | succeeded | failed | expired | cancelled
video_url / local_path when succeeded
error code/message when failed
```

### 5.3 为什么 async-first

即梦排队已证明：短剧视频生产不能把 chat turn 卡死在“等模型返回”。

Plotloom 应默认：

```text
submit -> receipt -> continue other work -> poll -> download -> Feishu 回传 -> accept/reroll
```

## 6. 一版 CLI 命令草案

如果压到最小 MVP，我建议只有这些：

```bash
plotloom init <slug> --title "..."
plotloom repos list
plotloom validate [--repo PATH]
plotloom doctor [--repo PATH]

plotloom image submit --kind cast --character lin-qiao --adapter codex-imagegen
plotloom image submit --kind cover --episode ep001 --adapter codex-imagegen
plotloom image list --kind cover --episode ep001

plotloom video submit --episode ep001 --clip clip-01 --adapter mock|dreamina|volcengine-seedance
plotloom video poll --episode ep001 --clip clip-01
plotloom select PATH/TO/candidates/v001.mp4
plotloom stitch --episode ep001
```

稍完整一点：

```bash
plotloom prompt extract --episode ep001 --clip clip-01
plotloom asset import/select
plotloom media probe FILE
plotloom candidates list PATH
plotloom package --episode ep001
```

不建议 MVP 做：

```bash
plotloom run
plotloom daemon
plotloom dashboard
plotloom workflow
plotloom batch-season
plotloom publish
```

## 7. 命令与短剧流程的映射

```text
新短剧开始
  -> plotloom init
  -> agent/skills 写 series.md characters.md episode-card.md video-prompts.md
  -> plotloom validate

角色/场景/封面图片
  -> agent/skills 写图片 brief / prompt
  -> plotloom image submit --adapter codex-imagegen
  -> plotloom image poll/list
  -> Feishu 回传候选
  -> plotloom asset select 或 character-grid 归档

视频生成
  -> agent 写 video-prompts-en.md
  -> plotloom prompt extract/check
  -> plotloom video submit
  -> plotloom video poll
  -> Feishu 回传候选
  -> plotloom select

成片
  -> plotloom stitch
  -> plotloom media probe
  -> agent/nova-lark deliver final.mp4
```

## 8. 开放问题

1. CLI 包名是否就叫 `plotloom`，还是保留 Python package + console script？倾向直接 `plotloom`。
2. 是否需要 `plotloom current` / `plotloom use`？MVP 不建议，避免隐式状态。
3. task receipt 放在 clip 目录下单文件，还是 `tasks/<task_id>.toml`？倾向 clip 目录单文件，便于人看。
4. 是否允许 CLI 写 `video-prompts-en.md`？不建议，除非只是模板生成；真正翻译/改写交给 skill。
5. VolcEngine API 是否比 Dreamina 快？明天拿 key 后实测。
6. character-grid 是否适合直接作为 Seedance reference image？需要图生视频探针验证，可能需要派生单张角色参考图。

## 9. 当前推荐路线

第一阶段：repo + fake E2E CLI

```text
init / validate / fake submit / select / stitch / probe
```

第二阶段：async adapter

```text
volcengine-seedance submit/poll/download
Dreamina submit/query/download 包装
```

第三阶段：image + asset/prompt helper

```text
image submit/list/poll
asset import/select
prompt extract/check
```

第四阶段：delivery/package

```text
package manifest
Feishu delivery adapter if necessary
```

不要先做 provider abstraction 大而全。先围绕 ep001 成片闭环，让 CLI 覆盖最容易出错的确定性动作。
