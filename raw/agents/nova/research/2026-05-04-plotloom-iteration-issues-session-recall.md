---
title: Plotloom 近期卡点复盘：reference、prompt、adapter、QA 四层契约
author: Nova
agent: nova
created: 2026-05-04 15:46 CST
material_type: research-note
status: raw
tags:
  - plotloom
  - short-drama
  - video-generation
  - reference-images
  - character-consistency
  - seedance
  - dreamina
  - qa
source:
  - Feishu session recall, 2026-04-29 to 2026-05-04
related:
  - raw/agents/mt/research/2026-05-04-plotloom-production-pipeline-optimization-review.md
  - raw/agents/nova/research/2026-04-29-plotloom-skill-enhancement-seedance-imagegen2.md
  - raw/agents/nova/research/2026-04-28-plotloom-agent-neutral-skill-pack-research.md
---

# Plotloom 近期卡点复盘：reference、prompt、adapter、QA 四层契约

## 一句话结论

Plotloom 下一轮不该先扩模型或堆功能，而应先把“我传了什么 reference、模型实际用了什么、结果是否符合、失败怎么追责”这条链路打硬。当前核心问题是 **reference / prompt / adapter / QA 四层契约还不够硬**。

## 背景

这份笔记来自 2026-04-29 至 2026-05-04 几轮 Plotloom 生产和调研的 session recall，涉及：

- Seedance / 火山 / Volcengine 视频生成；
- Dreamina / 即梦 CLI；
- HappyHorse/fal 调研；
- 人脸 reference / 角色一致性；
- first-frame / last-frame / clip 连续性；
- delogo / watermark / 拼接验收；
- Plotloom skill pack 与 CLI contract。

## 1. 人脸 / 角色一致性：当前最大不确定性

### 已观察到的卡点

- Seedance / 火山对 photoreal human reference 可能触发隐私或真人检测：
  - `InputImageSensitiveContentDetected.PrivacyInformation`
  - `input image may contain real person`
- 动物拟人可以绕过部分 policy，但用户体验不理想；贵平明确表示“不太想用动物”。
- 单靠文字描述“同一个人”不够，容易出现：脸漂、年龄漂、服装漂、体型漂。
- `character-grid.png` 有价值，但如果太真人照片感，可能被 Seedance 拒绝。

### 后续需要回答的问题

1. Plotloom 是否要定义 **人类角色 reference 的安全等级**？例如：
   - text-only blocking
   - stylized human
   - AI synthetic human
   - authorized human asset
   - animal fallback
2. `character-grid.png` 是否应区分：
   - `photoreal-grid`
   - `stylized-grid`
   - `provider-safe-grid`
3. 火山 / Seedance 是否需要单独支持 `asset://<ASSET_ID>` 授权资产路径？
4. 对真人短剧，默认是否先跑 **text-only + 首帧生成**，而不是直接上传人脸 grid？

### 建议方向

人脸问题要从 prompt 技巧升级成 Plotloom 的一等策略：每个角色应有 provider-specific face policy，告诉 agent 对某个 adapter 应该传什么、不该传什么。

## 2. reference 传递：语义太混，容易传错

### 已观察到的卡点

- prompt 里写“Image 1 是角色参考”，不等于 adapter 真按这个顺序传给 provider。
- 当前 Seedance adapter 更像统一传 `reference_image`，不会自动把第 1 张当 `first_frame`。
- HappyHorse 调研也证明必须区分：
  - `first_frame`：控制第一帧 / 镜头起点；
  - `reference_images`：控制脸、服装、风格、场景；
  - `last_frame`：承接上一 clip，通常要 ffmpeg 抽帧后再传。
- 参考图顺序必须和 provider request 顺序严格一致，否则 prompt 里的“图片1 / 图片2”会错位。

### 后续需要回答的问题

1. Plotloom 是否需要显式 `reference-map.toml` 或在 task receipt 中记录 reference mapping？例如：
   - `image_1 = character:Ethan`
   - `image_2 = scene:gala`
   - `image_3 = first_frame:clip-01-last-frame`
2. CLI 是否要强制打印 / 记录最终 provider request 的 reference 顺序？
3. 是否禁止 agent 只在 prompt 里写 reference，而没有实际传文件？
4. `plotloom video submit` 是否应该支持明确参数：
   - `--first-frame`
   - `--last-frame`
   - `--reference character=...`
   - `--reference scene=...`
