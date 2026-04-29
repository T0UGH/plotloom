# Plotloom MVP 技术设计（中文版）

> 状态：Draft v0.1  
> 日期：2026-04-29  
> Owner：贵平  
> Agent：Nova

## 1. 一句话技术定义

Plotloom 的工程形态是：

```text
repo-first agent-neutral skill pack
+ stable series repo contract
+ thin local/tool adapters
```

也就是说，Plotloom 不是一个常驻 runtime、不是 Web app、不是任务系统。它是一组可被不同 agent runtime 加载的短剧生产 skills，通过统一的 repo 文件协议协作；少量 Python scripts 和外部 CLI 只作为工具适配层存在。

## 2. 技术目标

MVP 技术实现要证明：

1. 一个 agent 可以在本地发现或创建 Plotloom series repo。
2. 多个 Plotloom skills 可以围绕同一个 repo 读写稳定 artifact。
3. 图片生成、视频生成、拼接、飞书回传可以通过薄 adapter 接入。
4. 第一集可以从 prompt package 推进到候选 clip、selected clip、final.mp4。
5. 后续更换图像/视频模型时，不需要改变 core skill graph 和 repo contract。

## 3. 非目标

MVP 不做：

- 后台服务 / daemon
- Web app / dashboard
- 数据库
- LangGraph / Temporal / Celery / queue
- 中心化 agent runtime
- 任务状态机 / production tracker
- MCP server 作为核心依赖
- 多模型 benchmark 系统
- 平台发布自动化

这些能力以后可以作为 adapter 或独立工具出现，但不能进入 Plotloom core。

## 4. 总体架构

```text
Agent Host
  Hermes / Codex / Claude Code / OpenCode / OpenClaw
        |
        v
Plotloom Skill Pack
  using-plotloom
  plotloom-create-series
  plotloom-design-character-grid
  plotloom-write-video-prompts
  plotloom-translate-video-prompts-en
  plotloom-draw-image
  plotloom-draw-video-clip
  plotloom-stitch-clips
  plotloom-deliver
        |
        v
Series Repo Contract
  ~/plotloom.toml
  plotloom_repo/<slug>/series.md
  plotloom_repo/<slug>/characters.md
  plotloom_repo/<slug>/episodes/ep001/video-prompts.md
  plotloom_repo/<slug>/episodes/ep001/video-prompts-en.md
  assets / candidates / selected / final.mp4
        |
        v
Thin Adapters
  codex-imagegen adapter
  jimeng-cli video adapter
  ffmpeg stitch adapter
  nova-lark Feishu delivery adapter
```

核心原则：

- skill pack 决定“该做什么”和“读写哪些 artifact”。
- series repo 承载上下文和产物，是跨 agent 协作的稳定边界。
- adapter 决定“具体怎么调用某个工具”。
- agent host 只负责加载 skill、执行命令、读写文件、向用户交互。

### 4.1 Plotloom Repo 目录设计

Plotloom 自身 repo 采用“多 skill 的 skill-pack repo”结构，而不是单个巨型 `SKILL.md`，也不是 runtime 项目。

```text
plotloom/
  README.md

  docs/
    prd/
      plotloom-mvp-prd.zh.md
    design/
      plotloom-technical-design.zh.md
    plans/
    decisions/

  skills/
    plotloom-series-bible/
      SKILL.md
      templates/
        series.md
        characters.md
    plotloom-episode-card/
      SKILL.md
      templates/
        episode-card.md
    plotloom-shot-prompts/
      SKILL.md
      references/
        visual-continuity.md
      templates/
        shot-list.md
        image-prompts.md
        video-prompts.md
    plotloom-asset-selection/
      SKILL.md
      references/
        selection-rubric.md
    plotloom-video-adapter/
      SKILL.md
      references/
        dreamina-cli.md
      templates/
        adapter-request.md
    plotloom-stitch-deliver/
      SKILL.md
      references/
        ffmpeg.md

  templates/
    series-repo/
      plotloom.toml
      series.md
      characters.md
      assets/
      episodes/
      outputs/

  scripts/
    init_series.py
    validate_repo.py
    select_candidate.py
    ffprobe_media.py
    stitch_ffmpeg.py
    adapters/
      fake_video.py
      dreamina_cli.py

  adapters/
    codex.md
    hermes.md
    claude-code.md
    opencode.md

  examples/
    tiny-series/
```

