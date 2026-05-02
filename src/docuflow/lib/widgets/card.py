"""
Card - base card with solid surface for Teal Industrial design.

Use instead of glass-card for industrial look.
"""

from collections.abc import Callable
from typing import Any

from nicegui import ui


class Card:
    """Card container with solid surface.

    Args:
        content: Callable - function to render content
        padding: str - padding classes (default: "p-4")
        classes: str - additional classes
    """

    def __init__(
        self,
        content: Callable[[], Any] | None = None,
        padding: str = "p-4",
        classes: str = "",
    ) -> None:
        self.content = content
        self.padding = padding
        self.classes = classes

    def render(self) -> None:
        """Рендерит карточку."""
        with ui.column().classes(f"card {self.padding} {self.classes}".strip()):
            if self.content:
                self.content()

    def __enter__(self) -> "Card":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class CardRow:
    """Card with row layout.

    Args:
        classes: str - additional classes
    """

    def __init__(self, classes: str = "") -> None:
        self.classes = classes

    def render(self) -> None:
        with ui.row().classes(f"card p-4 {self.classes}".strip()):
            pass

    def __enter__(self) -> "CardRow":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def is_empty(self) -> bool:
        """Returns True if CardRow has no content."""
        return True
