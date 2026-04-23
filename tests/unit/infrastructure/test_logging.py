"""TDD Tests for logging setup.

Coverage target: infrastructure/logging.py
"""

import pytest

from docuflow.infrastructure.logging import setup_logging


class TestSetupLogging:
    """RED: setup_logging should configure loguru without errors."""

    def test_runs_without_exception(self):
        """Minimal smoke test: function should execute cleanly."""
        setup_logging("DEBUG")

    def test_runs_with_info_level(self):
        setup_logging("INFO")

    def test_runs_with_warning_level(self):
        setup_logging("WARNING")