5. 每次生成后，QA 是否必须检查：
   - reference 是否真的被使用；
   - 第一帧是否贴近 `first_frame`；
   - 角色是否贴近 `character-grid`。

### 建议方向

reference 语义应从“prompt 里的自然语言约定”变成 adapter request 的显式字段，并进入 task receipt，方便复盘。

## 3. 首尾帧 / 分段连续性：应变成一等公民

### 已观察到的卡点

- 15 秒 clip 之间容易空间断裂。
- “接上上一段”只写在 prompt 里不可靠。
- 需要真实抽取上一段最后一帧，再作为下一段 first-frame / reference。
- EP1–EP8 拼长视频时也证明：最终拼接不是难点，难点是每段之间的故事和视觉承接。

### 后续需要回答的问题

1. 每个 selected clip 是否默认生成：
   - `first-frame.jpg`
   - `last-frame.jpg`
   - `contact-sheet.jpg`
2. 下一 clip 生成时，是否默认把上一 clip 的 `last-frame.jpg` 纳入 reference？
3. `plotloom select` 是否自动抽帧并写 handoff note？
4. video prompt 模板是否必须包含：
   - opening state
   - ending frame
   - handoff intent
5. QA 是否增加 “clip-to-clip continuity” 检查，而不是只看单 clip 是否可用？

### 建议方向

首尾帧不应只是 QA 辅助产物，而应成为 clip 之间的正式 handoff artifact。

## 4. Prompt 结构：需要从“shot prompt”升级为“叙事任务”

### 已确认原则

Seedance prompt 不应该是 shot list。正确链路应是：

```text
episode beat / director brief
→ continuous cinematic narrative task
→ provider-specific prompt
→ candidate video
```

### 当前问题

- `plotloom-shot-prompts` 名字容易误导成“逐镜头生成”。
- prompt 如果太工程化、编号太多，模型反而不稳定。
- prompt 如果放中文台词 / VO，容易生成字幕或乱码。
- provider-facing prompt 应该因模型不同而编译，不应一份 `video-prompts-en.md` 原样喂所有 provider。

### 后续需要回答的问题

1. `plotloom-shot-prompts` 是否需要改名，或在内部明确为 `video-narrative-prompts`？
2. 是否新增 `director brief` 层，但不强制生成一堆传统影视文档？
3. provider prompt 是否要有 `compile` 阶段：
   - Dreamina / Seedance prompt
   - HappyHorse prompt
   - Volcengine prompt
4. 是否明确规则：
   - 用户审中文创意源；
   - provider 使用英文 / 视觉化 prompt；
   - VO / 字幕默认后期处理，不直接塞进视频模型。
5. QA 是否检查 prompt 里有没有：
   - reference 顺序错；
   - 中文对白导致字幕风险；
   - 同时多人说话；
   - 镜头指令冲突；
   - 没有尾帧描述。

### 建议方向

Prompt 层应从“写给模型看的最终文本”拆成：中文创意源、provider-specific compiled prompt、QA checklist 三层。

## 5. Adapter 层：需要从“能调起来”变成“可追责”

### 已观察到的卡点

- Dreamina 队列长，失败原因不透明。
- query / download 会超时，但不能因此重烧 credits。
- Volcengine 已有成功生成，但 reference 语义还不够透明。
- HappyHorse 适合补 Ref2V / I2V / video edit，但还没有实测。
- 不同 provider 参数不同，不能用统一字段硬塞。

### 后续需要回答的问题

1. 每个 adapter 是否必须实现：
   - `capabilities()`
   - `validate_request()`
   - `compile_native_request()`
   - `submit()`
   - `poll()`
   - `download()`
2. task receipt 是否必须记录：
   - source prompt hash
   - compiled prompt hash
   - reference file list + order
   - provider native request 摘要
   - task id
   - cost / duration / queue time
3. 失败时是否禁止“盲重试”，必须先分类：
   - 上传失败
   - 内容审核失败
   - provider generation failed
   - download timeout
   - queue timeout
