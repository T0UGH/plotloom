# Plotloom MVP Implementation Plan

> Archived: this was the pre-CLI MVP implementation plan. It mentions repo-level Python scripts because those existed at the time; current supported deterministic entrypoint is the `plotloom` CLI.

> **For Hermes / Superpowers:** Use `subagent-driven-development` to execute this plan task-by-task. Keep the implementation prompt-first: write `SKILL.md`, references, templates, and acceptance examples before writing scripts. Do not build a runtime.

**Goal:** Build a minimal Plotloom skill pack that can take a short-drama idea into a first-episode production package, generate/accept video candidates, and stitch selected clips into `final.mp4`.

**Architecture:** Plotloom is a repo-first, agent-neutral skill pack. Core logic lives in prompt contracts and artifact contracts under `skills/` and `templates/`; Python is only allowed for deterministic helpers such as repo skeleton creation, validation, selected-copy backup, ffprobe/ffmpeg glue, and adapter command wrapping.

**Tech Stack:** Markdown + TOML, agent-neutral `SKILL.md`, thin Python helpers, ffmpeg/ffprobe, Codex imagegen adapter docs, Dreamina CLI adapter docs, nova-lark delivery docs.

---

## Implementation Principles

1. **多写 prompt，少写 Python。** 每个阶段先写清楚 agent 应如何判断、写什么 artifact、何时停下来问用户。
2. **Skill graph，不是 pipeline。** 每个 skill 可以独立触发，并根据 repo 现状决定下一步。
3. **Repo contract first。** 所有跨 agent 交接以 series repo 内 Markdown/TOML/media 文件为准。
4. **Scripts are helpers。** Python 只做确定性动作；不做创作判断、不维护 workflow state、不长期运行。
5. **Fake adapter first。** 先用 fake media 跑通 artifact / selected / stitch / delivery dry-run，再接真实 Codex/Dreamina。
6. **Fail fast。** 缺登录、缺会员、缺文件、媒体不兼容时清楚返回，不让 agent 卡死。

---

## Phase 0: Repo Grounding

### Task 0.1: Verify current design baseline

**Objective:** Confirm PRD/design already contain the current boundaries before implementation.

**Files:**
- Read: `docs/prd/plotloom-mvp-prd.zh.md`
- Read: `docs/design/plotloom-technical-design.zh.md`
- Read: `docs/research/2026-04-28-plotloom-agent-neutral-skill-pack-research.md`

**Steps:**
1. Read the three files.
2. Verify these phrases/ideas exist:
   - `repo-first agent-neutral skill pack`
   - `多写 prompt，少写脚本`
   - `~/plotloom.toml`
   - `Dreamina CLI` / `即梦 CLI`
   - `Codex imagegen`
   - `ffmpeg / ffprobe`
3. If any are missing, stop and update design before implementation.

**Verification:**

```bash
grep -R "repo-first agent-neutral skill pack\|多写 prompt\|~/plotloom.toml\|Dreamina\|Codex imagegen\|ffmpeg" docs/prd docs/design docs/research
```

Expected: all concepts appear in docs.

---

## Phase 1: Core Skill Pack Skeleton

### Task 1.1: Create the skill directories only

**Objective:** Add the empty directory shape for the six core skills.

**Files:**
- Create directories under `skills/`:
  - `skills/plotloom-series-brainstorming/`
  - `skills/plotloom-episode-card/`
  - `skills/plotloom-shot-prompts/`
  - `skills/plotloom-asset-selection/`
  - `skills/plotloom-video-adapter/`
  - `skills/plotloom-stitch-deliver/`

**Steps:**
1. Create directories and subdirectories listed below.
2. Add `.gitkeep` only where a directory would otherwise be empty.

```text
skills/
  plotloom-series-brainstorming/templates/
  plotloom-episode-card/templates/
  plotloom-shot-prompts/references/
  plotloom-shot-prompts/templates/
  plotloom-asset-selection/references/
  plotloom-video-adapter/references/
  plotloom-video-adapter/templates/
  plotloom-stitch-deliver/references/
```

