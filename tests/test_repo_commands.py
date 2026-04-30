from click.testing import CliRunner

from plotloom.cli import main


def test_init_creates_series_repo_and_registry(tmp_path):
    config = tmp_path / ".plotloom" / ".env.toml"
    repos_root = tmp_path / "repos"
    registry = tmp_path / "plotloom.toml"
    config.parent.mkdir()
    config.write_text(
        f'[plotloom]\nrepos_root = "{repos_root}"\nregistry_path = "{registry}"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--config", str(config), "init", "fake-heiress", "--title", "Fake Heiress"])

    assert result.exit_code == 0
    repo = repos_root / "fake-heiress"
    assert (repo / "series.md").exists()
    assert (repo / "characters.md").exists()
    assert 'slug = "fake-heiress"' in registry.read_text(encoding="utf-8")


def test_validate_requires_prompts(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes" / "ep001").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--repo", str(repo), "validate", "--episode", "ep001", "--require-prompts"])

    assert result.exit_code == 1
    assert "video-prompts" in result.output
