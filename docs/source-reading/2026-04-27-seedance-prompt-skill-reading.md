---
title: seedance-prompt-skill 源码/Prompt 解读：Seedance 2.0 的底层提示词规则库
created: 2026-04-27
agent: nova
material_type: source-reading
status: raw
tags:
  - seedance2
  - claude-code-skill
  - prompt-engineering
  - ai-video
  - short-drama
source:
  repo: https://github.com/songguoxs/seedance-prompt-skill
  local_path: /Users/wangguiping/workspace/github/research/seedance-prompt-skill
  commit: 57d1e2f273747c238dd892698a05137ab2f10d4a
related_topics:
  - dramaclaw
  - short-drama-skill-pack
  - Seedance2-Storyboard-Generator
---

# seedance-prompt-skill 源码/Prompt 解读：Seedance 2.0 的底层提示词规则库

## 结论先行

`seedance-prompt-skill` 是一个非常轻的 Claude Code skill 仓库，核心只有一个文件：

```text
.claude/skills/seedance/SKILL.md
```

它不是短剧完整工作流，而是 **Seedance 2.0 / 即梦的视频提示词规则库**。和前一个 `Seedance2-Storyboard-Generator` 相比：

- `Seedance2-Storyboard-Generator` 更像“故事/短剧生产工作流”
- `seedance-prompt-skill` 更像“Seedance prompt 技法手册”

所以它对我们未来做 `drama-short-*` skill pack 的定位应该是：**底层 Seedance prompt reference**，而不是主流程入口。

最值得吸收的是：

1. Seedance 2.0 的平台参数和素材上限
2. `@图片/@视频/@音频` 引用规则
3. 十大 prompt 能力模式
4. 超过 15 秒视频的分段/延长策略
5. 短剧对白、台词、音效的提示词写法
6. 输出格式：简单模式 / 完整模式 / 超长模式

---

## 仓库基本情况

- GitHub: <https://github.com/songguoxs/seedance-prompt-skill>
- 本地路径：`/Users/wangguiping/workspace/github/research/seedance-prompt-skill`
- 当前 commit：`57d1e2f273747c238dd892698a05137ab2f10d4a`
- 仓库体积：约 `204K`
- 文件：4 个

文件结构：

```text
.claude/skills/seedance/SKILL.md
README.md
README_zh.md
.gitignore
```

这说明它是一个非常纯粹的 skill 项目，没有示例项目、没有执行脚本、没有 CLI，也没有复杂 references 拆分。

---

## 核心入口：SKILL.md

`SKILL.md` frontmatter：

```yaml
name: seedance
description: This skill should be used when the user asks to "generate video prompts", ... mentions "Seedance", "即梦", "视频提示词", "视频生成", "AI视频", "短剧", "广告视频", "视频延长"...
version: 2.0.0
```

它的触发范围很宽：任何 Seedance / 即梦 / 视频提示词 / AI 视频 / 短剧 / 广告 / 视频延长相关需求都可触发。

Skill 的自我定位是：

> 专业的 AI 视频提示词工程师，专门为字节跳动即梦平台的 Seedance 2.0 视频生成模型编写高质量中文提示词。

这里有两个关键点：

1. **目标不是生成视频，而是生成可复制到即梦平台的 prompt。**
2. **所有 prompt 必须使用中文。**

这对我们很重要：即使未来有即梦 CLI，skill 层仍应优先产出“人/机器都可读”的中文 prompt，而不是把模型调用参数藏在代码里。

---

## Seedance 2.0 平台约束

Skill 开头直接列出平台参数：

| 输入 | 限制 |
|---|---|
| 图片 | jpeg/png/webp/bmp/tiff/gif，≤9 张，单张 <30MB |
| 视频 | mp4/mov，≤3 个，总时长 2-15 秒，单个 <50MB，分辨率 480p-720p |
| 音频 | mp3/wav，≤3 个，总时长 ≤15 秒，单个 <15MB |
| 混合上限 | 图片 + 视频 + 音频最多 12 个文件 |
| 生成时长 | 4-15 秒 |
| 分辨率 | 支持 2K 输出 |

还有两个关键注意：

