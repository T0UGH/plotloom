---
title: seedance_prompt 源码/Prompt 解读：短剧 Production Skills 与 Seedance 工作流拆解
created: 2026-04-28 01:49 CST
agent: nova
material_type: source-reading
status: raw
tags:
  - source-reading
  - short-drama
  - ai-video
  - seedance
  - production-skills
source:
  repo: https://github.com/xiasong0501/seedance_prompt
  local_path: /Users/wangguiping/workspace/github/research/seedance_prompt
  commit: 55f7a4d78bdabe166a70bb16bd032fed96424509
  commit_date: 2026-04-03 17:59:18 +0800
  commit_subject: "Rename ENVIRONMENT_SETUP.md to readme.md"
related_topics:
  - dramaclaw
  - 短剧生产流水线
  - Seedance 2.0
---

# seedance_prompt 源码/Prompt 解读：短剧 Production Skills 与 Seedance 工作流拆解

## 结论先行

`seedance_prompt` 不是一个轻量可直接拿来用的 dramaclaw skill pack，而是一个偏“生产系统 + prompt/skill 库 + OpenAI agent flow + Seedance 提交流水线”的大仓库。

它的价值不在于直接 fork，而在于给出了短剧生产链条中几个关键层的参考：

1. 从视频反向学习剧本、分镜、题材和 Seedance prompt 模板。
2. 从剧本生成导演讲戏本、人物/场景提示词、Seedance 分镜提示词。
3. 用风格迁移链路把已有 Seedance prompt 通过模板库增强。
4. 把参考图上传到 TOS，再走 Seedance API 生成视频。
5. 用 production skills 拆出剧本分析、视频脚本重构、Seedance 分镜、Seedance prompt review 等职责。

对 dramaclaw 来说，它不是第一版骨架，但可以作为“production skill 体系”和“Seedance 交付链”的参考。

## 仓库基本情况

- 仓库：`xiasong0501/seedance_prompt`
- 本地路径：`/Users/wangguiping/workspace/github/research/seedance_prompt`
- 当前 commit：`55f7a4d78bdabe166a70bb16bd032fed96424509`
- 最近提交：`Rename ENVIRONMENT_SETUP.md to readme.md`
- 体量：约 `88M`，`526` 个 git 文件
- 形态：脚本流水线 + prompt library + production skills + OpenAI Agents scaffold

核心入口：

```text
WORKFLOW_QUICKSTART.md
WORKFLOW_COMMANDS.md
skills/production/script-analysis-review-skill/SKILL.md
skills/production/video-script-reconstruction-skill/SKILL.md
skills/production/seedance-storyboard-skill/SKILL.md
skills/production/seedance-prompt-review-skill/SKILL.md
openai_agents/README.md
openai_agents/skills/common/output_contracts.md
openai_agents/skills/*_workflow.md
pipelines/*.py
prompt_library/**
```

## 总体工作流

`WORKFLOW_QUICKSTART.md` 把仓库主干概括为：

```text
视频 -> run_series_pipeline.sh -> 剧本经验/分镜经验/Seedance 模板库
  -> run_openai_agent_flow.sh -> 02-seedance-prompts
  -> run_seedance_style_transfer.sh（可选增强）
  -> Seedance 提交链
```

它不是单向“剧本转 prompt”，而是包含反向学习和正向生产两类能力。

### 1. run_series_pipeline.sh：从视频学习经验

`run_series_pipeline.sh` 是上游学习入口。它不只是视频转剧本，而是同时做：

- 从视频学习剧情结构、题材判断、连续性、剧本写法、镜头和分镜经验。
- 从视频学习 Seedance prompt 的模板和经验。

关键产物包括：

- `analysis/<剧名>/series_strength_playbook_draft.json`
- `analysis/<剧名>/series_bible.json`
- `analysis/<剧名>/series_context.json`
- `prompt_library/**`

这层对 dramaclaw 的启发是：短剧生产 skill 不一定只吃用户写好的剧本，也可以长期积累“题材经验 / 镜头经验 / prompt 模板”。但这更适合第二阶段，不适合 MVP 第一版一开始就做重。

### 2. run_openai_agent_flow.sh：从剧本到导演/服化道/分镜

`WORKFLOW_COMMANDS.md` 把主线说得更工程化：

