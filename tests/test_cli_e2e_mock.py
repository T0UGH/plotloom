from click.testing import CliRunner

from plotloom.cli import main


def test_cli_mock_e2e_without_real_providers(tmp_path):
    config = tmp_path / ".plotloom" / ".env.toml"
    config.parent.mkdir()
    repos_root = tmp_path / "repos"
    registry = tmp_path / "plotloom.toml"
    config.write_text(f'[plotloom]\nrepos_root = "{repos_root}"\nregistry_path = "{registry}"\n', encoding="utf-8")
    config.chmod(0o600)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config), "init", "fake-heiress", "--title", "Fake Heiress"])
    assert result.exit_code == 0

    repo = repos_root / "fake-heiress"
    ep = repo / "episodes" / "ep001"
    (ep / "video-prompts-en.md").write_text("## Clip 01\n\nPrompt string:\nA mock clip.\n", encoding="utf-8")

    result = runner.invoke(main, ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"])
    assert result.exit_code == 0

    candidate = next((ep / "videos" / "clip-01" / "candidates").glob("v001.mock.mp4"))
    result = runner.invoke(main, ["select", str(candidate)])
    assert result.exit_code == 0
    assert (ep / "videos" / "clip-01" / "selected.mp4").exists()
