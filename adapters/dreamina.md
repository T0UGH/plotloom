# Dreamina CLI Adapter Notes

## Purpose

Document verified Dreamina CLI behavior for Plotloom. This is an adapter contract, not a runtime client.

Recommended adapter name for Plotloom: `dreamina-cli`.

## Verified Facts

- binary in current environment: `/Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina`
- preflight: `HOME=/Users/wangguiping dreamina user_credit`
- requires `vip_level: maestro`
- `text2video` submit returns `submit_id`
- `image2video` uploads one local first-frame image and returns `submit_id`
- `query_result` has no `--poll` flag
- query loop must be external
- `query_result` supports `--download_dir`

## Preflight

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina user_credit
```

Pass condition:

- CLI exists
- account is logged in
- `vip_level: maestro`

Do not auto-login from Plotloom. Login is a host setup step.

## Text-to-video submit

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina text2video \
  --prompt="<plain prompt>" \
  --duration=15 \
  --ratio=9:16 \
  --video_resolution=720p \
  --model_version=seedance2.0fast \
  --poll=0
```

Supported values observed from CLI help:

- `duration`: Seedance 2.0 family supports 4-15s; default is 5, so Plotloom must pass it explicitly.
- `ratio`: `1:1`, `3:4`, `16:9`, `4:3`, `9:16`, `21:9`.
- `video_resolution`: Seedance 2.0 family supports `720p`.
- `model_version`: `seedance2.0`, `seedance2.0fast`, `seedance2.0_vip`, `seedance2.0fast_vip`.

## Image-to-video submit

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina image2video \
  --image=./first-frame.png \
  --prompt="<plain prompt>" \
  --duration=15 \
  --video_resolution=720p \
  --model_version=seedance2.0fast \
  --poll=0
```

`image2video` infers ratio from the input image, so Plotloom should prepare/crop first-frame images to the target aspect ratio before submitting.

## Poll / download

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina query_result \
  --submit_id=<id> \
  --download_dir=<candidate-dir>
```

If `queue_status` is `Queueing`, store `submit_id` and the query command in a visible task receipt near the clip folder. Do not create a hidden workflow DB.

On success, normalize/rename downloaded media to `candidates/vNNN.dreamina-cli.mp4`, then run ffprobe.

## Security

Do not include tokens, device codes, OAuth links, QR contents, credential files, or credential values. Redact sensitive identifiers as `[REDACTED]`.