**Verification:**

```bash
find skills -maxdepth 3 -type d | sort
```

Expected: all six skill directories and their reference/template directories exist.

**Commit:**

```bash
git add skills
git commit -m "chore: add Plotloom skill pack skeleton"
```

---

### Task 1.2: Write `plotloom-series-brainstorming/SKILL.md`

**Objective:** Define how an agent turns an idea into series-level context without generating video.

**Files:**
- Create: `skills/plotloom-series-brainstorming/SKILL.md`

**Prompt Contract:**

This skill should instruct the agent to:

1. Detect whether the current directory or parent is already a series repo.
2. If no repo exists, inspect `~/plotloom.toml` and decide whether to create or continue a repo.
3. When creating a new series repo, write only:
   - `series.md`
   - `characters.md`
   - baseline directory structure
   - registry entry in `~/plotloom.toml`
4. Design enough long-form series context so episode 1 is not a one-off skit:
   - premise
   - target audience/tone
   - recurring conflict engine
   - core cast
   - season arc outline with user-defined episode count
   - first three episodes enough to judge the opening arc
5. Stop before image/video generation.

**Required SKILL.md shape:**

```markdown
---
name: plotloom-series-brainstorming
description: >-
  Creates or updates a Plotloom short-drama series bible and core character context.
  Use when starting a new short drama, continuing from an idea, creating a series repo,
  or when `series.md` / `characters.md` are missing.
---

# Plotloom Series Brainstorming

## When to Use
## Inputs
## Outputs
## Workflow
## Series Brainstorming Writing Rules
## Stop Conditions
## Next Skill Handoff
## Failure Modes
```

**Important:** This is mostly prompt/instruction. Do not embed Python.

**Verification:**

```bash
grep -n "When to Use\|Inputs\|Outputs\|Stop Conditions\|Next Skill" skills/plotloom-series-brainstorming/SKILL.md
```

Expected: all sections present.

**Commit:**

```bash
git add skills/plotloom-series-brainstorming/SKILL.md
git commit -m "feat: add Plotloom series brainstorming skill"
```

---

### Task 1.3: Write series templates

**Objective:** Add human-readable Markdown templates used by the series brainstorming skill.

**Files:**
- Create: `skills/plotloom-series-brainstorming/templates/series.md`
- Create: `skills/plotloom-series-brainstorming/templates/characters.md`

**Template Requirements:**

`series.md` should include sections:

```markdown
# {{title}}

## Premise
## Target Audience / Tone
## Series Engine
## World Rules
## Season Shape
## Episode Arc Overview
## First Three Episodes
## Visual Direction
## Open Questions
```

`characters.md` should include sections:

```markdown
# Characters

## Core Cast
### {{character_name}}
- Role:
- Desire:
- Secret / Contradiction:
- Visual Identity:
- Voice / Dialogue Style:
- Required Asset:
  - `assets/cast/{{character_slug}}/character-grid.png`

## Supporting Cast
## Relationship Web
```

**Verification:**

```bash
grep -n "Series Engine\|First Three Episodes" skills/plotloom-series-brainstorming/templates/series.md
grep -n "Required Asset\|character-grid.png" skills/plotloom-series-brainstorming/templates/characters.md
```

**Commit:**

```bash
git add skills/plotloom-series-brainstorming/templates
git commit -m "feat: add Plotloom series bible templates"
```

---

### Task 1.4: Write `plotloom-episode-card/SKILL.md`

**Objective:** Define optional episode intent anchoring without forcing a heavy script/storyboard stack.

**Files:**
- Create: `skills/plotloom-episode-card/SKILL.md`
- Create: `skills/plotloom-episode-card/templates/episode-card.md`

**Prompt Contract:**

The skill should:

1. Read `series.md` and `characters.md`.
2. Create or update `episodes/epXXX/episode-card.md` only when story intent needs anchoring.
3. Keep it lean:
   - logline
   - emotional hook
   - main conflict
   - reversal
   - ending hook
   - required characters/assets
