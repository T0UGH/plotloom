# Plotloom Production Pipeline Implementation Plan

> 日期：2026-05-04  
> 状态：Design / implementation plan  
> 来源：`raw/agents/mt/research/2026-05-04-plotloom-production-pipeline-optimization-review.md`  
> 目的：把 MT 复盘里的 reference、人脸、批处理、验收建议拆成可落地阶段，避免再次把 CLI、receipt、provider payload、批处理执行和真实 API 调用混在同一波改动里。

## 1. 背景

MT 笔记的核心判断是对的：Plotloom 下一阶段的主要问题不是“能不能生成”，而是生产状态过于隐式。

具体隐式状态包括：

1. prompt 里写的 refs 和 provider 实际收到的 refs 可能不是同一组。
2. 角色资产有多个候选版本，prompt 或 characters.md 容易残留旧路径。
3. 人脸策略取决于 provider policy、素材类型和 reference role，不是单纯 prompt 文案问题。
4. 批量生成缺少可恢复状态，成功项容易被重复跑，失败项不容易继续。
5. contact sheet 和 review note 目前更像聊天里的临场流程，不是 repo 内固定产物。

本设计采用“先记录事实，再改变 provider 行为”的路线。第一阶段只做可解释、可 lint、可复盘的本地契约，不直接改变 Seedance / Dreamina 的真实提交语义。

## 2. 当前已完成能力

当前分支已经完成了第一波基础设施：

1. `video plan-references` 可以生成 provider-neutral reference map，并写入 clip-local `reference-map.toml`。
2. `video submit --reference-map` 可以把 reference intent 写进 receipt，用于追责和复盘。
3. `assets/cast/<character>/face-policy.toml` 支持三种真实使用路径：`safe-face-reference`、`text-only`、`cloud-face-asset`。
4. `plotloom validate` 会检查角色 face policy 的本地文件、provider、cloud asset id、body reference。
5. reference map 和 face policy 有交叉 lint，能发现 character ref 与策略不匹配。
6. `prompt compile/check --lint --reference-map` 能做 opt-in prompt slot lint。
7. receipt 增加 provider request summary 和失败分类，减少“失败了但不知道 provider 收到了什么”的情况。
8. 本地单元测试已验证过第一波能力；不包含 Seedance / Dreamina 真实 API E2E。

## 3. Non-goals

本设计不做：

1. 不直接调用 Seedance、Dreamina 或 imagegen 做 E2E。
2. 不把本地图片路径直接塞进 provider payload。
3. 不实现本地图片上传、签名 URL 或云端素材库管理。
4. 不承诺自动解决“同一张脸”，只把策略、输入和验收流程固定下来。
5. 不让 `video submit --first-frame/--reference-image` 在第一阶段直接改变 provider 请求。
6. 不在这一波引入 UI。

## 4. Implementation phases

### Phase 1: Prompt refs visibility and strict check

目标：提交前能明确看到“这个 clip 最终声明的 refs 是什么”，并能在本地严格失败。

新增命令：

```bash
plotloom prompt refs --episode ep001 --clip clip-03
plotloom prompt check --episode ep001 --clip clip-03 --strict-refs
```

行为：

1. `prompt refs` 默认读取 `episodes/<episode>/videos/<clip>/reference-map.toml`。
2. 输出 slot、kind、label、path/source、character/scene 等 clip-local refs。
3. 校验本地 reference 文件存在。
4. `--json` 输出稳定结构，供 agent 或脚本读取。
5. `prompt check --strict-refs` 在发现 unresolved `Image N`、reference slot 数量不匹配、reference map 缺失时失败。

暂缓：

1. `asset://...` 暂不进入普通 reference map，除非先定义清楚哪些字段代表本地文件、哪些字段代表 provider cloud asset。
2. `costume` / `face_anchor` 暂不加入通用 `REFERENCE_KINDS`，先通过 face policy 表达人脸和身体衣着策略。

### Phase 2: Explicit submit refs as intent-only sugar

目标：让用户能用更直接的 CLI 写 reference intent，但不直接改变 provider payload。

建议 CLI：

```bash
plotloom video submit \
  --episode ep001 \
  --clip clip-03 \
  --adapter volcengine-seedance \
  --mode reference-to-video \
  --first-frame assets/scenes/clip-03/selected.png \
  --reference-image character:rowan=assets/cast/rowan/selected-face-blocked.png
```

第一阶段语义：

1. 参数会被转换为 `reference_intent` 并写入 receipt。
2. receipt 记录 path、sha256、mtime、role、slot、character/scene label。
3. provider request summary 明确标注“not sent”或“intent only”，避免误以为真实 payload 已经接入。

暂缓：

1. 真正把 refs 转成 `PlotloomVideoRequest.reference_images`。
2. 上传本地文件到 provider 可访问 URL。
3. provider-specific role 编译。

### Phase 3: Face policy explain and smoke prompt

目标：把人脸策略从经验提醒变成一等命令。

新增命令：

```bash
plotloom face policy --character rowan --adapter volcengine-seedance
plotloom face smoke-prompt --character rowan --adapter volcengine-seedance
```

`face policy` 输出：

