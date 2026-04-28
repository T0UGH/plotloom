---
title: Seedance2-Storyboard-Generator 源码/Prompt 解读：一个以 Skill 为核心的短剧分镜工作流
created: 2026-04-27
agent: nova
material_type: source-reading
status: raw
tags:
  - seedance2
  - claude-code-skill
  - ai-short-drama
  - prompt-engineering
  - storyboard
source:
  repo: https://github.com/liangdabiao/Seedance2-Storyboard-Generator
  local_path: /Users/wangguiping/workspace/github/research/Seedance2-Storyboard-Generator
  commit: d9b6657e71398ff99b911297ef344dc0d7ccbe7d
related_topics:
  - dramaclaw
  - videoclaw
  - short-drama-skill-pack
---

# Seedance2-Storyboard-Generator 源码/Prompt 解读：一个以 Skill 为核心的短剧分镜工作流

## 结论先行

`Seedance2-Storyboard-Generator` 不是传统意义上的代码库，几乎没有可执行程序；它本质上是一个 **Claude Code Skill + Prompt 参考资料 + 示例项目资产库**。

它对我们做 `drama-short-*` / Dramaclaw 类短剧生产 skill 的价值很高，因为它已经把“故事/小说 → 剧本 → 素材清单 → Seedance 2.0 分镜 prompt”的工作流固化成了可复制的文本协议。

它最值得复用的不是仓库结构，而是三件事：

1. **Skill 作为产品心智**：把流程、格式、质量标准和常见坑写进 `SKILL.md`。
2. **资产编号体系**：用 `C/S/P` 管角色、场景、道具，降低多集分镜里的引用混乱。
3. **双层产物结构**：先写“剧本正文”，再把剧本转成 Seedance 可执行的 15 秒时间轴 prompt。

它不足的地方也明显：没有真实 CLI 执行层、没有 manifest/产物账本、没有自动调用生图/视频工具、没有可验证的端到端生成闭环。对我们来说，它更像 **上游创作与分镜规范**，不是完整生产流水线。

---

## 仓库基本情况

- GitHub: <https://github.com/liangdabiao/Seedance2-Storyboard-Generator>
- 本地路径：`/Users/wangguiping/workspace/github/research/Seedance2-Storyboard-Generator`
- 当前 commit：`d9b6657e71398ff99b911297ef344dc0d7ccbe7d`
- 仓库体积：约 `131M`
- 文件构成：约 100 个文件，其中 Markdown 82 个，另有少量 png/jpeg 示例素材。

它的主要内容不是源码，而是：

```text
.claude/skills/seedance-storyboard-generator/SKILL.md
.claude/skills/seedance-storyboard-generator/references/*.md
CLAUDE.md
README.md
docs/*.md
多个示例项目/
  *_剧本.md
  *_素材清单.md
  *_E01_分镜.md
  *_E02_分镜.md
  ...
```

示例项目包括：

- 林冲 / 风雪山神庙
- 武松打虎
- 草船借箭
- 司马光砸缸
- 鲁智深酒后寺庙闯祸
- 崖山海战
- 聂风篇
- 项链

这说明作者不是只写一个 prompt，而是在积累一套可复用的“故事转视频”样例语料。

---

## 核心入口：Skill.md

核心文件：

```text
.claude/skills/seedance-storyboard-generator/SKILL.md
```

frontmatter 里的 description 很长，实际上已经定义了产品定位：

> 专业的 Seedance 2.0 平台 AI 视频脚本和分镜生成器。用于：文章/故事转视频脚本、生成 Seedance 分镜提示词、规划多集 AI 视频系列、为图像模型创建角色/场景/道具生成提示词。

这个 skill 的 workflow 分 5 步：

```text
1. 分析输入
2. 确认制作参数
3. 生成完整剧本结构
4. 创建资产生成计划
5. 生成 Seedance 2.0 分镜脚本
```

这和我们之前讨论的“skill 是产品心智，CLI 只是执行器”高度一致。这里没有 CLI，却已经能完成最重要的创作编排。

---

## 工作流拆解

### 1. 输入分析

Skill 先判断输入类型：

- 完整文本：小说、文章、历史事件，需要改编和分集。
- 大纲：简短故事概念，需要扩写成完整脚本。

然后提取：

- 主角和关键角色
- 核心冲突和叙事弧线
- 场景/世界观元素
- 关键情节和情感节拍
- 核心梗/卖点

