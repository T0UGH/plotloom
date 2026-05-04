---
title: Plotloom 生产链路优化复盘：refs、人脸、批处理与验收
created: 2026-05-04
agent: mt
material_type: research
status: raw
source: Feishu session recall + local plotloom code inspection, repo T0UGH/plotloom
related_topics:
  - plotloom
  - short-drama
  - video-generation
  - reference-images
  - character-consistency
  - seedance
  - dreamina
---

# Plotloom 生产链路优化复盘：refs、人脸、批处理与验收

## 结论

Plotloom 现在最大问题不是“缺少生成能力”，而是短剧生产链路里仍有太多隐式状态：实际传了哪些 reference、角色资产用的是哪个版本、人脸策略是否适合当前 provider、批量任务是否可恢复、结果是否经过可复盘验收。

下一阶段应从“能生成”升级为：

> 能证明自己传了正确 refs、用了正确角色资产、失败可恢复、结果可验收。

优先级最高的是 reference 显式化和人脸策略工具化。因为这两类问题直接导致生成结果不可控，且复盘成本最高。

## 背景与卡点来源

近期 Graycrow Frontier / Plotloom 生产中暴露了几类重复卡点：

1. reference 传递错误：Markdown 里写的 reference 不等于 provider 实际收到的 reference。
2. 人脸一致性问题：Seedance 在西部骑马、远景、帽檐阴影等 archetype 场景里容易漂移成泛化西部男主。
3. ARK / VolcEngine 隐私拒绝：fictional character sheet 也可能被判为真人隐私图。
4. 红脸 / mesh overlay 方案误判：透明红色 facial topology、mesh overlay、pixelation 并不能可靠绕过 ARK 隐私拒绝。
5. 批量生成不可恢复：EP2 资产生成时已成功的黑矿石被重复跑，任务超时后剩余资产没有继续。
6. 验收靠人工临场组织：contact sheet、视觉检查、review note 没有变成 Plotloom 的固定命令和产物。
7. 角色资产版本污染：Rowan/Mara 从 v1/v2/v3 多次迭代，Enoch 也重做过，旧路径容易残留在 prompt 或 characters.md 里。

## 当前代码观察

本地仓库：`/Users/wangguiping/workspace/plotloom`，远端：`T0UGH/plotloom`。

相关代码状态：

- `plotloom/video/types.py` 中 `PlotloomVideoRequest` 已经有：
  - `first_frame`
  - `reference_images`
  - `reference_videos`
  - `source_video`
- `plotloom/video/adapters/volcengine_seedance.py` 的 `submit()` 支持 `reference_images`，并会把它们写入 `content`，role 为 `reference_image`。
- 但 `plotloom/commands/video.py` 的 `video submit` CLI 目前没有暴露 `--first-frame` / `--reference-image`，也没有从 prompt 文件解析 refs 后写入 request。
- `plotloom/prompts.py` 目前主要负责提取 `Prompt string` 并在 reference mode 下 prepend 一句 provider instruction，没有完整实现 reference image extraction / validation。

判断：数据结构和 adapter 层已经有接口雏形，但 CLI 和 prompt validation 层没有闭环，所以实际生产中仍靠 agent 记忆和手工检查。

## P0：Reference 传递必须显式化

### 1. 增加 `plotloom prompt refs/check`

问题：之前出现过 `Use Image 1` 把全局 Image mapping 误带入，导致实际提交给 Seedance 的 refs 不是 clip-local refs。用户在视觉上看到的是“角色不像”，根因却是 provider 收到的 reference 集合不对。

应该实现：

```bash
plotloom prompt refs --episode ep001 --clip clip-03
plotloom prompt check --episode ep001 --clip clip-03 --strict-refs
```

检查内容：

- 展示该 clip 最终解析出的 refs 列表。
- 校验本地 reference 文件存在。
- 支持并校验 `asset://...` face anchor。
- 检查未解析的 `Image N` 引用。
- 检查是否误引用非本 clip 的全局 image mapping。
- 明确区分：first frame、character reference、costume reference、scene reference、face anchor。

成功标准：提交视频前，agent 和用户都能看到“本次实际要传给 provider 的 refs 是什么”。

### 2. `video submit` 增加 explicit refs 参数

问题：文本 prompt 写本地路径没有实际效果。真正 provider 请求必须走 request field。

建议 CLI：