目录分工：

| 目录 | 职责 | 是否 core |
|---|---|---:|
| `skills/` | agent-neutral 短剧生产 skills，定义创作阶段、输入输出、验收标准 | 是 |
| `templates/series-repo/` | 新短剧 repo 的最小骨架和初始 artifact 模板 | 是 |
| `scripts/` | 确定性辅助脚本：初始化、校验、selected copy、ffprobe、ffmpeg、adapter glue | 是，但必须保持薄 |
| `scripts/adapters/` | 外部工具调用包装，如 fake video、Dreamina CLI | adapter |
| `adapters/` | Codex / Hermes / Claude Code / OpenCode 的安装与运行说明 | 非 core |
| `examples/` | tiny demo series，用于端到端验收和回归 | 是 |
| `docs/` | PRD、技术设计、implementation plan、决策记录 | 是 |

设计约束：

- core workflow 放 `skills/`，不是放 runtime-specific adapter。
- `adapters/` 只解释不同 agent host 如何加载/使用 Plotloom，不复制整套业务逻辑。
- `scripts/` 只做确定性动作；创作判断、审美判断、rerun 建议仍写在 skill/prompt 中。
- `templates/series-repo/` 是创建短剧 repo 的来源；实际生产状态以 series repo 内 Markdown/TOML/media 文件为准。
- MVP 先实现 core skills + templates + fake adapter + ffmpeg；Codex/Hermes/Claude/OpenCode adapters 等 core 稳定后再补全。

## 5. 技术选型

### 5.1 实现语言：Python 优先

MVP scripts 使用 Python。

原因：

- Hermes / 本地 agent 环境通常天然可运行 Python。
- 文件系统、TOML、Markdown、subprocess、路径处理都简单。
- 适合包一层 ffmpeg / ffprobe / CLI glue。
- 不需要编译，不引入重 runtime。

边界：

- Python scripts 是辅助工具，不是 Plotloom 产品 runtime。
- 不长期运行。
- 不维护后台状态。
- 不隐藏核心创作判断；创作判断仍在 skills 和 agent 中完成。

### 5.2 配置与文本格式：TOML + Markdown

- Markdown：创作上下文、prompt、说明文档。
- TOML：轻量 machine-readable 配置和索引。

MVP 使用：

```text
~/plotloom.toml              # home 级 repo registry
series.md                    # series 级中文创作上下文
characters.md                # 角色设定
video-prompts.md             # 中文视频生成主源
video-prompts-en.md          # 英文模型执行版
```

不用 YAML / JSON 作为 first-party repo artifact，避免 schema 负担和格式漂移。

### 5.3 Skill 格式：agent-neutral `SKILL.md` baseline

核心 skill 目录采用阶段拆分，而不是一个大 skill：

```text
skills/
  plotloom-series-bible/
    SKILL.md
    templates/
      series.md
      characters.md
  plotloom-episode-card/
    SKILL.md
    templates/
      episode-card.md
  plotloom-shot-prompts/
    SKILL.md
    references/
      visual-continuity.md
    templates/
      shot-list.md
      image-prompts.md
      video-prompts.md
  plotloom-asset-selection/
    SKILL.md
    references/
      selection-rubric.md
  plotloom-video-adapter/
    SKILL.md
    references/
      dreamina-cli.md
    templates/
      adapter-request.md
  plotloom-stitch-deliver/
    SKILL.md
    references/
      ffmpeg.md
```

旧命名如 `using-plotloom`、`plotloom-create-series`、`plotloom-draw-video-clip` 可作为内部别名或历史概念，但落地 repo 目录以以上阶段型 skill 名为准。

设计原则：

