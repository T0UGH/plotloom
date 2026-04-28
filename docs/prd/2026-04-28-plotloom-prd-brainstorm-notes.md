---
title: Plotloom PRD Brainstorm Notes
created: 2026-04-28 22:48 CST
agent: nova
material_type: prd-brainstorm
status: raw
tags:
  - plotloom
  - prd
  - brainstorm
  - short-drama
  - model-agnostic
  - commercial-judgement
---

# Plotloom PRD Brainstorm Notes

## 当前目标

这轮不是实现，而是先聊清楚 PRD，防止 Plotloom 跑偏或变奇怪。

Plotloom 应定义为：

```text
agent-neutral short-drama production superpowers
```

即一套可跨 Codex / Claude Code / OpenClaw / Hermes 等 agent 接入的短剧生产 skills。它通过串联 skills，把一个短剧 idea 推进到一集或多集短剧成品包。

## 核心边界

Plotloom 做：

- 短剧创意打磨
- 人设 / 世界观 / 爽点设计
- 剧集结构，尤其是前三集试水
- 剧本、分镜、镜头、prompt
- 图片 / 视频抽卡
- 短剧审美与商业判断
- 成片验收、回炉、候选选择
- 飞书 / Codex App / 本地等 delivery 回传

Plotloom 不做：

- 任务看板
- 进度管理
- 通用项目管理
- dashboard
- generic workflow runtime
- LangGraph / worker / queue / 重编排平台
- 和某个模型、某个 CLI、某个 API 强绑定

## 新增关键约束：模型/工具无关

Plotloom 不能绑定某一种模型、平台或 CLI。

例如：

```text
今天可能用即梦 CLI
明天可能切火山 API
后天可能用阿里 API / 其他视频模型
```

所以 Plotloom 的核心 skill 应表达导演意图、镜头需求、候选选择标准，而不是把实现写死成某个模型调用。

正确分层：

```text
Skill 层：短剧导演逻辑、prompt/镜头/审美判断
Tool Adapter 层：即梦 CLI / 火山 API / 阿里 API / 其他模型
Delivery Adapter 层：飞书 / Codex App / 本地目录 / Web preview
```

## 新增关键约束：短剧审美 / 商业判断是一等 skill

Plotloom 不能只是“会写剧情”。

短剧成败取决于：

- 前 3 秒强钩子
- 爽点密度
- 冲突是否直给
- 情绪是否上头
- 反转是否够短平快
- 结尾是否有追更钩子
- 封面是否有点击率
- 人设是否能被快速理解
- 前三集能不能验证题材有效

因此必须有一个或多个 skill 负责：

```text
short-drama-commercial-judge
plotloom-hook-review
plotloom-episode-market-fit-review
plotloom-cover-click-review
```

名字待定，但能力必须存在。

## 新增关键约束：前三集试水，不是无限剧集规划

短剧通常先做前几集发上去看效果。

当前 MVP 应围绕：

```text
先做前三集
上线/发布/试投
看效果
效果不好就砍掉
效果好再继续扩展
```

所以 Plotloom 不应该一开始做重型长季规划，而应该围绕“前三集能不能打”优化：

- 第一集：强钩子，快速建立冲突
- 第二集：承接爽点，加深矛盾
- 第三集：给出更强反转或更大悬念，验证追更欲望

## PRD 应回答的问题

1. Plotloom 一句话定义是什么？
2. MVP 是否以“前三集试水包”为验收目标？
3. 第一版要不要要求真生成视频，还是先支持半自动生成包？
4. Series repo 保存哪些连续性资产？
5. 抽卡候选如何组织、选择、回炉？
6. 飞书在 MVP 中承担哪些回传功能？
7. 模型/tool adapter 如何避免绑定死？
8. 短剧商业判断 skill 放在哪个环节？

## 暂定 MVP 成功样子

输入：

```text
一个短剧 idea + 题材/平台/风格约束
```

输出：

```text
一个前三集试水 production package：
- series bible
- 前三集剧情结构
- 第一集完整剧本 / 分镜 / 镜头 prompt
- 图片 / 视频抽卡候选
- selected 成片包或半自动生成包
- 短剧商业判断 review
- 飞书 / Codex App / 本地回传给用户选择和拍板
```

## 当前共识

Plotloom 要做的是短剧生产能力系统，不是管理系统。

它的核心价值是：

```text
让 agent 拥有可连续执行的短剧生产方法，
并能在模型不稳定的情况下通过抽卡、审美判断、回炉和用户选择，
产出前三集可试水的短剧包。
```
