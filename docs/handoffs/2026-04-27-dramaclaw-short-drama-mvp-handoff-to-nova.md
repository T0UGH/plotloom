---
title: Dramaclaw 短剧生产工具 MVP：从 videoclaw 另起炉灶的 handoff
created: 2026-04-27
agent: mt
material_type: handoff
status: raw
source: MT 与贵平 Feishu 对话；本地源码快速检查 /Users/wangguiping/workspace/github/videoclaw
related_topics:
  - ai-short-drama
  - videoclaw
  - dramaclaw
  - imagegen2
  - seedance2
  - jimeng-cli
---

# Dramaclaw 短剧生产工具 MVP：从 videoclaw 另起炉灶的 handoff

## 给 Nova 的结论

贵平已拍板：不要继续在 `videoclaw` 上补丁式改造，建议另起新项目，暂名 `dramaclaw` / `shortclaw` / `clipforge`。

核心定位：

> 新项目不是通用 AI 视频生成器，也不是 workspace/project 管理器，而是一个面向 AI 短剧测试的生产流水线执行器。

第一版只服务当前 5 条短剧开头测试，不做大而全。

## 背景

这轮讨论来自贵平想做 AI/短剧 Shorts 测试。前面已经定过第一批 5 个题材开头：

1. AI 职场黑色幽默：《公司裁掉最后一个后端》
   - 钩子：公司裁掉最后一个后端后，AI 在凌晨 3 点建议关闭公司。
2. 玄幻仙侠爽剧：《宗门把我赶下山后，掌门跪着求我回去》
   - 钩子：宗门嫌我只会扫地，把我赶下山。三天后，护山大阵塌了，掌门跪在我门口求我回去。
3. 末世美女搭档：《丧尸爆发后，校花敲开我家门》
   - 钩子：丧尸爆发第一天，校花敲开我家门，说她知道我囤了三年的泡面。
4. 夜店/酒吧美女悬疑：《凌晨两点，美女坐进我车里》
   - 钩子：凌晨两点，一个美女拉开我的车门说：开车，别问，后面那个人不是人。
5. 外卖员逆袭爽剧：《美女总裁点了我的外卖》
   - 钩子：我送外卖迟到 3 分钟，美女总裁却说：你终于来了，公司等你接手。

固定单集结构：

```text
0-3s：一句强钩子
3-15s：冲突建立
15-30s：问题升级
30-40s：反转打脸
40-45s：一句追更钩子
```

目标是先测：3 秒停留、评论欲、角色记忆点；不要先连续做 30 条。

相关已记录文档：

- `docs/research/2026-04-26-youtube-shorts-ai-comic-drama-feasibility.md`

## videoclaw 当前判断

MT 快速检查了本地仓库：

- 路径：`/Users/wangguiping/workspace/github/videoclaw`
- 分支：`main`
- 最近提交：`ab04ecc docs: 更新 README.md 和 CLAUDE.md`

当前可复用点：

- `videoclaw/cli/commands/merge.py`：ffmpeg 合并逻辑可参考。
- `videoclaw/ffmpeg/processor.py`：基础 ffmpeg 包装可参考，但很薄。
- `videoclaw/publisher/`：抖音/快手发布逻辑可参考。
- `skills/video-*`：可以作为负面/历史经验参考，不建议直接继承。

主要问题：

1. `workspace/project` 心智跑偏
   - README 和代码仍围绕 `videoclaw init <project>`、`~/videoclaw-projects/<project>`、`.videoclaw/config.yaml`。
   - 对短剧测试来说，这层是干扰项。

2. 模型后端过时
   - 旧代码仍围绕 dashscope / gemini / volcengine 内置 backend。
   - 文档提 Seedance 2.0、wan2.6、Gemini 图像等，但现实最优链路已经变化。

3. 当前最佳工具链不在 videoclaw 内部
   - 贵平明确：现在最好的图像模型是 `imagegen2`。
   - 视频模型 Seedance2 需要通过“即梦 CLI”调用。
   - 因此 videoclaw 自己维护 provider 抽象没有价值，容易变成追模型 API 的负担。

4. 工具链健康度一般
   - 系统 Python 跑 `python -m videoclaw.cli.main --help` 缺 `playwright`。
   - `.venv` 能跑 help，但缺 `pytest`。
   - 说明旧项目现在不是稳定可复用的生产工具链。

## 已达成的架构判断

不要继续改造 videoclaw。

原因：

- 要清 workspace/project。
- 要清旧 provider。
- 要清旧 skill。
- 要修环境/测试。
- 还要重写产品心智。

最后等于在旧房子里拆到只剩地基。

推荐做法：

```text
新项目：dramaclaw / shortclaw / clipforge
定位：AI 短剧生产流水线
底层：调用 imagegen2 + 即梦 CLI + ffmpeg + 发布工具
输入：episode.yaml
输出：final.mp4 + cover + subtitles + manifest.json
```