1. 当前角色策略：`safe-face-reference`、`text-only` 或 `cloud-face-asset`。
2. 当前 adapter 下推荐传什么、不推荐传什么。
3. 对 `cloud-face-asset`，显示 redacted cloud asset id，例如 `asset://asset-...-g6kpx` 或 `[REDACTED]`。
4. 明确说明 cloud face asset 是 face-only，需要本地 body / wardrobe reference 补充身体衣着。

`face smoke-prompt` 输出：

1. medium close-up。
2. front-left 3/4 face。
3. face visible at least 2 seconds。
4. no deep hat shadow。
5. face occupies 25-35% of frame。
6. minimal action, slight head turn。
7. 避免远景、骑马、峡谷、帽檐阴影这类会强化 archetype 的镜头。

### Phase 4: Canonical selected asset structure

目标：减少角色资产版本污染。

建议结构：

```text
assets/cast/<character>/
  selected.png
  selected-face-blocked.png
  metadata.toml
  candidates/
```

`metadata.toml` 建议字段：

```toml
character = "rowan"
selected_candidate = "candidates/v003.png"
selected_face_blocked = "selected-face-blocked.png"
face_policy = "face-policy.toml"
selected_at = "2026-05-04T00:00:00Z"
selected_by = "manual"
notes = "Canonical body/wardrobe reference for current production."
```

后续命令可以是：

```bash
plotloom asset select --character rowan --candidate assets/cast/rowan/candidates/v003.png
plotloom asset info --character rowan
```

第一刀只做结构和 lint，不自动改写历史 prompt。

### Phase 5: Image batch manifest with resume

目标：批量资产生成失败后可以继续，不重复跑已成功项。

建议命令：

```bash
plotloom image batch --manifest episodes/ep002/assets.toml --resume --skip-existing
```

manifest 示例：

```toml
[[items]]
kind = "scene"
episode = "ep002"
clip = "clip-07"
prompt_file = "episodes/ep002/prompts/scene-clip-07.md"
output = "assets/scenes/ep002-clip-07/candidates/v001.png"
status = "pending"
```

行为：

1. 默认 dry-run / local status，不直接调用 imagegen。
2. `--skip-existing` 看到 output 存在就标记 skipped。
3. 每项记录 pending、running、succeeded、failed、skipped。
4. 每项记录 started_at、finished_at、error、retry_count。
5. 单项失败不阻塞整个 batch。

真实 imagegen 执行应作为后续显式 flag 或单独 runner，不作为本阶段默认行为。

### Phase 6: Review contact sheet and review note

目标：把“看过候选图并做出选择”变成 repo 内产物。

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

1. candidate path。
2. pass/fail。
3. character consistency。
4. face visible。
5. refs used。
6. story beat clear。
7. provider artifacts。
8. selected/reroll/revise_prompt/ask_user。
9. reviewer and timestamp。

第一刀可以只支持静态图片候选，不支持视频帧抽取。

### Phase 7: Provider error taxonomy

目标：把 provider 错误变成可解释、可行动的本地诊断。

建议产物：

```text
docs/runbooks/provider-errors.md
```

后续命令：

```bash
plotloom doctor --explain-error InputImageSensitiveContentDetected.PrivacyInformation
```

字段：

1. provider。
2. raw code。
3. category。
4. likely cause。
5. safe next step。
6. whether retry is useful。

这应扩展现有失败分类，而不是另起一套错误系统。

## 5. Deferred provider payload work

真实 provider refs 接入应等以下条件满足后再做：

1. 明确本地文件如何上传到 provider 可访问 URL。
2. 明确火山 Seedance 对 `first_frame`、`reference_image`、face asset、body reference 的实际 payload 字段。
3. 明确 `asset://asset-...` 只能出现在 face policy / provider-specific input，还是可以进入 reference intent。
4. receipt 同时记录 Plotloom intent 和 provider native request summary。
5. 有本地 fake adapter / dry-run fixture 覆盖，不依赖真实 API E2E。

## 6. Acceptance criteria mapped to MT concerns

1. Reference 传递错误：`prompt refs` 和 receipt 能显示 clip-local reference intent。
2. 人脸一致性问题：`face policy` 和 `face smoke-prompt` 把策略与 smoke 测试固定下来。
3. ARK / VolcEngine 隐私拒绝：face policy 能明确 forbidden inputs 和 safer alternatives。
4. 红脸 / mesh overlay 误判：文档和 policy 输出不再推荐它作为可靠绕过方案。
5. 批量生成不可恢复：image batch manifest 有 resume、skip-existing 和 per-item 状态。
6. 验收靠人工临场组织：review contact sheet 和 review note 成为固定产物。
7. 角色资产版本污染：canonical selected asset 结构减少旧候选路径进入 prompt。
8. Provider 错误不可行动：provider error taxonomy 给出分类和下一步。

## 7. Recommended next implementation order

1. `prompt refs` + `prompt check --strict-refs`。
2. `face policy` + `face smoke-prompt`。
3. canonical selected asset lint。
4. `image batch --manifest --resume --skip-existing` 的 dry-run/local status。
5. `review contact-sheet` + `review-note.md`。
6. provider error taxonomy docs / doctor explain。
7. 最后再做真实 provider refs payload 编译。
