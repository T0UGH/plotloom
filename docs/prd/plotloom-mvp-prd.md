# Plotloom MVP PRD

> Status: Draft v0.1  
> Date: 2026-04-28  
> Owner: 贵平  
> Agent: Nova

## 1. One-line Definition

Plotloom is an agent-neutral short-drama production skill system.

It gives AI agents a set of composable short-drama production skills so they can help create a short-drama series from idea to first-episode video package, without binding the workflow to a specific agent runtime, model, CLI, or platform.

In short:

```text
Plotloom = short-drama production superpowers for agents
```

## 2. What Plotloom Is Not

Plotloom must not become a generic project-management or workflow platform.

Plotloom does not do:

- task boards
- progress management
- dashboards
- generic workflow runtime
- LangGraph / worker / queue orchestration
- heavy production tracking
- model-specific product lock-in
- a traditional film-production document stack

Plotloom is a short-drama production skill system, not a PM system.

## 3. MVP Goal

The MVP should prove that an AI agent can use Plotloom to produce the first episode of a short-drama series while preserving enough series context for later episodes.

MVP output:

```text
A Plotloom series repo containing:
- series-level context
- core character definitions and character grids
- first-episode prompt package
- generated video clips
- final stitched first-episode video
```

The MVP focuses on **Episode 1** as the generated video result.

It should still keep the series open-ended: target episode count is user-defined and should be inferred/discussed per story, not hardcoded to 12 or 18.

## 4. Core Principles

### 4.1 Skill Graph, Not Rigid Pipeline

Plotloom is not a fixed 12-step pipeline.

It is a skill graph:

```text
current user intent + repo state + available assets
  -> choose the most relevant Plotloom skill
  -> produce or update the needed artifact
  -> suggest the next useful skill
```

Canonical paths may exist, but they are not mandatory linear workflows.

Examples:

- new short drama from scratch
- continue an existing series repo
- reuse an existing character
- regenerate a character grid
- write or revise video prompts
- draw one more video clip candidate
- stitch accepted clips into final.mp4
- deliver media to Feishu or another channel

### 4.2 Minimal Artifacts

Plotloom should avoid creating unnecessary intermediate files.

For each episode, only these prompt artifacts are allowed by default:

```text
episode-card.md      # optional intent anchor
video-prompts.md     # Chinese creative source prompt
video-prompts-en.md  # English model-ready prompt, generated when needed
```

Do not add by default:

- script.md
- storyboard.md
- director-brief.md
- visual-plan.md
- image-prompts.md
- review.md
- manifest.json
- YAML files
- JSON files

### 4.3 TOML + Markdown, No YAML/JSON

For the MVP, Plotloom should use Markdown for human-readable creative content.

If structured config is later required, use TOML.

Do not use YAML or JSON for core repo artifacts.

### 4.4 User-facing Chinese, Model-facing English

Language policy:

- User interaction: Chinese
- Series repo creative files: Chinese by default
- `video-prompts.md`: Chinese creative source
- `video-prompts-en.md`: English model-ready prompt
- Model submission: English
- Short-drama dialogue: English by default, because the first target is overseas publishing

### 4.5 Model-agnostic Core

Plotloom must not bind itself to any specific model, CLI, or API.

Examples of tools that may change:

- 即梦 CLI
- Seedance / Volcengine API
- Alibaba API
- future video/image models
- manual web UI workflows

Plotloom core skills express short-drama production intent. Tool adapters translate that intent to a concrete model, CLI, API, or manual workflow.

### 4.6 Feishu in MVP, But Not the Only Delivery Target

Feishu is in MVP because the primary user interaction happens in Feishu and generated images/videos need to be returned there.

But Feishu is a delivery adapter, not the product center.

Other delivery targets may include:

- Codex App
- local folder
- web preview
- other chat systems

## 5. MVP Series Repo Structure

A Plotloom repo represents one short-drama series.

Default location:

```text
plotloom_repo/<slug>/
```

Minimal structure:

