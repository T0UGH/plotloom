---
title: Plotloom MVP Artifact Contract 初稿
created: 2026-04-28 22:12 CST
agent: nova
material_type: design-note
status: raw
tags:
  - plotloom
  - artifact-contract
  - short-drama
  - mvp
related:
  - docs/research/2026-04-28-plotloom-agent-neutral-skill-pack-research.md
---

# Plotloom MVP Artifact Contract 初稿

## 一句话结论

Plotloom 第一版的关键不是先做 runtime，而是先定一套不同 agent 都能读写的短剧生产 artifact。

建议 MVP 只保留 8 类文件：

```text
plotloom.yaml
episode.yaml
characters.yaml
shots.yaml
assets.yaml
jobs.yaml
manifest.json
review.md / rerun_plan.yaml
```

## 目录结构建议

```text
projects/<project-id>/
  plotloom.yaml
  episodes/
    ep001/
      episode.yaml
      characters.yaml
      shots.yaml
      assets.yaml
      jobs.yaml
      manifest.json
      review.md
      rerun_plan.yaml
      prompts/
        image_prompts.md
        video_prompts.md
      outputs/
        images/
        videos/
        final/
```

## `plotloom.yaml`

项目级元数据。

```yaml
project_id: office-backend-layoff
name: 公司裁掉最后一个后端
language: zh-CN
target:
  platform: douyin
  duration_sec: 45
  aspect_ratio: 9:16
  style: realistic_short_drama
runtime:
  preferred_agents: [hermes, codex, claude-code]
  generation_mode: semi_auto
created_at: 2026-04-28T22:12:00+08:00
```

## `episode.yaml`

45 秒短剧结构。

```yaml
episode_id: ep001
title: 公司裁掉最后一个后端
logline: 公司全面 AI 化后裁掉最后一个后端，结果生产系统在发布夜崩溃。
genre: workplace_dark_comedy
duration_sec: 45
hook: 他们裁掉我那天，公司所有 AI 都开始说人话。
beats:
  - id: b01
    time_range: 0-3
    function: hook
    description: 主角抱着纸箱走出工位，屏幕弹出全员降本增效公告。
  - id: b02
    time_range: 3-15
    function: conflict_setup
    description: CEO 宣布 AI 已经接管全部后端工作。
  - id: b03
    time_range: 15-30
    function: escalation
    description: 线上告警爆炸，AI 给出的修复方案互相矛盾。
  - id: b04
    time_range: 30-40
    function: reversal
    description: 主角离职前留下的注释成为唯一救命线索。
  - id: b05
    time_range: 40-45
    function: cliffhanger
    description: 主角手机收到一条来自生产数据库的求救短信。
constraints:
  max_locations: 2
  max_speaking_characters: 3
  must_end_with_follow_hook: true
```

## `characters.yaml`

角色一致性锚点。

```yaml
characters:
  - id: c01
    name: 林舟
    role: protagonist
    age: 29
    appearance: 瘦高，黑框眼镜，灰色连帽衫，抱纸箱
    personality: 冷静、讽刺、技术洁癖
    visual_anchors:
      - black rectangular glasses
      - gray hoodie
      - cardboard box
    voice: calm sarcastic male
  - id: c02
    name: CEO
    role: antagonist
    appearance: 西装，站在会议室大屏前
    personality: 自信、浮夸、盲目相信 AI
```

## `shots.yaml`

镜头表。每个 shot 必须可被图像/视频 prompt 继续编译。

```yaml
shots:
  - id: s001
    beat_id: b01
    duration_sec: 3
    location: open_office
    characters: [c01]
    camera: close-up, handheld slight shake
    action: 林舟抱着纸箱站在空工位旁，身后屏幕滚动裁员公告。
    dialogue: null
    emotion: absurd loneliness
    image_prompt_ref: ip001
    video_prompt_ref: vp001
  - id: s002
    beat_id: b02
    duration_sec: 6
    location: conference_room
    characters: [c02]
    camera: medium shot, corporate livestream style
    action: CEO 指着大屏宣布 AI 接管后端。
    dialogue: 从今天起，我们不再需要后端工程师。
    emotion: arrogant optimism
```

## `assets.yaml`

资产索引，不存大文件，只存路径、状态、来源和复用关系。

```yaml
assets:
  images:
    - id: img_c01_ref
      kind: character_reference
      character_id: c01
      path: outputs/images/c01_reference.png
      prompt_ref: ip_c01_ref
      status: generated
    - id: img_s001_first_frame
      kind: first_frame
      shot_id: s001
      path: outputs/images/s001_first_frame.png
      status: pending
  videos:
    - id: vid_s001
      kind: shot_video
      shot_id: s001
      path: outputs/videos/s001.mp4
      status: pending
```

## `jobs.yaml`

生成任务队列。把“要生成什么”和“用哪个工具生成”分开。

```yaml
jobs:
  - id: job_img_c01_ref
    type: image
    tool: imagegen2
    input:
      prompt_ref: ip_c01_ref
    output:
      asset_id: img_c01_ref
    status: pending
  - id: job_vid_s001
    type: video
    tool: seedance
    input:
      prompt_ref: vp001
      first_frame_asset: img_s001_first_frame
    output:
      asset_id: vid_s001
    status: pending
```

## `manifest.json`

最终成片和构建记录。

```json
{
  "project_id": "office-backend-layoff",
  "episode_id": "ep001",
  "version": "v001",
  "duration_sec": 45,
  "outputs": {
    "final_video": "outputs/final/ep001_v001.mp4",
    "cover": "outputs/final/cover.png",
    "subtitle": "outputs/final/subtitle.srt"
  },
  "source_artifacts": [
    "episode.yaml",
    "characters.yaml",
    "shots.yaml",
    "assets.yaml",
    "jobs.yaml"
  ],
  "created_by": "plotloom",
  "created_at": "2026-04-28T22:12:00+08:00"
}
```

## `review.md`

人工/agent 验收。

```markdown
# Review ep001 v001

## Scores

| Dimension | Score | Notes |
|---|---:|---|
| Hook | 4/5 | 0-3s 有钩子，但画面冲击可更强 |
| Conflict | 4/5 | 冲突明确 |
| Reversal | 3/5 | 反转略弱，需要更强打脸 |
| Continuity | 4/5 | 镜头连续基本成立 |
| Character consistency | 5/5 | 主角视觉一致 |
| Follow hook | 4/5 | 最后短信有追更感 |

## Decision

rerun_required: true

## Rerun targets

- s004: 反转镜头不够强
- cover: 点击率不足
```

## `rerun_plan.yaml`

```yaml
rerun:
  reason: reversal_not_strong_enough
  targets:
    - type: shot
      id: s004
      action: regenerate_video
      keep_assets: [img_c01_ref]
    - type: cover
      action: regenerate_image
  constraints:
    preserve_character_consistency: true
    preserve_total_duration_sec: 45
```

## 对 skill 拆分的影响

Artifact contract 定下来后，skill 边界自然清楚：

```text
plotloom-plan-episode      -> episode.yaml + characters.yaml
plotloom-storyboard-shots  -> shots.yaml
plotloom-image-prompts     -> image_prompts.md + assets.yaml image jobs
plotloom-video-prompts     -> video_prompts.md + video jobs
plotloom-review-rerun      -> review.md + rerun_plan.yaml
```

## 当前缺口

- 字段还没有 JSON Schema 化。
- imagegen2 / Seedance 的真实参数尚未绑定。
- 还没验证不同 agent 对同一套 artifact 的读写体验。
- 还没做样例项目端到端跑通。