```bash
plotloom video submit \
  --episode ep001 \
  --clip clip-03 \
  --adapter volcengine-seedance \
  --mode reference-to-video \
  --first-frame assets/scenes/clip-03/selected.png \
  --reference-image assets/cast/rowan-crowe/selected-face-blocked.png \
  --reference-image asset://asset-...
```

receipt 必须记录：

- `first_frame`
- `reference_images`
- `reference_roles`
- `compiled_prompt_sha256`
- 本地 ref 的 sha256 / mtime / path
- `asset://` id

否则后续无法复盘“为什么这一版脸漂了 / 为什么剧情元素丢了”。

## P0：人脸问题要变成一等公民

### 3. 增加 `plotloom face policy`

问题：Graycrow 中 Rowan/Mara 的脸部稳定不是单纯 prompt 问题，而是 provider policy + asset type + reference role 的组合问题。

已知经验：

- ARK / VolcEngine 可能把 fictional character sheet 判成隐私或真人图。
- 错误包括 `InputImageSensitiveContentDetected.PrivacyInformation` / `input image may contain real person`。
- transparent red facial topology、mocap mesh overlay、pixelation + red topology 不能可靠解决 ARK 隐私拒绝。
- Codex opaque red face blocker 可作为 costume / body / wardrobe reference。
- VolcEngine virtual face asset 是 face-only，不是完整角色设计来源。
- Rowan / Mara 已有 face anchor：具体 token 不应在公开/交付文本中泄漏，必要时写 `[REDACTED]`。

建议在系列 repo 中增加结构化角色策略，例如：

```toml
[characters.rowan]
canonical_ref = "assets/cast/rowan-crowe/selected.png"
face_anchor = "asset://[REDACTED]"
costume_ref = "assets/cast/rowan-crowe/selected-face-blocked.png"

[characters.rowan.provider_policy.volcengine-seedance]
strategy = "face-anchor-plus-face-blocked-costume"
forbid = ["full-character-sheet", "visible-face-sheet", "corpse-face-reference"]
```

工具命令：

```bash
plotloom face policy --character rowan --adapter volcengine-seedance
plotloom doctor --adapter volcengine-seedance --face-policy
```

输出应直接告诉 agent：

- 不要传 full visible-face character sheet。
- 应传 `asset://` face anchor。
- 可传 face-blocked costume sheet。
- scene refs 可以传。
- corpse / morgue / autopsy refs 风险高。

### 4. 增加人脸保持 smoke prompt 模板

问题：Seedance 在骑马、峡谷、远景、帽檐阴影、强西部 archetype 场景里，会把脸拉向泛化 rugged western protagonist。

建议内置一个标准 face consistency smoke：

- medium close-up
- front-left 3/4 face
- face visible at least 2 seconds
- no deep hat shadow
- face occupies 25-35% of frame
- minimal action, slight head turn
- no fast horse riding / canyon wide shot in smoke test

命令可以先简单做成模板输出：

```bash
plotloom face smoke-prompt --character rowan --adapter volcengine-seedance
```

目的不是自动判脸，而是把“脸部测试镜头”从临场经验变成固定流程。

## P1：批量生成要支持 resume / skip existing

### 5. 增加 `plotloom image batch --resume --skip-existing`

问题：EP2 资产批处理时，黑矿石已单独生成成功，但批处理又从第一项重跑，Codex image generation 超时，剩余 8 张资产没有继续生成。

建议 manifest：

```toml
[[items]]
kind = "scene"
episode = "ep002"
clip = "prop-black-resonance-ore"
scene = "ep002-prop-black-resonance-ore"
prompt_file = "episodes/ep002/prompts/prop-black-resonance-ore.md"
output = "assets/scenes/ep002-prop-black-resonance-ore/candidates/v001.png"

[[items]]
kind = "scene"
episode = "ep002"
clip = "clip-07"
scene = "ep002-clip-07-old-mine-gate-scratch-resonance"
prompt_file = "episodes/ep002/prompts/scene-ep002-clip-07-old-mine-gate-scratch-resonance.md"
```

命令：

```bash
plotloom image batch --manifest episodes/ep002/assets.toml --resume --skip-existing
```

要求：

- 已有 `candidates/v001.png` 默认跳过，除非 `--force`。
- 每项写状态：pending/running/succeeded/failed/skipped。
- 记录 started_at、finished_at、error、retry_count。
- 单项超时不阻塞整个 batch，继续下一个任务。

