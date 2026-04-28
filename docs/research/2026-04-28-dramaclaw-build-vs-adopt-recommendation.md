---
title: dramaclaw 路线建议：自研 Skill Pack，而不是直接采用现成项目
created: 2026-04-28 02:18 CST
agent: nova
material_type: decision-note
status: raw
tags:
  - dramaclaw
  - short-drama
  - skill-pack
  - ai-video
  - architecture-decision
source:
  - raw/agents/nova/source-reading/2026-04-27-seedance2-storyboard-generator-reading.md
  - raw/agents/nova/source-reading/2026-04-27-seedance-prompt-skill-reading.md
  - raw/agents/nova/source-reading/2026-04-27-awesome-gpt-image-2-reading.md
  - raw/agents/nova/source-reading/2026-04-28-shotcine-reading.md
  - raw/agents/nova/source-reading/2026-04-28-seedance-prompt-production-skills-reading.md
  - raw/agents/nova/source-reading/2026-04-28-gen-video-reading.md
  - raw/agents/nova/research/2026-04-28-autoflow-architecture-research.md
related_topics:
  - videoclaw
  - dramaclaw
  - Seedance
  - imagegen2
  - AI 短剧生产流水线
---

# dramaclaw 路线建议：自研 Skill Pack，而不是直接采用现成项目

## 一句话结论

建议 **自研一套 dramaclaw skill pack**，但不要从零发明；把这轮调研到的项目拆成“参考件库”，吸收各自成熟的局部设计。

更具体一点：

```text
dramaclaw = 自研 skill-first 短剧生产包
  + shotcine 的资产 / 分镜 / prompt artifact 契约
  + seedance_prompt 的 production skills 拆分和 Seedance 提交流程经验
  + gen-video 的导演层判断、模型/工作流分流、PDCA review
  + autoflow 的 Gate / QC / 回炉 / 成本质量指标思想
```

不推荐直接使用某个现成项目作为主线，也不推荐第一版上来就做平台。

## 背景

当前目标不是做一个泛视频工具，也不是做完整 AIGC 平台，而是围绕短剧生产做一套可被 agent 调用的 skill pack。

已知边界：

- `videoclaw` 的本质是一组 video production skills，不是 CLI 产品。
- `dramaclaw` 应延续 skill-first，而不是先做重 CLI / 重平台。
- 第一版目标更接近：服务 5 条 30–45 秒短剧测试，跑通核心链路。
- 输入核心应是类似 `episode.yaml` 的结构化剧集/短剧描述。
- 主链路倾向：imagegen2 / GPT Image 2 方向出图，Seedance / 即梦方向出视频，ffmpeg 合成。
- 现阶段先学习 GitHub prior art，再决定自建方式。

这轮已经读过几个关键项目：

| 项目 | 类型 | 对 dramaclaw 的价值 |
|---|---|---|
| `shotcine` | 短剧分镜 / prompt skill 原型 | 最接近短剧 skill 中段，可借 artifact 契约 |
| `seedance_prompt` | 生产流水线 + prompt/skill 库 | 可借 production skills 拆分和 Seedance 提交流程 |
| `gen-video` | AI 视频导演 skill | 可借模型/工作流分流、PDCA review |
| `autoflow` | 工业化 AIGC 短剧平台 | 可借 Gate/QC/回炉/成本质量指标，不适合直接用 |
| `Seedance2-Storyboard-Generator` | Seedance 分镜 skill | 可借四幕/分镜组织思路 |
| `seedance-prompt-skill` | Seedance prompt 规则库 | 可借底层 prompt 规则 |
| `awesome-gpt-image-2` | GPT Image 2 prompt 语料库 | 可借图像 prompt 表达与分类语料 |

## 为什么不直接用现成项目

### 1. 没有项目覆盖完整 dramaclaw 目标

我们要的不是单点 prompt 工具，而是一条短剧生产链：

```text
剧本 / episode 输入
  → 资产定义
  → 分镜规划
  → 图片提示词
  → 图片生成
  → 视频提示词
  → 视频生成
  → 素材管理
  → 合成
  → 字幕 / 封面 / manifest
  → 验收 / 回炉
```

