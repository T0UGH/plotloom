---
name: plotloom-storyboard-flowchart
description: >-
  Creates dark table-style Chinese storyboard flowcharts for Plotloom short dramas. Use when the user asks for
  15秒导流流程图, 分镜头脚本, black-background storyboard tables, numbered shot rows, Chinese dialogue columns,
  image-generation prompts for storyboard sheets, or red face-grid overlays on character faces.
---

# Plotloom Storyboard Flowchart

## When to Use
Use this skill when the user wants a short-drama scene, episode beat, or pasted script turned into a single storyboard flowchart image or image prompt.

Use especially for:
- `15秒导流流程图（分镜头脚本）`
- 黑底表格分镜
- short-video storyboard table
- a reference-style sheet with `镜头号 / 时间 / 景别 / 画面内容 / 镜头方式 / 表演调度 / 台词`
- face-obscuring overlays such as `红色网格线遮挡`, `脸部网格`, or `面部追踪线框`

Do not use this for full episode planning when `plotloom-episode-card` is missing and the user has not supplied a scene. Do not use it for continuous video prompt tasks; hand off to `plotloom-shot-prompts` for that.

## Inputs
- Optional `series.md` and `characters.md`
- Optional `episodes/epXXX/episode-card.md`
- User-provided scene/script/dialogue
- Optional reference image for layout style only
- Required visual constraints: character age, style, props, overlay rules, aspect ratio, language

## Outputs
Create or update episode-local artifacts when working inside a Plotloom series repo:

```text
episodes/epXXX/storyboard-flowchart.md
episodes/epXXX/storyboard-flowchart-prompt.txt
episodes/epXXX/storyboards/flowchart/selected.png   # only if the host actually generated an image
```

If no Plotloom episode repo is active, provide the refined 5-row plan and image prompt directly in the conversation.

## Read These Resources When...
- Use `templates/storyboard-flowchart.md` for the human-readable shot table.
- Use `templates/storyboard-flowchart-prompt.txt` for the image-generation prompt.
- Read `characters.md` or character reference assets when character identity continuity matters.

## Workflow
1. Identify the episode target.
   - If the user names an episode, use that path.
   - If not, default to `ep001` only when a Plotloom repo exists and the user is clearly asking to create a new storyboard artifact.
   - If there is no repo context, keep the output in chat.

2. Refine the script into 5 storyboard beats by default.
   - A 15-second scene defaults to five 3-second rows.
   - Keep the setup, challenge, prop/proof, reaction, and punchline.
   - Compress repeated dialogue so table text stays readable.

3. Build the production table.
   - Columns: `镜头号`, `时间`, `景别`, `画面内容`, `镜头方式（运镜）`, `表演调度 / 动作`, `台词 / 音乐`.
   - Include enough camera and acting notes for production use, but keep every cell short.
   - Dialogue should be Chinese unless the user asks otherwise.

4. Write the image prompt.
   - Use the prompt template and replace every bracketed placeholder.
   - Preserve the dark production-document look: black background, thin gray/white table lines, numbered rows, center stills, right technical notes, and footer blocks.
   - If the user supplied a style reference, use it for layout language only. Do not copy watermarks, account names, app UI text, logos, or social handles.

5. Preserve continuity constraints.
   - Keep character face, hair, wardrobe, body proportions, and signature props consistent across all rows.
   - For romance or kissing, characters must be clearly adult and the action must be tasteful and non-explicit.
   - For props, preserve exact user constraints such as `写着20的小纸条`, not real cash.

6. Apply overlay rules when requested.
   - For red grid requests, specify: semi-transparent thick red facial tracking mesh, face-only, on every visible face.
   - Do not cover clothing, hands, background, or the whole body unless explicitly requested.

7. Generate only when the host has an image tool and the user wants the actual storyboard image.
   - Otherwise stop after `storyboard-flowchart.md` and `storyboard-flowchart-prompt.txt`.
   - If an image is generated, save or record it at `episodes/epXXX/storyboards/flowchart/selected.png` when possible, while preserving the original generated asset path.

## Prompt Rules
- The storyboard must look like a professional production table, not a poster, marketing page, or comic page.
- Use `16:9` unless the user asks for another aspect ratio.
- Use short, readable Chinese text.
- Add generic right-side short-video-style icons only when the requested reference includes them; keep them non-branded.
- No logos, no watermark, no copied social handle, no unintended English text.
- If text would be too dense, reduce each row to one action phrase and one dialogue line.

## Stop Conditions
Stop when the storyboard table and image prompt are ready, or when the generated image exists and has been recorded. Do not proceed to clip generation unless the user asks; hand off to `plotloom-shot-prompts`.

## Next Skill Handoff
- Use `plotloom-shot-prompts` to turn the same scene into continuous video prompts.
- Use `plotloom-video-adapter` only after video prompts exist.
- Use `plotloom-asset-selection` if multiple generated storyboard images need review.

## Failure Modes
- Missing episode intent: use `plotloom-episode-card` first, unless the user supplied a complete scene.
- Output looks like a comic: strengthen `production storyboard table`, `technical notes`, `shot rows`, and `footer production blocks`.
- Face grid covers the whole image: revise with `face-only overlay`.
- Prop turns into real cash: revise with `plain small paper slip, handwritten number only, no currency symbol, no banknote pattern`.
- Reference watermark appears: revise with `do not copy any watermark, account name, social handle, app UI text, or brand mark`.