4. Avoid mandatory `script.md`, `storyboard.md`, `review.md`, `director-brief.md`.
5. Hand off to `plotloom-shot-prompts`.

**Verification:**

```bash
grep -n "script.md\|storyboard.md\|director-brief" skills/plotloom-episode-card/SKILL.md
```

Expected: these appear only as explicit non-goals.

**Commit:**

```bash
git add skills/plotloom-episode-card
git commit -m "feat: add Plotloom episode card skill"
```

---

### Task 1.5: Write `plotloom-shot-prompts/SKILL.md`

**Objective:** Define the core prompt-production skill: episode intent -> continuous video prompt tasks.

**Files:**
- Create: `skills/plotloom-shot-prompts/SKILL.md`
- Create: `skills/plotloom-shot-prompts/references/visual-continuity.md`
- Create: `skills/plotloom-shot-prompts/templates/video-prompts.md`
- Create: `skills/plotloom-shot-prompts/templates/video-prompts-en.md`

**Prompt Contract:**

The skill should:

1. Read:
   - `series.md`
   - `characters.md`
   - optional `episodes/epXXX/episode-card.md`
   - existing character grids
2. Write:
   - `episodes/epXXX/video-prompts.md`
   - `episodes/epXXX/video-prompts-en.md` only when adapter/model needs English
3. For Seedance/Dreamina-style models, write continuous narrative prompt tasks, not mechanical shot lists.
4. Default video task shape:
   - task id: `clip-01`
   - duration hint: `15-20s` when backend supports it
   - reference images and their purpose
   - cinematic timeline beats
   - character continuity rules
   - camera motion
   - dialogue windows if needed
   - ending frame / handoff point
5. Stop before calling a model.

**Reference content:**

`visual-continuity.md` should cover:

- how to use `character-grid.png`
- how to preserve outfit/face/age/style
- how to describe entrance/exit/occlusion
- how to avoid conflicting camera instructions
- how to write rerun notes after failed candidates

**Verification:**

```bash
grep -n "continuous\|Seedance\|character-grid\|clip-01" skills/plotloom-shot-prompts/SKILL.md skills/plotloom-shot-prompts/references/visual-continuity.md
```

**Commit:**

```bash
git add skills/plotloom-shot-prompts
git commit -m "feat: add Plotloom video prompt skill"
```

---

### Task 1.6: Write `plotloom-asset-selection/SKILL.md`

**Objective:** Define candidate review, accept/reroll, and selected-copy semantics as prompt-first behavior.

**Files:**
- Create: `skills/plotloom-asset-selection/SKILL.md`
- Create: `skills/plotloom-asset-selection/references/selection-rubric.md`

**Prompt Contract:**

The skill should:

1. Evaluate image/video candidates against intent.
2. Ask the user for accept / reroll / revise prompt when needed.
3. If accepted, instruct the deterministic helper to copy candidate to `selected.*`.
4. Explain backup semantics:
   - preserve `candidates/vNNN.*`
   - backup old selected to `selected-prev-YYYYMMDD-HHMMSS.*`
5. For video, process one candidate at a time.
6. Do not choose silently when quality is ambiguous.

**Rubric:**

`selection-rubric.md` should include:

- character consistency
- visual continuity
- short-drama clarity
- hook strength
- model artifacts
- whether rerun should change prompt or just retry same prompt

**Verification:**

```bash
grep -n "selected-prev\|reroll\|one candidate" skills/plotloom-asset-selection/SKILL.md skills/plotloom-asset-selection/references/selection-rubric.md
```

**Commit:**

```bash
git add skills/plotloom-asset-selection
git commit -m "feat: add Plotloom asset selection skill"
```

---

### Task 1.7: Write `plotloom-video-adapter/SKILL.md`

**Objective:** Define model/tool submission behavior without binding Plotloom core to Dreamina.

**Files:**
- Create: `skills/plotloom-video-adapter/SKILL.md`
- Create: `skills/plotloom-video-adapter/references/dreamina-cli.md`
- Create: `skills/plotloom-video-adapter/templates/adapter-request.md`

