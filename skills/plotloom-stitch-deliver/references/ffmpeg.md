# ffmpeg / ffprobe Reference

## Probe
Use `ffprobe -v error <video>` to confirm a file is readable. The helper may also inspect codec, resolution, frame rate, and duration.

## Stitch
The MVP stitch helper accepts explicit selected clip paths and writes `final.mp4`. It should either concat compatible files or normalize to one simple profile before concat.

## Output
Final output path:

```text
episodes/epXXX/videos/final.mp4
```

## Delivery
When requested, deliver `final.mp4` via nova-lark / lark-cli. Feishu is delivery, not the state center.

## Non-Goals
No edit decisions, subtitles, BGM, mixing, queue, runtime, or dashboard in MVP.