一句话定位：

> videoclaw 冻结归档，只当参考库；新项目从第一天就按短剧生产执行器设计。

## 新项目应该做什么

### 1. 规格层

定义短剧 `episode.yaml`，统一表达：

- series / episode id
- title
- hook
- 45 秒节奏结构
- characters
- scenes / shots
- dialogue / voiceover
- subtitles
- cover prompt
- publish metadata

示意：

```yaml
series: ai-backend
episode: ep01
title: 公司裁掉最后一个后端
hook: 公司裁掉最后一个后端后，AI 在凌晨 3 点建议关闭公司。
duration: 45
structure:
  - range: 0-3s
    purpose: strong_hook
  - range: 3-15s
    purpose: conflict_setup
  - range: 15-30s
    purpose: escalation
  - range: 30-40s
    purpose: reversal
  - range: 40-45s
    purpose: follow_hook
characters: []
shots: []
cover: {}
publish: {}
```

### 2. 编排层

不要内置模型后端，优先编排外部最强 CLI：

```text
episode.yaml
  ↓
script / shots / prompts
  ↓
imagegen2 CLI 生成角色图、场景图、封面
  ↓
即梦 CLI 调 Seedance2 生成镜头视频
  ↓
ffmpeg 合并 + 字幕 + 配音
  ↓
发布
```

### 3. 资产账本

每集输出一个 `manifest.json`，记录：

- 输入 episode spec hash
- 每张图的 prompt / engine / path / selected version
- 每段视频的 prompt / engine / path / selected version
- 字幕 / 音频 / final.mp4
- 发布信息

注意：这叫 manifest，不叫 workspace/state。它是产物账本，不是产品心智中心。

## MVP 命令建议

第一版命令要少：

```bash
dramaclaw plan episode.yaml
dramaclaw images episode.yaml
dramaclaw clips episode.yaml
dramaclaw assemble episode.yaml
```

可选后续：

```bash
dramaclaw batch ./episodes/
dramaclaw publish ./output/ai-backend/ep01/final.mp4
```

## 推荐目录结构

```text
short-drama/
├── series/
│   ├── ai-backend/
│   │   ├── characters.yaml
│   │   └── ep01.yaml
│   ├── xianxia/
│   ├── zombie-school-beauty/
│   ├── nightclub-mystery/
│   └── delivery-ceo/
└── output/
    └── <series>/<episode>/
        ├── script.md
        ├── shots.yaml
        ├── manifest.json
        ├── assets/
        ├── clips/
        ├── subtitles.srt
        ├── cover.png
        └── final.mp4
```

## Nova 下一步建议

建议 Nova 不要直接开写代码，先做 1 个非常小的设计/实施计划：

1. 确认新仓库名字：建议优先 `dramaclaw`，因为比 `shortclaw` 更贴“短剧生产”。
2. 检查本机是否已有 `imagegen2` CLI 和即梦 CLI，记录实际调用方式。
3. 设计最小 `episode.yaml` schema。
4. 设计 `manifest.json` schema。
5. 搭一个最小 Python CLI 骨架，只实现：
   - `dramaclaw plan episode.yaml`：把 episode 规范化为 `shots.yaml` / prompts。
   - `dramaclaw assemble episode.yaml`：先用已有本地 clips 跑 ffmpeg 合并，验证目录和 manifest 闭环。
6. 暂时不要接真实发布，先不碰抖音/快手登录态。
7. 暂时不要做 UI / workspace / web app。

## 验收标准

第一阶段不是“生成最热视频”，而是工具链闭环：

- 能读取一个 episode spec。
- 能生成可追踪的 output 目录。
- 能调用或预留 imagegen2 / 即梦 CLI 命令位。
- 能把若干 clips 合成 final.mp4。
- 能产出 manifest.json。
- 所有路径和产物能被下一轮复用。
- 不引入 workspace/project 概念。

## 风险与边界

- 不要把 dramaclaw 做成通用视频创作平台。
- 不要复刻 videoclaw 的 provider 抽象。
- 不要在第一版追求多模型兼容。
- 不要把 manifest 做成复杂状态机。
- 即梦 CLI 和 imagegen2 的真实命令参数必须以本机实测为准，不要凭记忆写死。

## 给 Nova 的一句话任务

请接手设计并启动一个新项目 `dramaclaw`：面向 45 秒短剧测试的生产流水线 CLI。以 `episode.yaml -> imagegen2 -> 即梦 Seedance2 -> ffmpeg -> manifest/final.mp4` 为主线，另起炉灶，不继承 videoclaw 的 workspace/project/provider 架构；videoclaw 只作为 ffmpeg 和 publish 逻辑参考。
