---
name: plotloom-asset-selection
description: >-
  Reviews Plotloom image/video candidates and instructs deterministic selection copy.
  Use when candidates exist and a human/agent must accept, reroll, or revise prompts.
---

# Plotloom Asset Selection

## When to Use
Use when image or video candidates exist under `candidates/` and the next step is accept, reroll, or prompt revision.

## Inputs
- Prompt intent and rerun notes.
- Candidate image/video path, one candidate at a time for video.
- Selection rubric.

## Outputs
- Human-readable review note or recommendation.
- If accepted, deterministic helper copies candidate to `selected.*`.

## Workflow
1. Evaluate candidates against intent, character consistency, visual continuity, short-drama clarity, hook strength, and model artifacts.
2. Ask the user for accept / reroll / revise prompt when quality is ambiguous.
3. If accepted, run or instruct `scripts/select_candidate.py` to copy the candidate to `selected.*`.
4. Preserve `candidates/vNNN.*`.
5. If replacing a selected file, back up old selected as `selected-prev-YYYYMMDD-HHMMSS.*`.
6. For video, process one candidate at a time.

## Stop Conditions
Stop after selected copy or rerun recommendation. Do not delete candidates or silently choose ambiguous video.

## Next Skill Handoff
After all required clips have `selected.mp4`, hand off to `plotloom-stitch-deliver`.

## Failure Modes
- Candidate missing: report missing path.
- Ambiguous quality: ask user rather than choosing silently.
- Prompt mismatch: recommend revise prompt, not just reroll.
