# OpenCode Host Adapter Notes

## Purpose
Thin notes for using Plotloom skills from OpenCode. Do not duplicate Plotloom business logic in host adapters.

## Expected Skill Location
`~/.config/opencode/skills/` as the recommended user-level skill location; alternatively symlink from the project if your OpenCode install uses a custom skills path.

## Skill Installation
Copy or symlink individual directories from this repo:

```text
skills/<name>/
```

to the host skill directory above. Keep the Plotloom repo `skills/` directory as the source of truth while developing.

## Expected Tools
- Markdown/TOML file editing.
- Shell execution for small deterministic helpers.
- ffmpeg / ffprobe when stitching or fake video tests are needed.
- Optional image/video generation tools configured by the host.

## Rules
- Use `skills/` as the source of truth.
- Keep adapters thin.
- Do not duplicate Plotloom business logic.
- Do not introduce runtime state, queues, dashboards, or databases.
