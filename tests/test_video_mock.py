import json

from click.testing import CliRunner

from plotloom.cli import main


def test_video_submit_mock_writes_receipt_and_candidate(tmp_path):
    repo = _series_repo(tmp_path)
    ep = repo / "episodes" / "ep001"

    result = CliRunner().invoke(
        main,
        ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"],
    )

    assert result.exit_code == 0
    assert list((ep / "videos" / "clip-01" / "tasks").glob("mock-*.toml"))
    assert list((ep / "videos" / "clip-01" / "candidates").glob("v001.mock.mp4"))


def test_video_submit_mock_json_includes_receipt_and_candidate(tmp_path):
    repo = _series_repo(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "video",
            "submit",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--adapter",
            "mock",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "video.submit"
    assert payload["provider_task_id"] == "local"
    assert payload["receipt_path"].endswith("tasks/mock-local.toml")
    assert payload["candidate_path"].endswith("candidates/v001.mock.mp4")


def test_video_poll_mock_uses_latest_pointer(tmp_path):
    repo = _series_repo(tmp_path)
    runner = CliRunner()
    submit = runner.invoke(
        main,
        ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"],
    )
    assert submit.exit_code == 0

    result = runner.invoke(
        main,
        ["--json", "--repo", str(repo), "video", "poll", "--episode", "ep001", "--clip", "clip-01"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "video.poll"
    assert payload["adapter"] == "mock"
    assert payload["status"] == "succeeded"


def _series_repo(tmp_path):
    repo = tmp_path / "series"
    ep = repo / "episodes" / "ep001"
    ep.mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    (ep / "video-prompts-en.md").write_text("## Clip 01\n\nPrompt string:\nA fake clip.\n", encoding="utf-8")
    return repo
