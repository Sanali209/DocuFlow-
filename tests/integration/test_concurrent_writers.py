import json

import anyio
import pytest

from docuflow.infrastructure.bus import FileBusSystem
from docuflow.infrastructure.config import Config


@pytest.mark.anyio
async def test_concurrent_writers(tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    system = FileBusSystem(cfg)
    system._ensure_directories_exist()

    async with anyio.create_task_group() as tg:
        for i in range(20):
            filename = f"REQ_node_foo_{i}.json"
            payload = {"header": {"id": str(i)}, "body": {"x": i}}
            tg.start_soon(system._atomic_write, system._inbox, filename, payload)

    # Verify files
    for i in range(20):
        final = system._inbox / f"REQ_node_foo_{i}.json"
        assert final.exists()
        data = json.loads(final.read_text(encoding="utf-8"))
        assert data["header"]["id"] == str(i)
