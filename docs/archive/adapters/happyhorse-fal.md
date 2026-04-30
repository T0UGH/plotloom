# fal / HappyHorse Adapter Notes

> Archived: this adapter is not implemented in the current Plotloom CLI. The active video adapters are `dreamina-cli`, `volcengine-seedance`, and local `mock`.

## Purpose

Document how Plotloom should call HappyHorse through fal.ai. This is an adapter contract, not core product logic.

## Preflight

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

Requirements:

- funded fal account
- API-scope key stored as `FAL_KEY`
- `fal-client` installed

Never write `FAL_KEY` into repo, receipts, logs, or chat.

## Endpoints

```text
alibaba/happy-horse/text-to-video
alibaba/happy-horse/image-to-video
alibaba/happy-horse/reference-to-video
alibaba/happy-horse/video-edit
```

## Prompt / reference format

- T2V/I2V prompt max: 2500 chars.
- Ref2V prompt must refer to image order as `character1`, `character2`, ... up to `character9`.
- Video edit prompt should refer to reference images as `@Image1`, `@Image2`, ... up to `@Image5`.
- Do not pass Plotloom's full Markdown prompt file directly; compile a short provider prompt first.

Ref2V example:

```text
character1 is the young delivery man. character2 is the wealthy heiress.
A vertical 9:16 cinematic short-drama scene: character1 enters the luxury lobby while character2 turns in shock.
Spoken dialogue: character2 says, "You are the only heir."
Ambient sound: rain outside, lobby footsteps, tense low strings.
No subtitles, no logo, no watermark.
```

## Submit

```python
import fal_client

handler = fal_client.submit(
    "alibaba/happy-horse/text-to-video",
    arguments={
        "prompt": prompt,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "duration": 15,
        "enable_safety_checker": True,
    },
)
request_id = handler.request_id
```

## Poll / result

fal queue statuses: `IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`.

Poll should use endpoint + request id from the Plotloom task receipt, then download `result["video"]["url"]` to `candidates/vNNN.happyhorse-fal.mp4` and run ffprobe.

## Local media inputs

HappyHorse expects URLs. Upload local files first:

```python
url = fal_client.upload_file("/path/to/reference.png")
```

Use uploaded URL as `image_url`, `image_urls`, `reference_image_urls`, or `video_url` depending on mode.

## Constraints

- prompt <= 2500 chars
- duration 3-15s
- resolution `720p` or `1080p`
- ratio `16:9`, `9:16`, `1:1`, `4:3`, `3:4`
- image refs: JPEG/JPG/PNG/WEBP, max 10MB; ref2v needs 1-9 images
- video edit input: MP4/MOV, max 100MB, 3-60s input, output capped at 15s

## Pricing snapshot

Observed on 2026-04-30:

```text
720p:  $0.14/s
1080p: $0.28/s
```

Run smoke tests at 720p first.
