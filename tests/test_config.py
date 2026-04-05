from docuflow.infrastructure.config import Config


def test_config_defaults():
    """Verify default values for P2P settings."""
    config = Config()
    assert config.app_name == "DocuFlow"
    assert config.heartbeat_interval == 15
    assert config.coordinator_timeout == 45
    assert config.shared_path == "./shared_network"


def test_config_env_override(monkeypatch):
    """Verify that environment variables override defaults."""
    monkeypatch.setenv("NODE_ID", "LASER_99")
    monkeypatch.setenv("SHARED_PATH", "/mnt/cifs/data")

    config = Config()
    assert config.node_id == "LASER_99"
    assert config.shared_path == "/mnt/cifs/data"
    assert config.bus_path == "/mnt/cifs/data/BUS"


def test_bus_path_derivation():
    """Verify that the File Bus path is correctly derived from the shared root."""
    config = Config(shared_path="/custom/path")
    assert config.bus_path == "/custom/path/BUS"
