import json

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.video.compare import compare_receipts


def test_compare_receipts_keeps_adapter_status(tmp_path):
    receipt = tmp_path / "r.toml"
    receipt.write_text(
        'adapter = "mock"\nstatus = "succeeded"\ncandidate_path = "episodes/ep001/videos/clip-01/candidates/v001.mock.mp4"\n',
        encoding="utf-8",
    )

    rows = compare_receipts([receipt])

    assert rows[0]["adapter"] == "mock"
    assert rows[0]["status"] == "succeeded"


def test_video_compare_command_reports_receipts(tmp_path):
    repo = tmp_path / "series"
    tasks = repo / "episodes" / "ep001" / "videos" / "clip-01" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "mock-local.toml").write_text(
        'adapter = "mock"\nstatus = "succeeded"\ncandidate_path = "episodes/ep001/videos/clip-01/candidates/v001.mock.mp4"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--json", "--repo", str(repo), "video", "compare", "--episode", "ep001"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "video.compare"
    assert payload["rows"][0]["adapter"] == "mock"


def test_video_poll_updates_mock_receipt(tmp_path):
    repo = _series_repo(tmp_path)
    runner = CliRunner()
    submit = runner.invoke(
        main,
        ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"],
    )
    assert submit.exit_code == 0

    poll = runner.invoke(
        main,
        ["--json", "--repo", str(repo), "video", "poll", "--episode", "ep001", "--clip", "clip-01"],
    )

    assert poll.exit_code == 0
    payload = json.loads(poll.output)
    assert payload["ok"] is True
    assert payload["status"] == "succeeded"
    latest = repo / "episodes" / "ep001" / "videos" / "clip-01" / "latest-task.toml"
    assert latest.exists()


def _series_repo(tmp_path):
    repo = tmp_path / "series"
    ep = repo / "episodes" / "ep001"
    ep.mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    (ep / "video-prompts-en.md").write_text("## Clip 01\n\nPrompt string:\nA fake clip.\n", encoding="utf-8")
    return repo
