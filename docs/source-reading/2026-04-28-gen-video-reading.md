---
title: gen-video 源码/Prompt 解读：一个面向模型分流的 AI 视频导演 Skill
created: 2026-04-28 01:49 CST
agent: nova
material_type: source-reading
status: raw
tags:
  - source-reading
  - ai-video
  - codex-skill
  - video-director
  - skill-pack
source:
  repo: https://github.com/lusipad/gen-video
  local_path: /Users/wangguiping/workspace/github/research/gen-video
  commit: 0d8a8c7e1caa8759ddc62aeec4491d66fbc4c7b1
  commit_date: 2026-04-09 08:38:13 +0800
  commit_subject: "Turn gen-video into a learning video director with reviewable PDCA loops"
related_topics:
  - dramaclaw
  - videoclaw
  - AI 视频导演
---

# gen-video 源码/Prompt 解读：一个面向模型分流的 AI 视频导演 Skill

## 结论先行

`gen-video` 不是短剧生产流水线，也不是 Seedance 专用 prompt pack。它更像一个“AI 视频导演 skill”：先判断视频任务应该怎么被做出来，再选择模型栈、平台、执行模式，并把判断落成剧本、分镜、素材清单、提示词和执行操作包。

它对 dramaclaw 的价值不在“资产/分镜 schema”，而在 **导演层决策**：

- 先锁定模型栈，而不是直接写 prompt。
- 区分模型栈和执行平台。
- 根据输入素材和控制目标选择工作流。
- 在 native / hybrid / manual 三种模式间分流。
- 用 PDCA、benchmark、knowledge layer 持续更新导演判断。

如果 `shotcine` 是短剧生产的“中段 prompt engine”，那 `gen-video` 更像“前段导演判断与模型路由层”。

## 仓库基本情况

- 仓库：`lusipad/gen-video`
- 本地路径：`/Users/wangguiping/workspace/github/research/gen-video`
- 当前 commit：`0d8a8c7e1caa8759ddc62aeec4491d66fbc4c7b1`
- 最近提交：`Turn gen-video into a learning video director with reviewable PDCA loops`
- 体量：约 `1.2M`，`120` 个 git 文件
- 形态：Codex skill + knowledge base + model profiles + modes + benchmarks

关键入口：

```text
.codex/skills/gen-video/SKILL.md
.codex/skills/gen-video/core/output-contract.md
.codex/skills/gen-video/core/pdca-loop.md
.codex/skills/gen-video/references/workflow-decision-tree.md
.codex/skills/gen-video/modes/native.md
.codex/skills/gen-video/modes/hybrid.md
.codex/skills/gen-video/modes/manual.md
.codex/skills/gen-video/profiles/*.md
.codex/skills/gen-video/knowledge/**
.codex/skills/gen-video/benchmarks/**
examples/**
```

## 核心定位：不是生成器，而是导演判断

`SKILL.md` 开头就说：

> 这个技能的核心不是“代替模型直接生成视频”，而是做 AI 视频导演判断。

它负责：

- 判断一条视频为什么成立。
- 判断一条视频该怎么被做出来。
- 决定该用什么模型、什么平台、什么执行顺序。
- 把这些判断编排成可执行的生产方案。

输出仍然是剧本、分镜、素材清单、提示词和执行操作包，但这些只是导演判断的落地形态。

这和 `shotcine` 的差异很大：`shotcine` 进入时已经默认 Seedream / Seedance；`gen-video` 则先问“到底该不该用这个模型、该走哪条工作流”。

## 新架构：一个导演后台 + 四个运行层

`gen-video` 的结构被拆成：

```text
knowledge/   原始来源、wiki、维护 schema、更新日志
core/        稳定规则：输出契约、真实性锚点、质量门
profiles/    模型 / 平台能力档案
modes/       native / hybrid / manual 三种执行模式
benchmarks/  样题、复核模板、评测模板、Check -> Act
```

它强调：