这里重要的是：它没有直接跳到“写 Seedance prompt”，而是先做故事结构分析。对短剧来说这是对的，因为 15 秒 prompt 只是末端表达，前面必须先有“钩子、冲突、升级、反转/释放”。

### 2. 制作参数确认

Skill 明确要求确认：

1. 视觉风格：写实 / 动画 / 水墨 / 科幻 / 复古 / 电影感等
2. 总时长：默认短剧 `5集 × 15秒 ≈ 75秒`
3. 画幅比例：16:9 / 9:16 / 2.35:1
4. 情绪基调：史诗 / 温馨 / 悬疑 / 欢快 / 忧伤等
5. 核心梗：绝境反杀 / 复仇爽剧 / 治愈温馨 / 悬疑惊悚等

这个阶段值得我们复用，但需要改造：我们的第一批测试是 **5 条 30-45 秒短剧开头**，不是 5 集连续剧，所以应该把“制作参数确认”压缩为：

```text
题材类型 / 目标时长 / 画幅 / 角色风格 / 3秒钩子 / 追更钩子 / 生成工具链
```

### 3. 剧本结构

Skill 要求输出一个标准剧本文件：

```text
# [Title] - 剧本

一、核心梗
二、故事梗概
三、一句话卖点
四、人物小传
五、剧本大纲
六、剧本正文
```

其中人物小传格式很具体：

```text
角色名
视觉形象：[Age, appearance details, clothing, key visual markers]
身份背景：[Social role, background, relationship to protagonist]
核心标签：[2-4 character traits]
性格特点：[Detailed personality description, arc transformation]
金句：[Memorable line]
```

剧本正文的核心格式是每个镜头以 `△` 开头：

```text
第X集
X-X [日/夜] [内/外] [场景名称]
道具：[List key props]
出场人物：[List characters in scene]

△ 【空镜/开场镜头】...
△ [Shot 2 description with specific camera movement]
角色名（os）：...
角色名（对白/动作描述）：...
【字幕：xxx】...
△ 【闪回】...
【闪回结束】
```

这个 `△` 格式很实用：它把“剧本语言”和“分镜镜头”区分开，方便后续解析或人工检查。我们未来如果做 `episode.yaml`，可以把它转成结构化字段：

```yaml
shots:
  - id: s01
    script_line: "△ ..."
    camera: "推镜头"
    dialogue: []
    duration: 3
```

### 4. 资产生成计划

这是这个项目最有价值的设计之一。

它将所有视觉资产编号：

| 类别 | 前缀 | 示例 | 描述 |
|---|---|---|---|
| 角色 | C01-C99 | C01 林冲·正面全身 | 每个角色多个角度 |
| 场景 | S01-S99 | S01 沧州草料场·雪景 | 关键位置 |
| 道具 | P01-P99 | P01 长枪 | 重要物品 |

素材清单示例：

```text
### C01 — 林冲·正面全身立绘
Chinese ink wash painting style mixed with anime cel-shading, a heroic Chinese warrior standing...

### S01 — 沧州草料场·大雪全景
Chinese ink wash painting style mixed with anime cel-shading, panoramic landscape...
```

`林冲项目/林教头风雪山神庙_素材清单.md` 里有一个完整例子：

- 角色：C01-C07
- 场景：S01-S06
- 道具：P01-P05
- 每个素材都使用统一风格前缀：`Chinese ink wash painting style mixed with anime cel-shading`
- 最后有素材编号总览，标注“用于集数”

这个设计直接解决短剧生成里的大问题：**角色/场景一致性和引用可追踪性**。

但它仍然是 Markdown 表格和自然语言 prompt；如果我们要接 imagegen2 / 即梦 CLI，应该升级为机器可读结构：

```yaml
assets:
  characters:
    - id: C01
      name: 林冲·正面全身立绘
      prompt: ...
      role: character_reference
      used_by: [shot01, shot02]
  scenes:
    - id: S01
      name: 沧州草料场·大雪全景
      prompt: ...
```

### 5. Seedance 分镜脚本

每集分镜文件一般包含三部分：

```text
## 素材上传清单
## Seedance Prompt
## 尾帧描述
```

典型结构：

```text
水墨武侠动漫风格，9:16竖屏，灰白墨黑色调，孤寂压抑氛围

0-3秒画面：...
3-6秒画面：...
6-9秒画面：...
9-12秒画面：...
12-15秒画面：...

【声音】寒风呼啸环境音 + 凄清的二胡独奏 + 雪花飘落的细微声响
【参考】@图片1 林冲角色参考，@图片2 尾帧背影参考，@图片3 草料场场景...
```

这里的关键是：它固定按 15 秒拆成五段，每段 3 秒左右。这种结构非常适合 Seedance 2.0，但对我们要做的 30-45 秒短剧开头，需要变成：

```text
0-3s：一句强钩子
3-15s：冲突建立
15-30s：问题升级
30-40s：反转打脸
40-45s：追更钩子
```

也就是说，它的“15秒单集”节奏可以复用为一个 shot/clip 单元，但我们的 episode 层需要更长的短剧结构。

---

## References 的设计

Skill 的 references 目录很重要：

```text
references/seedance-manual.md
references/优化分镜.md
references/好剧本.md
references/故事转视频脚本-转换工具.md
```

它把主 skill 之外的长知识拆到 reference 里，避免 `SKILL.md` 变成无法维护的百科。

### `好剧本.md`

这个文件其实是“好剧本标准样例”。它用林冲风雪山神庙展示：

- 核心梗
- 故事梗概
- 一句话卖点
- 人物小传
- 剧本大纲
- 剧本正文

它最重要的作用是给模型一个完整的正例。尤其是 `△` 镜头格式、OS/VO 标注、闪回、字幕等，都通过样例让模型模仿。

### `故事转视频脚本-转换工具.md`

这是一个更系统的“转换器说明书”。它把故事转换拆为：

1. 核心梗与故事分析
2. 人物小传构建
3. 剧本大纲（起承转合）
4. 剧本正文撰写
5. 15 秒集数节奏控制
6. 视觉与听觉设计

它里面的几个公式值得直接吸收：

- 一句话卖点公式：`情绪号召 + 核心冲突 + 视觉高潮画面`
- 人物小传公式：`年龄 + 外貌 + 服装 + 标志性动作/道具`
- 每集情绪弧线：`0-3 建立 → 3-9 上升 → 9-12 高潮 → 12-15 释放/悬念`
- 尾帧描述必须详细，用于下一集衔接

### `优化分镜.md`

这个文件更像 Seedance prompt 的压缩速查表：

```text
主体 + 动作 + 场景 + 光影 + 镜头语言 + 风格 + 画质 + 约束
```

它强调一个实际经验：

> 动作描述要写“慢”，越慢越稳；避免“夸张”“高速”“剧烈扭动”这类词，容易导致画面崩坏。

这对视频模型 prompt 很重要。短剧里很多动作如果写得过猛，模型会失控。我们自己的 skill 应该把“动作复杂度控制”写进质量检查。

### `seedance-manual.md` / `docs/structured-prompt.md`

这些文件提供了 Seedance 2.0 的能力边界：

- 图片 ≤ 9 张
- 视频 ≤ 3 个，总时长 ≤ 15s
- 音频 ≤ 3 个，总时长 ≤ 15s
- 总文件数 ≤ 12
- 支持 `@图片1`、`@视频1`、`@音频1`
- 不支持写实真人脸部素材
- 支持视频延长、视频编辑、参考运镜、参考动作、参考声音

这些应作为我们后续 `drama-short-seedance` reference 的底层约束。

---

## 示例项目如何组织

以林冲项目为例：

```text
林冲项目/
  林教头风雪山神庙_剧本.md
  林教头风雪山神庙_素材清单.md
  林教头风雪山神庙_E01_分镜.md
  林教头风雪山神庙_E02_分镜.md
  ...
```

每个项目的产物层次都比较稳定：

1. `*_剧本.md`：故事层 / 叙事层
2. `*_素材清单.md`：视觉资产层
3. `*_E01_分镜.md`：Seedance 执行层
4. `使用指南.md`：人工执行说明

这其实已经是一个手工版 manifest，只是没有机器可读化。

### 示例：林冲 E01

`林教头风雪山神庙_E01_分镜.md`：

- 素材槽：@图片1=C01，@图片2=C02，@图片3=S01，@图片4=P01，@图片5=P04
- 时间轴：0-3 高空俯拍，3-6 主体引入，6-9 面部特写，9-12 环绕孤影，12-15 拉远尾帧
- 声音：寒风 + 二胡 + 雪花声
- 尾帧：林冲背影消失在风雪中