**Prompt Contract:**

The skill should:

1. Read `video-prompts.md` / `video-prompts-en.md`.
2. Choose fake adapter by default for contract tests.
3. Use Dreamina only when explicitly running real generation and preflight passes.
4. Submit one candidate at a time.
5. Save outputs to `episodes/epXXX/videos/clip-YY/candidates/vNNN.mp4`.
6. If queueing, preserve the `submit_id` in a human-readable note near the clip folder, not a hidden runtime DB.

**Dreamina reference must include verified facts:**

```text
preflight: dreamina user_credit
requires: vip_level = maestro
submit: dreamina text2video ...
query: dreamina query_result --submit_id=...
download: dreamina query_result --submit_id=... --download_dir=...
failure: not logged in / not maestro / queueing / generation failed
```

**Important:** Do not write a full Python client here. This is a prompt and command contract.

**Verification:**

```bash
grep -n "maestro\|user_credit\|query_result\|fake adapter" skills/plotloom-video-adapter/SKILL.md skills/plotloom-video-adapter/references/dreamina-cli.md
```

**Commit:**

```bash
git add skills/plotloom-video-adapter
git commit -m "feat: add Plotloom video adapter skill"
```

---

### Task 1.8: Write `plotloom-stitch-deliver/SKILL.md`

**Objective:** Define final assembly and delivery flow.

**Files:**
- Create: `skills/plotloom-stitch-deliver/SKILL.md`
- Create: `skills/plotloom-stitch-deliver/references/ffmpeg.md`

**Prompt Contract:**

The skill should:

1. Find `selected.mp4` clips under `episodes/epXXX/videos/clip-*/`.
2. Stop if any required selected clip is missing.
3. Use ffprobe helper to inspect media compatibility.
4. Use ffmpeg helper to stitch or normalize + stitch.
5. Save `episodes/epXXX/videos/final.mp4`.
6. Verify the final file exists and is playable/probeable.
7. Deliver via nova-lark / lark-cli when requested.
8. Keep Feishu as delivery, not state center.

**Verification:**

```bash
grep -n "selected.mp4\|final.mp4\|ffprobe\|nova-lark" skills/plotloom-stitch-deliver/SKILL.md skills/plotloom-stitch-deliver/references/ffmpeg.md
```

**Commit:**

```bash
git add skills/plotloom-stitch-deliver
git commit -m "feat: add Plotloom stitch and delivery skill"
```

---

## Phase 2: Series Repo Template

### Task 2.1: Create the series repo template

**Objective:** Add the minimal template used by new Plotloom series repos.

**Files:**
- Create: `templates/series-repo/plotloom.toml`
- Create: `templates/series-repo/series.md`
- Create: `templates/series-repo/characters.md`
- Create directories:
  - `templates/series-repo/assets/cast/`
  - `templates/series-repo/assets/scenes/`
  - `templates/series-repo/episodes/ep001/images/covers/candidates/`
  - `templates/series-repo/episodes/ep001/videos/`
  - `templates/series-repo/outputs/`

**Template TOML:**

```toml
slug = "{{slug}}"
title = "{{title}}"
status = "active"
created_by = "plotloom"
```

**Verification:**

```bash
find templates/series-repo -maxdepth 5 -type d -o -type f | sort
```

**Commit:**

```bash
git add templates/series-repo
git commit -m "feat: add Plotloom series repo template"
```

---

### Task 2.2: Add tiny example series source files

**Objective:** Provide a minimal fixture for agent testing without real model calls.

**Files:**
- Create: `examples/tiny-series/series.md`
- Create: `examples/tiny-series/characters.md`
- Create: `examples/tiny-series/episodes/ep001/episode-card.md`
- Create: `examples/tiny-series/episodes/ep001/video-prompts.md`
- Create: `examples/tiny-series/episodes/ep001/video-prompts-en.md`

**Content Requirements:**

Use a tiny fictional series, e.g. `fake-heiress-reboot`, but keep it short.

The example should be good enough to test:

- repo discovery
- prompt generation style
- fake adapter output placement
- selected copy
- stitch dry-run

