import os
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class PartPreview(BaseDocuWidget):
    """
    A reusable widget for safe SVG preview rendering.

    Features:
    - Handles missing SVG files gracefully.
    - Path resolution relative to node storage.
    - consistent sizing for grids and modals.
    """

    def __init__(self, svg_path: str | None = None, size: str = "120px", system_scope: Any = None):
        super().__init__(system_scope)
        self.svg_path = svg_path
        self.size = size

    def render(self):
        """Render the thumbnail or placeholder."""
        if not self.svg_path:
            return self._render_placeholder()

        # check if file exists (on the current node)
        if not os.path.exists(self.svg_path):
            return self._render_placeholder("File Missing")

        try:
            return ui.image(self.svg_path).style(
                f"width: {self.size}; height: {self.size}; object-fit: contain;"
            )
        except Exception:
            return self._render_placeholder("Render Error")

    def _render_placeholder(self, label: str = "No Preview"):
        """Render a consistent placeholder style."""
        with (
            ui.card()
            .classes("items-center justify-center bg-zinc-800 border border-zinc-700 shadow-inner")
            .style(f"width: {self.size}; height: {self.size};")
        ):
            ui.icon("extension", size="24px").classes("text-zinc-600")
            ui.label(label).classes("text-[8px] uppercase tracking-tighter text-zinc-500 mt-1")
