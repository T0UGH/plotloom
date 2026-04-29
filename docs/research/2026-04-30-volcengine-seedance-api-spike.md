# 火山方舟 Seedance API 调研与明日验证计划

> 日期：2026-04-30  
> 目标：确认火山方舟 Seedance API 是否可作为 Plotloom 的视频生成主后端候选，重点验证：能否调用、是否也排队很久、与即梦 CLI 相比是否更适合 async-first 生产链路。

## 1. 结论先行

火山方舟已经提供官方 **视频生成 API**，适合纳入 Plotloom 的自有 CLI adapter：

```text
POST /api/v3/contents/generations/tasks       # 创建视频生成任务
GET  /api/v3/contents/generations/tasks/{id}  # 查询任务状态 / 取 video_url
GET  /api/v3/contents/generations/tasks       # 查询任务列表
DELETE /api/v3/contents/generations/tasks/{id} # 取消或删除任务
```

它本质仍是异步任务模型，不应该被 Plotloom 设计成同步阻塞调用。明天拿到 `ARK_API_KEY` 后，最重要的不是“能不能生成”，而是记录：

- 提交耗时
- queued 持续多久
- running 持续多久
- succeeded 总耗时
- 失败码 / 权限问题 / 余额问题
- `video_url` 是否 24h 临时链接，需要立即下载归档

如果 API 排队明显短于即梦 CLI，则 Plotloom CLI 应优先实现 `volcengine-seedance` adapter；如果仍然排队很长，也至少比即梦 CLI 更适合做 submit/poll/download 的 async-first 结构。

## 2. 与 Plotloom 的产品判断

Plotloom 可以开始长自己的薄 CLI 层：

```text
Plotloom = skills + series repo spec + thin CLI + async video adapters
```

火山 API 对这个方向有价值，因为它天然提供 task id、task status、callback、list/delete，和 Plotloom 的候选视频归档模型匹配。

建议后续 CLI 形态：

```bash
plotloom video submit --adapter volcengine-seedance --clip episodes/ep001/videos/clip-01
plotloom video poll <task_id> --download-dir episodes/ep001/videos/clip-01/candidates
plotloom video list --adapter volcengine-seedance --status queued
plotloom video cancel <task_id>
```

CLI 只做确定性执行：提交、记录 task_id、轮询、下载、归档；prompt 生成和 rerun 判断仍由 Plotloom skills / agent 层负责。

## 3. 官方 API 关键信息

来源：火山方舟文档《视频生成 API》《创建视频生成任务 API》《查询视频生成任务 API》。截至本次调研页面最近更新时间为 2026-04-25。

### 3.1 鉴权与 SDK

- Base URL：`https://ark.cn-beijing.volces.com/api/v3`
- 鉴权：`Authorization: Bearer $ARK_API_KEY`
- Python SDK：`volcengine-python-sdk[ark]`
- SDK client：

```python
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ["ARK_API_KEY"],
)
```

videoclaw 里已有旧实现，路径：

```text
/Users/wangguiping/workspace/github/videoclaw/videoclaw/models/volcengine/seedance.py
```

它已经使用：

```python
client.content_generation.tasks.create(...)
client.content_generation.tasks.get(task_id=...)
```

但 videoclaw 当前实现是同步轮询直到完成，Plotloom 不应照搬；应该拆成 `submit` 和 `poll/download`。

### 3.2 创建任务

官方接口：

```text
POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
```

SDK 示例核心形态：

```python
create_result = client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[
        {"type": "text", "text": "..."},
        {
            "type": "image_url",
            "image_url": {"url": "https://.../image.jpg"},
            "role": "reference_image",
        },
    ],
    generate_audio=True,
    ratio="9:16",
    duration=15,
    watermark=False,
)

task_id = create_result.id
```

文档说明创建任务是异步接口，拿到 ID 后需要查询任务状态。

### 3.3 查询任务

官方接口：

```text
GET https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{id}
```

状态枚举：

```text
queued     排队中
running    运行中
succeeded  成功
failed     失败
expired    超时
cancelled  已取消；只支持排队中任务取消
```

成功后返回：

```text
content.video_url
content.last_frame_url   # 创建任务时 return_last_frame=true 才有
duration
ratio
resolution
framespersecond
usage.completion_tokens / total_tokens
service_tier
created_at / updated_at
```

注意：`video_url` 文档说明 24 小时后清理，需要 Plotloom 在 poll 到 succeeded 后立即下载到：

```text
episodes/epXXX/videos/clip-YY/candidates/vNNN.mp4
```

### 3.4 输入能力

Seedance 2.0 / 2.0 fast 支持：