- `SKILL.md` 写 runtime-neutral 指令，不出现某个 agent 的专用 tool 名称。
- runtime-specific 安装、路径、权限放 adapter docs。
- scripts 只能做确定性工程动作，不能替代 creative judgment。
- 默认优先把能力写进 prompt / skill 指令；只有当动作需要确定性文件操作、媒体探测、CLI glue 或重复验证时才写 script。

### 5.4 图片生成：Codex imagegen adapter

MVP 图片生成选型：Codex imagegen。

用途：

- 核心角色 character grid。
- 关键场景 candidates。
- EP cover candidates。

输入：

- `series.md`
- `characters.md`
- skill 生成的图片创作说明
- 可选已有参考图

输出：

```text
assets/cast/<character-slug>/character-grid.png
assets/cast/<character-slug>/character-grid-vN.png
assets/scenes/<scene-slug>/candidates/v001.png
assets/scenes/<scene-slug>/selected.png
episodes/ep001/images/covers/candidates/v001.png
episodes/ep001/images/covers/selected.png
```

边界：

- Codex imagegen 是 MVP adapter，不是 Plotloom core。
- core skill 只表达图片意图、质量要求、输出路径。
- 如果未来换到其他 image model，只替换 adapter，不改 repo contract。
- `character-grid.png` 永远是当前有效引用。`character-grid-vN.png` 只作为历史版本或重生成归档；进入视频生成时，skills 只依赖 `character-grid.png`。

MVP 可执行契约：

- adapter 必须支持 dry-run，输出将要使用的 prompt、参考图、目标路径，不调用真实生成。
- adapter 必须把生成结果保存或复制到指定 output path，而不是让调用方去猜默认下载目录。
- adapter 必须返回简洁 stdout 摘要，包含 `ok`、`output_path`、`adapter`、失败原因；stdout 可用 JSON，但不要把 JSON 持久化为 repo artifact。
- adapter 的 auth、账号、模型参数、真实命令行写在 runtime-specific adapter 文档或脚本注释中，不写进 core skill。

### 5.5 视频生成：即梦 CLI adapter

MVP 视频生成选型：即梦 CLI。

用途：

- 按 clip 生成视频候选。
- 一次生成一个候选，不批量三连抽。
- 每个候选生成后立即回传用户决策。

输入：

- `episodes/ep001/video-prompts.md`
- `episodes/ep001/video-prompts-en.md`（如 adapter 需要英文）
- `assets/cast/<character-slug>/character-grid.png`
- 可选场景/封面/参考图

输出：

```text
episodes/ep001/videos/clip-01/candidates/v001.mp4
episodes/ep001/videos/clip-01/candidates/v002.mp4
episodes/ep001/videos/clip-01/selected.mp4
```

边界：

- 即梦 CLI 是 MVP adapter，不是 Plotloom core。
- adapter 只负责把 prompt 和参考图传给即梦 CLI，并把输出归档到 repo。
- prompt 仍由 Plotloom skills 生产，不在 adapter 内临时拼凑。
- 如果即梦 CLI 输出格式变化，adapter 吸收变化，repo contract 不变。

MVP 可执行契约：

- adapter 每次只生成一个候选视频。
- adapter 必须支持 dry-run，显示即将调用的 prompt section、参考图、输出路径、时长/画幅 hint。
- adapter 必须等待或轮询即梦 CLI 任务完成，并把最终视频保存为指定的 `candidates/vNNN.mp4`。
- adapter 失败时必须保留错误摘要和必要日志，但日志不进入 series repo 的核心 contract。
- adapter 不自动写 `selected.mp4`；只有用户接受候选后，skill 才执行 selected 落盘。

### 5.6 视频拼接：ffmpeg / ffprobe

MVP 拼接选型：ffmpeg + ffprobe。

职责：

1. 检查 selected clips 是否存在。
2. 用 ffprobe 读取：
   - container
   - video codec
   - audio codec
   - resolution
   - frame rate
   - duration
   - aspect ratio
3. 如果兼容，concat 为 final.mp4。
4. 如果不兼容，先归一化，或停止并报告问题。

输出：

```text
episodes/ep001/videos/final.mp4
```

