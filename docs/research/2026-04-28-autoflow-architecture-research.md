---
title: autoflow 架构调研：重型 AIGC 短剧生产线如何组织 Worker、Gate 与回炉
created: 2026-04-28 01:49 CST
agent: nova
material_type: architecture-research
status: raw
tags:
  - architecture-research
  - short-drama
  - aigc-pipeline
  - langgraph
  - workers
  - qc
source:
  repo: https://github.com/lijiannan828-oss/autoflow
  local_path: /Users/wangguiping/workspace/github/research/autoflow
  commit: 085b3776fd8b51366fef61474a0c191d946bb67e
  commit_date: 2026-04-28 01:08:18 +0800
  commit_subject: "feat(admin): /admin/generate-stats — 视频生成模块管理者统计页（spec + 7 API + 7 组件） (#146)"
related_topics:
  - dramaclaw
  - AIGC 短剧生产线
  - LangGraph
---

# autoflow 架构调研：重型 AIGC 短剧生产线如何组织 Worker、Gate 与回炉

## 结论先行

`autoflow` 是这轮候选里最接近“工业化 AIGC 短剧生产线”的项目，但它不是轻量 skill pack。它是一个重型平台：LangGraph 双图编排、7 个 worker agent、supervisor、Gate、QC、回炉、成本守卫、前端后台、数据库、Temporal / TOS / Redis / PostgreSQL / GPU worker 等基础设施都在里面。

对 dramaclaw 来说，`autoflow` 不适合直接继承，也不适合作为 MVP 代码骨架；它适合作为架构参照，尤其是：

- ProjectGraph / EpisodeGraph 双图拆分。
- Worker agent 职责边界。
- Gate 与 QC 自动打回的状态机。
- 成本、质量、吞吐作为一等指标。
- 人类反馈进入 RAG / Reflection 的进化闭环。
- 回炉不是盲重跑，而是定位节点 + 对象锚点 + 最小重跑计划。

如果 `shotcine` 是轻量 skill 中段样板，`autoflow` 就是“未来规模化平台长什么样”的参考。

## 仓库基本情况

- 仓库：`lijiannan828-oss/autoflow`
- 本地路径：`/Users/wangguiping/workspace/github/research/autoflow`
- 当前 commit：`085b3776fd8b51366fef61474a0c191d946bb67e`
- 最近提交：`feat(admin): /admin/generate-stats — 视频生成模块管理者统计页（spec + 7 API + 7 组件） (#146)`
- 体量：约 `112M`，`1611` 个 git 文件
- 形态：AIGC 短剧生产平台 + 前端后台 + 后端 API + V3 LangGraph agents + worker/gpu infra

核心入口：

```text
CLAUDE.md
.spec-workflow/specs/aigc-core-orchestrator-platform/requirements.md
.spec-workflow/specs/aigc-core-orchestrator-platform/design.md
.spec-workflow/specs/aigc-core-orchestrator-platform/tasks.md
aigc_video_pipeline/agents/graph_builder.py
aigc_video_pipeline/agents/supervisor/router.py
aigc_video_pipeline/agents/supervisor/cost_guard.py
aigc_video_pipeline/agents/workers/*.py
worker/video_gen/worker.py
worker/video_gen/worker.ts
prompt/qc-checklist.md
frontend/**
backend/**
```

## 项目定位

`CLAUDE.md` 对项目的定义很明确：

> Autoflow 是一套全自动化 AIGC 短剧生产系统。输入完整剧本（5–10 万字），通过双图 LangGraph 流水线自动生产 30–90 集短剧（每集 1–1.5 分钟）。

基础设施和约束：

- 火山引擎 TOS、VikingDB、PostgreSQL、Redis、VKE。
- 视频生成：ComfyUI on 4090 GPU / Seedance 2.0。
- 成本硬约束：≤ 30 元人民币 / 分钟成片。

