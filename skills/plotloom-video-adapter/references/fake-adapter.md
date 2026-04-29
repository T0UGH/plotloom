# Fake Video Adapter Reference

## Purpose
The fake adapter runs Plotloom contract tests without spending quota or waiting for a real model. It creates or copies a deterministic mp4 to the requested candidate path.

## Command Shape
```bash
python scripts/adapters/fake_video.py \
  --prompt-file episodes/ep001/video-prompts.md \
  --output episodes/ep001/videos/clip-01/candidates/v001.mp4
```

## What It Proves
- Prompt file path exists.
- Candidate output path can be created.
- Selection and stitching helpers can consume the candidate.
- ffprobe/ffmpeg are available.

## What It Does Not Prove
- Prompt quality.
- Character continuity.
- Model/provider availability.
- Commercial quality.

## When to Use
Use fake by default in MVP tests, CI-like checks, and examples. Use real Dreamina only when the user explicitly asks for real generation and preflight passes.
