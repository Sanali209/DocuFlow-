import asyncio

import anyio
import pytest
from unittest.mock import MagicMock, patch


def make_scanner(tmp_path):
    from docuflow.infrastructure.config import Config
    from docuflow.features.folder_scanner.system import FolderScannerSystem

    config = Config(node_id="TEST", shared_path=str(tmp_path))
    sdk = MagicMock()
    sdk.orchestrator.is_leader = True
    engine = MagicMock()
    return FolderScannerSystem(config=config, sdk=sdk, engine=engine)


@pytest.mark.asyncio
async def test_process_task_file_offloads_checksum_to_thread(tmp_path):
    """_calculate_file_checksum must be called via anyio.to_thread.run_sync."""
    scanner = make_scanner(tmp_path)

    run_sync_calls: list = []

    async def fake_run_sync(func, *args, **kwargs):
        run_sync_calls.append(func)
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    gnc_file = tmp_path / "part.GNC"
    gnc_file.write_bytes(b"")
    work_item = MagicMock()
    work_item.id = 1

    with patch("anyio.to_thread.run_sync", side_effect=fake_run_sync):
        with patch.object(scanner, "_calculate_file_checksum", return_value="abc123") as mock_cs:
            with patch.object(scanner, "gnc_content_parser") as mock_parser:
                mock_parser.parse.return_value = MagicMock(parts=[], mat_code=None)
                with patch.object(scanner, "task_filename_parser") as mock_tf:
                    mock_tf.parse_task_filename.return_value = MagicMock(
                        step_index=1, batch_index=0
                    )
                    with patch("sqlmodel.Session") as mock_session_cls:
                        mock_sess = MagicMock()
                        mock_sess.__enter__ = MagicMock(return_value=mock_sess)
                        mock_sess.__exit__ = MagicMock(return_value=False)
                        mock_sess.exec.return_value.first.return_value = None
                        mock_session_cls.return_value = mock_sess
                        try:
                            await scanner.process_task_file(gnc_file, work_item, tmp_path)
                        except Exception:
                            pass

    assert mock_cs in run_sync_calls, (
        "_calculate_file_checksum must be dispatched via anyio.to_thread.run_sync, not called directly"
    )