这已经远超 dramaclaw MVP 的范围。dramaclaw 当前更像 5 条 30–45 秒短剧测试链路；`autoflow` 是面向 30–90 集、单日 300 到 2000+ 分钟产能的平台级系统。

## V2 / V3 版本边界

仓库里同时存在 V2 和 V3 两套流水线，`CLAUDE.md` 强调所有新开发和排查基于 V3：

| 维度 | V3 当前活跃 | V2 遗留 |
|---|---|---|
| 流水线代码 | `aigc_video_pipeline/agents/` | `backend/orchestrator/graph/` |
| Worker | `aigc_video_pipeline/agents/workers/` | `backend/orchestrator/handlers/` |
| Supervisor | `aigc_video_pipeline/agents/supervisor/router.py` | `backend/orchestrator/graph/supervisor.py` |
| State | `aigc_video_pipeline/agents/state.py` | `backend/orchestrator/graph/state.py` |
| 拓扑 | `graph_builder.py` 的 P/E 节点 | V2 N01-N26 |

这说明它已经经历过一轮架构迁移：老 pipeline 不能删，因为前端 API 桥接仍依赖；新工作都放到 V3。

对 dramaclaw 的启发：第一版不要做太重，否则很快会出现 V1/V2 兼容债。skill pack MVP 应尽量保持 artifact 契约稳定、runtime 可替换。

## 核心架构：V3 LangGraph 双图流水线

`aigc_video_pipeline/agents/graph_builder.py` 开头说明它构建两个 LangGraph StateGraph：

```text
ProjectGraph: P01→P02→P03→P04∥P04b→P05
EpisodeGraph: E00→E01→E02→E03→...→E20
```

项目图负责全局资产，剧集图负责单集生产。

### ProjectGraph

`CLAUDE.md` 中给出的 ProjectGraph：

```text
P01 → P02 → P03 → P04 ∥ P04b → P05
```

其中 P05 是 Gate。ProjectGraph 更像全剧层面的资产/设定/美术/选角工作。

### EpisodeGraph

EpisodeGraph 是单集生产链，`CLAUDE.md` 概括为：

```text
E00 → E00b → E01 → ... → E20
```

关键节点：

- E00b：剧本调优 QC
- E02b：摄影 QC
- E04：分镜 QC
- E08：关键帧 QC
- E11：视频 QC
- E14：视觉 Gate + 定稿
- E16：视听 Gate + 定稿
- E18：成片 Gate

`graph_builder.py` 中还定义了 repair loop，例如：

```text
E11 QC fail → E10b → E11
```

这不是简单线性流水线，而是带 QC 打回、Gate 暂停、并行汇合、DIRECT 模式跳过的状态图。

## Supervisor：纯路由，不做 LLM

`aigc_video_pipeline/agents/supervisor/router.py` 的开头非常关键：

> Supervisor router — pure deterministic control flow (no LLM, no I/O).

它负责：

1. 正常推进到下一个节点。
2. QC auto-reject 时路由回源节点，最多 3 次。
3. 进入 Gate 时暂停，等待人工审核。
4. Gate resume 后处理人工决策。
5. 并行节点汇合等待。
6. rerun skip。
7. DIRECT mode skip。
8. cost guard 超预算降级或终止。
9. pipeline done / fatal error 终止。

这个设计很重要：supervisor 不应该是一个“万能大脑 LLM”，而应该是确定性的流程控制器。真正的语义工作由 worker 做，路由由状态机做。

这和用户偏好的“薄编排层、强验收层、统一协议+adapter，不喜欢重 runtime”一致。即便 dramaclaw 第一版不使用 LangGraph，也应该保持这个原则：编排层薄，确定性强，不让 LLM 决定所有控制流。

## Worker agent 职责拆分

`CLAUDE.md` 给出 V3 worker agent：

