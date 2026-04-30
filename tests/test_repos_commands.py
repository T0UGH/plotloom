import json
import tomllib

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.toml_io import toml_str


def write_config(path, registry):
    path.write_text(f"[plotloom]\nregistry_path = {toml_str(registry)}\n", encoding="utf-8")


def test_repos_list_reads_registry(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    repo = tmp_path / "series"
    repo.mkdir()
    write_config(config, registry)
    registry.write_text(
        "\n".join(
            [
                "[[repos]]",
                'slug = "demo"',
                'title = "Demo"',
                f"path = {toml_str(repo)}",
                'status = "active"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--config", str(config), "repos", "list"])

    assert result.exit_code == 0
    assert "demo" in result.output
    assert "active" in result.output
    assert str(repo) in result.output
    assert "Demo" in result.output


def test_repos_list_supports_global_json_after_command(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    repo = tmp_path / "series"
    repo.mkdir()
    write_config(config, registry)
    registry.write_text(
        f'[[repos]]\nslug = "demo"\ntitle = "Demo"\npath = {toml_str(repo)}\nstatus = "active"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--config", str(config), "repos", "list", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "repos.list"
    assert payload["repos"][0]["slug"] == "demo"


def test_repos_resolve_fails_for_missing_path(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    write_config(config, registry)
    registry.write_text(
        '[[repos]]\nslug = "demo"\ntitle = "Demo"\npath = "/no/such/path"\nstatus = "active"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--config", str(config), "repos", "resolve", "demo"])

    assert result.exit_code == 1
    assert "missing" in result.output.lower()


def test_repos_resolve_fails_when_entry_omits_path(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    write_config(config, registry)
    registry.write_text('[[repos]]\nslug = "demo"\ntitle = "Demo"\nstatus = "active"\n', encoding="utf-8")

    result = CliRunner().invoke(main, ["--config", str(config), "repos", "resolve", "demo"])

    assert result.exit_code == 1
    assert "missing path" in result.output.lower()
    assert "demo" in result.output


def test_repos_resolve_fails_when_active_entry_has_blank_path(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    write_config(config, registry)
    registry.write_text('[[repos]]\nslug = "demo"\ntitle = "Demo"\npath = "   "\nstatus = "active"\n', encoding="utf-8")

    result = CliRunner().invoke(main, ["--config", str(config), "repos", "resolve"])

    assert result.exit_code == 1
    assert "missing path" in result.output.lower()
    assert "demo" in result.output


def test_repos_resolve_json_error_command_is_stable(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    write_config(config, registry)
    registry.write_text(
        '[[repos]]\nslug = "demo"\ntitle = "Demo"\npath = "/no/such/path"\nstatus = "active"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--json", "--config", str(config), "repos", "resolve", "demo"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["command"] == "repos.resolve"
    assert "missing" in payload["error"]["message"]


def test_repos_add_set_status_and_remove_update_registry(tmp_path):
    config = tmp_path / ".env.toml"
    registry = tmp_path / "plotloom.toml"
    repo = tmp_path / "series"
    repo.mkdir()
    write_config(config, registry)

    add_result = CliRunner().invoke(
        main,
        ["--config", str(config), "repos", "add", "demo", "--title", "Demo", "--path", str(repo)],
    )
    status_result = CliRunner().invoke(main, ["--config", str(config), "repos", "set-status", "demo", "paused"])
    remove_result = CliRunner().invoke(main, ["--config", str(config), "repos", "remove", "demo"])

    assert add_result.exit_code == 0
    assert status_result.exit_code == 0
    assert remove_result.exit_code == 0
    data = tomllib.loads(registry.read_text(encoding="utf-8"))
    assert data["repos"] == []
