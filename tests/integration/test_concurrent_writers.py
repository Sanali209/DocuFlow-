import json
import asyncio

import pytest

from docuflow.infrastructure.config import Config
from docuflow.infrastructure.bus import FileBusSystem


@pytest.mark.anyio
async def test_concurrent_writers(tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    system = FileBusSystem(cfg)
    system._ensure_directories_exist()

    async def writer(idx: int):
        filename = f"REQ_node_foo_{idx}.json"
        payload = {"header": {"id": str(idx)}, "body": {"x": idx}}
        await system._atomic_write(system._inbox, filename, payload)

    tasks = [writer(i) for i in range(20)]
    await asyncio.gather(*tasks)

    # Verify files
    for i in range(20):
        final = system._inbox / f"REQ_node_foo_{i}.json"
        assert final.exists()
        data = json.loads(final.read_text(encoding="utf-8"))
        assert data["header"]["id"] == str(i)

