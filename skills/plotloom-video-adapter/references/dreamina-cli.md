# Dreamina CLI Adapter Reference

## Verified Facts
- preflight: `dreamina user_credit`
- requires: `vip_level = maestro`
- submit: `dreamina text2video ...`
- query: `dreamina query_result --submit_id=...`
- download: `dreamina query_result --submit_id=... --download_dir=...`
- failure modes: not logged in / not maestro / queueing / generation failed
- `query_result` has no `--poll` flag; query loop must be external.
- `query_result` supports `--download_dir`.

## Current Environment Note
In the current Nova/Hermes host, the binary has been observed at:

```text
/Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina
```

Recommended preflight shape in this environment:

```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina user_credit
```

Expected account permission:

```text
vip_level: maestro
```

## Queue Handling
Dreamina may return `gen_status: querying` with `queue_status: Queueing`. Store the `submit_id` in a visible note near the clip folder and poll externally. Do not introduce a runtime DB.

## Security
Never commit tokens, credentials, OAuth links, device codes, QR contents, or credential files. Use `[REDACTED]` when documenting sensitive material.
