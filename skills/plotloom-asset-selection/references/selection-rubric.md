# Selection Rubric

## Decision Output
Use one decision:
- `accept`
- `reroll`
- `revise_prompt`
- `ask_user`

## Scoring Dimensions
### Intent Match
Does the candidate perform the source prompt's action and emotional beat?

### Character Consistency
Does it preserve face, age, hairstyle, outfit, proportions, palette, and signature props from `character-grid.png` or reference sheet?

### Visual Continuity
Does motion, lighting, scene, prop placement, and ending frame remain coherent with surrounding clips?

### Short-Drama Clarity
Can the viewer understand conflict and status reversal quickly?

### Hook Strength
Does the opening or final moment create a reason to continue?

### Artifact Severity
Check hands, faces, text, warped props, temporal flicker, impossible motion, incoherent backgrounds, and unreadable pseudo-subtitles.

### Ending Frame / Handoff
Does the last frame support the next clip or episode?

## Thresholds
- **Accept** if intent and continuity are strong and artifacts are minor.
- **Reroll** if intent is right but artifacts are random/sample-specific.
- **Revise prompt** if failures are systematic: wrong action, missing reference, unclear ending, overloaded dialogue, or conflicting camera instructions.
- **Ask user** if two candidates trade off taste, style, or commercial direction.

## Image-Specific Notes
For character sheets or expression grids, reject or revise if identity changes across panels, outfit mutates, extra characters appear, labels become unreadable, or the grid lacks the required front/side/back or expression coverage.

## Video-Specific Notes
Review one candidate at a time. Watch for face drift over time, impossible hand movement, temporal flicker, action that does not reach the ending frame, or dialogue that feels too dense for the duration.

## Selected Semantics
Accepted files are copied to `selected.*`; previous selected files are backed up as `selected-prev-YYYYMMDD-HHMMSS-ffffff.*`; candidates remain untouched.
