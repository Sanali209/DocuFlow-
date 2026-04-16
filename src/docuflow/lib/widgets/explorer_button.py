"""
ExplorerButton — кнопка "📂 Открыть в Explorer".

Открывает папку в проводнике Windows через subprocess.Popen.
"""

import subprocess
from pathlib import Path
from typing import Any

from nicegui import ui

from docuflow.lib.base_widget import BaseDocuWidget


class ExplorerButton(BaseDocuWidget):
    """
    Кнопка для открытия папки в проводнике Windows.

    Props:
        path: str | Path — путь к папке
        label: str — текст кнопки (по умолчанию "📂")
        tooltip: str — подсказка
        system_provider: Any — провайдер систем (опционально)
    """

    def __init__(
        self,
        path: str | Path,
        label: str = "📂",
        tooltip: str = "Открыть в Explorer",
        system_provider: Any = None,
    ):
        super().__init__(system_provider)
        self.path = Path(path) if isinstance(path, str) else path
        self.label = label
        self.tooltip = tooltip

    def render(self) -> ui.button:
        """Рендерит кнопку."""
        return (
            ui.button(self.label)
            .props(f'flat round tooltip="{self.tooltip}"')
            .on_click(self._open_explorer)
        )

    def _open_explorer(self) -> None:
        """Открывает папку в проводнике или показывает путь при ошибке."""
        try:
            # subprocess.Popen is non-blocking, so we don't need safe_action/timer here
            subprocess.Popen(["explorer.exe", str(self.path)])
        except Exception as e:
            ui.notify(f"Не удалось открыть проводник автоматически: {e}", type="negative")
            self._show_fallback_dialog(str(e))

    def _show_fallback_dialog(self, error_msg: str) -> None:
        """Показывает диалог с путем и кнопкой копирования при ошибке открытия."""
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[500px]"):
            ui.label("📁 Путь к папке").classes("text-h6 mb-2")
            ui.label(
                "Не удалось открыть проводник автоматически (возможно, сетевой диск не подключен)."
            ).classes("text-sm text-slate-500 mb-4")

            path_str = str(self.path)
            with ui.row().classes(
                "w-full items-center bg-gray-100 p-2 rounded border border-gray-200"
            ):
                ui.label(path_str).classes("font-mono text-xs flex-grow truncate")
                ui.button(
                    icon="content_copy", on_click=lambda: self._copy_to_clipboard(path_str)
                ).props("flat round dense")

            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Закрыть", on_click=dialog.close).props("flat")

        dialog.open()

    def _copy_to_clipboard(self, text: str) -> None:
        """Копирует текст в буфер обмена через JS."""
        ui.run_javascript(f'navigator.clipboard.writeText("{text}")')
        ui.notify("Путь скопирован в буфер обмена", type="positive")