**Verification:**

```bash
grep -R "clip-01\|character-grid\|final.mp4" examples/tiny-series
```

**Commit:**

```bash
git add examples/tiny-series
git commit -m "test: add tiny Plotloom series fixture"
```

---

## Phase 3: Minimal Deterministic Helpers

> This phase must stay small. If a proposed helper starts containing creative judgment, move that logic back into `SKILL.md` or references.

### Task 3.1: Add `scripts/init_series.py`

**Objective:** Create a series repo from `templates/series-repo/` and update `~/plotloom.toml`.

**Files:**
- Create: `scripts/init_series.py`

**Allowed Behavior:**

- Accept `--slug`, `--title`, `--path`.
- Copy template files/directories.
- Replace `{{slug}}` and `{{title}}` in template text files.
- Create or update `~/plotloom.toml` with one `[[repos]]` entry.
- Refuse to overwrite an existing non-empty target unless `--force` is passed.

**Not Allowed:**

- Generate story content.
- Infer episode plan.
- Generate images/videos.
- Store workflow state.

**Verification:**

```bash
python scripts/init_series.py --slug test-series --title "Test Series" --path /tmp/plotloom-test-series
python - <<'PY'
from pathlib import Path
p = Path('/tmp/plotloom-test-series')
assert (p/'series.md').exists()
assert (p/'characters.md').exists()
assert (p/'episodes/ep001/videos').exists()
print('ok')
PY
```

**Commit:**

```bash
git add scripts/init_series.py
git commit -m "feat: add minimal series init helper"
```

---

### Task 3.2: Add `scripts/select_candidate.py`

**Objective:** Deterministically copy accepted candidate to `selected.*` with backup.

**Files:**
- Create: `scripts/select_candidate.py`

**Allowed Behavior:**

- Accept `--candidate path` and `--selected path`.
- Verify candidate exists.
- If selected exists, copy it to `selected-prev-YYYYMMDD-HHMMSS.ext`.
- Copy candidate to selected.
- Print a concise summary.

**Not Allowed:**

- Decide whether a candidate is good.
- Delete candidates.
- Use symlink as default.

**Verification:**

```bash
mkdir -p /tmp/plotloom-select/candidates
echo v1 > /tmp/plotloom-select/candidates/v001.mp4
python scripts/select_candidate.py --candidate /tmp/plotloom-select/candidates/v001.mp4 --selected /tmp/plotloom-select/selected.mp4
test "$(cat /tmp/plotloom-select/selected.mp4)" = "v1"
```

**Commit:**

```bash
git add scripts/select_candidate.py
git commit -m "feat: add selected candidate copy helper"
```

---

### Task 3.3: Add `scripts/validate_repo.py`

**Objective:** Validate that a series repo has the required MVP contract files/directories.

**Files:**
- Create: `scripts/validate_repo.py`

**Allowed Behavior:**

- Accept `--repo path`.
- Check for `series.md`, `characters.md`, `episodes/`.
- For an episode, check `video-prompts.md` when video generation is requested.
- Return non-zero on missing required contract files.
- Print clear missing paths.

**Not Allowed:**

- Validate story quality.
- Modify files.
- Create missing files.

**Verification:**

```bash
python scripts/validate_repo.py --repo examples/tiny-series
```

Expected: pass.

**Commit:**

```bash
git add scripts/validate_repo.py
git commit -m "feat: add Plotloom repo validator"
```

---

### Task 3.4: Add fake video adapter

**Objective:** Provide a deterministic fake adapter that copies a fixture mp4 into the candidate path.

**Files:**
- Create: `scripts/adapters/fake_video.py`
- Create: `examples/fixtures/fake-video.mp4` or document how to generate it with ffmpeg

**Allowed Behavior:**

- Accept `--output path` and optional `--prompt-file path`.
- If fixture exists, copy it to output.
- If fixture does not exist, create a 1-second test video using ffmpeg.
- Print output path.

**Not Allowed:**

- Pretend to be real model generation.
- Make creative decisions.

