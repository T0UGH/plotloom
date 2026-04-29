# Plotloom Series Repo Contract

## Repo Markers
A Plotloom series repo is recognized by the presence of several of these:
- `plotloom.toml`
- `series.md`
- `characters.md`
- `episodes/`
- `assets/`

## Home Registry
In Hermes, work often starts from `$HOME`, so `~/plotloom.toml` is the home-level registry. It only lists short-drama repos and does not become runtime state.

Example:

```toml
[[repos]]
slug = "fake-heiress-reboot"
title = "Fake Heiress Reboot"
path = "/Users/example/series/fake-heiress-reboot"
status = "active"
```

## Baseline Tree
```text
series.md
characters.md
plotloom.toml
assets/cast/
assets/scenes/
episodes/ep001/images/covers/candidates/
episodes/ep001/videos/
outputs/
```

## Collision Handling
- If a target repo path exists and is non-empty, stop unless the user explicitly chooses force/continue.
- If `~/plotloom.toml` has multiple plausible repos, ask the user instead of guessing.
- Do not overwrite existing `series.md` or `characters.md` silently.

## Do Not Create in MVP
- Hidden DBs.
- Dashboards.
- Queue/runtime manifests.
- Mandatory `script.md`, `storyboard.md`, `director-brief.md`, or `review.md`.
- Feishu as state center.
