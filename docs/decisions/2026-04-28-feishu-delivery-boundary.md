---
title: Plotloom 接入边界补充：Feishu 作为主要回传通道
created: 2026-04-28 22:30 CST
agent: nova
material_type: decision-note
status: raw
tags:
  - plotloom
  - feishu
  - lark
  - media-delivery
  - short-drama
---

# Plotloom 接入边界补充：Feishu 作为主要回传通道

## 核心结论

Plotloom 需要把 **Feishu / Lark 回传能力** 作为一等接入目标之一。

原因：贵平主要通过飞书和 AI chat；在短剧生产领域，图片、视频、分镜图、封面、样片等产物也主要需要通过飞书回传。

## 用户明确需求

贵平补充：

> 我们需要增加一下飞书相关的功能，因为我主要用飞书来和 AI chat，在短剧领域主要是用飞书给我回传视频和图片。

## 这不改变 Plotloom 的边界

Feishu 能力不是进度管理，也不是 dashboard。

它是 Plotloom 短剧生产链的 **交付/回传接口**：

```text
Plotloom skills 产出图片 / 视频 / 文档 / 审稿结果
  → 通过 Feishu 回传给用户
  → 用户在 chat 里继续反馈、挑选、要求回炉
```

## Feishu 在 Plotloom 中的定位

Feishu 应作为：

- AI chat 主交互入口
- 图片回传通道
- 视频回传通道
- 分镜 / 封面 / 样片审稿通道
- 用户反馈入口
- 可选的文档沉淀入口

不应作为：

- 任务看板
- 进度管理系统
- 项目管理平台
- production dashboard

## 需要支持的 Feishu 产物类型

第一版至少考虑：

```text
image/png, image/jpeg, image/webp  # 角色图、场景图、封面、关键帧
video/mp4                          # 单镜头视频、45s 成片、多集样片
audio/mp3/wav                      # 可选，配音/旁白/音效
markdown/text                      # 剧本、分镜、review、回炉建议
zip                                # 多集成品包或素材包
```

## 对 Plotloom skills 的影响

Plotloom 的 finishing / delivery 类 skill 应该能做：

```text
plotloom-deliver-feishu
  - 收集本轮生成的图片 / 视频 / review 文档
  - 生成简短说明
  - 通过 Feishu 回传媒体文件
  - 在消息里标注：版本、集数、镜头、是否需要用户拍板
```

但它不负责管理进度。

## 可能的 Skill 链补充

原草案：

```text
using-plotloom
  → concept / series / script / storyboard / prompt / generation / assembly / review
```

补充交付末端：

```text
  → plotloom-review-rerun
  → plotloom-deliver-feishu
```

`plotloom-deliver-feishu` 是输出 skill，不是管理 skill。

## 接入实现建议

优先级：

1. 先定义 Feishu delivery skill 的行为规范。
2. 复用当前环境中已有的 Feishu / Lark 发送能力。
3. 对不同 agent，提供 adaptor：
   - Hermes：原生 gateway / send media
   - OpenClaw：如果有飞书 bot 能力，则走 bot media upload/send
   - Codex / Claude Code：可先输出本地文件路径 + 调用外部 `lark-cli` / `nova-lark` wrapper
4. 第一版不要做复杂飞书文档协同，先保证 chat 里能收到图片和视频。

## 验收标准

Plotloom Feishu 接入第一版至少应验证：

- 能发送 1 张图片到当前飞书会话。
- 能发送 1 个 mp4 视频到当前飞书会话。
- 能发送一条带版本说明的文本消息。
- 文件名/说明能区分 episode、shot、version。
- 用户可以直接在飞书里回复：选哪个、哪里回炉、继续下一集。

## 当前结论

Feishu 是 Plotloom 的主要用户交互和媒体交付通道之一；它应被设计为 **delivery skill / adaptor**，而不是进度管理或 dashboard。
