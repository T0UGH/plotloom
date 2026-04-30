from pathlib import Path

from plotloom.video.adapters.volcengine_seedance import VolcEngineSeedanceAdapter
from plotloom.video.types import PlotloomVideoRequest, VideoMode


class FakeHTTP:
    def post(self, url, headers, json, timeout):
        self.post_url = url
        self.post_headers = headers
        self.post_json = json
        return type("Resp", (), {"json": lambda self: {"id": "cgt_123"}, "raise_for_status": lambda self: None})()

    def get(self, url, headers, timeout):
        self.get_url = url
        self.get_headers = headers
        return type(
            "Resp",
            (),
            {"json": lambda self: {"id": "cgt_123", "status": "succeeded", "output": {"video_url": "https://example.com/out.mp4"}}, "raise_for_status": lambda self: None},
        )()


def test_volcengine_submit_returns_task_id(tmp_path):
    http = FakeHTTP()
    adapter = VolcEngineSeedanceAdapter(http=http, ark_api_key="test-key", model="doubao-seedance-2-0-260128")
    req = _request(tmp_path)

    result = adapter.submit(req, candidate_path=tmp_path / "v001.mp4")

    assert result.provider_task_id == "cgt_123"
    assert http.post_url.endswith("/contents/generations/tasks")
    assert http.post_json["model"] == "doubao-seedance-2-0-260128"
    assert http.post_json["content"] == [{"type": "text", "text": "prompt"}]
    assert http.post_json["generate_audio"] is True
    assert http.post_json["watermark"] is False
    assert http.post_headers["Authorization"] == "Bearer test-key"


def test_volcengine_submit_includes_reference_media_urls(tmp_path):
    http = FakeHTTP()
    adapter = VolcEngineSeedanceAdapter(http=http, ark_api_key="test-key", model="doubao-seedance-2-0-260128")
    req = _request(tmp_path, mode=VideoMode.REFERENCE_TO_VIDEO, ratio="16:9", duration=11)

    result = adapter.submit(
        req,
        candidate_path=tmp_path / "v001.mp4",
        reference_images=[
            "https://example.com/r2v_tea_pic1.jpg",
            "https://example.com/r2v_tea_pic2.jpg",
        ],
        reference_videos=["https://example.com/r2v_tea_video1.mp4"],
        reference_audio="https://example.com/r2v_tea_audio1.mp3",
    )

    assert result.provider_task_id == "cgt_123"
    assert http.post_json["ratio"] == "16:9"
    assert http.post_json["duration"] == 11
    assert http.post_json["content"][1]["role"] == "reference_image"
    assert http.post_json["content"][3]["role"] == "reference_video"
    assert http.post_json["content"][4]["role"] == "reference_audio"


def test_volcengine_poll_returns_status_and_video_url(tmp_path):
    http = FakeHTTP()
    adapter = VolcEngineSeedanceAdapter(http=http, ark_api_key="test-key")

    result = adapter.poll("cgt_123", download_dir=tmp_path)

    assert http.get_url.endswith("/contents/generations/tasks/cgt_123")
    assert http.get_headers["Authorization"] == "Bearer test-key"
    assert result.status == "succeeded"
    assert result.video_url == "https://example.com/out.mp4"


def _request(tmp_path, **overrides):
    values = {
        "repo": tmp_path,
        "episode": "ep001",
        "clip": "clip-01",
        "adapter": "volcengine-seedance",
        "mode": VideoMode.TEXT_TO_VIDEO,
        "prompt_file": Path("p.md"),
        "prompt_text": "prompt",
        "ratio": "9:16",
        "resolution": "720p",
        "duration": 5,
    }
    values.update(overrides)
    return PlotloomVideoRequest(**values)