**Verification:**

```bash
python scripts/adapters/fake_video.py --output /tmp/plotloom-fake/v001.mp4
ffprobe -v error /tmp/plotloom-fake/v001.mp4
```

**Commit:**

```bash
git add scripts/adapters/fake_video.py examples/fixtures
git commit -m "feat: add fake video adapter"
```

---

### Task 3.5: Add ffprobe/ffmpeg stitch helper

**Objective:** Stitch selected clips into `final.mp4` using ffmpeg.

**Files:**
- Create: `scripts/ffprobe_media.py`
- Create: `scripts/stitch_ffmpeg.py`

**Allowed Behavior:**

- Probe video path with ffprobe.
- Accept list of selected clip paths.
- If compatible, concat.
- If incompatible, either normalize to one simple profile or fail with clear message.
- Write `final.mp4`.

**Not Allowed:**

- Make edit decisions.
- Add subtitles/BGM/mixing.
- Hide errors.

**Verification:**

```bash
python scripts/adapters/fake_video.py --output /tmp/plotloom-stitch/clip-01/selected.mp4
python scripts/adapters/fake_video.py --output /tmp/plotloom-stitch/clip-02/selected.mp4
python scripts/stitch_ffmpeg.py --output /tmp/plotloom-stitch/final.mp4 /tmp/plotloom-stitch/clip-01/selected.mp4 /tmp/plotloom-stitch/clip-02/selected.mp4
ffprobe -v error /tmp/plotloom-stitch/final.mp4
```

**Commit:**

```bash
git add scripts/ffprobe_media.py scripts/stitch_ffmpeg.py
git commit -m "feat: add ffmpeg stitch helper"
```

---

## Phase 4: Adapter Docs, Not Runtime

### Task 4.1: Add Codex imagegen adapter doc

**Objective:** Document how Plotloom expects image generation to be invoked without binding core to Codex internals.

**Files:**
- Create: `docs/adapters/codex-app-server.md`

**Content Requirements:**

- preflight expectations
- input files
- output paths
- dry-run behavior
- how character grid should be saved
- failure modes

**Verification:**

```bash
grep -n "character-grid.png\|dry-run\|output path" docs/adapters/codex-app-server.md
```

**Commit:**

```bash
git add docs/adapters/codex-app-server.md
git commit -m "docs: add Codex image adapter notes"
```

---

### Task 4.2: Add Dreamina adapter doc

**Objective:** Document verified Dreamina CLI behavior and MVP constraints.

**Files:**
- Create: `docs/adapters/dreamina-cli.md`

**Content Requirements:**

Include verified facts:

```text
binary: /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina in current environment
preflight: HOME=/Users/wangguiping dreamina user_credit
requires vip_level: maestro
text2video submit returns submit_id
query_result has no --poll flag
query loop must be external
query_result supports --download_dir
```

**Important:** Do not include tokens, device codes, OAuth links, QR contents, or credentials.

**Verification:**

```bash
grep -n "maestro\|query_result\|download_dir\|no --poll" docs/adapters/dreamina-cli.md
```

**Commit:**

```bash
git add docs/adapters/dreamina-cli.md
git commit -m "docs: add Dreamina adapter notes"
```

---

### Task 4.3: Add host adapter notes

**Objective:** Add thin install/use notes for Hermes, Claude Code, Codex, and OpenCode.

**Files:**
- Create: `docs/hosts/hermes.md`
- Create: `docs/hosts/claude-code.md`
- Create: `docs/hosts/opencode.md`

**Content Requirements:**

Each file should explain:

- where that host expects skills
- how to symlink/copy `skills/<name>/`
- what tools are expected
- what not to do: do not duplicate Plotloom business logic

**Verification:**

```bash
grep -R "do not duplicate\|skills/" docs/hosts/hermes.md docs/hosts/claude-code.md docs/hosts/opencode.md
```

**Commit:**

```bash
git add docs/hosts/hermes.md docs/hosts/claude-code.md docs/hosts/opencode.md
git commit -m "docs: add Plotloom host adapter notes"
```

