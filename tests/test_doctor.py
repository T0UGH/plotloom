import json

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.doctor import redact_present


def test_redact_present_never_returns_secret():
    assert redact_present("abc123", source="env") == "present via env"
    assert "abc" not in redact_present("abc123", source="env")
    assert redact_present("", source="config") == "absent"


def test_doctor_volcengine_reports_secret_presence_without_value(tmp_path, monkeypatch):
    cfg = tmp_path / ".env.toml"
    cfg.write_text('[adapters.volcengine-seedance]\nark_api_key = "hidden-value"\n', encoding="utf-8")
    cfg.chmod(0o600)
    monkeypatch.delenv("ARK_API_KEY", raising=False)

    result = CliRunner().invoke(main, ["--json", "--config", str(cfg), "doctor", "--adapter", "volcengine-seedance"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["checks"]["volcengine-seedance"]["ark_api_key"]["status"] == "present via config"
    assert "hidden-value" not in result.output
