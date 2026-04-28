---
title: Plotloom 结构边界补充：Series Repo 与抽卡机制
created: 2026-04-28 22:38 CST
agent: nova
material_type: decision-note
status: raw
tags:
  - plotloom
  - series-repo
  - short-drama
  - gacha
  - video-generation
  - image-generation
---

# Plotloom 结构边界补充：Series Repo 与抽卡机制

## 核心结论

Plotloom 需要 **repo 概念**，但它不是项目管理 repo，而是短剧系列的 **series bible / production package repo**。

同时，Plotloom 需要把 **抽卡机制** 作为短剧生成链路的一等能力：图片和视频模型都不稳定，不能假设一次生成就是最佳结果。

## 1. 为什么短剧需要 repo

短剧通常不是孤立单集，而是连续剧集。

它天然需要保存连续性资产：

- 人物不能崩
- 世界观不能崩
- 关系线要延续
- 爽点 / 悬念要递进
- 前后集要埋钩子
- 视觉风格和角色形象要一致
- 可复用素材要沉淀

如果没有 repo，Plotloom skills 很容易每集各写各的，变成一次性 prompt generator。

## 2. Repo 的定义

建议定义：

```text
Plotloom Repo = 一部短剧 / 一个系列的创作母本 + 生产资产包
```

它保存的是创作连续性，不是进度。

它不是：

- task repo
- progress tracker
- dashboard backend
- 项目管理系统

它是：

```text
短剧系列的记忆体
```

## 3. Repo 可能结构

```text
plotloom-series/
  series-bible.md              # 世界观、人设、调性、禁忌
  series.yaml                  # 系列元信息、平台规格、风格约束
  characters/
    c001.yaml
    c001-reference.png
  arcs/
    season-01.yaml             # 多集弧线、长线钩子
  episodes/
    ep001/
      script.md
      storyboard.yaml
      image-prompts.md
      video-prompts.md
      candidates/
        images/
        videos/
      selected/
        images/
        videos/
      review.md
    ep002/
  assets/                      # 可复用素材
  style/                       # 画风、镜头语言、平台规格
  delivery/                    # 飞书/本地/Codex app 回传记录，可选
```

## 4. Skill 层级变化

Plotloom 至少有两层 skills：

```text
Series-level skills:
  - 初始化一部短剧
  - 建 series bible
  - 设计人物关系和长线钩子
  - 规划 3/5/10 集弧线

Episode-level skills:
  - 生成某一集
  - 拆剧本 / 分镜
  - 生成图片 / 视频 prompt
  - 抽卡生成候选
  - 选择最佳候选
  - 出成片包
  - review & rerun
```

## 5. 为什么需要抽卡

短剧图片和视频生成不是确定性编译。

同一个 prompt 多次生成可能差异巨大：

- 角色脸不稳定
- 情绪不到位
- 镜头动作错
- 手部 / 字幕 / 物体细节错
- 视频模型运动失败
- 视频节奏、表演、戏剧张力不够
- 某次生成可能突然特别好

所以 Plotloom 不能假设：

```text
prompt -> 一次生成 -> 最终结果
```

更现实的链路是：

```text
prompt -> N 次生成候选 -> 初筛 -> 选择 / 合成 / 回炉 -> 最终采用
```

这就是短剧生产里的“抽卡”。

## 6. 抽卡机制的定位

抽卡不是进度管理。

抽卡是 AIGC 短剧生产中的核心创作机制：

```text
用多次生成提高命中好镜头 / 好角色图 / 好封面的概率
```

它应该进入 Plotloom 的 production skills，而不是外部随手操作。

## 7. 抽卡相关 artifacts

建议每个 episode / shot 保留 candidates：

```text
episodes/ep001/candidates/images/
  s001_first_frame_v001.png
  s001_first_frame_v002.png
  s001_first_frame_v003.png

episodes/ep001/candidates/videos/
  s001_v001.mp4
  s001_v002.mp4
  s001_v003.mp4

episodes/ep001/selected/
  s001_first_frame.png
  s001.mp4
```

候选 metadata：

```yaml
candidates:
  - id: s001_video_v001
    shot_id: s001
    type: video
    prompt_hash: abc123
    model: seedance
    seed: null
    path: candidates/videos/s001_v001.mp4
    score:
      character_consistency: 4
      motion: 3
      emotion: 5
      drama: 4
    decision: selected
    notes: 情绪最好，手部小瑕疵可接受
  - id: s001_video_v002
    decision: rejected
    notes: 动作错位，镜头不成立
```

## 8. 抽卡相关 skills

Plotloom skill 链需要补充：

```text
plotloom-draw-image-candidates
plotloom-select-image-candidates
plotloom-draw-video-candidates
plotloom-select-video-candidates
```

也可以合并成：

```text
plotloom-gacha-images
plotloom-gacha-videos
```

其中 select 阶段要支持：

- agent 自评
- 用户在飞书 / Codex App / 本地预览中选择
- 选中后写入 selected
- 未选中保留为候选，不污染最终成片

## 9. 对 Feishu / delivery 的影响

Feishu 回传不只是最终成片，也可能用于抽卡选择：

```text
一次回传 3 张角色图候选，让用户选 A/B/C
一次回传 3 个镜头视频候选，让用户选最佳版本
```

所以 delivery skill 需要支持候选批量回传：

```text
plotloom-deliver-candidates
  - image candidates
  - video candidates
  - with labels A/B/C or v001/v002/v003
```

但仍然不做进度管理。

## 10. 当前结论

Plotloom 的核心不只是“生成一条 prompt”，而是：

```text
series repo 维持连续性
skills 链推动创作
抽卡机制提高生成质量
用户/agent 选择候选
delivery adaptor 回传候选和成片
```

这比单集 prompt generator 更接近真实短剧生产。
