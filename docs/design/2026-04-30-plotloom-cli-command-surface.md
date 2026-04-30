# Plotloom CLI Command Surface

> 日期：2026-04-30  
> 状态：Draft v0.1  
> 目的：给 Plotloom CLI 定一套完整、稳定、agent-friendly 的命令面。本文只定义命令形态和行为边界，不是实现计划。  
> Source of truth:
> - `docs/design/2026-04-30-plotloom-cli-technical-design.md`
> - `docs/design/2026-04-30-plotloom-cli-contract-details.md`

## 1. Command Shape

Plotloom CLI 是 repo-first 的确定性执行层。命令必须适合 agent 非交互调用，不能依赖 TUI、prompt 选择或隐藏状态。

通用形态：

```bash
plotloom [GLOBAL_OPTIONS] <command> [COMMAND_OPTIONS]
```

Global options:

```bash
--repo PATH              # 指定 series repo；未指定时按 discovery 规则查找
--config PATH            # 默认 ~/.plotloom/.env.toml
--json                   # stdout 输出机器可读 JSON；不落持久 JSON 文件
--quiet                  # 只输出关键路径/状态
--dry-run                # 展示会执行什么，不调用外部 provider，不写重媒体
--version
--help
```

Repo discovery 顺序：

1. `--repo PATH`
2. 当前目录向上查找 `series.md`
3. 读取 `registry_path`，默认 `~/plotloom.toml`
4. 多个 active repo 或无法唯一判断时，列候选并返回非零
5. registry path 失效时不自动重建

输出规则：

- 默认 stdout 给人和 agent 看，短文本 + 关键路径。
- `--json` 只用于 stdout，不作为 first-party artifact。
- secrets 只显示 `present/absent`，不显示值、前后缀、token、OAuth code、QR 内容。
- mutating command 成功后必须输出主产物路径，例如 repo path、candidate path、receipt path、selected path、final path。

Exit codes:

```text
0 success
1 user/input error
2 local dependency/config missing
3 provider/adapter task failed
4 media validation failed
```

## 2. Config Commands

User-level config 放在 `~/.plotloom/.env.toml`。它只保存本机 provider 配置和 secret，不承载 series repo 状态。

```bash
plotloom config path
plotloom config init [--force] [--print-template]
plotloom config doctor [--adapter codex-app-server|dreamina-cli|happyhorse-fal|volcengine-seedance|all]
```

Behavior:

- `config path` 打印当前会读取的 config 路径。
- `config init` 创建 `~/.plotloom/.env.toml`，权限 `0600`；默认不覆盖。
- `config doctor` 检查 TOML 可解析、权限合理、依赖是否可用、key 是否 present。
- MVP 不提供 `config set`，避免 secret 进入 shell history；用户手动编辑 TOML。

Template:

```toml
[plotloom]
repos_root = "~/plotloom_repo"
registry_path = "~/plotloom.toml"
default_image_adapter = "codex-app-server"
default_video_adapters = ["dreamina-cli", "happyhorse-fal", "volcengine-seedance"]

[adapters.codex-app-server]
enabled = true
codex_binary = "codex"
app_server_url = ""

[adapters.dreamina-cli]
enabled = true
binary = "dreamina"
home = "~"

[adapters.happyhorse-fal]
enabled = true
fal_key = ""
default_resolution = "720p"

[adapters.volcengine-seedance]
enabled = true
ark_api_key = ""
base_url = "https://ark.cn-beijing.volces.com/api/v3"
model = "doubao-seedance-2-0-260128"
default_resolution = "720p"
```

## 3. Repo Commands

Repo commands 管 `~/plotloom.toml` 和 series repo 基础结构，不做创作判断。

```bash
plotloom init <slug> --title TEXT [--path PATH] [--no-registry]
plotloom repos list [--status active|paused|archived|all]
plotloom repos add <slug> --title TEXT --path PATH [--status active|paused|archived]
plotloom repos set-status <slug> active|paused|archived
plotloom repos remove <slug>
plotloom repos resolve [<slug>]
plotloom validate [--episode ep001] [--require-prompts] [--require-media]
plotloom doctor [--adapter all|codex-app-server|dreamina-cli|happyhorse-fal|volcengine-seedance] [--deep]
```

Design notes:

- `init` 只需要 slug/title/path，不生成剧情内容。
- `--path` 默认是 `repos_root/<slug>`。
- `repos remove` 只移除 registry entry，不删除真实目录。CLI 不提供隐式删目录能力。
- `validate` 检查 Plotloom contract：`series.md`、`characters.md`、`episodes/`、episode prompt/media 是否存在。
- `doctor` 检查本机依赖：config、Codex、Dreamina、fal、Ark SDK、ffmpeg/ffprobe。

