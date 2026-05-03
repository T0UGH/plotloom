---
name: plotloom-character-reference-sheet
description: >-
  Creates production-grade character reference sheet briefs/prompts for Plotloom short dramas: turnaround, color palette,
  expressions, micro-expressions, head details, wardrobe/accessory details, props, and hand gestures for AI-video consistency.
---

# Plotloom Character Reference Sheet

## When to Use
Use when the user asks for a character reference sheet / 角色设定图 / model sheet / turnaround sheet / AI-video character consistency asset, or when ordinary character grids are not enough for stable video production.

Use this before video generation when a named character needs stable identity, wardrobe, expression acting, props, or hand/gesture continuity.

## Inputs
- `series.md` and `characters.md`, if a Plotloom series repo already exists.
- User-approved character concept: name, role, age range, genre, personality, visual archetype, costume state, signature props.
- Optional existing images: character grid, portrait, style reference, storyboard keyframes, costume reference.
- Target output character slug, e.g. `aelia`, `cassian`, `selene`.

## Outputs
Create or update a production asset folder such as:

```text
assets/cast/<slug>/reference-sheet/
  brief.md
  prompt-imagegen2.txt
  negative-notes.md
  reference-inputs.json
  candidates/
  selected.png
```

For human-readable cast records, also update `characters.md` with the final selected path:

```text
assets/cast/<slug>/reference-sheet/selected.png
```

## Why This Format
A normal 3x3 character grid is useful for early visual exploration, but it often fails for AI video continuity because it emphasizes attractive portraits rather than production constraints. A full character reference sheet should lock:

- identity and silhouette
- front / 3-4 / side / back body views
- color palette
- expression progression
- micro-expressions
- head / hair details
- wardrobe and accessory construction
- signature prop design
- hand gestures and object-use gestures

This makes the character easier to reproduce across shots, angles, emotions, costumes, and video prompts.

## Required Sheet Sections
Every production sheet prompt should ask for these panels unless the user deliberately wants a lighter sheet:

1. **Character Metadata Block**
   - Name
   - Alias / title
   - Role
   - Age range
   - Personality keywords
   - Speech / posture / body-language notes
   - AI-video continuity invariants

2. **Main Identity + Scale Sheet**
   - full-body front view
   - full-body 3/4 front view
   - full-body side view
   - full-body back view
   - silhouette / height guide
   - body proportion and posture notes

3. **Color Palette**
   - skin
   - hair
   - primary costume color
   - secondary costume color
   - metal / jewelry / weapon color
   - shadow / accent color

4. **Expression Progression**
   - neutral
   - guarded smile
   - wounded / betrayed
   - anger restrained
   - shock
   - fear hidden under pride
   - determination
   - cold victory / comeback

5. **Micro Expressions**
   - eye tension
   - brow changes
   - mouth-corner shifts
   - side glance
   - suppressed tears
   - suspicious look
   - pre-revenge calm

6. **Head Detail Sheet**
   - front head
   - 3/4 head
   - side profile
   - back hair view
   - hair ornament / crown / scars / curse mark details

7. **Wardrobe / Accessories Details**
   - collar / neckline
   - sleeves / cuffs
   - belt / waist detail
   - shoes / boots
   - cape / train / skirt structure
   - jewelry / family crest / curse mark
   - fabric/material notes

8. **Prop Sheet**
   - signature prop front view
   - side/back view when relevant
   - active / glowing / broken state
   - how the character holds or wears it

9. **Hand Gestures**
   - relaxed hand
   - fist
   - pointing / accusing
   - signing contract
   - holding prop
   - touching pendant / crest / curse mark
   - reaching / refusing / gripping

## Prompt Rules
- Ask for **one single clean reference-sheet image**, not separate illustrations.
- Ask for readable panel layout with clear section blocks.
- Use minimal readable English section headers only; avoid long tiny captions that become gibberish.
- Do not include social-media UI, subtitles, watermark, logos, app overlays, likes, stars, or random numbers.
- Do not make the sheet a beauty poster. It is a production document.
- Preserve one outfit per sheet. If a character has multiple story states, make separate sheets:
  - `nameless-maid`
  - `contract-duchess`
  - `true-heiress`
- For AI-video continuity, include do-not-change invariants explicitly: face shape, hair silhouette, costume palette, signature prop, body language, and key accessories.
- For female-oriented short dramas, prioritize expressive acting references: betrayal, restrained hurt, comeback confidence, romantic guardedness, power shift.

## Recommended ImageGen2 / Codex Prompt Template
Use this as the base for `prompt-imagegen2.txt`:

```text
Create ONE production-grade CHARACTER REFERENCE SHEET for an AI-video short-drama character.

Character: <NAME>
Alias / title: <ALIAS>
Role: <ROLE>
Age range: <AGE>
Genre / market: <GENRE>
Personality keywords: <KEYWORDS>
Core contradiction: <CONTRADICTION>

Visual identity:
<FACE, HAIR, BODY, COSTUME, PALETTE, ACCESSORIES, PROP>

The sheet must be a clean professional animation / game / film concept-art reference sheet, not a poster, not a fashion illustration, not a social media screenshot.

Required layout, all in one vertical or wide production sheet:
1. CHARACTER METADATA BLOCK: name, alias/title, role, age, personality keywords, visual invariants.
2. MAIN IDENTITY + SCALE SHEET: full-body front view, 3/4 front view, side view, back view, plus a small silhouette/height guide.
3. COLOR PALETTE: 6-8 clean swatches matching skin, hair, main costume, secondary costume, metal/jewelry, accent/shadow colors.
4. EXPRESSION PROGRESSION: 8 bust/head expressions: neutral, restrained hurt, shock, anger restrained, suspicious side glance, suppressed tears, determination, cold comeback confidence.
5. MICRO EXPRESSIONS: close crops of eyes/brows/mouth showing subtle acting changes.
6. HEAD DETAIL SHEET: front, 3/4, side profile, back hair view, and key ornament/mark details.
7. WARDROBE / ACCESSORIES DETAILS: collar, sleeves, belt/waist, shoes, jewelry/crest/curse mark, fabric and construction closeups.
8. PROP SHEET: signature prop in normal and active/broken/glowing state, with how it is held/worn.
9. HAND GESTURES: relaxed hand, fist, pointing/accusing, signing contract, holding prop, touching key accessory, reaching/refusing gesture.

Style: <STYLE>. Consistent face and costume across every panel. Clean readable panel grid, production reference sheet, high detail, coherent proportions, no extra characters.

Hard constraints:
- no watermark, no logo, no social media UI, no Chinese subtitles, no random numbers
- no long unreadable micro text except simple section labels
- no inconsistent outfits between panels
- no duplicate different characters
- no distorted hands or extra fingers
- no beauty poster composition

Return JSON with image_path and notes.
```

## Plotloom Command Shape
When using the current Plotloom image path, generate via `plotloom image generate` so the asset stays in the repo-first flow:

```bash
plotloom --repo /Users/haha/plotloom_repo/<slug> image generate \
  --kind cast \
  --character <character-slug> \
  --filename reference-sheet/candidates/v001.png \
  --prompt-file /Users/haha/plotloom_repo/<slug>/assets/cast/<character-slug>/reference-sheet/prompt-imagegen2.txt \
  --image /optional/existing-character-grid-or-style-ref.png \
  --timeout 600
```

After visual review, copy or regenerate the accepted image to:

```bash
plotloom --repo /Users/haha/plotloom_repo/<slug> image generate \
  --kind cast \
  --character <character-slug> \
  --filename reference-sheet/selected.png \
  --prompt-file /Users/haha/plotloom_repo/<slug>/assets/cast/<character-slug>/reference-sheet/prompt-imagegen2.txt \
  --image /optional/existing-character-grid-or-style-ref.png \
  --timeout 600
```

Or copy the accepted candidate manually:

```bash
cp assets/cast/<character-slug>/reference-sheet/candidates/v001.png \
   assets/cast/<character-slug>/reference-sheet/selected.png
```

Do not merely write `prompt-imagegen2.txt` and stop when the user expects an image; this skill is an image-production skill.

## Workflow
1. Locate the active Plotloom series repo. If no repo exists, hand off to `plotloom-series-brainstorming` first.
2. Read `series.md`, `characters.md`, and any existing `assets/cast/<slug>/` images.
3. Decide whether this is a first-pass sheet or a state-specific sheet (`nameless-maid`, `contract-duchess`, `true-heiress`, etc.).
4. Write `assets/cast/<slug>/reference-sheet/brief.md` with stable identity, story function, visual invariants, palette, expressions, wardrobe, prop, and hand gestures.
5. Write `prompt-imagegen2.txt` using the template above.
6. Write `reference-inputs.json` listing all source images used and their purpose.
7. Generate candidates with `plotloom image generate` directly; do not stop at prompt files unless the user explicitly asks for prompt-only work.
8. Review candidates visually for:
   - same person across panels
   - complete front/side/back body views
   - readable expression progression
   - useful micro-expression details
   - wardrobe and prop consistency
   - no watermark/social UI/subtitle overlays
   - no unreadable text dominating the sheet
9. Copy the accepted candidate to `selected.png` and update `characters.md` with the path.

## Quality Bar
A good character reference sheet must answer:

- Can a video model keep this character consistent across front, side, back, and motion?
- Can a prompt writer describe this character without inventing missing costume details?
- Can an animator or AI video generator infer how this character emotes?
- Are the signature props and hand gestures clear enough for repeated story use?
- Does the sheet reduce ambiguity compared with a 3x3 beauty grid?

## Failure Modes
- If the output is a collage of pretty portraits only: rerun with stronger `production reference sheet / turnaround / wardrobe details / hand gestures` wording.
- If tiny text becomes gibberish: keep only section headers and store real metadata in `brief.md`.
- If outfits change across panels: split into separate outfit-state sheets or reduce visual complexity.
- If face identity drifts between panels: use a selected portrait or character grid as a reference image and explicitly say `same face in every panel`.
- If hands are poor: generate a separate hand/prop sheet rather than forcing everything into one image.

## Next Skill Handoff
- Use `plotloom-shot-prompts` after selected reference sheets exist and the user wants video prompts.
- Use `plotloom-video-adapter` when prompts are ready for Dreamina/Seedance generation.
- Use `plotloom-asset-selection` to accept/reroll generated sheet candidates.
