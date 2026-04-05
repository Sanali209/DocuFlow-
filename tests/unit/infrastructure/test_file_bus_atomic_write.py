import json
import os

import pytest

from docuflow.infrastructure import constants
from docuflow.infrastructure.bus import FileBusSystem
from docuflow.infrastructure.config import Config


@pytest.mark.anyio
async def test_atomic_write_success(tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    bus = FileBusSystem(cfg)
    bus._ensure_directories_exist()

    filename = "test_msg.json"
    payload = {"header": {"id": "1"}, "body": {"x": 1}}

    await bus._atomic_write(bus._inbox, filename, payload)

    final_path = bus._inbox / filename
    temp_path = bus._inbox / f"{constants.BUS_TEMP_PREFIX}{filename}"

    # Final file exists and contains JSON
    assert final_path.exists()
    with open(final_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["header"]["id"] == "1"

    # No temp file remains
    assert not temp_path.exists()


@pytest.mark.anyio
async def test_atomic_write_calls_fsync_and_replace(monkeypatch, tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    bus = FileBusSystem(cfg)
    bus._ensure_directories_exist()

    called = {"fsync": False, "replace": False}

    def fake_fsync(fd):
        called["fsync"] = True

    def fake_replace(a, b):
        called["replace"] = True

    monkeypatch.setattr(os, "fsync", fake_fsync)
    monkeypatch.setattr(os, "replace", fake_replace)

    filename = "test_msg2.json"
    payload = {"header": {"id": "2"}, "body": {"y": 2}}

    await bus._atomic_write(bus._inbox, filename, payload)

    assert called["fsync"] is True
    assert called["replace"] is True


@pytest.mark.anyio
async def test_atomic_write_replace_failure_cleans_temp(monkeypatch, tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    bus = FileBusSystem(cfg)
    bus._ensure_directories_exist()

    def raise_replace(a, b):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", raise_replace)

    filename = "test_msg3.json"
    payload = {"header": {"id": "3"}, "body": {"z": 3}}

    with pytest.raises(OSError):
        await bus._atomic_write(bus._inbox, filename, payload)

    temp_path = bus._inbox / f"{constants.BUS_TEMP_PREFIX}{filename}"
    # Temp file should be removed by cleanup
    assert not temp_path.exists()
