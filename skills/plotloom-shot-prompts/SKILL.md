---
name: plotloom-shot-prompts
description: >-
  Writes continuous Plotloom video prompt tasks from series and episode context.
  Use when an episode needs clip prompts before model submission.
---

# Plotloom Shot Prompts

## When to Use
Use after `series.md` and `characters.md` exist, with optional `episodes/epXXX/episode-card.md`, to create video prompts for clip generation.

## Inputs
- `series.md`
- `characters.md`
- Optional `episodes/epXXX/episode-card.md`
- Existing character grids such as `assets/cast/<slug>/character-grid.png`

## Outputs
- `episodes/epXXX/video-prompts.md`
- `episodes/epXXX/video-prompts-en.md` only when the adapter/model needs English.

## Workflow
1. Read series, characters, optional episode card, and available visual references.
2. Write continuous narrative prompt tasks, not mechanical shot lists.
3. For Seedance / Dreamina-style models, describe one coherent cinematic moment per clip.
4. Use the default video task shape: `clip-01`, duration hint `15-20s` when supported, references and purpose, cinematic timeline beats, continuity rules, camera motion, optional dialogue windows, and ending frame / handoff point.
5. Stop before calling a model.

## Prompt Rules
- Preserve character-grid identity: face, age, outfit, body language, and style.
- Avoid conflicting camera instructions.
- Include entrances/exits/occlusion when continuity matters.
- Prefer rerun notes over silently changing intent after failed candidates.

## Stop Conditions
Stop when video prompts are ready. Do not submit jobs, poll queues, copy selected files, or stitch videos.

## Next Skill Handoff
Use `plotloom-video-adapter` for fake or real model submission.

## Failure Modes
- Missing series context: hand off to `plotloom-series-bible`.
- Missing episode intent: create an episode card or ask for direction.
- Model requires English: produce `video-prompts-en.md` from the same intent.
