# Codex Imagegen Adapter Notes

## Purpose
Thin host adapter notes for generating Plotloom images with Codex imagegen. Do not duplicate Plotloom business logic here.

## Preflight Expectations
- Host can call the configured image generation tool.
- Target series repo has `series.md` and `characters.md`.
- Output directories exist or can be created.

## Input Files
- `characters.md`
- `series.md`
- Optional visual direction from episode notes.

## Output Paths
Character grid output path:

```text
assets/cast/<character-slug>/character-grid.png
```

Cover/candidate output path examples:

```text
episodes/ep001/images/covers/candidates/v001.png
```

## Dry-Run Behavior
In dry-run, write the intended prompt and output path without calling image generation.

## Failure Modes
- Missing character description.
- Missing output path.
- Image generation unavailable.
- Generated image fails visual review and should go through asset selection.
