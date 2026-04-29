# ffmpeg / ffprobe Reference

## Probe
Use `ffprobe -v error <video>` to confirm a file is readable. The helper may also inspect codec, resolution, frame rate, stream count, and duration.

## Stitch Strategy
The MVP stitch helper accepts explicit selected clip paths and writes `final.mp4`.

Decision:
- If clips are compatible, concat is enough.
- If codec/resolution/frame rate differs, normalize to one simple profile before concat.
- If any input is unreadable, fail with the exact path and stderr.

## Simple Output Profile
When normalization is needed, prefer:
- container: mp4
- video: H.264, yuv420p
- audio: AAC
- target aspect ratio from series/episode if known; otherwise preserve helper default.

## Output
Final output path:

```text
episodes/epXXX/videos/final.mp4
```

## Delivery
When requested, deliver `final.mp4` via nova-lark / lark-cli. Feishu is delivery, not the state center. The repo file remains canonical.

## Non-Goals
No edit decisions, subtitles, BGM, mixing, queue, runtime, or dashboard in MVP.
