---
title: AI 漫剧/漫画创作工具 GitHub 初筛
date: 2026-04-26
agent: mt
material_type: repo-triage
status: raw
source: GitHub CLI + 本地 clone / README / smoke tests
related:
  - 2026-04-26-youtube-shorts-ai-comic-drama-feasibility
---

# 结论

目标是 YouTube Shorts AI 漫剧生产线，偏好 `skill + CLI`、不要网页产品。当前最接近可用的组合是：

1. `JimLiu/baoyu-skills` 的 `baoyu-comic`：更像 Hermes/Claude skill，适合把“内容 → 分镜 → prompt → 图片”流程规范化；本机 Hermes 已安装同名 skill。
2. `augmentedmike/comic-cli`：真正 CLI toolchain，能从 scene JSON/notes 生成 comic frame/page/blog，并带 QA；但 repo 个人化强、测试有失败，适合参考/改造，不建议直接当生产底座。
3. `Absirkhan/ComicCrafter`：有 Python API/简陋 CLI 思路，强调 multi-agent + character memory；但工程包装不完整，README 与实际安装结构不匹配。

不推荐作为首选：
- `Dapeng960208/AI-Comic-Generator`：功能完整但核心是 FastAPI + Vue 可视化工作台，不符合“不要页面”。
- `Nutlope/make-comics`：热度较高，但 Next.js/SaaS 架构，依赖 Clerk/Neon/S3/Redis/Together，明显不是轻量 CLI。
- `strcho/ai_comic`：有 CLI，但更像普通 web app 后端附带命令；依赖未装时无法直接 smoke test。

# 仓库初筛

## 1. JimLiu/baoyu-skills / baoyu-comic

- URL: https://github.com/JimLiu/baoyu-skills
- Stars: 16480（GitHub CLI 查询时）
- Updated: 2026-04-25
- 类型：Agent skill，不是传统 CLI；README 中支持 `/baoyu-comic ... --storyboard-only / --prompts-only` 等 skill 命令形态。
- 本机状态：Hermes 已安装 `baoyu-comic` skill。
- 优点：
  - 正好是 skill 化工作流。
  - 关注 reproducibility：source、analysis、storyboard、characters、prompts、images 分目录保存。
  - 适合做“短剧 IP 的内容资产库”，不只是一次性出图。
- 缺点：
  - 当前 Hermes `image_generate` 是 prompt-only，不支持参考图输入；角色一致性主要靠文本描述，不是严格视觉锁定。
  - 更偏知识漫画/教育漫画，漫剧 Shorts 需要二次改造成“竖屏分镜 + 配音 + 字幕 + ffmpeg 拼接”。
- 判断：首选流程底座，适合先扩展一个 `ai-short-drama` skill。

## 2. augmentedmike/comic-cli

- URL: https://github.com/augmentedmike/comic-cli
- Stars: 0
- Updated: 2026-03-09
- 类型：CLI toolchain。
- README 核心命令：
  - `comic frame happy`
  - `comic page --scenes story.json`
  - `comic blog --notes day.md`
  - `comic qa page.png`
- 技术点：Gemini / kie.ai，scene JSON，layout，caption localization，视觉 QA。
- 本地检查：`python3 -m pytest -q tests` 结果 36 passed / 8 failed。失败集中在 `comic-emote` 测试里 `__file__` 未定义；不是主 page/blog pipeline 的直接失败，但说明工程质量一般。
- 优点：
  - CLI 形态最符合要求。
  - 有 scene JSON、layout、caption、QA，这些对短剧流水线有价值。
  - 可以借鉴 `comic page` / `comic qa` 的接口设计。
- 缺点：
  - repo 很个人化，默认路径如 `~/Desktop/crabby/config.json`。
  - 无 license 信息，生产复用要谨慎。
  - 不是 Shorts 视频流水线，只到 comic/page/blog。
- 判断：不建议直接用；建议 clone 后抽取接口思想，或让 Codex 改成内部 CLI。

## 3. Absirkhan/ComicCrafter

- URL: https://github.com/Absirkhan/ComicCrafter
- Stars: 1
- Updated: 2025-12-07
- License: MIT
- 类型：Python library + FastAPI demo + 简单 CLI 入口。
- README 说支持 story analysis、prompt generation、layout planning、RAG character memory、speech bubble overlay。
- 本地检查：没有 `setup.py/pyproject.toml`，但 README 写 `pip install -e .`，工程包装不完整。
- 优点：
  - 思路接近：multi-agent 拆故事、角色记忆、布局、对白。
  - MIT，适合借鉴。
- 缺点：
  - 可维护性/成熟度低。
  - CLI 很薄：`comiccrafter <story_file>`。
- 判断：可读源码借鉴，不作为生产工具。

## 4. Dapeng960208/AI-Comic-Generator

- URL: https://github.com/Dapeng960208/AI-Comic-Generator
- Stars: 9
- Updated: 2026-01-28
- 类型：FastAPI + Vue 工作台。
- 优点：功能看起来完整：storyboard、角色工坊、单帧重绘、全局风格 JSON、Gemini。
- 缺点：强 UI，不符合“不带页面”。
- 判断：可以参考数据模型，不建议采用。

## 5. Nutlope/make-comics

- URL: https://github.com/Nutlope/make-comics
- Stars: 355
- Updated: 2026-04-16
- 类型：Next.js SaaS。
- 栈：Next.js 16, Clerk, Neon, S3, Redis, Together AI。
- 判断：产品形态不错，但不是本地 CLI；部署面太重，不适合作为个人 Shorts 生产线底座。

## 6. strcho/ai_comic

- URL: https://github.com/strcho/ai_comic
- Stars: 0
- Updated: 2026-01-25
- 类型：FastAPI/Vue + 后端 CLI。
- README CLI: `python -m src.cli generate "Your story here..." -o comic.png -f png`
- 本地 smoke test：缺 `pydantic_settings`，未安装依赖无法直接运行。
- 判断：CLI 有，但项目成熟度低；不优先。

# 建议路线

不要直接押某个开源项目。更稳的是：

- 以本机 `baoyu-comic` skill 为流程骨架。
- 借 `comic-cli` 的 scene JSON / `comic page` / `comic qa` 命令设计。
- 新建或扩展一个内部 skill：`ai-short-drama`。
- CLI 目标：
  - `drama new "AI CTO"`
  - `drama episode --series ai-cto --n 1`
  - `drama storyboard episode.md`
  - `drama render panels episode.json`
  - `drama voice episode.md`
  - `drama assemble --shorts episode.json`（ffmpeg 合成 9:16 视频）
  - `drama qa output.mp4`

# 最小可行流水线

MVP 不需要复杂网页：

```text
series.yaml             # 世界观、角色、人设、画风、禁用词
episodes/001.md         # 45 秒剧本
storyboards/001.json    # 6-10 个镜头
prompts/001/*.md        # 每镜头图片 prompt
panels/001/*.png        # 生成图
voices/001.wav          # TTS
subs/001.srt            # 字幕
videos/001.mp4          # 9:16 Shorts
metrics/001.json        # 发布后指标
```

# 关键验收标准

- 纯 CLI 可跑，不依赖浏览器页面。
- 每次生成都有可复现的 `series.yaml + episode.md + storyboard.json + prompts/`。
- 支持角色一致性文本注入。
- 支持人工改 prompt 后局部重跑。
- 输出 9:16 mp4 + srt。
- 能记录 YouTube 数据，用数据反推下一集脚本。
