# Codex Image Generation Adapter Notes

## Purpose

Thin host adapter notes for generating Plotloom images through the local Codex install and built-in image generation capability. Do not duplicate Plotloom business logic here.

## Concrete Adapter

Recommended adapter name:

```text
codex-app-server
```

The adapter depends on:

```text
global codex binary
local Codex authentication/config
Codex built-in image_generation capability
```

The inspected `T0UGH/agent-skills/codex-imagegen2-api` skill proves a working local API shape for this adapter. It runs:

```bash
codex exec \
  --skip-git-repo-check \
  --sandbox read-only \
  --enable image_generation \
  --output-schema schema.json \
  --output-last-message result.json \
  --image <optional-input> \
  -
```

The helper asks Codex to generate exactly one raster image, return JSON, validates the generated file, optionally copies it into `--output-dir`, and returns a stable JSON result. Plotloom should own or port this implementation pattern instead of depending on a machine-specific installed helper path.

Expected adapter result fields:

```text
ok
image_path
image_url
source_image_path
notes
input_images
codex_exit_code
```

It uses the logged-in local Codex runtime and should not require provider API keys inside Plotloom config.

## Preflight Expectations

- `codex` CLI is available on PATH.
- Codex runtime is logged in.
- `codex exec --enable image_generation` works.
- Target series repo has `series.md` and `characters.md`.
- Output directories exist or can be created.

Preflight command:

```bash
which codex && codex --version
plotloom config doctor
```

The design constraint is that Plotloom depends on the user's local Codex installation/auth state, not on a machine-specific private script path. A direct app-server API can replace the `codex exec` implementation later if it becomes a better supported interface.

## Input Files

- `characters.md`
- `series.md`
- Optional visual direction from episode notes.
- Optional reference/edit images via repeated `--image PATH`.

## Output Paths

Character grid output path:

```text
assets/cast/<character-slug>/character-grid.png
```

Cover/candidate output path examples:

```text
episodes/ep001/images/covers/candidates/v001.png
```

## Character Grid Command Shape

```bash
plotloom image generate \
  --adapter codex-app-server \
  --kind cast \
  --character <character-slug> \
  --prompt-file /path/to/character-grid-prompt.txt \
  --repo /path/to/series-repo
```

For reference/edit images:

```bash
plotloom image generate \
  --adapter codex-app-server \
  --kind cast \
  --character <character-slug> \
  --prompt-file /path/to/character-grid-prompt.txt \
  --image /path/to/reference.png \
  --repo /path/to/series-repo
```

## Prompt Guidance

- Say whether attached images are style references, edit targets, or composition references.
- Say `no text` unless image text is required.
- Request exactly one image per adapter invocation.
- Always copy/write the final image into the series repo; do not rely on `$CODEX_HOME/generated_images` as the durable Plotloom path.
- Generated images still go through `plotloom-asset-selection`; do not silently treat them as accepted if quality is ambiguous.

## Dry-Run Behavior

In dry-run, write the intended prompt, output path, and adapter request without calling image generation.

## Failure Modes

- `codex` CLI missing.
- Codex not logged in or image generation unavailable.
- `codex exec --enable image_generation` unavailable or incompatible.
- Missing character description.
- Missing output path.
- Adapter returns `ok: false` or nonzero exit.
- Generated image fails visual review and should go through asset selection.

## Reference Skill

Reference implementation:

```text
https://github.com/T0UGH/agent-skills/tree/main/codex-imagegen2-api
```

Do not call it through a hardcoded local path. Use it as implementation guidance for Plotloom's own adapter.