边界：

- 只做最小可播放拼接。
- 不做完整剪辑系统。
- 不做复杂字幕、BGM、混音、调色。

默认归一化 profile：

```text
container: mp4
video: h264
audio: aac when audio exists
aspect: 9:16 preferred for short drama
resolution: preserve source if compatible; otherwise normalize to a single vertical profile
fps: preserve source if compatible; otherwise normalize to a single fps
```

具体 resolution / fps 可在实现时按即梦 CLI 输出确定；设计层只要求 final.mp4 兼容可播放。

### 5.7 飞书交付：nova-lark / lark-cli

MVP 飞书交付选型：复用 `nova-lark` / `lark-cli`。

职责：

- 回传图片候选。
- 回传视频候选。
- 回传 final.mp4。
- 消息内标注 episode、clip、version、需要用户做的决定。

边界：

- Feishu 是 delivery adapter，不是状态中心。
- 不把候选选择、生产进度、任务状态写进 Feishu 作为唯一事实源。
- 真实状态来自 series repo 文件。

MVP 可执行契约：

- adapter 必须支持 dry-run，输出将发送的 target、media path、message text。
- adapter 必须校验媒体文件存在，并在上传失败时返回简洁错误摘要。
- adapter 只负责发送媒体和提示，不负责记录用户选择；用户选择最终必须体现为 repo 中的 `selected.*` 文件。

## 6. Repo Registry 设计

Home 级 registry：

```toml
# ~/plotloom.toml

[[repos]]
slug = "fake-heiress-reboot"
title = "Fake Heiress Reboot"
path = "~/plotloom_repo/fake-heiress-reboot"
status = "active"
```

字段：

| 字段 | 必需 | 说明 |
|---|---:|---|
| `slug` | 是 | repo 唯一短名，用于目录和交互展示 |
| `title` | 是 | 人类可读短剧标题 |
| `path` | 是 | series repo 路径，支持 `~` |
| `status` | 是 | `active` / `paused` / `archived` |

不记录：

- 当前做到哪一步
- 已生成几个 clip
- 用户是否接受候选
- workflow state
- 任务列表

这些通过 repo 文件是否存在来判断。

## 7. Series Repo Contract

最小 series repo：

```text
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
          v002.png
        selected.png
        notes.md

  episodes/
    ep001/
      episode-card.md      # optional
      video-prompts.md
      video-prompts-en.md  # generated when needed

      images/
        covers/
          candidates/
            v001.png
            v002.png
            v003.png
          selected.png

      videos/
        clip-01/
          candidates/
            v001.mp4
            v002.mp4
          selected.mp4
        clip-02/
          candidates/
            v001.mp4
          selected.mp4
        final.mp4
```

Contract vs suggestion：

| 项 | 类型 | 稳定性 |
|---|---|---|
| `series.md` | contract | 必须稳定 |
| `characters.md` | contract | 必须稳定 |
| `video-prompts.md` | contract | 必须稳定 |
| `video-prompts-en.md` | contract when needed | 需要英文模型时稳定 |
| `assets/cast/*/character-grid.png` | contract | 核心角色必需 |
| `candidates/vNNN.*` | contract | 抽卡产物命名稳定 |
| `selected.*` | contract | 用户接受后稳定 |
| `final.mp4` | contract | MVP 成片输出 |
| `notes.md` | suggestion | 可选说明 |
| `episode-card.md` | optional contract | 需要意图锚点时使用 |

### 7.1 Selected 落盘语义

候选被用户接受后，使用 copy 语义写入 `selected.*`：

- 保留原始 `candidates/vNNN.*`。
- 将被接受候选复制为同目录下的 `selected.*`。
- 如果已有 `selected.*`，覆盖前先备份为 `selected-prev-YYYYMMDD-HHMMSS.*`。
- 不使用 symlink 作为 MVP 默认，避免跨 agent / 跨机器 / 打包交付时路径失效。
- `selected.*` 是当前有效选择；没有 `selected.*` 就不能视为该资产/clip 已被用户接受。

