"""
Тесты для HandoverForm и HandoverBanner.

Smoke тесты — проверяют, что виджеты рендерятся без ошибок.
"""

import pytest

pytest.importorskip("nicegui")

from docuflow.lib.widgets.handover_banner import HandoverBanner
from docuflow.lib.widgets.handover_form import HandoverForm


@pytest.mark.usefixtures("ui_context")
class TestHandoverForm:
    """Тесты для HandoverForm."""

    def test_renders_collapsed(self):
        """Рендерит форму в свернутом состоянии."""
        form = HandoverForm(
            node_id="LASER_1",
            on_submit=lambda a, b: None,
            system_scope=None,
        )
        result = form.render()
        assert result is not None


@pytest.mark.usefixtures("ui_context")
class TestHandoverBanner:
    """Тесты для HandoverBanner."""

    def test_renders(self):
        """Рендерит баннер входящей заметки."""
        banner = HandoverBanner(
            from_operator="admin",
            note="Test note",
            on_accept=lambda: None,
            system_scope=None,
        )
        result = banner.render()
        assert result is not None