现成项目大多只覆盖其中一段：

- `shotcine` 覆盖：剧本/分镜 → 资产 → shots → prompts → CSV。
- `seedance_prompt` 覆盖：学习、导演讲戏、Seedance prompt、提交链的一部分。
- `gen-video` 覆盖：视频任务形态判断、模型路由、执行包、review 思路。
- `autoflow` 覆盖：平台级生产线，但太重，且不是 skill-first。

没有一个项目能直接作为 dramaclaw 主体。

### 2. 直接 fork 会继承错误的产品形态

dramaclaw 应该优先是 skill pack。现有项目的产品形态并不完全匹配：

| 项目 | 直接 fork 的问题 |
|---|---|
| `shotcine` | 太窄，只到分镜/prompt/export，不负责真实生成和成片 |
| `seedance_prompt` | 太重，脚本/配置/目录耦合强，prompt library 体量大 |
| `gen-video` | 太泛，是通用视频导演，不是短剧生产线 |
| `autoflow` | 平台化过重，包含前后端、DB、LangGraph、worker、Gate 后台 |

如果直接采用其中任何一个，都会被它的原始目标牵引，而不是服务 dramaclaw 的 MVP。

### 3. 我们真正需要的是统一 artifact 契约

短剧生产的核心难点不是“写一个很长的 prompt”，而是让多阶段产物能稳定传递、审核、重跑。

也就是说，dramaclaw 的核心资产应该是：

```text
episode.yaml
assets.json / assets.yaml
shots.json / shots.yaml
storyboard.md
image_prompts.json
video_prompts.json
generation_manifest.json
assembly_manifest.json
review_report.md / review.json
```

现成项目各有自己的文件体系，但没有一个完全符合我们的链路。因此更合理的是自定义 dramaclaw 契约，再吸收外部项目的成熟片段。

## 推荐路线：自研，但采用“参考件库”策略

### 总体判断

推荐路线不是“完全自造”，也不是“直接采用现成项目”，而是：

```text
自己定义 dramaclaw 的主 artifact 和 skill 边界；
外部项目只作为局部设计来源；
第一版保持轻量、可跑通、可验收；
等链路稳定后再平台化。
```

这和当前目标更匹配：先跑通 5 条短剧，而不是提前做大系统。

## 各项目应该怎么借鉴

### 1. shotcine：借中段 artifact 契约

`shotcine` 是最接近短剧 skill pack 的项目。它最值得借的是：

```text
assets.json
shots.json
storyboard.md
prompts.json
groups.json
EPxx_grouped_prompts.csv
video_prompts.txt
```

核心思想：

- `assets.json` 管人物、场景、道具。
- `shots.json` 是分镜结构真源。
- `storyboard.md` 是人类审核视图。
- `prompts.json` 是每镜图片/视频提示词。
- CSV / txt 是面向具体工具的 export adapter。

特别值得继承的规则：

- `asset_id` 和 `name` 分离。
- 提示词开头用 `@asset_id` 锚定资产，正文使用真实名称。
- 图片 prompt 用自然短句，不加字段壳。
- 视频 prompt 用 `【景别】/【空间关系】/【画面动作】/【光影影调】/【台词】` 等字段化结构。
- 单镜默认不超过 15 秒，爆点镜 3–7 秒。
- 长台词拆镜头组，不塞进单镜。
- 9:16 竖屏优先中近景、近景、特写。

但 `shotcine` 不能直接当 dramaclaw，因为它缺：

- 图片生成 hook。
- 视频生成 hook。
- 素材文件管理。
- 成片合成。
- 字幕 / 封面 / manifest。
- 验收 / 回炉。

结论：`shotcine` 是 **dramaclaw 中段协议样板**，不是完整方案。

### 2. seedance_prompt：借 production skills 拆分

`seedance_prompt` 的价值在于 production skill 体系和 Seedance 端到端经验。

可借的 skill 拆分：

```text
script-analysis-review-skill
video-script-reconstruction-skill
seedance-storyboard-skill
seedance-prompt-review-skill
```

