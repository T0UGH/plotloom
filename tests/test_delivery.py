import json

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.delivery import episode_files


def test_episode_files_lists_final_and_selected(tmp_path):
    videos = tmp_path / "episodes" / "ep001" / "videos"
    (videos / "clip-01").mkdir(parents=True)
    (videos / "clip-01" / "selected.mp4").write_bytes(b"x")
    (videos / "final.mp4").write_bytes(b"x")

    files = episode_files(tmp_path, "ep001")

    assert "episodes/ep001/videos/final.mp4" in files
    assert "episodes/ep001/videos/clip-01/selected.mp4" in files


def test_delivery_files_command_json(tmp_path):
    repo = tmp_path / "series"
    selected = repo / "episodes" / "ep001" / "videos" / "clip-01" / "selected.mp4"
    selected.parent.mkdir(parents=True)
    selected.write_bytes(b"x")

    result = CliRunner().invoke(main, ["--json", "--repo", str(repo), "delivery", "files", "--episode", "ep001"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["files"] == ["episodes/ep001/videos/clip-01/selected.mp4"]
