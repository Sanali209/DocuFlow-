import os
import time

from docuflow.infrastructure import constants
from docuflow.infrastructure.bus import FileBusSystem
from docuflow.infrastructure.config import Config


def touch(path, older_by_seconds: int = 0):
    path.write_text("x")
    if older_by_seconds:
        atime = path.stat().st_atime - older_by_seconds
        mtime = path.stat().st_mtime - older_by_seconds
        os.utime(path, (atime, mtime))


def test_cleanup_temp_files_removes_stale(tmp_path):
    cfg = Config(shared_path=str(tmp_path))
    system = FileBusSystem(cfg)
    system._ensure_directories_exist()

    inbox = system._inbox
    fname_old = inbox / f"{constants.BUS_TEMP_PREFIX}old.json"
    fname_new = inbox / f"{constants.BUS_TEMP_PREFIX}new.json"

    # Create an old temp file (older than threshold)
    touch(fname_old)
    touch(fname_new)

    # Make the old file appear older than threshold (2 seconds)
    os.utime(fname_old, (time.time() - 10, time.time() - 10))

    # Run cleanup with threshold 5 seconds
    system._cleanup_temp_files(older_than_seconds=5)

    assert not fname_old.exists()
    assert fname_new.exists()
