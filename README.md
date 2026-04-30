# Plotloom

Agent-neutral short-drama production skills — a repo-first skill pack for turning a short-drama idea into series context, video prompts, candidates, selected clips, and `final.mp4`.

> Working name history: early notes used `dramaclaw`; the product/repo name is now **Plotloom**.

## What Plotloom Is

Plotloom is a **skill-first short-drama production pack**, not a runtime, dashboard, queue, or project-management system.

Core flow:

```text
series idea
  -> series.md / characters.md
  -> optional episode-card.md
  -> video-prompts.md / video-prompts-en.md
  -> fake or real video candidate
  -> accept / reroll / revise_prompt
  -> selected.mp4 clips
  -> final.mp4
```

## Install Skills

Default install path is **skills.sh** via the `skills` CLI.

### Install from GitHub

```bash
npx skills add T0UGH/plotloom --all
```

Useful variants:

```bash
# Project-level install, choose agents interactively
npx skills add T0UGH/plotloom

# Install globally/user-level
npx skills add T0UGH/plotloom --global --all

# Install only one skill
npx skills add T0UGH/plotloom --skill plotloom-shot-prompts --all

# List skills in the repo without installing
npx skills add T0UGH/plotloom --list
```

If the repository is private, make sure the local GitHub/Codex/agent environment can access `T0UGH/plotloom` before installing.

### Local development install

From this repository root:

```bash
npx skills add . --list
npx skills add . --all
```

`skills.sh` / `npx skills` can install to multiple agent targets such as Cursor, Claude Code, and other supported skill hosts. Use `--agent <agent>` to restrict targets when needed.

## Skills

```text
skills/
  plotloom-series-bible/      # series.md, characters.md, character asset briefs
  plotloom-episode-card/      # lean episode intent card
  plotloom-shot-prompts/      # continuous Seedance/Dreamina-style video prompts
  plotloom-video-adapter/     # fake/Dreamina candidate generation contract
  plotloom-asset-selection/   # accept/reroll/revise_prompt and selected.* semantics
  plotloom-stitch-deliver/    # ffprobe/ffmpeg stitch and delivery boundary
```

Each skill includes `SKILL.md`; most also include `references/`, `templates/`, and `evals/evals.json` for validation and future skill-creator workflows.

## Repository Layout

```text
docs/
  prd/
  design/
  plans/
  decisions/
  research/
skills/
templates/series-repo/
scripts/
  init_series.py
  validate_repo.py
  select_candidate.py
  ffprobe_media.py
  stitch_ffmpeg.py
  adapters/fake_video.py
adapters/
  codex.md
  dreamina.md
  hermes.md
  claude-code.md
  opencode.md
examples/tiny-series/
```

## Minimal Local Verification

```bash
python scripts/validate_repo.py --repo examples/tiny-series
python scripts/adapters/fake_video.py --output /tmp/plotloom-plan-check/v001.mp4
ffprobe -v error /tmp/plotloom-plan-check/v001.mp4
```

Full fake E2E:

```bash
python scripts/init_series.py --slug fake-heiress-reboot --title "Fake Heiress Reboot" --path /tmp/plotloom-demo/fake-heiress-reboot
cp examples/tiny-series/episodes/ep001/video-prompts.md /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/video-prompts.md
python scripts/adapters/fake_video.py --output /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/candidates/v001.mp4
python scripts/select_candidate.py --candidate /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/candidates/v001.mp4 --selected /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/selected.mp4
python scripts/stitch_ffmpeg.py --output /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/final.mp4 /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/selected.mp4
ffprobe -v error /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/final.mp4
```

## Real Adapters

- Image generation: local Codex install plus Codex app server, documented in `adapters/codex.md`.
- Video generation: Dreamina/即梦 CLI, HappyHorse through fal.ai, and VolcEngine Seedance through Ark async APIs.
- Stitching: local `ffmpeg` / `ffprobe` helpers.
- Delivery: Feishu/Lark is delivery only, not state center.

## Design Boundaries

Do not add these to MVP:

- dashboard
- database
- workflow runtime
- queue worker
- hidden workflow state
- mandatory `script.md`, `storyboard.md`, `director-brief.md`, or `review.md`
- batch-heavy video generation

Plotloom should stay prompt-first, repo-first, and adapter-thin.

## Tagline

Weave short dramas from sparks.
