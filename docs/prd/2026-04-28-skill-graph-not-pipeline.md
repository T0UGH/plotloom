---
title: Plotloom PRD 关键修正：Skill Graph 而非固定 Pipeline
created: 2026-04-28 22:58 CST
agent: nova
material_type: decision-note
status: raw
tags:
  - plotloom
  - prd
  - skill-graph
  - superpowers
  - character-reuse
  - short-drama
---

# Plotloom PRD 关键修正：Skill Graph 而非固定 Pipeline

## 核心结论

Plotloom 不能设计成固定 12 步线性流水线。

Plotloom 应该像 Superpowers 一样，是一组可组合、可跳转、可根据上下文触发的 skills：

```text
Plotloom = short-drama skill graph, not a rigid pipeline
```

Agent 应根据当前状态、已有素材、series repo 内容、用户意图，选择合适的下一个 skill，而不是每次从 idea 开始跑完整固定流程。

## 用户关键纠偏

贵平指出：

> 如果之前有设计好的角色，是不是可以复用？

这引申出关键问题：

> 12 个步骤太长了，应该随机排列组合，太死板了。Superpowers 不是这样的。

该纠偏成立。

## 错误方式：固定 Pipeline

不应把 Plotloom 设计成：

```text
idea → market-sense → cast-design → series-bible → episode-cards → ... → delivery
```

这种设计的问题：

- 每次都强迫从头开始
- 已有角色 / 素材 / 剧本无法自然复用
- 用户只想重抽某个镜头时也被拖进完整流程
- skill 之间变成死流程，而不是可组合能力
- 不符合 Superpowers 的灵活组织方式

## 正确方式：Skill Graph

Plotloom 应该是：

```text
当前上下文 / repo 状态 / 用户意图
  → 触发最合适的 skill
  → skill 完成后建议下一跳
  → 必要时 hard gate / review / 回炉
```

每个 skill 应定义：

- 适用触发条件
- 需要哪些上下文
- 可以读取哪些已有资产
- 会产出什么
- 完成后推荐哪些 next skills
- 什么情况下停止并要求用户拍板

## 多入口路径示例

### 1. 从 0 开始做新短剧

```text
using-plotloom
  → market-sense
  → cast-design
  → series-bible
  → episode-cards
  → ep001-production
```

### 2. 已有角色，想复用角色做新剧

```text
using-plotloom
  → load-character
  → character-fit-review
  → series-bible / episode-cards
```

### 3. 已有第一集剧本

```text
using-plotloom
  → script-review
  → storyboard
  → visual-prompt-director
  → video-gacha
```

### 4. 只想重抽某个镜头

```text
using-plotloom
  → load-shot-context
  → video-gacha
  → candidate-review
  → deliver
```

### 5. 想继续做第二集

```text
using-plotloom
  → load-series-bible
  → load-previous-episode-outcome
  → episode-design
  → production
```

## 角色复用是一等能力

短剧资产里最贵的是：

```text
角色认知 + 视觉一致性 + 用户已经接受的脸
```

所以 Plotloom 必须支持复用已有角色，而不是每次重新设计。

需要考虑相关 skills：

```text
plotloom-load-character
plotloom-character-fit-review
plotloom-character-refresh
plotloom-character-reference-gacha
```

角色复用逻辑：

```text
有角色就加载
没有角色就创建
角色不完整就补齐
用户指定复用时优先复用
角色不适合当前题材时给出改造建议
```

## Series Repo 的角色重新定义

Series repo 不是流程控制器，也不是进度系统。

它是上下文仓库：

```text
有就加载
没有就创建
不完整就补
用户指定复用就优先复用
```

它服务于 skill graph 的上下文复用，而不是强制 agent 按固定步骤执行。

## PRD 表述建议

PRD 不应写：

```text
Plotloom 主流程共 12 步，依次执行。
```

应写：

```text
Plotloom 提供一组短剧生产 skills。
Agent 根据当前输入状态和目标产物选择合适 skill 组合。
PRD 定义 canonical paths，但不强制唯一 pipeline。
```

## 当前共识

Plotloom 真正要学 Superpowers 的不是软件开发流程，而是：

```text
skills 自组织 + 触发条件 + hard gate + review + next-skill handoff
```

不是：

```text
固定流程图硬编码
```
