---
name: plotloom-video-adapter
description: >-
  Submits Plotloom clip prompts to fake or real video adapters and records candidate outputs. Use when the user asks to
  generate a candidate mp4, run fake adapter, run Dreamina/即梦, submit a clip, poll a queued submit_id, or turn
  `video-prompts.md` / `video-prompts-en.md` into `episodes/epXXX/videos/clip-YY/candidates/vNNN.mp4`.
---

# Plotloom Video Adapter

## When to Use
Use when `episodes/epXXX/video-prompts.md` or `video-prompts-en.md` exists and a clip candidate should be produced or queried.

## Inputs
- `video-prompts.md` / `video-prompts-en.md`
- Target clip id such as `clip-01`
- Adapter choice: fake adapter by default; Dreamina only for explicit real generation.

## Outputs
- `episodes/epXXX/videos/clip-YY/candidates/vNNN.mp4`
- If queueing, a human-readable queue note near the clip folder containing `submit_id`, status, adapter, and next query command.

## Read These Resources When...
- Read `references/fake-adapter.md` for contract tests and no-quota dry runs.
- Read `references/dreamina-cli.md` before any real Dreamina/即梦 submission or polling.
- Use `templates/adapter-request.md` to record preflight, command, status, and handoff.

## Workflow
1. Read the prompt file and target clip id.
2. Choose fake adapter by default for contract tests.
3. Use Dreamina only when explicitly running real generation and preflight passes.
4. Submit one candidate at a time.
5. Save outputs to `episodes/epXXX/videos/clip-YY/candidates/vNNN.mp4`.
6. If the provider queues, preserve `submit_id` in a visible note near the clip folder, not a hidden runtime DB.
7. Hand off to `plotloom-asset-selection` after a candidate exists.

## Adapter Rules
- Fail fast on missing prompt, missing clip id, invalid output path, missing login, missing `maestro`, missing quota, or provider error.
- Fake adapter proves file-path contracts and ffmpeg compatibility; it does not prove creative quality.
- Dreamina requires host pre-authentication. The adapter must not automate OAuth, store credentials, or copy tokens.
- Do not create a Python runtime client in the skill; keep this as a prompt and command contract plus thin deterministic scripts.
- Do not batch-generate three candidates in MVP.

## Stop Conditions
Stop after candidate creation, queue note, or provider failure report. Do not select or stitch.

## Next Skill Handoff
Use `plotloom-asset-selection` to review and accept/reroll the candidate.

## Failure Modes
- Fake adapter failure: check ffmpeg installation and output path.
- Dreamina not logged in: run `dreamina user_credit` manually on the host.
- Dreamina account not `maestro`: stop and report permission gap.
- Queueing: record `submit_id`, status, and query command visibly.
- Generation failed: preserve error and suggest prompt revision only if failure is prompt-related.
