# Plotloom 三家视频后端接入设计：即梦 CLI / fal HappyHorse / 火山方舟 Seedance

> Date: 2026-04-30 09:49 CST  
> Agent: Nova  
> Scope: 本期同时接入并对比三家视频生成后端，目标是看实际效果、速度、成本、稳定性，而不是提前押注单一模型。

## 结论先行

本期视频 adapter 应该同时接入三家：

```text
1. dreamina-cli          # 即梦 CLI：低门槛、已有本机登录/会员验证，适合作为可立即跑的基线
2. happyhorse-fal        # fal / HappyHorse：官方 API partner，音频原生，适合海外短剧效果试验
3. volcengine-seedance   # 火山方舟 Seedance：官方 async API，最适合 Plotloom 自有 adapter 形态
```

实现上不要做三个各自独立的流程；应统一到同一个 Plotloom video adapter contract：

```text
prompt/reference assets -> submit -> visible task receipt -> poll/download -> ffprobe -> candidate mp4
```

本期判断标准不是“哪个最强”，而是用同一组 prompt / reference asset / 15s 竖屏片段，实测：

- 能不能稳定提交；
- 排队与总耗时；
- 视频质量和短剧可用性；
- 音频/口型/环境声；
- reference/角色一致性；
- 成本；
- 失败可诊断性。

## 统一命令面

建议先不做复杂推断，显式 adapter + mode：

```bash
plotloom video submit \
  --repo ~/plotloom_repo/<slug> \
  --episode ep001 \
  --clip clip-01 \
  --adapter dreamina-cli \
  --mode text-to-video \
  --prompt-file episodes/ep001/video-prompts-en.md \
  --duration 15 \
  --ratio 9:16 \
  --resolution 720p

plotloom video poll \
  --repo ~/plotloom_repo/<slug> \
  --episode ep001 \
  --clip clip-01 \
  --adapter dreamina-cli
```

三家统一支持的最小 mode：

```text
text-to-video   # prompt-only smoke/prototype
image-to-video  # first-frame/reference still -> video
```

Provider-specific extended mode：

```text
happyhorse-fal: reference-to-video, video-edit
volcengine-seedance: reference-image / first-frame / first+last-frame / multimodal refs via content roles
dreamina-cli: image2video; 未来可补 multiframe2video / multimodal2video
```

## 统一目录与任务收据

每次 submit 在 clip 目录写一个 provider-specific receipt：

```text
episodes/ep001/videos/clip-01/
  tasks/
    dreamina-cli-20260430-095000.toml
    happyhorse-fal-20260430-095100.toml
    volcengine-seedance-20260430-095200.toml
  candidates/
    v001.dreamina-cli.mp4
    v002.happyhorse-fal.mp4
    v003.volcengine-seedance.mp4
  selected.mp4
```

不建议继续只用单个 `task.<adapter>.toml`，因为本期同一 clip 要并排跑三家、多轮抽卡；`tasks/<adapter>-<timestamp>.toml` 更适合对比实验。

通用 receipt 字段：

```toml
adapter = "happyhorse-fal"
provider = "fal.ai"
mode = "reference-to-video"
status = "submitted"
submitted_at = "2026-04-30T09:50:00+08:00"
updated_at = "2026-04-30T09:50:00+08:00"

repo = "~/plotloom_repo/example"
episode = "ep001"
clip = "clip-01"
prompt_file = "episodes/ep001/video-prompts-en.md"
prompt_sha256 = "..."

ratio = "9:16"
resolution = "720p"
duration = 15
generate_audio = true
seed = 123456

remote_task_id = "..."
remote_status = "IN_QUEUE"
remote_url = ""          # 临时 URL 可记录但不能依赖
candidate_path = ""      # 成功下载后填写

submit_elapsed_sec = 0.8
queued_elapsed_sec = 0.0
running_elapsed_sec = 0.0
total_elapsed_sec = 0.0

error_code = ""
error_message = ""
```

成功下载后追加媒体事实：

