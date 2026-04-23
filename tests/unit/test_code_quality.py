"""
TDD Tests for Code Quality: No Magic Numbers/Strings.

Principle: Code as Documentation — every value should be named and documented.
"""

import ast
from pathlib import Path


def _get_python_files(directory: str) -> list[Path]:
    """Get all Python files in directory recursively."""
    return list(Path(directory).rglob("*.py"))


def _extract_numbers_from_source(source: str) -> list[str]:
    """Extract numeric literals from Python source code."""
    tree = ast.parse(source)
    numbers = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            # Skip common non-magic numbers
            if node.value in (0, 1, -1, 2, True, False):
                continue
            numbers.append(str(node.value))

    return numbers


def _extract_strings_from_source(source: str) -> list[str]:
    """Extract string literals that look like magic values."""
    tree = ast.parse(source)
    strings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            # Skip empty strings, single chars, format strings, and common patterns
            if (
                len(value) <= 1
                or "{" in value
                or value in ("", " ", "\n", "\t")
                or value.startswith("_")
                or value.isupper()
            ):  # Already a constant
                continue
            # Skip file paths and URLs
            if "/" in value or "\\" in value or "http" in value:
                continue
            strings.append(value)

    return strings


class TestNoMagicNumbersInSystem:
    """Test that system.py has no magic numbers."""

    def test_no_magic_number_5_for_sleep(self):
        """RED: system.py should not have magic number 5 for sleep interval."""
        source = Path("src/docuflow/features/folder_scanner/system.py").read_text()

        # Check that number 5 is not used directly in asyncio.sleep
        assert "asyncio.sleep(5)" not in source, (
            "Magic number 5 in asyncio.sleep should be a named constant"
        )

    def test_no_magic_number_4096_for_md5(self):
        """RED: system.py should not have magic number 4096 for MD5 chunk size."""
        source = Path("src/docuflow/features/folder_scanner/system.py").read_text()

        # Check that number 4096 is not used directly in code (excluding constant definition)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            # Skip constant definition line
            if "MD5_CHUNK_SIZE" in line:
                continue
            # Check for 4096 in other lines
            if "4096" in line:
                assert False, f"Line {i + 1}: Magic number 4096 should use MD5_CHUNK_SIZE constant"

    def test_no_magic_string_general(self):
        """RED: system.py should not have magic string 'GENERAL' for default project."""
        source = Path("src/docuflow/features/folder_scanner/system.py").read_text()

        # Check that string "GENERAL" is not used directly
        assert '"GENERAL"' not in source, (
            "Magic string 'GENERAL' should use settings.default_project_name"
        )


class TestNoMagicNumbersInConfig:
    """Test that config.py has no magic numbers."""

    def test_no_magic_number_45_for_timeout(self):
        """RED: config.py should not have magic number 45.0 for coordinator timeout."""
        source = Path("src/docuflow/infrastructure/config.py").read_text()

        # Check that number 45.0 is not used directly (excluding comments)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            # Skip comment lines
            if line.strip().startswith("#"):
                continue
            # Check for 45.0 in code
            if "45.0" in line:
                assert False, (
                    f"Line {i + 1}: Magic number 45.0 should be a named constant in constants.py"
                )


class TestNoMagicStringsInParsers:
    """Test that parsers have no magic strings."""

    def test_no_magic_string_rework(self):
        """RED: folder.py should not have magic string 'REWORK'."""
        source = Path("src/docuflow/features/folder_scanner/parsers/folder.py").read_text()

        # Check that string "REWORK" is not used directly in code (excluding constant definition)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            # Skip constant definition line
            if "REWORK_KEYWORD" in line:
                continue
            # Check for "REWORK" in other lines
            if '"REWORK"' in line or "'REWORK'" in line:
                assert False, (
                    f"Line {i + 1}: Magic string 'REWORK' should use REWORK_KEYWORD constant"
                )


class TestAllMethodsHaveDocstrings:
    """Test that all public methods have docstrings."""

    def test_di_methods_have_docstrings(self):
        """RED: All provider methods in di.py should have docstrings."""
        source = Path("src/docuflow/infrastructure/di.py").read_text()
        tree = ast.parse(source)

        missing_docstrings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private methods and __init__
                if node.name.startswith("_"):
                    continue
                # Check for docstring
                if (
                    not node.body
                    or not isinstance(node.body[0], ast.Expr)
                    or not isinstance(node.body[0].value, ast.Constant)
                    or not isinstance(node.body[0].value.value, str)
                ):
                    missing_docstrings.append(node.name)

        assert not missing_docstrings, f"Methods without docstrings in di.py: {missing_docstrings}"

    def test_system_methods_have_docstrings(self):
        """RED: Key methods in system.py should have docstrings."""
        source = Path("src/docuflow/features/folder_scanner/system.py").read_text()
        tree = ast.parse(source)

        methods_needing_docstrings = [
            "_update_work_item_status",
            "_sync_material",
            "_sync_part",
            "_calculate_md5",
        ]

        missing_docstrings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in methods_needing_docstrings:
                if (
                    not node.body
                    or not isinstance(node.body[0], ast.Expr)
                    or not isinstance(node.body[0].value, ast.Constant)
                    or not isinstance(node.body[0].value.value, str)
                ):
                    missing_docstrings.append(node.name)

        assert not missing_docstrings, (
            f"Methods without docstrings in system.py: {missing_docstrings}"
        )
