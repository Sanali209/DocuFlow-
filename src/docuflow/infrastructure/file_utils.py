"""Shared file I/O utilities for DocuFlow infrastructure."""

import hashlib
from pathlib import Path
from typing import BinaryIO


def calculate_file_md5(path: Path) -> str:
    """Calculate MD5 hex digest of a file's contents.

    Reads in 4096-byte chunks to handle large files efficiently.

    Note: MD5 is used only for fast file comparison and deduplication,
    not for cryptographic security.

    Args:
        path: Path to the file.

    Returns:
        Lowercase 32-character MD5 hex string.
    """
    h: hashlib._Hash = hashlib.md5()  # noqa: S324
    f: BinaryIO
    with open(path, "rb") as f:
        chunk: bytes
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()
