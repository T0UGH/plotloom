---
title: Plotloom Agent-neutral Skill Pack 调研
created: 2026-04-28 22:12 CST
agent: nova
material_type: research-note
status: raw
tags:
  - plotloom
  - agent-neutral
  - skills
  - codex
  - claude-code
  - opencode
  - openclaw
  - hermes
source:
  - https://github.com/openai/codex
  - https://github.com/obra/superpowers
  - https://github.com/LeoYeAI/openclaw-master-skills
  - /Users/wangguiping/.hermes/profiles/nova/skills/autonomous-ai-agents/hermes-agent/SKILL.md
related:
  - raw/agents/nova/research/2026-04-28-dramaclaw-build-vs-adopt-recommendation.md
  - raw/agents/mt/handoffs/2026-04-27-dramaclaw-short-drama-mvp-handoff-to-nova.md
---

# Plotloom Agent-neutral Skill Pack 调研

## 一句话结论

Plotloom 不应该实现成“Claude Code skills”，而应该把 **短剧生产方法、artifact contract、模板和可执行脚本** 做成一套 agent-neutral skill pack；Codex / Claude Code / OpenCode / OpenClaw / Hermes 通过很薄的 adaptor 或安装映射接入。

最小可行方向：

```text
Plotloom core repo
  skills/<skill-name>/SKILL.md
  skills/<skill-name>/references/
  skills/<skill-name>/templates/
  skills/<skill-name>/scripts/
  schemas/
  examples/
  adapters/{codex,claude-code,opencode,openclaw,hermes}/
```

核心不是适配某个 agent，而是定义稳定的 **skill package + artifact contract**。

## 方向修正记录

贵平明确修正：

> 我们不做 claude code skills，我们可能是做一系列 skills，支持 codex、claudecode、openclaw、hermes 都能快速接入。

这意味着：

- Claude Code 只是一个目标运行时，不是产品边界。
- Plotloom 的长期资产应是跨 agent 的短剧生产知识与产物协议。
- 每个 agent 的差异应收敛到 adaptor 层，不污染核心 skill 内容。

## 现有 agent skill 形态对比

| Runtime | Skill 发现/安装 | 核心文件 | 触发机制 | 资源目录 | 对 Plotloom 的启发 |
|---|---|---|---|---|---|
| Codex | `~/.agents/skills/`；也可 symlink 外部 repo | `SKILL.md` + YAML frontmatter | `name`/`description` 自动匹配或显式提及 | `scripts/`、`references/`、`assets/`，另有 `agents/openai.yaml` | 最接近中立 skill 包；可作为 Plotloom 主格式基线 |
| Claude Code | built-in Skill tool / plugin marketplace；个人 skills 常见于 `~/.claude/skills` | `SKILL.md` | Skill tool 加载；description 用于发现 | 支持附加参考/脚本，但生态里常保持简洁 | 需要 adaptor/插件声明，避免只写 Claude 专属指令 |
| OpenCode | `~/.config/opencode/skills/`、`.opencode/skills/`；有 native `skill` tool | `SKILL.md` + frontmatter | `skill` tool list/load；可由 plugin 注入 bootstrap | 同样可 symlink skill repo | 可通过 symlink + 插件实现无侵入接入 |
| OpenClaw / MyClaw | `~/.openclaw/workspace/skills/`；`clawhub install` | `SKILL.md`，有的 skill 还带 `index.js` | slash command / skill 目录 | scripts、index.js、README 等较自由 | 需要兼容更松散的 skill 形态；不要依赖严格前置元数据 |
| Hermes | profile/global skills；`hermes skills install/search/publish`；运行时有 `skill_view`/`skill_manage` | `SKILL.md` + YAML frontmatter + metadata | skills list + 强制加载规则 + 可指定 `--skills` | `references/`、`templates/`、`scripts/`、`assets/` | 可作为开发与验证主环境，支持 profile 隔离和 registry/tap |

## 关键发现

### 1. `SKILL.md + YAML frontmatter` 已经是事实最小公约数

Codex、Claude Code、OpenCode、Hermes、OpenClaw 生态都能接受或很容易转换到：

```text
skill-name/
  SKILL.md
  references/
  scripts/
  templates/ 或 assets/
```

