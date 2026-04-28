---
title: shotcine 源码/Prompt 解读：最接近短剧 Skill Pack 的分镜提示词引擎
created: 2026-04-28 01:49 CST
agent: nova
material_type: source-reading
status: raw
tags:
  - source-reading
  - short-drama
  - ai-video
  - seedance
  - seedream
  - skill-pack
source:
  repo: https://github.com/blazegyna772-bot/shotcine
  local_path: /Users/wangguiping/workspace/github/research/shotcine
  commit: b3a3cf937129e3eb3c8607dac713db0dc602ed64
  commit_date: 2026-04-27 12:14:39 +0800
  commit_subject: "v2.5: shotcine 初始提交"
related_topics:
  - dramaclaw
  - videoclaw
  - 短剧生产流水线
---

# shotcine 源码/Prompt 解读：最接近短剧 Skill Pack 的分镜提示词引擎

## 结论先行

`shotcine` 是这轮 GitHub 深挖里最接近“短剧生产 skill pack 雏形”的项目。

它不是完整短剧生产线：不负责真实调用 Seedream / Seedance，不负责素材生成、视频生成、合成、字幕、封面、验收和回炉。但它已经把“剧本/已分镜脚本 → 资产清单 → shots.json → storyboard.md → Seedream 图片提示词 → Seedance 视频提示词 → 分组 CSV”这条中间链路做成了一个比较清楚的 agent skill。

对 dramaclaw 的价值很高：它证明第一版不一定要先做 CLI 或平台，而可以先做一个 **skill-first 的文本协议 + schema + 少量工程工具**。真正应该直接借鉴的是它的 artifact 设计、资产 ID 规则、分镜/提示词分离、以及 `episode.py validate/render/export` 这种“LLM 生成 JSON，脚本派生产物”的模式。

## 仓库基本情况

- 仓库：`blazegyna772-bot/shotcine`
- 本地路径：`/Users/wangguiping/workspace/github/research/shotcine`
- 当前 commit：`b3a3cf937129e3eb3c8607dac713db0dc602ed64`
- 最近提交：`v2.5: shotcine 初始提交`
- 体量：约 `428K`，`26` 个 git 文件
- 语言/形态：Markdown skill + JSON schema + Python 工具脚本

关键文件：

```text
SKILL.md
schemas/assets.schema.json
schemas/shots.schema.json
schemas/prompts.schema.json
schemas/groups.schema.json
tools/episode.py
tools/episode.json.template
references/spec/assets.md
references/spec/shots.md
references/spec/prompts.md
references/spec/grouped-prompts.md
references/templates/image-prompt.md
references/templates/video-prompt.md
references/constraints/direct-video-generation.md
references/examples/example-output.md
```

## 核心入口：SKILL.md

根目录 `SKILL.md` 把项目定义为：

> 将中国影视短剧标准剧本或已分镜脚本转成结构化分镜、资产清单，以及适配 Seedream 图片和 Seedance 视频的提示词。

它支持两种输入模式：

| 输入模式 | 输入内容 | 默认处理 |
|---|---|---|
| 剧本模式 | 未分镜的标准剧本文本 | 重新提取资产、重新规划镜头、生成 `shots.json` |
| 已分镜脚本模式 | 用户已有分镜脚本 / 视频脚本 / 镜头脚本 | 沿用已有分镜边界和镜头顺序，只做结构化补全、资产提取、提示词生成 |

这点很关键：短剧生产里经常不是“从空白开始”，而是已经有人给了分镜、片段、投流脚本、爆点脚本。`shotcine` 明确把“已分镜脚本模式”当作一等输入，而不是默认重拆。

推荐触发口令也很像一个真实 agent skill：

- `全流程生成`
- `生成资产`
- `生成分镜规划`
- `生成全部提示词`

产物也不是一份大 Markdown，而是一组可继续审核/续跑的结构化文件：

| 文件 | 内容 | 用途 |
|---|---|---|
| `assets.json` | 人物 / 场景 / 道具资产 | 审核、修改、引用 |
| `shots.json` | 分镜结构数据 | 审核、修改、续跑 |
| `storyboard.md` | `shots.json` 的人读视图 | 人工审核分镜 |
| `prompts.json` | 每镜图片/视频提示词 | 直接复制或下游消费 |
| `groups.json` | LLM 生成的分组方案 | export 阶段使用 |
| `EPxx_grouped_prompts.csv` | 分组提示词导出 | 给视频生成工具按组投喂 |
| `video_prompts.txt` | 视频提示词清爽版 | 快速审阅 / 批量复制 |

## 工作流拆解

### 1. 资产抽取：先建立稳定引用层

`references/spec/assets.md` 的核心是把真实世界名称和内部引用分开：

- `asset_id` 是内部资产标识，例如 `人物1`、`场景2`、`道具3`。
- `name` 是真实名称，例如“林小满”“咖啡馆窗边双人座”。
- 提示词开头使用 `@asset_id`，正文仍写真实名称。

