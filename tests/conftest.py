import pytest
from nicegui import ui, context

@pytest.fixture
def ui_context():
    """Provides a proper NiceGUI context for UI rendering tests."""
    # Simple approach: just yield a column container.
    # NiceGUI's user_simulation handles its own context,
    # but for unit tests of widgets, we need a slot.
    with ui.column() as container:
        with container:
            yield container