差异主要在：

- skill 放在哪里；
- description 如何用于触发；
- 是否有额外 marketplace/plugin/registry 元数据；
- 可执行脚本和工具权限如何声明。

所以 Plotloom 不需要发明完全不同的 skill 文件格式；应该在事实公约数上加一个 **Plotloom manifest**。

### 2. 不能把 runtime 专属工具名写死进核心 skill

例如：

- Claude Code: `Skill` / `Task` / `TodoWrite`
- OpenCode: native `skill` tool / `@mention` / `update_plan`
- Hermes: `skill_view` / `todo` / `delegate_task`
- Codex: shell/plan/tool capability 取决于运行环境

核心 skill 应写：

```text
Load reference X
Create or update artifact Y
Run script Z if available
Validate with rubric R
```

Adaptor 再映射成具体 runtime 的工具调用方式。

### 3. Codex 官方 skill 结构适合作为中立基线

OpenAI Codex repo 中的 skill-creator sample 明确：

```text
skill-name/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
├── references/
└── assets/
```

其中 `SKILL.md` frontmatter 的 `name` 和 `description` 是触发关键；body 在 skill 触发后加载；references/scripts/assets 用 progressive disclosure 降低上下文成本。

Plotloom 可采用这个思路，但不要只生成 `agents/openai.yaml`，而是生成：

```text
agents/openai.yaml
agents/claude-code.yaml
agents/opencode.yaml
agents/hermes.yaml
agents/openclaw.yaml
```

或把这些放在 `adapters/<runtime>/`。

### 4. OpenCode / Superpowers 证明“symlink + native skill discovery”可行

Superpowers 对 Codex/OpenCode 的安装方式本质是：

```text
clone skill repo
symlink skills/ 到 runtime 的 skill search path
restart runtime
```

这给 Plotloom 很好的安装模型：

```bash
plotloom install --target codex
plotloom install --target opencode
plotloom install --target hermes
```

第一版甚至可以不用 CLI，只提供安装脚本：

```text
adapters/codex/install.sh
adapters/opencode/install.sh
adapters/hermes/install.sh
adapters/openclaw/install.sh
```

### 5. OpenClaw 的 skill 生态更松散，需要兼容而不是强绑定

`openclaw-master-skills` 中的 skill 多为：

```text
skills/<name>/SKILL.md
skills/<name>/index.js        # 部分有
skills/<name>/README.md       # 部分有
```

安装路径：

```text
~/.openclaw/workspace/skills/
```

OpenClaw skill 可能偏 slash command / JS 执行器；因此 Plotloom 应提供：

- 纯文档 skill 版本；
- 可选 `index.js` wrapper；
- 不假设 OpenClaw 一定能理解 Codex 的 `agents/openai.yaml`。

### 6. Hermes 适合做 Plotloom 的开发与验证环境

Hermes 已支持：

- skills install/search/publish/tap；
- profile 隔离；
- `references/`、`templates/`、`scripts/`、`assets/`；
- `--skills` 预加载；
- cron / gateway / delegation，可验证长流程。

因此 Plotloom 可先在 Hermes 中验证 skill 行为，再生成其他 runtime 的 adaptor。

## Plotloom 中立 skill package 草案

建议每个 skill 目录长这样：

```text
skills/plotloom-plan-episode/
  SKILL.md
  plotloom.skill.yaml
  references/
    short-drama-beats.md
    genre-patterns.md
  templates/
    episode.yaml
  scripts/
    validate_episode.py
  examples/
    office-backend-layoff/episode.yaml
  agents/
    openai.yaml
    claude-code.yaml
    opencode.yaml
    hermes.yaml
    openclaw.yaml
```

其中：

- `SKILL.md`：面向 agent 的核心操作指南，尽量不写 runtime 专属工具名。
- `plotloom.skill.yaml`：Plotloom 自己的中立 manifest。
- `references/`：短剧方法论、题材模板、prompt 规则。
- `templates/`：artifact 模板。
- `scripts/`：验证、转换、导出、生成目录等确定性动作。
- `examples/`：可跑样例。
- `agents/`：各 runtime 的触发描述、安装元数据、工具映射。

## `plotloom.skill.yaml` 初稿

