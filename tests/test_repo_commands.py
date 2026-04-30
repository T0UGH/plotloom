from click.testing import CliRunner

import plotloom.repo as repo_module
from plotloom.cli import main
from plotloom.toml_io import toml_str


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


def test_init_repo_can_use_packaged_template_when_source_template_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_module, "project_root", lambda: tmp_path / "missing-project-root")

    repo_module.init_repo(tmp_path / "repo", slug="packaged-template", title="Packaged Template")

    assert (tmp_path / "repo" / "series.md").read_text(encoding="utf-8").startswith("# Packaged Template")
    assert (tmp_path / "repo" / "episodes" / "ep001" / "videos" / ".gitkeep").exists()


def test_validate_discovers_repo_from_current_directory(tmp_path, monkeypatch):
    repo = tmp_path / "series"
    (repo / "episodes").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    result = CliRunner().invoke(main, ["validate"])

    assert result.exit_code == 0
    assert "repo ok" in result.output


def test_validate_rejects_episode_path_traversal(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--repo", str(repo), "validate", "--episode", "../../outside"])

    assert result.exit_code == 1
    assert "invalid episode" in result.output


def test_registry_duplicate_slug_different_path_fails(tmp_path):
    registry = tmp_path / "plotloom.toml"
    repo = tmp_path / "repo"
    other = tmp_path / "other"
    registry.write_text(f'[[repos]]\nslug = "demo"\ntitle = "Demo"\npath = "{other}"\n', encoding="utf-8")

    try:
        repo_module.append_registry(registry, slug="demo", title="Demo", path=repo)
    except ValueError as error:
        assert "registry slug conflict" in str(error)
    else:
        raise AssertionError("expected duplicate slug conflict")


def test_toml_str_escapes_control_characters():
    assert "\\u0007" in toml_str("bad\x07value")
