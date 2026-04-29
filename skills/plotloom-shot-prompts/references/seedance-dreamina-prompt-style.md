# Seedance / Dreamina Prompt Style Reference

## Sources Borrowed
Patterns are adapted from local readings of Seedance prompt repos, including `seedance-prompt-skill`, `Seedance2-Storyboard-Generator`, `seedance_prompt`, `shotcine`, and `autoflow`.

## Core Rule
```text
Seedance prompt ≠ shot list
Seedance prompt = director brief translated into one continuous narrative timeline
```

Each generation task should be a complete 8-20s cinematic moment. A prompt may include multiple camera beats, but it must have one primary timeline.

## Useful Prompt Formula
```text
[规格总纲：竖屏/横屏，时长，风格，情绪]
素材引用：@图片1 = 主角外观参考；@图片2 = 场景参考；@视频1 = 上一段视频用于衔接
0-3秒：建立场景 / 钩子
3-6秒：主体入场 / 冲突出现
6-9秒：动作推进 / 情绪升级
9-12秒：高潮 / 反转
12-15秒：尾帧 / 悬念衔接
声音/台词：串行、简短、可拍
禁止：水印、logo、伪字幕、画面内乱码文字、身份漂移
```

## Reference Syntax
When the target platform supports it, use:
- `@图片1` to `@图片9`
- `@视频1` to `@视频3`
- `@音频1` to `@音频3`

Keep a visible material mapping near the prompt. Do not exceed the provider-specific material count. Some workflows use total multimodal files ≤12; API execution paths may be stricter (e.g. ≤9). Treat limits as adapter-specific constraints.

## Prompt Checks
- Is there exactly one primary timeline?
- Does every reference have a purpose?
- Are characters introduced with stable identity anchors?
- Are entrances, exits, and occlusions described where needed?
- Is dialogue serial rather than overlapping?
- Is camera motion attached to a stable space anchor?
- Is there an ending frame / handoff point?
- Does the prompt avoid key information only in the first/last 0.5s?

## Do Not
- Submit one model job per micro-shot.
- Convert a storyboard table directly into a video prompt.
- Overload a 15s prompt with more than one major reversal.
- Hide retry rationale; write rerun notes.
