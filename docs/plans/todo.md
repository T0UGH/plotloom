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
- [x] Enable `asset://asset-...` cloud face assets for Seedance provider payloads with fake/local tests only.
- [x] Strengthen prompt compile into source prompt -> provider compiled prompt -> QA checklist.
- [x] Add video review media evidence: ffprobe, audio check, frame extraction, first/last frame artifacts, and `REVIEW.md`.
- [x] Add receipt audit fields for source prompt hash, cost, queue/provider timing, and selection/rejection reason.
- [x] Add optional repo-configured video continuity artifacts; keep disabled by default.

## Guardrails

- Do not pass local reference files to provider requests until upload or cloud asset semantics are confirmed.
- Do pass `asset://asset-...` cloud assets to Seedance only when they are explicit reference intent URIs or validated cloud face assets.
- Do not mix failure classification with reference or face policy changes.
- Keep `video submit` provider behavior stable unless the change explicitly targets provider integration.
- Do not implement an automatic candidate/gacha loop; generation reruns are expensive and should remain explicit.
- Do not enable first/last-frame continuity by default. It must be gated by repo config because last-frame artifacts can contain unsafe or undesirable face references.

## External Provider Boundary

- VolcEngine cloud face asset IDs should be recorded as `asset://asset-...`.
- Plotloom can submit explicit `asset://asset-...` references to Seedance.
- Plotloom still does not submit local reference files to Seedance.
- Seedance / Dreamina real E2E tests remain manual and opt-in because they cost money.