这说明短剧生产不应该只有一个大 skill，而应该拆成多个职责清晰的子 skill：

```text
script-analysis
script-rewrite / episode-planning
asset-prompt-generation
storyboard-generation
seedance-prompt-generation
prompt-review
seedance-submit
```

可借的生产链：

```text
视频 -> 剧本经验 / 分镜经验 / Seedance 模板库
剧本 -> 导演讲戏本 / 服化道 / 分镜
分镜 -> 参考图 -> TOS -> Seedance 视频 API
```

但 dramaclaw 第一版不应该照搬它的全套脚本，因为：

- 仓库体量大。
- 配置、目录、本地脚本耦合强。
- prompt library 会带来上下文和维护负担。
- 反向学习链路不是 MVP 必需。

结论：`seedance_prompt` 是 **production skill 拆分参考**，不是初始代码骨架。

### 3. gen-video：借导演层与模型路由

`gen-video` 的核心价值是“视频导演判断”，而不是短剧流水线。

可借思想：

- 先确定模型栈，不急着写 prompt。
- 区分模型栈和执行平台。
- 根据输入素材选择工作流。
- 区分 native / hybrid / manual 三种模式。
- 把 review 和 PDCA 放进 skill，而不是只做一次性生成。

它的 workflow decision tree 很适合作为 dramaclaw 后续扩展参考：

| 输入素材 | 可能路线 |
|---|---|
| 只有文字 | 文本分镜 / 纯文本视频 prompt |
| 一张关键图 | image-to-video |
| 首帧 + 尾帧 | first-and-last-frame |
| 多张角色/场景/道具图 | ingredients / reference image video |
| 已有视频 | extend / edit / reference video |
| 参考样片 | 借运镜、节奏、动作，不一定续写 |

第一版 dramaclaw 可以先固定一条路线，但 artifact 中应预留：

```yaml
model_stack:
  image: gpt-image-2 / imagegen2
  video: seedance / jimeng
execution_platform:
  image: cli-or-api
  video: cli-or-api
workflow_mode: manual
input_materials:
  script: ...
  reference_images: ...
  reference_videos: ...
```

结论：`gen-video` 是 **导演层和模型分流参考**。

### 4. autoflow：借 Gate / QC / 回炉思想

`autoflow` 太重，不适合直接用。但它给了非常重要的工程方向：

- ProjectGraph / EpisodeGraph 分离。
- Supervisor 只做确定性路由，不用 LLM 控制一切。
- Worker agent 负责语义工作。
- Gate 让人类只在关键节点介入。
- QC 失败回到明确源节点。
- 回炉要定位节点 + 对象锚点。
- 成本、质量、吞吐是一等指标。

这些思想可以被轻量化成 dramaclaw 的本地 skill 设计。

例如第一版不需要 LangGraph，但可以有：

```text
assets_gate
storyboard_gate
image_qc
video_qc
final_qc
rerun_plan
```

回炉不要只写“重跑视频”，而应结构化：

```yaml
failure:
  episode_id: ep01
  shot_id: shot_004
  asset_id: character_hero
  media_id: video_004_v1
  reason: 角色服装与前镜不一致
  severity: blocker
rerun:
  from_stage: video_prompt
  target: shot_004
  preserve:
    - assets
    - approved_images
```

结论：`autoflow` 是 **未来平台化和验收闭环参考**，不是 MVP 技术路线。

## dramaclaw 应该是什么

### 产品形态

建议定义为：

> dramaclaw 是一个短剧生产 skill pack，用结构化 episode 输入驱动资产、分镜、图片生成、视频生成、合成与验收；CLI 只作为 skill 调用的薄工具层，不作为第一性产品。

这句话里最关键的是：

- `skill pack` 是主体。
- `episode 输入` 是核心真源。
- `artifact 契约` 是系统边界。
- `CLI` 是工具，不是产品本体。

### 第一版能力边界

第一版只需要服务 5 条 30–45 秒短剧测试，不要追求平台化。

建议第一版包括：