```text
plotloom_repo/<slug>/
  series.md
  characters.md

  assets/
    cast/
      <character-slug>/
        character-grid.png
        notes.md
    scenes/
      <scene-slug>/
        candidates/
          v001.png
          v002.png
          v003.png
        selected.png
        notes.md

  episodes/
    ep001/
      episode-card.md
      video-prompts.md
      video-prompts-en.md

      images/
        covers/
          candidates/
            v001.png
            v002.png
            v003.png
          selected.png

      videos/
        clip-01/
          candidates/
            v001.mp4
            v002.mp4
          selected.mp4
        clip-02/
          candidates/
            v001.mp4
          selected.mp4
        final.mp4
```

Notes:

- `series.md` and `characters.md` are Chinese creative context files.
- `assets/cast/` stores reusable character assets across episodes.
- `assets/scenes/` stores reusable scene assets if needed.
- Episode-specific covers and videos live inside `episodes/epXXX/`.
- Large media may stay local; Git is optional and not required for MVP.

## 6. Character Asset Rule

Core characters must have a character grid before video generation.

A character grid is not a candidate grid.

It is a single canonical character turnaround sheet showing the same character across useful views, for example:

```text
front view
back view
side view
3/4 view
expressions
full-body / half-body variations
key costume details
```

Path:

```text
assets/cast/<character-slug>/character-grid.png
```

Rules:

- Main/core characters must have `character-grid.png` before video generation.
- Minor background characters do not need a character grid.
- If a character is redesigned, regenerate the whole character grid.
- Do not treat grid cells as separate selected candidates.
- Do not create `selected.png` for cast assets in MVP.

## 7. Scene and Cover Asset Rules

Scenes are not always mandatory.

Rules:

- Key recurring scenes may have scene reference images.
- Ordinary one-off scenes may be described directly in video prompts.
- Scene assets use single-image candidates, not character grids.

Scene path:

```text
assets/scenes/<scene-slug>/
  candidates/v001.png
  candidates/v002.png
  selected.png
```

Covers are episode-specific:

```text
episodes/ep001/images/covers/
  candidates/v001.png
  candidates/v002.png
  candidates/v003.png
  selected.png
```

Image gacha rule:

- Character grid: generate/regenerate as a whole grid.
- Scene image: candidate-based.
- Cover image: candidate-based, typically 3 candidates.

## 8. Episode Artifacts

### 8.1 `episode-card.md` Optional

`episode-card.md` is an optional intent anchor.

It may include:

- episode logline
- episode hook
- emotional payoff
- reversal
- cliffhanger
- core characters
- this episode's role in the larger series

It is not a script, not a storyboard, and not a task plan.

If user intent is already clear enough, Plotloom may skip it.

### 8.2 `video-prompts.md` Required

`video-prompts.md` is the Chinese creative source for video generation.

It should contain clip-level prompts in Chinese.

Example structure:

```markdown
# EP001 Video Prompts

## Clip 01
中文创作版连续叙事 prompt...

## Clip 02
中文创作版连续叙事 prompt...
```

### 8.3 `video-prompts-en.md` Generated When Needed

`video-prompts-en.md` is the English model-ready version.

It is generated from `video-prompts.md` when the agent is about to call or submit to a model.

Example structure:

```markdown
# EP001 Video Prompts EN

## Clip 01
English model-ready continuous narrative prompt...

## Clip 02
English model-ready continuous narrative prompt...
```

## 9. Video Prompt Design

Plotloom must not treat video models as one-shot-per-shot APIs.

For Seedance-like models, the correct model-facing unit is a continuous narrative prompt task.

Principles:

```text
Seedance prompt != shot list
Seedance prompt = continuous narrative timeline
```

A prompt task may contain multiple visual beats or camera cuts, but it must preserve one main timeline.

Good model-facing prompts should describe:

- asset references and their purpose
- continuous scene progression
- timed beats such as 0-3s / 4-8s / 9-12s / 13-15s
- character entrance, exit, blocking, and spatial continuity
- camera path and visual emphasis
- dialogue windows
- sound / ambience / music if needed
- ending frame suitable for continuation