这个例子展示了一个好的单集 Seedance prompt 必须同时回答：

```text
用哪些素材？
每个素材在 prompt 里怎么引用？
每 3 秒画面是什么？
声音是什么？
最后一帧是什么？
下一集怎么接？
```

---

## 这个项目的“源码”本质：Prompt-as-code

这个仓库没有传统代码，但它依然有工程结构：

| 传统软件概念 | 本仓库对应物 |
|---|---|
| 程序入口 | `.claude/skills/.../SKILL.md` |
| 库函数/模块 | `references/*.md` |
| 测试样例 | 各示例项目的剧本/素材/分镜 |
| 数据模型 | C/S/P 编号、剧本格式、分镜格式 |
| 编译目标 | 可粘贴到 Seedance 2.0 的 prompt |
| 运行时 | Claude Code + 图像模型 + 即梦/Seedance 平台 |

所以阅读这个项目不能按“函数调用链”读，而要按“文本协议和产物转换链”读。

它的核心调用链可以抽象为：

```text
用户故事/小说
  ↓
Skill: 分析核心梗、角色、冲突、情绪弧
  ↓
剧本.md：故事结构 + 人物小传 + △镜头正文
  ↓
素材清单.md：C/S/P 编号 + 图像 prompt
  ↓
E01_分镜.md：素材槽映射 + 15秒 Seedance 时间轴 + 尾帧
  ↓
人工上传素材到 Seedance / 即梦生成视频
```

---

## 可直接复用的设计

### 1. Skill-first 结构

我们做短剧生产工具时，不应该先写大 CLI。可以先像这个项目一样，把“怎么做短剧”写成 skill：

```text
skills/drama-short-create/SKILL.md
skills/drama-short-create/references/short-drama-beats.md
skills/drama-short-create/references/seedance-rules.md
skills/drama-short-create/references/imagegen2-prompts.md
```

CLI 只在需要批量执行时补上。

### 2. 资产编号体系

`C/S/P` 非常值得保留：

- `C`：Character，角色图 / 角色锚点
- `S`：Scene，场景图
- `P`：Prop，道具图

但我们应扩展：

- `K`：Keyframe，首尾帧 / 关键帧
- `V`：Video clip，生成的视频片段
- `A`：Audio，配音 / 音效 / BGM

### 3. 尾帧描述

尾帧描述是多集衔接的关键。即使我们第一版只做 30-45 秒单条短剧，也应该保留：

```yaml
ending_frame:
  subject: ...
  background: ...
  lighting: ...
  composition: ...
  mood: ...
  next_hook: ...
```

这有助于后续做追更集、视频延长和续集。

### 4. 质量检查清单

Skill 里的 QA checklist 值得吸收：

- 资产引用是否都存在
- 时间轴是否覆盖完整时长
- 相机运动是否可执行
- 对白是否正确标注
- 是否有感官细节
- 是否有情绪弧线
- 是否记录尾帧

这可以变成我们自己的 `drama-short-review` skill。

---

## 需要改造的地方

### 1. 从“多集 15 秒”改为“单条 30-45 秒短剧开头”

原项目默认：

```text
5集 × 15秒 ≈ 75秒
每集 0-3 / 3-6 / 6-9 / 9-12 / 12-15
```

我们的第一批目标：

```text
0-3s：一句强钩子
3-15s：冲突建立
15-30s：问题升级
30-40s：反转打脸
40-45s：一句追更钩子
```

因此我们不能照搬“每集 15 秒”结构，而应把它当成 clip 单元，组合成 3-5 个 clips。

### 2. 从 Markdown 产物升级为 `episode.yaml`

原项目产物适合人工复制粘贴，不适合自动执行。

我们需要：

```text
episode.yaml
  → script.md
  → assets.yaml / prompts.yaml
  → shots.yaml
  → manifest.json
```

其中 `episode.yaml` 不是用户必须手写，而是 skill 生成和维护的中间协议。

### 3. 接入 imagegen2 / 即梦 CLI / ffmpeg

原项目停在“生成 prompt”。没有负责：

- 调 imagegen2 生成图
- 调即梦 CLI 生成视频
- 下载/管理视频片段
- ffmpeg 合成 final.mp4
- 写 manifest

这正是我们要补的执行层。

