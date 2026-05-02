import ast
import importlib
from pathlib import Path


def get_files_with_stdlib_logging():
    """Find source files that still use stdlib logging.getLogger."""
    src = Path("src/docuflow")
    bad_files = []
    for py_file in src.rglob("*.py"):
        # Skip excluded files
        excluded = [
            "folder_scanner/system.py",
            "folder_scanner/mirror.py",
            "folder_scanner/parsers/gnc.py",
        ]
        if any(str(py_file).replace("\\", "/").endswith(e) for e in excluded):
            continue
        content = py_file.read_text(encoding="utf-8")
        if "logging.getLogger" in content:
            bad_files.append(str(py_file))
    return bad_files


def test_no_stdlib_getlogger_in_source():
    """Source files must use loguru logger, not logging.getLogger."""
    bad = get_files_with_stdlib_logging()
    assert bad == [], (
        f"These files still use logging.getLogger (convert to loguru):\n" + "\n".join(bad)
    )
