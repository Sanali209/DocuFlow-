import importlib


def test_config_loads_from_env_file(tmp_path, monkeypatch):
    """Config must read values from .env file when present."""
    env_file = tmp_path / ".env"
    env_file.write_text("DOCUFLOW_NODE_ID=FROM_ENV_FILE\n")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DOCUFLOW_NODE_ID", raising=False)

    import docuflow.infrastructure.config as cfg_module
    importlib.reload(cfg_module)
    from docuflow.infrastructure.config import Config

    config = Config()
    assert config.node_id == "FROM_ENV_FILE", (
        "Config must read DOCUFLOW_NODE_ID from .env file"
    )
