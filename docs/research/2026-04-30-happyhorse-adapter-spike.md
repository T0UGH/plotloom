# HappyHorse 1.0 Adapter Spike

> Date: 2026-04-30 09:23 CST  
> Agent: Nova  
> Scope: how Plotloom should integrate HappyHorse as a video-generation adapter

## 一句话结论

HappyHorse 1.0 适合接入为 Plotloom 的 **可选 async video adapter**，优先走 `fal.ai` 的官方 API partner 接口；不要把它做成核心依赖，也不要把网页站点/非官方 wrapper 当成稳定接入面。

## 可信来源判断

### 1. 官方/可信接入面：fal.ai

fal 页面明确写了：

- HappyHorse-1.0 is available on fal as an official API partner.
- endpoints:
  - `alibaba/happy-horse/text-to-video`
  - `alibaba/happy-horse/image-to-video`
  - `alibaba/happy-horse/reference-to-video`
  - `alibaba/happy-horse/video-edit`
- supports native synchronized audio.
- queue-style API via `fal.subscribe` / request id / status / result.

对 Plotloom 来说，fal 是当前最适合写 adapter 的路径。

### 2. MuAPI / GitHub wrapper：可参考，不宜作为默认

GitHub 上有 `Anil-matcha/Awesome-Happy-Horse-1.0-API-and-Prompt` 和 `Anil-matcha/happyhorse-comfyui`，提供 MuAPI endpoint 示例：

- `/api/v1/happy-horse-1-text-to-video-{1080p|720p}`
- `/api/v1/happy-horse-1-image-to-video-{1080p|720p}`
- `/api/v1/happy-horse-1-reference-to-video-{1080p|720p}`
- `/api/v1/happy-horse-1-video-edit-{1080p|720p}`

但这些更像社区/第三方 wrapper，且 README 提到 Pro/Business access、closed beta/GA 等限制。可以借 schema 思路，不建议 Plotloom MVP 默认依赖。

### 3. 模型背景

CNBC 报道确认 Alibaba 是 HappyHorse-1.0 背后团队；Artificial Analysis 有 HappyHorse model family 页面。fal 页面引用其在 Video Arena 的表现：

- Text-to-Video no-audio: #1, Elo 1333
- Image-to-Video no-audio: #1, Elo 1392
- Text-to-Video with audio: #2, Elo 1205
- Image-to-Video with audio: #2, Elo 1161

注意：不要在 Plotloom 文档里宣称“已开源权重可本地跑”。当前可靠接入是 API，不是本地模型权重。

## 能力映射到 Plotloom

| HappyHorse endpoint | Plotloom 用法 | 备注 |
|---|---|---|
| `text-to-video` | 无参考图的 clip 生成 | 直接用 `video-prompts-en.md` 提取出的 prompt |
| `image-to-video` | 用 reference still / selected image 作为首帧生成 clip | 输入单张 `image_url` |
| `reference-to-video` | 用角色/场景参考图做一致性生成 | `image_urls` 1-9 张；prompt 中用 `character1` 等引用 |
| `video-edit` | reroll/局部编辑已选 clip | 输入 `video_url`，可带 0-5 张参考图；`audio_setting=auto/origin` |

最适合短剧的是 `reference-to-video`：可以把 Plotloom 的 `character-grid.png`、场景图、cover/reference still 上传后作为 `image_urls`，prompt 里显式写 `character1`、`character2`。

## fal API schema 要点

### Common

- env/auth: `FAL_KEY`
- resolution: `720p` / `1080p`
- duration: `3`-`15` seconds
- aspect ratio: `16:9`, `9:16`, `1:1`, `4:3`, `3:4`
- seed: optional integer `0-2147483647`
- safety checker: `enable_safety_checker=true` by default
- output: `video.url` plus media metadata such as width/height/fps/duration/frames

### Text-to-video

Input:

```json
{
  "prompt": "...",
  "aspect_ratio": "9:16",
  "resolution": "1080p",
  "duration": 15,
  "enable_safety_checker": true
}
```

### Image-to-video

Input:

```json
{
  "image_url": "https://.../first-frame.png",
  "prompt": "...",
  "resolution": "1080p",
  "duration": 15,
  "enable_safety_checker": true
}
```

Image constraints:

- JPEG/JPG/PNG/BMP/WEBP
- at least 300px dimensions
- aspect ratio between `1:2.5` and `2.5:1`
- max 10 MB

### Reference-to-video

Input:

```json
{
  "prompt": "character1 enters the neon alley...",
  "image_urls": ["https://.../character-grid.png", "https://.../scene.png"],
  "aspect_ratio": "9:16",
  "resolution": "1080p",
  "duration": 15,
  "enable_safety_checker": true
}
```

Reference constraints:

- 1-9 images
- JPEG/JPG/PNG/WEBP
- shortest side at least 400px; 720p+ recommended
- max 10 MB each
- prompt references are `character1`, `character2`, ... in image order

### Video edit

Input:

```json
{
  "video_url": "https://.../source.mp4",
  "prompt": "Recolor the sky to a deep purple sunset.",
  "reference_image_urls": ["https://.../style.png"],
  "resolution": "1080p",
  "audio_setting": "auto",
  "enable_safety_checker": true
}
```