Examples:

```bash
plotloom init fake-heiress --title "Fake Heiress Reboot"
plotloom repos list --status active
plotloom validate --repo ~/plotloom_repo/fake-heiress --episode ep001 --require-prompts
plotloom doctor --adapter all
```

## 4. Prompt Commands

Prompt commands 是调试和可视化接口。真实 `video submit` 必须内部执行 provider-aware prompt compile，不能把完整 Markdown artifact 原样提交给 provider。

```bash
plotloom prompt list --episode ep001
plotloom prompt check --episode ep001 [--clip clip-01] [--adapter ADAPTER] [--mode MODE]
plotloom prompt extract --episode ep001 --clip clip-01 [--field prompt-string]
plotloom prompt compile --episode ep001 --clip clip-01 --adapter ADAPTER --mode MODE [--output PATH]
```

Modes:

```text
text-to-video
image-to-video
reference-to-video
video-edit
```

Behavior:

- `prompt list` 列出 `video-prompts-en.md` 中可识别的 clips。
- `prompt check` 校验 clip 存在、duration/ratio/reference hints 合理、provider 限制是否满足。
- `prompt extract` 输出 provider-neutral 的纯 prompt。
- `prompt compile` 输出 provider-specific prompt，例如 HappyHorse Ref2V 的 `character1` 语义或 VolcEngine `content[]` 角色说明。
- 默认输出 stdout；只有显式 `--output` 才写临时文件。

Examples:

```bash
plotloom prompt check --episode ep001 --clip clip-01 --adapter happyhorse-fal --mode reference-to-video
plotloom prompt compile --episode ep001 --clip clip-01 --adapter volcengine-seedance --mode text-to-video
```

## 5. Image Commands

Image MVP 是 sync-first。Codex image adapter 依赖本机 Codex install/auth 和内置 `image_generation` 能力。MVP 实现可以移植 `T0UGH/agent-skills/codex-imagegen2-api` 的本地 JSON API 模式：prompt + optional images -> generated image path / `file://` URL。

```bash
plotloom image generate --kind cast --character SLUG --prompt-file PATH [--adapter codex-app-server] [--image PATH ...]
plotloom image generate --kind scene --scene SLUG --prompt-file PATH [--adapter codex-app-server] [--image PATH ...]
plotloom image generate --kind cover --episode ep001 --prompt-file PATH [--adapter codex-app-server] [--image PATH ...]
plotloom image generate --kind reference --episode ep001 --clip clip-01 --prompt-file PATH [--adapter codex-app-server] [--image PATH ...]
plotloom image list --kind cast|scene|cover|reference [--episode ep001] [--clip clip-01]
plotloom image info PATH
```

Output paths:

```text
cast      -> assets/cast/<character>/character-grid.png
scene     -> assets/scenes/<scene>/candidates/vNNN.png
cover     -> episodes/ep001/images/covers/candidates/vNNN.png
reference -> episodes/ep001/images/references/clip-01/candidates/vNNN.png
```

Rules:

- `cast` writes current effective `character-grid.png`; old grid is backed up.
- `scene` / `cover` / `reference` write numbered candidates.
- CLI does not judge quality. It only creates/imports/lists/probes/selects.
- No `image submit/poll` in MVP.

Examples:

```bash
plotloom image generate --kind cast --character lin-qiao --prompt-file /tmp/lin-qiao-grid.txt
plotloom image generate --kind cover --episode ep001 --prompt-file /tmp/ep001-cover.txt
plotloom image info episodes/ep001/images/covers/candidates/v001.png
```

## 6. Asset And Selection Commands

Asset commands handle local files and explicit acceptance semantics. `plotloom select` is the canonical acceptance command for image and video candidates.

```bash
plotloom asset import --kind cast --character SLUG --file PATH --as character-grid
plotloom asset import --kind scene --scene SLUG --file PATH --candidate
plotloom asset import --kind cover --episode ep001 --file PATH --candidate
plotloom asset import --kind reference --episode ep001 --clip clip-01 --file PATH --candidate
plotloom asset list --kind cast|scene|cover|reference [--episode ep001] [--clip clip-01]
plotloom asset info PATH

plotloom select PATH
```

Selection behavior:

```text
candidate path: .../candidates/v001.ext
selected path:  sibling selected.ext
backup path:    selected-prev-YYYYMMDD-HHMMSSffffff.ext
```

Rules:

- Always copy, never symlink by default.
- Preserve original candidate.
- If selected exists, back it up before overwrite.
- MVP does not accept remote URLs for `select`; download/import first.

Examples:

```bash
plotloom asset import --kind scene --scene boardroom --file /tmp/boardroom.png --candidate
plotloom select episodes/ep001/images/covers/candidates/v001.png
plotloom select episodes/ep001/videos/clip-01/candidates/v001.dreamina-cli.mp4
```

## 7. Video Commands

Video is async-first. `submit` writes a visible receipt; `poll` updates it and downloads/copies the candidate on success.

```bash
plotloom video submit --episode ep001 --clip clip-01 --adapter mock [COMMON_VIDEO_OPTIONS]
plotloom video submit --episode ep001 --clip clip-01 --adapter dreamina-cli --mode MODE [COMMON_VIDEO_OPTIONS]
plotloom video submit --episode ep001 --clip clip-01 --adapter happyhorse-fal --mode MODE [COMMON_VIDEO_OPTIONS]
plotloom video submit --episode ep001 --clip clip-01 --adapter volcengine-seedance --mode MODE [COMMON_VIDEO_OPTIONS]

plotloom video poll --receipt PATH [--download-dir PATH] [--no-download]
plotloom video poll --episode ep001 --clip clip-01 [--adapter ADAPTER] [--latest]
plotloom video poll --task-id ID --adapter ADAPTER [--download-dir PATH]
plotloom video poll --receipt PATH --watch [--interval 20] [--max-wait 900]

plotloom video list [--episode ep001] [--clip clip-01] [--adapter ADAPTER] [--status queued|running|succeeded|failed|expired|cancelled|all]
plotloom video cancel --receipt PATH
plotloom video cancel --task-id ID --adapter ADAPTER
plotloom video check-clip PATH
plotloom video compare --episode ep001 --clip clip-01 [--adapters all] [--output PATH]
```

Common video options:

```bash
--mode text-to-video|image-to-video|reference-to-video|video-edit
--prompt-file PATH              # default episodes/<ep>/video-prompts-en.md
--duration N
--ratio 9:16|16:9|1:1|4:3|3:4|21:9|adaptive
--resolution 720p|1080p
--audio none|native-if-supported|require-native
--seed N
--first-frame PATH
--reference-image PATH          # repeatable
--reference-video PATH          # repeatable
--source-video PATH             # for video-edit
--allow-downgrade
--allow-normalize-duration
--dry-run
```

Receipt paths:

```text
episodes/ep001/videos/clip-01/tasks/dreamina-cli-<submit-id>.toml
episodes/ep001/videos/clip-01/tasks/happyhorse-fal-<request-id>.toml
episodes/ep001/videos/clip-01/tasks/volcengine-seedance-<task-id>.toml
episodes/ep001/videos/clip-01/latest-task.toml
```

Candidate paths:

```text
episodes/ep001/videos/clip-01/candidates/v001.dreamina-cli.mp4
episodes/ep001/videos/clip-01/candidates/v002.happyhorse-fal.mp4
episodes/ep001/videos/clip-01/candidates/v003.volcengine-seedance.mp4
```

Rules:

- `submit` internally runs provider-aware prompt compile/check.
- Adapter validates capability before submit; no silent duration/resolution downgrade unless explicitly allowed.
- Default `poll` is one-shot. `--watch` is explicit and bounded by `--max-wait`.
- On success, `poll` downloads provider URL immediately and runs ffprobe.
- `compare` reads receipts/candidates and prints a same-prompt comparison summary; default stdout, optional explicit output.

Examples:

```bash
plotloom video submit --episode ep001 --clip clip-01 --adapter dreamina-cli --mode text-to-video --duration 15 --ratio 9:16 --resolution 720p
plotloom video submit --episode ep001 --clip clip-01 --adapter happyhorse-fal --mode reference-to-video --reference-image assets/cast/lin-qiao/character-grid.png
plotloom video submit --episode ep001 --clip clip-01 --adapter volcengine-seedance --mode image-to-video --first-frame episodes/ep001/images/references/clip-01/selected.png
plotloom video poll --episode ep001 --clip clip-01 --latest
plotloom video compare --episode ep001 --clip clip-01
```

## 8. Media Commands

Media commands are deterministic local helpers around ffprobe/ffmpeg and local file validation.

