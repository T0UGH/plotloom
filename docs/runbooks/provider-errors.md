# Provider Error Taxonomy

> Status: local runbook. This page explains provider errors without calling Seedance, Dreamina, or imagegen.

Use:

```bash
plotloom doctor --explain-error InputImageSensitiveContentDetected.PrivacyInformation
```

## Categories

| category | retryable | likely cause | next step |
| --- | --- | --- | --- |
| `content_rejected` | no | Provider moderation or privacy policy rejected prompt or input image, often realistic human face references. | Use `plotloom face policy` and avoid full visible-face character sheets. Prefer text-only or cloud face asset plus body/wardrobe reference. |
| `rate_limited` | yes | Provider throttled the account or model endpoint. | Resume only failed/pending batch items later. |
| `provider_unreachable` | yes | Timeout, DNS, connection, or temporary provider outage. | Retry failed item only after checking receipt. |
| `auth_error` | no | Missing, expired, or unauthorized credentials. | Run `plotloom doctor --adapter <adapter>` and fix credentials. |
| `request_invalid` | no | Unsupported model, bad parameter, missing input, malformed media, or schema mismatch. | Inspect receipt `provider_request` and fix local intent before retrying. |
| `upload_failed` | usually yes | Media upload or staging failed. | Check file existence, size, permissions, and network path. |
| `filesystem_error` | no | Local permission or path error. | Fix local repo path or permissions before retrying. |
| `provider_error` | unknown | Unclassified provider response. | Preserve receipt and raw error, then classify before rerun. |

## Face-specific guidance

`InputImageSensitiveContentDetected.PrivacyInformation`, `input image may contain real person`, and similar errors should be treated as `content_rejected`.

Do not treat red mesh, facial topology, pixelation, or transparent overlays as reliable privacy bypasses. For VolcEngine / Seedance face workflows, prefer one of the configured face policy strategies:

1. `safe-face-reference`: local sketch-like or masked face reference.
2. `text-only`: prompt description without face image.
3. `cloud-face-asset`: provider cloud face asset plus local body/wardrobe reference.
