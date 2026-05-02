"""
Surface - container with surface style for grouping elements.

Use for panels, sections, groups.
"""

from collections.abc import Callable

from nicegui import ui


class Surface:
    """Контейнер-поверхность.

    Args:
        content: Callable — функция для рендеринга
        padding: str — padding классы
        gap: str — gap для column/row
        layout: str — "col" или "row"
    """

    def __init__(
        self,
        content: Callable | None = None,
        padding: str = "p-4",
        gap: str = "gap-4",
        layout: str = "col",
    ) -> None:
        self.content = content
        self.padding = padding
        self.gap = gap
        self.layout = layout

    def render(self) -> None:
        """Рендерит surface."""
        base_classes: str = f"surface {self.padding}"
        if self.layout == "row":
            with ui.row().classes(f"{base_classes} {self.gap}"):
                if self.content:
                    self.content()
        else:
            with ui.column().classes(f"{base_classes} {self.gap}"):
                if self.content:
                    self.content()


class SurfaceSection:
    """Section with header title.

    Args:
        title: str - section title
        icon: str - icon name (optional)
        content: Callable - content to render
    """

    def __init__(
        self,
        title: str,
        icon: str = "",
        content: Callable | None = None,
    ) -> None:
        self.title = title
        self.icon = icon
        self.content = content

    def render(self) -> None:
        """Рендерит секцию."""
        with ui.column().classes("w-full gap-4"):
            # Заголовок
            with ui.row().classes("items-center gap-2"):
                if self.icon:
                    ui.icon(self.icon, size="18px", color="teal")
                ui.label(self.title).classes("text-lg font-bold text-white")

            # Контент
            with ui.column().classes("surface p-4 gap-4"):
                if self.content:
                    self.content()


class SurfaceCard:
    """Surface в виде карточки (alias для совместимости).

    Args:
        content: Callable
        title: str — заголовок
    """

    def __init__(
        self,
        content: Callable | None = None,
        title: str = "",
    ) -> None:
        self.content = content
        self.title = title

    def render(self) -> None:
        """Рендерит card."""
        with ui.column().classes("surface p-4 gap-4"):
            if self.title:
                ui.label(self.title).classes("text-lg font-bold text-white mb-2")
            if self.content:
                self.content()