```text
1. episode.yaml 输入规范
2. assets.json / yaml 生成
3. shots.json / yaml 生成
4. storyboard.md 人工审核视图
5. image_prompts.json 生成
6. imagegen2 / GPT Image 2 出图 hook
7. video_prompts.json 生成
8. Seedance / 即梦 出视频 hook
9. ffmpeg 合成
10. final package：final.mp4 / cover / subtitles / manifest
11. review checklist
12. rerun plan 最小回炉描述
```

不建议第一版做：

- Web UI。
- 多用户权限。
- 数据库。
- LangGraph / Temporal。
- 大规模 prompt library。
- 自动从视频反向学习。
- 复杂 RAG / Reflection。
- 多模型全量兼容。

## 推荐目录结构

如果新建 `dramaclaw`，建议先按 skill pack 组织，而不是平台工程组织：

```text
dramaclaw/
  README.md
  skills/
    dramaclaw-episode-create/
      SKILL.md
      references/
        episode-contract.md
        short-drama-rhythm.md
        acceptance-checklist.md
    dramaclaw-assets/
      SKILL.md
      references/
        assets-contract.md
        imagegen2-prompt-style.md
    dramaclaw-storyboard/
      SKILL.md
      references/
        shots-contract.md
        shot-splitting-rules.md
    dramaclaw-image-prompts/
      SKILL.md
      references/
        image-prompt-template.md
    dramaclaw-video-prompts/
      SKILL.md
      references/
        seedance-prompt-template.md
    dramaclaw-generate/
      SKILL.md
      references/
        generation-manifest.md
    dramaclaw-assemble/
      SKILL.md
      references/
        assembly-manifest.md
    dramaclaw-review/
      SKILL.md
      references/
        qc-checklist.md
        rerun-plan.md
  schemas/
    episode.schema.json
    assets.schema.json
    shots.schema.json
    image_prompts.schema.json
    video_prompts.schema.json
    generation_manifest.schema.json
    review.schema.json
  tools/
    dramaclaw.py
    validate_episode.py
    render_storyboard.py
    export_prompts.py
    assemble_video.py
  examples/
    ep01/
      episode.yaml
      expected_outputs/
```

这里的 `tools/` 只做确定性辅助：validate、render、export、assemble。不要让 CLI 承担产品主入口。

## 推荐核心 artifact

### 1. episode.yaml

`episode.yaml` 是用户/agent 输入真源。

建议包含：

```yaml
episode_id: ep01
title: 反击从辞职开始
duration_target_sec: 45
aspect_ratio: "9:16"
language: zh-CN
style:
  genre: 都市爽剧
  visual: 现实短剧感
  pacing: 快节奏，高冲突
characters:
  - id: hero
    name: 林小满
    role: 女主
    description: 28岁，职场白领，克制但有反击欲
  - id: boss
    name: 周启明
    role: 反派上司
premise: 女主被上司公开羞辱后，用录音反击并当场辞职。
beats:
  - id: b01
    function: hook
    content: 上司在会议室当众羞辱女主。
  - id: b02
    function: escalation
    content: 女主沉默忍受，同事冷眼旁观。
  - id: b03
    function: reversal
    content: 女主播放录音，揭穿上司甩锅。
  - id: b04
    function: payoff
    content: 女主辞职离场，上司失控。
constraints:
  must_include:
    - 录音笔特写
    - 女主最后一句台词：这个锅，我不背了。
  avoid:
    - 夸张玄幻特效
    - 复杂多人调度
```

### 2. assets.json

资产层负责角色、场景、道具的一致性。

```json
{
  "characters": [
    {
      "asset_id": "char_hero_01",
      "name": "林小满",
      "type": "character",
      "visual_baseline": "28岁女性，黑色低马尾，白衬衫，深灰西装外套",
      "notes": "克制、疲惫、眼神逐渐坚定"
    }
  ],
  "locations": [
    {
      "asset_id": "loc_meeting_room_01",
      "name": "玻璃会议室",
      "visual_baseline": "现代办公室会议室，长桌，玻璃墙，冷白顶光"
    }
  ],
  "props": [
    {
      "asset_id": "prop_recorder_01",
      "name": "黑色录音笔",
      "visual_baseline": "小型黑色录音笔，红色指示灯"
    }
  ]
}
```