```yaml
id: plotloom.plan-episode
name: plotloom-plan-episode
version: 0.1.0
kind: skill
runtime_neutral: true
summary: Plan a 30-60s short drama episode from a premise.
triggers:
  - plan a short drama
  - write a 45s mini drama episode
  - turn an idea into Plotloom episode.yaml
inputs:
  - name: premise
    type: text
  - name: genre
    type: enum
    values: [workplace, romance, revenge, suspense, fantasy, comedy]
outputs:
  - path: episode.yaml
    schema: schemas/episode.schema.json
  - path: characters.yaml
    schema: schemas/characters.schema.json
resources:
  references:
    - references/short-drama-beats.md
  templates:
    - templates/episode.yaml
  scripts:
    - scripts/validate_episode.py
requires:
  tools:
    - filesystem.write
    - shell.optional
adapters:
  codex:
    install_path: ~/.agents/skills/plotloom/plotloom-plan-episode
  claude_code:
    install_path: ~/.claude/skills/plotloom-plan-episode
  opencode:
    install_path: ~/.config/opencode/skills/plotloom/plotloom-plan-episode
  openclaw:
    install_path: ~/.openclaw/workspace/skills/plotloom-plan-episode
  hermes:
    install_path: ~/.hermes/skills/creative/plotloom-plan-episode
```

## Plotloom MVP skill 集合建议

第一版不要拆太碎，建议 5 个 skill：

| Skill | 目标 | 输入 | 输出 |
|---|---|---|---|
| `plotloom-plan-episode` | 把题材/梗概变成 45s 短剧结构 | premise / genre / constraints | `episode.yaml`, `characters.yaml` |
| `plotloom-storyboard-shots` | 把 episode 拆成镜头和节奏 | `episode.yaml`, `characters.yaml` | `shots.yaml` |
| `plotloom-image-prompts` | 生成角色、场景、封面、首尾帧图像 prompt | `characters.yaml`, `shots.yaml` | `assets.yaml`, `image_prompts.md` |
| `plotloom-video-prompts` | 生成 Seedance/即梦视频 prompt | `shots.yaml`, `assets.yaml` | `video_prompts.md`, `jobs.yaml` |
| `plotloom-review-rerun` | 按 rubric 验收并决定回炉 | `manifest.json`, generated assets/video | `review.md`, `rerun_plan.yaml` |

执行层（imagegen2、Seedance、ffmpeg）先不做成核心 skill，而是作为 scripts/adaptor 能力逐步接入。

## Artifact contract 优先级

Plotloom 的核心长期资产不是 skill 文档本身，而是这些 artifact：

```text
plotloom.yaml          # project-level metadata
episode.yaml           # 45s 剧集结构
characters.yaml        # 角色设定与一致性锚点
shots.yaml             # 镜头表
assets.yaml            # 图像/音频/视频资产索引
jobs.yaml              # 待提交生成任务
manifest.json          # 最终产物记录
review.md              # 人/agent 验收结果
rerun_plan.yaml        # 回炉计划
```

这些文件必须 agent-neutral。不同 agent 只是在同一批 artifact 上工作。

## Adaptor 层要回答的问题

每个 runtime adaptor 只回答四件事：

```text
1. skill 如何被发现？
2. SKILL.md / references 如何加载？
3. scripts 如何执行、权限如何声明？
4. artifact 写在哪里、如何验证？
```

不应该把短剧方法论复制到 adaptor 里。

## 下一步建议

进入头脑风暴前，还需要补齐两块：

1. **Artifact schema 深化**：先把 `episode.yaml / characters.yaml / shots.yaml / assets.yaml / manifest.json` 的最小字段定出来。
2. **跨 runtime 安装验证**：至少在本机验证 Codex/Hermes/OpenCode 三个路径能发现同一个测试 skill；Claude Code / OpenClaw 可先做文档级 adaptor。

## 结论

Plotloom 可以用 `SKILL.md` 作为生态兼容层，但真正的产品边界应是：

```text
agent-neutral short-drama production protocol
  = skills + schemas + templates + scripts + examples + adapters
```

这比“Claude Code skill pack”更大，也更符合贵平要的 Codex / Claude Code / OpenClaw / Hermes 快速接入方向。