```text
视频 -> 剧本：run_video_pipeline.sh / run_series_pipeline.sh
剧本 -> 导演/服化道/分镜：run_openai_agent_flow.sh
分镜 -> 参考图 -> TOS -> Seedance 视频 API：run_nano_banana_assets.sh / run_seedance_api_generation.sh / run_upload_seedance_refs.sh
```

OpenAI agent flow 的输出目标是：

```text
outputs/<剧名>/<集数>/01-director-analysis.md
outputs/<剧名>/<集数>/02-seedance-prompts.md
assets/<剧名>-gpt/character-prompts.md
assets/<剧名>-gpt/scene-prompts.md
```

这和 `shotcine` 不同：`shotcine` 更强调 JSON 结构真源；`seedance_prompt` 更强调多 agent / 多脚本串联后的文件产物。

## Production skills 体系

仓库中值得重点看的不是 prompt_library 的海量样本，而是 `skills/production/` 下的几类 skill：

```text
script-analysis-review-skill
video-script-reconstruction-skill
seedance-storyboard-skill
seedance-prompt-review-skill
```

这些 skill 体现了一个更工业化的拆分：

| skill | 职责 |
|---|---|
| script-analysis-review-skill | 审核/分析剧本结构、爆点、连续性等 |
| video-script-reconstruction-skill | 从视频或素材重构短视频脚本 |
| seedance-storyboard-skill | 基于导演讲戏本生成 Seedance 2.0 动态视频提示词 |
| seedance-prompt-review-skill | 审核 Seedance prompt 是否满足生成约束 |

这比单个 `SKILL.md` 更接近生产团队分工：先分析，再重构/创作，再分镜，再 review。

## seedance-storyboard-skill 细读

`skills/production/seedance-storyboard-skill/SKILL.md` 定义为：

> 分镜师技能。用于基于导演讲戏本编写 Seedance 2.0 格式的动态视频提示词。

它的关键输入不是普通剧本，而是上游的导演讲戏本和资产提示词：

- `01-director-analysis.md`
- `assets/<剧名>/character-prompts.md`
- `assets/<剧名>/scene-prompts.md`
- `seedance-prompt-methodology.md`
- 官方提示词示例

执行流程：

1. 读取上游产物。
2. 建立素材对应表。
3. 为每个剧情点编写 Seedance 2.0 提示词。
4. 按模板输出。

它有几个很有价值的规则。

### 素材对应表规则

人物和场景都通过 `@图片N` 引用，但只给已有素材文件中的人物/场景分配引用。群演、一次性配角不进对应表，而是直接文字描述。

场景素材还有一个重要规则：九宫格只是生成格式，最终每个格子要单独提取成独立场景参考图；因此素材对应表里每个场景必须独立编号，不能把整张九宫格当一个 `@图片`。

这点对短剧生产非常实际：资产生成和视频生成之间常有“拼图 / 九宫格 / 裁切 / 上传”的中间步骤，skill 必须意识到平台消费的是单独素材，不是生成时的整图。

### 单条提示词平台约束

`seedance-storyboard-skill` 明确 Seedance 单条提示词维度约束：

- 图片 ≤ 9 张 / 条
- 视频 ≤ 3 个 / 条
- 音频 ≤ 3 个 / 条
- 总文件数 ≤ 12 个 / 条

并说明素材对应表可以是全文档映射，超过单条限制；但每条生成任务必须满足平台限制。

这是 dramaclaw 后续做执行 adapter 时必须内置的硬约束。

### 统一主时间线

这个 skill 反复强调要写“唯一的复合 timeline”：把镜头、对白、声音和尾帧交棒融合在同一组 beat 里，再派生兼容字段。

它还要求：

- 每条提示词都要承接上一段尾态。
- 不允许压缩关键对白链条、羞辱反击链条、揭示链条。
- 必须拆出镜头节拍顺序，避免画面和台词同时过载。
- 每条提示词要明确入画路径、离场/遮挡方式，避免人物凭空出现或消失。
- 高能特效必须有源头、传播、余波、环境反馈。

这比“给每个镜头写一段 prompt”更成熟。它把 Seedance 生成任务视作一个连续叙事段落，而不是孤立镜头。

## OpenAI Agents scaffold

`openai_agents/README.md` 说明该目录是当前 `.claude` workflow 的 OpenAI-native 版本，但不是一对一 prompt 改名，而是映射到 OpenAI agent model：

- specialized `Agent` objects
- `handoffs` between agents
- custom `function_tool` tools for controlled file I/O
- a single orchestrator agent that decides when to delegate