| Worker | 职责 |
|---|---|
| `ScriptAnalystAgent` | 剧本分析 |
| `ShotDesignerAgent` | 分镜设计 |
| `VisualDirectorAgent` | 视觉导演 / 关键帧相关 |
| `AudioDirectorAgent` | 音频导演 |
| `CompositorAgent` | 合成 |
| `QCInspectorAgent` | 多模型质检 |
| `ReviewDispatcherAgent` | Gate 暂停 + 人工审核决策分发 |

这是一条完整短剧生产线的职能拆分。dramaclaw MVP 不需要全部实现为 agent，但可以借这个拆分来规划 skill 模块：

```text
script-analysis
shot-design
asset/image-prompt
video-prompt/video-gen
audio/subtitle
compose
qc/review
```

## QC：自动打回与多模型质检

`aigc_video_pipeline/agents/workers/qc_inspector.py` 定义 QCInspectorAgent 负责：

- E04：分镜 QC
- E08：关键帧 QC
- E09：连续性检查 + 定稿
- E11：视频 QC

自动打回：

```text
E00b → E00
E02b → E02
E04  → E03
E08  → E07
E11  → E10b
```

最多 3 次。

模型策略：

- E04 文本类 QC 使用 LLM。
- E08 / E11 视频视觉类 QC 使用 VLM，两轮筛查。
- `CLAUDE.md` 提到 E00b/E04 用双模型 + 裁判，E08/E11 用 Flash → Pro 两轮 VLM 筛查。

这说明 QC 不是一个尾部 checklist，而是生产图里的节点。每次失败都应该生成结构化反馈，回到上游修复。

## QC checklist：关键帧质检标准

`prompt/qc-checklist.md` 是很实用的短剧生成验收参考。它把关键帧 QC 拆成三类：

### A. 跨帧一致性（最高优先级）

- 主角服装一致：阻断
- 对手角色服装一致：阻断
- 关键道具一致：阻断
- 场景环境一致：严重
- 光照方向一致：中等
- 叙事连贯：严重

### B. 单帧质量

- 无人物重复：阻断
- 无属性泄漏：阻断
- 情绪符合剧情：严重
- 视线方向正确：严重
- 物体有支撑：严重
- 手部无严重畸变：中等
- 画幅正确：阻断
- 镜面无双人：阻断

### C. 场景完整性

- 有对手戏：严重
- 镜头角度多样：中等
- 戏剧起承转合：中等

这对 dramaclaw 特别有用：第一版即使没有自动 VLM QC，也可以把这些规则变成人工验收清单或轻量 review prompt。

## 需求规格：工业化目标

`.spec-workflow/specs/aigc-core-orchestrator-platform/requirements.md` 给出的核心目标是：

- 90% 自动化，人只做审核。
- 任意打回都能定位“节点 + 对象锚点（资产 / 镜头 / 时间戳）”，并生成最小重跑计划。
- 每次回炉产生新版本，并沉淀修订总结。
- 成本、效率、质量全链路可归因、可预警、可复盘。
- 20+ 节点生产链路中，仅保留 4 个关键人工审核节点。
- 横屏与竖屏双制式显式建模。
- 人类反馈进入 RAG / Reflection 进化闭环。
- MVP 起步单日 300 分钟，最终 2000+ 分钟。

北极星指标包括：

- 单集端到端平均耗时
- 平均回炉轮次
- 单分钟综合成本，红线 30 元 / 分钟
- 单日产能
- 节点瓶颈 Top3
- 人工介入时长占比 ≤10%
- Stage2 shot 一次通过率
- 角色一致性 / 音画同步 / 连续性质量分
- 人类反馈沉淀率

这套指标体系对 dramaclaw 未来很有参考价值，但 MVP 不宜全做。第一版可以只保留最小指标：成功生成率、人工修复次数、单条耗时、单条成本、关键失败原因。

## video_gen worker 与执行层

仓库还有 `worker/video_gen/worker.py`、`worker/video_gen/worker.ts`、`price_book.py` 等文件，说明视频生成被拆成独立 worker 模块，并且成本/价格是执行层的一部分。

