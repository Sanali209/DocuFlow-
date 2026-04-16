"""
Button - standard buttons for Teal Industrial design.

Primary: teal solid
Secondary: outlined
Ghost: text only
"""

from collections.abc import Callable

from nicegui import ui


class PrimaryBtn:
    """Primary button with teal background.

    Args:
        text: str - button label
        icon: str - icon name (optional)
        on_click: Callable - click handler
        size: str - size (sm, md, lg)
        disabled: bool - disabled state
    """

    def __init__(
        self,
        text: str = "",
        icon: str = "",
        on_click: Callable | None = None,
        size: str = "md",
        disabled: bool = False,
    ):
        self.text = text
        self.icon = icon
        self.on_click = on_click
        self.size = size
        self.disabled = disabled

    def render(self) -> ui.button:
        """Рендерит primary кнопку."""
        size_map = {
            "sm": "text-sm px-3 py-1",
            "md": "text-base px-4 py-2",
            "lg": "text-lg px-6 py-3",
        }

        classes = f"btn-primary {size_map.get(self.size, size_map['md'])} rounded-lg font-semibold"

        if self.icon:
            return (
                ui.button(self.text, icon=self.icon, on_click=self.on_click)
                .props(f"color=teal {'' if not self.disabled else 'disable'}")
                .classes(classes)
            )

        return (
            ui.button(self.text, on_click=self.on_click)
            .props(f"color=teal {'' if not self.disabled else 'disable'}")
            .classes(classes)
        )


class SecondaryBtn:
    """Secondary button with outlined style.

    Args:
        text: str - button label
        icon: str - icon name (optional)
        on_click: Callable - click handler
        size: str - size
    """

    def __init__(
        self,
        text: str = "",
        icon: str = "",
        on_click: Callable | None = None,
        size: str = "md",
    ):
        self.text = text
        self.icon = icon
        self.on_click = on_click
        self.size = size

    def render(self) -> ui.button:
        """Рендерит secondary кнопку."""
        size_map = {
            "sm": "text-sm px-3 py-1",
            "md": "text-base px-4 py-2",
            "lg": "text-lg px-6 py-3",
        }

        classes = (
            f"btn-secondary {size_map.get(self.size, size_map['md'])} rounded-lg font-semibold"
        )

        if self.icon:
            return (
                ui.button(self.text, icon=self.icon, on_click=self.on_click)
                .props("outline color=grey-5")
                .classes(classes)
            )

        return (
            ui.button(self.text, on_click=self.on_click)
            .props("outline color=grey-5")
            .classes(classes)
        )


class GhostBtn:
    """Ghost кнопка — только текст.

    Args:
        text: str — текст
        icon: str — иконка
        on_click: Callable
    """

    def __init__(
        self,
        text: str = "",
        icon: str = "",
        on_click: Callable | None = None,
    ):
        self.text = text
        self.icon = icon
        self.on_click = on_click

    def render(self) -> ui.button:
        """Renders ghost button."""
        classes = "text-slate-300 hover:text-white hover:bg-white/5 px-3 py-2 rounded-lg"

        if self.icon:
            return (
                ui.button(self.text, icon=self.icon, on_click=self.on_click)
                .props("flat")
                .classes(classes)
            )

        return ui.button(self.text, on_click=self.on_click).props("flat").classes(classes)