这种设计解决两个问题：

1. Agent 可以稳定引用资产，不受角色名变化、简称、别名影响。
2. 提示词仍保持自然语言可读，不会满篇都是机械 ID。

它还区分“同角色独立人物资产”：当服装明显变化、长期外貌变化、跨时间段状态差异时，可以为同一角色建独立人物资产；镜头级短暂变化则写在提示词 `[]` 中，而不是污染全局资产。

这对短剧很实用。因为短剧里同一个人物可能有“落魄版 / 华丽版 / 受伤版 / 婚礼版”，如果全部混在一个角色资产里，后续出图和视频一致性会很差。

### 2. 分镜规划：把 `shots.json` 作为结构真源

`SKILL.md` 明确：`shots.json` 是全流程的结构主文件，定义镜头编号、时段、镜头类型、景别、运镜、资产引用、画面动作、台词、时长。

`storyboard.md` 只是 `shots.json` 的人读投影视图，不应该从 Markdown 反推生成提示词。

这也是 dramaclaw 应该继承的方向：

- 真源：结构化 JSON / YAML
- 人读：Markdown 表格
- 执行：prompt / csv / txt / manifest 等派生产物

`references/spec/shots.md` 里最有价值的是拆镜原则：

> 剧本模式采用“戏眼优先 → 情绪段划分 → 台词覆盖设计 → 空间关系组织 → 结构化落表”，不机械按句号切镜。

这比很多“按句子切镜头”的粗糙工具更接近短剧生产。短剧的分镜不是语法切分，而是围绕爆点、反应、羞辱、反击、揭示、情绪落点组织镜头。

### 3. 图片提示词：Seedream 用自然短句，不用字段壳

`references/spec/prompts.md` 和 `references/templates/image-prompt.md` 明确区分图片提示词和视频提示词：

| 维度 | 图片提示词 | 视频提示词 |
|---|---|---|
| 格式 | 自然短句，分号分隔，无字段壳 | 结构化字段，`【字段名】` 包裹 |
| 原因 | Seedream 是图像生成模型，自然段落更稳定 | Seedance 需要精确控制景别、运镜、动作、台词 |

图片提示词唯一正式格式是：

```text
@资产引用；
景别与构图；
主体状态与动作瞬间；
光影氛围；
风格标签；
负面提示
```

并且有硬禁区：

- 不直接写“她很绝望”“他内心崩溃”这类不可见心理判断。
- 不用“他 / 她 / 他们”作为主锚点，优先写真实角色名或明确主体。
- 画面内文字若是关键信息，要通过 `screen_text` 或可见道具描述落地。

这个规则很适合短剧：短剧核心是情绪，但图像模型只能生成可见物理状态，不能直接生成抽象心理。

### 4. 视频提示词：Seedance 用字段化控制

`references/templates/video-prompt.md` 的视频模板使用：

```text
### 镜头01（0-3s）

【景别】...
【空间关系】...
【画面动作】...
【光影影调】...
【台词】...
```

字段分工很明确：

- `【景别】`：回答镜头拉到什么距离。
- `【空间关系】`：回答拍到哪里、角色在哪里、前后景关系是什么。
- `【画面动作】`：回答镜头怎么动、画面里怎么动。
- `【光影影调】`：只写光线与影调，避免和空间字段混压。
- `【台词】`：角色名 + 台词，OS 需要明确标注。

它还特别强调：`【空间关系】` 不要写成动作，`【画面动作】` 不要缺少运镜和时序连接词。这是视频提示词常见失败点：空间、动作、运镜、台词混在一个自然段里，模型只能大概理解，无法稳定执行。

### 5. 分组导出：把连续镜头合成生成任务

`references/spec/grouped-prompts.md` 是项目里非常实用的一层。

它定义 `grouped_prompts.csv` 的定位：按连续镜头分组导出，供视频生成工具按组使用。

分组规则包括：

- 优先保证人物、空间、道具、状态连续。
- 不为凑时长强行分组。
- 15 秒以内优先，15–17 秒可保留为一组。
- 单镜自身超过 15 秒，不自动拆分，交由人工处理。
- 同一空间内的连续动作链、连续情绪推进、同一道具主线持续推进，优先同组。

CSV 固定列为：

```text
序号,图片提示词,视频提示词,首帧提示词,尾帧提示词,文案
```

这层很像短剧生产中“投喂工具”的适配层。dramaclaw 如果后面接即梦 CLI / Seedance API / 网页自动化，也需要类似的 export adapter。

## 直接视频生成约束

`references/constraints/direct-video-generation.md` 是默认始终生效的约束。关键规则：

- 单镜默认不超过 15 秒。
- 强冲突、强情绪、爆点镜常见 3–7 秒。
- 长台词优先拆成镜头组覆盖，不要塞进一个镜头。
- 中文对白超过约 4.5 字/秒，需要检查停顿、反应镜、镜头功能。
- 竖屏 9:16 优先中近景、近景、特写；多人物用前后景、纵深、上下位关系组织。
- 提示词首行 `@资产[...]` 只写稳定视觉变更。