```toml
[media]
path = "episodes/ep001/videos/clip-01/candidates/v002.happyhorse-fal.mp4"
duration = 15.03
width = 720
height = 1280
fps = 24.0
has_audio = true
video_codec = "h264"
audio_codec = "aac"
```

## Provider 1：即梦 CLI / `dreamina-cli`

### 定位

- 本期基线 adapter。
- 优点：本机已有 CLI 经验；用户账号如果已登录且 `maestro` 可直接跑。
- 缺点：登录态/会员/队列都依赖外部桌面状态；不如 API 干净。

### Preflight

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina user_credit
```

验收：

- CLI 存在；
- 账号已登录；
- `vip_level: maestro`；
- 不读取、不打印、不提交 `~/.dreamina_cli/credential.json`。

### Text-to-video submit

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina text2video \
  --prompt "<plain prompt>" \
  --duration=15 \
  --ratio=9:16 \
  --video_resolution=720p \
  --model_version=seedance2.0fast \
  --poll=0
```

关键参数：

- `duration`: 4-15s，默认 5；Plotloom 必须显式传 15 或指定值。
- `ratio`: `1:1`, `3:4`, `16:9`, `4:3`, `9:16`, `21:9`。
- `video_resolution`: Seedance 2.0 family 只支持 `720p`。
- `model_version`: `seedance2.0`, `seedance2.0fast`, `seedance2.0_vip`, `seedance2.0fast_vip`。

Submit 输出中解析 `submit_id`，写入 receipt。

### Image-to-video submit

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina image2video \
  --image ./reference.png \
  --prompt "<plain prompt>" \
  --duration=15 \
  --video_resolution=720p \
  --model_version=seedance2.0fast \
  --poll=0
```

注意：`image2video` 的 ratio 由输入图片推断，不在命令里显式设置。因此 Plotloom 参考图/首帧图应提前裁成目标比例，尤其短剧默认 `9:16`。

### Poll/download

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina query_result \
  --submit_id=<submit_id> \
  --download_dir=episodes/ep001/videos/clip-01/candidates
```

`query_result` 无 `--poll`，Plotloom 自己循环：

1. 每 30-60s 查询；
2. 解析 Queueing / Generating / Finish / Failed；
3. 成功后把下载文件重命名为 `vNNN.dreamina-cli.mp4`；
4. ffprobe；
5. 更新 receipt。

## Provider 2：fal / HappyHorse / `happyhorse-fal`

### 定位

- 本期海外向、音频原生效果试验 adapter。
- 优点：官方 API partner、T2V/I2V/Ref2V/Edit 都有、原生同步音频。
- 缺点：成本较高；prompt max 2500 chars；本地素材需先上传成 URL。

### Preflight

```bash
python3 - <<'PY'
import os
print('FAL_KEY exists:', bool(os.environ.get('FAL_KEY')))
PY
python3 - <<'PY'
import fal_client
print('fal_client ok')
PY
```

可选价格检查：

```bash
curl "https://api.fal.ai/v1/models/pricing?endpoint_id=alibaba/happy-horse/text-to-video" \
  -H "Authorization: Key $FAL_KEY"
```

### Endpoints

```text
alibaba/happy-horse/text-to-video
alibaba/happy-horse/image-to-video
alibaba/happy-horse/reference-to-video
alibaba/happy-horse/video-edit
```

### Python submit

```python
import fal_client

handler = fal_client.submit(
    "alibaba/happy-horse/reference-to-video",
    arguments={
        "prompt": prompt,                  # <= 2500 chars
        "image_urls": image_urls,          # 1-9 reference images
        "aspect_ratio": "9:16",
        "resolution": "720p",             # or 1080p
        "duration": 15,                    # 3-15
        "enable_safety_checker": True,
    },
)
print(handler.request_id)
```

### Python status/result

fal queue lifecycle：`IN_QUEUE -> IN_PROGRESS -> COMPLETED`。

```python
status = handler.status()
result = handler.get()
video_url = result["video"]["url"]
```

如果 Plotloom poll 是另一个进程，receipt 至少需要保存：

```toml
endpoint = "alibaba/happy-horse/reference-to-video"
request_id = "..."
```