4. Dreamina download timeout 是否默认走 `video_url + curl` 恢复，而不是重提任务？
5. 三 provider 是否进入测试矩阵：
   - Dreamina = 当前最快 baseline
   - Volcengine Seedance = 长期 API 主候选
   - HappyHorse fal = audio / ref2v / video-edit 候选

### 建议方向

Adapter 层需要记录“编译后的真实请求”，而不是只记录创意 prompt。后续任何脸漂、reference 错位、失败重试，都应能追到具体 request。

## 6. QA / 验收：现在偏人工，应产品化

### 已经有效但还没制度化的 QA

- `ffprobe`
- decode check
- `blackdetect`
- contact sheet
- vision QA
- `final-selection.md`
- 用户 accept / reroll
- delogo / crop 后重新验证

### 后续需要回答的问题

1. 每个 candidate 是否必须生成：
   - ffprobe metadata
   - contact sheet
   - first / last frame
   - QA note
2. QA checklist 是否按类型拆：
   - face / character identity
   - reference adherence
   - action clarity
   - story beat clarity
   - subtitles / watermark
   - first / last-frame continuity
   - aspect ratio / crop / black frame
3. final 拼接是否必须只用 `selected.mp4`，禁止 glob 最新文件？
4. 用户提供“真 clip”时是否标记为 source of truth，默认不 crop、不 delogo？
5. delogo 是否必须保留 raw candidate，并写 postprocess note？

### 建议方向

“看过了 / 可用了”必须变成 repo 内可复盘工件，而不是聊天里一句话。

## 7. Repo / artifact 契约：MVP 可以轻，但不能模糊

### 当前不够明确的状态

- selected candidate 的选择理由；
- reference 顺序；
- task receipt；
- prompt compile 结果；
- clip handoff；
- postprocess 记录。

### 后续需要回答的问题

1. 是否接受每个 clip 下有：

```text
tasks/
refs/
candidates/
selected.mp4
selected-note.md
first-frame.jpg
last-frame.jpg
contact-sheet.jpg
```

2. `task.<adapter>.toml` 是否作为异步任务唯一状态载体？
3. 是否需要 `reference-map.toml`，还是 receipt 足够？
4. `final-selection.md` 是否成为 episode final 的强制产物？
5. generated media 是否继续不进 Git，只记录路径 / 说明？

### 建议方向

Plotloom 仍应保持 repo-first / skill-first / thin CLI，不需要重 runtime。但 repo 内必须留够可追责的轻量状态。

## 建议优先级

### P0：reference 语义收口

- 明确 `first_frame / last_frame / reference_images`。
- receipt 记录实际传参顺序。
- QA 检查 reference 是否生效。

### P1：人脸策略

- 定义 Seedance 真人 / 合成人脸安全路径。
- 测一组 text-only / stylized-human / synthetic-human / `asset://`。
- 不再默认退回动物；动物只做 fallback。

### P2：prompt 编译层

- 中文创意源 → provider-specific prompt。
- 禁字幕 / 禁中文文本规则固化。
- Seedance 连续叙事任务模板强化。

### P3：QA 自动化

- candidate 自动生成 contact sheet、首尾帧、ffprobe。
- final 拼接前后强验证。
- selected / final selection 固化。

### P4：多 provider 对照

- Dreamina / Volcengine / HappyHorse 同 prompt 小样测试。
- 记录质量、速度、reference 能力、成本、失败模式。

## 后续产品化问题清单

1. Plotloom 是否要增加 `plotloom prompt refs/check`？
2. `video submit` 是否要暴露 `--first-frame` / `--last-frame` / `--reference-image`？
3. 每个 adapter 的 task receipt 是否必须记录 compiled prompt 与 reference 顺序？
4. 人脸策略是否以 `face policy` 命令或角色 metadata 的方式落地？
5. selected clip 是否默认产出首尾帧和 contact sheet？
6. QA 是否从人工流程固化成 `plotloom review` 系列命令？
7. `plotloom-shot-prompts` 是否需要在概念上改为连续叙事任务，而不是 shot list？

## 结论

Plotloom 当前最该优化的不是“生成更多视频”，而是让生产链路从隐式经验变成可验证契约：reference 显式、prompt 可编译、adapter 可追责、QA 可复盘。这样后续无论接 Dreamina、Volcengine Seedance、HappyHorse，还是换其他 provider，都能保持短剧生产的稳定性和可交接性。