### 4. 从长故事改编转向强钩子短剧

原项目多是历史/文学故事改编，强调完整叙事和情绪弧。我们的短剧测试更偏：

- 3 秒停留
- 冲突密度
- 评论欲
- 追更钩子
- 角色记忆点

所以 skill 的剧作 reference 需要新增“短剧开头模板”，不能只用四幕式。

---

## 不适合直接继承的部分

1. **Nana Banana Pro 绑定**
   - 原项目默认 Nana Banana Pro 做图像素材。
   - 我们当前边界是 imagegen2，所以应抽出“图像 prompt 规范”，不要绑定工具。

2. **Markdown-only 执行链**
   - 适合学习，不适合批量生产。
   - 我们需要最小 manifest 和路径约定。

3. **过长复杂 prompt**
   - 原项目有些 prompt 很细，可能超过 Seedance 稳定执行范围。
   - 参考文档自己也说复杂提示词 300+ 字可能不稳定。
   - 我们应加入“短 prompt / 单镜头单动作 / 慢动作优先”的压缩规则。

4. **缺少真实验收闭环**
   - 没有记录每次生成的视频质量、失败原因、敏感词、重试参数。
   - 对生产工具来说，缺 manifest 是明显短板。

---

## 对 Dramaclaw / drama-short skill pack 的启发

基于这个仓库，建议我们的第一版 skill pack 不要做大而全，而是分层：

```text
drama-short-create
  主入口：从题材/一句话想法生成 30-45 秒短剧开头方案

drama-short-script
  负责短剧钩子、冲突、反转、追更结构

drama-short-assets
  负责 C/S/P/K 资产编号和 imagegen2 prompt

drama-short-seedance
  负责把 shots 转成 Seedance/即梦 prompt

drama-short-review
  负责检查钩子、资产引用、时间轴、动作复杂度、尾帧、可执行性
```

如果要保留执行层，再加很薄的脚本或 CLI：

```text
drama-short-exec
  mkdir output dirs
  call imagegen2
  call jimeng/seedance cli
  call ffmpeg
  write manifest.json
```

关键是：**创作判断放在 skill，机械执行放在工具。**

---

## 初步映射到我们的 5 条短剧测试

这个项目的范式可以这样迁移：

| 原项目 | 我们的短剧测试 |
|---|---|
| 核心梗 | 题材钩子：AI职场/仙侠/末世/夜店悬疑/外卖逆袭 |
| 人物小传 | 主角/对手/美女角色/AI系统等角色锚点 |
| C/S/P 资产清单 | imagegen2 生成角色图、场景图、封面图 |
| 每集 15 秒 prompt | 每条短剧拆为 3-5 个 Seedance clips |
| 尾帧描述 | 追更钩子与下一条开场衔接 |
| 使用指南 | manifest + 操作日志 + 重试记录 |

例如 AI 职场黑色幽默可以有：

```text
C01 最后一个后端工程师
C02 冷漠 HR
C03 公司 AI 系统人格化屏幕/机器人
S01 凌晨三点办公室
S02 空荡工位区
P01 服务器报警屏幕
K01 AI 建议关闭公司的一刻
```

Seedance prompt 不应一次写 45 秒，而应拆成：

```text
clip01 0-8s：公司宣布裁掉最后一个后端
clip02 8-18s：系统报警无人处理
clip03 18-30s：AI 发现公司全靠这个后端维持
clip04 30-40s：AI 建议关闭公司
clip05 40-45s：追更钩子 / 评论钩子
```

---

## 总评

`Seedance2-Storyboard-Generator` 是一个典型的 **Prompt-as-code / Skill-as-product** 项目。

它没有解决执行自动化，但它已经把短剧/漫剧生产里最难标准化的一部分——剧本结构、资产编号、Seedance 分镜格式、质量检查——做成了可学习的文本协议。

对我们来说，最优策略不是 fork 后直接改，而是：

1. 吸收它的 workflow 和 C/S/P 资产编号。
2. 把 15 秒集数结构改造成 30-45 秒短剧开头结构。
3. 把 Markdown 产物升级成 `episode.yaml` / `shots.yaml` / `manifest.json`。
4. 再接 imagegen2、即梦 CLI 和 ffmpeg 执行层。

一句话：

> 这个项目证明了短剧生产的第一层不是 CLI，而是 skill；CLI 只是把 skill 产出的协议跑起来。