## P1：验收要工具化

### 6. 增加 `plotloom review contact-sheet`

问题：现在候选验收靠 agent 手工组织 ffmpeg/contact sheet/vision review。这个流程有效，但不稳定，不容易交接。

建议命令：

```bash
plotloom review contact-sheet \
  --episode ep002 \
  --kind scenes \
  --output episodes/ep002/review/contact-sheet.png
```

同时生成：

```text
episodes/ep002/review/review-note.md
```

review note 字段：

- candidate path
- pass/fail
- character consistency
- face visible?
- refs used?
- story beat clear?
- provider artifacts
- selected/reroll/revise_prompt/ask_user
- reviewer and timestamp

目标：把“看过了 / 可交付”变成 repo 内可复盘工件，而不是聊天里的一句结论。

## P1：角色资产版本要 canonical 化

### 7. 增加 canonical selected asset 结构

问题：Rowan/Mara 从 v1 到 v3，Enoch 从 v1 到 v2。`characters.md` 如果直接引用候选路径，就容易残留旧版本；prompt 也可能误用过期 reference。

建议结构：

```text
assets/cast/rowan-crowe/
  selected.png
  selected-face-blocked.png
  metadata.toml
  candidates/
    v001.png
    v002.png
    v003.png
```

`characters.md` 只引用 canonical：

```md
Asset reference: assets/cast/rowan-crowe/selected.png
```

历史候选由 metadata 管理：

```toml
selected = "candidates/v003.png"
selected_at = "2026-05-02T20:00:00+08:00"
reason = "approved AAA 3D western asset card style"
rejected = ["candidates/v002.png"]
```

目标：业务文件引用稳定路径，版本演进留给 metadata。

## P2：Provider 错误要结构化归因

### 8. 增加 provider error taxonomy

问题：当前错误处理散落在经验和聊天记录里，agent 容易重复踩坑。

建议归因表：

| 错误 | 可能原因 | 推荐处理 |
|---|---|---|
| `InputImageSensitiveContentDetected.PrivacyInformation` | full visible-face sheet / corpse / morgue ref 触发隐私 | 移除 visible-face sheet；用 `asset://` face anchor + face-blocked costume；必要时 scene-only |
| `input image may contain real person` | fictional character sheet 被当真人 | 同上；不要用透明 mesh 方案硬试 |
| `TimeoutExpired` | Codex image generation 长任务超时 | 标记单项 failed，batch 继续；下次 `--resume` |
| `No such filter: ass` | ffmpeg 缺 libass | 使用 `/usr/local/opt/ffmpeg-full/bin/ffmpeg` |
| Dreamina not logged in | 本机 Dreamina CLI 登录态缺失 | 先 doctor，不自动处理 OAuth |
| Dreamina account not `maestro` | 权限/账号不对 | 停止并报告权限 gap |
| Upload absolute path failed | lark-cli 上传路径问题 | 进入文件目录，用 `--file ./name.mp4` |

可以落到：

```bash
plotloom doctor --adapter volcengine-seedance --explain-error <code>
```

或 docs/runbooks/provider-errors.md。

## 推荐开发顺序

1. `prompt refs/check` + `video submit --first-frame/--reference-image`。
2. canonical selected asset 结构。
3. `image batch --resume --skip-existing`。
4. `face policy` / VolcEngine provider policy。
5. `review contact-sheet` + review note。
6. provider error taxonomy。

判断：先做 P0，不要一上来做 UI 或复杂自动评估。Plotloom 当前最需要的是把生产中的隐式决策变成 repo 内显式工件和 CLI 可检查约束。

## 验收标准

这些优化是否有效，不看功能列表，看能否回答以下问题：

1. 某次视频生成实际传给 provider 的 refs 是什么？
2. 这些 refs 是 clip-local 还是全局误带入？
3. 使用的是角色 canonical selected 版本，还是旧 candidate？
4. 当前 provider 是否允许传 visible-face sheet？
5. face anchor、costume ref、scene ref 的职责是否分开？
6. 批量任务失败后能否从未完成项继续？
7. 候选图/视频是否有 contact sheet 和 review note？
8. 交付结论是否有解码验证、抽帧验证或人工 review 工件支撑？

如果这些问题能被 CLI 和 repo 文件回答，Plotloom 才算从“生成脚本集合”升级成“可复盘的短剧生产系统”。