### 7.2 媒体 Git 策略

MVP 不强制 series repo 使用 Git。若用户把 series repo 放进 Git，默认建议忽略重媒体和生成候选：

```gitignore
# Plotloom generated media
**/videos/**/*.mp4
**/videos/**/*.mov
**/videos/**/*.webm
**/images/**/candidates/*
**/assets/**/candidates/*

# Keep selected still images optional; large teams may choose Git LFS later.
```

原则：

- Markdown / TOML 创作源适合提交。
- 大视频和批量候选图默认本地保留或后续接 Git LFS / 对象存储。
- `selected.*` 是否提交由具体 repo 决定；MVP core 不强制。

## 8. Skill Graph 设计

Plotloom 不是固定 pipeline，但 MVP 有默认 happy path。

```text
using-plotloom
  -> plotloom-create-series
  -> plotloom-design-character-grid
  -> plotloom-write-video-prompts
  -> plotloom-translate-video-prompts-en
  -> plotloom-draw-image
  -> plotloom-draw-video-clip
  -> plotloom-deliver
  -> plotloom-stitch-clips
  -> plotloom-deliver
```

每个 skill 必须声明：

- trigger：什么时候应该加载。
- inputs：读哪些文件和上下文。
- outputs：写哪些文件。
- stop condition：何时停止问用户或等待反馈。
- next skills：完成后建议什么下一步。

### 8.1 `using-plotloom`

职责：发现当前 repo 或决定是否创建新 repo。

核心逻辑：

```text
if current dir or parent has series.md:
  use that repo
else:
  read ~/plotloom.toml
  if exactly one active repo and user says continue:
    use it, state selection basis
  elif multiple candidates:
    ask user to choose
  elif user clearly wants new series:
    create new repo via plotloom-create-series
  else:
    brainstorm only, do not write files
```

### 8.2 `plotloom-create-series`

职责：创建 series repo skeleton 和初始创作上下文。

写入：

- `series.md`
- `characters.md`
- 基础目录结构
- `~/plotloom.toml`

不做：

- 不生成视频。
- 不生成长季完整剧本。
- 不写任务计划。

### 8.3 `plotloom-design-character-grid`

职责：为核心角色生成或重生成 character grid。

MVP adapter：Codex imagegen。

完成条件：核心角色拥有 `assets/cast/<character-slug>/character-grid.png`。

### 8.4 `plotloom-write-video-prompts`

职责：把 series intent 转成 EP001 clip prompt。

输出：

- `episodes/ep001/video-prompts.md`
- 必要时 `episodes/ep001/episode-card.md`

原则：Seedance / 即梦类视频模型需要连续叙事 prompt，不是机械 shot list。

### 8.5 `plotloom-translate-video-prompts-en`

职责：生成英文模型执行版。

输出：

- `episodes/ep001/video-prompts-en.md`

如果目标 adapter 支持中文，可跳过；但 MVP 默认保留英文执行版，方便跨模型。

### 8.6 `plotloom-draw-image`

职责：调用 image adapter 生成图片候选或 character grid。

MVP adapter：Codex imagegen。

### 8.7 `plotloom-draw-video-clip`

职责：调用 video adapter 生成单条 clip 候选。

MVP adapter：即梦 CLI。

规则：

- 每次只生成一个候选。
- 输出保存到 `candidates/vNNN.mp4`。
- 生成后立即调用 delivery adapter 回传。
- 未经用户接受，不写 `selected.mp4`。

### 8.8 `plotloom-stitch-clips`

职责：把 selected clips 拼接成 final.mp4。

MVP adapter：ffmpeg / ffprobe。

规则：

- 缺少 selected clip 时停止。
- 不兼容时先归一化或报告。
- 输出 final.mp4 后需要验证可播放。

### 8.9 `plotloom-deliver`

职责：向飞书或其他通道交付媒体和选择提示。

MVP adapter：nova-lark。

## 9. Adapter Contract

### 9.1 通用 adapter 原则

adapter 不拥有 Plotloom 的业务状态。

adapter 输入输出应尽量是文件路径和少量参数：

