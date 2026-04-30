import json

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.stitch import discover_selected_clips


def test_discover_selected_clips_in_lexical_order(tmp_path):
    videos = tmp_path / "episodes" / "ep001" / "videos"
    (videos / "clip-02").mkdir(parents=True)
    (videos / "clip-01").mkdir(parents=True)
    (videos / "clip-02" / "selected.mp4").write_bytes(b"2")
    (videos / "clip-01" / "selected.mp4").write_bytes(b"1")

    clips = discover_selected_clips(tmp_path, "ep001")

    assert [path.parent.name for path in clips] == ["clip-01", "clip-02"]


def test_stitch_plan_command_lists_selected_clips(tmp_path):
    repo = tmp_path / "series"
    selected = repo / "episodes" / "ep001" / "videos" / "clip-01" / "selected.mp4"
    selected.parent.mkdir(parents=True)
    selected.write_bytes(b"1")

    result = CliRunner().invoke(main, ["--json", "--repo", str(repo), "stitch", "plan", "--episode", "ep001"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "stitch.plan"
    assert payload["clips"] == [str(selected)]
