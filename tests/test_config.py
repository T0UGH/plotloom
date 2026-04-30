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