- 文生视频：文本 prompt
- 图生视频首帧：1 张首帧图 + prompt
- 图生视频首尾帧：首帧 + 尾帧 + prompt
- 多模态参考生视频：参考图片 0-9、参考视频 0-3、参考音频 0-3、文本可选
- 有声视频 / 无声视频：`generate_audio`

关键约束：

- 图片 URL / Base64 / 素材 ID 均可。
- 单张图片小于 30MB；请求体不超过 64MB，大文件不要 Base64。
- 图片宽高长度 300-6000px；宽高比约束 `(0.4, 2.5)`。
- 参考视频单个 2-15s，最多 3 个，总时长不超过 15s。
- 参考音频单个 2-15s，最多 3 段，总时长不超过 15s；音频不能单独输入，至少要有图片或视频。
- Seedance 2.0 系列不支持直接上传含真人人脸的参考图/视频；需要授权素材、模型生成素材或虚拟人像路径。

### 3.5 时长 / 分辨率 / 比例

`duration`：

```text
seedance 2.0 & 2.0 fast: [4, 15] 秒，或 -1 让模型自选
seedance 1.5 pro: [4, 12] 秒，或 -1
seedance 1.0 系列: [2, 12] 秒
```

`ratio`：支持 `16:9`、`4:3`、`1:1`、`3:4`、`9:16`、`21:9`、`adaptive`。

`resolution`：常见为 `480p`、`720p`、`1080p`；文档注明 `seedance 2.0 fast` 不支持 `1080p`。

Plotloom MVP 建议默认：

```text
model = doubao-seedance-2-0-260128 或控制台启用后的等价 Model ID
ratio = 9:16
resolution = 720p
duration = 15
generate_audio = true/false 视测试目的分组
watermark = false
return_last_frame = true   # 便于连续 clip 接力
```

## 4. 即梦 CLI vs 火山 API

| 维度 | 即梦 CLI | 火山方舟 Seedance API |
|---|---|---|
| 接入门槛 | 登录即梦账号 / maestro | 需要 ARK_API_KEY、开通模型、余额或资源包 |
| 调用形态 | CLI submit + query_result | 官方 async task API |
| 排队观测 | CLI `list_task` / `query_result` | `queued/running/succeeded` 标准状态 |
| 归档 | CLI download_dir | `video_url` 需 24h 内下载 |
| 适合 Plotloom CLI | 可用，但偏外部工具包装 | 更适合做原生 adapter |
| 风险 | 登录态、会员、排队不透明 | 权限/余额/模型开通、仍可能排队 |

判断：火山 API 更适合作为 Plotloom 自有 CLI 的主候选；即梦 CLI 保留为低门槛/备用 adapter。

## 5. 明天拿 key 后的验证计划

### 5.1 前置检查

不要打印 key。只检查是否存在：

```bash
python3 - <<'PY'
import os
print('ARK_API_KEY exists:', bool(os.environ.get('ARK_API_KEY')))
PY
```

确认 SDK：

```bash
python3 - <<'PY'
from volcenginesdkarkruntime import Ark
print('ark sdk ok')
PY
```

### 5.2 最小文生视频探针

目标：避免素材限制，先测 API 是否可用、排队多久。

建议 prompt：

```text
A vertical 9:16 cinematic short-drama opening. A young delivery man stands in the rainy entrance of a luxury corporate tower at night. He holds a food delivery bag, looks confused as the glass doors open, and several executives turn toward him in shock. Dramatic lighting, realistic style, no subtitles, no watermark, no logo.
```

建议脚本：

```python
import os, time, json
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ["ARK_API_KEY"],
)

started = time.time()
res = client.content_generation.tasks.create(
    model=os.environ.get("ARK_SEEDANCE_MODEL", "doubao-seedance-2-0-260128"),
    content=[{"type": "text", "text": PROMPT}],
    ratio="9:16",
    resolution="720p",
    duration=15,
    generate_audio=False,
    watermark=False,
    return_last_frame=True,
    execution_expires_after=3600,
)
print(json.dumps({"task_id": res.id, "submit_elapsed_sec": time.time() - started}, ensure_ascii=False))

last = None
while True:
    task = client.content_generation.tasks.get(task_id=res.id)
    now = time.time()
    if task.status != last:
        print(json.dumps({
            "elapsed_sec": round(now - started, 1),
            "status": task.status,
            "created_at": getattr(task, "created_at", None),
            "updated_at": getattr(task, "updated_at", None),
            "duration": getattr(task, "duration", None),
            "ratio": getattr(task, "ratio", None),
            "resolution": getattr(task, "resolution", None),
            "error": getattr(task, "error", None).model_dump() if getattr(task, "error", None) else None,
        }, ensure_ascii=False))
        last = task.status
    if task.status in ("succeeded", "failed", "expired", "cancelled"):
        print(task)
        break
    time.sleep(30)
```

