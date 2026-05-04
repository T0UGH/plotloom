# Plotloom Reference / Face Policy TODO

## Done

- Slice A: `reference-map.toml` planning and parsing.
- Slice B: `assets/cast/<character>/face-policy.toml` lint with three strategies.
- Slice C: `video submit --reference-map` records reference intent in task receipt without changing provider payloads.

## Next

- [x] Document the current reference map and face policy workflow.
- [x] Add reference map / face policy cross-lint.
- [x] Add prompt lint / compile-prompt checks for reference order, subtitle risk, and shot-list style prompts.
- [x] Add adapter native request summary without changing provider behavior.
- [x] Add failure classification and retryable semantics as a separate change.
- [x] Investigate real VolcEngine Seedance reference payloads for cloud face assets before enabling provider-side reference submission.

## Guardrails

- Do not pass local reference files to provider requests until upload or cloud asset semantics are confirmed.
- Do not mix failure classification with reference or face policy changes.
- Keep `video submit` provider behavior stable unless the change explicitly targets provider integration.

## External Provider Boundary

- VolcEngine cloud face asset IDs should be recorded as `asset://asset-...`.
- Plotloom still does not submit local reference files or cloud face assets to Seedance.
- Seedance / Dreamina real E2E tests remain manual and opt-in because they cost money.
