# VolcEngine Seedance Adapter Notes

## Purpose

Document how Plotloom should call 火山方舟 Seedance through the official async task API. This is an adapter contract, not core product logic.

## Preflight

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

Requirements:

- `ARK_API_KEY`
- model access enabled in the account console
- account balance/resource package sufficient
- `volcengine-python-sdk[ark]` installed

Never write `ARK_API_KEY` into repo, receipts, logs, or chat.

## Client

```python
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ["ARK_API_KEY"],
)
```

## Prompt / reference format

- Use Seedance-style continuous narrative prompts with timeline beats, camera path, dialogue window, and sound intent.
- Do not use HappyHorse-specific `character1` labels by default.
- Bind references through `content[]` roles such as `first_frame` or `reference_image`, and reinforce the role in natural language.
- `generate_audio=true/false` is a native parameter; prompt can describe sound/dialogue but adapter must pass the parameter explicitly.

Example provider prompt:

```text
Use the first-frame image as the opening frame. Use the character reference image only for identity, outfit, and facial consistency.
A vertical 9:16 cinematic short-drama scene. 0-3s: the delivery man steps into a rainy luxury lobby...
Dialogue window: the heiress whispers, "You are the only heir."
Sound: rain outside, marble footsteps, tense low strings. No subtitles, no logo, no watermark.
```

## Submit

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

For image/reference modes, add `image_url` items:

```python
content = [
    {"type": "text", "text": prompt},
    {
        "type": "image_url",
        "image_url": {"url": "https://.../first-frame.png"},
        "role": "first_frame",  # or reference_image
    },
]
```

## Poll / result

```python
task = client.content_generation.tasks.get(task_id=task_id)
```

Status values:

```text
queued / running / succeeded / failed / expired / cancelled
```

On `succeeded`, download `task.content.video_url` immediately to `candidates/vNNN.volcengine-seedance.mp4`; VolcEngine video URLs are temporary.

## Constraints

- default Plotloom test: `9:16`, `720p`, `duration=15`, `watermark=False`
- Seedance 2.0 / fast duration: 4-15s or `-1`
- ratio: `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, `adaptive`
- `seedance2.0fast` may not support 1080p; start with 720p
- image size: 300-6000px, <30MB, aspect ratio about `(0.4, 2.5)`
- request body limit: 64MB; prefer URL over base64 for large files
- Seedance 2.0 series does not support direct uploads of real-human face reference images/videos; use AI-generated/authorized/virtual character references

## Existing reference

videoclaw has a blocking implementation at:

```text
/Users/wangguiping/workspace/github/videoclaw/videoclaw/models/volcengine/seedance.py
```

Plotloom should reuse lessons but split it into async `submit` and `poll/download`.