### 3. shots.json

分镜是真正的结构骨架。

```json
{
  "episode_id": "ep01",
  "shots": [
    {
      "shot_id": "shot_001",
      "start_sec": 0,
      "end_sec": 4,
      "shot_type": "dialogue_conflict",
      "beat_id": "b01",
      "assets": ["char_hero_01", "char_boss_01", "loc_meeting_room_01"],
      "shot_size": "中近景",
      "camera_motion": "缓慢推进",
      "visual_action": "周启明站在会议桌前俯视林小满，林小满坐在画面右侧沉默抬眼",
      "dialogue": [
        {"speaker": "周启明", "text": "这个项目出问题，就是你一个人的责任。"}
      ],
      "dramatic_function": "公开羞辱，建立冲突"
    }
  ]
}
```

### 4. prompts

可以拆成：

```text
image_prompts.json
video_prompts.json
```

图片 prompt 用自然短句，视频 prompt 用字段化结构。

### 5. generation_manifest.json

这是 dramaclaw 比 `shotcine` 必须多出来的部分。

```json
{
  "run_id": "20260428-ep01-v1",
  "episode_id": "ep01",
  "image_tasks": [
    {
      "shot_id": "shot_001",
      "provider": "imagegen2",
      "prompt_file": "image_prompts.json",
      "status": "succeeded",
      "output": "media/images/shot_001.png"
    }
  ],
  "video_tasks": [
    {
      "shot_id": "shot_001",
      "provider": "seedance",
      "input_image": "media/images/shot_001.png",
      "status": "succeeded",
      "output": "media/videos/shot_001.mp4"
    }
  ]
}
```

这个文件负责让后续排查、合成、回炉有据可查。

### 6. review_report / rerun_plan

验收不应该停留在“看起来不行”。建议结构化：

```yaml
review_result: fail
issues:
  - id: issue_001
    severity: blocker
    stage: video
    shot_id: shot_003
    category: character_consistency
    description: 女主外套颜色从深灰变成浅蓝，和前后镜不一致。
    suggested_fix: 保留已通过图片，重写 video prompt，强调深灰西装外套不变。
rerun_plan:
  from_stage: video_prompt
  targets:
    - shot_003
  preserve:
    - assets.json
    - shots.json
    - media/images/shot_003.png
```

## MVP 工作流建议

第一版可以按下面这条链路做：

```text
Step 1. 用户/agent 写 episode.yaml
Step 2. dramaclaw-episode-create 检查短剧结构：hook / escalation / reversal / payoff
Step 3. dramaclaw-assets 生成 assets.json
Step 4. dramaclaw-storyboard 生成 shots.json + storyboard.md
Step 5. 人工快速 review storyboard.md
Step 6. dramaclaw-image-prompts 生成 image_prompts.json
Step 7. imagegen2 生成关键图 / 首帧图
Step 8. dramaclaw-video-prompts 生成 video_prompts.json
Step 9. Seedance / 即梦生成视频片段
Step 10. dramaclaw-assemble 用 ffmpeg 合成 final.mp4
Step 11. dramaclaw-review 生成 review_report
Step 12. 如失败，生成 rerun_plan，只重跑必要片段
```

其中人类介入点只保留两个：

```text
storyboard gate：分镜是否值得生成
final gate：成片是否可接受
```

如果第一版还不稳定，可以临时加一个：

```text
image gate：关键图是否足够稳定
```

## 为什么第一版不要做平台

平台化要解决的是多用户、多项目、多并发、成本统计、队列、权限、审核后台、任务可观测性。

但当前更关键的是证明：

```text
一条短剧能不能从 episode.yaml 稳定走到 final.mp4？
失败后能不能定位到 shot / asset / prompt 并局部重跑？
```

如果这两个问题没跑通，平台只会放大复杂度。

所以推荐分阶段：

### Phase 0：纸面协议

产出：

- `episode.yaml` contract
- `assets/shots/prompts/manifest/review` schema
- 1 个手写 example

验收：不用真实生成，也能看出 artifact 是否连贯。

