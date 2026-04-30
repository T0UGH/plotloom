# Plotloom Provider Smoke Runbook

Manual smoke tests are opt-in. Do not run real provider submit or poll from pytest or CI.

## Prerequisites

- `plotloom config init` has created `~/.plotloom/.env.toml`.
- Dreamina CLI is installed, logged in, and available as `dreamina` or configured under `[adapters.dreamina-cli].binary`.
- VolcEngine Ark key is configured as `ARK_API_KEY` or `[adapters.volcengine-seedance].ark_api_key`.
- `ffmpeg` and `ffprobe` are installed for downloaded media verification.
- Use a disposable episode/clip when testing paid providers.

## Doctor

```bash
plotloom doctor --adapter dreamina-cli --deep
plotloom doctor --adapter volcengine-seedance --deep
plotloom config doctor --adapter volcengine-seedance
```

Doctor checks credentials as present or absent only. It must not print actual secrets.

## Dreamina Text-To-Video Smoke

```bash
plotloom --repo /path/to/series video submit \
  --episode ep001 \
  --clip clip-01 \
  --adapter dreamina-cli \
  --mode text-to-video \
  --duration 5 \
  --ratio 9:16 \
  --resolution 720p

plotloom --repo /path/to/series video poll \
  --episode ep001 \
  --clip clip-01
```

Expected paths:

- `episodes/ep001/videos/clip-01/tasks/dreamina-cli-*.toml`
- `episodes/ep001/videos/clip-01/latest-task.toml`
- `episodes/ep001/videos/clip-01/candidates/vNNN.dreamina-cli.mp4`

## VolcEngine Seedance Text-To-Video Smoke

```bash
plotloom --repo /path/to/series video submit \
  --episode ep001 \
  --clip clip-01 \
  --adapter volcengine-seedance \
  --mode text-to-video \
  --duration 5 \
  --ratio 9:16 \
  --resolution 720p

plotloom --repo /path/to/series video poll \
  --episode ep001 \
  --clip clip-01
```

Expected paths:

- `episodes/ep001/videos/clip-01/tasks/volcengine-seedance-*.toml`
- `episodes/ep001/videos/clip-01/latest-task.toml`
- `episodes/ep001/videos/clip-01/candidates/vNNN.volcengine-seedance.mp4`

## Cost Guardrails

- Run doctor first.
- Submit one short clip first; use 5 seconds unless validating a duration-specific bug.
- Do not run batch provider smoke.
- Do not rerun a failed submit until the receipt and provider status are inspected.
- Stop if credentials are missing, quota/credit is low, provider status is unclear, or the receipt lacks a provider task id.

## Failure Stop Conditions

- Provider command or HTTP response includes an auth or quota error.
- `latest-task.toml` is missing or points at a missing receipt.
- A downloaded candidate fails `plotloom media probe`.
- The receipt contains a real secret or full bearer token.