- 不支持上传含有写实真人脸部的素材，平台会拦截。
- 视频延长时，生成时长应是“新增部分”的时长。例如延长 5 秒，生成长度也选 5 秒。

这些约束应直接进入我们的 `drama-short-seedance` reference，因为它们会影响 episode 拆分：**单段最大 15 秒，所以 30-45 秒短剧必须拆段。**

---

## @ 引用系统

Skill 明确要求使用官方命名：

```text
@图片1 ... @图片9
@视频1 ... @视频3
@音频1 ... @音频3
```

并且要求每个引用必须说明用途：

```text
@图片1为首帧
参考@视频1的运镜效果
背景音乐参考@音频1
@图片1的人物形象
参考@视频1的打斗动作
```

这点比单纯“上传素材”重要得多。模型不是自动知道每个素材用途，prompt 必须显式区分：

- 角色参考
- 场景参考
- 首帧
- 尾帧
- 运镜参考
- 动作参考
- 声音参考
- 编辑对象

对我们的短剧 skill 来说，`episode.yaml` 里的 asset 应该有 `usage` 字段，例如：

```yaml
references:
  - slot: 图片1
    asset_id: C01
    usage: 角色外观参考
  - slot: 图片2
    asset_id: S01
    usage: 场景背景参考
  - slot: 视频1
    asset_id: V01
    usage: 延长上一段视频
```

---

## 十大 Prompt 能力模式

Skill 将 Seedance 2.0 的使用方式整理成十种能力。

### 1. 纯文本生成

模式：

```text
主体描述 + 动作序列 + 环境/光影 + 镜头语言 + 风格关键词
```

适合没有素材时快速生成，但短剧生产里只能作为兜底，因为角色一致性不稳定。

### 2. 一致性控制

模式：

```text
[角色]@图片N + [动作/剧情描述] + [场景]@图片N + [运镜/光影]
```

这是短剧里最关键的模式。角色和场景必须通过图片引用建立一致性。

### 3. 运镜与动作精准复刻

模式：

```text
参考@视频1的[运镜/动作/节奏] + [主体]@图片N + [场景描述]
```

这说明参考视频的价值不是“剧情参考”，而是可拆成：运镜、动作、节奏、表情、特效等不同用途。

### 4. 创意模板 / 特效复刻

模式：

```text
参考@视频1的[特效/转场/创意] + 将[元素]替换为@图片N + [补充说明]
```

适合广告、转场、热门模板复刻。对短剧测试不是 MVP 主线，但以后可用于“爆款短视频模板化”。

### 5. 剧情创作 / 补全

模式：

```text
[分镜脚本/图片内容描述] + [演绎方式] + [音效/台词要求]
```

这和前一个项目互补：前一个项目产出分镜脚本，这个 skill 提供把分镜转为 Seedance prompt 的底层写法。

### 6. 视频延长

模式：

```text
将@视频1延长[X]s + [新增内容描述]
延长@视频1 + [详细的画面分段描述]
向前延长[X]s + [前置剧情描述]
```

这是 30-45 秒短剧的关键。我们不应该一次 prompt 45 秒，而应：

```text
第1段：正常生成 ≤15秒
第2段：将@视频1延长15秒
第3段：将@视频1延长15秒
```

每段都必须有“衔接点”。

### 7. 声音控制

模式：

```text
[画面描述] + 音色/旁白参考@视频1 + [台词内容用引号标注]
```

Skill 特别强调台词用引号，并标注角色和情绪。短剧是强对白品类，这个规则要保留。

### 8. 一镜到底

模式：

```text
一镜到底 + @图片1@图片2@图片3... + [连续场景描述] + 全程不要切镜头
```

对短剧未必第一版需要，但“全程不要切镜头”这种硬约束写法值得保留。

### 9. 视频编辑

模式：

```text
将@视频1中的[A]换成@图片1 + [其他修改说明]
颠覆@视频1的剧情 + [新剧情描述]
```

这不是稳定主链路，更适合局部改稿。MVP 不应把它当核心。

### 10. 音乐卡点

模式：

```text
@图片1@图片2...@图片N + 参考@视频1的画面节奏/卡点 + [画面风格说明]
```