```bash
plotloom media probe PATH
plotloom media check PATH [--expect-video] [--expect-audio] [--ratio 9:16] [--resolution 720p]
plotloom media normalize INPUT --output PATH [--ratio 9:16] [--resolution 720p] [--fps 24] [--audio stereo|silent]
```

Rules:

- `probe` prints concise facts: duration, streams, codec, resolution, fps, audio presence.
- `check` returns nonzero if facts do not match expectations.
- `normalize` is explicit; no silent media changes.

Examples:

```bash
plotloom media probe episodes/ep001/videos/clip-01/selected.mp4
plotloom media check episodes/ep001/videos/clip-01/selected.mp4 --expect-video --ratio 9:16
```

## 9. Stitch Commands

Stitch commands assemble accepted selected clips into the episode final video.

```bash
plotloom stitch --episode ep001 [--output PATH]
plotloom stitch --episode ep001 --clips clip-01,clip-02 [--output PATH]
plotloom stitch --episode ep001 --normalize [--resolution 720p] [--fps 24]
plotloom stitch plan --episode ep001
```

Default behavior:

- Discover `episodes/<ep>/videos/clip-*/selected.mp4` in lexical order.
- Strictly check compatibility before stitching.
- Write `episodes/<ep>/videos/final.mp4` unless `--output` is provided.
- Run ffprobe on final output.

`--normalize` behavior:

- Explicitly normalizes selected clips before concat.
- Normalized intermediates should be temporary unless user gives an output directory.
- If normalization may visibly alter media, fail with a clear reason unless explicitly requested.

Examples:

```bash
plotloom stitch --episode ep001
plotloom stitch --episode ep001 --clips clip-01,clip-02 --normalize
plotloom media probe episodes/ep001/videos/final.mp4
```

## 10. Delivery Commands

Delivery stays outside core state. CLI can summarize local files for Feishu/Lark or another agent, but it does not send messages itself in MVP.

```bash
plotloom delivery summary --episode ep001 [--include-candidates] [--output PATH]
plotloom delivery files --episode ep001
```

Rules:

- Default output is stdout.
- `--output` must be explicit; recommended path is `/tmp/...`, not series repo.
- No persistent `manifest.json`, `workflow-state.json`, or hidden package state.
- Feishu/Lark sending remains an adapter/agent responsibility.

Examples:

```bash
plotloom delivery summary --episode ep001
plotloom delivery files --episode ep001 --json
```

## 11. Full Happy Path

From zero repo to first final video:

```bash
plotloom config init
plotloom config doctor

plotloom init fake-heiress --title "Fake Heiress Reboot"
plotloom validate --repo ~/plotloom_repo/fake-heiress

plotloom image generate --repo ~/plotloom_repo/fake-heiress --kind cast --character lin-qiao --prompt-file /tmp/lin-qiao-grid.txt
plotloom image generate --repo ~/plotloom_repo/fake-heiress --kind cover --episode ep001 --prompt-file /tmp/ep001-cover.txt
plotloom select ~/plotloom_repo/fake-heiress/episodes/ep001/images/covers/candidates/v001.png

plotloom prompt check --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01 --adapter dreamina-cli --mode text-to-video

plotloom video submit --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01 --adapter dreamina-cli --mode text-to-video --duration 15 --ratio 9:16 --resolution 720p
plotloom video submit --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01 --adapter happyhorse-fal --mode text-to-video --duration 15 --ratio 9:16 --resolution 720p
plotloom video submit --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01 --adapter volcengine-seedance --mode text-to-video --duration 15 --ratio 9:16 --resolution 720p

plotloom video poll --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01 --latest
plotloom video compare --repo ~/plotloom_repo/fake-heiress --episode ep001 --clip clip-01
plotloom select ~/plotloom_repo/fake-heiress/episodes/ep001/videos/clip-01/candidates/v001.dreamina-cli.mp4

plotloom stitch --repo ~/plotloom_repo/fake-heiress --episode ep001
plotloom media probe ~/plotloom_repo/fake-heiress/episodes/ep001/videos/final.mp4
plotloom delivery summary --repo ~/plotloom_repo/fake-heiress --episode ep001
```

## 12. Commands Intentionally Not In MVP

These names should not be implemented in MVP because they imply runtime, workflow, publishing, or hidden state:

```bash
plotloom run
plotloom daemon
plotloom dashboard
plotloom workflow
plotloom publish
plotloom image poll
plotloom voice generate
plotloom subtitle burn
```

Future async image providers can add `image submit/poll` later, but MVP should keep image generation sync-first.