验收：

- 能创建任务并返回 `cgt-*`。
- 能观察到 `queued -> running -> succeeded` 或失败原因。
- 如果成功，下载 `content.video_url` 到本地候选目录并 ffprobe。

### 5.3 最小参考图生视频探针

目标：验证 Plotloom character-grid / selected image 作为参考图的可行性。

输入策略：

- 先用非真人/AI 生成图，规避 Seedance 2.0 真人脸限制。
- `role = reference_image` 测多模态参考生视频。
- 另测 `role = first_frame` 看首帧稳定性。

要记录：

- 对 character-grid 这种设定表是否能正确理解，还是需要单张角色图。
- `reference_image` 与 `first_frame` 哪个更适合短剧角色一致性。
- 是否需要先从 character-grid 派生单张 half-body reference。

### 5.4 排队对比实验

同一个 15s 竖屏 prompt 分别跑：

```text
A. 即梦 CLI text2video / multimodal2video
B. 火山 API text task
C. 火山 API image/reference task
```

记录表：

| 后端 | submit_id/task_id | 提交时间 | queued 时长 | running 时长 | 总耗时 | 成功/失败 | 备注 |
|---|---|---:|---:|---:|---:|---|---|
| dreamina | | | | | | | |
| volc-t2v | | | | | | | |
| volc-i2v | | | | | | | |

如果火山 API 仍排队很久，Plotloom CLI 仍要 async-first；如果排队显著短，优先实现火山 adapter。

## 6. 对 Plotloom CLI 的实现建议

### 6.1 Adapter contract

建议 `plotloom video submit` 输出一段可持久化 TOML，而不是隐藏 DB：

```toml
# episodes/ep001/videos/clip-01/task.volcengine.toml
adapter = "volcengine-seedance"
task_id = "cgt-..."
model = "doubao-seedance-2-0-260128"
status = "queued"
submitted_at = "2026-04-30T...+08:00"
ratio = "9:16"
resolution = "720p"
duration = 15
prompt_file = "../../video-prompts-en.md"
```

这不是 workflow runtime，只是 clip 目录旁的可见任务收据。若不想固定文件名，也可以用 `tasks/<task_id>.toml`。

### 6.2 Poll/download behavior

`plotloom video poll`：

1. 读取 task TOML 或直接接收 task_id。
2. 调 `GET /contents/generations/tasks/{id}`。
3. 更新状态字段。
4. 成功时立即下载 `video_url` 到下一个候选号：
   `candidates/vNNN.mp4`。
5. 写入最小下载记录：URL 不长期依赖，最终以本地 mp4 为准。
6. 跑 `ffprobe`，记录 duration/resolution/fps。

### 6.3 不要做的事

- 不要同步阻塞等待几十分钟才返回。
- 不要把 API key 写入 repo 或任务 TOML。
- 不要把 task 状态放到隐藏数据库。
- 不要把火山 API 绑定为 Plotloom core；它只是 adapter。
- 不要默认 Base64 大文件；优先 URL / 已上传素材，避免 64MB 请求体限制。

## 7. 风险 / 未决问题

1. **模型开通与余额**：官方提示需账户余额 >= 200 元或已购资源包，否则可能无法开通 seedance 2.0 / fast。
2. **排队不可预判**：API 有 queued/running 状态，但实际排队时长要明天实测。
3. **真人脸限制**：Seedance 2.0 系列不支持直接上传含真人人脸参考图/视频；短剧角色图如果偏真人，需要走授权素材/模型生成素材/虚拟人像或只用文本/非真人参考。
4. **临时 URL**：生成视频 URL 24h 后清理，必须立即转存。
5. **模型 ID**：文档示例为 `doubao-seedance-2-0-260128`，实际可用 Model ID 以贵平账号控制台开通情况为准。
6. **有声视频成本和耗时**：`generate_audio=true` 可能增加耗时和成本，明天应分别测有声/无声。

## 8. 建议明天决策标准

如果满足：

```text
API 可用 + 15s 竖屏任务总耗时稳定可接受 + 下载/ffprobe 成功
```

则 Plotloom 下一步应优先实现：

```text
plotloom video submit/poll --adapter volcengine-seedance
```

如果 API 排队与即梦 CLI 一样长：

```text
仍实现 async-first adapter，但不把火山作为唯一主后端；保留 dreamina/mock/videoclaw adapter 并行。
```

如果 API 权限/余额阻塞：

```text
先落 CLI adapter skeleton + mock/fake E2E；等账号开通后补真实验证。
```