偏 MV/广告/社媒模板，不是短剧 MVP 主线。

---

## 高级提示词技巧

### 时间戳分镜法

对于 13-15 秒视频，skill 推荐使用时间戳：

```text
0-3秒：[画面描述 + 镜头语言]
4-8秒：[画面描述 + 镜头语言]
9-12秒：[画面描述 + 镜头语言]
13-15秒：[画面描述 + 镜头语言]
```

它的短剧示例是：

```text
画面（0-5秒）：特写女主撕契约镜头...
台词1（总裁，卑微慌乱）：...
画面（6-10秒）：女主抬脚避开他的手...
台词2（女主，冷漠反杀）：...
画面（11-15秒）：总裁僵在原地...
音效：...
时长：精准15秒
```

这个格式比前一个项目的“0-3 / 3-6 / 6-9 / 9-12 / 12-15”更适合现代短剧对白场景，因为它允许画面和台词分离。

### 技术参数指定法

Skill 建议在 prompt 开头明确：

```text
[尺寸]竖屏/横屏 + [画幅比] + [帧率] + [时长] + [色调/风格总纲]
```

例如：

```text
2.35:1，24fps，15秒，8镜头硬切
霓虹高饱和冷暖对比，现代舞台
浅景深突出动作，动作清晰，运动模糊真实
声音设计优先...
禁止文字logo水印
```

这个对执行很重要：视频模型如果不先定“规格总纲”，后续描述容易漂。

### 禁止项声明

Skill 建议在末尾加：

```text
禁止：
- 任何文字、字幕、LOGO或水印
- 不允许出现XXX
- 画面全部片段都不要出现字幕
```

对短剧要谨慎：如果视频平台后期会叠字幕，那生成阶段应禁止模型自己生成字幕；否则后期字幕和画面内伪文字会冲突。

---

## 超长视频分段拼接策略

这是这个 skill 对我们最有价值的一段。

Seedance 单次生成上限 15 秒，所以 >15 秒要拆分：

```text
1. 将总时长按叙事节奏切分为多个片段，每段 ≤15 秒
2. 每段之间必须有画面衔接点：上一段结尾状态 = 下一段开始状态
3. 第一段正常生成，后续每段使用“将@视频1延长Xs”
4. 每段标注清楚属于整体第几段、承接内容是什么
```

分段建议：

| 总时长 | 推荐分段 |
|---|---|
| 16-30 秒 | 2 段 |
| 31-45 秒 | 3 段 |
| 46-60 秒 | 4 段 |
| >60 秒 | 建议拆成独立场景再剪辑 |

这正好对应我们的第一批目标：30-45 秒短剧开头。也就是说，我们应该默认：

```text
30秒：2段
45秒：3段
```

每段需要独立产出：

```yaml
clips:
  - id: clip01
    mode: normal
    duration: 15
    prompt: ...
    end_frame: ...
  - id: clip02
    mode: extend
    input_video: clip01
    duration: 15
    prompt: 将@视频1延长15秒...
    end_frame: ...
```

---

## 输出模式设计

Skill 定义了三种输出格式：

### 简单模式

用户目标明确，且 ≤15 秒：直接输出可复制 prompt + 素材准备建议。

### 完整模式

需要探索创意方向，且 ≤15 秒：输出 2-3 个版本：

```text
## 视频提示词
主题 / 时长 / 比例
公共参考素材
版本一
  提示词
  参考素材
版本二
  提示词
  参考素材
提示词解析
```

### 超长模式

>15 秒：使用分段拼接策略，每段有独立 prompt 和衔接点。

这个设计对我们的 skill pack 有启发：

- `drama-short-create` 可以先生成 2-3 个“创意版本”
- 选中后再进入 `drama-short-seedance` 生成分段 prompt
- 分段 prompt 必须进入 manifest，而不只是在聊天里展示

---

## 这个项目与前一个项目的关系

两个项目刚好互补。

