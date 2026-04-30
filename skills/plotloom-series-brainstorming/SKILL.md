---
name: plotloom-series-brainstorming
description: >-
  Use when the user starts or revises a Plotloom/短剧 series idea, needs `series.md` or `characters.md`,
  mentions character bible, cast design, repeatable story engine, character-grid, or wants stable world/tone/visual
  anchors before episode, prompt, video, selection, or stitching work.
---

# Plotloom Series Brainstorming

## When to Use
Use when the user has a short-drama idea but the current repo does not yet have stable series context, or when `series.md` / `characters.md` are missing, thin, or visually under-specified. Also use before image/video work when character identity, conflict engine, or home repo registry status is unclear.

This skill is brainstorming-driven: align the series direction with the user before writing durable series files, unless the user explicitly asks for a fast Agent-led draft.

## Inputs
- User idea, title, genre, tone, desired episode count, and constraints.
- Current working directory and parent directories.
- Optional `~/plotloom.toml` home-level repo registry.
- Existing `series.md`, `characters.md`, character-grid images, or prior episode notes.

## Outputs
- 2-3 candidate series directions when the core direction is not already locked.
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
3. When creating a new repo, use `plotloom init <slug> --title <title>` for deterministic scaffolding only. Do not put story logic in the CLI.
4. If the premise, tone, protagonist identity, or repeatable conflict engine is not locked, present 2-3 candidate directions before writing files. Each option should include: one-sentence promise, repeatable engine, core cast shape, visual tone, and trade-off.
5. Recommend one option and ask exactly one alignment question. Prefer a multiple-choice question such as "选 A/B/C，还是混合 A+C?"
6. Ask at most one more blocking follow-up if a durable file would otherwise encode a major unknown. Do not run a long interview.
7. If the user explicitly asks for a fast Agent-led draft, pick the strongest direction, state the assumption, and write the files.
8. Develop enough long-form context so episode 1 is not a one-off skit: premise, audience/tone, recurring conflict engine, core cast, season arc, and first-three-episode runway.
9. For each core character, define stable visual anchors and the required `assets/cast/<slug>/character-grid.png` brief: front/side/back, expression grid, wardrobe lock, props, palette, and do-not-change invariants.
10. Stop before image generation, video generation, candidate selection, or stitching.

## Brainstorming Rules
- Offer concrete alternatives, not vague questions.
- One message should not ask the user to solve more than one creative decision.
- Lead with the recommended option and explain the trade-off briefly.
- If the user chooses a direction, proceed to write or update `series.md` and `characters.md` without restarting the brainstorm.
- Preserve existing user-approved facts when revising an existing repo.

## Series Brainstorming Writing Rules
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
