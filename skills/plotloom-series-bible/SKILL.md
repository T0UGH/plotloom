---
name: plotloom-series-bible
description: >-
  Creates or updates a Plotloom short-drama series bible and core character context.
  Use when starting a new short drama, continuing from an idea, creating a series repo,
  or when `series.md` / `characters.md` are missing.
---

# Plotloom Series Bible

## When to Use
Use when the user has a short-drama idea but the current repo does not yet have stable series context, or when `series.md` / `characters.md` are missing or too thin.

## Inputs
- User idea, title, genre, tone, desired episode count, and any constraints.
- Current working directory and parent directories.
- Optional `~/plotloom.toml` home-level repo registry.
- Existing `series.md` and `characters.md` if present.

## Outputs
- `series.md`
- `characters.md`
- Baseline series repo directories.
- One `~/plotloom.toml` registry entry when creating a new repo.

## Workflow
1. Detect whether the current directory or a parent is already a Plotloom series repo by looking for `plotloom.toml`, `series.md`, `characters.md`, or `episodes/`.
2. If no repo is active, inspect `~/plotloom.toml` and decide whether to continue an existing series or create a new repo. Ask only if multiple plausible repos exist.
3. When creating a new repo, use the series repo template and write only repo scaffolding plus `series.md` and `characters.md`.
4. Develop enough long-form context so episode 1 is not a one-off skit: premise, audience/tone, recurring conflict engine, core cast, season arc, and the first three episode intentions.
5. Stop before image generation, video generation, candidate selection, or stitching.

## Series Bible Writing Rules
- Keep the series engine reusable across episodes.
- Make conflicts repeatable, not exhausted in episode 1.
- Define character desire, contradiction, visual identity, and dialogue style.
- Record open questions rather than inventing user-sensitive facts.
- Prefer concise, production-usable Markdown over novelistic prose.

## Stop Conditions
Stop when `series.md` and `characters.md` are sufficient for `plotloom-episode-card` or `plotloom-shot-prompts`. Do not generate images, videos, scripts, storyboards, runtime state, or hidden manifests.

## Next Skill Handoff
- If episode intent is unclear, hand off to `plotloom-episode-card`.
- If episode intent is clear enough, hand off directly to `plotloom-shot-prompts`.

## Failure Modes
- Missing repo and ambiguous registry: ask the user which series to continue.
- Existing repo has conflicting title/slug: report the conflict and stop.
- User asks for video generation first: create or verify series context before generation.
