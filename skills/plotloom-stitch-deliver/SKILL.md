---
name: plotloom-stitch-deliver
description: >-
  Stitches selected Plotloom clips into `final.mp4` and prepares delivery. Use when the user asks to stitch clips,
  assemble an episode, concat selected videos, make final.mp4, probe media, or deliver a verified Plotloom episode to
  Feishu/Lark after `episodes/epXXX/videos/clip-*/selected.mp4` files exist.
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
- Optional delivery note and Feishu/Lark delivery message or uploaded file.

## Read These Resources When...
- Read `references/ffmpeg.md` before probing or stitching.
- Use `templates/delivery-note.md` after final verification or delivery.
- Use `plotloom --repo <repo> media probe <path>` and `plotloom --repo <repo> stitch --episode <episode>` for deterministic work.

## Workflow
1. Find selected clips in episode clip order.
2. Stop if any required selected clip is missing.
3. Use `plotloom media probe` to inspect each input.
4. Use `plotloom stitch` to stitch selected clips; use `--normalize` only when the target media behavior is understood.
5. Save `episodes/epXXX/videos/final.mp4`.
6. Verify final file exists, is probeable, has nonzero duration, and matches expected clip count/order.
7. Deliver via nova-lark / lark-cli when requested.
8. Keep Feishu as delivery, not state center.

## Final Verification Checklist
- `final.mp4` exists.
- `ffprobe` returns success.
- duration is nonzero.
- source clip order is correct.
- no prompts/candidates/selection notes were mutated during stitch.

## Stop Conditions
Stop after final probe and optional delivery. Do not mutate prompts, candidates, or selection notes.

## Failure Modes
- Missing selected clip: report exact missing path.
- ffprobe failure: report incompatible/unreadable media.
- ffmpeg failure: report stderr/command failure clearly; do not hide errors.
- Delivery failure: final file remains canonical in repo; Feishu is not state center.
