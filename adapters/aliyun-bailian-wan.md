# Aliyun Bailian Wan Adapter Notes

## Purpose

Document how Plotloom should call Alibaba Cloud Model Studio / Bailian Wan video APIs. This replaces the earlier fal / HappyHorse route in the first real-provider implementation plan.

## Preflight

```bash
python3 - <<'PY'
import os
print('DASHSCOPE_API_KEY exists:', bool(os.environ.get('DASHSCOPE_API_KEY')))
PY
python3 - <<'PY'
import dashscope
print('dashscope ok')
PY
```

Requirements:

- Bailian / DashScope API key for the same region as the selected model.
- Account balance or resource package sufficient for Wan video generation.
- `dashscope` installed if the SDK path is used, or `requests` for direct HTTP.

Never write `DASHSCOPE_API_KEY` into repo files, receipts, logs, or chat.

## Endpoints

Use the DashScope async task API first:

```text
POST https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis
GET  https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}
```

Required submit headers:

```text
X-DashScope-Async: enable
Authorization: Bearer $DASHSCOPE_API_KEY
Content-Type: application/json
```

## Prompt / reference format

- Start with `text-to-video` using Wan T2V models such as `wan2.6-t2v`.
- Keep provider prompts compact and production-facing; do not pass the full Plotloom Markdown prompt file directly.
- Do not use HappyHorse-specific `character1` or `@Image1` labels.
- For image/video input modes, prefer reachable HTTPS URLs. Reject local-only inputs until Plotloom has an explicit upload/import path that returns provider-reachable URLs.

Example T2V payload:

```json
{
  "model": "wan2.6-t2v",
  "input": {
    "prompt": "A vertical 9:16 cinematic short-drama scene in a rainy luxury lobby..."
  },
  "parameters": {
    "size": "720*1280",
    "prompt_extend": true,
    "watermark": false
  }
}
```

## Submit

```python
import os
import requests

resp = requests.post(
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
    headers={
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}",
        "Content-Type": "application/json",
    },
    json={
        "model": "wan2.6-t2v",
        "input": {"prompt": prompt},
        "parameters": {"size": "720*1280", "prompt_extend": True, "watermark": False},
    },
    timeout=30,
)
task_id = resp.json()["output"]["task_id"]
```

## Poll / result

```python
task = requests.get(
    f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=30,
).json()
```

Normalize DashScope task states into Plotloom receipt statuses. On success, download the returned video URL immediately to `candidates/vNNN.aliyun-bailian-wan.mp4`, then run ffprobe.

## Constraints

- Model, endpoint URL, and API key must belong to the same region.
- Video generation is async and normally takes minutes; never run provider submit from default tests.
- `text-to-video` is the first smoke target.
- `image-to-video`, first/last-frame, and VACE/edit flows require a small docs/API confirmation before implementation because their endpoint/body shapes differ by Wan model family.

## References

- https://help.aliyun.com/zh/model-studio/text-to-video-guide
- https://help.aliyun.com/zh/model-studio/legacy-wan-text-to-video-api-reference
- https://help.aliyun.com/zh/model-studio/image-to-video-api-reference/
- https://help.aliyun.com/zh/model-studio/wan-video-editing-api-reference
