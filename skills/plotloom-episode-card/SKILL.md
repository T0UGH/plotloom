---
name: plotloom-episode-card
description: >-
  Creates a lean Plotloom episode intent card before video prompt generation. Use when the user says plan ep001,
  next episode, make a 45s/60s short-drama episode, define hook/reversal/cliffhanger, or when `episodes/epXXX/episode-card.md`
  is missing or thin before writing Seedance/Dreamina/video prompts.
---

# Plotloom Episode Card

## When to Use
Use when `series.md` and `characters.md` exist but the next episode needs a compact intent anchor before writing video prompts. This skill is for intent, not full script/storyboard generation.

## Inputs
- `series.md`
- `characters.md`
- Optional existing `episodes/epXXX/episode-card.md`
- User direction for episode number, runtime, hook, conflict, reversal, or ending handoff.

## Outputs
- `episodes/epXXX/episode-card.md`

## Read These Resources When...
- Read `references/episode-intent.md` when the hook, visible conflict, reversal, or ending handoff is weak.
- Use `templates/episode-card.md` for output shape.

## Workflow
1. Read `series.md` and `characters.md`.
2. If series/character context is missing, hand off to `plotloom-series-brainstorming` rather than inventing it.
3. Create or update only `episodes/epXXX/episode-card.md` when story intent needs anchoring.
4. Keep the card lean: runtime target, opening hook, emotional hook, main conflict, escalation, reversal, ending hook, required characters/assets, locations, and continuity constraints.
5. Hand off to `plotloom-shot-prompts`.

## Episode Card Rules
- The first 1-3 seconds need a visible hook, not pure exposition.
- The main conflict must be filmable as action, posture, expression, prop, or dialogue window.
- Include a reversal/reveal and an ending handoff for the next clip or episode.
- Do not create mandatory `script.md`, `storyboard.md`, `review.md`, or `director-brief.md`.
- If a full script/storyboard is requested, mark it outside MVP and ask for explicit direction before expanding scope.

## Stop Conditions
Stop after the episode card is clear. Do not call image/video tools, write video prompts, or select media.

## Next Skill Handoff
Use `plotloom-shot-prompts` to turn this card into continuous video prompt tasks.

## Failure Modes
- Missing `series.md` or `characters.md`: hand off to `plotloom-series-brainstorming` first.
- Episode already has a good card: summarize it and proceed to prompt generation.
- User asks for full script/storyboard: confirm scope; do not create mandatory heavyweight artifacts by default.
