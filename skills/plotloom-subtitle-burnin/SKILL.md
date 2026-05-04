---
name: plotloom-subtitle-burnin
description: >-
  Use when a Plotloom final video needs English subtitles, Chinese subtitles, bilingual English+Chinese subtitles, subtitle timing alignment, ASS/SRT artifacts, burned-in captions, or verified review copies for delivery.
---

# Plotloom Subtitle Burn-in

## When to Use
Use after a final Plotloom video exists and the user asks to add subtitles, translate subtitles, burn captions into video, or prepare a subtitled delivery copy.

## Core Rule
Generate and align subtitles against the exact final video, not per-clip or per-episode fragments. Per-fragment subtitles introduce concat-boundary drift and make review harder.

## Inputs
- Final source video, usually `episodes/epXXX/videos/final.mp4` or `outputs/.../final.mp4`.
- Optional existing English script, prompt file, SRT, ASS, or ASR JSON for correction.
- Requested mode: English-only, Chinese-only, or bilingual English primary + Chinese below.

## Outputs
- Reviewable subtitle files: `.ass` as the styling source, `.srt` as exchange/review artifact.
- Burned HD video with explicit name such as `final-subtitled-v001.mp4` or `final-bilingual-en-zh-v001.mp4`.
- Smaller review copy when delivery channel benefits from compression.
- Contact sheet or sampled frames from the burned output.

## Workflow
1. Identify the exact final source video and encode source/version/mode in output names.
2. Extract mono 16 kHz audio from the final video:
   ```bash
   ffmpeg -y -i "$VIDEO" -vn -ac 1 -ar 16000 audio_16k_mono.wav
   ```
3. Generate first-pass timing with stable-ts or WhisperX. Prefer segment-level captions over word-level karaoke output:
   ```bash
   stable-ts audio_16k_mono.wav --model small -f json,srt,ass,txt --max_chars 42 --max_words 10 --overwrite
   ```
4. Correct obvious ASR mistakes against project source material, especially `video-prompts-en.md`, scripts, character names, place names, and recurring terms. Do not invent dialogue.
5. Translate only after the English text and timing are stable. Keep Chinese faithful and short enough for subtitle reading speed.
6. Generate ASS for final styling and SRT for review. Keep one timed event per subtitle segment unless there is clear drift evidence.
7. Burn with libass-enabled ffmpeg. If default ffmpeg lacks `ass` / `subtitles`, use an explicit full build:
   ```bash
   FF=/usr/local/opt/ffmpeg-full/bin/ffmpeg
   $FF -hide_banner -filters | grep -E ' ass|subtitles'
   $FF -y -i "$VIDEO" -vf "ass=$ASS" -c:v libx264 -crf 18 -preset slow -c:a copy "$OUT"
   ```
8. Derive any review-small version from the burned HD output so typography stays identical.
9. Verify by decoding and by visual frames from the burned output, not only by checking that ffmpeg exited:
   ```bash
   $FF -v error -i "$OUT" -f null -
   $FF -v error -i "$SMALL" -f null -
   ```

## Bilingual English + Chinese Style
When English is primary and Chinese should sit below it:
- ASS text format: `English sentence\N（中文翻译。）`.
- English is first line; Chinese is second line.
- Use Chinese full-width parentheses `（ ）` for the Chinese line.
- Use `\N` as the ASS line break, not literal `\\N`.
- For 1280×720, start around `Fontsize=38-42`, `Outline=4`, `Shadow=1`, `MarginV=70-85`.
- If the two-line block is too dense, shorten the Chinese translation or reduce font slightly; avoid three-line subtitles unless unavoidable.

## Review Checklist
- Source video is the final intended video, not an old subtitled or partial version.
- Subtitle timing was generated/aligned from the full final video.
- English and Chinese text share the same timing events in bilingual mode.
- Burned HD and small review copy both decode without errors.
- Contact sheet confirms subtitles are visible, centered, not cropped, and not seriously blocking key faces/actions.
- Delivery messages must not expose OAuth codes, device codes, file tokens, doc tokens, API keys, or secrets; write `[REDACTED]` if a token must be mentioned.

## Failure Modes
- Timing drifts near episode boundaries: regenerate from the final concatenated video instead of fixing fragment offsets by hand.
- Subtitles are invisible: inspect ASS `Style`, `Layer`, color alpha, font size, and bottom margin; render a single test frame before full encode.
- ffmpeg says `No such filter: ass` or `subtitles`: install/use a libass-enabled ffmpeg build.
- Chinese lines overcrowd the frame: shorten translation first; then adjust font and margins.
- Upload fails with an absolute path: retry from the file directory with a relative `--file ./name.mp4` path.
