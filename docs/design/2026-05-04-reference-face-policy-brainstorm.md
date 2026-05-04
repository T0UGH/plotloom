# Plotloom Reference / Face Policy Brainstorm

> 日期：2026-05-04  
> 状态：Brainstorm / design note  
> 来源：`docs/research/production-pipeline/2026-05-04-plotloom-iteration-issues-session-recall.md`  
> 目的：把人脸策略、reference 传递、prompt 编译、adapter 追责拆成可分阶段落地的小契约，避免一次 patch 同时改变 CLI、receipt、provider request 和重试行为。

## 1. 当前判断

这轮优化不应该先追求“更多 adapter 参数”或“更聪明的自动生成”，而应该先把生产链路里最容易失控的四件事拆清楚：

1. 人脸 reference 是否适合传给当前 provider。
2. 用户/agent 以为传了哪些 reference。
3. adapter 实际向 provider 传了哪些 reference。
4. 生成失败、脸漂、首帧不对时，可以追到哪一层。

核心原则：**先记录事实，再改变行为。**

也就是说，第一刀不应该直接重写 `volcengine-seedance` 的真实 payload，也不应该把失败分类、重试策略、人脸策略、prompt compiler 混在一个实现里。先把 schema 和 receipt 记录稳定下来，再逐个 provider 接入。

## 2. Non-goals

本轮暂不做：

- 不改变现有 provider submit 行为。
- 不默认上传本地 reference 图片到远程 URL。
- 不把本地文件路径直接塞进 provider `image_url.url`。
- 不把 Dreamina / Seedance / HappyHorse 的参数硬塞进一个统一字段。
- 不自动重试失败任务。
- 不承诺“同一张脸”一定成功，只记录策略和输入。
- 不把 prompt 改写、adapter native request 记录、失败分类一次性混进主流程。

## 3. Face Policy

### 3.1 问题

人脸一致性不是单纯 prompt 问题。Seedance / 火山可能拒绝 photoreal human reference，尤其是看起来像真实人物照片的人脸素材。当前如果 agent 直接上传 `character-grid.png`，可能会触发 privacy / real person policy。

### 3.2 建议契约

把人脸策略定义成角色资产和 provider 之间的策略，而不是一次 submit 的临时技巧。策略不需要分得太细，应该贴近用户真实会选择的三条路。

建议字段：

```toml
[characters.ethan.face]
strategy = "cloud-face-asset"
provider = "volcengine-seedance"
cloud_asset = "asset://asset-20260224225526-g6kpx"
body_reference = "assets/cast/ethan/body-wardrobe.png"
```

候选策略：

```text
safe-face-reference
text-only
cloud-face-asset
```

`safe-face-reference` 表示传本地安全脸图，例如素描人脸、带遮罩的人脸、低真人感 character grid。

`text-only` 表示不传任何人脸 reference，只用文字描述角色外貌和气质。

`cloud-face-asset` 表示使用火山引擎素材库里的云端人脸素材，同时搭配本地身体/衣着 reference。这里要把“脸”和“身体衣着”拆开记录，不能把云端脸当普通本地 reference 图。

示例：

```toml
[characters.ethan.face]
strategy = "safe-face-reference"
path = "assets/cast/ethan/safe-face-mask.png"
note = "Sketch-like masked face, not photoreal."

[characters.mira.face]
strategy = "text-only"
description = "Young East Asian woman, sharp gaze, restrained expression, elegant but tired."

[characters.li-chen.face]
strategy = "cloud-face-asset"
provider = "volcengine-seedance"
cloud_asset = "asset://asset-20260224225526-g6kpx"
body_reference = "assets/cast/li-chen/body-wardrobe.png"
```

### 3.3 第一刀实现

第一刀只做记录和 lint：

- `plotloom validate` 或未来的 `plotloom asset info` 能指出角色缺少 face strategy。
- lint 能检查 `safe-face-reference.path` 和 `cloud-face-asset.body_reference` 是否存在。
- lint 能检查 `cloud-face-asset` 是否提供 provider 和 cloud asset id。
- video task receipt 可以记录本次采用的 face policy。
- CLI 可以接受显式 override，但默认值应该来自角色/资产配置。

不建议第一刀就让 CLI 自动选择或替换图片；自动选择属于第二阶段。

## 4. Reference Map

### 4.1 问题

prompt 里写“Image 1 是角色参考”不等于 adapter 真的按这个顺序传给 provider。更糟的是，不同 provider 对 `first_frame`、`reference_image`、`last_frame` 的语义不同。

### 4.2 建议契约

新增一个 provider-neutral 的 reference intent，先用于记录，不直接等价为 provider payload。

建议结构：

```toml
[[references]]
slot = 1
kind = "first_frame"
path = "episodes/ep001/images/references/clip-01/first-frame.jpg"
source = "selected-video-last-frame"
character = ""
scene = ""

[[references]]
slot = 2
kind = "character"
path = "assets/cast/ethan/provider-safe-grid.png"
source = "asset"
character = "ethan"
scene = ""

[[references]]
slot = 3
kind = "scene"
path = "assets/scenes/gala/selected.png"
source = "asset"
character = ""
scene = "gala"
```

字段含义：

- `slot`：agent/prompt 可以引用的稳定顺序。
- `kind`：`first_frame | last_frame | character | scene | style | generic`。
- `path`：series repo 内路径，或未来的 `asset://...`。
- `source`：这个 reference 从哪里来，例如 `asset`、`generated-image`、`selected-video-last-frame`。
- `character` / `scene`：可选索引字段，便于 QA 和复盘。

### 4.3 Receipt 记录

task receipt 应记录两层信息：

```toml
[[reference_intent]]
slot = 1
kind = "character"
path = "assets/cast/ethan/provider-safe-grid.png"
character = "ethan"

[[provider_request.references]]
slot = 1
provider_role = "reference_image"
uri = "https://..."
source_path = "assets/cast/ethan/provider-safe-grid.png"
```

第一层是 Plotloom 语义；第二层是真实 provider request 摘要。

第一阶段可以只写 `reference_intent`。等上传/签名 URL 流程明确后，再写 `provider_request.references`。

## 5. CLI Surface

### 5.1 第一阶段

先做不会影响真实 provider submit 的命令和参数：

```bash
plotloom video plan-references \
  --episode ep001 \
  --clip clip-01 \
  --first-frame episodes/ep001/images/references/clip-01/first-frame.jpg \
  --reference character:ethan=assets/cast/ethan/provider-safe-grid.png \
  --reference scene:gala=assets/scenes/gala/selected.png
```

输出：

- human stdout 打印 slot 顺序。
- `--json` 输出结构化 reference intent。
- 可选写入 `episodes/ep001/videos/clip-01/reference-map.toml`。

### 5.2 第二阶段

`plotloom video submit` 支持读取 reference map：

```bash
plotloom video submit \
  --episode ep001 \
  --clip clip-01 \
  --adapter volcengine-seedance \
  --reference-map episodes/ep001/videos/clip-01/reference-map.toml
```

此时 submit 仍然可以先只把 map 写进 receipt，不一定立刻传给 provider。

### 5.3 第三阶段

adapter 增加显式 compile step：

```python
native_request = adapter.compile_native_request(request)
```

`compile_native_request()` 负责把 Plotloom reference intent 转成 provider-specific payload summary。`submit()` 只发送已经编译好的 native request。

## 6. Prompt Compiler

第4点可以做，但应独立成 prompt compiler，不和 reference schema 混写。

建议链路：

```text
episode beat / director brief
-> clip narrative task
-> provider-specific prompt
-> reference map
-> adapter native request
```

第一阶段先加一个只读命令：

```bash
plotloom video compile-prompt \
  --episode ep001 \
  --clip clip-01 \
  --adapter volcengine-seedance
```

这个命令只输出 compiled prompt 和 lint warnings，不 submit。

Lint 重点：

- prompt 引用了 Image 1 / Image 2，但没有 reference map。
- prompt 有中文对白或字幕风险。
- prompt 像 shot list 而不是 continuous cinematic task。
- prompt 没有 opening state / ending frame。
- prompt 声称同一角色，但没有 character reference intent 或 face policy。

## 7. Adapter Observability

第5点有道理，但应该单独做。

建议顺序：

1. 只记录 provider native request summary。
2. 再记录 provider error summary。
3. 再做 failure classification。
4. 最后才讨论 retry policy。

不要第一刀就把 poll/download 异常全部吞掉并改写 status。这样容易改变现有命令的可见失败方式。

建议字段：

```toml
[provider_request]
adapter = "volcengine-seedance"
model = "..."
mode = "text-to-video"
duration = 5
ratio = "9:16"

[[provider_request.references]]
slot = 1
provider_role = "reference_image"
source_path = "assets/cast/ethan/provider-safe-grid.png"
uri_kind = "remote-url"

[provider_error]
code = "InputImageSensitiveContentDetected.PrivacyInformation"
message = "..."
stage = "submit"
```

失败分类字段如 `failure_category`、`retryable` 可以后加，不要和 native request 记录同一刀。

## 8. Recommended Patch Slices

### Slice A: Reference Intent Only

新增 `reference-map.toml` schema 和 parser，增加只读/规划命令，不改 submit。

文件范围预计：

- `plotloom/video/reference_map.py`
- `plotloom/commands/video.py`
- `tests/test_video_reference_map.py`
- `docs/design/2026-05-04-reference-face-policy-brainstorm.md`

### Slice B: Face Policy Metadata

定义角色/资产级 face strategy schema，并加 lint，不改 provider。第一版只支持三种策略：`safe-face-reference`、`text-only`、`cloud-face-asset`。

文件范围预计：

- `plotloom/assets/...` 或现有角色解析模块
- `plotloom/commands/validate.py`
- `tests/test_face_policy.py`

### Slice C: Receipt Intent Recording

`video submit` 读取 reference map，并把 intent 写入 receipt，但 provider payload 保持当前行为。

文件范围预计：

- `plotloom/video/receipts.py`
- `plotloom/commands/video.py`
- `tests/test_video_receipts.py`

### Slice D: Provider Native Request Summary

给 adapter 加 `compile_native_request()` 或等价 helper，只记录 provider request summary。

文件范围预计：

- `plotloom/video/adapters/base.py`
- `plotloom/video/adapters/volcengine_seedance.py`
- `plotloom/video/adapters/dreamina_cli.py`
- `tests/test_volcengine_adapter.py`

### Slice E: Failure Classification

单独加入失败分类和 retryable 语义。这个 slice 必须有旧行为兼容讨论。

文件范围预计：

- `plotloom/video/errors.py`
- `plotloom/commands/video.py`
- `plotloom/video/receipts.py`
- `tests/test_video_poll_compare.py`

## 9. Suggested Next Step

下一步建议只做 Slice A。

原因：

- 它解决第2点最核心的“我以为传了什么”问题。
- 不改现有 adapter submit，风险低。
- 能为第1点 face policy 和第4点 prompt lint 提供共同输入。
- 后面如果要接 Seedance / HappyHorse 的 first-frame / last-frame，也有稳定数据结构。

Slice A 的验收标准：

- 能生成/解析 `reference-map.toml`。
- 能保证 slot 顺序稳定。
- 能拒绝不存在的本地 path。
- 能在 human stdout 和 JSON stdout 中打印最终 reference 顺序。
- 不改变 `plotloom video submit` 的现有行为。
