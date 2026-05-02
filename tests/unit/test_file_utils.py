from pathlib import Path


def test_calculate_file_md5_returns_hex_string(tmp_path):
    """calculate_file_md5 must return a 32-char lowercase hex MD5 string."""
    from docuflow.infrastructure.file_utils import calculate_file_md5

    f = tmp_path / "test.bin"
    f.write_bytes(b"hello world")

    result = calculate_file_md5(f)
    assert isinstance(result, str)
    assert len(result) == 32
    assert result == result.lower()
    # Known MD5 of b"hello world"
    assert result == "5eb63bbbe01eeed093cb22bb8f5acdc3"


def test_calculate_file_md5_empty_file(tmp_path):
    """calculate_file_md5 must work on empty files."""
    from docuflow.infrastructure.file_utils import calculate_file_md5

    f = tmp_path / "empty.bin"
    f.write_bytes(b"")

    result = calculate_file_md5(f)
    assert result == "d41d8cd98f00b204e9800998ecf8427e"  # MD5 of empty


def test_scanner_checksum_uses_shared_utility():
    """FolderScannerSystem._calculate_file_checksum must delegate to file_utils."""
    import inspect
    from docuflow.features.folder_scanner.system import FolderScannerSystem

    source = inspect.getsource(FolderScannerSystem._calculate_file_checksum)
    assert "file_utils" in source or "calculate_file_md5" in source, (
        "_calculate_file_checksum must delegate to infrastructure.file_utils.calculate_file_md5"
    )


def test_mirror_md5_uses_shared_utility():
    """NSMirrorService._calculate_md5 must delegate to file_utils."""
    import inspect
    from docuflow.features.folder_scanner.mirror import NSMirrorService

    source = inspect.getsource(NSMirrorService._calculate_md5)
    assert "file_utils" in source or "calculate_file_md5" in source, (
        "_calculate_md5 must delegate to infrastructure.file_utils.calculate_file_md5"
    )