---

## Phase 5: End-to-End Demo Without Real Model Calls

### Task 5.1: Run fake end-to-end flow

**Objective:** Prove the contract works without Codex/Dreamina.

**Steps:**

1. Initialize a temp series repo:

```bash
python scripts/init_series.py --slug fake-heiress-reboot --title "Fake Heiress Reboot" --path /tmp/plotloom-demo/fake-heiress-reboot
```

2. Copy example prompt files into the temp repo.
3. Generate two fake video candidates:

```bash
python scripts/adapters/fake_video.py --output /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/candidates/v001.mp4
python scripts/adapters/fake_video.py --output /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-02/candidates/v001.mp4
```

4. Select both candidates:

```bash
python scripts/select_candidate.py --candidate /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/candidates/v001.mp4 --selected /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/selected.mp4
python scripts/select_candidate.py --candidate /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-02/candidates/v001.mp4 --selected /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-02/selected.mp4
```

5. Stitch final:

```bash
python scripts/stitch_ffmpeg.py --output /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/final.mp4 /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-01/selected.mp4 /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/clip-02/selected.mp4
```

6. Probe final:

```bash
ffprobe -v error /tmp/plotloom-demo/fake-heiress-reboot/episodes/ep001/videos/final.mp4
```

**Expected:** `final.mp4` exists and ffprobe returns success.

**Commit:**

```bash
git add docs/plans/2026-04-29-plotloom-mvp-implementation-plan.zh.md
git commit -m "docs: add Plotloom MVP implementation plan"
```

---

## Phase 6: Real Adapter Smoke Tests

### Task 6.1: Codex imagegen smoke test

**Objective:** Verify the real image adapter can produce one `character-grid.png`.

**Input:**
- `examples/tiny-series/characters.md`

**Output:**
- `/tmp/plotloom-demo/fake-heiress-reboot/assets/cast/<character-slug>/character-grid.png`

**Verification:**

- file exists
- image can be opened/analyzed
- user can visually review it

**Commit:** No code commit required unless adapter docs change.

---

### Task 6.2: Dreamina CLI smoke test

**Objective:** Verify real Dreamina can submit and download one video candidate.

**Preflight:**

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina user_credit
```

Expected:

```text
vip_level: maestro
```

**Submit:**

Use one short prompt from `examples/tiny-series/episodes/ep001/video-prompts-en.md`.

**Query:**

Loop externally with:

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina query_result --submit_id=<id> --download_dir=<clip candidate dir>
```

**Verification:**

- candidate mp4 downloaded to expected path
- ffprobe succeeds

**Commit:** No code commit required unless Dreamina adapter docs change.

---

## Final Acceptance Criteria

MVP implementation is ready when:

1. All six core skills exist and can be loaded as standalone `SKILL.md` directories.
2. `templates/series-repo/` can create a valid series repo.
3. `examples/tiny-series/` exists and documents the happy path.
4. Fake adapter can produce candidate clips.
5. `select_candidate.py` copies candidates to `selected.*` with backup semantics.
6. `stitch_ffmpeg.py` can create a playable `final.mp4` from selected clips.
7. Dreamina real adapter is documented with `maestro` and queue constraints.
8. No runtime, database, queue, dashboard, or workflow state file has been introduced.
9. The implementation remains prompt-first; scripts are small deterministic helpers only.

## Do Not Build Yet

Do not implement these in MVP:

- Web dashboard
- queue/daemon/background worker
- database
- manifest/workflow-state JSON
- model benchmark suite
- automatic commercial viability scoring
- mandatory `script.md`, `storyboard.md`, `director-brief.md`, or `review.md`
- batch video generation of 3 candidates at once

## Handoff

After this plan is implemented, the next agent should run:

```bash
python scripts/validate_repo.py --repo examples/tiny-series
python scripts/adapters/fake_video.py --output /tmp/plotloom-plan-check/v001.mp4
ffprobe -v error /tmp/plotloom-plan-check/v001.mp4
```

Then run the full fake end-to-end flow in Phase 5.
