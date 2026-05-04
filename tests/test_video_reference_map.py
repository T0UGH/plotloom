import json
import tomllib

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.video.reference_map import read_reference_map


def test_video_plan_references_json_preserves_slots_without_writing(tmp_path):
    repo = _series_repo(tmp_path)
    _touch(repo / "episodes" / "ep001" / "images" / "references" / "clip-01-first.jpg")
    _touch(repo / "assets" / "cast" / "ethan" / "safe-face.png")
    _touch(repo / "assets" / "scenes" / "gala" / "selected.png")
    _touch(repo / "episodes" / "ep001" / "images" / "references" / "clip-01-last.jpg")

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "video",
            "plan-references",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--first-frame",
            "episodes/ep001/images/references/clip-01-first.jpg",
            "--reference",
            "character:ethan=assets/cast/ethan/safe-face.png",
            "--reference",
            "scene:gala=assets/scenes/gala/selected.png",
            "--last-frame",
            "episodes/ep001/images/references/clip-01-last.jpg",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "video.plan-references"
    assert payload["written"] is False
    assert [item["slot"] for item in payload["references"]] == [1, 2, 3, 4]
    assert [item["kind"] for item in payload["references"]] == ["first_frame", "character", "scene", "last_frame"]
    assert payload["references"][1]["character"] == "ethan"
    assert payload["references"][2]["scene"] == "gala"
    assert not (repo / "episodes" / "ep001" / "videos" / "clip-01" / "reference-map.toml").exists()


def test_video_plan_references_write_creates_reference_map(tmp_path):
    repo = _series_repo(tmp_path)
    _touch(repo / "assets" / "cast" / "ethan" / "safe-face.png")

    result = CliRunner().invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "plan-references",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--reference",
            "character:ethan=assets/cast/ethan/safe-face.png",
            "--write",
        ],
    )

    assert result.exit_code == 0
    path = repo / "episodes" / "ep001" / "videos" / "clip-01" / "reference-map.toml"
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    assert payload["references"] == [
        {
            "slot": 1,
            "kind": "character",
            "path": "assets/cast/ethan/safe-face.png",
            "source": "asset",
            "character": "ethan",
        }
    ]
    assert read_reference_map(path, repo)[0].character == "ethan"


def test_video_plan_references_rejects_missing_path(tmp_path):
    repo = _series_repo(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "video",
            "plan-references",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--reference",
            "character:ethan=assets/cast/ethan/missing.png",
            "--write",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["command"] == "video.plan-references"
    assert "reference path not found" in payload["error"]["message"]
    assert not (repo / "episodes" / "ep001" / "videos" / "clip-01" / "reference-map.toml").exists()


def _series_repo(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes" / "ep001").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    return repo


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"ref")