Agent 列表：

| Agent | 职责 |
|---|---|
| `producer_agent` | 总入口和协调者 |
| `explosive_agent` | 为留存和点击率评分、升级剧本 |
| `director_agent` | 生成 `01-director-analysis.md` |
| `art_agent` | 生成人物 / 场景提示词 |
| `storyboard_agent` | 生成 `02-seedance-prompts.md` |

这个设计对 dramaclaw 的启发是：skill pack 和 agent flow 可以共存。第一版可以是 Claude Code / Hermes skill；后续如果要接 OpenAI Agents SDK，可以保留同样的 artifact 契约，只换 orchestrator。

## Output contracts

`openai_agents/skills/common/output_contracts.md` 的思路是：每个阶段都有明确输出文件，而不是让 agent 随意发挥。

从 README 可见核心输出是：

```text
outputs/<剧名>/<集数>/01-director-analysis.md
outputs/<剧名>/<集数>/02-seedance-prompts.md
assets/<剧名>-gpt/character-prompts.md
assets/<剧名>-gpt/scene-prompts.md
```

这种“文件即契约”对多 agent 协作很重要。不同 agent 之间靠固定文件名、固定目录和固定字段传递，不靠上下文记忆。

## 可直接复用的设计

1. **production skills 拆分**
   - 剧本分析 review
   - 脚本重构
   - Seedance 分镜
   - Prompt review

2. **导演讲戏本作为中间层**
   - 剧本不直接进入视频 prompt
   - 先变成导演分析，再变成 prompt

3. **素材对应表**
   - 人物 / 场景独立编号
   - 群演不进资产表
   - 九宫格场景要拆成独立参考图

4. **平台硬约束进入 skill**
   - 单条提示词素材数量限制
   - 台词串行，不允许双声叠台词
   - 时间线 beat 控制

5. **反向学习链路**
   - 从视频学习剧本/分镜/Seedance prompt 模板
   - 形成长期 prompt library

6. **OpenAI agent migration 思路**
   - 同一生产链可映射到多个 agent runtime

## 需要改造的地方

如果给 dramaclaw 用，不能直接搬这个仓库：

1. **过重**
   - 88M、500+ 文件，包含大量 prompt library、脚本、pipeline、配置。
   - 不适合作为第一版 skill pack 骨架。

2. **脚本和本地目录耦合明显**
   - 多个 `run_*.sh` 和 config 文件依赖仓库内部组织。
   - 直接迁移成本高。

3. **真源结构不够统一**
   - 产物以 Markdown 和目录约定为主，不像 `shotcine` 那样有明确 `assets/shots/prompts` schema。
   - 对自动化续跑和验证不如结构化 JSON/YAML 稳。

4. **偏 Seedance 专用**
   - 对 imagegen2 / 即梦 CLI / ffmpeg 成片链路还需要重写 adapter。

## 不适合直接继承的部分

- 不建议把整个 `prompt_library` 作为 dramaclaw 初始资产：太重，且上下文污染风险高。
- 不建议第一版就做从视频反向学习的 pipeline：这会把 MVP 复杂度拉爆。
- 不建议照搬 OpenAI Agents scaffold：当前用户更关心 skill-first，agent SDK 可以作为未来迁移路径。

## 对 dramaclaw 的启发

`seedance_prompt` 最值得吸收的是 production skill 分层：

```text
script-analysis-review
  ↓
video-script-reconstruction / director-analysis
  ↓
asset-prompt-generation
  ↓
seedance-storyboard
  ↓
seedance-prompt-review
  ↓
seedance-submit
```

但 dramaclaw 第一版可以更薄：

- 不做视频反向学习。
- 不做大 prompt library。
- 不做复杂 OpenAI agent scaffold。
- 只保留：剧本/episode 输入、资产、分镜、图片 prompt、视频 prompt、生成 hook、合成、验收。

## 总评

`seedance_prompt` 是一个很有参考价值但不适合直接继承的生产仓库。

它告诉我们：真实短剧生产不是“写一段 Seedance prompt”那么简单，而是需要剧本经验、导演讲戏、资产提示词、素材引用、平台约束、提交链和 prompt review。

对 dramaclaw 来说，它是第二阶段参考：当第一版 skill pack 跑通后，可以从这里吸收 production skill 拆分、Seedance 提交约束、反向学习和 prompt review 机制。
