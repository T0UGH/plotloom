---
title: awesome-gpt-image-2 源码/Prompt 解读：GPT Image 2 图像 Prompt 语料库与自动 README 生成器
created: 2026-04-27
agent: nova
material_type: source-reading
status: raw
tags:
  - gpt-image-2
  - image-gen-2
  - prompt-engineering
  - ai-image
  - short-drama
source:
  repo: https://github.com/YouMind-OpenLab/awesome-gpt-image-2
  local_path: /Users/wangguiping/workspace/github/research/awesome-gpt-image-2
  commit: 1efb64641fc9a0d814b38427b0c0096bf4e1d64d
related_topics:
  - dramaclaw
  - imagegen2
  - short-drama-skill-pack
  - seedance2
---

# awesome-gpt-image-2 源码/Prompt 解读：GPT Image 2 图像 Prompt 语料库与自动 README 生成器

## 结论先行

`awesome-gpt-image-2` 是一个面向 **GPT Image 2 / image-gen-2** 的社区 prompt 语料库。它不是 skill，也不是生成工具，而是一个 **CMS 同步 + 多语言 README 自动生成 + 图像 prompt 展示** 的 awesome-list 型仓库。

它对我们做短剧生产流水线的价值主要在 **image prompt 参考层**：

1. 学 GPT Image 2 擅长什么：文字渲染、跨图一致性、商业级插画、故事板/产品系列、多语言设计。
2. 学图像 prompt 的结构：JSON 化结构、Raycast 参数化、场景/构图/文案/布局/样式/限制的显式拆分。
3. 借它的分类体系：Profile、Social Post、Infographic、YouTube Thumbnail、Comic/Storyboard、Product Marketing、E-commerce、Game Asset 等。
4. 为短剧资产生成提供素材 prompt 模板：角色定妆、封面图、分镜图、图文海报、短剧宣传图。

但它不提供：

- imagegen2 CLI 调用方式
- Claude Code skill 工作流
- 短剧资产一致性协议
- manifest / 产物账本
- 从 episode.yaml 到图像 prompt 的编译规则

所以它更适合被抽成 `drama-short-image-prompts` 的参考语料，而不是直接作为主项目。

---

## 仓库基本情况

- GitHub: <https://github.com/YouMind-OpenLab/awesome-gpt-image-2>
- 本地路径：`/Users/wangguiping/workspace/github/research/awesome-gpt-image-2`
- 当前 commit：`1efb64641fc9a0d814b38427b0c0096bf4e1d64d`
- 仓库体积：约 `35M`
- README 统计：`2717` prompts，`6` featured prompts
- README 最近更新时间：2026-04-27 13:15 UTC 左右

文件结构：

```text
README.md
README_zh.md
README_*.md                 # 多语言 README，共 16+ 种语言
docs/FAQ.md
docs/CONTRIBUTING.md
docs/LOCAL_DEVELOPMENT.md
.github/ISSUE_TEMPLATE/submit-prompt.yml
.github/workflows/update-readme.yml
scripts/generate-readme.ts
scripts/sync-approved-to-cms.ts
scripts/utils/cms-client.ts
scripts/utils/markdown-generator.ts
scripts/utils/i18n.ts
public/images/gpt-image-2-prompts-cover-en.png
public/images/gpt-image-2-prompts-cover-zh.png
```

这个仓库的“源码”主要是 README 生成脚本，不是 prompt 生成器。

---

## 这个仓库到底做什么

它从 YouMind 的 CMS 拉取 prompt 数据，按多语言生成 README：

```text
CMS prompt data
  ↓
scripts/sync-approved-to-cms.ts / cms-client.ts
  ↓
scripts/generate-readme.ts
  ↓
scripts/utils/markdown-generator.ts
  ↓
README.md / README_zh.md / README_ja-JP.md / ...
```

`package.json` 里只有两个主要命令：

```json
{
  "scripts": {
    "generate": "tsx scripts/generate-readme.ts",
    "sync": "tsx scripts/sync-approved-to-cms.ts"
  }
}
```

`generate-readme.ts` 的逻辑很清楚：

