---
title: Plotloom 边界修正：短剧生产 Skills，不做进度管理
created: 2026-04-28 22:25 CST
agent: nova
material_type: decision-note
status: raw
tags:
  - plotloom
  - decision
  - boundary
  - skills
  - short-drama
---

# Plotloom 边界修正：短剧生产 Skills，不做进度管理

## 核心结论

Plotloom 要做的是类似 Superpowers 的 **可串联 skills 能力系统**，但领域是短剧生产，不是软件开发，也不是项目管理。

更准确的定义：

```text
Plotloom = agent-neutral short-drama production superpowers
```

即：一组可串联、可自动触发、可跨 agent 接入的短剧生产 skills，让 agent 能从一个 idea 连续推进到一集或多集短剧成品包。

## 用户明确边界

贵平修正：

> 我们是通过一系列串联的 skill 直接出一集短剧或者好几集短剧。

并明确要求：

> 千万不要做什么进度管理或者乱七八糟的东西。

## 做什么

Plotloom 做短剧生产能力：

- 短剧创意打磨
- 人设 / 世界观 / 爽点设计
- 单集 / 多集剧情结构
- 剧本、分镜、镜头、prompt
- 图像 / 视频生成指令
- 成片组装建议
- 成片验收与回炉

## 不做什么

Plotloom 明确不做：

- 任务看板
- 进度管理
- 通用项目管理
- agent runtime
- 编排平台
- LangGraph / 队列 / worker
- dashboard
- generic artifact protocol 过度设计

## 从 Superpowers 学什么

Superpowers 值得学习的是：

- 多个 skill 如何串联成强流程链
- 每个 skill 如何定义触发条件
- 每个 skill 如何指向下一个 skill
- 哪些步骤需要 hard gate
- 哪些步骤必须 review
- 什么条件下停止、回炉、继续

不学习的是：

- 软件项目管理外壳
- implementation plan / task management 形态
- 进度管理
- 通用 workflow runtime

## 修正后的 Plotloom 心智模型

Plotloom 更像：

```text
短剧导演 + 编剧室 + 分镜师 + prompt 导演 + 剪辑验收
```

而不是：

```text
项目管理器 / 工作流引擎 / production tracker
```

## Skill 链心智模型草案

```text
using-plotloom
  → plotloom-concept-lab
  → plotloom-series-or-episode-structure
  → plotloom-script-room
  → plotloom-storyboard-director
  → plotloom-visual-prompt-director
  → plotloom-video-prompt-director
  → plotloom-assembly-guide
  → plotloom-review-rerun
```

这些名字只是草案，后续头脑风暴再定。关键是：Plotloom 的流程链应该服务于“直接出一集 / 多集短剧成品包”，不是服务于管理任务。
