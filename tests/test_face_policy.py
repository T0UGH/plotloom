import json

from click.testing import CliRunner

from plotloom.cli import main


def test_validate_face_policy_accepts_three_strategies(tmp_path):
    repo = _series_repo(tmp_path)
    _write_policy(
        repo,
        "ethan",
        """
character = "ethan"

[face]
strategy = "safe-face-reference"
path = "assets/cast/ethan/safe-face.png"
""",
    )
    _touch(repo / "assets" / "cast" / "ethan" / "safe-face.png")
    _write_policy(
        repo,
        "mira",
        """
[face]
strategy = "text-only"
description = "Young East Asian woman, sharp gaze, restrained expression."
""",
    )
    _write_policy(
        repo,
        "lichen",
        """
[face]
strategy = "cloud-face-asset"
provider = "volcengine-seedance"
cloud_asset = "asset://asset-20260224225526-g6kpx"
body_reference = "assets/cast/lichen/body-wardrobe.png"
""",
    )
    _touch(repo / "assets" / "cast" / "lichen" / "body-wardrobe.png")

    result = CliRunner().invoke(main, ["--json", "--repo", str(repo), "validate", "--face-policy"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "repo.validate"
    assert payload["face_policy"]["checked"] == 3


def test_validate_face_policy_reports_missing_policy_file(tmp_path):
    repo = _series_repo(tmp_path)
    (repo / "assets" / "cast" / "ethan").mkdir(parents=True)

    result = CliRunner().invoke(main, ["--repo", str(repo), "validate", "--face-policy"])

    assert result.exit_code == 1
    assert "missing face-policy.toml" in result.output


def test_validate_face_policy_reports_missing_reference_path(tmp_path):
    repo = _series_repo(tmp_path)
    _write_policy(
        repo,
        "ethan",
        """
[face]
strategy = "safe-face-reference"
path = "assets/cast/ethan/missing.png"
""",
    )

    result = CliRunner().invoke(main, ["--json", "--repo", str(repo), "validate", "--face-policy"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["command"] == "repo.validate"
    assert "path not found" in payload["error"]["message"]


def test_validate_face_policy_requires_volcengine_asset_uri_shape(tmp_path):
    repo = _series_repo(tmp_path)
    _write_policy(
        repo,
        "ethan",
        """
[face]
strategy = "cloud-face-asset"
provider = "volcengine-seedance"
cloud_asset = "asset://volcengine/face-assets/ethan"
body_reference = "assets/cast/ethan/body.png"
""",
    )
    _touch(repo / "assets" / "cast" / "ethan" / "body.png")

    result = CliRunner().invoke(main, ["--repo", str(repo), "validate", "--face-policy"])

    assert result.exit_code == 1
    assert "asset://asset-" in result.output


def test_validate_without_face_policy_does_not_require_policy_file(tmp_path):
    repo = _series_repo(tmp_path)
    (repo / "assets" / "cast" / "ethan").mkdir(parents=True)

    result = CliRunner().invoke(main, ["--repo", str(repo), "validate"])

    assert result.exit_code == 0
    assert "repo ok" in result.output


def _series_repo(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes").mkdir(parents=True)
    (repo / "assets" / "cast").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    return repo


def _write_policy(repo, character, text):
    path = repo / "assets" / "cast" / character / "face-policy.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"asset")
