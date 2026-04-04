import os
import pytest
from docuflow.infrastructure.config import Config

def test_config_has_p2p_intervals():
    """TDD: Verify that Config includes all required P2P polling intervals."""
    config = Config()
    
    # These should exist and have reasonable defaults from constants or env
    assert hasattr(config, "bus_poll_interval")
    assert hasattr(config, "sync_check_interval")
    assert hasattr(config, "gc_interval")
    
    # Verify defaults (placeholder values for now, will match constants later)
    assert config.bus_poll_interval > 0
    assert config.sync_check_interval > 0
    assert config.gc_interval > 0

def test_config_interval_env_override(monkeypatch):
    """TDD: Verify that environment variables correctly override intervals."""
    monkeypatch.setenv("BUS_POLL_INTERVAL", "5")
    monkeypatch.setenv("SYNC_CHECK_INTERVAL", "120")
    monkeypatch.setenv("GC_INTERVAL", "3600")
    
    config = Config()
    
    assert config.bus_poll_interval == 5
    assert config.sync_check_interval == 120
    assert config.gc_interval == 3600
