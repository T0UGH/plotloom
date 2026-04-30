---
name: plotloom-shot-prompts
description: >-
  Writes Plotloom continuous video prompt tasks for Seedance, Dreamina/即梦, and similar video models. Use when the user asks
  for video prompts, Seedance prompts, 即梦视频提示词, turn an episode card into clips, preserve character-grid continuity,
  or create `episodes/epXXX/video-prompts.md` / `video-prompts-en.md` before adapter submission.
---

# Plotloom Shot Prompts

## When to Use
Use after `series.md` and `characters.md` exist, with optional `episodes/epXXX/episode-card.md`, to create continuous video prompts for clip generation.

## Inputs
- `series.md`
- `characters.md`
- Optional `episodes/epXXX/episode-card.md`
- Existing character grids such as `assets/cast/<slug>/character-grid.png`
- Optional previous clip last frame or previous video reference.

## Outputs
- `episodes/epXXX/video-prompts.md`
- `episodes/epXXX/video-prompts-en.md` only when the adapter/model needs English.

## Read These Resources When...
- Read `references/visual-continuity.md` when character grids, reference sheets, previous clips, or inter-clip handoffs matter.
- Read `references/seedance-dreamina-prompt-style.md` when targeting Seedance 2.0 / Dreamina / 即梦 style video models.
- Use `templates/video-prompts.md` and `templates/video-prompts-en.md` for output shape.

## Workflow
1. Read series, characters, optional episode card, available visual references, and prior clip handoff notes.
2. Write continuous narrative prompt tasks, not mechanical shot lists.
3. For Seedance / Dreamina-style models, one clip prompt equals one coherent 8-20s cinematic moment with a single primary timeline.
4. Use the default task shape: `clip-01`, source beat, duration hint, references and purpose, timeline beats, continuity rules, camera motion, dialogue/audio window, negative constraints, ending frame / handoff point, and rerun notes.
5. If the model/adapter needs English, create `video-prompts-en.md` as an adapter copy that preserves the source intent and does not add new plot.
6. Stop before calling a model.

## Prompt Rules
- Seedance prompt ≠ shot list. It is a director brief translated into a continuous narrative timeline.
- Use visible action over abstract emotion.
- Mention `@图片N`, `@视频N`, `@音频N` only in adapter-targeted copies where that platform syntax is needed.
- Preserve character-grid identity: face, age, outfit, body language, style, and signature props.
- Include entrance/exit/occlusion when continuity could break.
- Avoid conflicting camera instructions. Use one dominant camera idea per clip.
- Dialogue must be serial and sparse; avoid two people speaking over each other in a short clip.
- Reserve head/tail safety: do not place the critical reveal only in the first or last 0.5s.
- Prefer rerun notes over silently changing intent after failed candidates.

## Stop Conditions
Stop when video prompts are ready. Do not submit jobs, poll queues, copy selected files, or stitch videos.

## Next Skill Handoff
Use `plotloom-video-adapter` for fake or real model submission.

## Failure Modes
- Missing series context: hand off to `plotloom-series-brainstorming`.
- Missing episode intent: create an episode card or ask for direction.
- Model requires English: produce `video-prompts-en.md` from the same intent.
- User asks for per-shot model calls: explain that Plotloom uses continuous prompt tasks, not one generation per micro-shot.
