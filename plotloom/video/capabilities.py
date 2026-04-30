from __future__ import annotations

from plotloom.video.types import PlotloomVideoRequest, ValidationIssue, ValidationResult, VideoAdapterCapabilities, VideoMode


DREAMINA_RATIOS = frozenset({"1:1", "3:4", "16:9", "4:3", "9:16", "21:9"})
VOLCENGINE_RATIOS = DREAMINA_RATIOS | frozenset({"adaptive"})


def capabilities_for(adapter: str) -> VideoAdapterCapabilities:
    if adapter == "dreamina-cli":
        return VideoAdapterCapabilities(
            adapter="dreamina-cli",
            modes=frozenset({VideoMode.TEXT_TO_VIDEO, VideoMode.IMAGE_TO_VIDEO}),
            min_duration=4,
            max_duration=15,
            ratios=DREAMINA_RATIOS,
            resolutions=frozenset({"720p"}),
            max_prompt_chars=None,
            supports_native_audio=False,
            supports_seed=False,
            supports_first_frame=True,
            supports_reference_images=False,
            supports_reference_videos=False,
            supports_video_edit=False,
        )
    if adapter == "volcengine-seedance":
        return VideoAdapterCapabilities(
            adapter="volcengine-seedance",
            modes=frozenset({VideoMode.TEXT_TO_VIDEO, VideoMode.IMAGE_TO_VIDEO, VideoMode.REFERENCE_TO_VIDEO}),
            min_duration=4,
            max_duration=15,
            ratios=VOLCENGINE_RATIOS,
            resolutions=frozenset({"720p"}),
            max_prompt_chars=None,
            supports_native_audio=True,
            supports_seed=False,
            supports_first_frame=True,
            supports_reference_images=True,
            supports_reference_videos=False,
            supports_video_edit=False,
            extra_durations=frozenset({-1}),
        )
    raise ValueError(f"unknown video adapter: {adapter}")


def validate_request(req: PlotloomVideoRequest, caps: VideoAdapterCapabilities) -> ValidationResult:
    issues: list[ValidationIssue] = []

    if req.adapter != caps.adapter:
        issues.append(
            _error(
                "ADAPTER_MISMATCH",
                f"request adapter {req.adapter!r} does not match capabilities adapter {caps.adapter!r}",
            )
        )

    if req.mode not in caps.modes:
        issues.append(_error("MODE_UNSUPPORTED", f"{req.mode.value} is not supported by {caps.adapter}"))

    if req.duration not in caps.extra_durations and not caps.min_duration <= req.duration <= caps.max_duration:
        issues.append(
            _error(
                "DURATION_UNSUPPORTED",
                f"duration={req.duration} is unsupported by {caps.adapter}; expected {caps.min_duration}-{caps.max_duration}s",
            )
        )

    if req.ratio not in caps.ratios:
        issues.append(_error("RATIO_UNSUPPORTED", f"ratio={req.ratio} is unsupported by {caps.adapter}"))

    if req.resolution not in caps.resolutions:
        issues.append(_error("RESOLUTION_UNSUPPORTED", f"resolution={req.resolution} is unsupported by {caps.adapter}"))

    if caps.max_prompt_chars is not None and len(req.prompt_text) > caps.max_prompt_chars:
        issues.append(
            _error(
                "PROMPT_TOO_LONG",
                f"prompt has {len(req.prompt_text)} chars; {caps.adapter} supports at most {caps.max_prompt_chars}",
            )
        )

    if req.first_frame is not None and not caps.supports_first_frame:
        issues.append(_error("FIRST_FRAME_UNSUPPORTED", f"first_frame is unsupported by {caps.adapter}"))

    if req.reference_images and not caps.supports_reference_images:
        issues.append(_error("REFERENCE_IMAGES_UNSUPPORTED", f"reference_images are unsupported by {caps.adapter}"))

    if req.reference_videos and not caps.supports_reference_videos:
        issues.append(_error("REFERENCE_VIDEOS_UNSUPPORTED", f"reference_videos are unsupported by {caps.adapter}"))

    if req.audio_intent == "require_native" and not caps.supports_native_audio:
        issues.append(_error("NATIVE_AUDIO_UNSUPPORTED", f"native audio is required but unsupported by {caps.adapter}"))

    if req.seed is not None and not caps.supports_seed:
        issues.append(_error("SEED_UNSUPPORTED", f"seed is unsupported by {caps.adapter}"))

    if (req.mode == VideoMode.VIDEO_EDIT or req.source_video is not None) and not caps.supports_video_edit:
        issues.append(_error("VIDEO_EDIT_UNSUPPORTED", f"video edit is unsupported by {caps.adapter}"))

    return ValidationResult(issues=issues)


def _error(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(level="error", code=code, message=message)