```text
input files + options -> output files + metadata summary
```

adapter 返回给 skill 的信息：

- 是否成功
- 输出文件路径
- 关键日志 / 错误摘要
- 可供用户决策的信息

### 9.2 Image Adapter

逻辑接口：

```text
generate_image(
  prompt_text,
  output_path,
  reference_images = [],
  aspect_ratio = optional,
  count = 1
) -> image_paths
```

MVP 实现：Codex imagegen。

### 9.3 Video Adapter

逻辑接口：

```text
generate_video_clip(
  prompt_text,
  output_path,
  reference_images = [],
  duration_hint = "15-20s",
  aspect_ratio = optional
) -> video_path
```

MVP 实现：即梦 CLI。

### 9.4 Stitch Adapter

逻辑接口：

```text
probe_video(video_path) -> media_info
check_compatibility(video_paths) -> ok | issues
normalize(video_path, target_profile) -> normalized_path
concat(video_paths, output_path) -> final_video_path
```

MVP 实现：ffmpeg / ffprobe。

### 9.5 Delivery Adapter

逻辑接口：

```text
deliver_media(
  target,
  media_path,
  message_text
) -> delivery_result
```

MVP 实现：nova-lark / lark-cli。

## 10. Scripts 设计

核心原则：**多写 prompt，少写脚本**。

Plotloom 的主要产能应该来自高质量 `SKILL.md`、references、templates 和 prompt 指令，而不是不断堆 Python 代码。脚本只用于确定性、可验证、重复执行容易出错的工程动作。

适合写成 prompt / skill 的内容：

- series 构思与角色设定。
- episode card。
- video prompt 编写与改写。
- 中英 prompt 转换。
- image/video 生成意图说明。
- 候选审美判断和 rerun 建议。

适合写成 script 的内容：

- `~/plotloom.toml` 读写。
- repo skeleton 创建。
- 路径、slug、版本号计算。
- ffprobe / ffmpeg 包装。
- candidate -> selected 的 copy/backup。
- adapter dry-run / 文件存在性校验。

MVP scripts 放在 skill 目录或 repo-level `scripts/` 中。

建议 scripts：

```text
scripts/
  plotloom_registry.py       # 读写 ~/plotloom.toml
  plotloom_repo.py           # 创建/检查 series repo skeleton
  plotloom_media_probe.py    # ffprobe 包装
  plotloom_stitch.py         # concat / normalize / final.mp4
  plotloom_paths.py          # slug/path/version helper
```

脚本设计规则：

- 只做确定性动作。
- 只向 stdout 输出 JSON 或简洁文本，方便 agent 读取。
- stdout JSON 只是工具返回值，不是 first-party repo artifact。
- 不在 series repo 中持久化 `manifest.json`、`media-info.json`、`repo-state.json`、`workflow-state.json` 等状态/清单文件。
- 不做创作判断。
- 不长期运行。
- 不持有后台状态。

最小错误分类：

```text
missing_input        # 必需文件不存在
adapter_unavailable # 外部 CLI / auth / adapter 不可用
generation_failed   # 图片/视频生成失败
invalid_media       # 媒体探测或兼容检查失败
delivery_failed     # 飞书或其他交付失败
```

错误分类只用于 agent 报告和重试决策，不形成 workflow state。

## 11. 测试策略

MVP 测 contract，不测创作质量。

单元测试：

- `~/plotloom.toml` 解析。
- repo discovery 优先级。
- repo skeleton 创建。
- candidate version 命名：`v001`, `v002`, `v003`。
- selected/final 路径推导。
- ffprobe 输出解析。

集成测试：

- 用 fake-heiress-reboot demo 创建 repo skeleton。
- 用小 fixture mp4 模拟 selected clips。
- stitch 生成 final.mp4。
- dry-run delivery message。

人工验收：

- Codex imagegen 能产出 character-grid.png。
- 即梦 CLI 能产出 clip candidate。
- nova-lark 能把候选/成片发回飞书。

## 12. MVP Demo 验收路径

Demo：`fake-heiress-reboot`。

