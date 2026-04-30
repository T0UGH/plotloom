import json

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.config import load_config


def test_config_init_writes_template_with_private_permissions(tmp_path):
    cfg = tmp_path / ".plotloom" / ".env.toml"
    result = CliRunner().invoke(main, ["--config", str(cfg), "config", "init"])

    assert result.exit_code == 0
    assert cfg.exists()
    assert cfg.stat().st_mode & 0o777 == 0o600
    assert "default_video_adapters" in cfg.read_text()


def test_config_env_overrides_toml(tmp_path, monkeypatch):
    cfg = tmp_path / ".env.toml"
    cfg.write_text('[adapters.happyhorse-fal]\nfal_key = "from-file"\n', encoding="utf-8")
    monkeypatch.setenv("FAL_KEY", "from-env")

    loaded = load_config(cfg)

    assert loaded.adapter_value("happyhorse-fal", "fal_key") == "from-env"


def test_config_path_json_shape_accepts_postfix_json(tmp_path):
    cfg = tmp_path / ".plotloom" / ".env.toml"
    result = CliRunner().invoke(main, ["--config", str(cfg), "config", "path", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "config.path"
    assert payload["config_path"] == str(cfg)
    assert "path" not in payload


def test_config_doctor_malformed_toml_json_error(tmp_path):
    cfg = tmp_path / ".env.toml"
    cfg.write_text("[plotloom\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--json", "--config", str(cfg), "config", "doctor"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["command"] == "config"
    assert payload["error"]["code"] == "CONFIG_ERROR"
    assert "Could not parse config TOML" in payload["error"]["message"]
    assert payload["error"]["next_step"]


def test_config_init_force_overwrites_malformed_toml(tmp_path):
    cfg = tmp_path / ".env.toml"
    cfg.write_text("[plotloom\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--config", str(cfg), "config", "init", "--force"])

    assert result.exit_code == 0
    assert "default_video_adapters" in cfg.read_text(encoding="utf-8")
    assert cfg.stat().st_mode & 0o777 == 0o600


def test_config_init_tightens_existing_permissions_without_overwriting(tmp_path):
    cfg = tmp_path / ".env.toml"
    cfg.write_text('[adapters.happyhorse-fal]\nfal_key = "keep-me"\n', encoding="utf-8")
    cfg.chmod(0o644)

    result = CliRunner().invoke(main, ["--config", str(cfg), "config", "init"])

    assert result.exit_code == 0
    assert cfg.read_text(encoding="utf-8") == '[adapters.happyhorse-fal]\nfal_key = "keep-me"\n'
    assert cfg.stat().st_mode & 0o777 == 0o600


def test_config_doctor_happyhorse_missing_key_reports_status_without_secret(tmp_path, monkeypatch):
    cfg = tmp_path / ".env.toml"
    cfg.write_text('[adapters.happyhorse-fal]\nfal_key = ""\n', encoding="utf-8")
    monkeypatch.delenv("FAL_KEY", raising=False)

    result = CliRunner().invoke(main, ["--json", "--config", str(cfg), "config", "doctor", "--adapter", "happyhorse-fal"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["command"] == "config.doctor"
    assert payload["adapter"] == "happyhorse-fal"
    assert payload["checks"]["fal_key"]["status"] == "absent"
    assert "from-file" not in result.output
    assert "keep-me" not in result.output
