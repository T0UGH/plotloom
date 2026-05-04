# Reference Map and Face Policy Runbook

This runbook covers the current low-risk reference workflow. It records user intent for later review, but it does not send local reference images to video providers yet.

## Current Boundary

Implemented:

- Plan ordered clip references with `plotloom video plan-references`.
- Write `episodes/<episode>/videos/<clip>/reference-map.toml`.
- Validate character face strategies with `plotloom validate --face-policy`.
- Record reference intent in task receipts with `plotloom video submit --reference-map`.
- Cross-check character references against face policies during `video submit --reference-map`.
- Run optional prompt lint with `plotloom prompt check --lint` or `--reference-map`.
- Record adapter native request summaries in task receipts without sending extra provider data.
- Classify submit / poll / download failures in receipts.

Not implemented yet:

- Uploading local reference files for provider use.
- Translating `reference-map.toml` into Seedance / Dreamina native payloads.
- Using VolcEngine cloud face assets in submit requests.
- Automatic face strategy selection.
- Paid Seedance / Dreamina E2E in automated tests.

## Reference Map

Use `plan-references` to define the ordered reference intent for one clip.

```bash
plotloom video plan-references \
  --repo /path/to/series \
  --episode ep001 \
  --clip clip-01 \
  --first-frame episodes/ep001/images/references/clip-01-first.jpg \
  --reference character:ethan=assets/cast/ethan/safe-face.png \
  --reference scene:gala=assets/scenes/gala/selected.png \
  --last-frame episodes/ep001/images/references/clip-01-last.jpg
```

By default this only prints the plan. Add `--write` to create:

```text
episodes/ep001/videos/clip-01/reference-map.toml
```

```bash
plotloom video plan-references \
  --repo /path/to/series \
  --episode ep001 \
  --clip clip-01 \
  --reference character:ethan=assets/cast/ethan/safe-face.png \
  --write
```

The generated TOML looks like:

```toml
[[references]]
slot = 1
kind = "character"
path = "assets/cast/ethan/safe-face.png"
source = "asset"
character = "ethan"
```

Supported `kind` values:

```text
first_frame
last_frame
character
scene
style
generic
```

## Face Policy

Each cast character can declare how face references should be handled:

```text
assets/cast/<character>/face-policy.toml
```

Supported strategies:

```text
safe-face-reference
text-only
cloud-face-asset
```

`safe-face-reference` uses a local provider-safe face image, such as a sketch, masked face, or low-photoreal character grid.

```toml
[face]
strategy = "safe-face-reference"
path = "assets/cast/ethan/safe-face.png"
```

`text-only` avoids face image references and relies on description.

```toml
[face]
strategy = "text-only"
description = "Young East Asian man, sharp brows, tired eyes, controlled expression."
```

`cloud-face-asset` records a provider cloud face asset plus a local body / wardrobe reference.

```toml
[face]
strategy = "cloud-face-asset"
provider = "volcengine-seedance"
cloud_asset = "asset://asset-20260224225526-g6kpx"
body_reference = "assets/cast/ethan/body-wardrobe.png"
```

VolcEngine documents this as an `image_url.url` URI shaped like `asset://<asset_id>` with `role = "reference_image"`. Plotloom records the URI now, but still does not submit it to providers.

Validate policies explicitly:

```bash
plotloom validate --repo /path/to/series --face-policy
```

Default `plotloom validate` does not require face policies.

## Submit With Reference Intent

After writing a reference map, pass it to submit:

```bash
plotloom video submit \
  --repo /path/to/series \
  --episode ep001 \
  --clip clip-01 \
  --adapter mock \
  --reference-map episodes/ep001/videos/clip-01/reference-map.toml
```

The task receipt records:

```toml
reference_map_path = "episodes/ep001/videos/clip-01/reference-map.toml"

[[reference_intent]]
slot = 1
kind = "character"
path = "assets/cast/ethan/safe-face.png"
source = "asset"
character = "ethan"
```

Provider payloads are unchanged. This is intentional: the receipt records what the user or agent intended, while provider integration remains a later explicit slice.

When `reference_intent` includes a character reference, submit validates it against the character face policy:

- `text-only` rejects character references.
- `safe-face-reference` requires the reference path to match `[face].path`.
- `cloud-face-asset` requires the reference path to match `[face].body_reference`; the cloud face is recorded in `cloud_asset`.

Receipts also include a `provider_request` summary. This is a local, redacted summary for debugging; it is not proof that references were sent to the provider.

## Prompt Lint

Prompt lint is opt-in and does not change compile output unless requested.

```bash
plotloom prompt check \
  --repo /path/to/series \
  --episode ep001 \
  --clip clip-01 \
  --reference-map episodes/ep001/videos/clip-01/reference-map.toml
```

It checks:

- prompt references to `Image 1`, `Image 2`, etc. against reference map length;
- CJK text that may cause unwanted subtitles or on-screen text;
- shot-list style prompts that should be rewritten as continuous cinematic tasks.

Use `--lint` without `--reference-map` to run text-only lint checks.

## Failure Classification

Task receipts can now record:

```toml
error_code = "SUBMIT_PROVIDER_UNREACHABLE"
failure_category = "provider_unreachable"
failure_stage = "submit"
retryable = true
```

Classification is local metadata. Plotloom still does not automatically retry provider jobs.

## Common Checks

- If `plan-references` fails with `reference path not found`, create/import the asset first.
- If `validate --face-policy` fails on `safe-face-reference`, check that `[face].path` points to an existing repo file.
- If `validate --face-policy` fails on `cloud-face-asset`, check `provider`, `cloud_asset`, and `body_reference`.
- If a receipt lacks `reference_intent`, submit was run without `--reference-map`.
- If `video submit --reference-map` fails on face policy validation, make the character reference path match the policy: `face.path` for `safe-face-reference`, `body_reference` for `cloud-face-asset`, or remove the character reference for `text-only`.
