import json

from click.testing import CliRunner

from plotloom.cli import main


def test_asset_import_cover_candidate(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes" / "ep001").mkdir(parents=True)
    image = tmp_path / "cover.png"
    image.write_bytes(b"png")

    result = CliRunner().invoke(
        main,
        ["--repo", str(repo), "asset", "import", "--kind", "cover", "--episode", "ep001", "--file", str(image), "--candidate"],
    )

    assert result.exit_code == 0
    assert (repo / "episodes" / "ep001" / "images" / "covers" / "candidates" / "v001.png").exists()


def test_asset_import_uses_adapter_suffix(tmp_path):
    repo = tmp_path / "series"
    (repo / "assets" / "scenes").mkdir(parents=True)
    image = tmp_path / "scene.webp"
    image.write_bytes(b"webp")

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "asset",
            "import",
            "--kind",
            "scene",
            "--scene",
            "cafe",
            "--file",
            str(image),
            "--adapter",
            "codex-app-server",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["path"].endswith("assets/scenes/cafe/candidates/v001.codex-app-server.webp")


def test_asset_list_and_info(tmp_path):
    repo = tmp_path / "series"
    target = repo / "episodes" / "ep001" / "images" / "covers" / "candidates"
    target.mkdir(parents=True)
    asset = target / "v001.png"
    asset.write_bytes(b"png")

    listed = CliRunner().invoke(main, ["--json", "--repo", str(repo), "asset", "list", "--kind", "cover", "--episode", "ep001"])
    assert listed.exit_code == 0
    assert json.loads(listed.output)["assets"][0]["size"] == 3

    info = CliRunner().invoke(main, ["--json", "asset", "info", str(asset)])
    assert info.exit_code == 0
    assert json.loads(info.output)["asset"]["suffix"] == ".png"
