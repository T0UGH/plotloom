---
title: Plotloom PRD 关键修正：Seedance Prompt 不是镜头列表
created: 2026-04-28 23:10 CST
agent: nova
material_type: decision-note
status: raw
tags:
  - plotloom
  - prd
  - seedance
  - prompt-director
  - video-generation
  - short-drama
---

# Plotloom PRD 关键修正：Seedance Prompt 不是镜头列表

## 核心结论

Plotloom 不能把 Seedance 2.0 当成“一个镜头调用一次”的低级视频 API。

Seedance 2.0 更适合吃一条 **连续叙事提示词**：一条 8-15 秒左右的视频生成任务，内部可以包含多个镜头 / 多个节拍，但必须是一套单主时间线。

因此：

```text
Seedance prompt ≠ shot list
Seedance prompt = director brief translated into a continuous narrative timeline
```

## 用户关键纠偏

贵平指出：

> Seedance 2.0 比你想的要强力，它一次性处理 8 个镜头都不成问题，我们不是一个镜头调用一次模型，它能生成 15-20 秒的视频出来。

随后进一步指出：

> 这不是一个好的给 Seedance 的 prompt，你之前不是学过怎么写吗，再去学一遍。

该纠偏成立。

## 错误方式：按 shot 列表喂模型

不应设计成：

```text
shot s001 -> 调一次模型
shot s002 -> 调一次模型
shot s003 -> 调一次模型
```

也不应把 prompt 写成：

```text
segment_001:
  shots: s001-s008
```

这种写法仍然是工程索引脑，不是 Seedance prompt 脑。

## 正确方式：单主时间线连续叙事 prompt

Seedance prompt 应包含：

- 素材引用声明：@图片 / @视频 / @音频 的用途
- 连续叙事段落
- 时间节拍：如 0-3s / 4-8s / 9-12s / 13-15s
- 人物入画、离场、遮挡、方位连续
- 运镜路径和空间锚点
- 台词窗口，而不是独立台词表
- 声音 / 音效 / BGM
- 尾帧衔接点，方便下一段延长或续写

核心原则：

```text
一条提示词 = 一段连续叙事视频
一条提示词内可有多镜头，但必须有唯一主时间线
```

## Plotloom 概念修正

Plotloom 内部仍然可以保留 storyboard / shot / beat 这类创作结构，但它们不是直接喂给 Seedance 的最终格式。

正确链路应该是：

```text
剧本 / 剧情节拍
  → 导演讲戏本 / director brief
  → Seedance prompt task
  → 视频抽卡候选
```

而不是：

```text
shot list
  → 每个 shot 一条视频生成任务
```

## 关键 Skill：Seedance Prompt Director

Plotloom 应有一个专门 skill：

```text
plotloom-seedance-prompt-director
```

职责是把：

- 剧本
- 导演讲戏本
- 角色参考
- 场景参考
- 台词
- 情绪节奏
- 镜头意图
- 衔接需求

翻译成 Seedance 擅长的连续叙事 prompt。

它不是简单拼接 shot 描述。

## Prompt 示例方向

更接近 Seedance 的 prompt 应像：

```text
以@图片1中的林舟为主角，场景参考@图片3的深夜办公室。15秒电影感短剧开场，冷白办公灯，压抑荒诞氛围。

0-3秒：远景建立，空旷办公室只剩几盏冷白灯，林舟抱着纸箱站在被清空的工位旁，身后大屏滚动“AI 降本增效完成”。镜头从走廊缓慢推入，先给环境，再落到林舟背影。

4-8秒：中景推近，林舟转身看向会议室玻璃门内，CEO 正在直播宣布“从今天起，我们不再需要后端工程师”。玻璃反光里同时出现林舟和屏幕公告，形成压迫感。

9-12秒：切到林舟面部近景，他没有愤怒，只是低头看手机，生产告警通知一条接一条弹出。手机冷光映在眼镜上，他轻声说：“希望 AI 会重启数据库。”

13-15秒：镜头快速切回大屏，直播画面突然卡顿，办公室所有屏幕同时变红，警报声响起。尾帧停在林舟抬头的一瞬间，方便下一段延长衔接。
```

## 对 PRD 的影响

PRD 里应避免把视频生成单位叫做普通 segment / shots bundle。

更合适的术语：

```text
video prompt task
Seedance narrative task
director prompt task
```

每个 task 面向一次模型生成，但内容是连续叙事 prompt。

## 当前共识

Plotloom 的视频生成层应该遵守：

```text
创作单位可以是 beat / scene / shot
模型输入单位必须是适配模型能力的 prompt task
Seedance 适配层应输出单主时间线连续叙事 prompt
不要把 Seedance 当逐镜头 API
```