1. 遍历 `SUPPORTED_LANGUAGES`
2. 从 CMS 拉 categories
3. 从 CMS 拉 prompts
4. 排序
5. 生成 Markdown
6. 写入对应语言的 README

因此这个项目本质上是一个 **prompt 展示与分发仓库**，不是离线完整数据库。README 里只展示部分 prompt；完整语料和图片主要在 youmind.com / CMS。

---

## GPT Image 2 能力定位

README 对 GPT Image 2 的社区能力判断：

- **Pixel-Perfect Text Rendering**：中文、英文、日文等文字渲染更稳定。
- **Cross-Image Consistency**：同一角色、风格、IP 在系列图中保持一致。
- **Commercial-Grade Illustration**：商业级插画可直接使用。
- **True Art Style Induction**：能更自然地诱导风格，而不只是粗糙模仿。
- **Storyboard & Product Series**：适合故事板、IP 角色、多面板产品视觉。
- **Multi-Language Design**：适合社媒卡片、banner、poster 里的多语言排版。

这些能力刚好命中短剧生产的图像侧需求：

```text
角色定妆照
场景参考图
关键帧 / 首尾帧
分镜 storyboard
封面图 / 海报图
小红书图文卡片
```

尤其是“文字渲染”和“系列一致性”：短剧封面经常需要大字标题，角色图又需要多集一致性，GPT Image 2 可能比普通生图模型更适合作为前期视觉资产生成器。

> 注意：`docs/FAQ.md` 第 7 行写成 “GPT Image 2 is Google's latest multimodal AI model”，这和 README 主文里的 OpenAI GPT Image 2 定位冲突，应该是文档复制/维护错误。后续引用时应以 README 主文和仓库名为准。

---

## 分类体系

README 的分类分三层：Use Cases、Style、Subjects。

### Use Cases

- Profile / Avatar
- Social Media Post
- Infographic / Edu Visual
- YouTube Thumbnail
- Comic / Storyboard
- Product Marketing
- E-commerce Main Image
- Game Asset
- Poster / Flyer
- App / Web Design

### Style

- Photography
- Cinematic / Film Still
- Anime / Manga
- Illustration
- Sketch / Line Art
- Comic / Graphic Novel
- 3D Render
- Chibi / Q-Style
- Isometric
- Pixel Art
- Oil Painting
- Watercolor
- Ink / Chinese Style
- Retro / Vintage
- Cyberpunk / Sci-Fi
- Minimalism

### Subjects

- Portrait / Selfie
- Influencer / Model
- Character
- Group / Couple
- Product
- Food / Drink
- Fashion Item
- Animal / Creature
- Vehicle
- Architecture / Interior
- Landscape / Nature
- Cityscape / Street
- Diagram / Chart
- Text / Typography
- Abstract / Background

对短剧生产来说，最关键的分类不是全部，而是：

| 分类 | 对短剧的用途 |
|---|---|
| Character / Portrait | 角色定妆、角色锚点 |
| Comic / Storyboard | 分镜图、漫画式镜头参考 |
| Cinematic / Film Still | 首帧/关键帧电影感图像 |
| YouTube Thumbnail | 短剧封面、强钩子标题图 |
| Social Media Post | 小红书/短视频平台图文宣传 |
| Poster / Flyer | 剧集海报、人物关系海报 |
| Infographic / Edu Visual | 剧情设定说明、系统/公司/修仙等级设定图 |
| Text / Typography | 标题字、字幕卡、封面字效 |

这套分类可以直接变成我们 `drama-short-assets` 的 prompt template index。

---

## README 展示的 Prompt 结构

README 每条 prompt 基本包含：

```text
### No. X: Title
Language badge / Featured / Raycast Friendly
Description
Prompt
Generated Images
Details
```

`Details` 包括：

- Author
- Source
- Published date
- Languages
- Try it now 链接

这说明它强调 prompt 和效果图绑定。对图像 prompt 来说，仅保存 prompt 不够，必须保存生成样图，否则无法判断风格是否真的合适。

这点对我们的 manifest 很重要：

