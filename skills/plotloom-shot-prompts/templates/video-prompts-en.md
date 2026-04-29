# Episode {{episode_number}} Video Prompts (English Adapter Copy)

> Preserve the source intent from `video-prompts.md`. Do not add new plot during translation.
> This file is still a Plotloom artifact, not the exact Dreamina CLI input. The adapter must extract one clip block into a single `--prompt` string plus CLI flags.

## clip-01
- Source clip id: `clip-01`
- Target adapter: Dreamina CLI
- Recommended command: `multimodal2video` if reference images exist; otherwise `text2video`
- Duration seconds: 15
- Ratio: 9:16
- Model version: seedance2.0fast_vip
- Reference images and purpose:
  - `assets/cast/{{character_slug}}/character-grid.png` — identity and outfit continuity; pass as `--image` only when using `multimodal2video`
- Prompt string for `--prompt`:
  ```text
  [Write one continuous cinematic prompt string here. Do not include Markdown bullets. Include visible action, character identity, camera motion, dialogue window if any, ending frame, and negative constraints such as no subtitles, no watermark, no logo.]
  ```
- Continuity rules:
- Camera motion:
- Dialogue / audio window:
- Ending frame / handoff point:
- Adapter-specific notes:
  - If using `text2video`, rewrite reference-image information into the prompt; the CLI will not read local images.
  - If using `multimodal2video`, pass real local paths with repeated `--image` flags.

## clip-02
- Source clip id: `clip-02`
- Target adapter: Dreamina CLI
- Recommended command: `multimodal2video` if reference images exist; otherwise `text2video`
- Duration seconds: 15
- Ratio: 9:16
- Model version: seedance2.0fast_vip
- Reference images and purpose:
- Prompt string for `--prompt`:
  ```text
  [One continuous cinematic prompt string. No Markdown bullets in the CLI input.]
  ```
- Continuity rules:
- Camera motion:
- Dialogue / audio window:
- Ending frame / handoff point:
- Adapter-specific notes:
