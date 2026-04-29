# Codex Imagegen Adapter Notes

## Purpose

Thin host adapter notes for generating Plotloom images with the private `codex-imagegen2-api` skill. Do not duplicate Plotloom business logic here.

## Concrete Adapter

Source skill repo:

```text
T0UGH/agent-skills
skill path: codex-imagegen2-api/
local path on this machine: /Users/wangguiping/workspace/agent-skills/codex-imagegen2-api
installed for Nova: /Users/wangguiping/.hermes/profiles/nova/skills/personal/codex-imagegen2-api
```

The helper script is:

```text
codex-imagegen2-api/scripts/codex_imagegen2.py
```

It wraps `codex exec --enable image_generation` and returns JSON with:

```text
ok
image_path
image_url
source_image_path
notes
input_images
codex_exit_code
```

It uses the logged-in Codex runtime and does not require `OPENAI_API_KEY`.

## Preflight Expectations

- `codex` CLI is available on PATH.
- Codex runtime is logged in and can use `image_generation`.
- `codex-imagegen2-api` skill is installed or accessible from `agent-skills`.
- Target series repo has `series.md` and `characters.md`.
- Output directories exist or can be created.

Preflight command:

```bash
which codex && codex --version
python3 /Users/wangguiping/.hermes/profiles/nova/skills/personal/codex-imagegen2-api/scripts/codex_imagegen2.py --help
```

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
python3 /Users/wangguiping/.hermes/profiles/nova/skills/personal/codex-imagegen2-api/scripts/codex_imagegen2.py \
  --prompt-file /path/to/character-grid-prompt.txt \
  --output-dir /path/to/series-repo/assets/cast/<character-slug> \
  --filename character-grid
```

For reference/edit images:

```bash
python3 /Users/wangguiping/.hermes/profiles/nova/skills/personal/codex-imagegen2-api/scripts/codex_imagegen2.py \
  --prompt-file /path/to/character-grid-prompt.txt \
  --image /path/to/reference.png \
  --output-dir /path/to/series-repo/assets/cast/<character-slug> \
  --filename character-grid
```

## Prompt Guidance

- Say whether attached images are style references, edit targets, or composition references.
- Say `no text` unless image text is required.
- Request exactly one image per helper invocation.
- Always pass `--output-dir`; do not rely on `$CODEX_HOME/generated_images` as the durable Plotloom path.
- Generated images still go through `plotloom-asset-selection`; do not silently treat them as accepted if quality is ambiguous.

## Dry-Run Behavior

In dry-run, write the intended prompt, output path, and exact helper command without calling image generation.

## Failure Modes

- `codex` CLI missing.
- Codex not logged in or image generation unavailable.
- Missing character description.
- Missing output path.
- Helper returns `ok: false` or nonzero exit.
- Generated image fails visual review and should go through asset selection.
