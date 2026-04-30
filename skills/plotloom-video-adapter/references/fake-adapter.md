# Mock Video Adapter Reference

## Purpose
The mock adapter runs Plotloom contract tests without spending quota or waiting for a real model. It creates a deterministic mp4 candidate through the normal `plotloom video submit` path.

## Command Shape
```bash
plotloom --repo . video submit \
  --episode ep001 \
  --clip clip-01 \
  --adapter mock
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
Use `mock` by default in tests, CI-like checks, and examples. Use real Dreamina or VolcEngine only when the user explicitly asks for real generation and preflight passes.
