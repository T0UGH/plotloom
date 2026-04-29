# Visual Continuity Reference

## Character Grid Usage
Use `character-grid.png` as the identity anchor for face, age, outfit, hairstyle, body type, palette, and rendering style. Refer to the image by path and state its purpose.

## Stable vs Mutable Traits
Stable traits should not change without user approval:
- face shape, age, hair, proportions;
- wardrobe lock and signature prop;
- palette and render style;
- relationship to other recurring characters.

Mutable traits may change by episode only if the story requires it:
- expression;
- pose;
- temporary dirt/damage/wetness;
- location lighting.

## Reference Sheet / Expression Grid Inputs
GPT Image 2 prompt libraries often use official character sheets, expression grids, and cast boards. When those exist, cite the exact file and describe the intended use: identity, expression, costume, prop, or scene style.

## Inter-Clip Handoff
For clip continuity, capture:
- starting state from previous clip;
- ending frame / tail pose;
- prop position;
- whether the character enters, exits, turns, or is occluded;
- whether first/last-frame images should be used by the adapter.

## Movement and Occlusion
Describe entrance, exit, partial occlusion, turns, and handoffs when continuity could break. Mention when the character remains visible throughout the clip.

## Camera Instructions
Use one dominant camera idea per clip. Avoid mixing contradictory instructions such as locked-off + fast tracking + drone orbit in the same 15-second task.

## Common Model Failures
- Face drift across time.
- Age drift.
- Outfit or prop mutation.
- Temporal flicker.
- Impossible hand motion.
- Background or text artifacts.
- Ending frame that does not match the next clip handoff.

## Rerun Notes
After failed candidates, write whether to retry the same prompt or revise the prompt. Revision notes should name the failure: character drift, visual continuity break, weak hook, artifact, pacing, unclear ending frame, or dialogue overload.
