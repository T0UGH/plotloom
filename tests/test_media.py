import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

import plotloom.commands.media as media_commands
import plotloom.media as media_module
from plotloom.cli import main
from plotloom.errors import MediaValidationError
from plotloom.media import MediaFacts


def ffprobe_payload() -> dict:
    return {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1080,
                "height": 1920,
                "avg_frame_rate": "24000/1001",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
            },
        ],
        "format": {
            "duration": "3.500000",
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        },
    }


def media_facts(path: Path) -> MediaFacts:
    return MediaFacts(
        path=path,
        duration=3.5,
        width=1080,
        height=1920,
        fps=24000 / 1001,
        has_audio=True,
        video_codec="h264",
        audio_codec="aac",
        format_name="mov,mp4,m4a,3gp,3g2,mj2",
    )


def test_probe_media_parses_ffprobe_json(tmp_path, monkeypatch):
    video = tmp_path / "candidate.mp4"
    video.write_bytes(b"placeholder")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        assert cmd[0] == "ffprobe"
        assert "-show_streams" in cmd
        assert "-show_format" in cmd
        assert cmd[-1] == str(video.resolve())
        assert kwargs["text"] is True
        assert kwargs["stdout"] == subprocess.PIPE
        assert kwargs["stderr"] == subprocess.PIPE
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(ffprobe_payload()), stderr="")

    monkeypatch.setattr(media_module.subprocess, "run", fake_run)

    facts = media_module.probe_media(video)

    assert len(calls) == 1
    assert facts.path == video.resolve()
    assert facts.duration == 3.5
    assert facts.width == 1080
    assert facts.height == 1920
    assert facts.fps == pytest.approx(23.976023976)
    assert facts.has_audio is True
    assert facts.video_codec == "h264"
    assert facts.audio_codec == "aac"
    assert facts.format_name == "mov,mp4,m4a,3gp,3g2,mj2"
    assert facts.to_dict()["path"] == str(video.resolve())


def test_probe_media_raises_media_validation_error_on_ffprobe_failure(tmp_path, monkeypatch):
    video = tmp_path / "broken.mp4"
    video.write_bytes(b"not really media")

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Invalid data found")

    monkeypatch.setattr(media_module.subprocess, "run", fake_run)

    with pytest.raises(MediaValidationError) as error:
        media_module.probe_media(video)

    assert "ffprobe failed" in error.value.message
    assert "Invalid data found" in error.value.message


def test_media_probe_command_json_reports_facts(tmp_path, monkeypatch):
    video = tmp_path / "candidate.mp4"
    video.write_bytes(b"placeholder")

    def fake_probe(path):
        assert path == video
        return media_facts(video.resolve())

    monkeypatch.setattr(media_commands, "probe_media", fake_probe)

    result = CliRunner().invoke(main, ["--json", "media", "probe", str(video)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "media.probe"
    assert payload["media"]["path"] == str(video.resolve())
    assert payload["media"]["duration"] == 3.5
    assert payload["media"]["width"] == 1080
    assert payload["media"]["height"] == 1920
    assert payload["media"]["has_audio"] is True
    assert payload["media"]["video_codec"] == "h264"
    assert payload["media"]["audio_codec"] == "aac"


def test_media_check_command_validates_expected_facts(tmp_path, monkeypatch):
    video = tmp_path / "candidate.mp4"
    video.write_bytes(b"placeholder")

    monkeypatch.setattr(media_commands, "probe_media", lambda path: media_facts(path.resolve()))

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "media",
            "check",
            str(video),
            "--expect-video",
            "--expect-audio",
            "--ratio",
            "9:16",
            "--resolution",
            "1080x1920",
            "--duration",
            "3.5",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "media.check"
    assert payload["checks"]["ratio"]["ok"] is True
    assert payload["checks"]["duration"]["ok"] is True


def test_media_probe_command_json_reports_ffprobe_failure(tmp_path, monkeypatch):
    video = tmp_path / "broken.mp4"
    video.write_bytes(b"not really media")

    def fail_probe(path):
        raise MediaValidationError("ffprobe failed for media: Invalid data found", next_step="Check the file path.")

    monkeypatch.setattr(media_commands, "probe_media", fail_probe)

    result = CliRunner().invoke(main, ["--json", "media", "probe", str(video)])

    assert result.exit_code == 4
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["command"] == "media.probe"
    assert payload["error"]["code"] == "MEDIA_VALIDATION_ERROR"
    assert "Invalid data found" in payload["error"]["message"]