poll 时通过 SDK/queue API 按 endpoint + request_id 取 status/result。

### File upload

HappyHorse 的 image/video inputs 需要 URL。Plotloom 对本地素材要做：

```python
url = fal_client.upload_file("/path/to/reference.png")
```

然后把 URL 放入 `image_url` / `image_urls` / `reference_image_urls`。

不要把 `FAL_KEY`、签名 URL、上传凭证写进 repo；receipt 里可以只保留 `local_path` 与 `uploaded=true`，必要时保存脱敏 URL 域名。

### Modes

- `text-to-video`: prompt-only。
- `image-to-video`: 单张首帧 `image_url`。
- `reference-to-video`: 1-9 张参考图，prompt 中用 `character1`, `character2` 对应顺序。
- `video-edit`: 输入已有 `video_url`，可带 0-5 张参考图，`audio_setting=auto|origin`。

### Pricing for test plan

当前 observed：

```text
720p:  $0.14/s
1080p: $0.28/s
```

本期试验建议全部先 720p：

- 3s smoke：约 $0.42；
- 15s clip：约 $2.10；
- 4 clips x 2 candidates：约 $16.80。

## Provider 3：火山方舟 Seedance / `volcengine-seedance`

### 定位

- 本期最像“正式 API adapter”的主候选。
- 优点：官方 async task API；状态、取消、列表、下载都适合 Plotloom；支持图/视频/音频多模态参考。
- 缺点：账号开通、余额、模型 ID、真人脸限制、临时 URL。

### Preflight

```bash
python3 - <<'PY'
import os
print('ARK_API_KEY exists:', bool(os.environ.get('ARK_API_KEY')))
PY
python3 - <<'PY'
from volcenginesdkarkruntime import Ark
print('ark sdk ok')
PY
```

### Python client

```python
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ["ARK_API_KEY"],
)
```

### Text submit

```python
res = client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[{"type": "text", "text": prompt}],
    ratio="9:16",
    resolution="720p",
    duration=15,
    generate_audio=True,
    watermark=False,
    return_last_frame=True,
)
task_id = res.id
```

### Reference / first-frame submit

```python
content = [
    {"type": "text", "text": prompt},
    {
        "type": "image_url",
        "image_url": {"url": "https://.../first-frame.png"},
        "role": "first_frame",  # or reference_image
    },
]

res = client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=content,
    ratio="9:16",
    resolution="720p",
    duration=15,
    generate_audio=True,
    watermark=False,
    return_last_frame=True,
)
```

输入约束：

- 图片 URL / Base64 / 素材 ID 均可；大文件优先 URL，避免 64MB request body。
- 单张图片 <30MB，尺寸 300-6000px，宽高比约 `(0.4, 2.5)`。
- 参考图片 0-9；参考视频 0-3；参考音频 0-3。
- Seedance 2.0 系列不支持直接上传含真人人脸参考图/视频；短剧角色优先用 AI 生成角色图。

### Poll/download

```python
task = client.content_generation.tasks.get(task_id=task_id)
print(task.status)  # queued/running/succeeded/failed/expired/cancelled

if task.status == "succeeded":
    video_url = task.content.video_url
```

成功后必须立即下载，因为 `video_url` 约 24h 后清理。

### Cancel/list

官方 API 支持：

```text
GET    /api/v3/contents/generations/tasks
DELETE /api/v3/contents/generations/tasks/{id}
```

Plotloom 本期至少实现 cancel；list 可以后置为诊断命令。

## 三家对比实验矩阵

### Round 0：preflight

| Adapter | Check | Pass condition |
|---|---|---|
| dreamina-cli | `dreamina user_credit` | logged in + maestro |
| happyhorse-fal | `FAL_KEY` + import `fal_client` | key exists + SDK ok |
| volcengine-seedance | `ARK_API_KEY` + import Ark | key exists + SDK ok |

### Round 1：3s / 最低成本 smoke

| Adapter | Mode | Duration | Resolution | Purpose |
|---|---|---:|---|---|
| dreamina-cli | text-to-video | 4s | 720p | CLI submit/poll/download baseline |
| happyhorse-fal | text-to-video | 3s | 720p | API/key/billing smoke |
| volcengine-seedance | text-to-video | 4s | 720p | API/model/queue smoke |

