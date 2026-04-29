# Dreamina CLI Adapter Reference

## Verified Facts
- preflight: `dreamina user_credit`
- requires: `vip_level = maestro`
- submit: `dreamina text2video ...`
- query: `dreamina query_result --submit_id=...`
- download: `dreamina query_result --submit_id=... --download_dir=...`
- failure modes: not logged in / not maestro / quota insufficient / queueing / generation failed
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

## Submit / Query Skeleton
```bash
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina text2video ...
HOME=/Users/wangguiping /Users/wangguiping/.hermes/profiles/nova/home/.local/bin/dreamina query_result --submit_id=<submit_id> --download_dir=<candidate-dir>
```

## Queue Note Shape
Store a visible Markdown note near the clip folder:

```markdown
# Dreamina Queue Note

- adapter: dreamina-cli
- clip: clip-01
- submit_id: <redacted-if-sharing>
- status: Queueing
- query command: `... query_result --submit_id=... --download_dir=...`
- last checked:
- next action:
```

## Queue Handling
Dreamina may return `gen_status: querying` with `queue_status: Queueing`. Poll externally. Do not introduce a runtime DB, queue worker, or hidden state file.

## Common Interpretations
- not logged in: host must complete manual login first.
- not maestro: account lacks CLI generation permission.
- queueing: preserve submit id and wait/poll.
- generation failed: keep error, then decide whether to revise prompt or retry.

## Security
Never commit tokens, credentials, OAuth links, device codes, QR contents, credential files, or raw account identifiers. Use `[REDACTED]` when documenting sensitive material.
