import json

import pytest

from docuflow.infrastructure.config import Config
from docuflow.infrastructure.bus import FileBusSystem


@pytest.mark.anyio
async def test_atomic_write_creates_final_file(tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    system = FileBusSystem(cfg)
    system._ensure_directories_exist()

    filename = "REQ_node_foo_123.json"
    payload = {"header": {"id": "123"}, "body": {"x": 1}}

    await system._atomic_write(system._inbox, filename, payload)

    final = system._inbox / filename
    temp = system._inbox / f"TEMP_{filename}"

    assert final.exists()
    assert not temp.exists()

    data = json.loads(final.read_text(encoding="utf-8"))
    assert data["header"]["id"] == "123"


@pytest.mark.anyio
async def test_atomic_write_overwrite(tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    system = FileBusSystem(cfg)
    system._ensure_directories_exist()

    filename = "REQ_node_foo_456.json"
    payload1 = {"header": {"id": "456"}, "body": {"x": 1}}
    payload2 = {"header": {"id": "456"}, "body": {"x": 2}}

    await system._atomic_write(system._inbox, filename, payload1)
    await system._atomic_write(system._inbox, filename, payload2)

    final = system._inbox / filename
    assert final.exists()
    data = json.loads(final.read_text(encoding="utf-8"))
    assert data["body"]["x"] == 2

