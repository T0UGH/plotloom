---
name: plotloom-episode-card
description: >-
  Creates a lean Plotloom episode intent card from an existing series bible.
  Use when episode intent needs anchoring before video prompt generation.
---

# Plotloom Episode Card

## When to Use
Use when `series.md` and `characters.md` exist but the next episode needs a compact intent anchor before writing video prompts.

## Inputs
- `series.md`
- `characters.md`
- Optional existing `episodes/epXXX/episode-card.md`
- User direction for episode number, hook, or reversal.

## Outputs
- `episodes/epXXX/episode-card.md`

## Workflow
1. Read `series.md` and `characters.md`.
2. Create or update only `episodes/epXXX/episode-card.md` when story intent needs anchoring.
3. Keep the card lean: logline, emotional hook, main conflict, reversal, ending hook, required characters/assets.
4. Hand off to `plotloom-shot-prompts`.

## Episode Card Rules
- Keep it short enough to guide video prompt writing.
- Do not create mandatory `script.md`, `storyboard.md`, `review.md`, or `director-brief.md`.
- If a full script/storyboard is requested, treat it as outside MVP and ask for explicit direction.

## Stop Conditions
Stop after the episode card is clear. Do not call image/video tools or select media.

## Next Skill Handoff
Use `plotloom-shot-prompts` to turn this card into continuous video prompt tasks.

## Failure Modes
- Missing `series.md` or `characters.md`: hand off to `plotloom-series-bible` first.
- Episode already has a good card: summarize it and proceed to prompt generation.
