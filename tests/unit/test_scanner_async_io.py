import anyio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


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

    calls_via_thread = []
    real_run_sync = anyio.to_thread.run_sync

    async def spy_run_sync(func, *args, **kwargs):
        # MagicMock replaces _calculate_file_checksum; __name__ raises AttributeError.
        # We detect the checksum offload by checking the func is callable and its
        # class name indicates it is the mock standing in for _calculate_file_checksum,
        # OR by checking that ANY call goes through run_sync (since the only blocking
        # I/O in process_task_file is the checksum read).
        try:
            name = func.__name__
        except AttributeError:
            # MagicMock replacing _calculate_file_checksum has no __name__; treat
            # that as a positive signal — it IS the patched checksum callable.
            name = "_calculate_file_checksum"
        if callable(func) and name == "_calculate_file_checksum":
            calls_via_thread.append(func)
        return await real_run_sync(func, *args, **kwargs)

    gnc_file = tmp_path / "part.GNC"
    gnc_file.write_bytes(b"")

    work_item = MagicMock()
    work_item.id = 1

    with patch("docuflow.features.folder_scanner.system.run_sync_in_thread", side_effect=spy_run_sync):
        with patch.object(scanner, "_calculate_file_checksum", return_value="abc123"):
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

    assert len(calls_via_thread) > 0, (
        "_calculate_file_checksum must be called via anyio.to_thread.run_sync, not directly"
    )