```json
{
  "asset_id": "C01",
  "prompt": "...",
  "generated_images": ["assets/C01_v1.png", "assets/C01_v2.png"],
  "selected": "assets/C01_v2.png",
  "reason": "角色脸更稳定，服装更贴近设定"
}
```

---

## Prompt 写法特征

### 1. JSON prompt 很多

Featured prompts 中很多是结构化 JSON，例如：

```json
{
  "type": "exploded view product diagram poster",
  "subject": "VR headset",
  "style": "clean high-tech 3D render, studio lighting, glowing accents",
  "background": "soft purple and blue gradient",
  "header": {
    "logo": "...",
    "subtitle": "..."
  },
  "layout": {
    "centerpiece": "...",
    "callout_labels": {...}
  }
}
```

这说明 GPT Image 2 对结构化指令的接受度可能较好。相比一大段散文式 prompt，JSON prompt 更适合工程化生成：

- 字段可控
- 可复用模板
- 可替换参数
- 更容易从 `episode.yaml` 编译出来

### 2. Raycast 参数化

README 提到部分 prompt 支持 Raycast Snippets：

```text
{argument name="quote" default="Stay hungry, stay foolish"}
{argument name="author" default="Steve Jobs"}
```

这对我们很有启发：短剧 asset prompt 也可以模板参数化：

```text
{character_name}
{visual_marker}
{costume}
{scene}
{mood}
{aspect_ratio}
```

也就是说，我们可以把图像 prompt 设计成模板，而不是每次重新写自然语言。

### 3. 强布局意识

很多 prompt 不只是描述画面，还描述版式：

- header / subtitle
- centerpiece
- callout labels
- left_side / right_side
- grid / panel
- typography
- poster composition

这和 GPT Image 2 的“文字渲染更强”有关。它特别适合做：

- 封面大字标题
- 剧集海报
- 信息图
- 人物设定卡
- 分镜说明图

短剧生产里，`cover.png` 很可能比视频本身还影响点击率，所以这类 prompt 值得单独抽成 `cover_prompt` 模板。

### 4. Prompt 与用途绑定

每条 prompt 都有 description，说明“什么时候用它”。这比直接堆 prompt 更有用。我们后续做 skill 时，也应该让 prompt reference 带 use_case：

```yaml
template_id: short_drama_cover_v1
use_case: 竖屏短剧封面，强标题，大人物脸，冲突感
best_for:
  - 逆袭爽剧
  - 霸总短剧
  - 夜店悬疑
not_for:
  - 水墨仙侠长镜头
```

---

## 示例条目对短剧的启发

README featured 里有几个有代表性的 prompt：

### VR Headset Exploded View Poster

结构化 JSON，适合产品拆解海报。对我们可借鉴为：

- AI 公司系统架构图
- 修仙等级设定图
- 末世物资清单图
- 角色装备拆解图

### Illustrated City Food Map

图文地图型 prompt。可迁移到：

- 宗门地图
- 丧尸小区地图
- 公司楼层/机房逃生图
- 夜店街区路线图

### Momotaro Explainer Slide

将故事做成解释型 slide。这适合做：

- 短剧剧情设定卡
- “上一集回顾”图
- 角色关系说明图

### Anime Martial Arts Battle Illustration

动漫战斗插画。适合仙侠/动作类短剧首帧或关键帧。

### E-commerce Live Stream UI Mockup

UI/直播界面型 prompt。可迁移到：

- 短剧里手机直播间画面
- 公司系统后台画面
- AI 监控面板画面
- 外卖平台订单界面

这些不是直接可用的短剧 prompt，但提供了图像资产类型的范式。

---

## 与前两个 Seedance 项目的关系

目前我们读了三类材料：

| 项目 | 作用 |
|---|---|
| `Seedance2-Storyboard-Generator` | 短剧/故事怎么拆成剧本、素材、分镜 |
| `seedance-prompt-skill` | Seedance 2.0 视频 prompt 怎么写、怎么延长 |
| `awesome-gpt-image-2` | GPT Image 2 图像 prompt 怎么组织、怎么做角色/封面/分镜资产 |

合起来就是：

