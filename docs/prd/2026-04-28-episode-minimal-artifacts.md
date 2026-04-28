---
title: Plotloom PRD 关键收敛：Episode 只保留两个核心文件
created: 2026-04-28 23:22 CST
agent: nova
material_type: decision-note
status: raw
tags:
  - plotloom
  - prd
  - episode-format
  - anti-overdesign
  - short-drama
---

# Plotloom PRD 关键收敛：Episode 只保留两个核心文件

## 核心结论

Plotloom 的 episode 目录必须极简，避免过度设计成奇怪的生产管理系统。

当前明确收敛为：

```text
episodes/ep001/
  episode-card.md      # 可选意图锚点
  video-prompts.md     # 最小可执行产物
```

不要再默认增加：

```text
script.md
storyboard.md
director-brief.md
visual-plan.md
image-prompts.md
review.md
manifest.json
*.yaml
*.json
```

## 用户明确边界

贵平确认：

> 那就只要这两个，不要再增加了，一定不要过度设计变成一个怪东西。

该边界必须写入 PRD。

## 文件定位

### `video-prompts.md`

最小可执行产物。

只要有它，Plotloom 就能进入视频生成 / 抽卡 / 回传链路。

它承载：

- 可直接投喂模型或经 adapter 转换的连续叙事 prompt
- 画面动作
- 台词窗口
- 运镜与节奏
- 素材引用说明
- 尾帧衔接
- 模型相关注意事项（如果需要）

### `episode-card.md`

推荐但非必需的意图锚点。

当用户输入不够清晰，或需要避免短剧长线跑偏时，用它记录：

- 本集 logline
- 本集爽点
- 反转
- 结尾钩子
- 必须保留的人设/信息
- 本集在 12/18 集中的功能

它不是剧本，不是分镜，不是任务计划。

## 最小运行原则

```text
video-prompts.md is the minimum runnable artifact.
episode-card.md is an optional intent anchor.
```

中文：

```text
video prompt 是能跑的最小单元。
episode card 是防跑偏的可选锚点。
```

## Skill Graph 中的行为规则

- 用户只要 prompt：直接生成 `video-prompts.md`。
- 用户要做一集短剧但意图不清：先补 `episode-card.md`。
- 用户已有 episode intent：不强制生成 `episode-card.md`。
- 用户已有 `video-prompts.md`：直接进入抽卡、回传、回炉。
- 缺图片 / 场景 / 角色参考时，不默认写 `image-prompts.md`，只在 `video-prompts.md` 中表达需要的素材；实际素材由对应 tool / adapter / 用户提供。

## 反过度设计原则

Plotloom 不走传统影视工业文件堆：

```text
剧本 → 导演阐述 → 分镜 → 镜头表 → prompt → manifest → review
```

Plotloom 第一版只围绕：

```text
episode-card.md（可选） → video-prompts.md（必备） → 抽卡 / 回传 / 回炉
```

## 当前共识

Plotloom 的价值不在于创造一堆文件，而在于让 agent 掌握短剧生产 skills，并能直接产出可用视频 prompt 和候选视频。

因此 episode artifact 必须保持极简。
