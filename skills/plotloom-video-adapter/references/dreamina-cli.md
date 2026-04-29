# Dreamina CLI Adapter Reference

## Verified Facts

- preflight: `dreamina user_credit`
- requires: `vip_level = maestro`
- text-only submit: `dreamina text2video --prompt "..." --duration=15 --ratio=9:16 --model_version=seedance2.0fast_vip`
- image/reference submit: prefer `dreamina multimodal2video --image ... --prompt "..." ...`; use `image2video` for one first-frame image, `multiframe2video` for frame-to-frame transitions
- query: `dreamina query_result --submit_id=...`
- download: `dreamina query_result --submit_id=... --download_dir=...`
- `query_result` has no `--poll` flag; query loop must be external.
- `text2video`, `image2video`, `multimodal2video`, and `multiframe2video` support `--poll N` immediately after submit.
- failure modes: not logged in / not maestro / quota insufficient / queueing / generation failed

## Important Format Boundary

Plotloom `video-prompts.md` / `video-prompts-en.md` are **internal human-readable artifacts**. Do **not** pass the whole Markdown block to Dreamina CLI.

Dreamina CLI expects:

```text
one prompt string via --prompt
plus command flags such as --duration, --ratio, --model_version, --image, --video, --audio
```

Bad adapter input:

```text
## clip-01
- Duration hint: 15-20s
- Reference images:
- assets/cast/lin-qiao/character-grid.png — preserve identity
- Prompt: ...
- Ending frame / handoff point: ...
```

Good adapter input:

```bash
dreamina text2video \
  --prompt "A tense modern short-drama scene: in a glossy corporate boardroom on a rainy night, Lin Qiao steps out of an elevator carrying a delivery bag... End with her hand pausing over a hidden family seal. No subtitles, no watermark, no logo." \
  --duration=15 \
  --ratio=9:16 \
  --model_version=seedance2.0fast_vip
```

## Current Environment Note

In the current Nova/Hermes host, the binary has been observed at:

```text
/Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina
```

Recommended preflight shape in this environment:

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina user_credit
```

Expected account permission:

```text
vip_level: maestro
```

## Command Selection

### `text2video`

Use only when there are **no actual local reference images/videos/audio** to upload. Text mentions of `assets/cast/.../character-grid.png` are not used by this command unless their content is rewritten into the prompt.

Supported by current help:

```text
model_version: seedance2.0, seedance2.0fast, seedance2.0_vip, seedance2.0fast_vip
ratio: 1:1, 3:4, 16:9, 4:3, 9:16, 21:9
duration: 4-15 seconds, default 5
video_resolution: 720p
```

Example:

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina text2video \
  --prompt "$PROMPT" \
  --duration=15 \
  --ratio=9:16 \
  --model_version=seedance2.0fast_vip \
  --poll=30
```

### `image2video`

Use when there is one first-frame/reference image.

```bash
dreamina image2video \
  --image ./first-frame.png \
  --prompt "$PROMPT" \
  --duration=15 \
  --model_version=seedance2.0fast_vip
```

### `multimodal2video`

Use when Plotloom has character grids, scene references, prior clips, or audio references. This corresponds to Dreamina “全能参考”.

```bash
dreamina multimodal2video \
  --image ./assets/cast/lin-qiao/character-grid.png \
  --image ./assets/cast/shen-mo/character-grid.png \
  --prompt "$PROMPT" \
  --duration=15 \
  --ratio=9:16 \
  --video_resolution=720p \
  --model_version=seedance2.0fast_vip
```

Limits from current help:

```text
image <= 9
video <= 3
audio <= 3
duration 4-15 seconds
```

### `multiframe2video`

Use for frame-to-frame transitions. Inputs: 2-20 images. For N images, provide N-1 transition prompts/durations if using 3+ images.

## Adapter Translation Rules

When converting `video-prompts-en.md` to CLI:

1. Select one `clip-YY` block.
2. Extract only the model-facing prose from `Prompt`, `Continuity rules`, `Camera motion`, `Dialogue / audio window`, and `Ending frame`.
3. Convert reference-image bullets into real CLI flags only if the files exist and the command supports them.
4. For Dreamina CLI with reference images, use `multimodal2video`, not `text2video`.
5. Translate `Duration hint` into `--duration`, clamped to 4-15 seconds.
6. Translate aspect ratio into `--ratio`; for short-drama default use `9:16` unless the user chooses otherwise.
7. Add negative constraints inside the prompt string: no subtitles, no watermark, no logo, no garbled text.
8. Store submit/query commands in a visible adapter note.

## Submit / Query Skeleton

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina <command> ... --poll=30
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina query_result --submit_id=<submit_id> --download_dir=<candidate-dir>
```

## Queue Note Shape

Store a visible Markdown note near the clip folder:

```markdown
# Dreamina Queue Note

- adapter: dreamina-cli
- command: text2video | image2video | multimodal2video | multiframe2video
- clip: clip-01
- submit_id: <redacted-if-sharing>
- status: Queueing | Generating | Finish | Failed
- query command: `... query_result --submit_id=... --download_dir=...`
- last checked:
- next action:
```

## Queue Handling

Dreamina may return `gen_status: querying` with `queue_status: Queueing` or `Generating`. Poll externally for long waits. Do not introduce a runtime DB, queue worker, or hidden state file.

## Common Interpretations

- not logged in: host must complete manual login first.
- not maestro: account lacks CLI generation permission.
- output around 4-5 seconds: likely omitted `--duration`; default is 5 and observed fast output may be ~4.06s.
- queueing/generating: preserve submit id and wait/poll.
- generation failed: keep error, then decide whether to revise prompt or retry.

## Security

Never commit tokens, credentials, OAuth links, device codes, QR contents, credential files, or raw account identifiers. Use `[REDACTED]` when documenting sensitive material.