说明：Dreamina/VolcEngine Seedance 最小时长通常 4s；HappyHorse/fal 支持 3s。

### Round 2：15s 竖屏 prompt-only

同一条英文短剧 prompt，三家都跑 `9:16 / 720p / 15s / audio on where possible`。

记录：

| Adapter | task_id | submit sec | queued sec | running sec | total sec | cost | has_audio | result |
|---|---|---:|---:|---:|---:|---:|---|---|
| dreamina-cli | | | | | | | | |
| happyhorse-fal | | | | | | | | |
| volcengine-seedance | | | | | | | | |

### Round 3：reference image / character consistency

输入同一个 AI 角色图或 character-grid 派生图。

建议优先用单张 half-body/reference still，不直接把整个 character-grid 丢给模型；如果要测 grid，可作为独立分组。

| Adapter | Mode | Reference strategy | Watch |
|---|---|---|---|
| dreamina-cli | image2video | first-frame image | 起手帧稳定、角色是否漂移 |
| happyhorse-fal | reference-to-video | `image_urls=[character, scene]` | `character1` 是否可控 |
| volcengine-seedance | reference_image / first_frame | same image, compare roles | 哪个更适合短剧连续性 |

### Round 4：音频/对白

只在 prompt 里加入简单英文对白窗口，观察：

- 是否生成语音；
- 口型是否贴；
- 环境声/BGM 是否自然；
- 是否需要 Plotloom 后续独立 voice/subtitle adapter。

## 本期实现顺序

```text
Phase A: 统一 adapter skeleton / receipt / ffprobe / download helpers
Phase B: dreamina-cli adapter（最快可跑基线）
Phase C: happyhorse-fal adapter（API + upload + queue）
Phase D: volcengine-seedance adapter（API + URL/base64 + queue + 24h download）
Phase E: 三家同 prompt 对比报告
```

不要先写复杂 UI，不要写 daemon，不要接入隐藏 DB。

## CLI skeleton 建议

最低文件：

```text
plotloom/
  cli.py
  video.py
  adapters/
    base.py
    dreamina_cli.py
    happyhorse_fal.py
    volcengine_seedance.py
  media.py
  receipts.py
```

如果当前 repo 还没有 Python package，可以先保留 `scripts/adapters/*.py` 路线：

```text
scripts/adapters/dreamina_cli.py
scripts/adapters/happyhorse_fal.py
scripts/adapters/volcengine_seedance.py
scripts/video_submit.py
scripts/video_poll.py
```

但设计上要向未来 `plotloom video submit/poll` 收敛。

## 风险与处理

| Risk | Adapter | Handling |
|---|---|---|
| 登录态/会员失效 | dreamina-cli | preflight 明确失败，不自动重登 |
| API key/余额缺失 | fal/volc | doctor 只检查存在，不打印 key；失败信息写 receipt |
| URL 过期 | fal/volc | poll 成功立即下载，本地 mp4 为准 |
| prompt 太长 | happyhorse-fal | `prompt check` 限制 2500 chars |
| Seedance 真人脸限制 | volcengine | 用 AI 角色图；不要上传真人参考 |
| 本地素材无法直接传 | happyhorse-fal | upload_file 转 URL |
| 排队很久 | all | submit 立即返回；poll 可重复；不阻塞 chat turn |
| 成本不可控 | fal/volc | 先 720p smoke；receipt 记录估算/实际 cost |

## 决策建议

本期别争默认后端，直接并排接入：

```text
default for test baseline: dreamina-cli
best API-shaped candidate: volcengine-seedance
best audio-native overseas candidate: happyhorse-fal
```

最终根据三家同题实测结果决定下一期默认：

- 如果火山速度/质量稳定：它做主 adapter；
- 如果 HappyHorse 音频/短剧观感明显更强：它做海外短剧优先 adapter；
- 如果即梦效果够好且最易用：保留 CLI fallback，但不让它成为唯一依赖。