### Phase 1：本地 skill MVP

产出：

- 一组 Claude Code / Hermes skills
- 少量 Python 工具
- 5 条短剧样例
- 能从 episode 到 final.mp4

验收：至少 3/5 条能端到端生成可观看版本。

### Phase 2：执行稳定化

产出：

- rerun plan
- review checklist
- provider adapter
- 失败样本库

验收：常见失败可以局部重跑，不需要整条重做。

### Phase 3：再考虑平台化

只有当出现这些信号时，才考虑吸收 `autoflow` 式架构：

- 多项目并发。
- 生成任务量大。
- 需要多人审核。
- 需要成本统计。
- 需要后台追踪每个节点。
- 需要自动队列和 worker。

## Build vs Adopt 决策矩阵

| 维度 | 直接采用现成项目 | 自研 dramaclaw skill pack |
|---|---|---|
| 与目标匹配 | 中低，各项目只覆盖部分链路 | 高，可按短剧 MVP 定义 |
| 初始速度 | 看似快，实际适配成本高 | 中等，但边界清楚 |
| 长期可控性 | 低，会继承项目原始形态 | 高，artifact 自己定义 |
| skill-first | 不稳定，有的偏平台/脚本 | 高，天然按 skill 组织 |
| 生成链路 | 需要补大量 adapter | 可从一开始按链路设计 |
| 验收/回炉 | 多数缺失或过重 | 可做轻量闭环 |
| 维护成本 | 容易被外部结构牵引 | 可控，但需要自己设计 |
| 适合当前 MVP | 不适合直接用 | 适合 |

结论：**自研胜出，但必须借鉴现成项目，避免重新踩坑。**

## 最小可行设计原则

### 1. Artifact-first

先定义文件契约，再写 skill 和工具。

如果没有稳定 artifact，agent 会每轮靠上下文猜，无法续跑、审核、回炉。

### 2. Skill-first

skill 是产品本体，CLI 是确定性辅助。

```text
Skill：负责语义任务、流程判断、prompt 生成、review
Tool：负责 validate、render、export、ffmpeg、manifest 更新
```

### 3. Human gate 极少但明确

第一版不要每一步都问人，只保留关键 gate：

- storyboard gate
- final gate
- 必要时 image gate

### 4. Review 可结构化

验收结果必须能变成 rerun plan，而不是聊天式评价。

### 5. Provider adapter 可替换

不要把 imagegen2 / Seedance / 即梦 CLI 写死在上层 artifact 里。

上层只记录：

```yaml
provider: seedance
adapter: jimeng-cli
model: seedance-2.0
```

### 6. 不提前平台化

先跑通单机、本地、少量样例。平台化等任务量证明之后再做。

## 建议下一步

如果继续推进，我建议下一步不是直接写全部代码，而是先写 dramaclaw 的第一份设计文档：

```text
Dramaclaw MVP Skill Pack Design
```

这份设计应该包含：

1. 产品定位：skill pack，不是 CLI / 平台。
2. MVP 范围：5 条 30–45 秒短剧。
3. Artifact 契约：episode/assets/shots/prompts/manifest/review。
4. Skill 列表与职责。
5. Tool 列表与职责。
6. 端到端流程。
7. 验收标准。
8. 暂不做事项。
9. 从现有调研项目吸收的设计对应表。

之后再进入实现。

## 最终建议

最终建议很明确：

> 自己搞一套 dramaclaw，但不要搞成大平台；先做一套轻量、可验证、可局部回炉的短剧生产 skill pack。

现成项目的正确用法是：

- `shotcine`：抄中段结构，不抄边界。
- `seedance_prompt`：抄 skill 拆分，不抄重脚本体系。
- `gen-video`：抄导演判断，不抄泛视频产品定位。
- `autoflow`：抄 Gate/QC/回炉思想，不抄平台架构。

这样做的好处是：

1. 保持和 videoclaw 一致的 skill-first 路线。
2. 不被现成项目的历史包袱拖住。
3. 第一版能更快跑通真实短剧生成。
4. 后续可以自然扩展到 CLI、adapter、worker 或平台。