- 原始来源留在 `knowledge/raw`。
- 可更新判断留在 `knowledge/wiki`。
- 稳定规则留在 `core`。
- 变化快的模型能力留在 `profiles`。
- 先判断模型原生能力，再决定 skill 接管多少。
- 默认优先 `native` 或 `hybrid`，只有高控制度需求才走 `manual`。

这点对当前用户的“AI 已经大幅替代 coding，重点在方案、验收与流程能力”非常契合：agent 不应该机械接管所有细节，而应该根据模型能力决定介入深度。

## 硬门：开场先选模型

`SKILL.md` 设了一个非常强的模型选择门：

- 如果用户已经指定模型栈，不重复追问。
- 如果用户没有指定模型栈，默认先用一句简短问题让用户选择。
- 如果用户说不确定，默认推荐 `Veo 3.1 + Nano Banana 2`。
- 只有用户明确表示“直接开始 / 不用问 / 你定就行”才跳过。

候选项包括：

1. Veo 3.1 + Nano Banana 2
2. Veo 3.1 + Nano Banana Pro
3. Seedance 风格分镜输出
4. 自定义模型栈

这条规则很有价值。视频 prompt 不是通用文本，不同模型对结构、长度、素材引用、首尾帧、ingredients、参考视频的理解差异很大。先写 prompt 再问模型，通常会导致返工。

对 dramaclaw 来说，如果第一版已经限定 imagegen2 + 即梦 CLI / Seedance，可以不每次问模型；但仍应在 `episode.yaml` 或 run config 中显式记录模型栈。

## 模型分流与平台分流

`gen-video` 明确区分“模型栈”和“执行平台”：

- 如果只是要模型提示词包，按 Nano Banana / Veo / Seedance 分流。
- 如果明确在 Google Flow 中使用，则输出不是单纯提示词，而应包含素材图、镜头、存帧、回灌、Scenebuilder 拼接等操作包。

它还区分多种 Veo / Seedance 工作流：

- `Veo image-to-video`
- `Veo first-and-last-frame`
- `Veo ingredients-to-video`
- `Veo extend video`
- `Seedance 参考视频`

并特别提醒：不要把“参考视频”误写进 `Veo first-and-last-frame`；首尾帧工作流只负责用两张图约束起点和终点。

这类规则是“视频导演 skill”最应该沉淀的东西：不是 prompt 文采，而是避免选错工作流。

## Workflow decision tree

`references/workflow-decision-tree.md` 的核心判断方式是：不要先看模型名，先看任务形态。

先看用户手里有什么素材：

| 输入素材 | 优先路线 |
|---|---|
| 只有文字 | Veo 文本起稿 / Seedance 纯文本分镜 |
| 一张关键图 | image-to-video 或先出图再做视频 |
| 首帧图 + 尾帧图 | first-and-last-frame |
| 多张图片素材 | ingredients-to-video 或 Seedance 图片参考分镜 |
| 已有视频 | extend video 或 Seedance 视频编辑 |
| 参考视频但不续写 | Seedance 参考视频 |

再看用户真正想控制什么：

- 控制起点和终点状态
- 控制中间运动过程
- 控制角色和场景一致性
- 参考另一段视频的感觉
- 把已有视频往后接
- 改掉已有视频的一部分剧情

这对 dramaclaw 的启发是：短剧生产虽然 MVP 可能先固定一条链路，但后续一定会遇到不同输入形态：只有剧本、已有角色图、已有视频片段、已有爆款样片、想续拍、想改局部。工作流选择树可以提前抽成独立 skill/reference。

## native / hybrid / manual 三种模式

`gen-video` 的 mode 设计很值得吸收：

| 模式 | 含义 | 适用情况 |
|---|---|---|
| native | 模型原生能力已经足够，skill 只补目标、锚点、交付整理 | 平台/模型可以直接理解复杂任务 |
| hybrid | 模型先做主生成，skill 补连续性、真实性和执行结构 | 大多数实用视频任务 |
| manual | skill 深度拆解，手工控制镜头、素材、提示词 | 高控制度、强一致性、复杂短剧生产 |

