# Plotloom MVP PRD（中文版）

> 状态：Draft v0.1  
> 日期：2026-04-28  
> Owner：贵平  
> Agent：Nova

## 1. 一句话定义

Plotloom 是一套 **agent-neutral 的短剧生产 skills 系统**。

它让 Codex / Claude Code / OpenClaw / Hermes 等不同 AI agent 都能接入同一套短剧生产能力，从一个短剧想法推进到第一集视频生产包，而不绑定某个具体 agent runtime、模型、CLI 或平台。

一句话：

```text
Plotloom = 给 agent 用的短剧生产 Superpowers
```

## 2. Plotloom 不是什么

Plotloom 不能变成通用项目管理或工作流平台。

Plotloom 不做：

- 任务看板
- 进度管理
- dashboard
- 通用 workflow runtime
- LangGraph / worker / queue 编排
- 重型 production tracking
- 绑定某个模型或 CLI 的产品
- 传统影视生产文件堆

Plotloom 是短剧生产 skills 系统，不是 PM 系统。

## 3. MVP 目标

MVP 要证明：AI agent 可以使用 Plotloom 创建一部短剧 series repo，并完成第一集视频生产。

MVP 输出：

```text
一个 Plotloom series repo，包含：
- series 级上下文
- 核心角色设定和 character grid
- 第一集 prompt package
- 生成的视频 clip
- 拼接后的第一集 final.mp4
```

MVP 重点是 **第一集成片**。

同时，series 不能被写死。目标集数由用户根据题材和剧本决定，不默认写死 12 或 18 集。

## 4. 核心原则

### 4.1 Skill Graph，不是固定 Pipeline

Plotloom 不是固定 12 步流水线。

Plotloom 是 skill graph：

```text
当前用户意图 + repo 状态 + 可用素材
  -> 选择最合适的 Plotloom skill
  -> 生成或更新必要产物
  -> 建议下一步 skill
```

可以有常见路径，但不能强制唯一线性流程。

典型入口包括：

- 从 0 开始创建新短剧
- 继续已有 series repo
- 复用已有角色
- 重做角色 character grid
- 编写或修改 video prompts
- 为某个 clip 再抽一次视频
- 把已接受 clips 拼成 final.mp4
- 通过飞书或其他通道回传媒体

### 4.2 极简 Artifact

Plotloom 要避免生成不必要的中间文件。

每一集默认只允许这些 prompt artifact：

```text
episode-card.md      # 可选，意图锚点
video-prompts.md     # 中文创作主源
video-prompts-en.md  # 英文模型执行版，需要时生成
```

默认不要增加：

- script.md
- storyboard.md
- director-brief.md
- visual-plan.md
- image-prompts.md
- review.md
- manifest.json
- YAML 文件
- JSON 文件

### 4.3 Markdown + TOML，不用 YAML/JSON

MVP 中，创作内容使用 Markdown。

如果后续确实需要结构化配置，使用 TOML。

核心 repo artifact 不使用 YAML 或 JSON。

### 4.4 用户中文，模型英文

语言策略：

- 用户交互：中文
- series repo 创作文件：默认中文
- `video-prompts.md`：中文创作主源
- `video-prompts-en.md`：英文模型执行版
- 提交给模型：英文
- 短剧台词：默认英文，因为优先面向海外发布

### 4.5 Core 不绑定模型

Plotloom 不能绑定某个模型、CLI 或 API。

可能变化的工具包括：

- 即梦 CLI
- Seedance / 火山 API
- 阿里 API
- 未来的视频/图像模型
- 手动 Web UI 工作流

Plotloom core skills 表达短剧生产意图；tool adapter 再把意图翻译成具体模型、CLI、API 或人工操作流程。

### 4.6 Feishu 在 MVP 内，但不是唯一出口

Feishu 在 MVP 范围内，因为贵平主要通过飞书和 AI chat 交互，生成图片和视频也需要通过飞书回传。

但 Feishu 是 delivery adapter，不是产品中心。

未来其他出口可以包括：

- Codex App
- 本地目录
- Web preview
- 其他 chat 系统

