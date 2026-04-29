---
name: plotloom-series-bible
description: >-
  Creates or updates the Plotloom short-drama series bible, character context, and character asset briefs.
  Use whenever the user starts a new Plotloom/短剧 idea, asks to create or continue a series repo, needs `series.md`
  or `characters.md`, mentions a repeatable story engine, character bible, cast design, character-grid, or wants stable
  world/tone/visual anchors before episode, prompt, video, selection, or stitching work.
---

# Plotloom Series Bible

## When to Use
Use when the user has a short-drama idea but the current repo does not yet have stable series context, or when `series.md` / `characters.md` are missing, thin, or visually under-specified. Also use before image/video work when character identity, conflict engine, or home repo registry status is unclear.

## Inputs
- User idea, title, genre, tone, desired episode count, and constraints.
- Current working directory and parent directories.
- Optional `~/plotloom.toml` home-level repo registry.
- Existing `series.md`, `characters.md`, character-grid images, or prior episode notes.

## Outputs
- `series.md`
- `characters.md`
- Baseline series repo directories.
- One `~/plotloom.toml` registry entry when creating a new repo.
- Character asset briefs sufficient for later GPT Image 2 / Codex imagegen `character-grid.png` generation.

## Read These Resources When...
- Read `references/short-drama-series-engine.md` when the premise feels like a one-off skit or lacks a repeatable conflict engine.
- Read `references/repo-contract.md` before creating repo scaffolding or touching `~/plotloom.toml`.
- Read `references/character-asset-briefs.md` when character design, expression grids, reference sheets, or visual continuity are needed.
- Use `templates/series.md` and `templates/characters.md` as output shapes.

## Workflow
1. Detect whether the current directory or a parent is already a Plotloom series repo by looking for `plotloom.toml`, `series.md`, `characters.md`, or `episodes/`.
2. If no repo is active, inspect `~/plotloom.toml` and decide whether to continue an existing series or create a new repo. Ask only if multiple plausible repos exist.
3. When creating a new repo, use the series repo template or repo-level `scripts/init_series.py` for deterministic scaffolding only. Do not put story logic in scripts.
4. Develop enough long-form context so episode 1 is not a one-off skit: premise, audience/tone, recurring conflict engine, core cast, season arc, and first-three-episode runway.
5. For each core character, define stable visual anchors and the required `assets/cast/<slug>/character-grid.png` brief: front/side/back, expression grid, wardrobe lock, props, palette, and do-not-change invariants.
6. Stop before image generation, video generation, candidate selection, or stitching.

## Series Bible Writing Rules
- Make the conflict repeatable across episodes and not exhausted in ep001.
- Define character desire, wound/contradiction, leverage/secret, role in the conflict engine, visual identity, and dialogue style.
- Separate stable visual anchors from mutable episode styling.
- Record open questions rather than inventing user-sensitive facts.
- Prefer concise, production-usable Markdown over novelistic prose.

## Quality Bar
- The premise can be pitched in one sentence.
- The series engine can generate at least 10 episode conflicts.
- Each core character has desire + contradiction + visual anchor.
- First three episodes form a runway: hook → escalation → complication.
- Character asset briefs can drive a reference sheet / expression grid without new guessing.

## Stop Conditions
Stop when `series.md` and `characters.md` are sufficient for `plotloom-episode-card` or `plotloom-shot-prompts`. Do not generate images, videos, scripts, storyboards, runtime state, or hidden manifests.

## Next Skill Handoff
- If episode has no hook/conflict/reversal, hand off to `plotloom-episode-card`.
- If episode intent is clear enough, hand off directly to `plotloom-shot-prompts`.
- If character images already exist, mention them as continuity anchors for later skills.

## Failure Modes
- Missing repo and ambiguous registry: ask the user which series to continue.
- Existing repo has conflicting title/slug: report the conflict and stop.
- User asks for video generation first: create or verify series context before generation.
- Character visual identity is underspecified: produce a character asset brief, not a generated image.