这和纯 prompt skill 的差异很大：工业化平台必须关心队列、状态、GPU/API、成本和失败重试。

对 dramaclaw MVP 来说，暂时不需要复制 worker 架构，但应保留执行 manifest：

```text
which prompt generated which media
which provider/model was used
cost/duration/status/error
which media entered final assembly
```

否则后续排查会很难。

## 可直接复用的设计

1. **ProjectGraph / EpisodeGraph 双层拆分**
   - 全局资产和单集生产分开。

2. **Supervisor 确定性路由**
   - 不用 LLM 做控制流。
   - Gate / QC / retry / skip 都是状态机。

3. **Worker 职责边界**
   - 剧本分析、分镜、视觉、音频、合成、QC、审核分发分离。

4. **QC 自动打回**
   - 失败回到明确源节点，不是全量重跑。

5. **Gate 暂停**
   - 人只在关键关卡介入。

6. **结构化反馈**
   - QC 失败给 issues / fix_suggestions。

7. **成本红线**
   - 成本不是事后统计，而是路由和降级依据。

8. **验收清单工程化**
   - 关键帧一致性、单帧质量、场景完整性都能转成 checklist。

## 需要改造的地方

用于 dramaclaw 时，不能直接搬：

1. **架构过重**
   - 前端、后端、Temporal、数据库、K8s、GPU worker、MCP server 都不是 MVP 必需。

2. **业务尺度不同**
   - `autoflow` 面向 30–90 集、1–1.5 分钟/集、日产数百到数千分钟。
   - dramaclaw 当前是 5 条 30–45 秒测试短剧。

3. **运行依赖重**
   - 火山引擎、TOS、VikingDB、Redis、PostgreSQL、VKE、ComfyUI/4090 等。

4. **非 skill-first**
   - 它是平台和工程系统，不是 agent skill pack。
   - 对当前“先做 skill，必要时 CLI”的路线不匹配。

## 不适合直接继承的部分

- 不建议把 LangGraph / Temporal / 前端后台作为 dramaclaw 第一版必需组件。
- 不建议一开始就做 20+ 节点完整生产图。
- 不建议引入复杂数据库状态模型，除非已有多用户、多项目、多并发需求。
- 不建议复制 V2/V3 并存的历史包袱。

## 对 dramaclaw 的启发

`autoflow` 更适合被拆成若干未来设计原则：

### 1. MVP 也要有 Gate / QC 概念

即使第一版只是本地 skill，也可以有：

```text
assets review gate
storyboard review gate
generation qc
final assembly qc
```

### 2. 回炉要定位对象锚点

不要只说“这条视频不好，重跑”。要定位：

```text
episode_id
shot_id
asset_id
media_id
timestamp
failure_reason
suggested_fix
rerun_from
```

### 3. 编排层保持薄

不必一开始用 LangGraph，但可以用 manifest + deterministic script 控制流程，让 LLM 只负责语义生成和 review。

### 4. 成本和质量要早记录

即便不做后台，也应在 run manifest 里记录：

```text
provider
model
task_id
cost_estimate
duration
status
error
review_result
```

### 5. 多集后再考虑 ProjectGraph / EpisodeGraph

第一版 5 条短剧可以先单 episode；当开始做 20 集/多角色连续性时，再引入全局 Project 层。

## 总评

`autoflow` 是一个平台级 AIGC 短剧生产线参考，不是 dramaclaw 的近期实现模板。

它最值得学习的是工程思想：生产线必须有状态机、Gate、QC、回炉、成本和可观测性；人类反馈不能停留在聊天记录里，应该沉淀成结构化修订和知识闭环。

对当前 dramaclaw 来说，最佳策略是：不复制其重平台，只吸收其验收和回炉思想。先做轻量 skill pack，把 artifact 契约和执行 manifest 定好；当链路跑通、任务量上来后，再考虑类似 `autoflow` 的 worker/gate/platform 化。