`SKILL.md` 默认原则是：不要默认 `manual`。当模型原生能力明显足够时，skill 应后退。

这点对当前 dramaclaw 讨论也有启发：如果短剧链路完全自己拆，控制力强但成本高；如果平台原生能力越来越强，skill 应该从“替模型做所有事”转向“定义目标、验收、修正、包装”。

## 输出契约与 PDCA

`core/output-contract.md` 和 `core/pdca-loop.md` 虽然不是完整生产线代码，但体现了这个项目的核心思想：视频生成不是一次性 prompt，而是可复核、可学习、可回写的流程。

仓库里有：

```text
benchmarks/video-evidence.md
benchmarks/video-review.md
benchmarks/video-review-actions.md
knowledge/log.md
knowledge/nightly-review.md
knowledge/video-learning.md
knowledge/writeback-queue.md
```

这说明它把 `Check -> Act` 也纳入 skill 结构：产出视频后要复核，复核结果要形成行动队列，行动队列再回写知识层。

这对 dramaclaw 未来很关键。短剧生成必然会有大量失败：角色不一致、动作不连贯、对白拥挤、画幅错误、镜头漂移、字幕不匹配。没有 PDCA，skill 会一直靠人工经验重试。

## 可直接复用的设计

1. **先做模型/平台选择，不直接写 prompt**
2. **模型栈和执行平台分离**
3. **输入素材驱动 workflow decision tree**
4. **native / hybrid / manual 分流**
5. **profile 管理模型能力，而不是写死在主 skill**
6. **knowledge layer 区分 raw source、wiki、log、suggestions**
7. **benchmark / review / action queue 形成 PDCA**
8. **输出不只是 prompt，而是执行操作包**

## 需要改造的地方

用于 dramaclaw 时，`gen-video` 还缺：

1. **短剧结构模型**
   - 没有 episode.yaml、角色资产、场次、镜头等专门 schema。

2. **生产执行层**
   - 不调用具体图像/视频生成工具。
   - 不负责 ffmpeg 合成。

3. **短剧投流节奏**
   - 它偏通用视频导演，不专门处理 30–45 秒短剧的钩子、反转、爽点、付费点。

4. **多集连续性管理**
   - 有 longform 示例，但不是一个完整多集 production pipeline。

## 不适合直接继承的部分

- 不建议把 dramaclaw 做成以“模型选择提问”为主入口的通用视频导演；当前目标更明确，是短剧生产 skill pack。
- 不建议第一版就引入 nightly review / knowledge automation 全套后台，会过重。
- 不建议把 `gen-video` 的默认模型栈当成 dramaclaw 默认，因为 dramaclaw 的短期链路是 imagegen2 / 即梦 CLI / Seedance 方向。

## 对 dramaclaw 的启发

`gen-video` 可以作为 dramaclaw 的“导演层参考”：

```text
输入任务
  ↓
明确模型栈 / 平台 / 执行环境
  ↓
选择 native / hybrid / manual
  ↓
决定是否需要资产拆解、首尾帧、ingredients、参考视频、extend
  ↓
生成对应执行包
  ↓
复核结果并回写经验
```

dramaclaw MVP 可以先固定一条路线，但要在设计里预留：

- `model_stack`
- `execution_platform`
- `workflow_mode`
- `input_materials`
- `review_result`
- `rerun_plan`

这样后续从单一路线扩展到多模型/多平台，不会推翻整体结构。

## 总评

`gen-video` 不是 dramaclaw 的直接骨架，但它提供了很好的“视频导演层”设计样本。

它最值得借鉴的是：不要把 video skill 降级成 prompt 模板库；真正有价值的是判断视频为什么成立、怎么做、用哪个模型、如何控制，以及如何通过 review 继续学习。

如果说 `shotcine` 适合作为 dramaclaw 的分镜/prompt 中段样板，`gen-video` 就适合作为前段导演判断和后段 PDCA 的参考。