Plotloom may use internal skill reasoning similar to a director brief, but `director-brief.md` is not a required repo artifact.

## 10. Video Generation and Gacha

### 10.1 Clip-based Video Generation

Episode 1 is generated as multiple clips.

Rules:

- Each clip is around 15-20 seconds.
- Each clip corresponds to one prompt section in `video-prompts.md` / `video-prompts-en.md`.
- Video is drawn one candidate at a time.
- After each candidate is generated, deliver it to the user immediately.
- The user can accept, reject, ask for another draw, or ask to revise the prompt.

Directory:

```text
episodes/ep001/videos/clip-01/candidates/v001.mp4
episodes/ep001/videos/clip-01/candidates/v002.mp4
episodes/ep001/videos/clip-01/selected.mp4
```

### 10.2 Final Stitching Required

MVP should produce a final episode video:

```text
episodes/ep001/videos/final.mp4
```

Stitching may be simple concat, but Plotloom must validate that selected clips are compatible.

Before stitching, selected clips must have the same or compatible:

- aspect ratio
- resolution
- frame rate if relevant
- codec/container if relevant
- audio presence / audio format if relevant

If clips are incompatible, the agent must either normalize them or stop and report the issue.

This is not a full editing system. It is the minimum needed to assemble accepted clips into one playable episode.

## 11. Delivery

MVP delivery must support Feishu.

Behavior:

- Every generated video candidate is returned immediately.
- Image candidates may be returned in batches.
- Delivery message should identify episode, clip, version, and what decision is needed.

Example:

```text
EP001 / Clip 01 / v002
请选择：接受 / 继续抽 / 修改 prompt 后重抽
```

Feishu is not a progress tracker. It is a media delivery and feedback channel.

## 12. Entry Behavior

When Plotloom starts:

- If current directory contains `series.md`, treat it as the current Plotloom repo and continue.
- If no `series.md` exists, ask whether to create a new Plotloom repo.
- If the user only asks for an isolated video prompt, do not force repo creation.

A new repo represents one short-drama series.

## 13. MVP Skill Set

The MVP should focus on a small set of composable skills.

Suggested skills:

```text
using-plotloom
plotloom-create-series
plotloom-design-character-grid
plotloom-write-video-prompts
plotloom-translate-video-prompts-en
plotloom-draw-image
plotloom-draw-video-clip
plotloom-deliver
plotloom-stitch-clips
```

Possible later skills:

```text
plotloom-market-sense
plotloom-cover-click-review
plotloom-series-continuation
plotloom-character-refresh
plotloom-model-adapter-optimizer
```

Commercial judgement / market-sense is not MVP.

## 14. Out of MVP

The following are explicitly out of MVP:

- real platform market data research
- short-drama business scoring gates
- dashboard
- task tracking
- fixed workflow engine
- automatic multi-model benchmarking
- full audio/music pipeline
- platform publishing automation
- long-season full script generation
- mandatory Git or GitHub integration
- YAML/JSON artifact schemas

## 15. MVP Success Criteria

Plotloom MVP is successful if:

1. A user can create or continue a Plotloom series repo.
2. Core characters have reusable `character-grid.png` assets.
3. Episode 1 has `video-prompts.md` and `video-prompts-en.md`.
4. The agent can generate video candidates one clip at a time.
5. Each candidate can be delivered back to the user, especially via Feishu.
6. The user can accept/reject/redraw clip candidates.
7. Accepted clips can be stitched into `episodes/ep001/videos/final.mp4`.
8. The system avoids becoming a PM tool, dashboard, or over-designed artifact protocol.

## 16. Current Open Questions

These are intentionally left for later, not MVP blockers:

- Which concrete image/video model adapter should be first?
- Whether to support Git/LFS for media-heavy repos.
- Whether to create a Codex App preview adapter.
- Whether to add market-sense after the production loop works.
- How to package and distribute skills across Codex / Claude Code / OpenClaw / Hermes.