## 5. MVP Series Repo 结构

一个 Plotloom repo 表示一部短剧 / 一个 series。

默认位置：

```text
plotloom_repo/<slug>/
```

最小结构：

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
          v003.png
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

说明：

- `series.md` 和 `characters.md` 是中文创作上下文。
- `assets/cast/` 存放跨集复用的角色资产。
- `assets/scenes/` 存放需要跨集复用的场景资产。
- 每集自己的封面和视频放在 `episodes/epXXX/` 内。
- 大媒体文件可以只保留本地；MVP 不强制 Git 或 GitHub。

## 6. 角色资产规则

核心角色在进入视频生成前，必须有 character grid。

character grid 不是候选九宫格。

它是一张同一角色的设定表 / turnaround sheet，展示同一人物的多个视角，例如：

```text
正面
背面
侧面
3/4 侧面
表情
全身 / 半身变化
关键服装细节
```

路径：

```text
assets/cast/<character-slug>/character-grid.png
```

规则：

- 主角 / 核心角色在视频生成前必须有 `character-grid.png`。
- 路人 / 一次性背景角色不需要 character grid。
- 如果重做角色，要重新生成整张 character grid。
- 不把 grid 里的单格当作候选图。
- MVP 不为 cast asset 创建 `selected.png`。

## 7. 场景和封面资产规则

场景图不是永远必需。

规则：

- 关键常驻场景可以有场景参考图。
- 普通一次性场景可以直接在 video prompt 里描述。
- 场景资产使用单张图片候选，不使用 character grid。

场景目录：

```text
assets/scenes/<scene-slug>/
  candidates/v001.png
  candidates/v002.png
  selected.png
```

封面是 episode 专属资产：

```text
episodes/ep001/images/covers/
  candidates/v001.png
  candidates/v002.png
  candidates/v003.png
  selected.png
```

图片抽卡规则：

- 角色：生成 / 重生成整张 character grid。
- 场景：候选图模式。
- 封面：候选图模式，通常 3 张。

## 8. Episode Artifacts

### 8.1 `episode-card.md` 可选

`episode-card.md` 是可选的意图锚点。

它可以包含：

- 本集 logline
- 本集 hook
- 情绪支付
- 反转
- 结尾钩子
- 核心角色
- 本集在整个 series 中的作用

它不是剧本，不是分镜，不是任务计划。

如果用户意图已经足够清晰，Plotloom 可以跳过它。

### 8.2 `video-prompts.md` 必需

`video-prompts.md` 是视频生成的中文创作主源。

它按 clip 组织中文 prompt。

示例：

```markdown
# EP001 Video Prompts

## Clip 01
中文创作版连续叙事 prompt...

## Clip 02
中文创作版连续叙事 prompt...
```

### 8.3 `video-prompts-en.md` 需要时生成

`video-prompts-en.md` 是英文模型执行版。

当 agent 准备调用或提交给模型时，从 `video-prompts.md` 生成。

示例：

```markdown
# EP001 Video Prompts EN

## Clip 01
English model-ready continuous narrative prompt...

## Clip 02
English model-ready continuous narrative prompt...
```

## 9. Video Prompt 设计

Plotloom 不能把视频模型当成“一镜头一次调用”的 API。

对于 Seedance 这类模型，正确的模型输入单位是连续叙事 prompt task。

原则：

```text
Seedance prompt != shot list
Seedance prompt = continuous narrative timeline
```

一个 prompt task 可以包含多个视觉节拍或镜头切换，但必须保持一条主时间线。

好的模型执行 prompt 应描述：

- 素材引用及其用途
- 连续场景推进
- 时间节拍，例如 0-3s / 4-8s / 9-12s / 13-15s
- 人物入画、离场、遮挡和空间连续性
- 运镜路径和视觉重心
- 台词窗口
- 声音 / 环境音 / 音乐（如需要）
- 适合后续衔接的尾帧

Plotloom skill 内部可以使用类似导演讲戏的方法，但 `director-brief.md` 不是必须落盘 artifact。

## 10. 视频生成与抽卡

### 10.1 Clip 级视频生成

第一集由多个 clip 组成。

规则：

- 每个 clip 约 15-20 秒。
- 每个 clip 对应 `video-prompts.md` / `video-prompts-en.md` 中的一个 prompt section。
- 视频一条一条抽。
- 每条候选生成后，立即回传给用户。
- 用户可以接受、拒绝、继续抽，或要求修改 prompt 后重抽。

目录：

```text
episodes/ep001/videos/clip-01/candidates/v001.mp4
episodes/ep001/videos/clip-01/candidates/v002.mp4
episodes/ep001/videos/clip-01/selected.mp4
```

### 10.2 MVP 必须合成最终视频

MVP 应输出最终第一集视频：

```text
episodes/ep001/videos/final.mp4
```

合成可以是简单 concat，但 Plotloom 必须先验证已选 clip 是否兼容。

合成前，selected clips 必须具有相同或兼容的：

- 画幅比例
- 分辨率
- 帧率（如相关）
- codec / container（如相关）
- 是否有音频、音频格式（如相关）

如果 clips 不兼容，agent 必须先归一化，或停下来报告问题。

这不是完整剪辑系统，只是把已接受 clips 拼成一集可播放视频的最小能力。

## 11. Delivery

MVP delivery 必须支持 Feishu。

行为：

- 每条视频候选生成后立即回传。
- 图片候选可以批量回传。
- 回传消息必须标注 episode、clip、version，以及需要用户做什么决定。

示例：

```text
EP001 / Clip 01 / v002
请选择：接受 / 继续抽 / 修改 prompt 后重抽
```

Feishu 不是进度系统，只是媒体回传和反馈通道。

## 12. 入口行为

Plotloom 启动时：

- 如果当前目录有 `series.md`，视为当前 Plotloom repo，并继续。
- 如果没有 `series.md`，询问是否创建新的 Plotloom repo。
- 如果用户只是要一个独立 video prompt，不强制创建 repo。

一个新 repo 表示一部短剧 / 一个 series。

## 13. MVP Skill Set

MVP 聚焦少量可组合 skills。

建议 skills：

```text
using-plotloom
plotloom-create-series
plotloom-design-character-grid
plotloom-write-video-prompts
plotloom-translate-video-prompts-en
plotloom-draw-image
plotloom-draw-video-clip
plotloom-deliver
plotloom-stitch-clips
```

后续可加：

```text
plotloom-market-sense
plotloom-cover-click-review
plotloom-series-continuation
plotloom-character-refresh
plotloom-model-adapter-optimizer
```

商业判断 / market-sense 不进 MVP。

## 14. 不在 MVP 范围内

以下明确不在 MVP：

- 真实平台市场数据调研
- 短剧商业评分 gate
- dashboard
- 任务追踪
- 固定 workflow engine
- 自动多模型 benchmark
- 完整音频 / 音乐 pipeline
- 平台发布自动化
- 长季完整剧本生成
- 强制 Git 或 GitHub 集成
- YAML / JSON artifact schema

## 15. MVP 成功标准

Plotloom MVP 成功的标准：

1. 用户可以创建或继续一个 Plotloom series repo。
2. 核心角色拥有可复用的 `character-grid.png`。
3. 第一集拥有 `video-prompts.md` 和 `video-prompts-en.md`。
4. agent 可以按 clip 一条一条生成视频候选。
5. 每条候选可以回传给用户，尤其是通过 Feishu。
6. 用户可以接受 / 拒绝 / 继续抽 / 要求回炉 clip 候选。
7. 已接受 clips 可以拼成 `episodes/ep001/videos/final.mp4`。
8. 系统不会变成 PM 工具、dashboard 或过度设计的 artifact protocol。

## 16. 当前暂不解决的问题

这些留到后续，不作为 MVP blocker：

- 第一个具体 image/video model adapter 选哪个？
- 是否为媒体-heavy repo 支持 Git / LFS？
- 是否做 Codex App preview adapter？
- production loop 跑通后是否加 market-sense？
- 如何把 skills 分发到 Codex / Claude Code / OpenClaw / Hermes？