验收步骤：

1. 从 home 启动 agent。
2. 读取或创建 `~/plotloom.toml`。
3. 创建 `plotloom_repo/fake-heiress-reboot/`。
4. 写入 `series.md` 和 `characters.md`。
5. 使用 Codex imagegen 生成 Ava 的 `character-grid.png`。
6. 生成 EP001 的 `video-prompts.md`。
7. 生成 `video-prompts-en.md`。
8. 使用即梦 CLI 生成 `clip-01/candidates/v001.mp4`。
9. 通过 Feishu 回传 clip-01 候选，请用户接受或重抽。
10. 用户接受后写入 `clip-01/selected.mp4`。
11. 对 clip-02 重复生成/接受流程。
12. 使用 ffprobe 检查 selected clips。
13. 使用 ffmpeg 拼接 `final.mp4`。
14. 通过 Feishu 回传 final.mp4。

MVP 成功标准：用户在飞书收到可播放的 EP001 final.mp4，并且后续可以基于同一 repo 要求“重抽 clip-02”或“继续第二集 prompt”。

## 13. Runtime Adapter 计划

### 13.1 Hermes

优先验证环境。

- 直接使用 Hermes skill registry / profile-local skills。
- scripts 通过本地 Python 执行。
- delivery 使用 `nova-lark`。

### 13.2 Codex

目标：可安装同一组 `SKILL.md` baseline。

- Codex imagegen 作为图片 adapter。
- 保持 core skill 不依赖 Codex 专有工具名。
- Codex adapter 文档只说明如何调用 imagegen 和保存文件。

### 13.3 Claude Code

目标：可读取同一套 skills 和 repo contract。

- 不把 Claude Code 的 Task / Skill tool 写入 core skill。
- 只在 adapter 文档说明安装路径和权限。

### 13.4 OpenCode / OpenClaw

目标：通过 symlink 或 adapter docs 加载同一套 skill 内容。

- 不复制整套 workflow。
- 只处理安装路径和本地命令差异。

## 14. 风险与处理

| 风险 | 影响 | 处理 |
|---|---|---|
| 即梦 CLI 参数或输出不稳定 | video adapter 易碎 | 把调用封装在 adapter script，日志落盘，repo contract 不变 |
| Codex imagegen 运行环境差异 | 图片生成不可复现 | image adapter 只承诺输出文件，不承诺模型一致性 |
| 大媒体文件进 Git | repo 变重 | MVP 不强制 Git；大媒体可仅本地保留 |
| 用户选择状态散落在聊天 | selected 状态不清 | 只有写入 `selected.*` 才算接受状态落盘 |
| 多 agent 同时写 repo | 冲突/覆盖 | MVP 先不做并发控制；后续可加简单 lock 或 git workflow |
| prompt 与 adapter 耦合 | 换模型成本高 | 中文创作源和英文执行版分离，adapter 只做模型适配 |

## 15. 暂不实现

- Web preview。
- UI dashboard。
- 生产进度数据库。
- 多 agent 调度。
- 云端同步服务。
- 自动发布 TikTok / YouTube / Reels。
- 市场数据采集。
- 多模型自动评分。

## 16. 下一步实现顺序

建议按下面顺序落地：

1. 先写 `SKILL.md` / templates / prompt contracts，明确 agent 如何做。
2. `using-plotloom` + registry/repo discovery script。
3. `plotloom-create-series` + repo skeleton/template。
4. `plotloom-write-video-prompts` + `translate-video-prompts-en`。
5. path/version helper + selected copy/backup semantics。
6. fake image/video/delivery adapters，先跑通 repo contract。
7. `plotloom-stitch-clips` + ffmpeg/ffprobe。
8. `plotloom-deliver` + nova-lark dry-run / real send。
9. `plotloom-design-character-grid` + Codex imagegen adapter。
10. `plotloom-draw-video-clip` + 即梦 CLI adapter。
11. fake-heiress-reboot end-to-end demo。

每一步都以 repo artifact 是否正确落盘为验收，不以“流程看起来跑了”为验收。
