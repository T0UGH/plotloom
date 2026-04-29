# Dreamina CLI Adapter Notes

## Purpose
Document verified Dreamina CLI behavior for Plotloom. This is an adapter contract, not a runtime client.

## Verified Facts
- binary in current environment: `/Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina`
- preflight: `HOME=/Users/wangguiping dreamina user_credit`
- requires `vip_level: maestro`
- `text2video` submit returns `submit_id`
- `query_result` has no `--poll` flag
- query loop must be external
- `query_result` supports `--download_dir`

## Commands

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina user_credit
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina text2video ...
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina query_result --submit_id=<id> --download_dir=<candidate-dir>
```

## Queue Handling
If `queue_status` is `Queueing`, store `submit_id` and the query command in a visible note near the clip folder. Do not create a hidden workflow DB.

## Security
Do not include tokens, device codes, OAuth links, QR contents, credential files, or credential values. Redact sensitive identifiers as `[REDACTED]`.
