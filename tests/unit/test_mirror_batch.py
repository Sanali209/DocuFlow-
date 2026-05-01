# tests/unit/test_mirror_batch.py
import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from docuflow.domain.entities.production import TaskItem, WorkerBucketEntry


def make_engine() -> Engine:
    # Use StaticPool so all connections share the same in-memory DB,
    # including connections opened from threads via anyio.to_thread.run_sync.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def make_mirror(tmp_path: Path, engine: Engine) -> Any:
    from docuflow.features.folder_scanner.mirror import NSMirrorService
    from docuflow.infrastructure.config import Config

    config = Config(node_id="STATION_A", shared_path=str(tmp_path))
    sdk = MagicMock()
    return NSMirrorService(config=config, sdk=sdk, engine=engine)


@pytest.mark.asyncio
async def test_sync_bucket_does_not_n_plus_one(tmp_path: Path) -> None:
    """_sync_bucket must load all tasks in a single JOIN query, not one per entry."""
    engine = make_engine()
    mirror = make_mirror(tmp_path, engine)

    with Session(engine) as session:
        for i in range(1, 4):
            task = TaskItem(
                id=i,
                work_item_id=1,
                file_name=f"part{i}.GNC",
                file_path=f"folder/part{i}.GNC",
                file_hash="abc",
            )
            entry = WorkerBucketEntry(task_item_id=i, node_id="STATION_A")
            session.add(task)
            session.add(entry)
        session.commit()

    query_count = [0]
    original_exec = Session.exec

    def counting_exec(self: Session, stmt: Any, *args: Any, **kwargs: Any) -> Any:
        query_count[0] += 1
        return original_exec(self, stmt, *args, **kwargs)

    settings = MagicMock()
    settings.local_ns_path = str(tmp_path / "ns")
    settings.ns_mirror_copy_timeout_s = 5.0

    with (
        patch.object(Session, "exec", counting_exec),
        patch.object(mirror, "_mirror_task", new=AsyncMock(return_value=[])),
        patch.object(mirror, "_db_commit_logs", return_value=None),
    ):
        await mirror._sync_bucket(settings)

    assert query_count[0] <= 2, (
        f"Expected at most 2 DB queries (1 for bucket+tasks, 1 optional), got {query_count[0]}"
    )


@pytest.mark.asyncio
async def test_mirror_task_offloads_md5_to_thread(tmp_path: Path) -> None:
    """_calculate_md5 must be called via anyio.to_thread.run_sync."""
    engine = make_engine()
    mirror = make_mirror(tmp_path, engine)

    dst = tmp_path / "ns" / "part.GNC"
    dst.parent.mkdir(parents=True)
    dst.write_bytes(b"GNC content")

    task = MagicMock()
    task.file_name = "part.GNC"
    task.file_path = "part.GNC"
    task.file_hash = "different_hash"
    task.id = 1
    task.work_item_id = 1

    settings = MagicMock()
    settings.local_ns_path = str(tmp_path / "ns")
    settings.ns_mirror_copy_timeout_s = 5.0
    settings.sidra_scan_path = None
    settings.mihtav_scan_path = None
    settings.other_scan_path = None

    run_sync_calls: list[Any] = []

    async def fake_run_sync(func: Any, *args: Any, **kwargs: Any) -> Any:
        run_sync_calls.append(func)
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    with (
        patch("anyio.to_thread.run_sync", side_effect=fake_run_sync),
        patch.object(mirror, "_resolve_source_path_no_session", return_value=dst),
    ):
        await mirror._mirror_task(task, settings)

    assert any(getattr(f, "__name__", None) == "_calculate_md5" for f in run_sync_calls), (
        "_calculate_md5 must go through anyio.to_thread.run_sync"
    )
