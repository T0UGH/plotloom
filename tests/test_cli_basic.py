import json

from click.testing import CliRunner

from plotloom.cli import main


def test_cli_version_runs():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert "plotloom" in result.output.lower()


def test_cli_json_error_shape_for_missing_command():
    result = CliRunner().invoke(main, ["--json", "missing-command"])
    payload = json.loads(result.output)

    assert result.exit_code == 1
    assert payload["ok"] is False
    assert payload["command"] == "missing-command"
    assert "No such command" in payload["error"]["message"]
    assert payload["error"]["code"]
