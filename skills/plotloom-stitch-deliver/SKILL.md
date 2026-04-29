---
name: plotloom-stitch-deliver
description: >-
  Stitches selected Plotloom video clips into final.mp4 and prepares delivery.
  Use when required clip folders have selected.mp4 files.
---

# Plotloom Stitch and Deliver

## When to Use
Use after all required `episodes/epXXX/videos/clip-*/selected.mp4` files exist.

## Inputs
- `selected.mp4` clips under `episodes/epXXX/videos/clip-*/`
- Target episode id.
- Optional delivery request via nova-lark / lark-cli.

## Outputs
- `episodes/epXXX/videos/final.mp4`
- Optional Feishu/Lark delivery message or uploaded file.

## Workflow
1. Find selected clips in episode clip order.
2. Stop if any required selected clip is missing.
3. Use ffprobe helper to inspect compatibility.
4. Use ffmpeg helper to stitch or normalize + stitch.
5. Save `episodes/epXXX/videos/final.mp4`.
6. Verify the final file exists and is playable/probeable.
7. Deliver via nova-lark / lark-cli when requested.
8. Keep Feishu as delivery, not state center.

## Stop Conditions
Stop after final probe and optional delivery. Do not mutate prompts, candidates, or selection notes.

## Failure Modes
- Missing selected clip: report exact missing path.
- ffprobe failure: report incompatible/unreadable media.
- ffmpeg failure: report stderr/command failure clearly; do not hide errors.
- Delivery failure: final file remains canonical in repo; Feishu is not state center.