```text
故事/题材
  ↓
短剧结构与分镜（Seedance2-Storyboard-Generator）
  ↓
图像资产生成：角色 / 场景 / 封面 / 首尾帧（awesome-gpt-image-2）
  ↓
视频 prompt 编译与延长（seedance-prompt-skill）
  ↓
imagegen2 + 即梦/Seedance + ffmpeg 执行层（我们自己补）
```

---

## 对 Dramaclaw / short-drama skill pack 的启发

### 1. 增加 `drama-short-image-prompts`

建议未来 skill pack 至少包含：

```text
drama-short-image-prompts
  负责把角色/场景/封面/首尾帧需求编译成 GPT Image 2 prompt
```

它应该使用结构化模板：

```yaml
asset_id: C01
asset_type: character
purpose: role_anchor
prompt:
  type: cinematic character reference sheet
  subject: ...
  outfit: ...
  visual_markers: ...
  expression: ...
  background: clean neutral background
  style: ...
  constraints:
    - same face identity across future images
    - no text
    - no watermark
```

### 2. 封面图应单独建模

短剧 MVP 不应只生成视频，还要生成 `cover.png`。GPT Image 2 的文字渲染能力让它很适合封面图：

```yaml
cover:
  title_text: "公司裁掉最后一个后端"
  subtitle_text: "凌晨3点，AI建议关闭公司"
  visual: "空荡办公室 + 崩溃服务器屏幕 + 男主背影"
  layout: "9:16 vertical, big bold Chinese title, dramatic contrast"
```

### 3. 角色定妆图要和 Seedance 引用打通

GPT Image 2 生成的角色图应直接进入 Seedance：

```text
imagegen2 生成 C01 角色定妆图
  ↓
Seedance prompt 中引用 @图片1 为 C01 角色外观参考
```

所以 manifest 需要记录：

```json
{
  "asset_id": "C01",
  "path": "assets/C01_selected.png",
  "seedance_slot": "图片1",
  "usage": "男主角色外观参考"
}
```

### 4. Prompt 库要按“短剧资产类型”重组

原仓库按通用图片用途分类。我们不应照搬全部分类，而应筛选成：

```text
character_anchor
scene_background
cover_poster
storyboard_panel
social_card
system_ui_mockup
prop_design
relationship_chart
```

这更贴合短剧生产。

---

## 不适合直接照搬的地方

1. **没有 skill 入口**
   - 它是 awesome list，不是 agent workflow。

2. **README 只展示部分数据**
   - 统计说 2717 prompts，但 README 实际展示 featured + 部分 regular；完整数据依赖 CMS/网站。

3. **数据不是本地 JSON prompt 库**
   - 和 Nano Banana prompt skill 不同，这个仓库没有 `references/*.json`。
   - 如果要离线检索，需要解析 README 或接 CMS API。

4. **用途太泛**
   - 包含头像、电商、海报、UI、游戏资产等。短剧只需要其中一部分。

5. **FAQ 有模型归属错误**
   - `docs/FAQ.md` 写成 Google model，需谨慎引用。

---

## 我们可以怎么用它

短期建议不是 fork，而是做素材阅读与模板提取：

1. 从 README 抽取 `Comic / Storyboard`、`Cinematic / Film Still`、`Character`、`YouTube Thumbnail`、`Text / Typography` 相关 prompt。
2. 总结成 8-12 个短剧资产模板。
3. 写入我们自己的 `drama-short-image-prompts` reference。
4. 用第一批 5 条短剧分别生成：
   - 角色定妆图 prompt
   - 场景图 prompt
   - 封面图 prompt
   - 关键帧/首帧 prompt
5. 将图像 prompt 输出结构和 Seedance slot 映射打通。

---

## 总评

`awesome-gpt-image-2` 是一个 prompt 语料仓库，不是工具链。但它补上了前两个 Seedance 项目缺失的一块：**图像资产 prompt 的大规模参考样本**。

它给 Dramaclaw 的价值可以概括为：

> 用 GPT Image 2 生成短剧生产所需的“稳定视觉资产”：角色、场景、封面、首尾帧、分镜图；再把这些资产作为 @图片 输入喂给 Seedance 2。

一句话：

> Seedance 负责动起来，GPT Image 2 负责先把角色、场景和封面画准。