这些约束不是“美学建议”，而是避免 AI 视频生成失败的工程规则。

## 工程工具：episode.py

`tools/episode.py` 是这个仓库少量但关键的工程部分。它不是完整 CLI 产品，而是 skill 的辅助工具。

它提供：

```bash
python3 tools/episode.py init --ep EP01
python3 tools/episode.py render --ep EP01
python3 tools/episode.py export --ep EP01
python3 tools/episode.py video-export --ep EP01
python3 tools/episode.py validate --ep EP01
```

对应能力：

- `init`：初始化集数目录与 `episode.json`。
- `render`：`shots.json` → `storyboard.md`。
- `export`：`shots.json + prompts.json + groups.json` → `EPxx_grouped_prompts.csv`。
- `video-export`：`prompts.json` → `video_prompts.txt`。
- `validate`：校验 schema、资产引用、shot/prompts 对齐、prompt 结构、groups 覆盖与顺序。

它还有一个重要边界：默认产物写入用户项目目录 `storyboard/EPxx/`，不得写回 skill 安装目录。

这正是 skill-first 项目应该有的工具形态：LLM 负责语义生成，Python 负责确定性派生和校验。

## 可直接复用的设计

1. **artifact 分层**
   - `assets.json`：资产基线
   - `shots.json`：结构真源
   - `storyboard.md`：人读审核
   - `prompts.json`：生成提示词
   - `groups.json` / CSV：投喂工具适配

2. **资产 ID + 真实名称双层表达**
   - 内部引用稳定
   - 提示词自然可读

3. **分步触发口令**
   - 先资产
   - 再分镜
   - 再提示词
   - 最后 export

4. **输入模式区分**
   - 普通剧本重拆
   - 已分镜脚本沿用边界

5. **LLM 生成 JSON，脚本派生产物**
   - 降低 LLM 手工转写错误
   - 方便 validate

6. **Seedream / Seedance prompt 格式分离**
   - 图片自然短句
   - 视频字段结构

## 需要改造的地方

如果用于 dramaclaw，`shotcine` 还缺几层：

1. **没有真实 generation hook**
   - 不调用 imagegen2 / Seedream
   - 不调用即梦 CLI / Seedance
   - 不产出任务状态和 media manifest

2. **没有成片装配**
   - 不处理 ffmpeg merge
   - 不处理字幕、封面、BGM、音效
   - 不输出 final video package

3. **没有端到端验收闭环**
   - 只校验 JSON / 引用 / prompt 结构
   - 没有实际视频质量检查
   - 没有失败回炉策略

4. **schema 是 JSON-first，不一定适合 dramaclaw 第一版**
   - dramaclaw MVP 如果输入核心是 `episode.yaml`，需要转换/兼容。
   - 但输出中间产物仍可借鉴 JSON schema。

5. **没有 workspace / run manifest 概念**
   - 后续多集、多版本、多模型、多次重跑时，需要 `runs/<id>/manifest.json` 之类的运行真源。

## 不适合直接继承的部分

- 不建议直接 fork 成 dramaclaw 主库：它更像单一分镜提示词 skill，而不是完整短剧生产流水线。
- 不建议把 `grouped_prompts.csv` 当成唯一执行接口：CSV 适合人工/平台复制粘贴，但对自动化不够稳。
- 不建议让 Markdown 变成真源：`shotcine` 已经避免了这一点，dramaclaw 也应坚持结构化真源。

## 对 dramaclaw 的启发

`shotcine` 给出的最重要启发是：短剧生产 skill pack 的第一版可以很薄，但 artifact 契约必须早定。

建议 dramaclaw 第一版继承以下思想：

```text
episode.yaml
  ↓
assets.yaml/json
  ↓
shots.yaml/json
  ↓
storyboard.md
  ↓
image_prompts.json + video_prompts.json
  ↓
generation manifest
  ↓
ffmpeg assembly manifest
  ↓
final package
```

也就是说，`shotcine` 可以作为 dramaclaw 的“分镜与 prompt 中段参考”，但 dramaclaw 还要补上：

- 输入 episode 契约
- imagegen2 / Seedance 执行 hook
- 生成文件管理
- 成片合成
- 端到端验收
- 失败回炉

## 总评

`shotcine` 不是完整可用的短剧生产 skill pack，但它是目前看到的最接近“短剧分镜 + prompt skill 原型”的项目。

它值得重点吸收，不是因为代码复杂，而是因为它把短剧 AI 视频生产里最容易混乱的几件事拆开了：资产、分镜、图片提示词、视频提示词、分组导出、结构校验。

对 dramaclaw 来说，最佳策略不是直接复用，而是把它当作中段协议样板：保留 skill-first、schema-first、工具校验的思路，再向前补 episode 输入，向后补生成、合成和验收。
