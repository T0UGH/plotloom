import subprocess
from pathlib import Path

from plotloom.video.adapters.dreamina_cli import DreaminaCliAdapter
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_dreamina_submit_parses_submit_id(monkeypatch, tmp_path):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout='{"submit_id":"sub_123"}', stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    req = PlotloomVideoRequest(
        repo=tmp_path,
        episode="ep001",
        clip="clip-01",
        adapter="dreamina-cli",
        mode=VideoMode.TEXT_TO_VIDEO,
        prompt_file=Path("p.md"),
        prompt_text="prompt",
        ratio="9:16",
        resolution="720p",
        duration=5,
    )

    result = DreaminaCliAdapter(binary="dreamina", home="~").submit(req, candidate_path=tmp_path / "v001.mp4")

    assert result.provider_task_id == "sub_123"


def test_dreamina_submit_builds_text_to_video_command(monkeypatch, tmp_path):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append(args[0])
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="submit_id=sub_456", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    req = _request(tmp_path)

    DreaminaCliAdapter(binary="dreamina").submit(req, candidate_path=tmp_path / "v001.mp4")

    assert calls[0][:2] == ["dreamina", "text2video"]
    assert "--prompt" in calls[0]
    assert "prompt" in calls[0]
    assert "--duration" in calls[0]
    assert "5" in calls[0]
    assert "--poll=0" in calls[0]


def test_dreamina_submit_builds_image_to_video_command(monkeypatch, tmp_path):
    calls = []
    first_frame = tmp_path / "first.png"
    first_frame.write_bytes(b"png")

    def fake_run(*args, **kwargs):
        calls.append(args[0])
        return subprocess.CompletedProcess(args=args, returncode=0, stdout='{"submit_id":"sub_img"}', stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    req = _request(tmp_path, mode=VideoMode.IMAGE_TO_VIDEO, first_frame=first_frame)

    DreaminaCliAdapter(binary="dreamina").submit(req, candidate_path=tmp_path / "v001.mp4")

    assert calls[0][:2] == ["dreamina", "image2video"]
    assert calls[0][calls[0].index("--image") + 1] == str(first_frame)


def _request(tmp_path, **overrides):
    values = {
        "repo": tmp_path,
        "episode": "ep001",
        "clip": "clip-01",
        "adapter": "dreamina-cli",
        "mode": VideoMode.TEXT_TO_VIDEO,
        "prompt_file": Path("p.md"),
        "prompt_text": "prompt",
        "ratio": "9:16",
        "resolution": "720p",
        "duration": 5,
    }
    values.update(overrides)
    return PlotloomVideoRequest(**values)
