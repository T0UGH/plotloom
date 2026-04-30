# Character Asset Briefs for GPT Image 2 / Codex Imagegen

## Sources Borrowed
Patterns are adapted from GPT Image 2 prompt libraries such as `awesome-gpt-image-2-prompts`, `awesome-gpt-image-2`, `Awesome-GPT-Image-2-API-Prompts`, `awesome-gpt-image`, and `gpt_image_2_skill`.

## Reference Sheet Pattern
Use this when a character needs a stable `character-grid.png`:

```text
Create an official character reference sheet for [character]. Include front, side, and back full-body views; facial expression variations; clothing/equipment callouts; color palette; and a short worldview note. Use a clean production-design board layout on a light background. Keep the same face, age, hairstyle, proportions, outfit, and signature props across all views.
```

## Expression Grid Pattern
```text
Create a 16-panel expression grid of [character]. Keep face shape, hairstyle, outfit, age, proportions, and visual identity highly consistent across all panels. Expressions: happy, sad, angry, surprised, shy, speechless, evil grin, contemplative, curious, proud, wronged, disdainful, confused, scared, crying, heart expression.
```

## Cast Board Pattern
```json
{
  "type": "cast reference board",
  "layout": "clean production design board, separated labeled sections",
  "characters": [
    {
      "name": "...",
      "role": "...",
      "identity_anchor": "face, hair, outfit, silhouette, palette",
      "full_body_poses": 3,
      "expressions": 4,
      "detail_shots": 6
    }
  ],
  "continuity": "stable proportions, palette, outfit, and design language across all panels"
}
```

## Plotloom Requirements
For each core character, capture:
- identity anchor: face, age, hair, body/silhouette;
- wardrobe lock and signature prop;
- palette and rendering style;
- expression list relevant to the drama genre;
- `do-not-change` invariants;
- target file path: `assets/cast/<slug>/character-grid.png`.

## Codex Image Generation Adapter
Use the `codex-app-server` image adapter when generating character grids through Codex. It depends on the user's local Codex install/auth and built-in `image_generation` capability, not on a machine-specific helper path. The adapter should follow the `codex-imagegen2-api` local JSON contract: prompt + optional images -> generated image path / `file://` URL.

Command shape:

```bash
plotloom image generate \
  --adapter codex-app-server \
  --kind cast \
  --character <character-slug> \
  --prompt-file /path/to/character-grid-prompt.txt \
  --repo /path/to/series-repo
```

Always ensure the generated image is copied into the Plotloom series repo at `assets/cast/<character-slug>/character-grid.png` instead of remaining only under Codex's generated-images storage.

## Avoid
- Style-locking to a third-party IP unless the user explicitly asks.
- Treating a generated image as accepted without asset selection.
- Mixing two characters in one reference sheet unless producing a cast board.
