"""
Input - standard input fields for Teal Industrial design.

Standardized inputs with labels and consistent style.
"""

from collections.abc import Callable

from nicegui import ui


class InputLabel:
    """Input field with label.

    Args:
        label: str - label above field
        placeholder: str - placeholder text
        value: str - initial value
        on_change: Callable - change handler
        input_type: str - input type (text, password, number)
        disabled: bool - disabled state
    """

    def __init__(
        self,
        label: str,
        placeholder: str = "",
        value: str = "",
        on_change: Callable | None = None,
        input_type: str = "text",
        disabled: bool = False,
    ) -> None:
        self.label = label
        self.placeholder = placeholder
        self.value = value
        self.on_change = on_change
        self.input_type = input_type
        self.disabled = disabled

    def render(self) -> ui.input:
        """Renders input with label."""
        with ui.column().classes("gap-1"):
            ui.label(self.label).classes("text-sm text-slate-300 font-medium")

            input_field = (
                ui.input(
                    placeholder=self.placeholder,
                    value=self.value,
                    on_change=self.on_change,
                )
                .props(f"type={self.input_type} {'disable' if self.disabled else ''}")
                .classes("w-full input-field")
            )

            return input_field


class TextareaLabel:
    """Textarea field with label.

    Args:
        label: str - label text
        placeholder: str - placeholder
        value: str - initial value
        rows: int - number of rows
    """

    def __init__(
        self,
        label: str,
        placeholder: str = "",
        value: str = "",
        rows: int = 3,
    ) -> None:
        self.label = label
        self.placeholder = placeholder
        self.value = value
        self.rows = rows

    def render(self) -> ui.textarea:
        """Рендерит textarea."""
        with ui.column().classes("gap-1"):
            ui.label(self.label).classes("text-sm text-slate-300 font-medium")

            return (
                ui.textarea(
                    placeholder=self.placeholder,
                    value=self.value,
                )
                .props(f"rows={self.rows}")
                .classes("w-full input-field")
            )


class SelectLabel:
    """Select dropdown with label.

    Args:
        label: str - label text
        options: list[tuple[str, str]] - (value, label) pairs
        value: str - initial value
        on_change: Callable - change handler
    """

    def __init__(
        self,
        label: str,
        options: list[tuple[str, str]],
        value: str = "",
        on_change: Callable | None = None,
    ) -> None:
        self.label = label
        self.options = options
        self.value = value
        self.on_change = on_change

    def render(self) -> ui.select:
        """Рендерит select."""
        with ui.column().classes("gap-1"):
            ui.label(self.label).classes("text-sm text-slate-300 font-medium")

            return (
                ui.select(
                    options=self.options,
                    value=self.value,
                    on_change=self.on_change,
                )
                .props("use-chips")
                .classes("w-full input-field")
            )


class SwitchLabel:
    """Switch toggle with label.

    Args:
        label: str - label text
        value: bool - initial value
        on_change: Callable - change handler
    """

    def __init__(
        self,
        label: str,
        value: bool = False,
        on_change: Callable | None = None,
    ) -> None:
        self.label = label
        self.value = value
        self.on_change = on_change

    def render(self) -> ui.switch:
        """Рендерит switch."""
        return ui.switch(self.label, value=self.value, on_change=self.on_change).props("color=teal")


class CheckboxLabel:
    """Checkbox with label.

    Args:
        label: str - label text
        value: bool - initial value
        on_change: Callable - change handler
    """

    def __init__(
        self,
        label: str,
        value: bool = False,
        on_change: Callable | None = None,
    ) -> None:
        self.label = label
        self.value = value
        self.on_change = on_change

    def render(self) -> ui.checkbox:
        """Рендерит checkbox."""
        return ui.checkbox(self.label, value=self.value, on_change=self.on_change).props(
            "color=teal"
        )
