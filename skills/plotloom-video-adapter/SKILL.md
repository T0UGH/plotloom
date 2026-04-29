---
name: plotloom-video-adapter
description: >-
  Submits Plotloom video prompt tasks to fake or real video adapters.
  Use after `video-prompts.md` exists and before asset selection.
---

# Plotloom Video Adapter

## When to Use
Use when `episodes/epXXX/video-prompts.md` or `video-prompts-en.md` exists and a clip candidate should be produced.

## Inputs
- `video-prompts.md` / `video-prompts-en.md`
- Target clip id such as `clip-01`
- Adapter choice: fake adapter by default; Dreamina only for explicit real generation.

## Outputs
- `episodes/epXXX/videos/clip-YY/candidates/vNNN.mp4`
- If queueing, a human-readable note near the clip folder containing `submit_id`, status, adapter, and next query command.

## Workflow
1. Read the prompt file and target clip id.
2. Choose fake adapter by default for contract tests.
3. Use Dreamina only when explicitly running real generation and preflight passes.
4. Submit one candidate at a time.
5. Save outputs to the candidate path.
6. If the provider queues, preserve `submit_id` in a note near the clip folder, not a hidden runtime DB.
7. Hand off to `plotloom-asset-selection` after a candidate exists.

## Adapter Rules
- Fail fast on missing login, missing `maestro`, missing quota, missing prompt, or provider error.
- Do not create a Python runtime client in the skill; keep this as a prompt and command contract.
- Do not batch-generate three candidates in MVP.

## Stop Conditions
Stop after candidate creation or after recording queue status. Do not select or stitch.

## Next Skill Handoff
Use `plotloom-asset-selection` to review and accept/reroll the candidate.

## Failure Modes
- Fake adapter failure: check ffmpeg installation.
- Dreamina not logged in: run `dreamina user_credit` manually on the host.
- Dreamina account not `maestro`: stop and report permission gap.
- Queueing: record `submit_id` and query command.