Source video constraints:

- MP4/MOV, H.264 recommended
- 3-60s input, output capped at first 15s
- max 100 MB
- longer side <= 2160px, shorter side >= 320px
- fps > 8

## Plotloom CLI adapter shape

Recommended adapter name:

```text
happyhorse-fal
```

Commands should reuse existing async video command surface:

```bash
plotloom video submit \
  --episode ep001 \
  --clip clip-01 \
  --adapter happyhorse-fal \
  --mode reference-to-video \
  --resolution 1080p \
  --duration 15

plotloom video poll --episode ep001 --clip clip-01
```

Allowed modes:

```text
text-to-video
image-to-video
reference-to-video
video-edit
```

Adapter selection rule:

1. If clip has explicit first-frame image -> `image-to-video`.
2. Else if clip has character/scene reference URLs -> `reference-to-video`.
3. Else -> `text-to-video`.
4. If user asks to edit an existing clip -> `video-edit`.

For MVP, do not make mode inference too magical. It is acceptable to require `--mode` until the prompt/reference artifact contract is settled.

## Task receipt

Use repo-visible receipt, same as other video adapters:

```toml
adapter = "happyhorse-fal"
provider = "fal.ai"
endpoint = "alibaba/happy-horse/reference-to-video"
request_id = "..."
status = "queued"
submitted_at = "2026-04-30T09:23:00+08:00"
mode = "reference-to-video"
model = "happyhorse-1.0"
ratio = "9:16"
resolution = "1080p"
duration = 15
audio = "native"
prompt_file = "episodes/ep001/video-prompts-en.md"
clip = "clip-01"
```

Poll result should update status and download final output to:

```text
episodes/ep001/videos/clip-01/candidates/vNNN.mp4
```

Then run `ffprobe` and keep enough media facts in the receipt for debugging.

## Implementation notes

### Python SDK path

Use `fal-client` as optional extra:

```bash
pip install fal-client
```

Pseudo-code:

```python
import fal_client

handler = fal_client.submit(
    "alibaba/happy-horse/reference-to-video",
    arguments={
        "prompt": prompt,
        "image_urls": image_urls,
        "aspect_ratio": ratio,
        "resolution": resolution,
        "duration": duration,
        "enable_safety_checker": True,
    },
)
request_id = handler.request_id
```

Polling can use the fal queue/result API or SDK handler/result methods, depending on the stable SDK surface available in the environment.

### File upload

HappyHorse endpoints expect URLs, not raw local paths. For local Plotloom files:

1. upload local images/videos through fal file upload;
2. use returned URL in request;
3. never store API key or signed upload details in Git;
4. only store sanitized public/temporary media URL if needed for debugging.

### Prompt extraction

fal prompt max is 2500 characters. `plotloom prompt extract/check` must ensure:

- not passing the full Markdown artifact;
- English model-ready prompt is <= 2500 chars;
- for reference mode, image order and `character1..character9` names are explicit;
- duration target is within 3-15s.

## Fit / Trade-off

Pros:

- Native synchronized audio, so it fits the “no separate voice CLI in MVP” direction.
- Supports T2V/I2V/Ref2V/Edit in one provider family.
- Aspect ratios and 3-15s durations match short-video / short-drama clip needs.
- fal official API partner is cleaner than browser/CLI automation.

Cons / risks:

- API cost/access depends on fal availability and account quota.
- 15s max duration means it is clip-oriented, not one full episode generation.
- Prompt max 2500 chars forces stronger prompt compression than long Seedance-style narrative prompts.
- Reference image upload/URL lifecycle must be handled by adapter.
- Model ranking and API surface are new; stability needs real key-based probe.

## Recommendation

Do not replace the current VolcEngine Seedance priority yet.

Recommended priority:

1. `mock` for deterministic E2E.
2. `volcengine-seedance` as current first real adapter candidate.
3. `happyhorse-fal` as next high-value real adapter because it gives native audio + ref2v/edit through official API.
4. `dreamina` as fallback/comparison path where authenticated CLI is already available.

Next validation should be a small key-based probe:

```bash
FAL_KEY=... plotloom video submit --adapter happyhorse-fal --mode text-to-video --duration 3 --resolution 720p
plotloom video poll --episode ep001 --clip clip-01
ffprobe candidates/v001.mp4
```

Acceptance:

- request id returned;
- receipt written;
- final mp4 downloaded;
- audio stream exists or absence is explicitly recorded;
- duration/resolution/aspect ratio match request or mismatch is clearly reported.

## Sources

- https://fal.ai/happyhorse-1.0
- https://fal.ai/models/alibaba/happy-horse/text-to-video/api
- https://fal.ai/models/alibaba/happy-horse/image-to-video/api
- https://fal.ai/models/alibaba/happy-horse/reference-to-video/api
- https://fal.ai/models/alibaba/happy-horse/video-edit/api
- https://artificialanalysis.ai/video/model-families/happyhorse
- https://www.cnbc.com/2026/04/10/alibaba-happyhorse-ai-video-model-benchmark-reveal.html
- https://github.com/Anil-matcha/Awesome-Happy-Horse-1.0-API-and-Prompt
- https://github.com/Anil-matcha/happyhorse-comfyui
