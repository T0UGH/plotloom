---
name: plotloom-asset-selection
description: >-
  Reviews Plotloom image/video candidates and decides accept, reroll, revise_prompt, or ask_user before copying to `selected.*`.
  Use when the user asks to review a candidate, choose the best version, accept/reroll, check character consistency, evaluate
  model artifacts, or copy a candidate to `selected.mp4` / `selected.png` with backup semantics.
---

# Plotloom Asset Selection

## When to Use
Use when image or video candidates exist under `candidates/` and the next step is accept, reroll, prompt revision, or deterministic selected-copy.

## Inputs
- Prompt intent and rerun notes.
- Candidate image/video path; process video one candidate at a time.
- Selection rubric and optional review note template.

## Outputs
- Candidate review note or recommendation.
- If accepted, deterministic helper copies candidate to `selected.*`.

## Read These Resources When...
- Read `references/selection-rubric.md` before evaluating candidates.
- Use `templates/review-note.md` for review output.
- Use `plotloom --repo <repo> select <candidate>` only after accept decision.

## Workflow
1. Evaluate candidate against intent, character consistency, visual continuity, short-drama clarity, hook strength, ending handoff, and artifacts.
2. Choose one decision: `accept`, `reroll`, `revise_prompt`, or `ask_user`.
3. Ask the user when quality is ambiguous or trade-offs are subjective.
4. If accepted, run or instruct `plotloom --repo <repo> select <candidate>` to copy the candidate to `selected.*`.
5. Preserve `candidates/vNNN.*`.
6. If replacing a selected file, back up old selected as `selected-prev-YYYYMMDD-HHMMSS-ffffff.*`.
7. For video, process one candidate at a time.

## Decision Rules
- **accept:** intent matches, identity stable, artifacts minor, ending frame works.
- **reroll:** prompt is right, but sample has random artifacts or weak rendering.
- **revise_prompt:** candidate repeatedly misses action, character, reference use, camera, or ending frame.
- **ask_user:** trade-off is taste-based or multiple versions are plausible.

## Stop Conditions
Stop after selected copy or rerun recommendation. Do not delete candidates, generate new media, or silently choose ambiguous video.

## Next Skill Handoff
After all required clips have `selected.mp4`, hand off to `plotloom-stitch-deliver`.

## Failure Modes
- Candidate missing: report missing path.
- Ambiguous quality: ask user rather than choosing silently.
- Prompt mismatch: recommend revise prompt, not just reroll.
- Existing selected: use backup semantics before replacement.
