from pathlib import Path

import pytest

from plotloom.video.capabilities import capabilities_for, validate_request
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def make_request(**overrides):
    values = {
        "repo": Path("/tmp/series"),
        "episode": "ep001",
        "clip": "clip-01",
        "adapter": "dreamina-cli",
        "mode": VideoMode.TEXT_TO_VIDEO,
        "prompt_file": Path("episodes/ep001/video-prompts-en.md"),
        "prompt_text": "prompt",
        "ratio": "9:16",
        "resolution": "720p",
        "duration": 5,
    }
    values.update(overrides)
    return PlotloomVideoRequest(**values)


def issue_codes(req):
    return [issue.code for issue in validate_request(req, capabilities_for(req.adapter)).issues]


def test_video_request_defaults():
    req = make_request()

    assert req.audio_intent == "native_if_supported"
    assert req.reference_images == []
    assert req.reference_videos == []
    assert req.first_frame is None
    assert req.source_video is None
    assert not req.allow_downgrade
    assert not req.allow_normalize_duration


def test_capabilities_for_current_provider_set_only():
    assert capabilities_for("dreamina-cli").adapter == "dreamina-cli"
    assert capabilities_for("aliyun-bailian-wan").adapter == "aliyun-bailian-wan"
    assert capabilities_for("volcengine-seedance").adapter == "volcengine-seedance"

    with pytest.raises(ValueError, match="unknown video adapter"):
        capabilities_for("unknown-provider")


def test_aliyun_bailian_rejects_too_long_prompt():
    req = make_request(
        adapter="aliyun-bailian-wan",
        prompt_file=Path("p.md"),
        prompt_text="x" * 5001,
    )

    result = validate_request(req, capabilities_for("aliyun-bailian-wan"))

    assert not result.ok
    assert result.issues[0].code == "PROMPT_TOO_LONG"


def test_aliyun_bailian_uses_current_wan_t2v_constraints():
    req = make_request(
        adapter="aliyun-bailian-wan",
        prompt_text="x" * 1501,
        ratio="3:4",
        resolution="1080p",
        duration=2,
        seed=123,
        audio_intent="require_native",
    )

    result = validate_request(req, capabilities_for("aliyun-bailian-wan"))

    assert [issue.code for issue in result.issues] == ["PROMPT_TOO_LONG"]


def test_capability_sets_cannot_poison_future_results():
    caps = capabilities_for("dreamina-cli")

    with pytest.raises(AttributeError):
        caps.ratios.add("bad:ratio")

    assert "bad:ratio" not in capabilities_for("dreamina-cli").ratios


def test_dreamina_rejects_unsupported_resolution_and_short_duration():
    req = make_request(resolution="1080p", duration=3)

    assert issue_codes(req) == ["DURATION_UNSUPPORTED", "RESOLUTION_UNSUPPORTED"]


def test_dreamina_allows_first_frame_but_not_reference_images():
    ok_req = make_request(
        mode=VideoMode.IMAGE_TO_VIDEO,
        first_frame=Path("episodes/ep001/images/clip-01.png"),
    )
    bad_req = make_request(
        mode=VideoMode.REFERENCE_TO_VIDEO,
        reference_images=[Path("assets/cast/lead.png")],
    )

    assert validate_request(ok_req, capabilities_for("dreamina-cli")).ok
    assert "MODE_UNSUPPORTED" in issue_codes(bad_req)
    assert "REFERENCE_IMAGES_UNSUPPORTED" in issue_codes(bad_req)


def test_volcengine_requires_native_audio_when_requested():
    volc_req = make_request(adapter="volcengine-seedance", audio_intent="require_native")
    dreamina_req = make_request(audio_intent="require_native")

    assert validate_request(volc_req, capabilities_for("volcengine-seedance")).ok
    assert issue_codes(dreamina_req) == ["NATIVE_AUDIO_UNSUPPORTED"]


def test_seed_and_video_edit_are_rejected_for_mvp_adapters():
    seed_req = make_request(adapter="volcengine-seedance", seed=123)
    edit_req = make_request(
        adapter="aliyun-bailian-wan",
        mode=VideoMode.VIDEO_EDIT,
        source_video=Path("episodes/ep001/videos/source.mp4"),
    )

    assert issue_codes(seed_req) == ["SEED_UNSUPPORTED"]
    assert "VIDEO_EDIT_UNSUPPORTED" in issue_codes(edit_req)