| 维度 | Seedance2-Storyboard-Generator | seedance-prompt-skill |
|---|---|---|
| 定位 | 故事/小说 → 剧本/素材/分镜 | 即梦/Seedance prompt 技法库 |
| 粒度 | 项目级 / 多集级 | 单条 prompt / 单能力模式 |
| 产物 | 剧本、素材清单、E01 分镜 | 可复制提示词、多版本方案 |
| 强项 | 工作流、资产编号、示例项目 | 平台约束、@引用、延长、短剧对白 |
| 弱项 | 没有执行层、prompt 规则分散 | 没有故事生产链、没有样例项目 |

因此我们不应二选一，而应合并抽象：

```text
上层：短剧创作/分镜 workflow ← 学 Seedance2-Storyboard-Generator
下层：Seedance prompt 编译规则 ← 学 seedance-prompt-skill
执行层：imagegen2 / 即梦 CLI / ffmpeg / manifest ← 我们自己补
```

---

## 可直接吸收进 Dramaclaw 的规则

### 1. Prompt 编译前必须明确素材用途

不能只写：

```text
@图片1 @图片2 @视频1
```

必须写：

```text
@图片1为男主角色外观参考
@图片2为凌晨办公室场景参考
@视频1为上一段视频，用于延长衔接
```

### 2. 30-45 秒短剧默认分段

```text
30秒 → 2段，每段约15秒
45秒 → 3段，每段约15秒
```

第一段正常生成，后续段使用视频延长。

### 3. 短剧对白要画面/台词分开

适合格式：

```text
画面（0-5秒）：...
台词1（角色，情绪）："..."
画面（6-10秒）：...
台词2（角色，情绪）："..."
音效：...
```

比把台词揉在画面描述里更清晰。

### 4. 禁止生成画面内字幕/水印

如果最终字幕由 ffmpeg/后期加，Seedance prompt 应加：

```text
禁止出现任何文字、字幕、LOGO、水印
```

但如果故意要手机聊天记录、系统弹窗、公司公告这类画面内文字，则需要显式例外。

### 5. 输出应保留多个版本

前期创意探索时可以生成 2-3 个版本，但进入生产后必须收敛为一个 selected version，并写入 manifest。

---

## 不适合直接照搬的地方

1. **它只生成 prompt，不管理产物。**
   - 没有 episode spec、没有 manifest、没有输出目录。

2. **所有逻辑塞在一个 SKILL.md。**
   - 对小项目可行，但我们后续应拆 references，否则 skill 会越来越难维护。

3. **它偏泛化能力枚举。**
   - 十大能力覆盖广告、科普、MV、视频编辑等。
   - 我们第一版只做短剧测试，不应继承这么宽的触发范围。

4. **缺少失败反馈机制。**
   - 没有记录生成失败、敏感词、角色漂移、动作崩坏等结果。
   - 我们应在 manifest 里记录 retries / failure_reason / selected_output。

---

## 对我们的下一步启发

如果把它抽到我们的 skill pack，建议变成一个底层 reference：

```text
skills/drama-short-seedance/SKILL.md
skills/drama-short-seedance/references/seedance-platform-limits.md
skills/drama-short-seedance/references/seedance-prompt-patterns.md
skills/drama-short-seedance/references/short-drama-dialogue-patterns.md
```

其中 `seedance-prompt-patterns.md` 可以吸收：

- 纯文本生成
- 一致性控制
- 运镜/动作复刻
- 视频延长
- 声音控制
- 时间戳分镜
- 技术参数指定
- 禁止项声明

但主入口 skill 不应叫 `seedance`，而应叫：

```text
drama-short-seedance
```

因为我们的任务不是“帮用户写任意 Seedance prompt”，而是“把短剧 episode/shots 编译成 Seedance 可执行 prompt”。

---

## 总评

`seedance-prompt-skill` 是一个小而完整的 Seedance 2.0 prompt 技法库。它没有完整短剧工作流，但把平台约束、@引用、多模态能力、视频延长和短剧对白写法整理得很清楚。

对 Dramaclaw / short-drama skill pack 来说，它应该扮演 **prompt compiler reference**：

```text
episode.yaml / shots.yaml
  ↓
drama-short-seedance skill
  ↓
Seedance 2.0 分段 prompt + 素材槽映射 + 衔接点
```

一句话：

> 第一个项目教我们“短剧怎么拆”；第二个项目教我们“拆完怎么喂给 Seedance”。
